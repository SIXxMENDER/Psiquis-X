# 🏛️ SOVEREIGN QUANT: ARCHITECTURE MAP
## High-Frequency Verifiable Intelligence

This map represents the sovereignty flow of the system. It is not a simple script; it is a cryptographic chain of custody for financial truth.

```mermaid
graph TD
    subgraph External_World
        Binance[Binance API - OHLCV Data]
    end

    subgraph Sovereign_Engine_Rust
        Math[High-Performance Math Engine]
        Merkle[Merkle Tree Generator]
        Ledger[audit_ledger.json - Immutable]
    end

    subgraph Courtroom_Layer_LangGraph
        Strategist[Lead Quant Strategist - Alpha]
        CRO[Chief Risk Officer - Security]
        CIO[Chief Investment Officer - Verdict]
    end

    subgraph Output_Layer
        Report[FINAL_AUDIT_REPORT.md]
    end

    Binance --> Math
    Math --> Strategist
    Math --> CRO
    
    Strategist <--> CRO
    
    Strategist --> CIO
    CRO --> CIO
    
    CIO --> Merkle
    Math --> Merkle
    
    Merkle --> Ledger
    CIO --> Report
    Ledger --> Report

    style Binance fill:#f9f,stroke:#333,stroke-width:2px
    style Ledger fill:#ff9,stroke:#333,stroke-width:4px
    style CIO fill:#f66,stroke:#333,stroke-width:2px
```

### 🔐 Integrity Protocol
*   **Rust Sovereign Layer:** Deterministic calculations protected against memory manipulation.
*   **Adversarial Consensus:** No strategy is approved without cross-scrutiny.
*   **Merkle Evidence:** Each block contains a Merkle root linking raw data to the final AI decision.
