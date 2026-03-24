
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Forzar ruta raíz para imports
sys.path.append(os.getcwd())

class TestStructuralIntegrity(unittest.TestCase):
    """
    NIVEL A: Pruebas de Integridad Estructural ($0 Token Cost).
    Valida la arquitectura LangGraph sin invocar LLMs.
    """

    def setUp(self):
        # Mocker Genérico para 'cortex.ask' (Evita llamadas a Gemini)
        self.patcher = patch('core.cortex.cortex.ask')
        self.mock_ask = self.patcher.start()
        self.mock_ask.return_value = "MOCK_RESPONSE"

    def tearDown(self):
        self.patcher.stop()

    def test_01_imports_critical(self):
        """Verifica que los módulos core cargan sin errores de sintaxis/dependencias."""
        try:
            import core.topology.supervisor
            import core.topology.subgraphs.finance
            import core.topology.subgraphs.marketing
            import core.topology.main_graph
        except ImportError as e:
            self.fail(f"CRITICAL: Fallo al importar módulos core: {e}")

    def test_02_graph_compilation(self):
        """Verifica que el Grafo Soberano compila (sin ciclos infinitos obvios)."""
        try:
            from core.topology.main_graph import sovereign_engine
            # Verificar que es un CompiledStateGraph
            self.assertTrue(hasattr(sovereign_engine, "astream"), "El motor no expone 'astream'")
        except Exception as e:
            self.fail(f"CRITICAL: El grafo no compila: {e}")

    def test_03_node_connectivity(self):
        """Verifica la conectividad básica de los subgrafos (Mockeado)."""
        from core.topology.subgraphs.marketing import marketing_graph
        
        # Simular Estado Inicial
        mock_state = {"objetivo_general": "TEST_MARKETING", "messages": []}
        
        # Ejecutar grafo en modo mock (ainvoke)
        # Nota: Al ser async, unitest estándar requiere un wrapper, 
        # pero aquí validamos solo la instanciación por ahora.
        self.assertIsNotNone(marketing_graph, "El grafo de marketing es None")

    def test_04_vault_paths_exist(self):
        """Valida que las carpetas de datos existan para evitar FileNotFoundError."""
        required_dirs = ["data/finance", "data/marketing", "data/development", "data/research"]
        for d in required_dirs:
            self.assertTrue(os.path.exists(d), f"Falta directorio crítico: {d}")

if __name__ == '__main__':
    print("🛡️ [GAUNTLET] Iniciando Nivel A: Structural Integrity Test...")
    unittest.main(verbosity=2)
