from __future__ import annotations
from dataclasses import dataclass
from .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences
from .oad_188_crypto_verified_learned_case_postgresql_persistence import persist_verified_learned_cases
from .oad_198_crypto_continuous_exact_outcome_maturation import mature_continuous_crypto_outcomes

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class ContinuousVerifiedLearnedCaseResult:
    exact_outcomes:int
    candidate_matches:int
    already_present:int
    committed_new:int
    exact_readback:int
    experience_ids:tuple
    assets:tuple
    physical_ready:bool
    execution_authority:bool=False

def form_continuous_verified_learned_cases(
    root=None,
    horizon_seconds:int=60,
    timeout_seconds:float=120.0,
    acquisition_timeout_seconds:float=20.0,
    per_asset_limit:int=256,
    now=None,
):
    maturity=mature_continuous_crypto_outcomes(
        root=root,horizon_seconds=horizon_seconds,timeout_seconds=acquisition_timeout_seconds,
        per_asset_limit=per_asset_limit,now=now
    )
    if not maturity.outcomes:
        return ContinuousVerifiedLearnedCaseResult(
            0,0,0,0,0,tuple(),tuple(),True,False
        )
    rb=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)
    by_id={x.experience_id:x for x in rb.records}
    pairs=[]
    for outcome in maturity.outcomes:
        experience=by_id.get(outcome.experience_id)
        if experience is None:
            raise RuntimeError("exact outcome has no persisted source experience")
        pairs.append((experience,outcome))
    persisted=persist_verified_learned_cases(tuple(pairs),root=root,timeout_seconds=timeout_seconds)
    ready=bool(persisted.exact_readback==len(pairs))
    return ContinuousVerifiedLearnedCaseResult(
        len(maturity.outcomes),len(pairs),int(persisted.already_present),int(persisted.committed_new),
        int(persisted.exact_readback),tuple(x[0].experience_id for x in pairs),
        tuple(sorted({x[0].asset for x in pairs})),ready,False
    )
