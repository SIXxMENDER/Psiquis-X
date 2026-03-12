import yaml
import importlib
import logging
import os
from typing import List, Dict, Any
from core.registry import AgentRegistry

class PluginLoader:
    """
    Loads agents dynamically based on a YAML configuration file.
    Acts as the 'Brain Loader' for the engine.
    """
    
    def __init__(self, config_path: str = "config/agents.yaml"):
        self.config_path = config_path
        self.loaded_plugins = []

    def load_plugins(self):
        """
        Reads the config and imports enabled agents.
        """
        if not os.path.exists(self.config_path):
            logging.error(f"❌ [Loader] Config not found: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                
            agents_config = config.get("agents", [])
            logging.info(f"🔌 [Loader] Found {len(agents_config)} agents in config.")
            
            for agent_conf in agents_config:
                self._load_single_agent(agent_conf)
                
        except Exception as e:
            logging.error(f"❌ [Loader] Error reading config: {e}")

    def _load_single_agent(self, agent_conf: Dict[str, Any]):
        name = agent_conf.get("name")
        module_path = agent_conf.get("module")
        enabled = agent_conf.get("enabled", False)
        
        if not enabled:
            logging.info(f"⚪ [Loader] Skipping disabled agent: {name}")
            return

        try:
            logging.info(f"🔌 [Loader] Loading {name} from {module_path}...")
            # Dynamic Import
            module = importlib.import_module(module_path)
            
            # The agent module should register itself via AgentRegistry.register() 
            # when imported. We verify if it's in the registry.
            # Note: The name in registry might differ from config name if hardcoded in agent.
            # Ideally, we should enforce consistency, but for now we trust the import side-effect.
            
            self.loaded_plugins.append(name)
            logging.info(f"✅ [Loader] Successfully loaded: {name}")
            
        except ImportError as e:
            logging.error(f"❌ [Loader] Failed to import {module_path}: {e}")
        except Exception as e:
            logging.error(f"❌ [Loader] Error loading {name}: {e}")

    def get_loaded_plugins(self) -> List[str]:
        return self.loaded_plugins

    def hot_reload(self):
        """
        Reloads all plugins from config without restarting the engine.
        Useful for Auto-Evolution when a new agent is generated.
        """
        logging.info("🔥 [Loader] Initiating Hot Reload...")
        
        # 1. Clear internal state
        self.loaded_plugins = []
        
        # 2. Re-read config
        if not os.path.exists(self.config_path):
            logging.error(f"❌ [Loader] Config not found: {self.config_path}")
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            agents_config = config.get("agents", [])
            
            for agent_conf in agents_config:
                name = agent_conf.get("name")
                module_path = agent_conf.get("module")
                enabled = agent_conf.get("enabled", False)
                
                if not enabled:
                    continue
                    
                # Check if module is already imported
                if module_path in sys.modules:
                    logging.info(f"🔄 [Loader] Reloading existing module: {module_path}")
                    try:
                        module = sys.modules[module_path]
                        importlib.reload(module)
                        self.loaded_plugins.append(name)
                    except Exception as e:
                        logging.error(f"❌ [Loader] Failed to reload {module_path}: {e}")
                else:
                    # New module
                    self._load_single_agent(agent_conf)
                    
            logging.info(f"✅ [Loader] Hot Reload Complete. Active Plugins: {self.loaded_plugins}")
            
        except Exception as e:
            logging.error(f"❌ [Loader] Hot Reload Failed: {e}")
