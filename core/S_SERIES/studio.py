import os
import json
from datetime import datetime
import logging
import asyncio
import edge_tts
from core.cortex import Cortex

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Studio")

class ScriptWriter:
    def __init__(self, data_lake_path="market_data_lake.json"):
        self.data_lake_path = data_lake_path
        self.cortex = Cortex()
        self.style_profile = self._analyze_style()

    def _analyze_style(self):
        """
        Analyzes the user's past videos to determine the 'Voice of the Brand'.
        """
        try:
            with open(self.data_lake_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            videos = data.get("me", {}).get("videos", [])
            if not videos:
                return "Estilo genérico ocultista."

            # Calculate average length
            lengths = [len(v.get("description", "")) for v in videos]
            avg_len = sum(lengths) / len(lengths) if lengths else 0
            
            # Extract sample texts for few-shot prompting
            samples = [v.get("description", "") for v in videos[:3]]
            
            style = {
                "avg_length": int(avg_len),
                "samples": samples,
                "tone": "Solemne, poético, devocional, directo."
            }
            logger.info("✅ Style Profile Extracted.")
            return style
        except Exception as e:
            logger.error(f"❌ Failed to analyze style: {e}")
            return None

    def generate_script(self, topic: str) -> str:
        """
        Generates a TikTok script for a specific topic using the Forensic Strategy.
        Topic: e.g., "Señales de que Mammon te escucha"
        """
        prompt = f"""
        ACTÚA COMO: El Guionista de 'Doctrina Oscura'.
        
        TU MISIÓN: Escribir un guion para TikTok sobre: "{topic}".
        
        ESTROGIA FORENSE (OBLIGATORIA):
        1. Gancho (0-3s): Pregunta de reto o afirmación polémica.
        2. Cuerpo: Dato técnico ocultista (nombres, libros, jerarquías).
        3. Cierre: Llamado a la acción (Guardar video).
        
        ESTILO DE ESCRITURA (DIALECTO MISTÉRICO):
        - Usa palabras arcaicas/cultas (Ej: "Recinto", "Morada", "Velo", "Impío", "Transmutar").
        - Articulación: Usa puntos suspensivos (...) para marcar pausas dramáticas.
        - Estructura: Frases cortas y contundentes.
        - Tono: Profético, Oscuro, Autoritario (No pidas por favor, ORDENA).
        
        REGLAS:
        - INCLUYE pausas explícitas (...) en el texto.
        - NO uses 'Hola amigos'. Empieza directo con el misterio.
        """
        
        logger.info(f"✍️ Generating script for: {topic}")
        script = self.cortex.ask(user_prompt=prompt, system_prompt="Eres un experto en Ocultismo y Copywriting persuasivo.")
        return script.strip()

class VoiceoverArtist:
    def __init__(self):
        # Voice: es-MX-DaliaNeural (Female) or es-MX-JorgeNeural (Male). 
        # For "Doctrina Oscura", a male voice might fit better, or a deep female one.
        # Jorge is usually good for narration.
        self.voice = "es-MX-JorgeNeural" 
        
    async def generate_audio(self, text: str, output_file: str):
        """
        Generates TTS audio using Edge-TTS.
        Voice: 'es-US-AlonsoNeural'.
        Parameters for 'Natural Deep' (Oscuridad Humana):
        - Pitch: -8Hz (Deep but strictly preserving neural articulation).
        - Rate: -5% (Slightly slower for solemnity, avoiding drag).
        - Volume: +10% (Presence).
        """
        logger.info(f"🎙️ Generating Audio (NATURAL DEEP): {output_file}")
        voice = "es-US-AlonsoNeural" 
        # The 'Sweet Spot' for this model before it breaks into metallic sound.
        communicate = edge_tts.Communicate(text, voice, rate="-5%", pitch="-8Hz", volume="+10%")
        await communicate.save(output_file)
        logger.info("✅ Audio Saved.")
        
# Facade for easy usage
class Studio:
    def __init__(self):
        self.writer = ScriptWriter()
        self.voice = VoiceoverArtist()
        
    def produce_audio_content(self, topic: str, output_filename: str):
        """
        Generates Script -> Audio.
        """
        # 1. Write Script
        script = self.writer.generate_script(topic)
        print(f"\n📜 GUION GENERADO ({topic}):\n{script}\n")
        
        # 2. Save Script Text
        txt_filename = output_filename.replace(".mp3", ".txt")
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(script)
            
        # 3. Generate Audio (Async wrapper)
        loop = asyncio.get_event_loop_policy().get_event_loop()
        loop.run_until_complete(self.voice.generate_audio(script, output_filename))
        
        return script, output_filename

studio = Studio()
