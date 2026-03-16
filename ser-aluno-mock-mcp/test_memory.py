import json
import logging
from memory_service import update_profile_with_llm, get_student_profile

logging.basicConfig(level=logging.INFO)

config_list_mini = [{
    "model": "gpt-4o-mini",
    "api_key": "os.environ.get("OPENAI_API_KEY", "")"
}]

# Define mock chat interaction
RA = "01493115"
chat_history = "Aluno diz: Oi! Queria saber as minhas notas e faltas. Estou bem ansioso!\nSofia diz: Olá, Lucas! Suas notas são ótimas na maioria, vamos trabalhar nessas faltas."

print("Iniciando update via LLM da Memória de longo prazo...")
update_profile_with_llm(RA, chat_history, config_list_mini)

print("---")
print("Novo perfil no SQLite:")
print(get_student_profile(RA))
