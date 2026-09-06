import chromadb
import os

# Define paths for the Chroma database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")

# Ensure the data directory exists
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
# This saves the vector data locally on your hard drive
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Get or create a collection (like a table in SQL)
collection = client.get_or_create_collection(name="agi_semantic_memory")

def add_to_semantic_memory(memory_id: str, content: str):
    """
    Converts text into a vector and saves it to ChromaDB.
    """
    try:
        collection.add(
            documents=[content],
            ids=[memory_id]
        )
    except Exception as e:
        print(f"⚠️ [CHROMA ERROR] Failed to save semantic memory: {e}")

def search_semantic_memory(query: str, n_results: int = 2) -> str:
    """
    Searches the memory by meaning, not just exact keywords.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Check if we found any documents
        if not results or not results['documents'] or not results['documents'][0]:
            return "No relevant memories found."
            
        memories = results['documents'][0]
        
        memory_str = f"Found {len(memories)} conceptually related memories:\n"
        for idx, mem in enumerate(memories):
            memory_str += f"- {mem}\n"
            
        return memory_str
    except Exception as e:
        return f"Error searching semantic memory: {e}"