import unittest
import asyncio
import os
import shutil
import sys
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.loader import PluginLoader
from core.registry import AgentRegistry
from agentes import agente_p1_ingesta
from agentes import agente_p5_genesis

class TestFinalIntegration(unittest.TestCase):
    
    def setUp(self):
        # Backup config
        if os.path.exists("config/agents.yaml"):
            shutil.copy("config/agents.yaml", "config/agents.yaml.bak")
        
    def tearDown(self):
        # Restore config
        if os.path.exists("config/agents.yaml.bak"):
            shutil.move("config/agents.yaml.bak", "config/agents.yaml")
        # Cleanup generated agents
        if os.path.exists("agentes/generated"):
            shutil.rmtree("agentes/generated")

    @patch('agentes.ingestion.agente_web_scraper.ejecutar', new_callable=MagicMock)
    @patch('agentes.agente_p0.ejecutar', new_callable=MagicMock)
    @patch('agentes.agente_p3.ejecutar', new_callable=MagicMock)
    @patch('agentes.genesis_sandbox.validar_con_reintentos', new_callable=MagicMock)
    def test_full_system_flow(self, mock_validate, mock_p3, mock_p0, mock_scraper):
        """
        Verifies:
        1. Plugin Loading
        2. P1 Facade Routing
        3. P5 Auto-Evolution
        """
        print("\n🧪 --- STARTING FINAL SYSTEM TEST ---")
        
        # 1. Test Plugin Loader
        print("🧪 1. Testing Plugin Loader...")
        loader = PluginLoader()
        loader.load_plugins()
        self.assertTrue(len(loader.get_loaded_plugins()) > 0, "No plugins loaded")
        print("   ✅ Plugins Loaded")

        # 2. Test P1 Facade (Ingestion)
        print("🧪 2. Testing P1 Facade (Ingestion)...")
        f_scrape = asyncio.Future()
        f_scrape.set_result({"status": "MOCK_OK", "data": "some data"})
        mock_scraper.return_value = f_scrape
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        p1_result = loop.run_until_complete(agente_p1_ingesta.ejecutar(url="http://test.com"))
        self.assertEqual(p1_result["status"], "MOCK_OK")
        print("   ✅ P1 Facade Routing Working")

        # 3. Test P5 Meta-Genesis (Evolution)
        print("🧪 3. Testing P5 Meta-Genesis (Evolution)...")
        
        # Mock P0
        f_p0 = asyncio.Future()
        f_p0.set_result({"respuesta": "Research done"})
        mock_p0.return_value = f_p0
        
        # Mock P3 (Generate a valid agent)
        code = """
async def ejecutar(**kwargs):
    return {'status': 'EVOLVED', 'msg': 'I am alive'}
"""
        f_p3 = asyncio.Future()
        f_p3.set_result({"codigo_python": code})
        mock_p3.return_value = f_p3
        
        # Mock Validation
        f_val = asyncio.Future()
        f_val.set_result((True, "", 1))
        mock_validate.return_value = f_val
        
        # Register Mocks in Registry for P5 to find them
        AgentRegistry.register("P0", MagicMock(ejecutar=mock_p0))
        AgentRegistry.register("P3", MagicMock(ejecutar=mock_p3))
        AgentRegistry.register("P8", MagicMock()) # P8 is used for file ops, but we mocked the file write in P5 logic? 
        # Wait, P5 MetaGenesis writes directly to file now, but imports P8. 
        # We need to make sure P8 doesn't crash if called, though MetaGenesis uses standard open() for the agent file.
        
        p5_result = loop.run_until_complete(agente_p5_genesis.ejecutar_genesis("Create a test agent"))
        
        self.assertEqual(p5_result["status"], "SUCCESS")
        print(f"   ✅ P5 Auto-Evolution Working (New Skill: {p5_result['skill']})")
        
        loop.close()
        print("🧪 --- FINAL SYSTEM TEST PASSED ---")

if __name__ == '__main__':
    unittest.main()
