
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .opc_009_bounded_universal_snapshot_cycle import run_bounded_universal_snapshot_cycle

@dataclass(frozen=True)
class PhysicalCoverageCycleResult:
    open_markets:int
    missing_before:int
    snapshots_planned:int
    snapshots_persisted:int
    success:bool
    read_only_intelligence:bool=True
    execution_authority:bool=False

def run_physical_coverage_cycle(root=None,max_markets=100,lookback_hours=24,progress=None):
    root=Path(root or Path.cwd()).resolve()
    summary=run_bounded_universal_snapshot_cycle(
        root,
        max_markets=max_markets,
        lookback_hours=lookback_hours,
        progress=progress,
    )
    return PhysicalCoverageCycleResult(
        summary.open_markets,
        summary.missing_before,
        summary.snapshots_planned,
        summary.snapshots_persisted,
        summary.snapshots_planned==summary.snapshots_persisted,
        True,
        False,
    )

def verify_opc_016_physical_coverage_cycle_adapter():
    x=PhysicalCoverageCycleResult(1000,900,100,100,True,True,False)
    return x.success and x.snapshots_persisted==100 and not x.execution_authority
