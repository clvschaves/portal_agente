import os
import sys
import uuid
import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Ensure the local path is reachable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.services.agent_service import run_chat_sync
import memory_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentAPI")

# Inicializa o banco de dados (perfis, jobs, sessoes)
memory_service.init_db()

app = FastAPI(
    title="SerEduc Agent API - WhatsApp & Web",
    description="API assíncrona com suporte a sessões para comunicação com o Agente",
    version="1.1.0"
)

class ChatRequest(BaseModel):
    ra: str
    message: str
    session_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    coligada: Optional[int] = 1
    habilitacao: Optional[int] = 1

class ChatResponse(BaseModel):
    task_id: str
    session_id: str
    status: str
    message: str

def process_agent_task(task_id: str, session_id: str, prompt: str, ra: str, coligada: int, habilitacao: int):
    try:
        logger.info(f"Iniciando processamento da task {task_id} para o RA {ra} na sessao {session_id}")
        
        # O agente já lê a memória de longo prazo internamente (`memory_service.get_student_profile(ra)`).
        
        # Puxa histórico de curto prazo (sessão)
        messages_db = memory_service.get_session_messages(session_id)
        chat_context = ""
        for m in messages_db:
            role_name = "Aluno" if m["role"] == "user" else "Sofia"
            chat_context += f"[{m['created_at']}] {role_name}: {m['content']}\\n"
            
        if not chat_context:
            chat_context = "Nenhuma mensagem anterior nesta sessão."

        # Chama a execução síncrona do Autogen
        reply_text, internal_disc = run_chat_sync(
            prompt=prompt,
            chat_context=chat_context,
            ra=ra,
            session_id=session_id,
            coligada=coligada,
            habilitacao=habilitacao,
            is_initial=False
        )
        
        logger.info(f"Task {task_id} concluída com sucesso.")
        
        # Salva a resposta do assistente no histórico da sessão
        memory_service.add_message(session_id, "assistant", reply_text)
        
        # Salvar o job
        import json
        result_dict = {
            "reply": reply_text,
            "internal_discussion": internal_disc
        }
        result_str = json.dumps(result_dict, ensure_ascii=False)
        memory_service.update_job(task_id, "completed", result_str)
        
    except Exception as e:
        logger.error(f"Erro no processamento da task {task_id}: {e}", exc_info=True)
        memory_service.update_job(task_id, "failed", str(e))

@app.post("/api/chat", response_model=ChatResponse)
async def start_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Recebe uma mensagem, vincula a uma sessão (ou cria uma) e coloca o processamento
    da IA em background. Retorna imediatamente.
    """
    session_id = request.session_id
    
    # 1. Gerenciar Sessão
    if not session_id:
        # Se for nova sessão, usamos as primeiras palavras como título (ou mockamos)
        title = request.message[:30] + "..." if len(request.message) > 30 else request.message
        session_id = memory_service.create_session(request.ra, title=title)
        
    # Salvar a mensagem do usuário no histórico da sessão
    memory_service.add_message(session_id, "user", request.message)
    
    # 2. Gerenciar Background Task
    task_id = str(uuid.uuid4())
    memory_service.create_job(task_id, request.ra)
    
    background_tasks.add_task(
        process_agent_task, 
        task_id=task_id, 
        session_id=session_id,
        prompt=request.message, 
        ra=request.ra, 
        coligada=request.coligada, 
        habilitacao=request.habilitacao
    )
    
    return {
        "task_id": task_id,
        "session_id": session_id,
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
    
    import json
    result_data = job["result"]
    if result_data and job["status"] == "completed":
        try:
            result_data = json.loads(result_data)
        except Exception:
            pass
            
    return {
        "task_id": job["job_id"],
        "ra": job["ra"],
        "status": job["status"],
        "result": result_data,
        "created_at": job["created_at"]
    }

@app.get("/api/sessions/{ra}")
async def list_sessions(ra: str):
    """Lista todas as sessões de um RA."""
    return memory_service.get_sessions_by_ra(ra)

@app.get("/api/sessions/{session_id}/messages")
async def get_session_history(session_id: str):
    """Retorna o histórico de mensagens de uma sessão específica."""
    return memory_service.get_session_messages(session_id)
