from app.services.aluno_mock_service import AlunoMockService
import memory_service
import os
from dotenv import load_dotenv

load_dotenv()

config_list_mini = [{
    "model": "gpt-4o-mini",
    "api_key": os.environ.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
}]
RA = "01493115"
chat_history = "Aluno diz: Quero trancar tudo!\nSofia diz: Poxa vida! Vamos conversar primeiro, o que houve?"

print("--- INICIANDO UPDATE ---")
memory_service.update_profile_with_llm(RA, chat_history, config_list_mini)

print("--- OBTENDO DADO SALVO ---")
print(memory_service.get_student_profile(RA))
