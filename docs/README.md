# PSIQUIS-X SOVEREIGN ENGINE (V3)

> **Status:** PROTOTYPE (Under Remediation)
> **Engine:** "Sovereign" V3 (Hybrid FastAPI + LangGraph)

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for Dashboard)
- Playwright (`playwright install`)

### 2. Installation
```bash
# Clone and Install Dependencies
pip install -r requirements.txt
playwright install chromium
```

### 3. Environment Setup
Copy the example environment file and fill in your API keys:
```bash
cp .env.example .env
```

### 4. Running the Engine
Do NOT run `main.py` directly. Use the Sovereign Server V2:
```bash
python server_v2.py
```
*Server will start at `http://localhost:8001`*

### 5. Running the Dashboard
```bash
cd frontend
npm run dev
```
*Frontend will start at `http://localhost:3000`*

---

## 🏗️ Architecture (Sovereign V3)

### Core Components
- **Orchestrator (`server_v2.py`):** The central nervous system. Handles WebSocket/SSE streams and API endpoints. Uses a "Shark Patch" to intercept `stdout`.
- **Cortex (`core/cortex.py`):** Universal LLM Router (Polyglot). Supports Gemini, Groq, OpenAI, Anthropic.
- **Talker (`agentes/talker.py`):** System 1 Agent. Fast, empathetic, non-blocking.
- **Hydra (`core/manager_llaves.py`):** Key Rotation Manager. Enforces rate limits (8 RPM).
- **State Manager (`core/state_manager.py`):** SQLite persistence layer for Chat History and Mission State.

### Directory Structure
- `/agentes`: Specialized Workers (P8, Enjambre, Talker).
- `/core`: Kernel logic (Cortex, Config, Logger, Topology).
- `/data`: Persistent storage (Vault) for artifacts.
- `/frontend`: Next.js Visual Interface.

---

## ⚠️ Known Issues (Under Remediation)
- **Memory:** `chat_history` is capped at 100 turns. Old messages are pruned.
- **Concurrency:** Uses `run_in_executor` for LLM calls to prevent blocking the Event Loop.
- **Security:** Run via Docker is recommended for sandboxing.

---
*Maintained by the Antigravity Team.*
