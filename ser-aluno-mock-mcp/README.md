# Ser Aluno Mock MCP + Streamlit Agent UI

Servidor MCP (Model Context Protocol) **mock** em Python para testes e desenvolvimento com dados simulados do sistema SerEduc, integrado agora a um **Client Web no Streamlit** e uma **API Assíncrona com Memória Vetorial RAG** usando ChromaDB e SQLite.

Esta aplicação funciona tanto como um mock isolado do sistema escolar quanto como uma interface final para o Agente Autogen interagir de forma inteligente, mantendo estado cruzado de sessões.

## ✨ Características Adicionadas

- **🖥️ Streamlit Frontend**: UI responsiva via Web para falar com o agente, com separação de sessões.
- **🧠 Memória de Longo Prazo (RAG)**: O Agente busca memórias do banco vetorial local (ChromaDB) de conversas passadas para responder de forma contextual.
- **📁 Banco SQLite Local**: Gerenciamento de sessões de conversa e perfis psicológicos/acadêmicos gerados pelo LLM a cada sessão.
- **💬 Início Proativo**: O agente é capaz de puxar o assunto da última conversa sozinho se você apenas logar sem dizer nada.
- **⚡ API Assíncrona (FastAPI)**: As chamadas pesadas ao LLM rodam em jobs de background (polling do front-end) protegendo o timeout do HTTP.

---

## 🚀 Quick Start (Como instalar e rodar)

Você vai precisar instalar as novas dependências de Inteligência Artificial e Banco Vetorial.

### 1. Instalar as Dependências

```bash
# Clone e acesse o diretório
cd ser-aluno-mock-mcp

# Crie e ative seu ambiente virtual (recomendado)
python3 -m venv .venv
source .venv/bin/activate

# Instale os requisitos (incluindo dependências do RAG e UI)
pip install -r requirements.txt
pip install chromadb streamlit
```

Certifique-se de configurar sua chave da OpenAI exportada na variável do terminal ou no `.env`:
```bash
export OPENAI_API_KEY="sk-..."
```

### 2. Rodar a API Backend (FastAPI + ChromaDB)

Em um terminal ativo com a venv, inicie o servidor na porta `8000`:

```bash
python -m uvicorn agent_api:app --reload --port 8000
```
Isso vai criar automaticamente os bancos `aluno_memory.db` (SQLite) e a pasta `./chroma_data` (Banco Vetorial).

### 3. Rodar o Client de Atendimento (Streamlit)

Em outro terminal ativo com a venv, suba a aplicação gráfica na porta `8501`:

```bash
python -m streamlit run app_streamlit.py
```
Acesse no seu navegador: `http://localhost:8501`

---

## 🛠 Como usar a API Assíncrona do Agente

Se você quiser integrar este agente em outro sistema (como um bot de WhatsApp) em vez do Streamlit, use a API Assíncrona REST.

### 1. Iniciar uma Conversa

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "ra": "01493115",
    "message": "Qual é a minha média de faltas no curso?",
    "session_id": null
  }'
```
**Atenção (Contato Proativo)**: Se você mandar a `"message": ""`, a API entende que é apenas uma conexão nova de login e o Agente vai saudar o aluno buscando dinamicamente o último gancho na memória.

**Resposta de Retorno**:
```json
{
  "task_id": "ee76dfb4-c6a6...",
  "session_id": "f5f0b5d1-...",
  "status": "pending",
  "message": "Mensagem recebida e em processamento na fila da IA."
}
```

### 2. Fazer Polling (Aguardar a reposta da IA)

Use o `task_id` gerado para perguntar o status:

```bash
curl http://localhost:8000/api/chat/ee76dfb4-c6a6...
```
*(Fique repetindo esse request a cada 2 segundos até o status virar `completed`)*

**Resposta de Retorno (Sucesso)**:
```json
{
  "task_id": "ee76dfb4-c6a6...",
  "ra": "01493115",
  "status": "completed",
  "result": {
    "reply": "Olá João! Sua média atual de faltas está boa, você não corre riscos. Algo mais que posso ajudar?",
    "internal_discussion": "Acessei o MCP e li o histórico..."
  },
  "created_at": "2024-03-22T10:00:00"
}
```

---

## 📂 Recursos MCP Mantidos e Suporte

O ecossistema nativo do MCP local e os dados em JSON continuam rodando conforme arquitetura principal:

- **Dados Locais**: A biblioteca `student_support_agent.py` consulta os tools MCP simulados pelas bibliotecas locais consumindo o arquivo `database.json`.
- **RA Mockado**: Use o RA restrito **01493115** para que a aplicação de ponta a ponta tenha dados escolares fakes para manipular e ler.

## 🗂 Estrutura do Projeto Agente

```
ser-aluno-mock-mcp/
├── agent_api.py            # API Assíncrona (Gestão de Sessions e Polling)
├── app_streamlit.py        # Interface Web Chat consumindo a agent_api
├── memory_service.py       # Gerenciamento SQLite (Sessões, Jobs, Dossiê Autogen)
├── vector_memory_service.py # Gerenciamento RAG ChromaDB (Memória Semântica longa)
├── student_support_agent.py # Definição do Agente e integração LLM -> MCP Tools
├── database.json            # Base de dados Fake Escolar
├── requirements.txt         # Pacotes (adicionar chromadb, streamlit)
└── chroma_data/             # Pasta local do Banco Vetorial (auto-gerada)
```
