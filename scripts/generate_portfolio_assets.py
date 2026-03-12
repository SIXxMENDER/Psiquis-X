import os
import shutil
import sys
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_utils import invocar_llm

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"📁 Created directory: {path}")

def copy_dir_contents(src, dst):
    if not os.path.exists(src):
        print(f"⚠️ Source directory not found: {src}")
        return
    
    ensure_dir(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print(f"✅ Copied contents from {src} to {dst}")

import re
import json

def clean_llm_response(response):
    """
    Cleans the response from invocar_llm.
    If it contains an error message with a JSON candidate, it extracts the text from the JSON.
    """
    if not response:
        return ""
        
    try:
        # Check for the specific error pattern
        if "Error generating content" in response and "Candidate:" in response:
            print("⚠️ Detected LLM Error wrapper. Attempting to extract content...")
            
            # Strategy 1: JSON Parsing
            try:
                # Extract the JSON part after "Candidate:"
                json_str = response.split("Candidate:", 1)[1].strip()
                
                # Try to find the JSON object by matching braces
                start = json_str.find("{")
                end = json_str.rfind("}")
                
                if start != -1 and end != -1:
                    json_candidate = json_str[start:end+1]
                    data = json.loads(json_candidate)
                    # Navigate the JSON structure: content -> parts -> [0] -> text
                    text = ""
                    if "content" in data and "parts" in data["content"]:
                        for part in data["content"]["parts"]:
                            if "text" in part:
                                text += part["text"]
                    if text:
                        print("✅ Successfully extracted text from error response (JSON parse).")
                        return text
            except Exception as e:
                print(f"⚠️ JSON parse failed: {e}")

            # Strategy 2: Regex Fallback
            try:
                matches = re.findall(r'"text":\s*"(.*?)"', response, re.DOTALL)
                if matches:
                    # Take the longest match as it's likely the main content
                    longest_match = max(matches, key=len)
                    # Manually unescape common JSON escapes
                    cleaned_text = longest_match.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    print("✅ Successfully extracted text from error response (Regex).")
                    return cleaned_text
            except Exception as e:
                print(f"⚠️ Regex fallback failed: {e}")

    except Exception as e:
        print(f"❌ Unexpected error in clean_llm_response: {e}")
        
    # If all else fails, return the original response (better than crashing)
    return response

def generate_english_content(context, asset_type, asset_name):
    print(f"🧠 Generating English content for {asset_name}...")
    
    prompt_system = """
    You are the Chief Technology Officer of "Psiquis-X", an elite AI agency.
    Your task is to write high-impact, professional technical documentation in ENGLISH.
    
    TONE:
    - Professional, confident, institutional.
    - Persuasive but grounded in technical reality.
    - "Show, don't just tell."
    
    OUTPUT:
    - Return ONLY the content of the requested file (Markdown).
    - Do not include conversational filler.
    """
    
    prompt_user = f"""
    CONTEXT:
    {context}
    
    TASK:
    Generate the **README.md** for the **{asset_name}** repository.
    
    REQUIREMENTS:
    1.  **Title & Subtitle:** Impactful and descriptive.
    2.  **The Problem:** Briefly describe the business pain point this solves.
    3.  **The Solution:** How Psiquis-X solves it (refer to specific scripts/agents if known).
    4.  **Key Features:** Bullet points of technical capabilities.
    5.  **Demo Section:** A placeholder for a GIF/Video (e.g., `![Demo](demo.gif)`).
    6.  **Installation/Usage:** Simple steps to run it.
    7.  **Call to Action:** "Contact us to deploy this architecture."
    
    Make it sound like a premium product.
    """
    
    raw_response = invocar_llm(prompt_system, prompt_user, modelo="gemini-2.5-pro", temperatura=0.7)
    return clean_llm_response(raw_response)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    outputs_dir = os.path.join(root_dir, 'outputs_freelance')
    
    # Define new structure
    repos = {
        "psiquis-quant-engine": {
            "source": "Silver_Arbitrage_Bot",
            "desc": "Institutional-grade algorithmic trading engine with genetic optimization."
        },
        "psiquis-automator": {
            "source": "Gold_FinOps_Pipeline",
            "desc": "Hyper-automation pipeline for financial operations and data extraction."
        },
        "psiquis-genesis-framework": {
            "source": None, # New
            "desc": "The core framework for autonomous agent generation and self-correction."
        },
        ".github": {
            "source": None,
            "desc": "Organization profile and case studies."
        }
    }
    
    print("🚀 Starting Portfolio Generation Sequence...")
    
    # 1. Create Structure & Migrate
    for repo_name, info in repos.items():
        repo_path = os.path.join(outputs_dir, repo_name)
        ensure_dir(repo_path)
        
        # Migration
        if info["source"]:
            src_path = os.path.join(outputs_dir, info["source"])
            if os.path.exists(src_path):
                copy_dir_contents(src_path, repo_path)
        
        # Special case for Genesis (Create dummy files)
        if repo_name == "psiquis-genesis-framework":
            # 1. Base Agent (The Abstract Base Class)
            base_agent_code = """import uuid
import abc
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class GenesisAgent(abc.ABC):
    \"\"\"
    Abstract Base Class for all autonomous agents within the Psiquis Genesis Framework.
    Enforces strict typing, lifecycle management, and neural fabric connectivity.
    \"\"\"
    
    def __init__(self, agent_id: Optional[str] = None, config: Dict[str, Any] = None):
        self.id = agent_id or str(uuid.uuid4())
        self.config = config or {}
        self.created_at = datetime.utcnow()
        self.state = "INITIALIZED"
        self.memory_vector = []  # Placeholder for vector embeddings
        
        self.logger = logging.getLogger(f"GenesisAgent.{self.__class__.__name__}.{self.id}")
        self.logger.info(f"Agent initialized with config: {self.config.keys()}")

    @abc.abstractmethod
    async def perceive(self, environment_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Process incoming sensory data from the environment.
        \"\"\"
        pass

    @abc.abstractmethod
    async def reason(self, context: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Execute cognitive processing and decision making logic.
        \"\"\"
        pass

    @abc.abstractmethod
    async def act(self, decision: Dict[str, Any]) -> None:
        \"\"\"
        Perform actions on the environment based on reasoning.
        \"\"\"
        pass

    def connect_to_fabric(self, fabric_uri: str) -> bool:
        \"\"\"
        Establishes a secure websocket connection to the Neural Fabric.
        \"\"\"
        self.logger.info(f"Handshaking with Neural Fabric at {fabric_uri}...")
        # Simulation of cryptographic handshake
        return True
"""
            with open(os.path.join(repo_path, "base_agent.py"), "w") as f:
                f.write(base_agent_code)

            # 2. Genesis Core (The Engine)
            genesis_core_code = """import asyncio
from typing import List
from .base_agent import GenesisAgent

class GenesisEngine:
    \"\"\"
    The Orchestration Kernel for the Psiquis Genesis Framework.
    Manages agent lifecycles, resource allocation, and inter-agent communication protocols.
    \"\"\"
    
    def __init__(self):
        self.agents: List[GenesisAgent] = []
        self.tick_rate = 60  # Hz
        self.is_running = False

    def register_agent(self, agent: GenesisAgent):
        \"\"\"
        Registers a new agent into the active runtime.
        \"\"\"
        print(f"[KERNEL] Registering agent: {agent.id} ({type(agent).__name__})")
        self.agents.append(agent)

    async def run_loop(self):
        \"\"\"
        Main event loop. Synchronizes agent perception and action cycles.
        \"\"\"
        self.is_running = True
        print("[KERNEL] Genesis Engine Online. Neural Fabric Active.")
        
        while self.is_running:
            # 1. Perception Phase
            perception_tasks = [agent.perceive({}) for agent in self.agents]
            await asyncio.gather(*perception_tasks)
            
            # 2. Reasoning Phase
            # ... (Complex orchestration logic would go here)
            
            # 3. Action Phase
            # ...
            
            await asyncio.sleep(1 / self.tick_rate)

if __name__ == "__main__":
    # Example Usage
    engine = GenesisEngine()
    print("Genesis Framework v2.4.0 - Initialized")
"""
            with open(os.path.join(repo_path, "genesis_core.py"), "w") as f:
                f.write(genesis_core_code)

    # 2. Generate Content (READMEs)
    for repo_name, info in repos.items():
        repo_path = os.path.join(outputs_dir, repo_name)
        readme_path = os.path.join(repo_path, "README.md")
        
        content = generate_english_content(info["desc"], "Repository", repo_name)
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Generated README.md for {repo_name}")

    # 3. Generate Profile Content (.github)
    profile_dir = os.path.join(outputs_dir, ".github", "profile")
    ensure_dir(profile_dir)
    
    print("🧠 Generating Profile README...")
    profile_content_raw = invocar_llm(
        prompt_sistema="You are an expert copywriter for GitHub profiles.",
        prompt_usuario="Generate a stunning **profile/README.md** for 'Psiquis-X', an AI Agency. Include a table linking to: psiquis-quant-engine, psiquis-automator, psiquis-genesis-framework. Use badges. English only.",
        modelo="gemini-2.5-pro"
    )
    profile_content = clean_llm_response(profile_content_raw)
    
    with open(os.path.join(profile_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(profile_content)

    print("🧠 Generating Case Studies...")
    case_studies_raw = invocar_llm(
        prompt_sistema="You are a technical writer.",
        prompt_usuario="Generate a **CASE_STUDIES.md** file with 2 simulated success stories (Silverfish Arbitrage and Gold FinOps). Use metrics. English only.",
        modelo="gemini-2.5-pro"
    )
    case_studies_content = clean_llm_response(case_studies_raw)
    
    with open(os.path.join(outputs_dir, ".github", "CASE_STUDIES.md"), "w", encoding="utf-8") as f:
        f.write(case_studies_content)

    # 4. Generate Demo Guide
    print("🧠 Generating Demo Recording Guide...")
    demo_guide_raw = invocar_llm(
        prompt_sistema="You are a video production expert.",
        prompt_usuario="Generate a **DEMO_RECORDING_GUIDE.md**. Instructions for recording a 60s terminal demo using OBS. Include a script for AI voiceover. English only.",
        modelo="gemini-2.5-pro"
    )
    demo_guide_content = clean_llm_response(demo_guide_raw)
    
    with open(os.path.join(outputs_dir, "DEMO_RECORDING_GUIDE.md"), "w", encoding="utf-8") as f:
        f.write(demo_guide_content)

    print("\n✅ Portfolio Generation Complete! Check 'outputs_freelance'.")

if __name__ == "__main__":
    main()
