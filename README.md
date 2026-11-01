# NotebookLM MCP Serverless (Vercel)

Servidor MCP para conectar **Google NotebookLM** con **ChatGPT Web** ejecutándose de manera serverless 24/7 en **Vercel**.

## 🚀 Despliegue en Vercel

1. Importa este repositorio en tu cuenta de Vercel.
2. Configura las siguientes Variables de Entorno (**Environment Variables**):
   - `NOTEBOOKLM_BASE_URL`: `https://notebook.google.com`
   - `NOTEBOOKLM_COOKIES`: *(Tus cookies activas de Google)*
3. Haz clic en **Deploy**.

## 🔌 Conexión en ChatGPT

- **URL del servidor:** `https://<tu-dominio>/mcp`
- **Autenticación:** Sin autenticación
- **Transporte:** Streamable-HTTP / SSE
