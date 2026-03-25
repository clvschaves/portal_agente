import os
import json
import requests
import autogen
from typing import Annotated, Dict, Any
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()


# Configuração — lida de variáveis de ambiente (.env)
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
REALM = os.environ.get("REALM", "sereduc-mcps")
CLIENT_ID = os.environ.get("CLIENT_ID", "ser-mcp-client")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "")

MCP_URL = os.environ.get("MCP_URL", "http://localhost:8081/mcp")

# Mock data (dados de demonstração — podem ser sobrescritos via env em produção)
RA = os.environ.get("DEMO_RA", "01493115")
COLIGADA = int(os.environ.get("DEMO_COLIGADA", "1"))
HABILITACAO = int(os.environ.get("DEMO_HABILITACAO", "18486"))

# Autogen Config (OPENAI_API_KEY obrigatória no ambiente)
_openai_key = os.environ.get("OPENAI_API_KEY", "")
if not _openai_key:
    raise EnvironmentError("OPENAI_API_KEY não está definida. Configure no arquivo .env.")

config_list = [
    {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
        "api_key": _openai_key
    }
]

def get_access_token() -> str:
    """Obtém um bearer token do Keycloak."""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

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

# --- Ferramentas para o Agente ---

def get_aluno_dados() -> str:
    """Obtém os dados pessoais básicos do aluno (telefone, email, endereço)."""
    try:
        res = call_mcp("resources/read", {
            "uri": "aluno:dados",
            "arguments": {
                "codColigada": COLIGADA,
                "ra": RA
            }
        })
        contents = res.get("result", {}).get("contents", [])
        return contents[0].get("text", "Nenhum dado encontrado") if contents else "Nenhum dado encontrado"
    except Exception as e:
        return f"Erro ao consultar dados: {str(e)}"

def get_aluno_disciplinas() -> str:
    """Obtém as disciplinas do aluno incluindo notas e faltas."""
    try:
        res = call_mcp("resources/read", {
            "uri": "aluno:disciplinas",
            "arguments": {
                "ra": RA,
                "idHabilitacaoFilial": HABILITACAO,
                "codColigada": COLIGADA,
                "retornarNotasFaltas": True
            }
        })
        contents = res.get("result", {}).get("contents", [])
        return contents[0].get("text", "Nenhuma disciplina encontrada") if contents else "Nenhuma disciplina encontrada"
    except Exception as e:
        return f"Erro ao consultar disciplinas: {str(e)}"

def get_aluno_summary() -> str:
    """Obtém um sumário geral do aluno (dados pessoais, cursos, disciplinas totais)."""
    try:
        res = call_mcp("tools/call", {
            "name": "get_aluno_summary",
            "arguments": {
                "ra": RA,
                "codColigada": COLIGADA,
                "idHabilitacaoFilial": HABILITACAO,
                "includeNotasFaltas": True
            }
        })
        contents = res.get("result", {}).get("content", [])
        return contents[0].get("text", "Nenhum resumo encontrado") if contents else "Nenhum resumo encontrado"
    except Exception as e:
        return f"Erro ao consultar resumo: {str(e)}"


def build_agent() -> autogen.AssistantAgent:
    llm_config = {
        "config_list": config_list,
        "timeout": 120,
    }

    system_message = (
        "Você é um agente de atendimento ao aluno (virtual assistant) da instituição SerEduc. "
        "Seu nome é 'Ser Humanozinho' ou pode se apresentar de forma criativa. "
        "Você deve se comunicar com uma LINGUAGEM JOVIAL, AMENA e ACOLHEDORA. "
        "Utilize TÉCNICAS DE PSICOLOGIA COGNITIVA no atendimento: seja empático, valide os sentimentos e frustrações do aluno, "
        "pratique reforço positivo para notas boas e reenquadramento (reframing) positivo para notas não tão boas ou faltas altas, "
        "incentivando-o a não desistir e oferecendo suporte. Respire fundo e dê respostas curtas e claras. "
        "Você tem acesso a recursos para checar os dados do aluno cadastrado, suas disciplinas, notas e faltas, e um resumo geral. "
        "Se perguntarem notas ou faltas, utilize as ferramentas disponíveis chamando 'get_aluno_disciplinas' ou 'get_aluno_summary' "
        "para consultar as informações no sistema antes de responder."
    )

    support_agent = autogen.AssistantAgent(
        name="SuporteAlunoAgent",
        system_message=system_message,
        llm_config=llm_config,
    )

    return support_agent

def main():
    support_agent = build_agent()
    
    # User object
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",  # Never ask human in automated test
        max_consecutive_auto_reply=3,  # Run automatically
        code_execution_config=False,
    )
    
    # Registers executor and caller
    autogen.agentchat.register_function(
        get_aluno_dados, caller=support_agent, executor=user_proxy, name="get_aluno_dados", description="Obtém os dados pessoais básicos do aluno autenticado (telefone, email, endereço)."
    )
    autogen.agentchat.register_function(
        get_aluno_disciplinas, caller=support_agent, executor=user_proxy, name="get_aluno_disciplinas", description="Obtém as disciplinas do aluno atual no semestre. INCLUI INFORMAÇÕES CRÍTICAS SOBRE SUAS NOTAS E FALTAS atuais."
    )
    autogen.agentchat.register_function(
        get_aluno_summary, caller=support_agent, executor=user_proxy, name="get_aluno_summary", description="Obtém o resumo acadêmico inteiro do aluno autenticado, com cursos e quantidade de disciplinas matriculadas."
    )

    print("Iniciando chat com o suporte...")
    
    # Test message queries:
    chat_result = user_proxy.initiate_chat(
        support_agent,
        message="Oi, tô super preocupado. Quais são as minhas notas e faltas nesse semestre? Não sei se vou passar...",
        summary_method="last_msg"
    )
    
    print("\n[RESULTADO DO ATENDIMENTO]")
    print(chat_result.summary)

if __name__ == "__main__":
    main()
