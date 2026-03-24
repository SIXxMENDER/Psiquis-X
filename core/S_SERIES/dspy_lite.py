"""
DSPy-Lite Optimizer (v5.0) - Level 4.2 Declarative Prompting
Allows Psiquis-X to 're-compile' and optimize prompts based on evaluation metrics.
Instead of static prompts, we use Feedback-Driven Instruction Refinement.
"""
import logging
from typing import Dict, Any, List, Optional
from core.cortex import cortex

class DSPyLite:
    def __init__(self):
        self.signatures = {} # task_name -> current_optimized_prompt

    async def optimize(self, task_name: str, base_prompt: str, failures: List[str], max_retries: int = 3) -> str:
        """
        Phase 4.2: Compiles a new prompt by analyzing failed attempts.
        Implements a Circuit Breaker (max_retries) to avoid infinite loops (ASI08).
        """
        if len(failures) > max_retries:
            logging.warning(f"🚫 [DSPy-Lite] Circuit Breaker triggered for '{task_name}'. Optimization limit reached.")
            return base_prompt # Return original or last known good to avoid loop
            
        logging.info(f"🛠️ [DSPy-Lite] Optimizing Signature for '{task_name}' (Attempt {len(failures)}/{max_retries})...")
        
        failure_context = "\n".join([f"- {f}" for f in failures])
        
        compiler_prompt = f"""
        OBJETIVO: Optimizar el programa de lenguaje (Prompt) para la tarea: {task_name}.
        PROMPT ACTUAL: {base_prompt}
        FALLOS DETECTADOS EN INTENTOS PREVIOS:
        {failure_context}
        
        RETAREA: Reescribe las instrucciones para el agente de modo que EVITE estos fallos. 
        Sé extremadamente técnico, preciso y directo. No uses placeholders ambiguos.
        Enfócate en las restricciones que fallaron.
        """
        
        optimized_prompt = cortex.ask(compiler_prompt, system_prompt="Eres un Compilador de Prompts (DSPy Mode).")
        self.signatures[task_name] = optimized_prompt
        
        return optimized_prompt

dspy = DSPyLite()
