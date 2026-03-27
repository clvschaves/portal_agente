import os
import sys
import uuid
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente imediatamente no início
load_dotenv(os.path.join(os.getcwd(), ".env"))

import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Adapts the path for imports
sys.path.append(os.getcwd())

from api.services.agent_service import run_chat_sync
from api.services import memory_service

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
    message: str = ""
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
        user_msg_count = 0
        for m in messages_db:
            role_name = "Aluno" if m["role"] == "user" else "Sofia"
            chat_context += f"[{m['created_at']}] {role_name}: {m['content']}\n"
            if m["role"] == "user":
                user_msg_count += 1
            
        if not chat_context:
            chat_context = "Nenhuma mensagem anterior nesta sessão."

        is_initial = (user_msg_count <= 1)

        # Chama a execução síncrona do Autogen
        reply_text, internal_disc = run_chat_sync(
            prompt=prompt,
            chat_context=chat_context,
            ra=ra,
            session_id=session_id,
            coligada=coligada,
            habilitacao=habilitacao,
            is_initial=is_initial
        )
        
        logger.info(f"Task {task_id} concluída com sucesso.")
        
        # Salvar o raciocínio interno (thought) para que o Streamlit exiba
        if internal_disc:
            reasoning_text = ""
            for idx, d in enumerate(internal_disc):
                content = str(d.get("content", ""))
                # Se o conteudo tiver [MENSAGEM AO ALUNO], não colocar essa última parte do gerente no pensamento
                if "[MENSAGEM AO ALUNO]" in content:
                    content = content.split("[MENSAGEM AO ALUNO]")[0]
                content = content.replace("TERMINATE", "").strip()
                if content:
                    reasoning_text += f"\n\n**{d.get('name', 'Agente')}**:\n{content}"
            if reasoning_text.strip():
                memory_service.add_message(session_id, "thought", reasoning_text.strip())
        
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
        if not title.strip():
            title = "Início Proativo"
        session_id = memory_service.create_session(request.ra, title=title)
    else:
        # Se já existe sessão e o usuário mandou texto real
        if request.message.strip():
            session_info = memory_service.get_session_by_id(session_id)
            if session_info and session_info["title"] in ["", "Início Proativo", "Nova Conversa"]:
                new_title = request.message[:30] + "..." if len(request.message) > 30 else request.message
                memory_service.update_session_title(session_id, new_title)
        
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
