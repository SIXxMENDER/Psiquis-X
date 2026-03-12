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

import os
import logging
import requests
import json
import time
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
from dotenv import load_dotenv
from core.S_SERIES.manager_llaves import hydra_manager

# --- LAZY IMPORTS (Drivers) ---
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    print("[CORTEX] 'vertexai' module imported successfully.")
except Exception as e: 
    vertexai = None
    print(f"[CORTEX] Failed to import 'vertexai': {e}")

try:
    from groq import Groq
except Exception: Groq = None

try:
    import openai
    from openai import OpenAI
except Exception: OpenAI = None

try:
    import anthropic
    from anthropic import Anthropic
except Exception: Anthropic = None

try:
    import google.generativeai as genai
except Exception: genai = None

load_dotenv()

class Cortex:
    """
    Cortex v3 (Final): Universal X-Intelligence Router.
    Supports: Ollama, Vertex, Groq, OpenAI (GPT), Anthropic (Claude).
    Philosophy: "Plug & Play". If Key exists, Intelligence exists.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Cortex, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger("Cortex")
        self.default_provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        self.active_providers = {} 
        
        # --- OBSERVABILITY (Phase 5: LangSmith) ---
        self.tracing_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        if self.tracing_enabled:
            print("[CORTEX] Observability Enabled (LangSmith/Tracing v2)")
        
        # --- LOAD ALL DRIVERS ---
        # self._init_ollama()
        self._init_vertex()
        self._init_groq()
        self._init_openai()    # NEW: GPT Support
        self._init_anthropic() # NEW: Claude Support
        self._init_gemini()    # NEW: Google AI Studio (Free Tier)
        
        active_list = list(self.active_providers.keys())
        print(f"[CORTEX] Brains Active: {active_list}. Default: {self.default_provider}")
        self.logger.info(f"Cortex Ready. Active Brains: {active_list}. Default: {self.default_provider}")

    # --- INICIALIZADORES (Los Enchufes) ---

    def _init_ollama(self):
        url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            requests.get(url, timeout=0.5)
            self.active_providers["ollama"] = {"url": url, "model": os.environ.get("OLLAMA_MODEL", "mistral")}
        except: pass

    def _init_vertex(self):
        # Vertex AI is now the PRIMARY BRAIN
        # Auto-detected from user screenshot: psiquis-x
        project_id = os.environ.get("GCP_PROJECT_ID", "your-gcp-project")
        
        if not vertexai: 
            print("[CORTEX] Vertex AI skipped because module is not loaded.")
            return

        try:
            print(f"[CORTEX] Initializing Vertex AI with Project: {project_id}...")
            # Forzamos api_transport="rest" para evadir el deadlock de gRPC en Windows asyncio
            vertexai.init(
                project=project_id, 
                location=os.environ.get("GCP_REGION", "us-central1"),
                api_transport="rest"
            )
            self.active_providers["vertexai"] = {"model_name": "gemini-2.5-pro"}
            print(f"[CORTEX] Vertex AI (Gemini 2.5 Pro) Ready & Active. Project: {project_id} [REST Transport]")
        except Exception as e:
            print(f"[CORTEX] Vertex AI Init Failed: {e}")
            import traceback
            traceback.print_exc()

    def _init_anthropic(self):
        if not Anthropic: return
        # Solo activar si hay llaves en Hydra
        if any(k["provider"] == "anthropic" for k in hydra_manager.pool):
            self.active_providers["anthropic"] = {"model": "claude-3-5-sonnet-20240620"}
            print("[CORTEX] Anthropic (Hydra-Enabled) Ready.")

    def _init_gemini(self):
        if not genai: return
        # Solo activar si hay llaves en Hydra
        if any(k["provider"] == "gemini" for k in hydra_manager.pool):
            self.active_providers["gemini"] = {"model": "gemini-2.0-flash", "include_thoughts": True}
            print("[CORTEX] Gemini 2.0 Flash (Hydra-Enabled) Ready.")

    def _init_groq(self):
        if not Groq: return
        # Solo activar si hay llaves en Hydra
        if any(k["provider"] == "groq" for k in hydra_manager.pool):
            self.active_providers["groq"] = {"model": "llama-3.3-70b-versatile"}
            print("[CORTEX] Groq (Hydra-Enabled) Ready.")

    def _init_sambanova(self):
        if not OpenAI: return
        self.active_providers["sambanova"] = {"model": "Llama-3.3-70B"}
        print("[CORTEX] SambaNova (Hydra-Enabled) Ready.")

    def _init_openai(self):
        if not OpenAI: return
        # Solo activar si hay llaves en Hydra
        if any(k["provider"] == "openai" for k in hydra_manager.pool):
            self.active_providers["openai"] = {"model": "gpt-4o"}
            print("[CORTEX] OpenAI (Hydra-Enabled) Ready.")

    def _init_openrouter(self):
        if not OpenAI: return
        self.active_providers["openrouter"] = {"model": "google/gemini-2.0-flash-exp:free"}
        print("[CORTEX] OpenRouter (Hydra-Enabled) Ready.")

    # --- ROUTING INTELIGENTE ---

    def _resolve_provider(self, requested: str):
        # FORCE VERTEX AI (User Request: "Only leave vertex")
        if "vertexai" in self.active_providers:
            return "vertexai"
            
        # If Vertex is dead, we are dead.
        raise RuntimeError("[ERROR] DEAD ZONE: Vertex AI is not available.")

    # --- API PUBLICA (CON RESILIENCIA v3.3) ---
    async def ask_vision(self, prompt: str, image_path: str, model: str = "gemini-2.5-pro") -> str:
        """
        Multimodal cognition: Analyzes an image + prompt.
        Optimized for VertexAI Gemini 2.0 Flash.
        """
        if not os.path.exists(image_path):
            return f"Error: Image not found at {image_path}"

        print(f"[CORTEX] Analyzing image: {image_path}...")
        
        # Implementation for VertexAI (Gemini)
        if "vertexai" in self.active_providers:
            try:
                from vertexai.generative_models import Part, GenerativeModel
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                # Use 2.0 Flash for Vision too
                model_instance = GenerativeModel("gemini-2.5-pro")
                image_part = Part.from_data(data=image_data, mime_type="image/png")
                
                response = model_instance.generate_content([prompt, image_part])
                return response.text
            except Exception as e:
                print(f"[CORTEX] VertexAI Vision Error: {e}")

    # ... (rest of vision methods) ...

    def _ask_vertex(self, user, system, model):
        """Driver para Vertex AI (Google Cloud) via direct REST to bypass SDK/Windows deadlocks."""
        project_id = os.environ.get("GCP_PROJECT_ID", "your-gcp-project")
        location = os.environ.get("GCP_REGION", "us-central1")
        model_id = model or "gemini-2.5-pro"
        
        import google.auth
        import google.auth.transport.requests
        try:
            credentials, _ = google.auth.default()
            req = google.auth.transport.requests.Request()
            credentials.refresh(req)
        except Exception as e:
            raise RuntimeError(f"Error fetching Google Auth Credentials: {e}")

        url = f"https://{{location}}-aiplatform.googleapis.com/v1/projects/{{project_id}}/locations/{{location}}/publishers/google/models/{{model_id}}:generateContent"
        
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {"temperature": 0.2}
        }
        
        print(f"[CORTEX] Sending pure REST payload ({len(user)} chars) to Vertex {model_id}...")
        
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=180)
        except requests.exceptions.Timeout:
            raise RuntimeError(f"VertexAI LLM failed due to Timeout (180s) on a {len(user)} character payload.")
        except Exception as e:
            raise RuntimeError(f"Fatal Vertex REST Error: {e}")
            
        if resp.status_code != 200:
            raise RuntimeError(f"Vertex API Error {resp.status_code}: {resp.text}")
            
        json_res = resp.json()
        try:
            return json_res["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Vertex API format: {str(json_res)[:200]}")

        # Fallback to OpenAI Vision if active
        if "openai" in self.active_providers:
            try:
                import base64
                with open(image_path, "rb") as f:
                    b64_image = base64.b64encode(f.read()).decode('utf-8')
                
                cfg = self.active_providers["openai"]
                res = cfg["client"].chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=300
                )
                return res.choices[0].message.content
            except Exception as e:
                print(f"[CORTEX] OpenAI Vision Error: {e}")

        return "Error: No vision-capable provider active (VertexAI/OpenAI required)."

    # --- MEMORY / RAG INTERFACE ---

    def retrieve_context(self, query: str, collection: str = "core_context", n_results: int = 2) -> str:
        """Retrieves semantic context from memory (RAG) with JSON Fallback."""
        snippets = []
        
        # 1. Try Vector DB (Chroma)
        try:
            from agentes.P_SERIES.agente_db_vectorial import buscar_recuerdos_similares
            recuerdos = buscar_recuerdos_similares(query, n_results=n_results)
            
            if recuerdos:
                for res in recuerdos:
                    title = res.get("metadata", {}).get("tipo", "Fragment")
                    content = res.get("content", "")
                    snippets.append(f"--- [VECTOR: {title}] ---\n{content}\n")
                return "\n".join(snippets)
        except Exception as e:
            print(f"[CORTEX] Vector Retrieval Failed: {e}. Switching to Static Fallback.")

        # 2. Try Static JSON (Fallback)
        try:
            static_path = os.path.join("data", "memory", "static_context.json")
            if os.path.exists(static_path):
                import json
                with open(static_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Simple keyword match
                q_tokens = query.lower().split()
                matches_found = 0
                for title, content in data.items():
                    # Score based on title match or content content
                    score = 0
                    if any(t in title.lower() for t in q_tokens): score += 3
                    if any(t in content.lower()[:500] for t in q_tokens): score += 1
                    
                    if score > 0:
                        snippets.append(f"--- [STATIC: {title}] ---\n{content}\n")
                        matches_found += 1
                        if matches_found >= n_results: break
                return "\n".join(snippets)
        except Exception as e:
            print(f"[CORTEX] Static Retrieval Failed: {e}")

        return ""

    def ask(self, user_prompt: str, system_prompt: str = "You architecture is a Senior Assistant.", provider: str = None, model: str = None) -> str:
        """
        Request a response from the AI with automatic retry (Fallback).
        Supports TRACING for Level 3 Observability.
        NEW: Implements Semantic Cache (FinOps).
        """
        # 0. Aplicar Delay (Anti-429)
        delay = int(os.environ.get("LLM_DELAY_SECONDS", 2))
        if delay > 0:
            time.sleep(delay)

        # 1. Verificar Cache Semantico (DESHABILITADO TEMPORALMENTE POR SEGURIDAD)
        from core.S_SERIES.state_manager import StateManager
        sm = StateManager()
        # cached_res = sm.check_cache(f"{system_prompt}{user_prompt}")
        # if cached_res:
        #    print("[CORTEX] Semantic Cache Hit! Ahorrando tokens...")
        #    return cached_res

        # OBSERVAIBLITY V3: Emitir "Pensando..." al Dashboard
        try:
            from core.S_SERIES.mission_control import mission_manager
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                msg = f"Consultando a {provider or self.default_provider} (ID: {getattr(self, '_last_key_id', 'unknown')})..."
                loop.create_task(mission_manager.emit_event("thought", msg, agent="CORTEX", log_to_console=False))
        except: pass

        last_err = "Error desconocido"
        start_time = time.time()
        
        # Intentar con el proveedor solicitado (o el default)
        try:
            target = self._resolve_provider(provider)
            res = self._execute_ask(target, user_prompt, system_prompt, model)
            
            # 2. Guardar en Cache (DESHABILITADO)
            # sm.save_to_cache(f"{system_prompt}{user_prompt}", res)

            # Phase 5: Trace successful execution
            if self.tracing_enabled:
                self._record_trace(target, user_prompt, res, time.time() - start_time)
            
            # Estimate token usage (~4 chars per token average)
            try:
                tokens_used = (len(user_prompt) + len(system_prompt) + len(res)) // 4
                if tokens_used > 0:
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        from core.S_SERIES.mission_control import mission_manager
                        loop.create_task(mission_manager.emit_event("consume_tokens", tokens_used, agent="CORTEX", log_to_console=False))
                    except (RuntimeError, ValueError):
                        # No running loop or thread mismatch. Sync fallback to persistence only.
                        from core.S_SERIES.state_manager import StateManager
                        sm = StateManager()
                        current = sm.get_metadata("tokens_used")
                        current_val = int(current) if current is not None else 0
                        sm.save_metadata("tokens_used", current_val + tokens_used)
            except Exception:
                pass

            return res
        except Exception as e:
            last_err = str(e)
            print(f"[WARN] [CORTEX] Primary failure ({provider or 'default'}): {last_err}. Activating Resilience Protocol...")

            # PROTOCOLO DE RESILIENCIA: Probar todos los proveedores activos
            preference_order = ["gemini", "groq", "openai", "vertexai", "anthropic", "ollama"]
            for fallback_p in preference_order:
                if fallback_p not in self.active_providers:
                    continue
                
                # Evitar repetir si es el mismo que falló
                if fallback_p == provider and model is None: 
                    continue
                    
                try:
                    print(f"[CORTEX] [RESILIENCE] Probando fallback con {fallback_p}...")
                    fallback_res = self._execute_ask(fallback_p, user_prompt, system_prompt, model=None)
                    print(f"[CORTEX] [RESILIENCE] Fallback {fallback_p} EXITOSO.")
                    
                    # Guardar en Cache el resultado del fallback
                    # sm.save_to_cache(f"{system_prompt}{user_prompt}", fallback_res)

                    # Estimate token usage for fallback (~4 chars per token)
                    try:
                        tokens_used = (len(user_prompt) + len(system_prompt) + len(fallback_res)) // 4
                        if tokens_used > 0:
                            import asyncio
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                from core.S_SERIES.mission_control import mission_manager
                                loop.create_task(mission_manager.emit_event("consume_tokens", tokens_used, agent="CORTEX", log_to_console=False))
                    except Exception as token_err:
                        pass
                    
                    return fallback_res
                except Exception as fe:
                    last_err = f"[{fallback_p}] {str(fe)}"
                    print(f"[CORTEX] Fallback {fallback_p} failed: {last_err}")
            
            err_final = f"CRITICAL ERROR: All brains failed. Last error: {last_err}"
            print(f"[ERROR] [CORTEX] {err_final}")
            return err_final

    async def ask_async(self, user_prompt: str, system_prompt: str = "Eres un Asistente Senior.", provider: str = None, model: str = None) -> str:
        """Version asincrona de ask()."""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.ask(user_prompt, system_prompt, provider, model)
        )

    def ask_json(self, user_prompt: str, system_prompt: str = "Eres un Asistente Senior.", schema: Type[BaseModel] = None, provider: str = None, model: str = None) -> Dict[str, Any]:
        """Solicita respuesta y extrae JSON validado."""
        raw_res = self.ask(user_prompt, system_prompt, provider, model)
        schema_json = schema.model_json_schema() if schema else None
        return self.extract_json(raw_res, schema_json, provider)

    async def ask_json_async(self, user_prompt: str, system_prompt: str = "Eres un Asistente Senior.", schema: Type[BaseModel] = None, provider: str = None, model: str = None) -> Dict[str, Any]:
        """Version asincrona de ask_json()."""
        import asyncio
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.ask_json(user_prompt, system_prompt, schema, provider, model)
        )

    def _execute_ask(self, target: str, user: str, system: str, model: str = None) -> str:
        """Helper interno para dirigir la llamada al driver correcto con Hydra."""
        # 1. Resolve Hydra Key
        key_data = hydra_manager.get_optimal_key(provider_filter=target)
        if not key_data:
            raise RuntimeError(f"[HYDRA] All keys for {target} are exhausted. Waiting for cooldown...")

        key_id = key_data["id"]
        self._last_key_id = key_id # Store for logging
        api_key = key_data["key"]

        print(f"[CORTEX] Invocando {target} con identidad: {key_id}")

        try:
            if target == "ollama": res = self._ask_ollama(user, system, model)
            elif target == "vertexai": res = self._ask_vertex(user, system, model)
            elif target == "groq": res = self._ask_groq(user, system, model, api_key)
            elif target == "openai": res = self._ask_openai(user, system, model)
            elif target == "anthropic": res = self._ask_anthropic(user, system, model)
            elif target == "gemini": res = self._ask_gemini(user, system, model, api_key)
            elif target == "sambanova": res = self._ask_sambanova(user, system, model, api_key)
            elif target == "openrouter": res = self._ask_openrouter(user, system, model, api_key)
            else: raise ValueError(f"Unknown provider: {target}")

            # 2. Register success in semaphore
            hydra_manager.register_call(key_id)
            return res
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                print(f"[HYDRA] Key {key_id} saturated (429). Marking cooldown.")
                hydra_manager.mark_error(key_id)
            elif any(code in err_str for code in ["401", "400", "403"]):
                print(f"[HYDRA] Key {key_id} invalid or expired ({err_str}). Blacklisting.")
                hydra_manager.blacklist_key(key_id)
            raise e

    # --- DRIVERS DE EJECUCION ---

    def _ask_ollama(self, user, system, model):
        cfg = self.active_providers["ollama"]
        r = requests.post(f"{cfg['url']}/api/chat", json={
            "model": model or cfg["model"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False
        })
        return r.json()["message"]["content"]

    def _ask_gemini(self, user, system, model, api_key):
        """Driver para Google AI Studio (Gemini 2.0)."""
        genai.configure(api_key=api_key)
        cfg_model = self.active_providers.get("gemini", {}).get("model", "gemini-2.0-flash")
        
        model_instance = genai.GenerativeModel(
            model_name=model or cfg_model,
            system_instruction=system
        )
        return model_instance.generate_content(user).text

    def _ask_groq(self, user, system, model, api_key):
        client = Groq(api_key=api_key)
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=model or self.active_providers["groq"]["model"]
        ).choices[0].message.content

    def _ask_openai(self, user, system, model, api_key=None):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key: raise ValueError("No OpenAI API Key found.")
        client = OpenAI(api_key=key)
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=model or self.active_providers["openai"]["model"]
        ).choices[0].message.content

    def _ask_anthropic(self, user, system, model, api_key=None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key: raise ValueError("No Anthropic API Key found.")
        client = Anthropic(api_key=key)
        return client.messages.create(
            model=model or self.active_providers["anthropic"]["model"],
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}]
        ).content[0].text

    def _ask_sambanova(self, user, system, model, api_key):
        client = OpenAI(api_key=api_key, base_url="https://api.sambanova.ai/v1")
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=model or self.active_providers["sambanova"]["model"]
        ).choices[0].message.content

    def _ask_openrouter(self, user, system, model, api_key):
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        return client.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            model=model or self.active_providers["openrouter"]["model"]
        ).choices[0].message.content
    
    # (JSON Extraction methods)
    def extract_json(self, text, schema, provider=None):
        """
        Extrae JSON con resiliencia de alto nivel (Nivel 4+).
        1. Intenta parseo directo.
        2. Intenta encontrar bloques de codigo JSON.
        3. Intenta limpieza agresiva via Regex.
        """
        if not text: return {}
        
        # Etapa 1: Limpieza basica
        try:
            # Eliminar markdown
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except: pass

        # Etapa 2: Regex para encontrar el objeto JSON mas grande (Resiliencia ASI06)
        import re
        try:
            # Busca algo que empiece con { y termine con }
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except: pass

        # Etapa 3: Invocar re-validacion si el schema se proporciono
        if schema:
            self.logger.warning("[WARN] [CORTEX] Extraccion fallida. Re-validando con schema...")
            # Aqui podriamos orquestar un segundo ask() de limpieza, 
            # pero para evitar bucles infinitos, devolvemos {} y dejamos que el orquestador maneje el reintento.
        
        self.logger.error(f"[ERROR] Imposible extraer JSON valido del texto: {text[:100]}...")
        return {}
    
    def _parse_json(self, text):
        # Mantenemos para compatibilidad pero redirigimos a extract_json
        return self.extract_json(text, None)

cortex = Cortex()
