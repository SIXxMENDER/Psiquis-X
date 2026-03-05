# Metacognitive Self-Correction Loop

The **Metacognitive Self-Correction Loop** is an autonomous error-handling and hallucination-detection mechanism built into the LangGraph orchestration layer of Psiquis-X.

## How It Works

Unlike standard LLM systems that fail silently or produce confident hallucinations, Psiquis-X monitors its own execution path in real time. If an agent detects a structural error, a logic flaw, or missing context during the *Courtroom Audit* phase, the loop automatically triggers a targeted re-evaluation.

```mermaid
stateDiagram-v2
    [*] --> TaskExecution: Start Workflow
    
    state TaskExecution {
        [*] --> DraftGeneration
        DraftGeneration --> SelfEvaluation: Internal Agent Review
        
        SelfEvaluation --> DraftGeneration: Detected Minor Issue
        SelfEvaluation --> AuditPhase: Passed Initial Check
    }
    
    TaskExecution --> AdversarialAudit
    
    state AdversarialAudit {
        [*] --> FactCheck
        FactCheck --> SchemaCheck
    }
    
    AdversarialAudit --> Finalize: All Checks Passed
    AdversarialAudit --> MetacognitiveCorrection: Error Detected
    
    state MetacognitiveCorrection {
        [*] --> AnalyzeFailure
        AnalyzeFailure --> FormulateFix
        FormulateFix --> FetchMissingContext
    }
    
    MetacognitiveCorrection --> TaskExecution: Apply Fix & Retry
    
    Finalize --> [*]: Deliver Result

    %% Styling
    classDef error fill:#e53935,color:white,font-weight:bold;
    classDef success fill:#00a67d,color:white,font-weight:bold;
    class MetacognitiveCorrection error;
    class Finalize success;
```

This self-healing capability allows long-running autonomous processes to recover from intermediate failures without requiring human intervention, ensuring high reliability for enterprise deployments.
