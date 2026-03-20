import os
import json
import requests
import autogen
import logging
from typing import Dict, Any, Tuple
import threading
import asyncio
from dotenv import load_dotenv

# Assuming memory_service is accessible from the project root
import memory_service

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
    """Obtém um bearer token do Keycloak."""
    import time
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
        
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
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
    response = requests.post(MCP_URL, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def init_autogen(ra: str, coligada: int, habilitacao: int):
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

    atendente = autogen.AssistantAgent(
        name="Atendente",
        system_message=(
            "Você é a 'Sofia', uma atendente virtual jovial, amena e acolhedora da instituição SerEduc. "
            "Sua função principal é conversar de forma fluida com o aluno como se fosse humano, usando a memória de longo prazo para puxar assuntos passados. "
            "Sempre que precisar saber quem é o aluno (dados) ou quando o aluno pedir sobre notas ou faltas, USE AS FERRAMENTAS. "
            f"\\n\\n[MEMÓRIA DE LONGO PRAZO - PERFIL DO ALUNO]\\n{perfil_atual}\\n\\n"
            "COMUNICAÇÃO A2A (AGENT-TO-AGENT): Sua comunicação interna não é estocástica, deve seguir estritamente o protocolo abaixo:\\n"
            "[RACIOCÍNIO]: (Escreva seu pensamento passo-a-passo sobre o que o aluno quer e qual o gancho da memória usar)\\n"
            "[FERRAMENTAS]: (Declare quais ferramentas vai usar caso necessário)\\n"
            "[PROPOSTA DE RESPOSTA]: (O texto humanizado que você sugere enviar ao aluno)\\n"
            "Sua proposta será enviada ao Gerente para aprovação obrigatória."
        ),
        llm_config=llm_config,
    )

    gerente = autogen.AssistantAgent(
        name="Gerente",
        system_message=(
            "Você é o Gerente de Qualidade. Sua função é avaliar a proposta da 'Atendente' usando protocolo A2A. "
            "A resposta deve ser fluida, chamar o aluno pelo nome e, se houver um [GANCHO PARA O PRÓXIMO CONTATO] na memória, puxar o assunto imediatamente! "
            "Sua avaliação interna não é estocástica, siga o protocolo rígido:\\n"
            "[ANÁLISE]: (Analise criticamente a proposta da Atendente)\\n"
            "[DECISÃO]: (APROVAR ou REFATORAR)\\n"
            "[MENSAGEM AO ALUNO]: (A versão final polida direcianada ao aluno. Encerre imediatamente após com a palavra TERMINATE.)"
        ),
        llm_config=llm_config_mini,
    )

    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        is_termination_msg=lambda msg: "TERMINATE" in str(msg.get("content", "")).upper(),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
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
        max_round=12,
        speaker_selection_method="auto"
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    return manager, user_proxy


def extract_final_message(chat_history):
    reply_text = ""
    if not chat_history:
        return ""
        
    for msg in reversed(chat_history):
        content = str(msg.get("content", ""))
        name = msg.get("name", "")
        
        if name == "Gerente":
            if "[MENSAGEM AO ALUNO]" in content:
                parts = content.split("[MENSAGEM AO ALUNO]")
                text = parts[-1].strip()
                text = text.lstrip(":")
                reply_text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
                if reply_text: return reply_text
            
            if "[DECISÃO]" in content:
                parts = content.split("[DECISÃO]")
                text_after_decisao = parts[-1].strip()
                if "\\n" in text_after_decisao:
                    text_after_decisao = text_after_decisao.split("\\n", 1)[1].strip()
                else:
                    text_after_decisao = text_after_decisao.replace("APROVAR", "").replace("REFATORAR", "").strip()
                reply_text = text_after_decisao.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
                if reply_text: return reply_text
                
            if "TERMINATE" in content:
                reply_text = content.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
                if reply_text: return reply_text

        if name == "Atendente" and "[PROPOSTA DE RESPOSTA]" in content and not reply_text:
            parts = content.split("[PROPOSTA DE RESPOSTA]")
            text = parts[-1].strip()
            text = text.lstrip(":")
            reply_text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
            if reply_text: return reply_text
            
    return reply_text


def run_chat_sync(prompt: str, chat_context: str, ra: str, coligada: int, habilitacao: int, is_initial: bool = False):
    """Synchronously run the chat using Autogen."""
    manager, proxy = init_autogen(ra, coligada, habilitacao)
    
    if is_initial:
        full_message = "[SISTEMA]: O aluno acabou de abrir o chat. Por favor, inicie a conversa PROATIVAMENTE. Consulte os dados dele usando `get_aluno_dados` para descobrir e chamá-lo pelo nome, e se houver um [GANCHO PARA O PRÓXIMO CONTATO] na memória, puxe esse assunto imediatamente para demonstrar empatia."
    else:
        full_message = f"Histórico:\\n{chat_context}\\nAluno diz agora: {prompt}\\n\\nAtendente, processe via A2A. Gerente, garanta a qualidade e finalize com [MENSAGEM AO ALUNO] e TERMINATE quando pronto."
        
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
                memory_service.update_profile_with_llm(ra, contexto_novo, config_list_mini)
            except Exception as e:
                logger.error(f"Erro na thread de memória: {e}")
            finally:
                loop.close()
                
        threading.Thread(target=run_memory_update).start()
        
    return reply_text, internal_discussion

async def process_chat_async(prompt: str, chat_context: str, ra: str, coligada: int, habilitacao: int, is_initial: bool = False):
    """Asynchronously process the chat using a thread pool to avoid blocking the event loop."""
    return await asyncio.to_thread(
        run_chat_sync,
        prompt, chat_context, ra, coligada, habilitacao, is_initial
    )
