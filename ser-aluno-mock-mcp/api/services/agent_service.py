import os
import json
from pathlib import Path

# Directory where prompts are stored
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
import requests
import autogen
import logging
from typing import Dict, Any, Tuple
import threading
import asyncio
from dotenv import load_dotenv

# Assuming memory_service is accessible from the api.services package
from api.services import memory_service
from api.services import vector_memory_service

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()


logger = logging.getLogger("AgentService")

# --- Autogen Config ---
_openai_key = os.environ.get("OPENAI_API_KEY")
if not _openai_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")

config_list = [
    {
        "model": "gpt-4o",
        "api_key": _openai_key
    }
]

config_list_mini = [
    {
        "model": "gpt-4o-mini",
        "api_key": _openai_key
    }
]

# --- Keycloak & MCP Config — lidos de variáveis de ambiente (.env) ---
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.environ.get("REALM", "sereduc-mcps")
CLIENT_ID = os.environ.get("CLIENT_ID", "ser-mcp-client")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")
MCP_URL = os.environ.get("MCP_URL", "http://localhost:8081/mcp")

# Cache token manually for non-Streamlit contexts
_token_cache = {"token": None, "expires_at": 0}

def get_access_token() -> str:
    """Obtém um bearer token do Keycloak (ou token fake em DEV_MODE)."""
    import time
    
    # DEV_MODE: skip Keycloak authentication
    dev_mode = os.environ.get("DEV_MODE", "false").lower() == "true"
    if dev_mode:
        logger.warning(f"DEV_MODE=true: usando token fake para chamar MCP local na URL {MCP_URL}")
        return "dev-mode-fake-token"
    
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
        
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    logger.info(f"Obtendo token real do Keycloak na url {token_url} (client: {CLIENT_ID})")
    try:
        response = requests.post(token_url, data=payload, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"FALHA CRITICA ao tentar autenticar no Keycloak {token_url}: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Response data: {e.response.text}")
        raise
        
    data = response.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 300) - 10
    return _token_cache["token"]

def call_mcp(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Chama a API do MCP Server autenticado com JWT."""
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    logger.info(f"Chamando MCP Server url={MCP_URL} method={method}")
    try:
        response = requests.post(MCP_URL, json=data, headers=headers, timeout=25)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"FALHA CRITICA ao chamar o MCP Server ({MCP_URL}) - method: {method}")
        logger.error(f"Erro original: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Status: {e.response.status_code} | Body raw: {e.response.text}")
        raise
    return response.json()


def init_autogen(ra: str, semantic_memory: str, coligada: int, habilitacao: int):
    llm_config = {
        "config_list": config_list, 
        "timeout": 120,
        "temperature": 0.0,
        "seed": 42
    }
    
    llm_config_mini = {
        "config_list": config_list_mini, 
        "timeout": 120,
        "temperature": 0.0,
        "seed": 42
    }

    perfil_atual = memory_service.get_student_profile(ra)
    # Detectar se é primeiro contato (sem histórico real salvo)
    is_first_contact = "Nenhum perfil prévio encontrado" in perfil_atual

    if is_first_contact:
        contexto_memoria = (
            "[SITUAÇÃO]: Este é o PRIMEIRO CONTATO do aluno com a Sofia. NÃO existe histórico anterior. "
            "Você NUNCA conversou com este aluno antes. PROIBIDO mencionar conversas passadas."
        )
        if semantic_memory:
            contexto_memoria += f"\n\n[MEMÓRIAS SOLTAS RECUPERADAS (RAG)]\n{semantic_memory}"
            
        instrucao_gerente_memoria = (
            "ATENÇÃO CRÍTICA: Este é o PRIMEIRO CONTATO. NÃO existe histórico anterior. "
            "NUNCA mencione conversas passadas, metas anteriores ou qualquer assunto de interações prévias. "
            "Se for saudação inicial, a Sofia deve se apresentar brevemente como assistente da SerEduc e perguntar como pode ajudar."
        )
    else:
        contexto_memoria = (
            f"[MEMÓRIA DE LONGO PRAZO - PERFIL DO ALUNO]\n{perfil_atual}"
        )
        if semantic_memory:
            contexto_memoria += f"\n\n[MEMÓRIA EPISÓDICA SEMÂNTICA RELEVANTE PARA ESTA PERGUNTA (RAG)]\n{semantic_memory}"
            
        instrucao_gerente_memoria = (
            "Se houver um [GANCHO PARA O PRÓXIMO CONTATO] no perfil, use-o naturalmente na conversa."
        )

        # Carregar prompts externos (Protocolo N2N)
    with open(PROMPTS_DIR / "atendente.md", "r", encoding="utf-8") as f:
        atendente_prompt_template = f.read()
    
    with open(PROMPTS_DIR / "gerente.md", "r", encoding="utf-8") as f:
        gerente_prompt_template = f.read()

    atendente = autogen.AssistantAgent(
        name="Atendente",
        system_message=atendente_prompt_template.format(contexto_memoria=contexto_memoria),
        llm_config=llm_config,
    )

    gerente = autogen.AssistantAgent(
        name="Gerente",
        system_message=gerente_prompt_template.format(instrucao_gerente_memoria=instrucao_gerente_memoria),
        llm_config=llm_config_mini,
    )

    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        is_termination_msg=lambda msg: "TERMINATE" in str(msg.get("content", "")).upper(),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=4,
        code_execution_config=False,
    )

    def get_aluno_dados() -> str:
        try:
            res = call_mcp("resources/read", {
                "uri": "aluno:dados",
                "arguments": {"codColigada": coligada, "ra": ra}
            })
            contents = res.get("result", {}).get("contents", [])
            return contents[0].get("text", "Nenhum dado encontrado") if contents else "Nenhum dado encontrado"
        except Exception as e:
            logger.error(f"Erro ao consultar dados pessoais no MCP: {e}", exc_info=True)
            return "Erro técnico: Não foi possível obter os dados do aluno no momento."

    def get_aluno_disciplinas() -> str:
        try:
            res = call_mcp("resources/read", {
                "uri": "aluno:disciplinas",
                "arguments": {
                    "ra": ra,
                    "idHabilitacaoFilial": habilitacao,
                    "codColigada": coligada,
                    "retornarNotasFaltas": True
                }
            })
            contents = res.get("result", {}).get("contents", [])
            return contents[0].get("text", "Nenhuma disciplina encontrada") if contents else "Nenhuma disciplina encontrada"
        except Exception as e:
            logger.error(f"Erro ao consultar disciplinas no MCP: {e}", exc_info=True)
            return "Erro técnico: Não foi possível obter as disciplinas/notas do aluno no momento."

    def get_aluno_summary() -> str:
        try:
            res = call_mcp("tools/call", {
                "name": "get_aluno_summary",
                "arguments": {
                    "ra": ra,
                    "codColigada": coligada,
                    "idHabilitacaoFilial": habilitacao,
                    "includeNotasFaltas": True
                }
            })
            contents = res.get("result", {}).get("content", [])
            return contents[0].get("text", "Nenhum resumo encontrado") if contents else "Nenhum resumo encontrado"
        except Exception as e:
            logger.error(f"Erro ao consultar resumo academico no MCP: {e}", exc_info=True)
            return "Erro técnico: Não foi possível obter o resumo do aluno no momento."

    # Register tools
    autogen.agentchat.register_function(
        get_aluno_dados, caller=atendente, executor=user_proxy, name="get_aluno_dados", description="Obtém os dados pessoais básicos do aluno autenticado (telefone, email, endereço)."
    )
    autogen.agentchat.register_function(
        get_aluno_disciplinas, caller=atendente, executor=user_proxy, name="get_aluno_disciplinas", description="Obtém as disciplinas do aluno atual no semestre. INCLUI INFORMAÇÕES CRÍTICAS SOBRE SUAS NOTAS E FALTAS atuais."
    )
    autogen.agentchat.register_function(
        get_aluno_summary, caller=atendente, executor=user_proxy, name="get_aluno_summary", description="Obtém o resumo acadêmico inteiro do aluno autenticado, com cursos e quantidade de disciplinas matriculadas."
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, atendente, gerente],
        messages=[],
        max_round=6,
        speaker_selection_method="auto"
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    return manager, user_proxy


def parse_message_for_user(content: str) -> str:
    """Extrai apenas a parte destinada ao aluno de um texto completo."""
    if not content:
        return ""
    if "[MENSAGEM AO ALUNO]" in content:
        parts = content.split("[MENSAGEM AO ALUNO]")
        text = parts[-1].strip()
        text = text.lstrip(":")
        text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
        return text
    if "[DECISÃO]" in content:
        parts = content.split("[DECISÃO]")
        text_after = parts[-1].strip()
        if "\\n" in text_after:
            text_after = text_after.split("\\n", 1)[1].strip()
        else:
            text_after = text_after.replace("APROVAR", "").replace("REFATORAR", "").strip()
        text_after = text_after.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
        return text_after
    
    if "[PROPOSTA DE RESPOSTA]" in content:
        parts = content.split("[PROPOSTA DE RESPOSTA]")
        text = parts[-1].strip()
        text = text.lstrip(":")
        text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
        return text
        
    return ""


def extract_final_message(chat_history):
    if not chat_history:
        return ""
        
    for msg in reversed(chat_history):
        content = str(msg.get("content", ""))
        name = msg.get("name", "")
        
        parsed = parse_message_for_user(content)
        if parsed:
            return parsed
            
        if name == "Gerente" and "TERMINATE" in content:
             reply_text = content.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
             if reply_text: return reply_text
             
    return ""


def run_chat_sync(prompt: str, chat_context: str, ra: str, session_id: str, coligada: int, habilitacao: int, is_initial: bool = False):
    """Synchronously run the chat using Autogen."""
    
    # 1. Recupera RAG Memos 
    memories = vector_memory_service.retrieve_memories(ra, prompt, top_k=5)
    semantic_memory = "\\n---\\n".join(memories) if memories else ""
    
    manager, proxy = init_autogen(ra, semantic_memory, coligada, habilitacao)
    
    if is_initial:
        if prompt.strip():
            msg_context = f"mandando a primeira mensagem: '{prompt}'. Por favor, use essa mensagem como ponto de partida juntamente com uma abordagem PROATIVA."
        else:
            msg_context = "apenas abrindo o chat (sem enviar mensagem). Por favor, inicie o contato de forma PROATIVA."
            
        full_message = f"""[SISTEMA]: O aluno acabou de iniciar a sessão {msg_context}
        
Sua tarefa imediata:
1. Responda ao aluno de forma proativa (dando boas-vindas com o nome dele obtido por `get_aluno_dados`, se necessário).
2. Se houver um gancho na memória longa, traga-o de volta rapidamente.
3. Não divague nem explique a sua arquitetura.

Atendente, processe sua análise. Gerente, garanta a qualidade e as GRUARDRAILS acadêmicas, e finalize com [MENSAGEM AO ALUNO] e TERMINATE quando pronto."""
    else:
        full_message = f"Histórico:\\n{chat_context}\\nAluno diz agora: {prompt}\\n\\nAtendente, processe sua análise. Gerente, garanta a qualidade e as GUARDRAILS acadêmicas, e finalize com [MENSAGEM AO ALUNO] e TERMINATE quando pronto."
        
    res = proxy.initiate_chat(
        manager,
        message=full_message,
        clear_history=True,
        summary_method="last_msg"
    )
    
    reply_text = ""
    internal_discussion = []
    
    if hasattr(res, 'chat_history'):
        reply_text = extract_final_message(res.chat_history)
        internal_discussion = [{"name": m.get("name", "Agente"), "content": m.get("content", "")} for m in res.chat_history]
    
    if not reply_text:
        summary_raw = getattr(res, "summary", "")
        if summary_raw:
            parsed = parse_message_for_user(str(summary_raw))
            if parsed:
                reply_text = parsed
            else:
                reply_text = str(summary_raw).replace("TERMINATE", "").strip()

    if not reply_text and is_initial:
        reply_text = "Olá! Como posso te ajudar hoje?"
    elif not reply_text:
        reply_text = "Desculpe, a gerência não conseguiu concluir a resposta a tempo."
        
    # Atualiza o perfil em background
    if prompt and reply_text and not is_initial:
        contexto_novo = f"Aluno diz: {prompt}\\nSofia diz: {reply_text}"
        
        def run_memory_update():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 1. Salva o RAG no ChromaDB
                if session_id:
                    vector_memory_service.store_memory(ra, session_id, "user", prompt)
                    vector_memory_service.store_memory(ra, session_id, "assistant", reply_text)
                    
                # 2. Atualiza Dossiê no SQLite     
                memory_service.update_profile_with_llm(ra, contexto_novo, config_list_mini)
            except Exception as e:
                logger.error(f"Erro na thread de memória: {e}")
            finally:
                loop.close()
                
        threading.Thread(target=run_memory_update).start()
        
    return reply_text, internal_discussion

async def process_chat_async(prompt: str, chat_context: str, ra: str, session_id: str, coligada: int, habilitacao: int, is_initial: bool = False):
    """Asynchronously process the chat using a thread pool to avoid blocking the event loop."""
    return await asyncio.to_thread(
        run_chat_sync,
        prompt, chat_context, ra, session_id, coligada, habilitacao, is_initial
    )
