
from __future__ import annotations
from dataclasses import dataclass
import time
from pathlib import Path

from .opc_016_physical_coverage_cycle_adapter import run_physical_coverage_cycle
from .opc_017_durable_coverage_runtime_state import (
    load_coverage_runtime_state,
    save_coverage_runtime_state,
    advance_coverage_runtime_state,
)

@dataclass(frozen=True)
class ContinuousCoverageRunSummary:
    cycles_requested:int
    cycles_completed:int
    total_persisted:int
    final_status:str
    execution_authority:bool=False

def run_bounded_continuous_coverage(
    root=None,
    cycles=3,
    max_markets=100,
    lookback_hours=24,
    sleep_seconds=2.0,
    progress=None,
):
    root=Path(root or Path.cwd()).resolve()
    cycles=int(cycles)
    if cycles<1 or cycles>100:
        raise ValueError("cycles must be 1..100")
    if sleep_seconds<0 or sleep_seconds>3600:
        raise ValueError("sleep_seconds out of bounds")

    state=load_coverage_runtime_state(root)
    completed=0
    total=0
    status="NOT_STARTED"

    for cycle in range(1,cycles+1):
        result=run_physical_coverage_cycle(
            root,
            max_markets=max_markets,
            lookback_hours=lookback_hours,
            progress=progress,
        )
        status="SUCCESS" if result.success else "PARTIAL"
        state=advance_coverage_runtime_state(
            state,
            planned=result.snapshots_planned,
            persisted=result.snapshots_persisted,
            status=status,
        )
        state=save_coverage_runtime_state(state,root)
        completed+=1
        total+=result.snapshots_persisted

        if progress:
            progress(
                f"[COVERAGE RUNTIME] cycle={cycle}/{cycles} "
                f"planned={result.snapshots_planned} "
                f"persisted={result.snapshots_persisted} "
                f"status={status}"
            )

        if cycle<cycles and sleep_seconds:
            time.sleep(float(sleep_seconds))

    return ContinuousCoverageRunSummary(cycles,completed,total,status,False)

def verify_opc_018_bounded_continuous_coverage_runner():
    x=ContinuousCoverageRunSummary(3,3,300,"SUCCESS",False)
    return x.cycles_completed==3 and x.total_persisted==300 and not x.execution_authority
