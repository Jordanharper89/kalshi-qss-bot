from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
RUNNER_NAME="run_oad_276_solana_continuous_observation_production_child.py"

@dataclass(frozen=True,slots=True)
class SolanaContinuousRunnerAdmission:
    runner_present:bool
    check_interface_present:bool
    bounded_cycle_interface_present:bool
    execution_boundary_preserved:bool
    admitted:bool

def evaluate_solana_continuous_runner(root=None):
    root=Path(root or Path.cwd()).resolve()
    p=root/RUNNER_NAME
    if not p.is_file():
        return SolanaContinuousRunnerAdmission(False,False,False,True,False)
    src=p.read_text(encoding="utf-8")
    check="--check" in src
    bounded="--max-cycles" in src
    safe="execution_authority=TRUE" not in src and "EXECUTION_AUTHORITY=True" not in src
    return SolanaContinuousRunnerAdmission(True,check,bounded,safe,bool(check and bounded and safe))
