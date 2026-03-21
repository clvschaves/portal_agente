import sqlite3
import autogen
import logging
from typing import List, Dict, Any

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryService")

DB_PATH = 'aluno_memory.db'

def init_db():
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                ra TEXT PRIMARY KEY,
                dossie TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS chat_jobs (
                job_id TEXT PRIMARY KEY,
                ra TEXT,
                status TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def create_job(job_id: str, ra: str):
    """Cria um novo job assíncrono com status pending."""
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO chat_jobs (job_id, ra, status, result)
            VALUES (?, ?, 'pending', null)
        ''', (job_id, ra))
        conn.commit()

def update_job(job_id: str, status: str, result: str = None):
    """Atualiza o status de um job assíncrono longo (ex: 'completed', 'failed')."""
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE chat_jobs 
            SET status = ?, result = ?
            WHERE job_id = ?
        ''', (status, result, job_id))
        conn.commit()

def get_job(job_id: str) -> Dict[str, Any]:
    """Retorna o status atual de um job pelo id."""
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT job_id, ra, status, result, created_at FROM chat_jobs WHERE job_id = ?', (job_id,))
        row = c.fetchone()
        
    if row:
        return {
            "job_id": row[0],
            "ra": row[1],
            "status": row[2],
            "result": row[3],
            "created_at": row[4]
        }
    return None

def get_student_profile(ra: str) -> str:
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT dossie FROM student_profiles WHERE ra = ?', (ra,))
        row = c.fetchone()
    return row[0] if row else "Nenhum perfil prévio encontrado. Este é o primeiro contato do aluno."

def save_student_profile(ra: str, dossie: str):
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO student_profiles (ra, dossie)
            VALUES (?, ?)
            ON CONFLICT(ra) DO UPDATE SET dossie = excluded.dossie
        ''', (ra, dossie))
        conn.commit()

def update_profile_with_llm(ra: str, chat_history: str, config_list: List[Dict[str, Any]]):
    old_profile = get_student_profile(ra)
    
    llm_config = {"config_list": config_list, "timeout": 120}
    
    profiler = autogen.AssistantAgent(
        name="AnalistaComportamental",
        system_message="Você é o Analista Comportamental do time SerEduc. Sua função é ler o histórico e atualizar o dossiê psicológico e acadêmico do aluno. Retorne APENAS o texto atualizado do dossiê, sem saudações.",
        llm_config=llm_config
    )
    user = autogen.UserProxyAgent(
        name="Sistema",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False
    )
    
    prompt = f"""
    [PERFIL ATUAL DO ALUNO (RA: {ra})]
    {old_profile}
    
    [NOVA INTERAÇÃO / HISTÓRICO RECENTE]
    {chat_history}
    
    Sua tarefa: Reescreva o perfil do aluno de forma clara. 
    1. Atualize as dores principais, sentimentos demonstrados, características marcantes e estilo de conversa. 
    2. CRIE UMA SEÇÃO OBRIGATÓRIA chamada [GANCHO PARA O PRÓXIMO CONTATO], com uma sugestão EXATA do que a Atendente deve perguntar ou comentar da próxima vez que ele logar (ex: "Perguntar se a crise de ansiedade com matemática passou").
    Lembre-se de manter o histórico consolidado. Retorne SOMENTE o texto do novo dossiê.
    """
    
    try:
        logger.info(f"[Memória] Iniciando profiling via LLM para {ra}...")
        res = user.initiate_chat(profiler, message=prompt, summary_method="last_msg")
        
        # O mesmo bug do Streamlit pode acontecer aqui, o autogen pode terminar com mensagem vazia
        new_profile = ""
        if hasattr(res, 'chat_history'):
            for msg in reversed(res.chat_history):
                # Ignora as mensagens que nós mesmos mandamos pro LLM (Sistema/user)
                if msg.get("name") == "Sistema" or msg.get("role") == "user":
                    continue
                
                content = str(msg.get("content", ""))
                if "[GANCHO PARA O PRÓXIMO CONTATO]" in content or content.strip():
                    # We just take the whole content if it has some substance
                    new_profile = content.replace("TERMINATE.", "").replace("TERMINATE", "").strip()
                    if new_profile:
                        break
        
        if not new_profile:
            new_profile = getattr(res, "summary", "").replace("TERMINATE.", "").replace("TERMINATE", "").strip()
            
        if new_profile:
            save_student_profile(ra, new_profile)
            logger.info(f"[Memória] Perfil do aluno {ra} atualizado com sucesso! Tamanho: {len(new_profile)} chars")
        else:
            logger.warning(f"[Memória] LLM não retornou nenhum perfil válido para o RA {ra}. Chat history: {res.chat_history}")
            
    except Exception as e:
        logger.error(f"[Memória] Erro ao atualizar perfil do aluno {ra}: {e}", exc_info=True)

def clear_student_profile(ra: str):
    with sqlite3.connect(DB_PATH, timeout=10.0, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM student_profiles WHERE ra = ?', (ra,))
        conn.commit()
    logger.info(f"[Memória] Perfil do aluno {ra} APAGADO com sucesso!")
