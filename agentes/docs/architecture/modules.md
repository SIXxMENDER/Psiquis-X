# Core Modules & Implementation Architecture

The operational capabilities of **Psiquis-X** are driven by a highly decoupled, modular codebase designed for strict enterprise environments. While the source code remains proprietary and isolated from public access, the following breakdown illustrates our engineering approach and module designation inside the live production system.

## 1. The Asynchronous Core API (`server_v3`)
At the root of the execution environment sits a lightweight, high-performance orchestration server built defensively around **FastAPI**.
- **Role:** Handles ingestion hooks, triggers background agent missions, and maintains state.
- **SSE Streaming:** Employs Server-Sent Events (SSE) to broadcast real-time telemetry, agent "thoughts," and latency metrics directly to our React/Next.js 19 frontend observables.
- **Fault-Isolation:** Operations are dispatched into isolated event loops (`_safe_run` and `sandbox` wrappers) to ensure that a catastrophic failure in an agent reasoning step never halts the main API thread.

## 2. Cognitive Orchestration (`core/orchestration`)
The `core/` directory acts as the central nervous system, built on top of **LangGraph**. It defines the deterministic state-machines that dictate how and when agents interact.
- **StateManager:** A robust class preserving the Long-Term Memory (LTM) context.
- **MCP Client (`mcp_client.py`):** Natively integrates the Model Context Protocol to fetch external data (financial feeds, repository contexts, web scrapers) securely injected into the LLM context.
- **Drift Validation (`drift_search.py`):** Algorithms dedicated to detecting logical drift during long-context generation phases.

## 3. The Dual-Agent Architecture (`agentes/`)
Agent logic is rigorously separated by risk profile and computation weight into two series:

### 3.1 P-Series (Processing & Heavy Lifting)
Located within the `P_SERIES` cluster, these agents are the heavy lifters deployed for complex data ingestion and strategy formulation.
- **Execution Sandbox (`genesis_sandbox.py`):** P-Series agents execute code and complex reasoning inside a strictly controlled sandbox, isolating untrusted output or dynamic code execution from the host environment.
- **Secrets Management (`agente_secrets_manager.py`):** Implements zero-trust handling of API keys inside agent sub-routines.

### 3.2 S-Series (Supervision & Skepticism)
Located within the `S_SERIES` cluster, these are lightweight, fast, and aggressively adversarial agents representing the "Courtroom Architecture."
- **Adversarial Audit:** They do not generate net-new logic; instead, they inspect the P-Series outputs using strict deterministic rules.
- **Hunter Protocol (`hunter_apify.py`):** Specific fast-execution routines designed to pinpoint data lineage discrepancies (e.g., verifying if a Gross Margin calculation exactly matches the extracted PDF slice).

## 4. Secure Vault & File Management (`data/` & `Vault API`)
Psiquis-X avoids treating documents as ephemeral inputs. Data ingestion relies on a dedicated Vault mechanism:
- **Dynamic Slicing:** Documents are managed locally; PDFs (such as complex 10-K/10-Q NVIDIA presentations) are ingested and sliced into overlapping 15,000-token blocks.
- **Metadata-Injection:** Every slice retains an encrypted or traceable metadata tag (Data Lineage) mapping back to the exact file and page, ensuring output calculations (like YoY financial metrics in the Excel dashboard) are perfectly traceable to the source document.
