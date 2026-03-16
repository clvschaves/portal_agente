"""Main FastAPI application for ser-aluno-mock-mcp."""
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import settings
from app.services.keycloak_oauth_service import KeycloakOAuthService
from app.services.aluno_mock_service import AlunoMockService
from app.resources import ResourceHandler
from app.tools import ToolHandler
from app.middleware.auth_middleware import BearerTokenMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize services
keycloak_oauth_service = KeycloakOAuthService()
aluno_service = AlunoMockService()
resource_handler = ResourceHandler(aluno_service)
tool_handler = ToolHandler(aluno_service)

# Create FastAPI app
app = FastAPI(title="Ser Aluno Mock MCP", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bearer token authentication middleware
app.add_middleware(BearerTokenMiddleware, keycloak_oauth_service=keycloak_oauth_service)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting ser-aluno-mock-mcp server...")
    
    # Test Keycloak OAuth connection by fetching JWKS
    try:
        await keycloak_oauth_service.get_jwks()
        logger.info("Successfully connected to Keycloak OAuth")
    except Exception as e:
        logger.error(f"Failed to connect to Keycloak OAuth: {e}")
        raise Exception("Failed to connect to Keycloak OAuth")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ser-aluno-mock-mcp server...")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "mode": "mock", "database": settings.database_file}


@app.get("/mcp")
async def mcp_info(request: Request):
    """MCP discovery endpoint with optional SSE support."""
    accept_header = request.headers.get("Accept", "")
    wants_sse = "text/event-stream" in accept_header.lower()
    
    logger.info(f"GET /mcp - Accept: {accept_header}, WantsSSE: {wants_sse}")
    
    if wants_sse:
        # SSE connection for discovery/streaming
        import uuid
        async def event_stream():
            connection_id = str(uuid.uuid4())
            yield f"event: connected\ndata: {{\"status\":\"connected\",\"connectionId\":\"{connection_id}\",\"mode\":\"mock\"}}\n\n"
            
            heartbeat_count = 0
            while True:
                await asyncio.sleep(30)  # 30 seconds
                heartbeat_count += 1
                yield f"event: heartbeat\ndata: {{\"count\":{heartbeat_count}}}\n\n"
        
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    # JSON response for discovery
    return {
        "protocol": "mcp",
        "version": "2024-11-05",
        "server": "ser-aluno-mock-mcp",
        "description": "Mock MCP Server for Ser Aluno with local database",
        "capabilities": ["resources", "tools"],
        "mode": "mock",
        "database": settings.database_file
    }


@app.get("/mcp/info")
async def mcp_detailed_info():
    """Detailed MCP server information."""
    return {
        "name": "ser-aluno-mock-mcp",
        "description": "Mock MCP Server for Ser Aluno - uses local JSON database",
        "version": "1.0.0",
        "mode": "mock",
        "database": settings.database_file,
        "resources": resource_handler.list_resources(),
        "tools": tool_handler.list_tools()
    }


@app.post("/mcp")
@app.post("/mcp/request")
async def mcp_request(request_data: dict):
    """Handle MCP JSON-RPC 2.0 requests."""
    logger.info(f"MCP Request: {request_data}")
    
    try:
        # Validate JSON-RPC 2.0 structure
        if not isinstance(request_data, dict) or "jsonrpc" not in request_data:
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 request")
        
        jsonrpc = request_data.get("jsonrpc")
        method = request_data.get("method")
        params = request_data.get("params", {})
        req_id = request_data.get("id")
        
        if jsonrpc != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")
        
        # Handle different MCP methods
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "resources": {"subscribe": False, "list": True},
                    "tools": {"list": True}
                },
                "serverInfo": {
                    "name": "ser-aluno-mock-mcp",
                    "version": "1.0.0"
                }
            }
        
        elif method == "resources/list":
            result = {"resources": resource_handler.list_resources()}
        
        elif method == "resources/read":
            uri = params.get("uri")
            arguments = params.get("arguments", {})
            
            if not uri:
                raise HTTPException(status_code=400, detail="URI is required for resources/read")
            
            try:
                content = await resource_handler.read_resource(uri, arguments)
                result = {
                    "contents": [{
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(content, ensure_ascii=False, indent=2)
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
                raise HTTPException(status_code=400, detail="Name is required for tools/call")
            
            try:
                tool_result = await tool_handler.call_tool(name, arguments)
                result = {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(tool_result, ensure_ascii=False, indent=2)
                    }]
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }
        
        logger.info(f"MCP Response: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing MCP request: {e}", exc_info=True)
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }
        return Response(
            content=json.dumps(error_response),
            status_code=500,
            media_type="application/json"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)