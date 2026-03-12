import os
import sys
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.orchestration import orchestrator as P6a_JefeDeCocina
from core.engine_12_12 import Engine12

def run_full_system_test():
    print("\n[PSIQUIS-X] INICIANDO PRUEBA DE SISTEMA COMPLETO")
    print("=====================================================")
    print("Objetivo: Validar la cadena de valor completa (P0 -> P9)")
    
    # Plan de Prueba Integral
    plan_full = {
        "plan_id": "TEST_FULL_SYSTEM_001",
        "parametros_globales": {"modo": "TEST", "verbose": True},
        "plan_de_ejecucion": [
            # 1. Investigación (P0)
            {
                "job_id": "J0",
                "agente": "P0_Investigador",
                "parametros": {"query": "Estrategia de trading de cruce de medias móviles simple en Python con pandas"},
                "dependencias": []
            },
            # 2. Ingesta de Datos (P1)
            {
                "job_id": "J1",
                "agente": "P1_Datos",
                "parametros": {
                    "ticker": "BTC-USD", 
                    "interval": "1h", 
                    "output_path": "data/market_data.csv"
                },
                "dependencias": []
            },
            # 3. Auditoría de Datos (P2)
            {
                "job_id": "J2",
                "agente": "P2_DQA",
                "parametros": {"data_path": "{J1.data_path}"}, # Dependencia de P1
                "dependencias": ["J1"]
            },
            # 4. Generación de Estrategia (P3)
            {
                "job_id": "J3",
                "agente": "P3_Estrategia",
                "parametros": {"descripcion": "{J0.respuesta}"}, # Dependencia de P0
                "dependencias": ["J0"]
            },
            # 5. Auditoría de Seguridad (P9) - Antes de ejecutar
            {
                "job_id": "J9",
                "agente": "P9_Seguridad",
                "parametros": {"code_to_scan": "{J3.codigo_python}"},
                "dependencias": ["J3"]
            },
            # 6. Auditoría de Riesgo Cognitivo (P7)
            {
                "job_id": "J7",
                "agente": "P7_Riesgo",
                "parametros": {
                    "oferta": {
                        "title": "Propuesta Generada por P3",
                        "description": "{J0.respuesta}",
                        "budget": 5000
                    }
                },
                "dependencias": ["J3", "J0"]
            },
            # 7. Backtest (P4)
            {
                "job_id": "J4",
                "agente": "P4_Backtest",
                "parametros": {"codigo_python": "{J3.codigo_python}", "data_path": "{J1.data_path}"},
                "dependencias": ["J3", "J1"]
            },
            # 8. Optimización (P5)
            {
                "job_id": "J5",
                "agente": "P5_Optimizador",
                "parametros": {"objetivo": "{J4.metricas_clave}"},
                "dependencias": ["J4"]
            },
            # 9. Auditoría del Sistema Nervioso (P6b)
            {
                "job_id": "J6",
                "agente": "P6b_Auditor",
                "parametros": {"audit_target": "Full Cycle", "context": "{J5.optimization_report}"},
                "dependencias": ["J5"]
            },
            # 10. Integración Final (P8)
            {
                "job_id": "J8",
                "agente": "P8_Integrador",
                "parametros": {
                    "codigo": "{J3.codigo_python}",
                    "nombre_archivo": "strategy_final.py",
                    "directorio_destino": "output",
                    "documentation": "{J0.respuesta}"
                },
                "dependencias": ["J3", "J0"]
            }
        ]
    }
    
    try:
        P6a_JefeDeCocina.ejecutar_prueba_motor(plan_full)
        print("\n[OK] PRUEBA DE SISTEMA COMPLETO FINALIZADA CON EXITO")
    except Exception as e:
        print(f"\n[ERROR] ERROR CRITICO EN PRUEBA DE SISTEMA: {e}")

def run_engine_12_test():
    print("\n[PSIQUIS-X] INICIANDO PRUEBA DE MOTOR 12/12 (CHAMELEON)")
    print("=========================================================")
    print("Objetivo: Validar ciclo de 12 pasos (Identidad -> Acción -> Narrativa)")
    
    try:
        engine = Engine12()
        # Test with a complex prompt to trigger multiple modules
        engine.run_cycle("Analizar viabilidad de estrategia de Arbitraje triangular en Binance")
        print("\n[OK] PRUEBA DE MOTOR 12/12 FINALIZADA CON EXITO")
    except Exception as e:
        print(f"\n[ERROR] ERROR CRITICO EN MOTOR 12/12: {e}")
        import traceback
        traceback.print_exc()

def run_genesis_test():
    print("\n[PSIQUIS-X] INICIANDO PRUEBA DE PROTOCOLO GÉNESIS (AUTONOMOUS AGENT)")
    print("======================================================================")
    print("Objetivo: Validar la creación autónoma de un agente (P3 -> P8 -> P6a)")
    
    from agentes.agente_p5_genesis import ejecutar_genesis_con_reintento
    
    try:
        # Simple objective to test the flow without complex logic
        objetivo_test = "Crear un agente que calcule el factorial de un número dado en 'number' y retorne el resultado."
        
        result = ejecutar_genesis_con_reintento(objetivo_test, max_intentos=2)
        
        if result.get("status") == "SUCCESS":
            print(f"\n[OK] PRUEBA GÉNESIS FINALIZADA CON ÉXITO")
            print(f"    Agente creado en: {result.get('agent_path')}")
            print(f"    Resultado ejecución: {result.get('result')}")
        else:
            print(f"\n[FAIL] PRUEBA GÉNESIS FALLIDA")
            print(f"    Error: {result.get('error')}")
            raise Exception("Genesis Protocol Failed")
            
    except Exception as e:
        print(f"\n[ERROR] ERROR CRITICO EN GÉNESIS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 1. Run Legacy Test (P6a)
    # run_full_system_test() 
    
    # 2. Run New Engine 12 Test
    run_engine_12_test()
    
    # 3. Run Genesis Protocol Test
    run_genesis_test()
