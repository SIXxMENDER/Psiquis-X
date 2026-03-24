import os
import sys

# Simulation of environment
os.environ["ENV"] = "test"
sys.path.append(os.getcwd())

print("--- [SMOKE TEST V3] ---")

try:
    print("1. Testing cortex import...")
    from core.cortex import cortex
    print("✅ Cortex imported.")
except Exception as e:
    print(f"❌ Cortex failed: {e}")

try:
    print("2. Testing mission manager...")
    from core.mission_control import mission_manager
    print("✅ Mission Control imported.")
except Exception as e:
    print(f"❌ Mission Control failed: {e}")

try:
    print("3. Testing state manager...")
    from core.state_manager import StateManager
    sm = StateManager()
    print("✅ State Manager imported and initialized.")
except Exception as e:
    print(f"❌ State Manager failed: {e}")

try:
    print("4. Testing LangGraph import...")
    from core.topology.main_graph import sovereign_engine
    print("✅ Sovereign Engine (LangGraph) imported.")
except Exception as e:
    print(f"❌ LangGraph failed: {e}")

print("--- [SMOKE TEST COMPLETE] ---")
