import os
import sys
import json
import subprocess
from datetime import datetime
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

# Import schemas
from schemas import SimulationResult, QuantConsensus

# Add root to sys.path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# Import real cortex
from core.S_SERIES.cortex import cortex

# --- CONSTANTS ---
RUST_BINARY = os.path.join(os.path.dirname(__file__), 'rust_core', 'target', 'release', 'rust_core.exe')
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'btc_1h.csv')
LEDGER_PATH = os.path.join(os.path.dirname(__file__), 'audit_ledger.json')
REPORT_PATH = os.path.join(os.path.dirname(__file__), 'FINAL_AUDIT_REPORT.md')

# --- STATE ---
class AuditState(TypedDict):
    ema_short: int
    ema_mid: int
    ema_long: int
    iteration: int
    rust_results_json: str
    quant_discussion: str
    consensus_json: str
    is_approved: bool
    sealed_hash: str

# --- NODES ---
def run_simulation_node(state: AuditState):
    print("\n" + "="*50)
    print("   CORE RUST ENGINE: MISSION INITIALIZED")
    print("="*50)
    print(f"[PROCESS] Running Monte Carlo Simulation (Iteration {state['iteration']})...")
    
    # Args: run_simulation <csv> <ema_short> <ema_mid> <ema_long> <ema_trend>
    cmd = [
        RUST_BINARY, 
        "run_simulation", 
        CSV_PATH, 
        str(state['ema_short']), 
        str(state['ema_mid']), 
        str(state['ema_long']), 
        "200"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[FATAL] Rust Engine Error: {result.stderr}")
        return {"rust_results_json": "{}"}
        
    output = result.stdout.strip()
    print(f"[DATA] Engine Math Output: {output}")
    return {"rust_results_json": output}

def quant_debate_node(state: AuditState):
    print("\n" + "*"*50)
    print("   COURTROOM LAYER: ADVERSARIAL CONSENSUS")
    print("*"*50)
    print(f"[STATUS] Auditing Iteration {state['iteration']} via Triple-Agent Protocol...")
    
    # Prompts provided by user
    OPTIMIST_PROMPT = """Actúa como Lead Quantitative Strategist de un fondo institucional Web3 de alta frecuencia. Tu objetivo es la generación de Alpha mediante el aprovechamiento de ineficiencias de mercado en el par BTC/USDT.
REGLAS DE EVALUACIÓN:
1. Prioriza el 'net_profit_percent' y el 'win_rate' por encima de la volatilidad intradía.
2. Analiza las EMAs (3, 12, 21) calculadas por el núcleo de Rust: busca confirmación de momentum. Si la EMA corta está sobre la larga, ignora correcciones menores; es una señal de acumulación institucional.
3. Argumenta basado en el 'Opportunity Cost': en un mercado de alta volatilidad, la inacción es una pérdida latente de capital.
4. Tu veredicto debe ser agresivo si el 'win_rate' supera el 55% y la tendencia es alcista.
FORMATO DE RESPUESTA:
- Tesis de Inversión: (Breve y técnica)
- Justificación Matemática: (Basada en los datos de Rust)
- Nivel de Confianza: (0-100%)
- Recomendación: [PROCEED] o [WAIT]
Tono: Ejecutivo, directo, orientado a la rentabilidad y al despliegue inmediato de capital."""
    
    SCEPTIC_PROMPT = """Actúa como Chief Risk Officer (CRO) de un fondo de cobertura institucional DeFi. Tu única misión es proteger el capital y detectar fallos sistémicos en la estrategia propuesta. Tu éxito no se mide por las ganancias, sino por las pérdidas evitadas.
REGLAS DE EVALUACIÓN:
1. Escrutinio del Sharpe Ratio: Si el valor es inferior a 2.0, califica el retorno como "ruido" no compensado por el riesgo.
2. Análisis de Drawdown: Evalúa si el net_profit_percent justifica la exposición en temporalidad de 1h, considerando la volatilidad inherente de BTC.
3. Cuestionamiento de Indicadores: Argumenta que los cruces de EMAs son indicadores retrasados ("lagging") y propensos a "fakeouts" en entornos de baja liquidez o manipulación de mercado.
4. Tu sesgo es la preservación absoluta del Tesoro (Treasury): ante cualquier anomalía estadística en los datos de Rust, tu voto debe ser negativo.
FORMATO DE RESPUESTA:
- Análisis de Riesgo: (Identificación de fallas en la tesis de inversión)
- Métricas de Alerta: (Uso estricto del Sharpe Ratio y Drawdown de Rust)
- Veredicto de Seguridad: [VETO] o [CAUTION]
Tono: Frío, clínico, escéptico y extremadamente conservador."""
    
    JUDGE_PROMPT = f"""Act as Chief Investment Officer (CIO) and Governance Guardian of a Digital Sovereign Fund. Your role is dialectical synthesis: you must decide if the Alpha opportunity compensates for systemic risk based on immutable Rust data and analyst arguments.
REGLAS DE DECISIÓN:
1. Data Weighting: The mathematical report from the Rust engine is the base truth. If Sharpe Ratio < 1.0, rejection is automatic regardless of optimism.
2. Conflict Resolution: Evaluate the technical validity of the Risk Manager versus the opportunity of the Alpha Hunter. Do not seek a middle ground; seek the most institutionally robust decision.
3. Protocol Validation: If approved, your synthesis will become the 'Rationale' sealed via 'seal_block' in the audit_ledger.json, being auditable forever on the chain.
4. Your verdict is final and binding for the Smart Contract.
RUST DATA: {state['rust_results_json']}
RESPONSE FORMAT (STRICT JSON IN ENGLISH):
{{
    "is_approved": bool,
    "reasoning": "Synthesis of the debate in English",
    "rationale_ledger": "A single blunt technical sentence in English justifying the block sealing",
    "new_ema_short": int,
    "new_ema_mid": int,
    "new_ema_long": int
}}
Tone: Authoritative, analytical, neutral, and responsible for institutional capital."""

    print("   [ANALYSIS] Alpha Hunter is scanning for market inefficiencies...")
    print("   [AUDIT] Risk Manager is scrutinizing capital exposure...")
    print("   [VERDICT] CIO is finalizing institutional rationale...")
    
    try:
        verdict = cortex.ask(JUDGE_PROMPT, system_prompt="Output only raw JSON matching the schema.", model=None)
        
        if "```json" in verdict:
            verdict = verdict.split("```json")[-1].split("```")[0].strip()
        elif "```" in verdict:
            verdict = verdict.split("```")[-1].split("```")[0].strip()
            
        consensus = json.loads(verdict)
        is_approved = consensus.get("is_approved", False)
        
        print(f"\n[FINAL VERDICT] {'STRATEGY APPROVED' if is_approved else 'STRATEGY REJECTED'}")
        print(f"[REASONING] {consensus.get('reasoning', '')}")
        
        return {
            "consensus_json": json.dumps(consensus),
            "is_approved": is_approved,
            "ema_short": consensus.get("new_ema_short", state['ema_short']),
            "ema_mid": consensus.get("new_ema_mid", state['ema_mid']),
            "ema_long": consensus.get("new_ema_long", state['ema_long']),
            "iteration": state['iteration'] + 1
        }
    except Exception as e:
        print(f"[ERROR] Courtroom Failure: {e}")
        return {"is_approved": False, "iteration": state['iteration'] + 1}

def router_node(state: AuditState):
    if state['is_approved']:
        return "seal_blockchain"
    elif state['iteration'] > 3:
        print("[LIMIT] Maximum validation attempts reached. Forcing immutable seal for forensic audit.")
        return "seal_blockchain"
    else:
        print("[RETRY] Consensus not reached. Adjusting parameters for next Monte Carlo cycle...")
        return "run_simulation"

def seal_blockchain_node(state: AuditState):
    print("\n" + "#"*50)
    print("   BLOCKCHAIN LAYER: IMMUTABLE SEALING")
    print("#"*50)
    
    params_json = json.dumps({
        "ema_short": state['ema_short'],
        "ema_mid": state['ema_mid'],
        "ema_long": state['ema_long']
    })
    
    cmd = [
        RUST_BINARY, 
        "seal_block", 
        LEDGER_PATH, 
        params_json, 
        state['rust_results_json'], 
        state['consensus_json']
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Sealing Failure: {result.stderr}")
        return {"sealed_hash": "ERROR"}
    else:
        res_data = json.loads(result.stdout.strip())
        sealed_hash = res_data.get("sealed_hash", "0x000")
        print(f"[SUCCESS] Block Sealed. Merkle Root: {sealed_hash[:16]}...")
        return {"sealed_hash": sealed_hash}

def generate_report_node(state: AuditState):
    print("\n" + "-"*50)
    print("   OUTPUT LAYER: EXECUTIVE SUMMARY GENERATION")
    print("-"*50)
    
    results = json.loads(state['rust_results_json'])
    consensus = json.loads(state['consensus_json'])
    
    report_content = f"""# 🏛️ SOVEREIGN QUANT: FINAL AUDIT REPORT
## Status: {"APPROVED" if state['is_approved'] else "REJECTED"}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Merkle Block Hash:** `{state['sealed_hash']}`

---

### 🧠 CIO Synthesis
> "{consensus.get('reasoning', 'N/A')}"

**Ledger Rationale:**
`{consensus.get('rationale_ledger', 'N/A')}`

---

### 📊 Verification Metrics (Rust Engine)
| Metric | Value |
| :--- | :--- |
| **Win Rate** | {results.get('win_rate', 0):.2f}% |
| **Net Profit** | {results.get('net_profit_percent', 0):.2f}% |
| **Sharpe Ratio** | {results.get('sharpe_ratio', 0):.2f} |
| **Max Drawdown** | {results.get('max_drawdown_percent', 0):.2f}% |
| **Total Trades** | {results.get('total_trades', 0)} |

---

### 🔐 Audited Strategy Parameters
*   **Short EMA:** {state['ema_short']}
*   **Mid EMA:** {state['ema_mid']}
*   **Long EMA:** {state['ema_long']}
*   **Timeframe:** 1h (Binance Data)

---

**[VERDICT] READY FOR HIGH-FREQUENCY EXECUTION.**
"""
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"[DONE] Executive Report generated at: {REPORT_PATH}")
    return {}

# --- GRAPH COMPILE ---
def build_quant_graph():
    workflow = StateGraph(AuditState)
    
    workflow.add_node("run_simulation", run_simulation_node)
    workflow.add_node("quant_debate", quant_debate_node)
    workflow.add_node("seal_blockchain", seal_blockchain_node)
    workflow.add_node("generate_report", generate_report_node)
    
    workflow.set_entry_point("run_simulation")
    workflow.add_edge("run_simulation", "quant_debate")
    
    workflow.add_conditional_edges(
        "quant_debate",
        router_node,
        {
            "seal_blockchain": "seal_blockchain",
            "run_simulation": "run_simulation"
        }
    )
    
    workflow.add_edge("seal_blockchain", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

if __name__ == "__main__":
    print("\n" + "!"*60)
    print("!!!   SOVEREIGN QUANT PROTOCOL INFILTRATION: ACTIVE   !!!")
    print("!"*60)
    
    graph = build_quant_graph()
    initial_state = {
        "ema_short": 3,
        "ema_mid": 12,
        "ema_long": 21,
        "iteration": 1,
        "rust_results_json": "{}",
        "quant_discussion": "",
        "consensus_json": "{}",
        "is_approved": False,
        "sealed_hash": ""
    }
    
    if not os.path.exists(RUST_BINARY):
        print(f"[WARNING] Rust binary not found at {RUST_BINARY}. Please build it first.")
        sys.exit(1)
        
    final_state = graph.invoke(initial_state)
    print("\n[FINISH] MISSION ACCOMPLISHED. SYSTEM SECURE.")
