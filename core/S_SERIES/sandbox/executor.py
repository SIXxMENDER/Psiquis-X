import subprocess
import sys
import os
import tempfile
import time
from typing import Dict, Any

class CodeSandbox:
    """
    ASI05: Safe Code Execution.
    Ejecuta código generado por agentes en un entorno controlado y efímero.
    """
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def execute_python(self, code: str) -> Dict[str, Any]:
        """
        Ejecuta código Python en un proceso separado y captura el output.
        Nivel de seguridad: Aislamiento de Proceso (OS Level).
        """
        # Crear un archivo temporal para el script
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
            tmp_name = tmp.name
            tmp.write(code)

        start_time = time.time()
        try:
            # -I: isolate Python from user's environment (no site-packages, etc.)
            # Por ahora no usamos -I para permitir que los agentes usen dependencias instaladas, 
            # pero bloqueamos variables de entorno críticas.
            env = os.environ.copy()
            # Limpiar llaves sensibles del entorno del subproceso
            keys_to_clear = ["GOOGLE_API_KEY", "GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            for k in keys_to_clear: env.pop(k, None)

            process = subprocess.Popen(
                [sys.executable, tmp_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            stdout, stderr = process.communicate(timeout=self.timeout)
            duration = time.time() - start_time

            return {
                "status": "SUCCESS" if process.returncode == 0 else "ERROR",
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "duration": duration
            }

        except subprocess.TimeoutExpired:
            process.kill()
            return {"status": "ERROR", "error": "Timeout de ejecución (Sandbox Limit)"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

sandbox = CodeSandbox()
