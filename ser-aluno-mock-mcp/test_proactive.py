import os
import json
import autogen
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

config_list = [{
    "model": "gpt-4o",
    "api_key": os.environ.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
}]
config_list_mini = [{
    "model": "gpt-4o-mini",
    "api_key": os.environ.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
}]

def get_aluno_dados(): return "Nome do aluno: Lucas Costa"
def get_aluno_disciplinas(): return "Nenhuma"
def get_aluno_summary(): return "Sem resumo"

llm_config = {"config_list": config_list, "timeout": 120, "temperature": 0.0, "seed": 42}
llm_config_mini = {"config_list": config_list_mini, "timeout": 120, "temperature": 0.0, "seed": 42}

atendente = autogen.AssistantAgent(
    name="Atendente",
    system_message=(
        "Você é a 'Sofia', uma atendente virtual jovial, amena e acolhedora da instituição SerEduc. "
        "Sua função principal é conversar com o aluno e usar a memória para puxar assuntos. "
        "Sempre que precisar saber quem é o aluno, USE AS FERRAMENTAS. "
        "[MEMÓRIA DE LONGO PRAZO - PERFIL DO ALUNO]\nO aluno se chama Lucas. Ele está ansioso.\n\n"
        "COMUNICAÇÃO A2A: "
        "[RACIOCÍNIO]: (...)\n"
        "[FERRAMENTAS]: (Declare)\n"
        "[PROPOSTA DE RESPOSTA]: (...)"
    ),
    llm_config=llm_config,
)

gerente = autogen.AssistantAgent(
    name="Gerente",
    system_message=(
        "Você é o Gerente de Qualidade. Sua função é avaliar a proposta da 'Atendente'. "
        "[ANÁLISE]: (...)\n"
        "[DECISÃO]: (...)\n"
        "[MENSAGEM AO ALUNO]: (Versão final polida. Encerre imediatamente após com a palavra TERMINATE.)"
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

autogen.agentchat.register_function(get_aluno_dados, caller=atendente, executor=user_proxy, name="get_aluno_dados", description="Obtém os dados do aluno.")
autogen.agentchat.register_function(get_aluno_disciplinas, caller=atendente, executor=user_proxy, name="get_aluno_disciplinas", description="Obtém disciplinas.")
autogen.agentchat.register_function(get_aluno_summary, caller=atendente, executor=user_proxy, name="get_aluno_summary", description="Obtém resumo.")

groupchat = autogen.GroupChat(agents=[user_proxy, atendente, gerente], messages=[], max_round=12, speaker_selection_method="auto")
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

prompt_inicial = "[SISTEMA]: O aluno acabou de abrir o chat. Por favor, inicie a conversa PROATIVAMENTE. Consulte os dados dele usando `get_aluno_dados` para descobrir e chamá-lo pelo nome, e se houver um [GANCHO PARA O PRÓXIMO CONTATO] na memória, puxe esse assunto imediatamente para demonstrar empatia."

print("Iniciando chat...")
res = user_proxy.initiate_chat(manager, message=prompt_inicial, clear_history=True, summary_method="last_msg")
print("\n--- RESUMO ---")
print(res.summary)
