from __future__ import annotations
from dataclasses import dataclass

from .oad_115_authoritative_sports_idempotent_persistence import persist_current_authoritative_sports
from .oad_114_authoritative_sports_exact_postgresql_readback import exact_authoritative_sports_readback

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class PersistedAuthoritativeSportsCohort:
    rows: tuple
    observation_ids: tuple
    providers: tuple
    cohort_size: int
    committed_new: int
    execution_authority: bool=False

def load_persisted_authoritative_sports_cohort(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):
    p=persist_current_authoritative_sports(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
    )
    ids=tuple(p.observation_ids)
    rows=tuple(exact_authoritative_sports_readback(ids,root)) if ids else ()
    if len(rows)!=len(ids):
        raise RuntimeError("persisted sports cohort exact readback mismatch")
    for oid,row in zip(ids,rows):
        if getattr(row,"observation_id",None)!=oid:
            raise RuntimeError("persisted sports cohort identity mismatch")
    return PersistedAuthoritativeSportsCohort(
        rows=rows,
        observation_ids=ids,
        providers=tuple(p.providers),
        cohort_size=len(rows),
        committed_new=int(p.committed_new),
        execution_authority=False,
    )
