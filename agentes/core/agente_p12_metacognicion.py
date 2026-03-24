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
from typing import Dict, Any
from core.S_SERIES.cortex import cortex

async def execute(self=None, **kwargs) -> Dict[str, Any]:
    """
    Agent P12: Metacognition and Self-Reflection.
    Analyzes system logs and generated reports to evaluate performance.
    """
    print("[META] Initializing Self-Reflection Protocol...")
    
    # 1. READ RECENT LOGS
    log_content = ""
    try:
        # Try to read the most recent log
        log_files = [f for f in os.listdir(".") if f.startswith("startup_log") and f.endswith(".txt")]
        if log_files:
            latest_log = max(log_files, key=os.path.getmtime)
            with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                log_content = "".join(lines[-200:]) # Last 200 lines
    except Exception as e:
        print(f"[META] Error reading logs: {e}")
        log_content = "Logs not available."

    # 2. READ LATEST REPORT
    report_content = ""
    try:
        report_dir = "data/reports"
        if os.path.exists(report_dir):
            reports = [os.path.join(report_dir, f) for f in os.listdir(report_dir)]
            if reports:
                latest_report = max(reports, key=os.path.getmtime)
                with open(latest_report, "r", encoding="utf-8", errors="ignore") as f:
                    report_content = f.read()[:2000] # First 2000 characters
    except Exception as e:
        print(f"[META] Error reading reports: {e}")
        report_content = "No previous reports."

    # 3. COGNITIVE ANALYSIS (CORTEX)
    prompt = f"""
    ANALYZE YOUR OWN PERFORMANCE.
    
    CONTEXT (SYSTEM LOGS):
    {log_content}
    
    RESULT (LATEST REPORT):
    {report_content}
    
    TASK:
    1. Identify bottlenecks or errors in logs.
    2. Evaluate the quality of the final report.
    3. Propose 3 concrete improvements for the next execution.
    
    Respond in concise Markdown format.
    """
    
    reflexion = await cortex.ask_async(prompt, system_prompt="SYSTEM META-COGNITION MODULE")
    
    # 4. GUARDAR REFLEXIÓN
    os.makedirs("data/metacognition", exist_ok=True)
    import time
    timestamp = int(time.time())
    filename = f"data/metacognition/reflection_{timestamp}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(reflexion)
        
    print(f"[META] Reflection saved to: {filename}")
    
    return {
        "status": "SUCCESS",
        "result": "Self-Reflection Completed",
        "response": reflexion,
        "data": {"path": filename, "content": reflexion}
    }
