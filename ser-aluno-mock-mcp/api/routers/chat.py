from fastapi import APIRouter, HTTPException, status
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.agent_service import process_chat_async
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """
    Endpoint para conversar com a agente Sofia.
    A comunicação e rascunhos internos ocorrem via protocolo A2A com o Gerente antes da resposta final.
    """
    try:
        chat_context = ""
        for m in request.chat_history:
            chat_context += f"{m.role}: {m.content}\n"
            
        reply, internal_discussion = await process_chat_async(
            prompt=request.prompt,
            chat_context=chat_context,
            ra=request.ra,
            coligada=request.coligada,
            habilitacao=request.habilitacao,
            is_initial=request.is_initial_greeting
        )
        return ChatResponse(reply=reply, internal_discussion=internal_discussion)
    except Exception as e:
        logger.error(f"Chat execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno ao processar a conversa.")
