import chromadb
from pathlib import Path
import json

CHROMA_DIR = Path("./chroma_data")

def inspect_chroma():
    print(f"Buscando banco de dados ChromaDB na pasta: {CHROMA_DIR.absolute()}")
    
    # Inicia o cliente Chroma local na pasta onde os dados foram persistidos
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Lista todas as "Coleções" (tabelas) criadas. No nosso código criamos coleções no formato: memory_{ra}
    collections = client.list_collections()
    
    if not collections:
        print("Nenhuma coleção encontrada! Você precisa conversar com a Sofia primeiro para gerar memórias.")
        return
        
    print(f"\nColeções encontradas: {[c.name for c in collections]}")
    
    # Vamos inspecionar a primeira coleção encontrada (Provavelmente memory_01493115)
    for col in collections:
        print(f"\n=========== Inspecionando Coleção: {col.name} ===========")
        collection = client.get_collection(col.name)
        
        # O método `.get()` retorna os metadados, IDs, e conteúdos guardados
        data = collection.get()
        
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        
        print(f"Total de memórias/documentos gravados: {len(ids)}")
        
        for i in range(min(5, len(ids))): # Mostra as 5 primeiras memórias para não lotar a tela
            print(f"\n--- Memória [{i+1}] | ID: {ids[i]} ---")
            print(f"Conteúdo: {documents[i][:150]}...")
            print(f"Metadados: {metadatas[i]}")

if __name__ == "__main__":
    inspect_chroma()
