import os
import sys

# Define CHROMA_PORT para 8002 para bater com o host port configurado no docker-compose local
os.environ["CHROMA_PORT"] = "8002"
os.environ["CHROMA_HOST"] = "localhost"

# Check if OPENAI_API_KEY is present
if not os.environ.get("OPENAI_API_KEY"):
    print("OPENAI_API_KEY missing - skipping test.")
    sys.exit(0)

from vector_memory_service import store_memory, retrieve_memories, client

def test():
    print("Testando ChromaDB HTTP Client com OpenAI Embeddings...")
    
    try:
        # Check heartbeat
        print(f"Heartbeat: {client.heartbeat()}")
        
        test_ra = "TEST_999"
        store_memory(test_ra, "test_sess", "user", "Eu adoro estudar matemática e física, quero aprender álgebra.")
        
        # Recuperando...
        print("Recuperando memória...")
        memories = retrieve_memories(test_ra, "Eu preciso de ajuda com exatas")
        
        if memories:
            print(f"Sucesso! Memória encontrada: {memories[0]}")
        else:
            print("Falhou em recuperar a memória.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Erro no teste: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test()
