import os
import sys
import uuid
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional

# Ensure the local path is reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.agent_service import run_chat_sync
import memory_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentAPI")

# Inicializa o banco de dados (perfis e jobs)
memory_service.init_db()

app = FastAPI(
    title="SerEduc Agent API - WhatsApp Webhook",
    description="API assíncrona para comunicação com o Agente de Atendimento via mensageria",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    ra: str
    message: str
    whatsapp_number: Optional[str] = None
    coligada: Optional[int] = 1
    habilitacao: Optional[int] = 1

class ChatResponse(BaseModel):
    task_id: str
    status: str
    message: str

def process_agent_task(task_id: str, prompt: str, ra: str, coligada: int, habilitacao: int):
    try:
        logger.info(f"Iniciando processamento da task {task_id} para o RA {ra}")
        
        # O agente já lê a memória de longo prazo internamente (`memory_service.get_student_profile(ra)`).
        chat_context = f"Mensagem recebida via WhatsApp."
        
        # Chama a execução síncrona do Autogen
        result = run_chat_sync(
            prompt=prompt,
            chat_context=chat_context,
            ra=ra,
            coligada=coligada,
            habilitacao=habilitacao,
            is_initial=False # Podemos alterar essa lógica se necessário
        )
        
        logger.info(f"Task {task_id} concluída com sucesso.")
        
        import json
        result_str = json.dumps(result, ensure_ascii=False) if isinstance(result, (dict, list)) else str(result)
        
        memory_service.update_job(task_id, "completed", result_str)
        
    except Exception as e:
        logger.error(f"Erro no processamento da task {task_id}: {e}", exc_info=True)
        memory_service.update_job(task_id, "failed", str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def start_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Recebe uma mensagem, gera um ID de requisição e coloca o processamento
    da IA em background. Retorna imediatamente para não dar timeout no Webhook.
    """
    task_id = str(uuid.uuid4())
    memory_service.create_job(task_id, request.ra)
    
    background_tasks.add_task(
        process_agent_task, 
        task_id=task_id, 
        prompt=request.message, 
        ra=request.ra, 
        coligada=request.coligada, 
        habilitacao=request.habilitacao
    )
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Mensagem recebida e em processamento na fila da IA."
    }

@app.get("/api/chat/{task_id}")
async def get_chat_status(task_id: str):
    """
    Consulta o status e a resposta gerada pela IA para a mensagem original (Polling).
    """
    job = memory_service.get_job(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Task_id não encontrado.")
    
    return {
        "task_id": job["job_id"],
        "ra": job["ra"],
        "status": job["status"],
        "result": job["result"],
        "created_at": job["created_at"]
    }
