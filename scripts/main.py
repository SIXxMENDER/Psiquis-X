import os
import json
from core.orchestration import orchestrator as P6a_JefeDeCocina

def main():
    print("Psiquis-X Engine Starting...")
    
    # 0. Load Plugins (Dynamic Agent Loading)
    from core.loader import PluginLoader
    loader = PluginLoader()
    loader.load_plugins()
    print(f"Loaded Plugins: {loader.get_loaded_plugins()}")
    
    # 1. Get Plan Configuration (Eventarc/Env Vars)
    bucket_name = os.environ.get("CE_BUCKET", "mock-bucket")
    file_name = os.environ.get("CE_NAME", "plan.json")
    
    print(f"Processing plan from gs://{bucket_name}/{file_name}")
    
    # 2. Load Plan (Mocking GCS download)
    # In production: storage_client.bucket(bucket_name).blob(file_name).download_as_string()
    
    # Creating a dummy plan for demonstration if file doesn't exist or just hardcoded for skeleton
    plan_dummy = {
        "plan_id": "PLAN_DEMO_001",
        "parametros_globales": {"modo": "TEST"},
        "plan_de_ejecucion": [
            {
                "job_id": "J1",
                "agente": "P1_Datos",
                "parametros": {"source": "synthetic"},
                "dependencias": []
            },
            {
                "job_id": "J2",
                "agente": "P2_DQA",
                "parametros": {"data_path": "{J1.data_path}"},
                "dependencias": ["J1"]
            }
        ]
    }
    
    # 3. Invoke Orchestrator
    P6a_JefeDeCocina.ejecutar_prueba_motor(plan_dummy)

if __name__ == "__main__":
    main()
