# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Psiquis-X: Enterprise Multi-Agent Framework
# Proprietary Software - All Rights Reserved
# Copyright (c) 2026 SIXxMENDER & Bosniack-94
# -----------------------------------------------------------------------------
# WARNING: This source code is proprietary and confidential. 
# Unauthorized copying, distribution, or use via any medium is strictly 
# prohibited. This code is provided solely for authorized technical review 
# and evaluation purposes.
# -----------------------------------------------------------------------------

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List
import logging
import json
from datetime import datetime

import threading
from config.settings import DB_PATH, CHROMA_COLLECTION_NAME

# Singleton resources
_chroma_client = None
_embedding_model = None
_collection = None
_lock = threading.Lock()

def _get_resources():
    global _chroma_client, _embedding_model, _collection
    
    # Double-checked locking pattern for thread safety
    if _collection is None:
        with _lock:
            if _chroma_client is None:
                logging.info(f"🧠 Initializing Vector Memory at: {DB_PATH}")
                os.makedirs(DB_PATH, exist_ok=True)
                _chroma_client = chromadb.PersistentClient(path=DB_PATH)
                
            if _embedding_model is None:
                logging.info("🧠 Loading embedding model (all-MiniLM-L6-v2)...")
                _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
            if _collection is None:
                _collection = _chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
        
    return _collection, _embedding_model

def save_memory_in_vdb(memory: Dict[str, Any]):
    """
    Saves a memory in the vector database.
    The 'memory' must have at least a 'content' or 'description' field to vectorize.
    """
    try:
        collection, model = _get_resources()
        
        # Extract text to vectorize
        text_to_vectorize = memory.get("content") or memory.get("description") or str(memory)
        
        # Generar ID único
        doc_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(texto_a_vectorizar)}"
        
        # Generar embedding
        embedding = model.encode(texto_a_vectorizar).tolist()
        
        # Prepare metadata (flatten dictionary because Chroma requires simple metadata)
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": memory.get("type", "general"),
            "origin": memory.get("origin", "system")
        }
        
        # Save
        collection.add(
            documents=[text_to_vectorize],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[doc_id]
        )
        logging.info(f"✅ Memory saved in ChromaDB: {doc_id}")
        
    except Exception as e:
        logging.error(f"❌ Error saving in Vector DB: {e}")

def search_similar_memories(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """
    Searches for semantically similar memories to the query.
    """
    try:
        collection, model = _get_resources()
        
        # Generar embedding de la query
        query_embedding = model.encode(query).tolist()
        
        # Buscar
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        memories = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                memories.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "id": results['ids'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
                
        logging.info(f"🔍 Found {len(memories)} similar memories for: '{query}'")
        return memories
        
    except Exception as e:
        logging.error(f"❌ Error searching in Vector DB: {e}")
        return []
