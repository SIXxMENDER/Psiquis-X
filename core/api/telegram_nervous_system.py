import os
import logging
import asyncio
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, Application
from telegram.error import ChatMigrated
from collections import deque
import sys

# Add project root to path for imports
sys.path.append(os.getcwd())
from core.utils.llm_utils import invocar_llm
# from agentes.agente_p5_genesis import ejecutar_genesis_con_reintento # Moved to local import to avoid circular dependency

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global Bot instance for non-async access from P6a
_bot_instance: Optional[Bot] = None
_chat_id: Optional[int] = None

# Chat History Memory (RAM only)
# Format: {"chat_id:thread_id": deque([msg1, msg2, ...], maxlen=500)}
_chat_histories: Dict[str, deque] = {}

def _get_thread_key(chat_id: int, thread_id: Optional[int]) -> str:
    """Generates a composite key for chat history isolation."""
    t_id = thread_id if thread_id else 0
    return f"{chat_id}:{t_id}"

def _get_bot() -> Bot:
    """Returns singleton bot instance for emergency notifications."""
    global _bot_instance
    if _bot_instance is None:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        _bot_instance = Bot(token=token)
    return _bot_instance

def set_chat_id(chat_id: int):
    """Sets the target chat ID for emergency notifications and persists to file."""
    global _chat_id
    _chat_id = chat_id
    
    # Persist to file for other processes
    try:
        with open(".sixmender_chat_id", "w") as f:
            f.write(str(chat_id))
        logging.info(f"Sixmender: Chat ID set to {chat_id} and saved to file")
    except Exception as e:
        logging.error(f"Sixmender: Failed to save chat_id to file: {e}")

def _load_chat_id_from_file() -> int:
    """Loads chat_id from file if it exists."""
    try:
        if os.path.exists(".sixmender_chat_id"):
            with open(".sixmender_chat_id", "r") as f:
                return int(f.read().strip())
    except Exception as e:
        logging.error(f"Sixmender: Failed to load chat_id from file: {e}")
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store user's chat ID for emergency notifications."""
    set_chat_id(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Sixmender online. Listening for commands.\n\nChat ID registered for emergency alerts."
    )

# ============================================================================
# USER EXPERIENCE MODULE
# ============================================================================

class UserManager:
    """Manages user state and preferences."""
    STATE_FILE = "user_state.json"
    
    @classmethod
    def _load_state(cls) -> Dict[str, Any]:
        if os.path.exists(cls.STATE_FILE):
            try:
                with open(cls.STATE_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @classmethod
    def _save_state(cls, state: Dict[str, Any]):
        with open(cls.STATE_FILE, "w") as f:
            json.dump(state, f)

    @classmethod
    def is_new_user(cls, user_id: int) -> bool:
        state = cls._load_state()
        return str(user_id) not in state

    @classmethod
    def mark_user_seen(cls, user_id: int):
        state = cls._load_state()
        state[str(user_id)] = {"seen_welcome": True, "first_seen": str(asyncio.get_event_loop().time())}
        cls._save_state(state)

async def _progress_simulator(context: ContextTypes.DEFAULT_TYPE, chat_id: int, thread_id: Optional[int], message_id: int, stop_event: asyncio.Event):
    """
    Updates a message with friendly progress status every few seconds.
    """
    statuses = [
        "🔨 Building your specialist... (~30 sec)",
        "🔧 Installing tools... 20%",
        "📚 Reading documentation... 40%",
        "🧠 Configuring neural network... 60%",
        "🧪 Testing solutions... 80%",
        "✨ Polishing final details... 90%",
        "📦 Packaging result..."
    ]
    
    idx = 0
    while not stop_event.is_set():
        try:
            await asyncio.sleep(10) # Update every 10 seconds
            if stop_event.is_set(): break
            
            idx = (idx + 1) % len(statuses)
            text = statuses[idx]
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"⏳ {text}"
            )
        except Exception as e:
            logging.warning(f"Progress simulator error: {e}")
            break

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows available commands and usage instructions.
    """
    help_text = (
        "🧠 **SIXMENDER // COMMANDS**\n\n"
        "**Conversational Mode:**\n"
        "Just talk to me. I'll respond as your strategic assistant.\n\n"
        "**Production Mode (Don 420):**\n"
        "`Don 420: [Instruction]` -> Creates an expert agent to solve your task.\n"
        "`Don 420 dev: [Instruction]` -> Same, but shows logs and code (Dev Mode).\n\n"
        "**Icebreaker Tools:**\n"
        "`/solve [problem]` -> Attempts to solve a logical problem.\n"
        "`/abort` -> Stops current execution.\n"
        "`/resume` -> Resumes a paused execution.\n\n"
        "**Dashboard:**\n"
        "Visit `http://localhost:5000` to see my brain in real-time."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

def classify_intent(message: str) -> str:
    """
    Uses LLM to classify user intent: CHAT, GENESIS, or AMBIGUOUS.
    """
    system_prompt = """
    You are the Sixmender Decision Router.
    Your job is to classify the user's intent into one of three categories:

    1. CHAT: Simple queries, questions, conversation, quick doubts. (e.g., "Hello", "What time is it?", "Explain this", "Summary").
    2. GENESIS: Requests that require creating software, tools, scripts, complex data analysis, or files. (e.g., "Create a script", "Analyze this CSV", "Make a bot", "Give me a detailed plan in PDF").
    3. AMBIGUOUS: It's not clear if they want to just talk or build something.

    Respond ONLY with one word: CHAT, GENESIS, or AMBIGUOUS.
    """
    
    response = invocar_llm(
        prompt_sistema=system_prompt,
        prompt_usuario=f"User message: '{message}'\n\nClassification:",
        temperatura=0.0,
        max_output_tokens=10
    ).strip().upper()
    
    # Fallback cleanup
    if "CHAT" in response: return "CHAT"
    if "GENESIS" in response: return "GENESIS"
    return "AMBIGUOUS"

async def don_420_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Protocolo de Producción ('Don 420').
    Supports Default Mode (Clean) and Dev Mode (Verbose).
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    thread_id = update.message.message_thread_id
    user_name = update.effective_user.first_name
    msg_text = update.message.text.lower().strip()
    
    # --- 1. WELCOME MESSAGE (One-time) ---
    if UserManager.is_new_user(user_id):
        welcome_msg = (
            f"Hello {user_name}! I am Sixmender.\n\n"
            "Every time you use **“Don 420”**, I create an expert program on your PC specifically for your request. "
            "You only see the final result here on Telegram.\n\n"
            "If you want to see the code and logs, write `Don 420 dev` at the beginning.\n"
            "Try it now with something simple!"
        )
        await context.bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=welcome_msg, parse_mode="Markdown")
        UserManager.mark_user_seen(user_id)
        # Don't return, continue processing the command

    # --- 2. DETECT MODE & INTENT ---
    dev_triggers = ["don 420 dev", "don 420 debug", "don 420 show code", "don 420 código"]
    is_dev_mode = any(msg_text.startswith(t) for t in dev_triggers)
    
    # Check for Explicit Overrides (User replying to ambiguity)
    intent = "AMBIGUOUS"
    if msg_text in ["chat", "1"]:
        intent = "CHAT"
    elif msg_text in ["genesis", "2"]:
        intent = "GENESIS"
    else:
        # AI Classification
        status_msg = await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=f"🤔 Analyzing request..."
        )
        intent = classify_intent(msg_text)
        await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

    # Use composite key for history
    history_key = _get_thread_key(chat_id, thread_id)
    
    # --- ROUTER LOGIC ---
    
    if intent == "AMBIGUOUS":
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=(
                "🤔 **I detect ambiguity in your request.** How would you like me to approach it?\n\n"
                "⚡ **Quick Mode (Chat):** I'll give you an immediate opinion based on what I know.\n"
                "🛠️ **Expert Mode (Genesis):** I'll create custom software for this (slower but more powerful).\n\n"
                "👉 Respond **CHAT** or **GENESIS**."
            ),
            parse_mode="Markdown"
        )
        return

    if intent == "CHAT":
        # Conversational Mode
        await context.bot.send_chat_action(chat_id=chat_id, message_thread_id=thread_id, action="typing")
        
        # Retrieve history for context
        history = _chat_histories.get(history_key, deque())
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        
        system_prompt = """
        You are Sixmender, a tactical and efficient assistant.
        The user has asked for something that does NOT require generating complex code.
        Respond directly, helpfully, and with personality.
        """
        
        response = invocar_llm(system_prompt, f"History:\n{history_text}\n\nUser: {msg_text}\n\nResponse:", temperatura=0.7)
        
        await context.bot.send_message(
            chat_id=chat_id,
            message_thread_id=thread_id,
            text=response
        )
        return

    # --- GENESIS MODE (Existing Logic) ---
    
    # Initial Response
    if is_dev_mode:
        status_msg = await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=f"👨‍💻 **MODO DEV ACTIVADO**\n\nRecopilando contexto y generando ticket..."
        )
    else:
        status_msg = await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=f"🤖 Entendido, armando tu especialista... (~30 seg)"
        )

    # 3. Retrieve history
    history = _chat_histories.get(history_key, deque())
    if not history:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=status_msg.message_id,
            text="⚠️ No hay historial reciente. Escribe la idea primero."
        )
        return

    # 4. Generate Ticket (Internal)
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    
    system_prompt = """
    Eres el Jefe de Operaciones. Genera un TICKET DE PRODUCCIÓN estructurado basado en el chat.
    El usuario ha dicho "Don 420" (Aprobado).
    """
    user_prompt = f"Historial:\n{history_text}\n\nGenera el ticket definitivo."
    
    ticket = invocar_llm(system_prompt, user_prompt, temperatura=0.4)
    
    # Show Ticket ONLY in Dev Mode
    if is_dev_mode:
        await context.bot.send_message(
            chat_id=chat_id, message_thread_id=thread_id,
            text=ticket, parse_mode="Markdown"
        )
        await context.bot.send_message(
            chat_id=chat_id, message_thread_id=thread_id,
            text="🚀 Iniciando Protocolo Génesis..."
        )

    # 5. EXECUTE GENESIS PROTOCOL
    stop_progress = asyncio.Event()
    progress_task = None
    
    if not is_dev_mode:
        # Start progress simulator
        progress_task = asyncio.create_task(
            _progress_simulator(context, chat_id, thread_id, status_msg.message_id, stop_progress)
        )
    
    try:
        # Run Genesis
        from agentes.agente_p5_genesis import ejecutar_genesis_con_reintento # Local import to avoid cycle
        genesis_result = await asyncio.to_thread(
            ejecutar_genesis_con_reintento, 
            objetivo=f"Implementar lo siguiente:\n{ticket}"
        )
        
        # Stop progress simulator
        stop_progress.set()
        if progress_task: await progress_task
        
        if genesis_result.get("status") == "SUCCESS":
            agent_path = genesis_result.get("agent_path", "Desconocido")
            execution_result = genesis_result.get("result", "Sin resultado explícito")
            
            if is_dev_mode:
                await context.bot.send_message(
                    chat_id=chat_id, message_thread_id=thread_id,
                    text=f"✅ **Agente Creado y Ejecutado**\n\n📍 Ruta: `{agent_path}`",
                    parse_mode="Markdown"
                )
            else:
                # Clean up status message
                await context.bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)

            # Smart Delivery (Always)
            await _send_smart_result(context, chat_id, thread_id, execution_result)

        else:
            error_msg = genesis_result.get("error", "Error desconocido")
            if is_dev_mode:
                await context.bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"❌ **Fallo en Génesis**\nError: {error_msg}")
            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=status_msg.message_id,
                    text=f"😕 Hubo un problema técnico creando el especialista.\n\nError: {error_msg}"
                )
            
    except Exception as e:
        stop_progress.set()
        logging.error(f"Error executing Genesis: {e}")
        await context.bot.send_message(chat_id=chat_id, message_thread_id=thread_id, text=f"💥 Error crítico: {str(e)}")

async def _send_smart_result(context: ContextTypes.DEFAULT_TYPE, chat_id: int, thread_id: Optional[int], result: Any):
    """
    Analyzes the result and sends it as Text or File depending on size/type.
    """
    # 1. Extract Content
    content = ""
    if isinstance(result, dict):
        # Try to find the most relevant field
        for key in ["report", "content", "strategy", "code", "data", "output"]:
            if key in result and result[key]:
                content = str(result[key])
                break
        if not content:
            content = str(result) # Fallback to full dict string
    else:
        content = str(result)
        
    # 2. Check Size
    MAX_TEXT_LENGTH = 3000
    
    if len(content) < MAX_TEXT_LENGTH:
        # Send as Text
        await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=f"📊 **Resultado:**\n\n{content}",
            parse_mode=None # Disable markdown to avoid breaking on raw text
        )
    else:
        # Send as File
        filename = f"Reporte_Genesis_{asyncio.get_event_loop().time()}.md"
        
        try:
            # Write to temp file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Send Document
            await context.bot.send_document(
                chat_id=chat_id,
                message_thread_id=thread_id,
                document=open(filename, "rb"),
                caption="📊 Aquí tienes el reporte completo."
            )
            
            # Cleanup
            os.remove(filename)
            
        except Exception as e:
            logging.error(f"Failed to send document: {e}")
            # Fallback to truncated text
            await context.bot.send_message(
                chat_id=chat_id, 
                message_thread_id=thread_id,
                text=f"⚠️ Error enviando archivo. Mostrando inicio del resultado:\n\n{content[:3000]}..."
            )

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja mensajes de texto.
    1. Guarda historial por TOPIC.
    2. Si mencionan '@sixmender', responde con LLM en el TOPIC correcto.
    3. Si dicen 'Don 420', activa protocolo.
    4. Si no, silencio (observador pasivo).
    """
    chat_id = update.effective_chat.id
    user = update.effective_user.first_name if update.effective_user else "Unknown"
    
    # Debug: Log everything
    logging.info(f"🔍 Update received: {update}")
    
    # --- AUDIO/VOICE HANDLING ---
    audio_obj = update.message.voice or update.message.audio
    if audio_obj:
        await context.bot.send_chat_action(chat_id=chat_id, message_thread_id=thread_id, action="upload_voice")
        
        # Download file
        file_id = audio_obj.file_id
        new_file = await context.bot.get_file(file_id)
        file_byte_array = await new_file.download_as_bytearray()
        
        # Prepare prompt
        system_prompt = """
        Eres Sixmender. El usuario te ha enviado un audio.
        Tu tarea es:
        1. Transcribir mentalmente el audio.
        2. Si es una pregunta o instrucción, RESPONDERLA directamente.
        3. Si es solo información, confirmar que la recibiste.
        
        Responde en texto plano. Sé conciso.
        """
        
        # Invoke LLM with audio
        response = invocar_llm(
            system_prompt=system_prompt,
            prompt_usuario="[AUDIO ATTACHED] Please process this audio.",
            audio_data=bytes(file_byte_array),
            mime_type="audio/ogg" if update.message.voice else "audio/mpeg" # Voice is usually ogg, Audio is mp3/m4a
        )
        
        # Reply
        await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=f"🎤 {response}"
        )
        
        # Add to history (Approximation)
        history_key = _get_thread_key(chat_id, thread_id)
        if history_key not in _chat_histories:
            _chat_histories[history_key] = deque(maxlen=500)
        
        _chat_histories[history_key].append({"role": f"User ({user})", "content": "[AUDIO MESSAGE]"})
        _chat_histories[history_key].append({"role": "Sixmender", "content": response})
        return

    if not update.message or not update.message.text:
        logging.info("⚠️ Update has no text message. Ignoring.")
        return

    msg = update.message.text
    thread_id = update.message.message_thread_id  # Extract Topic ID
    
    # 0. Check special trigger "Don 420" (Case insensitive) OR Explicit Router Reply
    if "don 420" in msg.lower() or msg.lower() in ["chat", "genesis", "1", "2"]:
        await don_420_handler(update, context)
        return

    # 1. Update History (ISOLATED BY TOPIC)
    history_key = _get_thread_key(chat_id, thread_id)
    
    if history_key not in _chat_histories:
        _chat_histories[history_key] = deque(maxlen=500)
    
    _chat_histories[history_key].append({"role": f"User ({user})", "content": msg})
    
    # Debug logging
    logging.info(f"📩 Message stored in [{history_key}]: '{msg}'")

    # 2. Check for Mention (@sixmender)
    # Relaxed logic: allow "@sixmender", "@ sixmender", or just "sixmender" if it's a DM
    target_triggers = ["@sixmender", "@ sixmender", "sixmender"]
    is_mentioned = any(t in msg.lower() for t in target_triggers) or (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)
    
    if is_mentioned:
        # Add bot's "thinking" placeholder
        await context.bot.send_chat_action(chat_id=chat_id, message_thread_id=thread_id, action="typing")
        
        # Prepare context for LLM (ISOLATED)
        history = _chat_histories.get(history_key)
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        
        system_prompt = """
        Eres Sixmender, el Sistema Nervioso de un Motor de IA avanzado.
        Tu personalidad es: Eficiente, Táctica, Ligeramente Cínica pero Leal.
        
        Responde a la pregunta del usuario utilizando el contexto de la conversación si es necesario.
        Sé conciso y directo.
        """
        
        response = invocar_llm(system_prompt, f"Contexto:\n{history_text}\n\nPregunta actual: {msg}")
        
        # Reply to the specific thread
        await context.bot.send_message(
            chat_id=chat_id, 
            message_thread_id=thread_id,
            text=response
        )
        
        # Add bot response to history
        _chat_histories[history_key].append({"role": "Sixmender", "content": response})

    # 3. Passive Mode (Do nothing if not mentioned)
    else:
        pass

async def apikey_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles /apikey command for storing API keys.
    Format: /apikey <service> <key> [secret]
    """
    try:
        args = context.args
        if len(args) < 2:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Uso: /apikey <servicio> <key> [secret]\n\nEjemplo: /apikey binance tu_api_key tu_api_secret"
            )
            return
        
        service = args[0].lower()
        api_key = args[1]
        api_secret = args[2] if len(args) > 2 else None
        
        # Import secrets manager
        import sys
        sys.path.append(os.getcwd())
        from agentes import agente_secrets_manager
        
        # Store the key
        success = agente_secrets_manager.guardar_api_key(service, api_key, api_secret)
        
        if success:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ API Key guardada para {service.upper()}"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error guardando API key para {service}"
            )
            
    except Exception as e:
        logging.error(f"Error in apikey_handler: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Error: {str(e)}"
        )


async def resume_job_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🧠 NEURO-CIRUGÍA: Webhook for resuming hibernated jobs.
    Format: /resume_job <job_id>
    
    This is called when a human responds to a WAITING_FOR_HUMAN notification.
    It "resurrects" the job by loading its state from Firestore and re-launching P6a.
    """
    try:
        args = context.args
        if len(args) < 1:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Uso: /resume_job <job_id>\n\nEjemplo: /resume_job plan_123"
            )
            return
        
        job_id = args[0]
        
        # Import state manager
        import sys
        sys.path.append(os.getcwd())
        from utils import state_manager
        
        # Load job state from Firestore
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔄 Recuperando estado del Job {job_id}..."
        )
        
        job_state = state_manager.cargar_estado(job_id)
        
        if not job_state:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ No se encontró el Job {job_id} en Firestore"
            )
            return
        
        if job_state.estado != "WAITING_FOR_HUMAN":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ El Job {job_id} no está en estado WAITING_FOR_HUMAN\nEstado actual: {job_state.estado}"
            )
            return
        
        # Resume the job (rehidratación)
        razon = job_state.metadata.get('razon', 'N/A')
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🚀 Resucitando Job {job_id}...\n\nPaso actual: {job_state.paso_actual}\nRazón de pausa: {razon}"
        )
        
        # Mark as RUNNING again
        state_manager.guardar_estado(
            job_id=job_id,
            estado="RUNNING",
            paso_actual=job_state.paso_actual,
            variables=job_state.variables,
            metadata={
                "resumed_at": str(asyncio.get_event_loop().time()),
                "resumed_by": "human",
                "previous_state": "WAITING_FOR_HUMAN"
            }
        )
        
        logging.info(f"🧠 RESURRECTION: Job {job_id} estado cambiado a RUNNING")
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ Job reanudado.\n\nEl motor lo procesará en breve cuando se levante una nueva instancia."
        )
        
        # TODO: Trigger Cloud Run job or invoke P6a directly
        # For local: This would require a background worker listening to Firestore changes
        
    except Exception as e:
        logging.error(f"Error in resume_job_handler: {e}")
        import traceback
        traceback.print_exc()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Error resucitando job: {str(e)}"
        )


# ============================================================================
# EMERGENCY NOTIFICATION SYSTEM (Sistema Nervioso)
# ============================================================================

def notificar_emergencia(titulo: str, diagnostico: str, accion_sugerida: str, contexto: Dict[str, Any] = None) -> bool:
    """
    Sends an emergency alert to Telegram synchronously.
    Called by P6a when critical errors occur (gravedad >= 7).
    
    Returns True if notification sent successfully.
    """
    global _chat_id
    
    # Try to load chat_id from file if not set in memory
    if _chat_id is None:
        _chat_id = _load_chat_id_from_file()
    
    if _chat_id is None:
        logging.error("Sixmender: Cannot send emergency alert - chat_id not set. User must /start the bot first.")
        return False
    
    try:
        bot = _get_bot()
        
        # Format emergency message
        contexto_str = ""
        if contexto:
            contexto_str = f"\n\n**Contexto**:\n"
            for k, v in contexto.items():
                contexto_str += f"- {k}: {v}\n"
        
        mensaje = f"""
🚨 **CRITICAL ENGINE ALERT** 🚨

**{titulo}**

**Diagnosis**:
{diagnostico}

**Suggested Action**:
{accion_sugerida}{contexto_str}

_Sent by the Nervous System (P6b → Sixmender)_
        """
        
        # Send synchronously using asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            bot.send_message(chat_id=_chat_id, text=mensaje, parse_mode="Markdown")
        )
        loop.close()
        
        logging.info(f"Sixmender: Emergency notification sent - {titulo}")
        return True
        
    except Exception as e:
        logging.error(f"Sixmender: Failed to send emergency notification: {e}")
        return False

def solicitar_verificacion_humana(service: str, url_kyc: str, job_id: str) -> bool:
    """
    Requests human identity verification (KYC) via Telegram.
    Used by P6a when authentication is needed.
    
    Returns True if notification sent successfully.
    """
    global _chat_id
    
    # Try to load chat_id from file if not set in memory
    if _chat_id is None:
        _chat_id = _load_chat_id_from_file()
    
    if _chat_id is None:
        logging.error("Sixmender: Cannot request verification - chat_id not set.")
        return False
    
    try:
        bot = _get_bot()
        
        mensaje = f"""
🎭 **Identity Verification Required** 🎭

**Service**: {service}
**Job ID**: {job_id}

The engine needs your human identity to continue.

**Steps**:
1. Complete verification here: {url_kyc}
2. Obtain your API Keys
3. Send them using: `/apikey {service} YOUR_KEY_HERE`
4. Resume the job: `/resume_job {job_id}`

_The plan is PAUSED until you confirm._
        """
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            bot.send_message(chat_id=_chat_id, text=mensaje, parse_mode="Markdown")
        )
        loop.close()
        
        logging.info(f"Sixmender: Verification request sent for {service} (Job: {job_id})")
        return True
        
    except Exception as e:
        logging.error(f"Sixmender: Failed to send verification request: {e}")
        return False

def notificar_oportunidad(titulo: str, score: int, resumen: str, propuesta_draft: str, url: str = "#") -> bool:
    """
    Sends a High Value Opportunity alert to Telegram.
    """
    global _chat_id
    if _chat_id is None:
        _chat_id = _load_chat_id_from_file()
    
    if _chat_id is None:
        logging.error("Sixmender: Cannot send opportunity alert - chat_id not set.")
        return False
        
    try:
        bot = _get_bot()
        
        # Determine Status Emoji
        emoji_score = "🟢" if score >= 90 else "🟡"
        
        # 1. Alert Message (Improved Layout)
        mensaje_alerta = f"""
🚀 **NEW OPPORTUNITY DETECTED**

**{titulo}**

{emoji_score} **Score:** `{score}/100`
🔗 [View Original Offer]({url})

📝 **Pain Analysis:**
_{resumen}_

👇 **Generated Proposal Below** 👇
        """
        
        # 2. Proposal Message (Monospaced for copy-paste)
        mensaje_propuesta = f"```\n{propuesta_draft}\n```"
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Send Alert
        loop.run_until_complete(
            bot.send_message(chat_id=_chat_id, text=mensaje_alerta, parse_mode="Markdown")
        )
        
        # Send Proposal
        loop.run_until_complete(
            bot.send_message(chat_id=_chat_id, text=mensaje_propuesta, parse_mode="Markdown")
        )
        
        # Send Actions
        loop.run_until_complete(
            bot.send_message(chat_id=_chat_id, text="Commands: `/proceed` (Simulated) or `/discard`")
        )
        
        loop.close()
        logging.info(f"Sixmender: Opportunity notification sent for {titulo}")
        return True
        
    except Exception as e:
        logging.error(f"Sixmender: Failed to send opportunity notification: {e}")
        return False


# --- ICEBREAKER MODULE (HITO 2.0) ---
import json
from datetime import datetime

CHALLENGE_STATE_FILE = "challenge_state.json"

async def notificar_desafio(screenshot_path: str, contexto: Dict[str, Any] = None) -> bool:
    """
    Envía una alerta de CAPTCHA/Challenge a Telegram con la screenshot.
    """
    global _chat_id
    if _chat_id is None:
        _chat_id = _load_chat_id_from_file()
    
    if _chat_id is None:
        logging.error("Sixmender: Cannot send challenge alert - chat_id not set.")
        return False
    
    try:
        bot = _get_bot()
        
        mensaje = """
🧊 **FREEZE PROTOCOL ACTIVADO** 🧊

**¡Amenaza Detectada!**
El sistema ha detectado un desafío (CAPTCHA/Cloudflare).
El motor está **CONGELADO** esperando órdenes.

**Opciones:**
🔴 `/abort` - Abortar misión y salvar IP.
🟢 `/solve` - Intentar resolución automática (CapSolver).
🟡 `/resume` - Ya lo resolví manualmente (Human).
        """
        
        # Reset state file
        with open(CHALLENGE_STATE_FILE, 'w') as f:
            json.dump({"status": "WAITING", "timestamp": str(datetime.now())}, f)

        # Send photo directly (awaiting)
        with open(screenshot_path, 'rb') as photo:
            await bot.send_photo(chat_id=_chat_id, photo=photo, caption=mensaje, parse_mode="Markdown")
        
        logging.info("Sixmender: Challenge notification sent.")
        return True
        
    except Exception as e:
        logging.error(f"Sixmender: Failed to send challenge notification: {e}")
        return False

async def icebreaker_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja los comandos de respuesta al Freeze Protocol.
    """
    command = update.message.text.replace('/', '')
    
    if command not in ['abort', 'solve', 'resume']:
        return

    logging.info(f"🧊 Icebreaker Command Received: {command}")
    
    # Update state file
    state = {"status": command.upper(), "timestamp": str(datetime.now())}
    with open(CHALLENGE_STATE_FILE, 'w') as f:
        json.dump(state, f)
    
    response_map = {
        'abort': "🔴 Aborting mission... Closing connections.",
        'solve': "🟢 Starting automatic resolution sequence...",
        'resume': "🟡 Resuming engine (Human intervention confirmed)."
    }
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=response_map.get(command, "Comando recibido.")
    )

# --- END ICEBREAKER MODULE ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and handle ChatMigrated."""
    logging.error(msg="Exception while handling an update:", exc_info=context.error)
    
    if isinstance(context.error, ChatMigrated):
        new_chat_id = context.error.new_chat_id
        logging.info(f"⚠️ Chat migrated to new ID: {new_chat_id}. Updating configuration...")
        set_chat_id(new_chat_id)
        
        # If possible, try to notify the user in the new chat
        try:
            await context.bot.send_message(
                chat_id=new_chat_id,
                text=f"🔄 Chat updated to Supergroup. New ID: {new_chat_id} saved."
            )
        except Exception as e:
            logging.error(f"Could not send confirmation to new chat ID: {e}")

def main():
    """
    Main entry point for the Sixmender bot process.
    """
    # Load token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return


# ============================================================================
# DASHBOARD SERVER (AIOHTTP)
# ============================================================================
import aiohttp
from aiohttp import web
import json

class DashboardServer:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/status', self.handle_status)
        self.app.router.add_get('/api/validation_report', self.handle_validation_report)
        self.app.router.add_get('/ws/logs', self.websocket_handler)
        self.runner = None
        self.site = None
        self.websockets = set()

    async def handle_index(self, request):
        try:
            with open('dashboard/index.html', 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        except FileNotFoundError:
            return web.Response(text="Dashboard not found. Run 'mkdir dashboard' and create index.html", status=404)

    async def handle_status(self, request):
        # Read memory stats
        try:
            with open('data/memory/skills_registry.json', 'r') as f: skills = len(json.load(f).get('skills', []))
            with open('data/memory/learned_lessons.json', 'r') as f: lessons = len(json.load(f).get('lessons', []))
            with open('data/memory/long_term_memory.json', 'r') as f: episodes = len(json.load(f).get('episodes', []))
        except:
            skills, lessons, episodes = 0, 0, 0

        status = {
            "status": "ONLINE",
            "active_agent": "Sixmender Core",
            "memory": {
                "skills": skills,
                "lessons": lessons,
                "episodes": episodes
            },
            "system": {
                "cpu": "12%", # Mock for now
                "ram": "450MB"
            }
        }
        return web.json_response(status)

    async def handle_validation_report(self, request):
        try:
            with open('validation_report.json', 'r') as f:
                report = json.load(f)
            return web.json_response(report)
        except FileNotFoundError:
            return web.json_response({"error": "Report not found"}, status=404)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websockets.add(ws)
        
        try:
            async for msg in ws:
                pass # Just keep connection open
        finally:
            self.websockets.remove(ws)
        return ws

    async def broadcast_log(self, message: str, type: str = "info"):
        if not self.websockets: return
        data = json.dumps({"message": message, "type": type})
        for ws in list(self.websockets):
            try:
                await ws.send_str(data)
            except:
                self.websockets.remove(ws)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', 5000)
        await self.site.start()
        logging.info("🌐 Dashboard Server running at http://localhost:5000")

    async def stop(self):
        if self.site: await self.site.stop()
        if self.runner: await self.runner.cleanup()

# Global Server Instance
dashboard_server = DashboardServer()

# Monkey-patch logging to broadcast to dashboard
original_log = logging.info
def broadcast_logging(msg, *args, **kwargs):
    original_log(msg, *args, **kwargs)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(dashboard_server.broadcast_log(str(msg)))
    except RuntimeError:
        pass # No running loop
    except Exception:
        pass

logging.info = broadcast_logging

# Redirect stdout (print) to dashboard
class StreamToDashboard:
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            if line:
                try:
                    # Print to console
                    sys.__stdout__.write(line + '\n')
                    # Send to dashboard
                    loop = asyncio.get_running_loop()
                    loop.create_task(dashboard_server.broadcast_log(line, "info"))
                except RuntimeError:
                    pass # No running loop
                except Exception:
                    pass
    def flush(self):
        sys.__stdout__.flush()
    
    def reconfigure(self, *args, **kwargs):
        # Dummy method to prevent crashes when agents try to set encoding
        pass

sys.stdout = StreamToDashboard()


async def post_init(application: Application) -> None:
    """Start the web server when the bot starts."""
    await dashboard_server.start()

async def post_shutdown(application: Application) -> None:
    """Stop the web server when the bot stops."""
    await dashboard_server.stop()

def main() -> None:
    """
    Main entry point for the Sixmender bot process.
    """
    # Load token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create Application
    application = ApplicationBuilder().token(token).post_init(post_init).post_shutdown(post_shutdown).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("resume_job", resume_job_handler))
    
    # Icebreaker Handlers
    application.add_handler(CommandHandler("abort", icebreaker_command_handler))
    application.add_handler(CommandHandler("solve", icebreaker_command_handler))
    application.add_handler(CommandHandler("resume", icebreaker_command_handler))
    
    # "Don 420" handler (Regex to match case insensitive)
    application.add_handler(MessageHandler(filters.Regex(r"(?i)^don\s?420"), don_420_handler))

    # Message handler - Listen to EVERYTHING to debug
    msg_handler = MessageHandler(filters.ALL, echo_handler)
    application.add_handler(msg_handler)
    
    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    logging.info("🧠 Sixmender (Nervous System) active and listening...")
    print("Sixmender is running. Press Ctrl+C to stop.")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logging.critical(f"🔥 CRITICAL FAILURE IN MAIN LOOP: {e}", exc_info=True)
        print(f"🔥 CRITICAL FAILURE: {e}")

if __name__ == '__main__':
    main()
