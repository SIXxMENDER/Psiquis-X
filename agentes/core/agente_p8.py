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
from typing import Dict, Any

from core.utils.schemas import IOInput, IOOutput

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Writes content to disk. Handles 'codigo' or 'contenido_a_guardar'.
    Implements AgentProtocol with Pydantic Validation.
    """
    try:
        input_data = IOInput(**kwargs)
    except Exception as e:
        return {"status": "ERROR", "error": f"Validation Error: {e}"}

    # --- SECURITY PATCH (Round 66) ---
    root_dir = os.getcwd()
    target_dir = os.path.abspath(input_data.target_directory)
    
    # Force jail if target is outside allowed scope
    if not target_dir.startswith(root_dir):
        print(f"⚠️ [SECURITY] Redirecting write from {target_dir} to Sandbox.")
        target_dir = os.path.join(root_dir, "agentes_en_desarrollo")
        
    full_path = os.path.abspath(os.path.join(target_dir, input_data.file_name))
    
    # Final check: Is the resulting file inside the project?
    if not full_path.startswith(root_dir):
         return {"status": "ERROR", "error": "SECURITY: Path traversal attempt blocked."}
    # ---------------------------------
    
    # Ensure full parent directory exists (Nivel 5 Robustness)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(str(input_data.content))
        
    print(f"P8 wrote file to {full_path}")
    
    output = IOOutput(
        status="SUCCESS",
        modified_file=full_path,
        file_path=full_path
    )
    return output.model_dump()

# Alias for backward compatibility
async def write_code_to_disk(file_name: str, **kwargs) -> Dict[str, str]:
    return await execute(file_name=file_name, **kwargs)

# --- REGISTRATION ---
from core.utils.registry import AgentRegistry
import sys
AgentRegistry.register("P8", execute)
