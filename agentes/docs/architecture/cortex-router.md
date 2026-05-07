# Universal Cortex Router

The **Universal Cortex Router** is the dynamic routing engine at the heart of Psiquis-X. It intelligently dispatches tasks across a portfolio of local and cloud-based Large Language Models (LLMs) to optimize for **latency, cost, and capability**.

## Routing Logic

Instead of relying on a single frontier model for every component of a workflow, the router analyzes the intent and complexity of the prompt:
- **Simple, repetitive tasks** (like standard text formatting or basic extraction) are routed to local models (via Ollama) or extremely fast APIs (like Groq).
- **Complex reasoning and coding** are routed to frontier models (Anthropic Claude 3.5 Sonnet, Google Gemini 2.5 Pro).

```mermaid
flowchart LR
    A[Incoming Task: server_v3_minimal] --> B{Semantic Intent Router}
    
    B -- "Low Complexity / High Speed" --> C[Groq / Llama 3]
    B -- "Deep Reasoning / Code" --> D[Claude 3.5 Sonnet]
    B -- "Large Context Window" --> E[Gemini 2.5 Pro]
    B -- "Data Privacy Required" --> F[Local Ollama Models]
    
    C --> G[core/mcp_client.py]
    D --> G
    E --> G
    F --> G
    
    G --> H([Tool Aggregation & Completion])

    style B fill:#3a0ca3,stroke:#fff,stroke-width:2px,color:#fff
    style H fill:#00a67d,stroke:#000,stroke-width:2px,color:#fff
```

By leveraging local embeddings to classify the task before execution, the Cortex Router drastically reduces token costs while maintaining sub-second latency where it matters most.
