from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from types import SimpleNamespace
from .oad_182_crypto_persisted_experience_exact_readback import read_persisted_crypto_experiences
from .oad_183_crypto_experience_outcome_maturity_gate import select_mature_crypto_experiences,DEFAULT_HORIZON_SECONDS
from .oad_184_crypto_coinbase_future_outcome_observation import acquire_crypto_future_outcomes
from .oad_185_crypto_verified_learning_event_activation import activate_verified_crypto_learning_event

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class CryptoOutcomeLearningPhysicalCertification:
    persisted_experiences:int
    mature_experiences:int
    outcomes:int
    verified_learning_events:int
    intake_ready:int
    assets:tuple
    horizon_seconds:int
    physical_ready:bool
    certified_at:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def _candidate_from_record(r):
    return SimpleNamespace(
        experience_id=r.experience_id,asset=r.asset,snapshot_at=r.snapshot_at,cohort_state=r.cohort_state,
        condition_vector=r.condition_vector,temporal_vector=r.temporal_vector,evidence_hash=r.evidence_hash,
        condition_hash=r.condition_hash,experience_hash=r.experience_hash,outcome_attached=False,
        probability=None,direction=None,execution_authority=False
    )

def _lineage_from_record(r):
    return SimpleNamespace(experience_id=r.experience_id,lineage_hash=r.lineage_hash)

def run_crypto_outcome_learning_activation_physical_certification(
    root=None,timeout_seconds=20.0,horizon_seconds=DEFAULT_HORIZON_SECONDS,per_asset_limit=256
):
    readback=read_persisted_crypto_experiences(root=root,per_asset_limit=per_asset_limit)
    mature=select_mature_crypto_experiences(
        readback.records,horizon_seconds=horizon_seconds,now=datetime.now(timezone.utc),latest_per_asset=True
    )
    if not mature:
        raise RuntimeError(
            f"no crypto experience has reached the real {int(horizon_seconds)}s outcome horizon; "
            f"persisted_experiences={readback.experiences}"
        )
    outcomes=acquire_crypto_future_outcomes(mature,timeout_seconds)
    activations=[]
    by_exp={x.experience.experience_id:x for x in mature}
    for outcome in outcomes:
        rec=by_exp[outcome.experience_id].experience
        activations.append(
            activate_verified_crypto_learning_event(_candidate_from_record(rec),_lineage_from_record(rec),outcome)
        )
    activations=tuple(activations)
    assets=tuple(sorted(x.asset for x in activations))
    ready=bool(
        readback.experiences>0 and len(mature)>0 and len(outcomes)==len(mature)
        and len(activations)==len(mature) and all(x.intake_ready for x in activations)
    )
    if not ready:
        raise RuntimeError(
            f"crypto outcome learning activation failed; persisted={readback.experiences}; "
            f"mature={len(mature)}; outcomes={len(outcomes)}; activations={len(activations)}"
        )
    return CryptoOutcomeLearningPhysicalCertification(
        readback.experiences,len(mature),len(outcomes),len(activations),
        sum(x.intake_ready for x in activations),assets,int(horizon_seconds),True,
        datetime.now(timezone.utc).isoformat(),False,False,False
    )
