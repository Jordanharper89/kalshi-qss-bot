from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_175_crypto_durable_temporal_intelligence_runtime import run_crypto_durable_temporal_intelligence
from .oad_177_crypto_historical_experience_candidate import build_crypto_historical_experience_candidates,verify_crypto_historical_experience_candidate
from .oad_178_crypto_experience_evidence_lineage import build_crypto_experience_evidence_lineage,verify_crypto_experience_evidence_lineage
from .oad_179_crypto_experience_candidate_postgresql_persistence import persist_crypto_experience_candidates
from .oad_180_crypto_experience_learning_outcome_handoff_gate import evaluate_crypto_learning_handoff

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoHistoricalExperiencePhysicalCertification:
    runtime_ready:bool
    candidates:int
    verified_candidates:int
    verified_lineages:int
    committed_new:int
    exact_readback:int
    outcome_pending:int
    learning_event_ready:int
    assets:tuple
    physical_ready:bool
    certified_at:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_crypto_historical_experience_physical_certification(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0,per_source_history_limit=512):
    runtime=run_crypto_durable_temporal_intelligence(
        root=root,timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
        per_source_history_limit=per_source_history_limit,
    )
    candidates=build_crypto_historical_experience_candidates(runtime)
    lineages=tuple(build_crypto_experience_evidence_lineage(x) for x in candidates)
    verified_candidates=sum(verify_crypto_historical_experience_candidate(x) for x in candidates)
    verified_lineages=sum(verify_crypto_experience_evidence_lineage(x) for x in lineages)
    pairs=tuple(zip(candidates,lineages))
    persisted=persist_crypto_experience_candidates(pairs,root=root,timeout_seconds=timeout_seconds)
    gates=tuple(evaluate_crypto_learning_handoff(c,l) for c,l in pairs)
    pending=sum(x.gate_state=="HOLD_OUTCOME_REQUIRED" for x in gates)
    ready=sum(x.learning_event_ready for x in gates)
    assets=tuple(sorted(x.asset for x in candidates))
    physical_ready=bool(
        runtime.runtime_ready and candidates and verified_candidates==len(candidates)
        and verified_lineages==len(lineages) and persisted.exact_readback==len(candidates)
        and pending==len(candidates) and ready==0
    )
    if not physical_ready:
        raise RuntimeError(
            f"crypto experience certification failed; runtime={runtime.runtime_ready}; "
            f"candidates={len(candidates)}; verified_candidates={verified_candidates}; "
            f"verified_lineages={verified_lineages}; readback={persisted.exact_readback}; "
            f"pending={pending}; learning_ready={ready}"
        )
    return CryptoHistoricalExperiencePhysicalCertification(
        runtime.runtime_ready,len(candidates),verified_candidates,verified_lineages,
        persisted.committed_new,persisted.exact_readback,pending,ready,assets,True,
        datetime.now(timezone.utc).isoformat(),False,False,False
    )
