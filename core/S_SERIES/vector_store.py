import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any

class VectorStore:
    """
    The Hippocampus of Psiquis-X.
    Manages long-term semantic memory using ChromaDB.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.db_path = os.path.join(os.getcwd(), "data", "chroma_db")
        os.makedirs(self.db_path, exist_ok=True)
        
        print(f"🧠 [MEMORY] Initializing Vector Store at {self.db_path}...")
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Create or get the main collection
        self.collection = self.client.get_or_create_collection(
            name="psiquis_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"🧠 [MEMORY] Knowledge Base Active. Items: {self.collection.count()}")

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any] = None):
        """Adds a document to the vector memory."""
        if not content: return
        
        # Simple chunking could go here, for now we store the whole block if small
        self.collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {}]
        )
        print(f"💾 [MEMORY] Memorized: {doc_id}")

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Semantic search for relevant context."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        structured_results = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                structured_results.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": results["distances"][0][i] if results["distances"] else 0
                })
                
        return structured_results

    def count(self):
        return self.collection.count()

# Singleton
vector_store = VectorStore()
