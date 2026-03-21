import os
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import logging
import uuid
from typing import List

logger = logging.getLogger("VectorMemoryService")

# Use a local directory to store actual vector databases
CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# Setting up OpenAI embedding function using the key
_openai_key = os.environ.get("OPENAI_API_KEY", "")
if _openai_key:
    # Use high-quality embeddings from OpenAI
    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=_openai_key,
        model_name="text-embedding-3-small"
    )
else:
    # Fallback to local sentence-transformers (might take time to download if first run)
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Create or get the collection
collection_name = "aluno_memories"
try:
    memory_collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )
except Exception as e:
    logger.error(f"Erro ao inicializar coleção ChromaDB: {e}")
    memory_collection = None

def store_memory(ra: str, session_id: str, role: str, text: str):
    """
    Armazena um trecho da conversa como um chunk vetorial.
    O texto armazenado terá na metadata informando o dono da mémoria (ra).
    """
    if not memory_collection or not text.strip():
        return
        
    doc_id = str(uuid.uuid4())
    
    # Prefix the role to give semantic meaning 
    # Example: "O Aluno disse: Estou super preocupado com matemática."
    prefix = "O Aluno disse: " if role == "user" else "O Assistente Ser Humanozinho respondeu: "
    full_text = prefix + text.strip()
    
    metadata = {
        "ra": ra,
        "session_id": session_id,
        "role": role
    }
    
    try:
        memory_collection.add(
            documents=[full_text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logger.info(f"💾 Memória Vetorial guardada para RA {ra} [ID: {doc_id}]")
    except Exception as e:
        logger.error(f"Falha ao salvar a memória no ChromaDB: {e}")

def retrieve_memories(ra: str, query: str, top_k: int = 5) -> List[str]:
    """
    Recupera as últimas mensagens/fatos relevantes da mesma matrícula baseado na pergunta atual.
    """
    if not memory_collection or not query.strip():
        return []
        
    try:
        results = memory_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"ra": ra}
        )
        
        memories = []
        if results and results['documents'] and len(results['documents']) > 0:
            for doc_list in results['documents']:
                for doc in doc_list:
                    memories.append(doc)
        
        if memories:
            logger.info(f"🧠 {len(memories)} Memórias Recobradas para {ra}.")
            
        return memories
    except Exception as e:
        logger.error(f"Erro ao buscar RAG no ChromaDB para '{query}': {e}")
        return []
