from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from .oad_116_authoritative_sports_production_persistence_certification import (
    run_authoritative_sports_production_certification,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class LiveSportsPersistenceGate:
    certified: bool
    cohort_size: int
    already_present: int
    committed_new: int
    exact_readback: int
    providers: tuple
    certified_at: str
    execution_authority: bool=False

def run_live_authoritative_sports_persistence_gate(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):
    r=run_authoritative_sports_production_certification(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
    )
    if r.get("certified") is not True:
        raise RuntimeError("authoritative sports production persistence not certified")
    cohort=int(r.get("cohort_size",0))
    exact=int(r.get("exact_readback",0))
    already=int(r.get("already_present",0))
    committed=int(r.get("committed_new",0))
    if exact!=cohort:
        raise RuntimeError("live sports exact readback does not equal cohort")
    if already+committed!=cohort:
        raise RuntimeError("live sports persistence accounting does not close")
    return LiveSportsPersistenceGate(
        certified=True,
        cohort_size=cohort,
        already_present=already,
        committed_new=committed,
        exact_readback=exact,
        providers=tuple(r.get("providers",())),
        certified_at=datetime.now(timezone.utc).isoformat(),
        execution_authority=False,
    )
