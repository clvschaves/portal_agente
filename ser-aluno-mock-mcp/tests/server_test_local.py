"""
Servidor MCP local de teste com autenticação bypassada.
Utilizado para validar a lógica MCP sem precisar do Keycloak/Docker.
"""
import json
import logging
import asyncio
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Definir variáveis de ambiente antes de importar config
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8082")
os.environ.setdefault("KEYCLOAK_URL", "http://localhost:8080")
os.environ.setdefault("KEYCLOAK_REALM", "sereduc-mcps")
os.environ.setdefault("KEYCLOAK_CLIENT_ID", "ser-mcp-client")
os.environ.setdefault("DATABASE_FILE", "database.json")

from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import settings
from app.services.aluno_mock_service import AlunoMockService
from app.resources import ResourceHandler
from app.tools import ToolHandler

logging.basicConfig(level=logging.WARNING)  # Menos verboso para testes
logger = logging.getLogger(__name__)

# ─── Middleware de auth bypassado ──────────────────────────────────────────

class BypassAuthMiddleware(BaseHTTPMiddleware):
    """Bypass de autenticação para testes locais.
    Aceita qualquer Bearer token como válido.
    Rejeita requisições sem token (para testar segurança).
    """
    # Endpoints que não precisam de auth
    PUBLIC_PATHS = {"/health", "/mcp", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # Endpoints públicos liberados
        if method == "GET" and path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Para POST /mcp e GET /mcp/info — exige Bearer token
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"}
            )
        # Token presente: aceita qualquer valor (bypass)
        return await call_next(request)


# ─── Serviços e App ───────────────────────────────────────────────────────

aluno_service = AlunoMockService()
resource_handler = ResourceHandler(aluno_service)
tool_handler = ToolHandler(aluno_service)

app = FastAPI(title="Ser Aluno Mock MCP (Test Mode)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BypassAuthMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "mock", "database": settings.database_file}


@app.get("/mcp")
async def mcp_info(request: Request):
    accept_header = request.headers.get("Accept", "")
    if "text/event-stream" in accept_header.lower():
        import uuid
        async def event_stream():
            cid = str(uuid.uuid4())
            yield f'event: connected\ndata: {{"status":"connected","connectionId":"{cid}","mode":"mock"}}\n\n'
            while True:
                await asyncio.sleep(30)
                yield 'event: heartbeat\ndata: {"count":1}\n\n'
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    return {
        "protocol": "mcp",
        "version": "2024-11-05",
        "server": "ser-aluno-mock-mcp",
        "description": "Mock MCP Server for Ser Aluno (TEST MODE)",
        "capabilities": ["resources", "tools"],
        "mode": "mock",
        "database": settings.database_file,
    }


@app.get("/mcp/info")
async def mcp_detailed_info():
    return {
        "name": "ser-aluno-mock-mcp",
        "description": "Mock MCP Server for Ser Aluno - uses local JSON database",
        "version": "1.0.0",
        "mode": "mock",
        "database": settings.database_file,
        "resources": resource_handler.list_resources(),
        "tools": tool_handler.list_tools(),
    }


@app.post("/mcp")
@app.post("/mcp/request")
async def mcp_request(request_data: dict):
    try:
        if not isinstance(request_data, dict) or "jsonrpc" not in request_data:
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 request")

        jsonrpc = request_data.get("jsonrpc")
        method = request_data.get("method")
        params = request_data.get("params", {})
        req_id = request_data.get("id")

        if jsonrpc != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")

        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {"subscribe": False, "list": True},
                    "tools": {"list": True},
                },
                "serverInfo": {"name": "ser-aluno-mock-mcp", "version": "1.0.0"},
            }
        elif method == "resources/list":
            result = {"resources": resource_handler.list_resources()}
        elif method == "resources/read":
            uri = params.get("uri")
            arguments = params.get("arguments", {})
            if not uri:
                raise HTTPException(status_code=400, detail="URI is required")
            try:
                content = await resource_handler.read_resource(uri, arguments)
                result = {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content, ensure_ascii=False, indent=2),
                    }]
                }
            except KeyError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        elif method == "tools/list":
            result = {"tools": tool_handler.list_tools()}
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                raise HTTPException(status_code=400, detail="Name is required")
            try:
                tool_result = await tool_handler.call_tool(name, arguments)
                result = {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(tool_result, ensure_ascii=False, indent=2),
                    }]
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return Response(
            content=json.dumps({
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {"code": -32603, "message": "Internal error", "data": str(e)},
            }),
            status_code=500,
            media_type="application/json",
        )


if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor MCP em modo de teste local (porta 8082)...")
    print("   Auth: BYPASSADA (aceita qualquer Bearer token)")
    print("   Database:", settings.database_file)
    uvicorn.run(app, host="0.0.0.0", port=8082, log_level="warning")
