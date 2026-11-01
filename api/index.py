import os
from notebooklm_tools.mcp.server import mcp
from starlette.responses import JSONResponse
from starlette.routing import Route

# Asegurar URL canónica de Gemini Notebook
if not os.environ.get("NOTEBOOKLM_BASE_URL"):
    os.environ["NOTEBOOKLM_BASE_URL"] = "https://notebook.google.com"

# Aplicación ASGI estándar para Vercel Serverless
app = mcp.http_app(transport="streamable-http", stateless_http=True, path="/mcp")

# Ruta raíz para verificación de estado en navegador y monitores
async def health_check(request):
    return JSONResponse({
        "status": "online",
        "service": "NotebookLM MCP Serverless",
        "mcp_endpoint": "/mcp"
    })

app.routes.insert(0, Route("/", health_check))
