import os
import asyncio
from notebooklm_tools.mcp.server import mcp
from starlette.responses import JSONResponse
from starlette.routing import Route

if not os.environ.get("NOTEBOOKLM_BASE_URL"):
    os.environ["NOTEBOOKLM_BASE_URL"] = "https://notebook.google.com"

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
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            url_path = headers.get(b"x-forwarded-url", b"").decode("utf-8")
            print(f"DEBUG: path={scope.get('path')} matched_path={matched_path} forwarded={url_path}")
            
            # Si x-matched-path está presente, ese es el path solicitado originalmente
            if matched_path:
                scope["path"] = matched_path
            elif scope.get("path", "").startswith("/api/index.py"):
                scope["path"] = "/"

        if not self._started:
            self._started = True
            asyncio.create_task(self._run_lifespan())
            await self._ready_event.wait()

        await self.asgi_app(scope, receive, send)

app = VercelServerlessASGI(raw_app)
