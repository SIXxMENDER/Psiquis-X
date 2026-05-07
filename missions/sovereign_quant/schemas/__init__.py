from pydantic import BaseModel, Field

class SimulationResult(BaseModel):
    total_trades: int
    winning_trades: int
    win_rate: float
    net_profit_percent: float
    max_drawdown_percent: float
    sharpe_ratio: float

class QuantConsensus(BaseModel):
    is_approved: bool = Field(description="True if the strategy parameters are solid and verified, False if they need readjustment.")
    reasoning: str = Field(description="The professional quant explanation of why this was approved or rejected.")
    rationale_ledger: str = Field(description="A single technical and blunt sentence justifying the block sealing for the ledger.")
    new_ema_short: int = Field(description="Suggested new short EMA period, or the same if approved.")
    new_ema_mid: int = Field(description="Suggested new mid EMA period, or the same if approved.")
    new_ema_long: int = Field(description="Suggested new long EMA period, or the same if approved.")
