from pathlib import Path

ROOT = Path(__file__).resolve().parent
MOD = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_021_continuous_solana_learning_activation_gate.py"
TEST = ROOT / "test_osi_021b_continuous_solana_learning_activation_gate.py"

MOD_TEXT = r"""from __future__ import annotations
from pathlib import Path

def gate(root: Path) -> dict:
    required = {
        "live_child": root / "run_osi_solana_intelligence_live.py",
        "restart_recovery": root / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_019_restart_recovery_gate.py",
        "throughput_gate": root / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_020_live_throughput_observation_gate.py",
        "outcome_worker": root / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_014_live_outcome_maturity_worker.py",
        "learning_runtime": root / "qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_010_continuous_strategy_learning_runtime.py",
    }
    present = {name: path.is_file() for name, path in required.items()}
    launcher = (root / "run_oracle_live.py").read_text(encoding="utf-8", errors="replace")
    launcher_registered = "run_osi_solana_intelligence_live.py" in launcher
    missing = [name for name, ok in present.items() if not ok]
    if not launcher_registered:
        missing.append("launcher_registration")
    ready = not missing
    return {
        "components_present": present,
        "launcher_registered": launcher_registered,
        "missing_components": missing,
        "continuous_activation_ready": ready,
        "execution_authority": False,
        "read_only": True,
        "profitability_certified": False,
        "continuous_24h_certified": False,
    }
"""

TEST_TEXT = r"""import unittest
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
"""

def main():
    print("=" * 112)
    print(" OSI-021B CONTINUOUS SOLANA LEARNING ACTIVATION DIAGNOSTIC GATE")
    print("=" * 112)
    MOD.parent.mkdir(parents=True, exist_ok=True)
    MOD.write_text(MOD_TEXT, encoding="utf-8")
    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print("[PASS] replaced:", MOD.relative_to(ROOT))
    print("[PASS] test:", TEST.name)
    print("[PASS] execution_authority=FALSE")
    print("[SCOPE] Replacement for failed OSI-021; names exact missing activation component")

if __name__ == "__main__":
    main()
