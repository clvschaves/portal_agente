import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Sofia 🎓", page_icon="🎓")

st.title("🎓 Sofia - Atendimento SerEduc")
st.markdown("👋 *Oi! Eu sou a Sofia. Me pergunte sobre suas notas, faltas, ou converse comigo sobre o semestre!*")

# --- UI Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações (Mock)")
    RA = st.text_input("RA do Aluno", value="01493115")
    COLIGADA = st.number_input("Coligada", value=1, step=1)
    HABILITACAO = st.number_input("Habilitação", value=18486, step=1)
    
    st.markdown("---")
    st.header("💬 Conversas")
    
    # Busca sessões
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
        
    selected_session = st.selectbox(
        "Selecione uma sessão ou crie nova:",
        options=list(session_options.keys()),
        format_func=lambda x: session_options[x]
    )
    
    # Store selected session in state to detect changes
    if "current_session" not in st.session_state or st.session_state.current_session != selected_session:
        st.session_state.current_session = selected_session
        st.session_state.messages = []
        
        # Load history if it's an existing session
        if selected_session != "new":
            try:
                hist_resp = requests.get(f"{API_URL}/api/sessions/{selected_session}/messages")
                if hist_resp.status_code == 200:
                    st.session_state.messages = hist_resp.json()
            except:
                pass


# Mostra histórico na UI
for msg in st.session_state.messages:
    role = "assistant" if msg["role"] == "assistant" else "user"
    with st.chat_message(role):
        st.markdown(msg["content"])


# Input do usuário
if prompt := st.chat_input("Ex: 'Estou com medo das minhas faltas...'"):
    # Render user msg locally immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Send to API
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
                
                # If it was a new session, we update our local trackers
                if st.session_state.current_session == "new":
                    st.session_state.current_session = new_session_id
                    
                # Polling for task completion
                max_attempts = 120 # 2 minutes timeout
                while max_attempts > 0:
                    status_resp = requests.get(f"{API_URL}/api/chat/{task_id}")
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        if status_data["status"] == "completed":
                            result = status_data.get("result", {})
                            reply = result.get("reply", "") if isinstance(result, dict) else str(result)
                            placeholder.markdown(reply)
                            st.session_state.messages.append({"role": "assistant", "content": reply})
                            break
                        elif status_data["status"] == "failed":
                            err = f"Desculpe, a Sofia teve um problema: {status_data.get('result')}"
                            placeholder.markdown(err)
                            st.session_state.messages.append({"role": "assistant", "content": err})
                            break
                    time.sleep(2)
                    max_attempts -= 1
                    
                if max_attempts <= 0:
                    reply = "A Sofia demorou a responder, tente novamente."
                    placeholder.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
            else:
                placeholder.markdown(f"Erro na requisição: {post_resp.status_code} - {post_resp.text}")
        except Exception as e:
            placeholder.markdown(f"Opa, tive um problema técnico: {str(e)}")
            
        st.rerun()  # reload to show newly created session in the sidebar
