import streamlit as st
import memory_service
import logging
from dotenv import load_dotenv
from api.services.agent_service import run_chat_sync

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StreamlitApp")

# Inicializar Banco de Memória SQLite
memory_service.init_db()

# Mock data
RA = "01493115"
COLIGADA = 1
HABILITACAO = 18486

# --- Streamlit UI ---
st.set_page_config(page_title="Sofia 🎓", page_icon="🎓")

st.title("🎓 Sofia - Atendimento SerEduc")
st.markdown("👋 *Oi! Eu sou a Sofia, Me pergunte sobre suas notas, faltas, ou converse comigo sobre o semestre!*")

with st.sidebar:
    st.header("🧠 Módulo de Memória")
    st.markdown(f"**Aluno Atual (RA):** {RA}")
    st.info(memory_service.get_student_profile(RA))
    st.caption("O perfil é atualizado silenciosamente em background a cada interação.")
    
    st.markdown("---")
    if st.button("🗑️ Limpar Dossiê e Conversa (Reset)"):
        memory_service.clear_student_profile(RA)
        st.session_state.messages = []
        st.rerun()

# Inicializa estado da conversa
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra histórico de conversa na interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Saudação Proativa Autônoma ---
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        with st.spinner("A Sofia está lendo o seu perfil para te atender... 🧠"):
            try:
                reply_text, _ = run_chat_sync(
                    prompt="",
                    chat_context="",
                    ra=RA,
                    coligada=COLIGADA,
                    habilitacao=HABILITACAO,
                    is_initial=True
                )
            except Exception as e:
                reply_text = f"Oi! Houve um problema ao iniciar: {e}"

            st.markdown(reply_text)
            st.session_state.messages.append({"role": "assistant", "content": reply_text})

# Captura novo input de chat
prompt = st.chat_input("Ex: 'Estou com medo das minhas faltas nessa disciplina...'")
if prompt:
    # Adiciona a mensagem do usuário no chat UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Spinner de Loading
    with st.chat_message("assistant"):
        with st.spinner("A Sofia e seu Gerente estão analisando a resposta... 🧠"):
            try:
                chat_context = ""
                for m in st.session_state.messages[:-1]:
                    chat_context += f"{m['role']}: {m['content']}\\n"

                reply_text, internal_discussion = run_chat_sync(
                    prompt=prompt,
                    chat_context=chat_context,
                    ra=RA,
                    coligada=COLIGADA,
                    habilitacao=HABILITACAO,
                    is_initial=False
                )
                
                with st.expander("Ver discussão interna dos Agentes 🧠"):
                    for msg in internal_discussion:
                        st.markdown(f"**{msg.get('name', 'Agente')}**: {msg.get('content', '')}")
                        
            except Exception as e:
                reply_text = f"Opa, tive um problema técnico aqui: {str(e)}"

        # Renderiza a resposta do assistente
        st.markdown(reply_text)
        st.session_state.messages.append({"role": "assistant", "content": reply_text})
