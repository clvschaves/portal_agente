import streamlit as st
import requests
import time
import os

API_URL = os.environ.get("API_URL", "http://agent-api:8000")

st.set_page_config(page_title="Sofia 🎓", page_icon="🎓")

st.title("🎓 Sofia - Atendimento SerEduc")
st.markdown("👋 *Oi! Eu sou a Sofia. Me pergunte sobre suas notas, faltas, ou converse comigo sobre o semestre!*")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_session" not in st.session_state:
    st.session_state.current_session = "new"

with st.sidebar:
    st.header("⚙️ Configurações (Mock)")
    RA = st.text_input("RA do Aluno", value="01493115")
    COLIGADA = st.number_input("Coligada", value=1, step=1)
    HABILITACAO = st.number_input("Habilitação", value=18486, step=1)
    
    st.markdown("---")
    st.header("💬 Conversas")
    
    sessions = []
    try:
        resp = requests.get(f"{API_URL}/api/sessions/{RA}", timeout=5)
        if resp.status_code == 200:
            sessions = resp.json()
    except Exception as e:
        st.error(f"Erro ao conectar com API (Lembre de ligar o uvicorn na porta 8000): {e}")

    session_options = {"new": "➕ Nova Conversa"}
    for s in sessions:
        session_options[s["session_id"]] = f"🗨️ {s['title']} ({s['created_at'][:10]})"
        
    options_list = list(session_options.keys())
    
    try:
        current_index = options_list.index(st.session_state.current_session)
    except ValueError:
        current_index = 0

    selected = st.selectbox(
        "Selecione uma sessão ou crie nova:",
        options=options_list,
        index=current_index,
        format_func=lambda x: session_options[x]
    )
    
    # Switch de sessão
    if selected != st.session_state.current_session:
        st.session_state.current_session = selected
        if selected == "new":
            st.session_state.messages = []
        else:
            try:
                hist_resp = requests.get(f"{API_URL}/api/sessions/{selected}/messages")
                if hist_resp.status_code == 200:
                    st.session_state.messages = hist_resp.json()
            except:
                pass
        st.rerun()

# Renderiza histórico
for msg in st.session_state.messages:
    if msg["role"] == "thought":
        with st.expander("🧐 Raciocínio Interno da IA"):
            st.markdown(msg["content"])
    else:
        role = "assistant" if msg["role"] == "assistant" else "user"
        if msg["content"].strip():
            with st.chat_message(role):
                st.markdown(msg["content"])

# Callback de chat
prompt = st.chat_input("Ex: 'Estou com medo das minhas faltas...'")

# Permite iniciar proativamente se for uma sessão nova e sem mensagens
trigger_proactive = False
if st.session_state.current_session == "new" and len(st.session_state.messages) == 0:
    if st.button("Iniciar Atendimento Proativo (Sem Mensagem)"):
        prompt = ""
        trigger_proactive = True

if prompt is not None or trigger_proactive:
    # Se não for proativo vazio, appenda o user message instantaneamente
    if prompt.strip():
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("A Sofia está pensando... 🧠")
        
        payload = {
            "ra": RA,
            "message": prompt,
            "coligada": COLIGADA,
            "habilitacao": HABILITACAO
        }
        if st.session_state.current_session != "new":
            payload["session_id"] = st.session_state.current_session
            
        try:
            post_resp = requests.post(f"{API_URL}/api/chat", json=payload)
            if post_resp.status_code == 200:
                data = post_resp.json()
                task_id = data["task_id"]
                new_session_id = data["session_id"]
                
                # Aguarda até o assistente responder (polling de 2s)
                max_attempts = 120
                completed = False
                while max_attempts > 0:
                    status_resp = requests.get(f"{API_URL}/api/chat/{task_id}")
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        if status_data["status"] == "completed":
                            completed = True
                            break
                        elif status_data["status"] == "failed":
                            completed = True
                            break
                    time.sleep(2)
                    max_attempts -= 1
                    
                if not completed:
                    st.error("A inteligência artificial demorou muito a responder.")
                
                # Fetch atualizado das mensagens pela API
                st.session_state.current_session = new_session_id
                try:
                    hist_resp = requests.get(f"{API_URL}/api/sessions/{new_session_id}/messages")
                    if hist_resp.status_code == 200:
                        st.session_state.messages = hist_resp.json()
                except:
                    pass
                    
            else:
                placeholder.markdown(f"Erro na requisição: {post_resp.status_code} - {post_resp.text}")
        except Exception as e:
            placeholder.markdown(f"Opa, tive um problema técnico: {str(e)}")
            
        # Força rerun para fixar o seletor na sessão atual via UI e renderizar final  
        st.rerun()
