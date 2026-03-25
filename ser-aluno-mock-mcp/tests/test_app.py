import json
import asyncio
from unittest.mock import MagicMock
# We just want to parse a dummy chat history to test the logic
chat_history = [
    {"content": "Oi fulano! Aqui é a sua proposta.\n[PROPOSTA DE RESPOSTA]: Oi Lucas, que bom falar com vc!"},
    {"content": "[ANÁLISE]: Achei a proposta ótima.\n[DECISÃO]: APROVADO.\n[MENSAGEM AO ALUNO]: Oi Lucas, que bom falar com você! Vi que estava ansioso da última vez. TERMINATE"},
    {"content": ""}  # Empty proxy message
]
reply_text = ""
for msg in reversed(chat_history):
    content = str(msg.get("content", ""))
    if "[MENSAGEM AO ALUNO]:" in content:
        reply_text = content.split("[MENSAGEM AO ALUNO]:")[1].replace("TERMINATE", "").strip()
        break
    elif "[PROPOSTA DE RESPOSTA]:" in content and not reply_text:
        reply_text = content.split("[PROPOSTA DE RESPOSTA]:")[1].replace("TERMINATE", "").strip()

print(f"Reply Text Extract: '{reply_text}'")
