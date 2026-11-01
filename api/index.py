import os
import sys
import tempfile
from pathlib import Path

# En entornos serverless (Vercel / AWS Lambda), el home es read-only.
# Redirigir almacenamiento de tokens y caché al directorio temporal /tmp:
temp_storage = os.path.join(tempfile.gettempdir(), ".notebooklm-mcp-cli")
os.environ["NOTEBOOKLM_MCP_CLI_PATH"] = temp_storage
os.environ["HOME"] = tempfile.gettempdir()
try:
    os.makedirs(temp_storage, exist_ok=True)
except Exception:
    pass

# Asegurar URL canónica de Gemini Notebook
if not os.environ.get("NOTEBOOKLM_BASE_URL"):
    os.environ["NOTEBOOKLM_BASE_URL"] = "https://notebook.google.com"

import asyncio
from notebooklm_tools.mcp.server import mcp
from starlette.responses import JSONResponse
from starlette.routing import Route

raw_app = mcp.http_app(transport="streamable-http", stateless_http=True, path="/mcp")

async def health_check(request):
    return JSONResponse({
        "status": "online",
        "service": "NotebookLM MCP Serverless",
        "mcp_endpoint": "/mcp"
    })

raw_app.routes.insert(0, Route("/", health_check))

class VercelServerlessASGI:
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
        self._started = False
        self._ready_event = asyncio.Event()
        self._stop_event = asyncio.Event()

    async def _run_lifespan(self):
        try:
            async with self.asgi_app.router.lifespan_context(self.asgi_app):
                self._ready_event.set()
                await self._stop_event.wait()
        except Exception as e:
            print(f"Lifespan error: {e}")

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            header_dict = {k.decode("latin1").lower(): v.decode("latin1") for k, v in scope.get("headers", [])}
            raw_path = (
                header_dict.get("x-vercel-matched-path")
                or header_dict.get("x-matched-path")
                or header_dict.get("x-forwarded-uri")
                or ""
            )
            if "mcp" in raw_path or "mcp" in header_dict.get("referer", "") or scope.get("method") == "POST":
                scope["path"] = "/mcp"
            elif raw_path:
                scope["path"] = raw_path
            else:
                scope["path"] = "/"

        if not self._started:
            self._started = True
            asyncio.create_task(self._run_lifespan())
            await self._ready_event.wait()

        await self.asgi_app(scope, receive, send)

app = VercelServerlessASGI(raw_app)
