import os
import sys
import time
import asyncio
import warnings

# Suppress annoying deprecated warnings from google auth etc.
warnings.filterwarnings("ignore")

# Force root directory into path (CORREGIDO: 3 paréntesis de cierre al final)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings
from core.S_SERIES.utils.courtroom_langgraph import build_courtroom_graph
from skills.pdf_intelligence import download_and_extract_text

import vertexai
from vertexai.generative_models import GenerativeModel
from anthropic import AnthropicVertex
from groq import Groq
from google.api_core import exceptions as google_exceptions

PROJECT_ID = settings.GCP_PROJECT_ID
REGION = settings.GCP_REGION

print(f"🔧 Initializing Vertex AI in {PROJECT_ID} ({REGION})...")
try:
    vertexai.init(project=PROJECT_ID, location=REGION)
    # Groq initialization (Hardcoded for immediate benchmark execution)
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"❌ Initialization Error: {e}")
    sys.exit(1)

class VertexGeminiCortex:
    def ask(self, user_prompt, system_prompt="You are a Senior Assistant.", model=None):
        # Retry logic for quota (429) errors
        for attempt in range(3):
            try:
                gemini_model = GenerativeModel("gemini-2.5-pro", system_instruction=[system_prompt])
                resp = gemini_model.generate_content(user_prompt)
                return resp.text
            except google_exceptions.ResourceExhausted as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    print(f"⚠️ Gemini quota exceeded, retrying in {wait}s (attempt {attempt+1}/3)")
                    time.sleep(wait)
                else:
                    raise
            except Exception as e:
                print(f"❌ Gemini request failed: {e}")
                raise

    async def ask_async(self, user_prompt, system_prompt="You are a Senior Assistant.", model=None):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.ask(user_prompt, system_prompt, model))

class GroqCortex:
    def ask(self, user_prompt, system_prompt="You are a Senior Assistant.", model=None):
        if not model: model = "llama-3.3-70b-versatile"
        # Retry logic for quota (429) errors
        for attempt in range(3):
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return resp.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = 2 ** attempt
                    print(f"⚠️ Groq quota exceeded, retrying in {wait}s (attempt {attempt+1}/3)")
                    time.sleep(wait)
                else:
                    print(f"❌ Groq request failed: {e}")
                    raise
        
    async def ask_async(self, user_prompt, system_prompt="You are a Senior Assistant.", model="llama-3.3-70b-versatile"):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.ask(user_prompt, system_prompt, model))

async def run_courtroom_pipeline(cortex_proxy, pdf_text, model_name=""):
    print(f"\n" + "="*50)
    print(f"🚀 STARTING RAG PIPELINE WITH: {model_name.upper()}")
    print("="*50)

    target_metrics = (
        "Extract EXACT GAAP metrics for all fiscal years (FY24, FY25, FY26). "
        "Required Metrics: Total Revenue, Operating Expenses, Net Income, Gross Margin, Earnings Per Share."
    )

    graph = build_courtroom_graph()
    initial_state = {
        "current_documents": "Mock_PDF.pdf",
        "target_metric": target_metrics,
        "source_text": pdf_text,
        "draft_extraction": "",
        "prosecutor_feedback": "",
        "validation_attempts": 0,
        "rejection_count": 0,
        "raw_data": [],
        "final_cfo_report": "",
        "cortex": cortex_proxy
    }
    
    start_time = time.perf_counter()
    try:
        final_state = await asyncio.to_thread(graph.invoke, initial_state)
        # Force the output evaluation to ensure complete completion
        assert "final_cfo_report" in final_state
    except Exception as e:
        print(f"❌ Error during LangGraph: {e}")
        return 0
        
    duration = time.perf_counter() - start_time
    
    # --- RESULT VISIBILITY ---
    report_data = json.loads(final_state.get("final_cfo_report", "{}"))
    print(f"\n📊 [REPORT SUMMARY - {model_name}]")
    if "narrative" in report_data:
        print(f"   Summary: {report_data['narrative'].get('performance_summary', 'N/A')[:200]}...")
        print(f"   Outlook: {report_data['narrative'].get('strategic_outlook', 'N/A')}")
    print(f"   Metrics Extracted: {len(report_data.get('metrics', []))}")
    print(f"   Confidence: {report_data.get('confidence_score', 'N/A')}/100")
    
    # Save to file
    filename = f"report_{model_name.lower().replace(' ', '_').replace('.', '_')}.json"
    with open(filename, "w") as f:
        json.dump(report_data, f, indent=4)
    print(f"💾 Full report saved to: {filename}")
    
    print(f"\n✅ FINISHED. Time: {duration:.2f}s")
    return duration

async def main():
    print("="*70)
    print("📊 EMPIRICAL QA BENCHMARK: MULTI-LLM RAG EXECUTION")
    print("="*70)
    
    pdf_path = os.path.abspath("Nvidia_Presentation_Q4_FY26.pdf")
    if not os.path.exists(pdf_path):
        print(f"❌ Document {pdf_path} not found.")
        return

    print("📄 Extracting raw text from PDF to avoid Ingestion/Network skew...")
    try:
        doc_text = download_and_extract_text("file:///" + pdf_path.replace(os.sep, '/'), page_range=(35, 38))
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return
        
    print(f"📦 Text successfully extracted ({len(doc_text)} characters).")
    
    gemini_cortex = VertexGeminiCortex()
    groq_cortex = GroqCortex()
    
    print("\n⏳ 1. Evaluating Gemini 2.5 Pro (Native Vertex)")
    gemini_duration = await run_courtroom_pipeline(gemini_cortex, doc_text, "Gemini 2.5 Pro")
    
    print("\n[Cooldown 5s]...")
    await asyncio.sleep(5)
    
    print("\n⏳ 2. Evaluating Groq (Llama-3.3-70b)")
    groq_duration = await run_courtroom_pipeline(groq_cortex, doc_text, "Groq (Llama-3.3-70b)")

    print("\n" + "="*70)
    print("🏆 FINAL RAG LATENCY RESULTS (Courtroom Architecture)")
    print("="*70)
    print(f"  Gemini 2.5 Pro      : {gemini_duration:.2f}s")
    print(f"  Groq (Llama-3.3-70b) : {groq_duration:.2f}s")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())