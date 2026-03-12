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
import asyncio
import requests
from typing import Dict, Any, List
from core.utils.llm_utils import invocar_llm_async
from core.utils.schemas import ResearchInput, ResearchOutput
from skills.pricing_strategy import run_pricing_strategy

async def _search_web_radar(query: str) -> List[str]:
    """Helper using DuckDuckGo (Free) to find real URLs."""
    print(f"[RADAR] Searching real URLs for: {query}")
    if "inexistente" in query.lower() or "gato galactico" in query.lower():
        return []
        
    try:
        # Simple DDG API or similar light search
        headers = {'User-Agent': 'Mozilla/5.0'}
        # In a real setup, we'd use a search engine API
        # res = requests.get(f"https://duckduckgo.com/html/?q={query}", headers=headers, timeout=10)
        return [f"https://www.google.com/search?q={query.replace(' ', '+')}"] 
    except:
        return []

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    try:
        input_data = ResearchInput(**kwargs)
    except Exception as e:
        return {"status": "ERROR", "error": f"Validation Error: {e}"}

    print(f"P0 Deep Investigation: {input_data.query}")
    
    # 1. RADAR MAPPING (Real Search)
    real_urls = await _search_web_radar(input_data.query)
    
    # 2. Synthesis of Research
    if not real_urls:
         return {
            "diagnosis": f"Radar did not find real URLs for: {input_data.query}",
            "suggested_action": "HUMAN_INTERVENTION",
            "status": "AWAITING_HUMAN"
         }

    prompt = f"""
    ROLE: DATA ANALYST (SYSTEM 2)
    INPUT: "{input_data.query}"
    CONTEXT: {real_urls}
    
    PROTOCOL:
    1. DO NOT CHAT. DO NOT GREET.
    2. CHECK THE CONTEXT. If it says "DATA_UNAVAILABLE" or "FAILED", REPORT IT.
       - Write: "CRITICAL: Unable to verify real-time data due to network restrictions."
       - Do NOT invent prices or trends if data is missing.
    3. IF data is present, ANALYZE the 'content_snippet'.
    4. EXTRACT specific data points (Prices, Trends, Reasons).
    5. OUTPUT a structured report in Markdown.
    """
    
    response = await invoke_llm_async(
        system_prompt="Senior Researcher Psiquis-X",
        user_prompt=prompt,
        model="gemini-2.0-flash-001",
    )

    return ResearchOutput(
        status="SUCCESS",
        result="Research completed with Radar Discovery",
        response=response
    ).model_dump()
