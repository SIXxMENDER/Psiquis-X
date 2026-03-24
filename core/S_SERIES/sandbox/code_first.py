from typing import Dict, Any
from core.cortex import cortex
from core.sandbox.executor import sandbox

async def code_first_process(task: str, data_context: str) -> Dict[str, Any]:
    """
    Patrón Code-First (Anthropic Style): 
    En lugar de leer datos pesados, genera un script para procesarlos.
    """
    prompt = f"""
    Eres un Científico de Datos experto en Python.
    Tu tarea es escribir un script de Python para resolver este problema:
    "{task}"

    CONTEXTO DE DATOS DISPONIBLES:
    {data_context}

    REGLAS:
    1. Escribe código Python válido y eficiente.
    2. Importa pandas, numpy o lo que necesites.
    3. Imprime el resultado FINAL al final del script para capturarlo en stdout.
    4. NO uses markdown. Devuelve solo el código.
    """
    
    print("🧠 [CODE-FIRST] Generando script de procesamiento...")
    code = cortex.ask(prompt, system_prompt="Data Scientist Agent", model="gemini-2.0-flash-001")
    
    # Limpiar markdown si el LLM se equivoca
    code = code.replace("```python", "").replace("```", "").strip()
    
    print("🧪 [CODE-FIRST] Ejecutando en Sandbox...")
    result = sandbox.execute_python(code)
    
    return result
