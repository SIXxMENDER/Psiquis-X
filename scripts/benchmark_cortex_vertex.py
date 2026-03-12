import os
import sys
import time
import requests
import warnings

# Use absolute path resolving for core library imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import settings
warnings.filterwarnings("ignore")

from core.S_SERIES.cortex import cortex
import vertexai
from vertexai.generative_models import GenerativeModel
from groq import Groq

PROJECT_ID = settings.GCP_PROJECT_ID
REGION = settings.GCP_REGION

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
    gemini_model = GenerativeModel("gemini-2.5-pro")
    groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    print(f"❌ Initialization Error: {e}")
    sys.exit(1)

TEST_QUERIES = [
    # Vector DB / Local context cases
    "What are the core principles and architecture of Psiquis-X?",
    "Identity of the p3 agent.",
    "What is your name and purpose?",
    
    # Complex cases requiring LLM inferences
    "Write a Python script for a crypto arbitrage bot using WebSockets.",
    "Explain in detail how the LangGraph Courtroom engine works.",
    "Generate a data structure for a 5-billion-token RAG model.",
    "What is the civil liability framework in a B2B SaaS Software contract?",
    "Explain string theory in 3 paragraphs for a 10-year-old child.",
    "Draft a Pydantic JSON to validate international commercial invoices.",
    "Synthesize an 80-page RFP into 5 key metrics for public bidding."
]

def ask_gemini(prompt):
    start = time.perf_counter()
    resp = gemini_model.generate_content(prompt)
    lat = time.perf_counter() - start
    tokens = resp.usage_metadata.total_token_count
    return lat, tokens

def ask_groq(prompt):
    start = time.perf_counter()
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    lat = time.perf_counter() - start
    tokens = resp.usage.total_tokens
    return lat, tokens

def run_benchmark():
    print("="*80)
    print("🧠 INITIATING EMPIRICAL FINOPS BENCHMARK (Vertex AI Zero-Mock)")
    print("="*80)
    
    total = len(TEST_QUERIES)
    local_hits = 0
    
    gemini_total_ms = 0.0
    gemini_total_tokens = 0
    groq_total_ms = 0.0
    groq_total_tokens = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Q{i}/{total}] {query[:60]}...")
        
        # 1. First Pass: Can Cortex Local RAG answer it without GCP?
        # Note: we use Cortex's built-in fetch without touching ask() 
        context = cortex.retrieve_context(query)
        if context and len(context) > 20 and ("STATIC" in context or "VECTOR" in context):
            local_hits += 1
            print(" 🛡️  Resolved LOCALLY (Cache/ChromaDB). API Bypassed.")
            continue
            
        # 2. Not bypassed: Dispatch to both models empirically
        print(" ☁️  Routing to GCP Vertex AI for complex resolution...")
        
        try:
            gem_lat, gem_tok = ask_gemini(query)
            gemini_total_ms += gem_lat
            gemini_total_tokens += gem_tok
            print(f"      [Gemini 2.5 Pro]    Latency: {gem_lat:.2f}s | Tokens Consumed: {gem_tok}")
        except Exception as e:
            print(f"      [Gemini 2.5 Pro]    ❌ Error: {e}")
            
        try:
            groq_lat, groq_tok = ask_groq(query)
            groq_total_ms += groq_lat
            groq_total_tokens += groq_tok
            print(f"      [Groq Llama-3.3-70b] Latency: {groq_lat:.2f}s | Tokens Consumed: {groq_tok}")
        except Exception as e:
            print(f"      [Groq Llama-3.3-70b] ❌ Error: {e}")

    # === REPORTING ===
    print("\n" + "="*80)
    print("📊 FINAL EMPIRICAL AUDIT RESULTS (Side-by-Side)")
    print("="*80)
    
    bypass_pct = (local_hits / total) * 100
    print(f"✅ RAG Local Offload: {bypass_pct:.1f}% of queries NEVER touched Vertex AI.")
    print("-" * 80)
    
    # Calculation strictly for the calls that hit the models
    api_calls = total - local_hits
    if api_calls > 0:
        avg_gem_lat = gemini_total_ms / api_calls
        avg_groq_lat = groq_total_ms / api_calls
        
        gem_tps = gemini_total_tokens / gemini_total_ms if gemini_total_ms > 0 else 0
        groq_tps = groq_total_tokens / groq_total_ms if groq_total_ms > 0 else 0
        
        print(f"{'EMPIRICAL METRIC':<25} | {'GEMINI 2.5 PRO (Vertex)':<25} | {'GROQ LLAMA-3.3-70B':<25}")
        print("-" * 80)
        print(f"{'Queries Processed':<25} | {api_calls:<25} | {api_calls:<25}")
        print(f"{'Total Network Time':<25} | {gemini_total_ms:.2f}s {' ':<18} | {groq_total_ms:.2f}s")
        print(f"{'Average Latency / Req':<25} | {avg_gem_lat:.2f}s {' ':<18} | {avg_groq_lat:.2f}s")
        print(f"{'Total Tokens Executed':<25} | {gemini_total_tokens:,} {' ':<23} | {groq_total_tokens:,}")
        print(f"{'Network Efficiency (TPS)':<25} | {gem_tps:.1f} Tokens/s {' ':<11} | {groq_tps:.1f} Tokens/s")
    else:
        print("All queries were absorbed by the local database. No external consumption.")
        
    print("="*80)

if __name__ == '__main__':
    run_benchmark()
