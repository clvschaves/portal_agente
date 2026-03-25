import json

chat_history = [
    {"name": "Atendente", "content": "Oi, sua resposta é [PROPOSTA DE RESPOSTA]: Oi Lucas, que bom falar com você! 😊 TERMINATE"},
    {"name": "Gerente", "content": "[ANÁLISE]: Achei excelente.\n[DECISÃO]: APROVAR\nOi Lucas, que bom falar com você! Vi que estava ansioso da última vez. TERMINATE."},
    {"name": "", "content": ""}
]

reply_text = ""
for msg in reversed(chat_history):
    content = str(msg.get("content", ""))
    name = msg.get("name", "")
    
    if name == "Gerente":
        if "[MENSAGEM AO ALUNO]" in content:
            parts = content.split("[MENSAGEM AO ALUNO]")
            text = parts[-1].strip()
            text = text.lstrip(":")
            reply_text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
            if reply_text: break
        
        if "[DECISÃO]" in content:
            parts = content.split("[DECISÃO]")
            text_after_decisao = parts[-1].strip()
            if "\n" in text_after_decisao:
                text_after_decisao = text_after_decisao.split("\n", 1)[1].strip()
            reply_text = text_after_decisao.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
            if reply_text: break
            
        if "TERMINATE" in content:
            reply_text = content.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
            if reply_text: break

    if name == "Atendente" and "[PROPOSTA DE RESPOSTA]" in content and not reply_text:
        parts = content.split("[PROPOSTA DE RESPOSTA]")
        text = parts[-1].strip()
        text = text.lstrip(":")
        reply_text = text.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
        if reply_text: break

print(f"Extraction result: '{reply_text}'")
