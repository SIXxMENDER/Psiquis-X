# 🏛️ SOVEREIGN GOVERNANCE PROTOCOL
## Adversarial Consensus & Deterministic Risk Mitigation

This document outlines the institutional governance logic implemented in the `sovereign_quant` module. Unlike standard algorithmic trading systems, Psiquis-X operates under a multi-agent adversarial framework to ensure capital preservation.

### 🧠 The Triple-Agent Consensus
Every execution cycle is scrutinized by three specialized AI nodes:
1.  **Lead Quant Strategist (Alpha Hunter):** Focuses on yield, momentum, and market inefficiencies.
2.  **Chief Risk Officer (CRO):** Focuses on volatility, drawdown, and systemic risk.
3.  **Chief Investment Officer (CIO):** Performs the final dialectical synthesis.

### 🔐 The Deterministic Kill-Switch
A core feature of our governance is the **Automated Neutralization Protocol**. If the mathematical reality (calculated by the Rust Core) fails to meet institutional standards, the CIO enforces a "Safe State".

**Key Rule: Sharpe Ratio < 1.0**
- If the backtesting engine returns a Sharpe Ratio below 1.0, the strategy is deemed **statistically invalid** for sovereign capital.
- **Action:** The CIO automatically zeroes out execution parameters (EMA periods).
- **Result:** The system enters a state of **Active Inaction** (Total Trades: 0).

### ⛓️ Merkle-Proofed Audit Trail
All decisions, including rejections and "Kill-Switch" activations, are hashed into a Merkle Tree and sealed in the `audit_ledger.json`. This ensures that every moment of "Inaction" is as auditable and transparent as any trade.

> *"In Sovereign Quant, we don't just optimize for profit; we optimize for certainty. The power to say 'No' is the ultimate institutional advantage."*
