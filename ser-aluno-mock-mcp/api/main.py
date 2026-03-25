from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.services import memory_service  # To initialize DB
from .routers import chat

# Inicializar Banco de Memória SQLite
memory_service.init_db()

app = FastAPI(
    title="Sofia Atendimento API",
    description="API RESTful assíncrona para comunicação com os agentes autônomos de atendimento (Sofia e Gerente).",
    version="1.0.0"
)

# Adicionar CORS para permitir chamadas do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")

@app.get("/health", tags=["System"])
def health_check():
    """Endpoint simplificado para verificação de disponibilidade."""
    return {"status": "ok", "message": "API rodando normal"}
