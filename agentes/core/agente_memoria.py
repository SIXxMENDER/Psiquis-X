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

from typing import Dict, Any
from core.S_SERIES.vector_store import vector_store

async def execute(**kwargs) -> Dict[str, Any]:
    """
    AgentProtocol implementation for MemoryAgent (Unified).
    Delegates to the central VectorStore (Hippocampus).
    """
    query = kwargs.get("query") or kwargs.get("objetivo") or kwargs.get("task_description")
    
    if not query:
        return {"status": "ERROR", "error": "No query provided for memory lookup."}

    print(f"🧠 [MEMORY] Searching Hippocampus for: '{query}'...")
    
    try:
        # Semantic Search in the Knowledge Base
        results = vector_store.query(query, n_results=3)
        
        if not results:
            return {
                "status": "SUCCESS",
                "result": "No relevant information found in long-term memory.",
                "data": []
            }
            
        # Format results for the engine
        formatted_context = "\n".join([
            f"- [{r['metadata'].get('source', 'Unknown')}] (Relevance: {1 - r['distance']:.2f}): {r['content'][:300]}..." 
            for r in results
        ])
        
        return {
            "status": "SUCCESS",
            "result": f"Memory retrieved:\n{formatted_context}",
            "data": results
        }
        
    except Exception as e:
        print(f"❌ [MEMORY] Retrieval Failed: {e}")
        return {"status": "ERROR", "error": str(e)}
