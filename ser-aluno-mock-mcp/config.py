"""Configuration management for ser-aluno-mock-mcp."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix=""
    )
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8081  # Different port to avoid conflicts
    
    # Keycloak OAuth configuration (para validação de tokens recebidos)
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "sereduc-mcps"
    keycloak_client_id: str = "ser-mcp-client"
    
    # Mock database file
    database_file: str = "database.json"


settings = Settings()