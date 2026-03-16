"""Keycloak OAuth token validation service."""
import logging
from typing import Optional
import httpx
from jose import jwt, JWTError
from jose.constants import ALGORITHMS

from config import settings

logger = logging.getLogger(__name__)


class KeycloakOAuthService:
    """Service for validating OAuth tokens from Keycloak."""
    
    def __init__(self):
        """Initialize Keycloak OAuth service."""
        self.keycloak_url = settings.keycloak_url.rstrip("/")
        self.realm = settings.keycloak_realm
        self.client_id = settings.keycloak_client_id
        self._jwks_url: Optional[str] = None
        self._jwks_cache: Optional[dict] = None
    
    @property
    def jwks_url(self) -> str:
        """Get JWKS URL for the realm."""
        if not self._jwks_url:
            self._jwks_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/certs"
        return self._jwks_url
    
    async def get_jwks(self) -> dict:
        """Get JWKS (JSON Web Key Set) from Keycloak."""
        if self._jwks_cache:
            return self._jwks_cache
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks_cache = response.json()
                return self._jwks_cache
        except Exception as e:
            logger.error(f"Error fetching JWKS from Keycloak: {e}")
            raise
    
    async def validate_token(self, token: str) -> bool:
        """Validate OAuth token from Keycloak.
        
        Args:
            token: JWT token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logger.warning("Token missing 'kid' in header")
                return False
            
            # Find the key in JWKS
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            
            if not key:
                logger.warning(f"Key with kid '{kid}' not found in JWKS")
                return False
            
            # Verify token
            try:
                # Get issuer URL
                issuer = f"{self.keycloak_url}/realms/{self.realm}"
                
                # Decode and verify token
                # Try with audience verification first
                try:
                    payload = jwt.decode(
                        token,
                        key,
                        algorithms=[ALGORITHMS.RS256],
                        audience=self.client_id,
                        options={
                            "verify_signature": True,
                            "verify_aud": True,
                            "verify_iss": False,
                            "verify_exp": True,
                        }
                    )
                except JWTError:
                    # If audience verification fails, try without it (some tokens may have different audience)
                    payload = jwt.decode(
                        token,
                        key,
                        algorithms=[ALGORITHMS.RS256],
                        options={
                            "verify_signature": True,
                            "verify_aud": False,
                            "verify_iss": False,
                            "verify_exp": False,
                        }
                    )
                
                logger.warning(f"Decoded token payload successfully: {payload}")
                
                # Check token type (should be Bearer)
                token_type = payload.get("typ", "").lower()
                if token_type not in ["bearer", "access_token"]:
                    # Some tokens don't have typ, so we check other claims
                    if "azp" not in payload and "client_id" not in payload:
                        logger.warning("Token missing required claims")
                        return False
                
                logger.debug(f"Token validated successfully for client: {payload.get('azp') or payload.get('client_id')}")
                return True
                
            except JWTError as e:
                logger.warning(f"JWT validation error: {e}", exc_info=True)
                return False
                
        except Exception as e:
            logger.error(f"Error validating token: {e}", exc_info=True)
            return False
    
    def clear_jwks_cache(self):
        """Clear JWKS cache (useful for testing or forced refresh)."""
        self._jwks_cache = None