import json
from core.S_SERIES.cortex import cortex

class SemanticRouter:
    """
    Responsible for translating high-level human intent into 
    machine-optimized queries for specific agents.
    """
    
    def decompose_objective(self, objective: str) -> dict:
        """
        Breaks down a complex objective into specific queries for each domain.
        Returns a JSON dict: { "marketing": "...", "finance": "...", ... }
        """
        print(f"🧠 [SEMANTIC ROUTER] Decomposing: '{objective}'")
        
        prompt = f"""
        TASK: Semantic Decomposition
        OBJECTIVE: "{objective}"
        
        INSTRUCTIONS:
        1. Analyze the objective.
        2. Break it down into specific, keyword-optimized SEARCH QUERIES for these 4 domains:
           - MARKETING (News, trends, products)
           - FINANCE (Stock price, valuation, market cap)
           - DEVELOPMENT (Tech stack, complexity, github)
           - TRIBUNAL (Risks, legal, controversy)
           
        3. The queries must be short, factual, and optimized for a search engine (Google/DDG).
        4. If a domain is NOT relevant, return null.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "marketing": "query string...",
            "finance": "query string...",
            "development": "query string...",
            "tribunal": "query string..."
        }}
        """
        
        try:
            response = cortex.ask(prompt, system_prompt="Semantic Router & Query Optimizer")
            # Clean markdown
            json_str = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(json_str)
            return data
        except Exception as e:
            print(f"⚠️ [SEMANTIC ROUTER] Failed: {e}")
            # Fallback: Return original objective for all (better than nothing)
            return {
                "marketing": objective,
                "finance": objective,
                "development": objective,
                "tribunal": objective
            }

semantic_router = SemanticRouter()
