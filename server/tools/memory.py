import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

pc = None
index = None

def init_pinecone():
    global pc, index
    if not PINECONE_API_KEY:
        return False
    
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        # Check if index exists, if not create it (simplified for demo)
        existing_indexes = [i.name for i in pc.list_indexes()]
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            # We assume it exists or will fail gracefully
            # print(f"Index {PINECONE_INDEX_NAME} not found. Please create it manually.")
            return False
            
        index = pc.Index(PINECONE_INDEX_NAME)
        return True
    except Exception as e:
        # print(f"Error initializing Pinecone: {e}")
        return False

# Initialize on module load
init_pinecone()

def store_memory(text: str, vector: list[float]) -> str:
    """
    Store a memory vector in Pinecone.
    
    Args:
        text: The text content of the memory.
        vector: The embedding vector of the text.
    """
    if not index:
        return "Error: Pinecone index not initialized."
    
    try:
        import uuid
        id = str(uuid.uuid4())
        
        index.upsert(vectors=[(id, vector, {"text": text})])
        return f"Memory stored with ID: {id}"
    except Exception as e:
        return f"Error storing memory: {e}"

def retrieve_memory(vector: list[float], top_k: int = 3) -> str:
    """
    Retrieve relevant memories from Pinecone.
    
    Args:
        vector: The query embedding vector.
        top_k: Number of results to return.
    """
    if not index:
        return "Error: Pinecone index not initialized."
    
    try:
        results = index.query(vector=vector, top_k=top_k, include_metadata=True)
        
        memories = []
        for match in results.matches:
            memories.append(f"- {match.metadata['text']} (Score: {match.score})")
            
        return "\n".join(memories) if memories else "No relevant memories found."
    except Exception as e:
        return f"Error retrieving memory: {e}"
