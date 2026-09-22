from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences
from .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences
from .oad_187_crypto_exact_horizon_coinbase_outcome import acquire_exact_coinbase_outcome
from .oad_188_crypto_verified_learned_case_postgresql_persistence import persist_verified_learned_cases
from .oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history
from .oad_190_crypto_comparable_condition_outcome_statistics import build_comparable_condition_outcome_statistics

READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoDurableLearningStatisticsCertification:
    persisted_experiences:int; mature_experiences:int; exact_outcomes:int; learned_cases_written:int
    exact_readback:int; historical_learned_cases:int; statistics_groups:int; assets:tuple; physical_ready:bool
    certified_at:str; probability_enabled:bool=False; direction_enabled:bool=False; execution_authority:bool=False

def run_crypto_durable_learning_statistics_physical_certification(root=None,horizon_seconds=60,timeout_seconds=120.0,per_asset_limit=256):
    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)
    mature=select_mature_crypto_experiences(rb.records,horizon_seconds=horizon_seconds,now=datetime.now(timezone.utc),latest_per_asset=True)
    if not mature: raise RuntimeError("no mature persisted crypto experiences")
    outcomes=tuple(acquire_exact_coinbase_outcome(x.experience,horizon_seconds,min(20.0,float(timeout_seconds))) for x in mature)
    pairs=tuple((m.experience,o) for m,o in zip(mature,outcomes))
    persisted=persist_verified_learned_cases(pairs,root=root,timeout_seconds=timeout_seconds)
    history=read_crypto_learned_case_history(root=root,per_asset_limit=512)
    stats=build_comparable_condition_outcome_statistics(history)
    assets=tuple(sorted({x.asset for x in history}))
    ready=bool(outcomes and persisted.exact_readback==len(outcomes) and len(history)>=len(outcomes) and stats)
    if not ready: raise RuntimeError(f"durable learning statistics certification failed outcomes={len(outcomes)} readback={persisted.exact_readback} history={len(history)} stats={len(stats)}")
    return CryptoDurableLearningStatisticsCertification(rb.experiences,len(mature),len(outcomes),persisted.committed_new,persisted.exact_readback,len(history),len(stats),assets,True,datetime.now(timezone.utc).isoformat(),False,False,False)
