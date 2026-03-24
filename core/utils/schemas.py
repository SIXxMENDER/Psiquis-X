# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Psiquis-X: Enterprise Multi-Agent Framework
# Proprietary Software - All Rights Reserved
# Copyright (c) 2026 SIXxMENDER & Bosniack-94
# -----------------------------------------------------------------------------
# WARNING: This source code is proprietary and confidential. 
# Unauthorized copying, distribution, or use via any medium is strictly 
# prohibited. This code is provided solely for authorized technical review 
# and evaluation purposes.
# -----------------------------------------------------------------------------

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union

# --- Base Schemas ---
class AgentOutput(BaseModel):
    status: str = Field(..., description="Execution status: SUCCESS or ERROR")
    error: Optional[str] = Field(None, description="Error message if status is ERROR")

# --- P0: Research ---
class ResearchInput(BaseModel):
    query: str = Field(..., description="The research question or objective")

class ResearchOutput(AgentOutput):
    result: str = Field(..., description="Short summary of the result")
    response: str = Field(..., description="Detailed research findings")

# --- P3: Code Generation ---
class CodeGenInput(BaseModel):
    task_description: str = Field(..., description="Description of the code to generate")
    previous_error: Optional[str] = Field(None, description="Error from previous attempt (for self-correction)")
    previous_code: Optional[str] = Field(None, description="Code from previous attempt")

class CodeGenOutput(AgentOutput):
    python_code: str = Field("", description="The generated Python code")
    description: str = Field("", description="Description of what was generated")

# --- P4: Backtest ---
class BacktestInput(BaseModel):
    historical_data: Union[List[Dict[str, Any]], str] = Field(..., description="Historical data (list of dicts or CSV path)")
    strategy_code: str = Field(..., description="Python code defining the strategy")
    initial_capital: float = Field(10000.0, description="Initial capital")
    commission: float = Field(0.001, description="Commission rate (e.g., 0.001 for 0.1%)")

class BacktestOutput(AgentOutput):
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics (ROI, Sharpe, etc.)")
    trade_returns: List[float] = Field(default_factory=list, description="List of returns per trade")
    equity_curve: List[float] = Field(default_factory=list, description="Equity curve points")

# --- P8: IO / Integration ---
class IOInput(BaseModel):
    file_name: str = Field(..., description="Name of the file to write")
    code: Optional[str] = Field(None, description="Content to write (alias 1)")
    content_to_save: Optional[str] = Field(None, description="Content to write (alias 2)")
    target_directory: str = Field("agentes_en_desarrollo", description="Target directory")

    @property
    def content(self) -> str:
        return self.code or self.content_to_save or ""

class IOOutput(AgentOutput):
    modified_file: str = Field("", description="Full path of the written file")
    file_path: str = Field("", description="Full path (alias)")

# --- P11: Narrative ---
class NarrativeInput(BaseModel):
    technical_logs: Dict[str, Any] = Field(..., description="Technical logs to translate")

class NarrativeOutput(AgentOutput):
    narrative: str = Field("", description="The generated narrative story")

# --- Orchestration Schemas (Merged from utils) ---
class Job(BaseModel):
    job_id: str
    agente: str
    parametros: Dict[str, Any] = Field(default_factory=dict)
    dependencias: List[str] = Field(default_factory=list)
    agente_experimental_path: Optional[str] = None

class EsquemaPlan(BaseModel):
    plan_id: str
    objetivo_general: Optional[str] = "Strategic Enterprise Objective"
    parametros_globales: Dict[str, Any] = Field(default_factory=dict)
    plan_de_ejecucion: List[Job]

class SRIP(BaseModel):
    """Structured Response for Intervention Plan (P6b diagnosis)"""
    diagnosis: str = "System Diagnosis (Auto-generated)"
    suggested_action: str = "CONTINUE" # CONTINUE, OPTIMIZE, HUMAN_INTERVENTION, REPLAN
    action_details: Dict[str, Any] = Field(default_factory=dict)
    gravity: int = 1

    @classmethod
    def create_safe_fallback(cls, error_msg: str, original_input: Any = None):
        """Safe state generator for parsing failures"""
        return cls(
            diagnosis=f"FALLBACK CORE: Audit processing error. {error_msg}",
            suggested_action="CONTINUE",
            action_details={"raw_input": str(original_input)[:200]},
            gravity=2
        )
