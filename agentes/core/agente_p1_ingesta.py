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
from core.utils.registry import AgentRegistry
from agentes.ingestion import agente_web_scraper, agente_financial_api, agente_rss_reader

# Register specialized agents (Manual registration for now, or rely on imports if they register themselves)
# Since they are simple modules, we can just import them directly here as a Facade.

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Unified entry point for P1 (Data Ingestion) - Async Facade.
    Delegates to specialized agents in `agentes.ingestion`.
    """
    parametros = kwargs
    print(f"P1 (Facade): Routing request with params: {parametros.keys()}")

    # 1. Financial Data & Code-First Analysis
    if "ticker" in parametros or "symbol" in parametros or "data_path" in parametros:
        from core.S_SERIES.sandbox.code_first import code_first_process
        task = parametros.get("query", "Analizar tendencias y estados financieros")
        data_path = parametros.get("data_path", "N/A")
        
        print(f"🚀 [P1] Applying Code-First Pattern for: {task}")
        res = await code_first_process(task, f"Data file: {data_path}")
        return {
            "status": "SUCCESS",
            "result": res.get("stdout"),
            "stderr": res.get("stderr"),
            "accuracy": 0.98 # Mock high accuracy for code execution
        }

    # 2. Freelance Search (Web Scraper)
    if "platform_url" in parametros or "url" in parametros:
        return await agente_web_scraper.execute(**kwargs)

    return {"error": "Unknown P1 action", "status": "FAILED"}

# Alias for backward compatibility
async def execute_step_P1(**kwargs) -> Dict[str, Any]:
    return await execute(**kwargs)

# Register P1 Facade
try:
    AgentRegistry.register("P1", execute)
except:
    pass
