from __future__ import annotations
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
