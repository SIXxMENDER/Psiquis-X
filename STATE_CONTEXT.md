# Psiquis_X - Deep Scan Context (Internal Knowledge Base)
*Este archivo compila un mapeo exhaustivo del código fuente real en `C:\py.freelance\BLAXTER\Psiquis_X`, analizado carpeta por carpeta.*

---

## 📂 Directorio 1: `agentes/`
Contiene la lógica base de las entidades autónomas y los escudos de seguridad.

### 📄 `agente_secrets_manager.py`
- **Propósito:** Gestor de secretos zero-trust local basado en `.env` (Paso 1 antes de migrar a Google Secret Manager).
- **Mecánica:** Intercepta requests para leer/escribir `SERVICE_API_KEY` y `SERVICE_API_SECRET`.
- **Implementación:** I/O directo sobre el archivo `.env` garantizando que las llaves nunca pasen por la memoria a largo plazo (ChromaDB) de la orquestación.

### 📄 `genesis_sandbox.py` (v3.7)
- **Propósito:** Entorno de validación local y aislamiento para código generado por LLMs (P-Series).
- **Mecánica:** Utiliza `subprocess.run` llamando al mismo `sys.executable` para inyectar y probar el script temporal generado.
- **Safety:** Impone un `timeout=10` estricto para prevenir Infinite Loops (Ataques lógicos accidentales).
- **Self-Healing:** Implementa la función `validar_con_reintentos()`, que atrapa cualquier error del compilador (`result.stderr`) y fuerza un callback asíncrono para que el agente reescriba el código basándose en el error (hasta 3 intentos).

### 📁 `P_SERIES/`
- *(Directorio detectado como sub-módulo de agentes orientados a Ingesta y Desarrollo/Ejecución, orquestados desde el nodo central)*.

---
## 📂 Directorio 6: `skills/`
Herramientas funcionales listas para ser consumidas por los agentes P-Series bajo demanda (el "cuerpo" de la IA).

### 📄 `excel_reporter.py`
- **Propósito:** Generador programático de Excel nativos a nivel Enterprise (OpenPyXL).
- **Mecánica:** Toma el JSON validado del CFO y genera dinámicamente gráficos de barras (Revenue vs Opex), matrices de análisis de cohortes con semaforización condicional (`coherence_flag`) y una hoja estricta de "Raw Data Traceability" que incrusta hyperlinks directos y los *literal snippets* extraídos.

### 📄 `pdf_intelligence.py`
- **Propósito:** Ingesta de PDFs con tracking nativo.
- **Mecánica:** Descarga local o web del PDF y fuerza (mediante `pypdf`) la anexión de una huella digital en cada fragmento procesado: `[SOURCE_FILE: nombre] [PAGE: N]`. Esta es la base de la Trazabilidad Total (Data Lineage) mencionada en el contexto del repo.

---
## 📄 Core API: `server_v3_minimal.py`
El punto de entrada unificado y real del ecosistema.
- **Propósito:** Expone el motor LangGraph hacia el mundo exterior vía una API RESTful (`FastAPI`) montada en `uvicorn` (Puerto 8001).
- **Funcionalidades Clave:**
  - `launch_mission`: Recibe el JSON y lanza el grafo asincrónicamente usando un `_safe_run`.
  - `stream_mission`: Habilita el Server-Sent Events (SSE) usando un generador asíncrono que transmite la telemetría en vivo a tu front-end.
  - Endpoints del **Data Vault** (`upload_file`, `list_vault`, `read_file`): Permiten al usuario/dashboard inyectar reportes manualmente en `data/input`.
  - Subsistemas de telemetría (`get_stats`) para consumir y auditar el historial de uso en la UI Next.js.
  
***
*✓ Escaneo Exclusivo (Omitiendo `EXTERNO/`) Completado. El Contexto Interno está sellado.*

## 📂 Directorio 4: `scripts/`
Un cajón de utilidades, demostraciones aisladas y herramientas de auditoría profunda. Aquí nace la data de los Benchmarks que mostramos en la Vitrina.

### 📄 `QUANTUM_ARBITRAGE_V1.py`
- **Propósito:** Demostrador de latencia ultra-baja (HFT) en entornos Crypto.
- **Mecánica:** Utiliza `ccxt.async_support` para conectarse a nodos públicos de Binance y Kraken simultáneamente.
- **Lógica:** Implementa una táctica de escaneo continuo de Order Books, detectando Spread cruzado en milisegundos y arrojando "Anomalías Cuánticas" (Arbitrajes rentables) con cálculos precisos de fees (`FEE_RATE = 0.001`). 

### 📄 `benchmark_rag_vertex.py`
- **Propósito:** Ejecutor del Benchmark empírico de Arquitectura "Sala de Tribunal".
- **Mecánica:** Interroga PDFs locales (`Nvidia_Presentation_Q4_FY26.pdf`) extrayendo texto vía scraping.
- **Batalla de Modelos:** Instancia nativamente `VertexGeminiCortex` (Gemini 2.5 Pro) vs `GroqCortex` (Llama-3.3-70b-versatile). Los invoca asincrónicamente usando `build_courtroom_graph()` (LangGraph) para medir no sólo el output, sino la velocidad total de la tubería defensiva (Juez + Escéptico).

### 📄 Resto de Herramientas
- **Robusteza:** Contiene `validate_robustness.py`, `key_validator.py` y `audit_lister.py` para asegurar que el entorno local esté libre de fallas de entorno o llaves muertas antes de encender el servidor principal.
---

## 📂 Directorio 5: `data/`
El sistema de persistencia de estado físico (Long-Term Memory y Local Vault).

### 📄 `SELF_DEFINITION.md`
- **Propósito:** Declaración de "conciencia" y propósito auto-generada del motor.
- **Contenido:** Describe a sí mismo como "Psiquis-X Engine V3", un sistema de IA plug & play con la misión implícita de aprender y mejorar a través de la interacción vía su API RESTful.

### 📄 `hydra_state.json`
- **Propósito:** Registro del balanceador de cargas API (Cortex Router).
- **Mecánica:** Mantiene un track en formato Unix timestamp de llamadas límite (`calls`) y tiempos de bloqueo anti-RateLimit (`cooldown_until`) cruzando llaves de `vertex_system_adc`, `groq_orquestador` y `groq_bruno_p6`. Esencial para rotación de keys y supervivencia en ejecuciones extremas.

### 💽 Persistencia Activa (`psiquis_state.db` & `chroma_db/`)
- Mantiene la base de datos SQL (`psiquis_state.db`) para el `StateManager` de langgraph.
- Aloja el directorio vectorial `chroma_db/` mapeado a la colección `psiquis_core`.

### 📁 Vault Local (Ecosistema de Archivos)
- Divide el I/O físico de los P-Series en entornos silenciados: `input/`, `output/`, `reports/`, `finance/`, `market_data.csv` y archivos `.pdf` base (como los de NVIDIA que sirven para benchmarks).
---

## 📂 Directorio 3: `core/`
El sistema nervioso central de PSIQUIS-X. Coordina la validación cruzada y la interfaz con el mundo real.

### 📄 `mcp_client.py` (v5.0 - Phase 5.2)
- **Propósito:** Interfaz Universal MCP (Model Context Protocol).
- **Mecánica:** Estandariza cómo Psiquis-X se conecta a servidores de herramientas externas. Actúa como la "Mano Universal" del Gestor Estratégico, abstrayendo la ejecución de herramientas como `google_search`.

### 📄 `drift_search.py`
- **Propósito:** DRIFT Search (Dynamic Reasoning and Inference with Flexible Traversal).
- **Mecánica:** Implementación híbrida de Vector + Graph RAG para razonamiento multi-salto.
- **Lógica:** Primero identifica "Comunidades" de conocimiento (Macro-contexto), luego realiza una recuperación vectorial (Micro-datos), y usa el `cortex.ask` para sintetizar la conexión entre ambas dimensiones.

### 📄 `data_interface.py`
- **Propósito:** Módulo de Ingesta Web dinámico.
- **Mecánica:** Script automatizado usando Selenium WebDriver (`webdriver.Chrome` con opciones `--headless` y anti-bot detection evasion).
- **Fallbacks:** Incluye un diseño resiliente con `fallback_data` (datos cacheados) que se activa automáticamente si el scraper lanza excepciones (por bloqueos anti-bot o cambios irreversibles del DOM).

### 📁 `orchestration/`
- *(Directorio detectado como el motor de grafos donde ocurren los lazos metacognitivos de LangGraph).*
---

## 📂 Directorio 2: `config/`
Contiene la configuración del entorno, orquestación de bases de datos y manifiestos de los ecosistemas (agentes y scrapers).

### 📄 `agents.yaml`
- **Propósito:** Registro central de agentes habilitados para el router.
- **Contenido clave:** Mapea nombres virtuales de agentes ("P0_Research", "P3_Coder", "P5_Genesis") a sus respectivos módulos en Python (`agentes.agente_p0`, etc.). Adicionalmente, incluye agentes autogenerados dinámicamente (`AutoAgent_agent_3143`).

### 📄 `blueprints.json` & `strategies.json`
- **Propósito:** Plantillas de comportamiento para agentes de extracción web.
- **Mecánica (`blueprints.json`):** Define una arquitectura híbrida *Scrapy-Playwright* como un "Resilient State Machine", con protocolos de self-healing para selectores HTML rotos. 

### 📄 `settings.py`
- **Propósito:** Variables de entorno y rutas base del ecosistema P-Series / Router.
- **Integraciones:** Apunta la persistencia vectorial a `data/chroma_db` (Colección: `psiquis_core`) y configura el Cortex Router con `GCP_PROJECT_ID` y `GCP_REGION = global` (Vertex AI).

### 📄 Entornos `.env`
- Se observan múltiples plantillas, desde `.env.example` hasta `.env.production.example`, denotando un marco listo para despliegue aislado.
---
