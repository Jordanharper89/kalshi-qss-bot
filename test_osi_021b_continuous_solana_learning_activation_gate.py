import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_021_continuous_solana_learning_activation_gate import gate

ROOT = Path(__file__).resolve().parent

class T(unittest.TestCase):
    def test_gate(self):
        g = gate(ROOT)
        print("[COMPONENTS]", g["components_present"])
        print("[LAUNCHER_REGISTERED]", g["launcher_registered"])
        print("[MISSING]", g["missing_components"])
        if not g["continuous_activation_ready"]:
            self.fail("ACTIVATION_NOT_READY_MISSING=" + ",".join(g["missing_components"]))
        self.assertFalse(g["execution_authority"])
        self.assertFalse(g["profitability_certified"])
        print("[PASS] OSI-021B continuous Solana learning activation-ready gate")
        print("[TRADER] All required live Solana research gears are physically present")
        print("[SCOPE] Activation-ready only; restart/live progression/24h learning still require observation")

if __name__ == "__main__":
    unittest.main()
