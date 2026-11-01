import os
import asyncio
from notebooklm_tools.mcp.server import mcp
from starlette.responses import JSONResponse
from starlette.routing import Route

# Asegurar URL canónica de Gemini Notebook
if not os.environ.get("NOTEBOOKLM_BASE_URL"):
    os.environ["NOTEBOOKLM_BASE_URL"] = "https://notebook.google.com"

# Aplicación FastMCP para Streamable HTTP (stateless para serverless)
raw_app = mcp.http_app(transport="streamable-http", stateless_http=True, path="/mcp")

# Ruta de verificación de estado
async def health_check(request):
    return JSONResponse({
        "status": "online",
        "service": "NotebookLM MCP Serverless",
        "mcp_endpoint": "/mcp"
    })

raw_app.routes.insert(0, Route("/", health_check))

# Wrapper para inicializar el TaskGroup de MCP en entornos Serverless (Vercel)
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
        # Normalizar path si Vercel antepone el nombre del handler
        if scope.get("type") == "http":
            path = scope.get("path", "")
            if path.startswith("/api/index.py"):
                normalized = path[len("/api/index.py"):]
                scope["path"] = normalized if normalized else "/"
            elif path.startswith("/api"):
                normalized = path[len("/api"):]
                scope["path"] = normalized if normalized else "/"

        if not self._started:
            self._started = True
            asyncio.create_task(self._run_lifespan())
            await self._ready_event.wait()

        await self.asgi_app(scope, receive, send)

app = VercelServerlessASGI(raw_app)
