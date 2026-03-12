import os
import time
import asyncio
from core.S_SERIES.missions.doc_intelligence import execute_mission

async def main():
    print("="*60)
    print("🚀 INICIANDO BENCHMARK QA: RAG PIPELINE (COURTROOM)")
    print("="*60)
    
    # Utilizing an existing PDF in the directory to simulate a SAM.gov RFP document
    # We will use Nvidia_Presentation_Q4_FY26.pdf as the empirical test case
    pdf_path = os.path.abspath("Nvidia_Presentation_Q4_FY26.pdf")
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Archivo de prueba {pdf_path} no encontrado. Por favor coloca un PDF válido.")
        return
        
    prompt = f"Por favor extrae las métricas financieras de file:///{pdf_path.replace(os.sep, '/')}"
    
    # Callback para ignorar actualizaciones visuales y centrarse en la medición
    async def mock_broadcast(msg):
        msg_type = msg.get("type", "info")
        data = str(msg.get("data", ""))
        
        if msg_type == "error":
            print(f"⚠️ [Misión Error] {data}")
        elif msg_type == "thought":
            # Print a truncated line of the thought process so we see progress
            print(f"ℹ️ [Progreso] {data[:70]}...")
        elif msg_type == "success":
            print(f"✅ [Éxito] {data}")

    print(f"📄 Documento Objetivo: {os.path.basename(pdf_path)}")
    print("⏱️ Iniciando reloj de ejecución perf_counter...")
    
    # QA Automation: Metric Start
    start_time = time.perf_counter()
    
    try:
        await execute_mission(prompt, mock_broadcast)
    except Exception as e:
        print(f"❌ Excepción durante ejecución de la misión: {e}")
        
    # QA Automation: Metric End
    end_time = time.perf_counter()
    duration_seconds = end_time - start_time
    
    print("\n" + "="*60)
    print(f"✅ BENCHMARK FINALIZADO: MÉTRICA EMPÍRICA CAPTURADA")
    print(f"⏱️ Tiempo de ejecución total (FinOps KPI): {duration_seconds:.2f} segundos")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
