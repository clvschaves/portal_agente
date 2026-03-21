"""Configuration management for ser-aluno-mock-mcp."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_prefix="",
        extra="ignore",  # ignora variáveis desconhecidas no .env
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8081

    # Keycloak OAuth (para validação de tokens recebidos pelo MCP server)
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "sereduc-mcps"
    keycloak_client_id: str = "ser-mcp-client"
    keycloak_client_secret: str = ""

    # Aliases diretos (usados por agent_service e student_support_agent via os.environ)
    realm: str = "sereduc-mcps"
    client_id: str = "ser-mcp-client"
    client_secret: str = ""
    openai_api_key: str = ""
    mcp_url: str = "http://localhost:8081/mcp"

    # Modo de desenvolvimento — bypassa Keycloak localmente
    dev_mode: bool = False

    # Mock database file
    database_file: str = "database.json"


settings = Settings()