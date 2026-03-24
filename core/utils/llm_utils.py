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

"""
LLM Utils - Transition Proxy for core.cortex.
"""
from typing import Dict, Any, Type
from pydantic import BaseModel
from core.S_SERIES.cortex import cortex

def invoke_llm(
    system_prompt: str, 
    user_prompt: str, 
    model: str = None,   
    provider: str = None, 
    temperature: float = 0.7,
    **kwargs
) -> str:
    return cortex.ask(user_prompt, system_prompt, provider=provider, model=model)

async def invoke_llm_async(
    system_prompt: str, 
    user_prompt: str, 
    model: str = None, 
    provider: str = None,
    **kwargs
) -> str:
    return await cortex.ask_async(user_prompt, system_prompt, provider=provider, model=model)

def invoke_llm_json(
    system_prompt: str, 
    user_prompt: str, 
    pydantic_schema: Type[BaseModel] = None,
    provider: str = None
) -> Dict[str, Any]:
    return cortex.ask_json(user_prompt, system_prompt, schema=pydantic_schema, provider=provider)

async def invoke_llm_json_async(
    system_prompt: str, 
    user_prompt: str, 
    pydantic_schema: Type[BaseModel] = None,
    provider: str = None
) -> Dict[str, Any]:
    return await cortex.ask_json_async(user_prompt, system_prompt, schema=pydantic_schema, provider=provider)
