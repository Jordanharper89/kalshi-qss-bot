from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence
from .oad_177_crypto_historical_experience_candidate import (
    build_crypto_historical_experience_candidates,
    verify_crypto_historical_experience_candidate,
)
from .oad_178_crypto_experience_evidence_lineage import (
    build_crypto_experience_evidence_lineage,
    verify_crypto_experience_evidence_lineage,
)
from .oad_179_crypto_experience_candidate_postgresql_persistence import persist_crypto_experience_candidates

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class ContinuousCryptoExperienceFormationResult:
    snapshot_at:str
    runtime_ready:bool
    candidates:int
    verified_candidates:int
    verified_lineages:int
    already_present:int
    committed_new:int
    exact_readback:int
    assets:tuple
    experience_ids:tuple
    physical_ready:bool
    execution_authority:bool=False

def form_continuous_crypto_experience_cycle(
    root=None,
    timeout_seconds:float=120.0,
    acquisition_timeout_seconds:float=20.0,
    per_source_history_limit:int=512,
    snapshot_at=None,
):
    runtime=run_crypto_durable_temporal_intelligence(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
        per_source_history_limit=per_source_history_limit,
        snapshot_at=snapshot_at,
    )
    if not runtime.runtime_ready:
        raise RuntimeError("durable temporal intelligence runtime is not ready")
    candidates=build_crypto_historical_experience_candidates(runtime)
    verified=tuple(x for x in candidates if verify_crypto_historical_experience_candidate(x))
    if len(verified)!=len(candidates):
        raise RuntimeError("continuous experience candidate verification mismatch")
    lineages=tuple(build_crypto_experience_evidence_lineage(x) for x in verified)
    if not all(verify_crypto_experience_evidence_lineage(x) for x in lineages):
        raise RuntimeError("continuous experience lineage verification failed")
    pairs=tuple(zip(verified,lineages))
    persisted=persist_crypto_experience_candidates(pairs,root=root,timeout_seconds=timeout_seconds)
    assets=tuple(sorted(x.asset for x in verified))
    ids=tuple(sorted(x.experience_id for x in verified))
    ready=bool(
        verified and
        persisted.exact_readback==len(verified) and
        len(lineages)==len(verified)
    )
    return ContinuousCryptoExperienceFormationResult(
        str(runtime.snapshot_at),bool(runtime.runtime_ready),len(candidates),len(verified),len(lineages),
        int(persisted.already_present),int(persisted.committed_new),int(persisted.exact_readback),
        assets,ids,ready,False
    )
