from __future__ import annotations
from dataclasses import dataclass
from qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation,verify_market_behavior_observation
from qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import learn_market_behavior
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import evaluate_learning_maturity
from .oad_218_existing_ocl_state_hash_envelope import envelope
from .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SnapshotBehaviorMaturity:
    as_of_sequence:int
    snapshot_hash:str
    learned_cases:int
    behavior_observations:int
    market_behavior_state_hash:str|None
    maturity_state_hash:str
    maturity_band:str
    maturity_score:float
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def materialize_snapshot_behavior_maturity(root=None,per_asset_limit=512):
    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)
    groups={};returns=[];families=set()
    for seq,oid,source,observed,praw in snap.rows:
        p=praw if isinstance(praw,dict) else dict(praw or ())
        asset=str(p.get("asset") or "").upper()
        evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")
        if p.get("return_fraction") is not None:returns.append(float(p["return_fraction"]))
        for row in tuple(p.get("condition_vector") or ()):
            if isinstance(row,(list,tuple)) and row:families.add(str(row[0]))
        if asset and len(evh)==64 and len(outh)==64 and p.get("return_fraction") is not None:
            ts=observed.isoformat() if hasattr(observed,"isoformat") else str(observed)
            o=build_market_behavior_observation(asset,"crypto_realized_return","return_fraction_observed_interval",float(p["return_fraction"]),ts,evh,outh)
            if not verify_market_behavior_observation(o):raise RuntimeError("OCL-011 verification failed")
            groups.setdefault(asset,[]).append(o)
    states=tuple(learn_market_behavior(tuple(groups[a])) for a in sorted(groups)) if groups else ()
    mbh=envelope("market_behavior",states).state_hash if states else None
    if returns:
        pos=sum(x>0 for x in returns);neg=sum(x<0 for x in returns);flat=len(returns)-pos-neg
        consistency=max(pos,neg,flat)/len(returns);contradiction=min(pos,neg)/len(returns)
    else:
        consistency=0.0;contradiction=0.0
    maturity=evaluate_learning_maturity(len(returns),len(families),consistency,contradiction,0.0)
    return SnapshotBehaviorMaturity(snap.as_of_sequence,snap.snapshot_hash,snap.row_count,sum(len(x) for x in groups.values()),mbh,envelope("maturity",maturity).state_hash,maturity.maturity_band,maturity.maturity_score)
