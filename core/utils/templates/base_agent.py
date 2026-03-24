"""
Base Agent Template
This file serves as the skeleton for all generated agents.
P3 will inject the logic into the {{LOGICA_AGENTE}} placeholder.
"""
import sys
import os
import json
import textwrap
import traceback
import logging
from typing import Dict, Any

# --- CONFIGURACIÓN DE ENTORNO ---
try:
    # Intentar obtener el directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback si __file__ no está definido (ej. exec())
    current_dir = os.getcwd()

# Añadir raíz del proyecto al path para importar utils
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

# Force UTF-8 for Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# --- IMPORTS DEL SISTEMA ---
try:
    from utils.llm_utils import invocar_llm
except ImportError:
    # Mock de emergencia si falla el import
    def invocar_llm(prompt_sistema, prompt_usuario, **kwargs):
        return f"MOCK LLM: {prompt_usuario[:50]}..."

# --- LÓGICA DEL AGENTE ---

def ejecutar_paso(**kwargs) -> Dict[str, Any]:
    """
    Función principal del agente.
    Args:
        **kwargs: Argumentos variables (contexto, datos previos).
    Returns:
        Dict con keys 'status' y 'result' (o 'error').
    """
    try:
        print("🚀 Iniciando ejecución del agente...")
        
        # ---------------------------------------------------------
        # AQUÍ SE INYECTA LA LÓGICA GENERADA POR P3
        # ---------------------------------------------------------
        
        # {{LOGICA_AGENTE}}
        
        # ---------------------------------------------------------
        # FIN DE LÓGICA GENERADA
        # ---------------------------------------------------------
        
        # Si la lógica no retornó nada, forzamos un error
        return {"status": "FAILED", "error": "El agente no retornó ningún valor."}

    except Exception as e:
        error_msg = f"Error en agente: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_msg}")
        return {"status": "FAILED", "error": error_msg}

# --- SELF TEST (Inyectado dinámicamente o estático) ---
if __name__ == "__main__":
    print("🛡️ Ejecutando Self-Test...")
    try:
        resultado = ejecutar_paso()
        print(f"✅ Resultado: {resultado}")
    except Exception as e:
        print(f"❌ Falló Self-Test: {e}")
