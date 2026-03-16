"""OAuth Bearer token authentication middleware."""
import logging
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.services.keycloak_oauth_service import KeycloakOAuthService

logger = logging.getLogger(__name__)


class BearerTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to validate Bearer tokens via Keycloak OAuth."""
    
    def __init__(self, app, keycloak_oauth_service: KeycloakOAuthService):
        """Initialize middleware."""
        super().__init__(app)
        self.keycloak_oauth_service = keycloak_oauth_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate Bearer token."""
        # Skip authentication for health check and info endpoints
        path = request.url.path
        method = request.method
        
        if path == "/health" or (path == "/mcp" and method == "GET") or path == "/mcp/info":
            return await call_next(request)
        
        # Extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"Missing Bearer token from {request.client.host if request.client else 'unknown'}")
            return Response(
                content='{"error":"Unauthorized","message":"Bearer token is required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        token = auth_header[7:].strip()  # Remove "Bearer " prefix
        if not token:
            logger.warning(f"Empty Bearer token from {request.client.host if request.client else 'unknown'}")
            return Response(
                content='{"error":"Unauthorized","message":"Bearer token is required"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Validate token with Keycloak OAuth
        is_valid = await self.keycloak_oauth_service.validate_token(token)
        if not is_valid:
            logger.warning(f"Invalid OAuth token from {request.client.host if request.client else 'unknown'}")
            return Response(
                content='{"error":"Unauthorized","message":"Invalid OAuth token"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
        
        # Store validated token in request state for later use
        request.state.oauth_token = token
        request.state.authenticated = True
        
        return await call_next(request)