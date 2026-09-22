from __future__ import annotations
from dataclasses import dataclass

from .oad_111_authoritative_sports_physical_acquisition_gate import run_physical_gate
from .oad_112_authoritative_sports_canonical_batch_gate import AuthoritativeSportsCanonicalBatch
from .oad_113_authoritative_sports_single_writer_binding import (
    submit_authoritative_sports_batch,
    await_authoritative_sports_commit,
)
from .oad_114_authoritative_sports_exact_postgresql_readback import (
    find_authoritative_sports_observation,
    exact_authoritative_sports_readback,
)

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True, slots=True)
class AuthoritativeSportsPersistenceResult:
    cohort_size: int
    already_present: int
    missing_before_write: int
    committed_new: int
    exact_readback: int
    request_id: str|None
    providers: tuple
    observation_ids: tuple
    execution_authority: bool=False

def persist_current_authoritative_sports(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):
    physical=run_physical_gate(timeout_seconds=acquisition_timeout_seconds)
    canonical=tuple(physical["canonical"])
    if not canonical:
        return AuthoritativeSportsPersistenceResult(
            0,0,0,0,0,None,tuple(physical["providers"]),(),False
        )

    existing=[]
    missing=[]
    for i,obs in enumerate(canonical):
        row=find_authoritative_sports_observation(obs.observation_id,root,i)
        if row is None:
            missing.append(obs)
        else:
            if getattr(row,"observation_id",None)!=obs.observation_id:
                raise RuntimeError("exact PostgreSQL identity mismatch")
            existing.append(row)

    request_id=None
    committed_new=0
    if missing:
        batch=AuthoritativeSportsCanonicalBatch(
            canonical_observations=tuple(missing),
            provenance_validated=len(missing),
            ready_for_existing_single_writer=True,
            acquisition_batch_id="oad115.missing-only",
            execution_authority=False,
        )
        submission=submit_authoritative_sports_batch(batch,root)
        request_id=str(submission.request_id)
        evidence=tuple(await_authoritative_sports_commit(request_id,root,timeout_seconds))
        accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)
        if len(accepted)!=len(missing):
            raise RuntimeError("sports single-writer commit count mismatch")
        committed_new=len(accepted)

    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_authoritative_sports_readback(ids,root))
    if len(rows)!=len(ids):
        raise RuntimeError("sports exact readback count mismatch")
    return AuthoritativeSportsPersistenceResult(
        cohort_size=len(ids),
        already_present=len(existing),
        missing_before_write=len(missing),
        committed_new=committed_new,
        exact_readback=len(rows),
        request_id=request_id,
        providers=tuple(physical["providers"]),
        observation_ids=ids,
        execution_authority=False,
    )
