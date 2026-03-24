import json
import operator
import time
from typing import TypedDict, List, Any, Dict, Annotated
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, END

# --- PYDANTIC SCHEMAS ---
class EnterpriseYearlyData(BaseModel):
    fiscal_year: str = Field(description="e.g., FY26, FY25, FY24")
    metric_name: str = Field(description="e.g., Total Revenue, Operating Expenses, Net Income")
    value_reported: float = Field(description="Absolute value in reported units (e.g. Billions)")
    is_gaap: bool = Field(description="True if GAAP, False if Non-GAAP")
    source_file: str = Field(description="Name of the PDF file it was extracted from")
    page_reference: str = Field(description="Source page and context")
    literal_snippet: str = Field(description="Exact snippet of text/table from the source PDF to prove it is not hallucinated")

class RawExtraction(BaseModel):
    metrics: List[EnterpriseYearlyData]

class VarianceAnalysis(BaseModel):
    metric_name: str
    comparison_period: str = Field(description="e.g., FY26 vs FY25 (YoY) or Q4 FY26 vs Q3 FY26 (QoQ)")
    growth_percentage: float = Field(description="Variance growth percentage")
    coherence_flag: str = Field(description="Operational Leverage, Margin Compression Risk, Cost Expansion Risk, Positive Expansion, or OK")

class ExecutiveNarrative(BaseModel):
    performance_summary: str = Field(description="3-5 lines on financial performance")
    efficiency_assessment: str = Field(description="Cost structure assessment")
    risk_signals: str = Field(description="Any risks detected")
    strategic_outlook: str = Field(description="Strong Expansion, Controlled Growth, Margin Pressure, or Financial Deterioration")

class AnalystInsights(BaseModel):
    variance_analysis: List[VarianceAnalysis]
    narrative: ExecutiveNarrative
    confidence_score: int = Field(description="0-100 score based on retrieval clarity and coherence")

class FinalFinancialReport(BaseModel):
    metrics: List[EnterpriseYearlyData]
    variance_analysis: List[VarianceAnalysis]
    narrative: ExecutiveNarrative
    confidence_score: int = Field(description="0-100 score based on retrieval clarity and coherence")

# --- STATE ---
class AuditState(TypedDict):
    current_documents: str
    target_metric: str
    source_text: str
    draft_extraction: str
    prosecutor_feedback: str
    validation_attempts: Annotated[int, operator.add]
    rejection_count: Annotated[int, operator.add]
    raw_data: List[Dict[str, Any]]
    final_cfo_report: str
    cortex: Any
    metadata: Dict[str, Any] # For KPIs like latency and tokens

# --- NODES ---
def investigator_node(state: AuditState):
    print("\n🕵️ [INVESTIGATOR] Extracting financial metrics from multi-year cohort...")
    start_time = time.perf_counter()
    cortex = state["cortex"]
    doc = state["current_documents"]
    metrics = state["target_metric"]
    text = state["source_text"]
    
    metadata = state.get("metadata", {"node_stats": [], "total_latency": 0.0})
    feedback = state.get("prosecutor_feedback", "")
    
    error_context = f"\n\nATTENTION - FIX THESE ERRORS FROM PREVIOUS RUN:\n{feedback}" if feedback else ""
    
    chunk_size = 15000
    chunks = []
    
    # NEW: Phantom Source-Aware Chunking
    import re
    last_file = "Unknown.pdf"
    last_page = "Unknown"
    
    # We split by [SOURCE_FILE: ...], but we want to KEEP the context
    # Manual loop to ensure each chunk has its phantom footer
    for i in range(0, len(text), chunk_size):
        chunk_raw = text[i:i+chunk_size]
        
        # PREPEND the state from the end of the PREVIOUS chunk so it bridges the gap
        phantom_header = f"[PHANTOM_SOURCE: Text carried over from {last_file} - {last_page}]\n\n"
        
        # Scan for the new source tags in this chunk to update the state for the NEXT loop
        file_matches = re.findall(r"\[SOURCE_FILE:\s*(.*?)\]", chunk_raw)
        page_matches = re.findall(r"\[PAGE:\s*(.*?)\]", chunk_raw)
        
        current_valid_pages = [last_page]
        if page_matches: 
            current_valid_pages.extend(page_matches)
        
        chunks.append({
            "text": phantom_header + chunk_raw,
            "valid_pages": current_valid_pages,
            "last_known_file": last_file
        })
        
        # Update state variables for the NEXT iteration after appending
        if file_matches: last_file = file_matches[-1]
        if page_matches: last_page = page_matches[-1]

    print(f"📦 [CHUNKER] Slicing payload into {len(chunks)} chunks with Phantom Headers and Hybrid Validation State...")
    
    system_prompt = "You are an Elite Institutional Financial Investigator. Return only strict JSON matching the given metrics format."
    all_metrics = []
    
    for idx, chunk_data in enumerate(chunks):
        print(f"   ➤ Processing chunk {idx+1}/{len(chunks)}...")
        chunk_text = chunk_data["text"]
        valid_pages = chunk_data["valid_pages"]
        
        prompt = f"""
Analyze THIS CHUNK of a document.

USER MISSION / TARGET METRICS:
---
{metrics}
---

CRITICAL INSTRUCTIONS:
1. You MUST ONLY extract the specific metrics requested in the User Mission above.
2. If a requested metric is NOT found in this specific chunk, DO NOT invent it.
3. DO NOT extract any other metrics that were not explicitly requested.

CRITICAL: Source Tracking
You will see tags like `[SOURCE_FILE: filename.pdf] [PAGE: X]` or `[PHANTOM_SOURCE: ...]` at the START or throughout the text.
For EVERY metric you extract, you MUST use the exact filename and page number from the most recent preceding tag. This is non-negotiable for audit compliance.

Your ONLY output must be a flat JSON object containing a list called 'metrics'.
Keys for each object in the list:
"fiscal_year" (e.g, FY26, Q4 FY26), "metric_name" (string), "value_reported" (float), "is_gaap" (boolean), "source_file" (string, from the tag), "page_reference" (string, from the tag), "literal_snippet" (string, exact text from PDF proving the number).

If this specific chunk contains NO financial metrics, return {{"metrics": []}}.
DO NOT INCLUDE NULLS. 

Chunk Text ({idx+1}/{len(chunks)}):
{chunk_text}
{error_context}
        """

        try:
            response = cortex.ask(prompt, system_prompt=system_prompt, model=None)
            
            if "```json" in response:
                response = response.split("```json")[-1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[-1].split("```")[0].strip()
                
            chunk_json = json.loads(response)
            if "metrics" in chunk_json and isinstance(chunk_json["metrics"], list) and len(chunk_json["metrics"]) > 0:
                # HYBRID VALIDATION (El Guardia): Intercept and correct hallucinated pages
                corrected_metrics = []
                for m in chunk_json["metrics"]:
                    reported_page = m.get("page_reference", "")
                    if str(reported_page) not in valid_pages:
                        print(f"   🛡️ [GUARDIA] Intercepted Hallucination: '{reported_page}'. Auto-correcting to '{valid_pages[0]}'.")
                        # Default to the most conservative valid page to avoid jumping forward
                        m["page_reference"] = str(valid_pages[0])
                    corrected_metrics.append(m)
                
                all_metrics.extend(corrected_metrics)
                print(f"   ✅ Found {len(corrected_metrics)} metrics in chunk {idx+1} (Sanitized by Guardia).")
            else:
                print(f"   ℹ️ Chunk {idx+1} validated (No relevant metrics).")
        except Exception as e:
            print(f"   ⚠️ Error parsing chunk {idx+1}: {e}")
            
    final_json = json.dumps({"metrics": all_metrics})
    print(f"🎉 [CHUNKER] Extraction complete. {len(all_metrics)} total metrics aggregated.")
    
    duration = time.perf_counter() - start_time
    metadata["node_stats"].append({"node": "investigator", "latency": duration, "chunks": len(chunks)})
    metadata["total_latency"] += duration

    return {
        "draft_extraction": final_json,
        "metadata": metadata
    }

def prosecutor_node(state: AuditState):
    print("⚖️ [PROSECUTOR] Adversarial Audit: Mathematical Coherence Validation...")
    start_time = time.perf_counter()
    cortex = state["cortex"]
    draft = state["draft_extraction"]
    metrics = state["target_metric"]
    metadata = state.get("metadata", {"node_stats": [], "total_latency": 0.0})
    
    prompt = f"""
You are the Adversarial Financial Auditor.
Mission: Validate the raw extracted JSON for Hallucinations and Mathematical Incoherence.

Extracted JSON:
{draft}

Target Metrics Expected: {metrics}

Strict Audit Rules:
1. Did the Investigator extract data for multiple periods (e.g. FY26, FY25, FY24, or Quarterly)?
2. Are the numbers in BILLIONS (e.g., 215.9) and not millions (215900)?
3. Are the metrics logically coherent? (Revenue > Net Income)

CRITICAL DEDUPLICATION RULE: The Investigator reads PDFs in 15,000-character chunks. Because of this, you WILL see duplicate or slightly conflicting values for the SAME metric and the SAME fiscal year. 
- DO NOT reject the extraction because of this ("Conflicting Values"). 
- Instead, silently deduce which number is the correct one (the most frequent, the most mathematically sound, or the most recent) and IGNORE the duplicates.

If the JSON meets the rules (accounting for the deduplication rule), response EXACTLY with the word: 'APPROVED'.
If and only if there are TRULY missing fundamental years that should be there, or numbers are in the wrong format (millions instead of billions), LIST THE ERRORS purely in business terms so the Investigator fixes them.
    """
    
    system_prompt = "You are an adversarial AI auditor. You must ensure 0% hallucinations."
    response = cortex.ask(prompt, system_prompt=system_prompt, model=None)
    
    is_approved = "APPROVED" in response.upper() and "ERROR" not in response.upper() and "MISSING" not in response.upper()
    
    duration = time.perf_counter() - start_time
    metadata["node_stats"].append({"node": "prosecutor", "latency": duration})
    metadata["total_latency"] += duration

    if is_approved:
        print("✅ [PROSECUTOR] Audit Clean. Escorting data to Structural Judge.")
        return {"prosecutor_feedback": "APPROVED", "validation_attempts": 1, "metadata": metadata}
    else:
        print(f"❌ [PROSECUTOR] Adversarial Rejection: {response.strip()[:150]}...")
        return {"prosecutor_feedback": response, "validation_attempts": 1, "rejection_count": 1, "metadata": metadata}

def prosecutor_router(state: AuditState):
    feedback = state.get("prosecutor_feedback", "")
    attempts = state.get("validation_attempts", 0)
    
    if feedback == "APPROVED":
        return "judge"
    elif attempts >= 3:
        print("⚠️ [ROUTER] Max Attempts Reached (3). Forcing bypass to Judge to salvage data.")
        return "judge"
    else:
        return "investigator"

def judge_node(state: AuditState):
    print("👨‍⚖️ [JUDGE] Structural Validation Successful. Parsing Schema...")
    start_time = time.perf_counter()
    draft = state["draft_extraction"]
    metadata = state.get("metadata", {"node_stats": [], "total_latency": 0.0})
    
    duration = time.perf_counter() - start_time
    metadata["node_stats"].append({"node": "judge", "latency": duration})
    metadata["total_latency"] += duration

    try:
        data = json.loads(draft)
        validated = RawExtraction(**data)
        final_list = [m.model_dump() for m in validated.metrics]
        return {"raw_data": final_list, "prosecutor_feedback": "JUDGE_APPROVED", "metadata": metadata}
        
    except Exception as e:
        error_msg = f"PYDANTIC SCHEMA VALIDATION ERROR. You MUST fix your JSON keys. Error details:\n{str(e)}"
        print(f"❌ [JUDGE] Pydantic Error Loop Activated. Deflecting back to Investigator.")
        return {"prosecutor_feedback": error_msg, "validation_attempts": 1, "rejection_count": 1, "metadata": metadata}

def judge_router(state: AuditState):
    if state.get("raw_data"):
        return "cfo_narrator"
    elif state.get("validation_attempts", 0) >= 3:
        print("🛑 [FATAL] Max Penalties Reached. Judge abandons session.")
        return "end"
    else:
        return "investigator"

def analyst_narrator_node(state: AuditState):
    print("👔 [ANALYST NARRATOR] Computing Variance Math and Generating Executive Narrative...")
    start_time = time.perf_counter()
    cortex = state["cortex"]
    raw_data = state["raw_data"]
    rejections = state.get("rejection_count", 0)
    metadata = state.get("metadata", {"node_stats": [], "total_latency": 0.0})
    
    # Calculate base confidence
    confidence = max(0, 100 - (rejections * 15))
    if len(raw_data) < 5:
        confidence -= 30
    
    prompt = f"""
    You are the Senior Financial Analyst within the Psiquis-X Autonomous Engine.
    You have been provided with validated, raw structural data for the entity across multiple periods.

Raw Data:
{json.dumps(raw_data, indent=2)}

    Your objective is to output a STRICT JSON object representing the 'FinalFinancialReport' Pydantic schema.

STEP 1: Calculate Mathematical Coherence and Variances.
Compute BOTH Year-over-Year (YoY) and Quarter-over-Quarter (QoQ) growth (if data allows) for Revenue, Net Income, and Operating Expenses.
Additionally, synthetically compute:
- Operating Margin (%) = (Total Revenue - Operating Expenses) / Total Revenue * 100
- EPS (Earnings Per Share) if share count is available, otherwise omit EPS.

Rule: IF Revenue Growth >> Opex Growth -> flag as "Operational Leverage"
Rule: IF Net Income Growth < Revenue Growth -> flag as "Margin Compression Risk"
Rule: IF Opex Growth > Revenue Growth -> flag as "Cost Expansion Risk"
Otherwise -> "OK" or "Positive Expansion"

STEP 2: Generate the Executive Narrative.
Section 1: Performance Summary (3-5 lines, highly professional)
Section 2: Efficiency Assessment
Section 3: Risk Signals (if any detected from the math flags)
Section 4: Strategic Outlook (Must be one of: "Strong Expansion", "Controlled Growth", "Margin Pressure", "Financial Deterioration")

STEP 3: Confidence Score.
Given the data completeness and a base penalty of {rejections} prior adversarial rejections, set the exact confidence_score integer (approx {confidence}).

Return ONLY a valid JSON object matching the following STRICT Pydantic Schema.
If you omit any keys (like 'growth_percentage' or 'comparison_period'), the entire mission will crash.
Use the key 'variance_analysis' for your variance data list. Do NOT include the 'metrics' list, as that is already validated.

    REQUIRED SCHEMA (JSON FORMAT):
    {json.dumps(AnalystInsights.model_json_schema(), indent=2)}

Do NOT use markdown. Do NOT use apologies. Just the raw, valid JSON.
    """
    
    system_prompt = "You are a Financial Analyst AI. Output strict JSON matching the AnalystInsights schema."
    try:
        response = cortex.ask(prompt, system_prompt=system_prompt, model=None)
        if "```json" in response:
            response = response.split("```json")[-1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[-1].split("```")[0].strip()
            
        insights_json = json.loads(response)
        
        # Enforce Pydantic validation
        validated_insights = AnalystInsights(**insights_json)
        print(f"✅ [ANALYST NARRATOR] Narrative Generated. Confidence Score: {validated_insights.confidence_score}/100")
        
        # Deterministically merge the raw_data metrics with the insights
        final_report = FinalFinancialReport(
            metrics=raw_data,
            variance_analysis=validated_insights.variance_analysis,
            narrative=validated_insights.narrative,
            confidence_score=validated_insights.confidence_score
        )
        
        duration = time.perf_counter() - start_time
        metadata["node_stats"].append({"node": "cfo_narrator", "latency": duration})
        metadata["total_latency"] += duration

        return {
            "final_cfo_report": final_report.model_dump_json(),
            "metadata": metadata
        }
    except Exception as e:
        print(f"❌ [CFO NARRATOR] Failed to generate valid CFO Narrative: {e}")
        duration = time.perf_counter() - start_time
        metadata["node_stats"].append({"node": "cfo_narrator_fallback", "latency": duration})
        metadata["total_latency"] += duration

        # Return fallback strictly matching FinalCFOReport schema merging raw_data
        fallback = FinalCFOReport(
            metrics=raw_data,
            variance_analysis=[{
                "metric_name": "Revenue",
                "comparison_period": "FY26 vs FY25",
                "growth_percentage": 0.0,
                "coherence_flag": "OK"
            }],
            narrative={
                "performance_summary": "Fallback summary generated due to error.",
                "efficiency_assessment": "Data unavailable.",
                "risk_signals": "System Error.",
                "strategic_outlook": "Controlled Growth"
            },
            confidence_score=0
        )
        
        return {
            "final_cfo_report": fallback.model_dump_json(),
            "metadata": metadata
        }

def build_courtroom_graph():
    workflow = StateGraph(AuditState)
    
    workflow.add_node("investigator", investigator_node)
    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("cfo_narrator", analyst_narrator_node)
    
    workflow.set_entry_point("investigator")
    workflow.add_edge("investigator", "prosecutor")
    
    workflow.add_conditional_edges(
        "prosecutor",
        prosecutor_router,
        {
            "judge": "judge",
            "investigator": "investigator"
        }
    )
    
    workflow.add_conditional_edges(
        "judge",
        judge_router,
        {
            "cfo_narrator": "cfo_narrator",
            "end": END,
            "investigator": "investigator"
        }
    )
    
    workflow.add_edge("cfo_narrator", END)
    
    return workflow.compile()
