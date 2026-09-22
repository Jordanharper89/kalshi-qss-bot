from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CryptoHistoricalExperienceCandidate:
    experience_id:str
    asset:str
    snapshot_at:str
    cohort_state:str
    condition_vector:tuple
    temporal_vector:tuple
    evidence_state:str
    consistency_state:str
    market_native_metrics:int
    independent_chain_metrics:int
    comparable_temporal_metrics:int
    evidence_hash:str
    condition_hash:str
    experience_hash:str
    outcome_attached:bool=False
    probability:None=None
    direction:None=None
    execution_authority:bool=False

def build_crypto_historical_experience_candidates(runtime_result):
    changes_by_asset={}
    for x in tuple(runtime_result.changes):
        changes_by_asset.setdefault(str(x.asset),[]).append(x)
    profiles={str(x.asset):x for x in tuple(runtime_result.profiles)}
    out=[]
    for asset in sorted(profiles):
        p=profiles[asset]
        changes=tuple(sorted(changes_by_asset.get(asset,()),key=lambda x:(x.source_family,x.metric_name)))
        cond=tuple((
            str(x.source_family),str(x.metric_name),float(x.current_value),str(x.current_condition)
        ) for x in changes)
        temporal=tuple((
            str(x.source_family),str(x.metric_name),str(x.temporal_state),
            None if x.absolute_change is None else float(x.absolute_change),
            None if x.percent_change is None else float(x.percent_change),
            bool(x.comparable_history_present),
        ) for x in changes)
        evidence_raw={
            "asset":asset,
            "evidence_state":str(p.evidence_state),
            "consistency_state":str(p.consistency_state),
            "market_native_metrics":int(p.market_native_metrics),
            "independent_chain_metrics":int(p.independent_chain_metrics),
        }
        evidence_hash=_h(evidence_raw)
        condition_hash=_h({"condition_vector":cond,"temporal_vector":temporal})
        raw={
            "asset":asset,"snapshot_at":str(runtime_result.snapshot_at),
            "cohort_state":str(runtime_result.cohort_state),
            "evidence_hash":evidence_hash,"condition_hash":condition_hash,
            "outcome_attached":False,"probability":None,"direction":None,
        }
        experience_hash=_h(raw)
        experience_id=f"crypto-exp:{asset}:{experience_hash[:24]}"
        out.append(CryptoHistoricalExperienceCandidate(
            experience_id,asset,str(runtime_result.snapshot_at),str(runtime_result.cohort_state),
            cond,temporal,str(p.evidence_state),str(p.consistency_state),
            int(p.market_native_metrics),int(p.independent_chain_metrics),
            sum(1 for x in changes if x.comparable_history_present),
            evidence_hash,condition_hash,experience_hash,False,None,None,False
        ))
    return tuple(out)

def verify_crypto_historical_experience_candidate(x):
    if x.outcome_attached or x.probability is not None or x.direction is not None or x.execution_authority:
        return False
    evidence_hash=_h({
        "asset":x.asset,"evidence_state":x.evidence_state,"consistency_state":x.consistency_state,
        "market_native_metrics":x.market_native_metrics,"independent_chain_metrics":x.independent_chain_metrics,
    })
    condition_hash=_h({"condition_vector":x.condition_vector,"temporal_vector":x.temporal_vector})
    experience_hash=_h({
        "asset":x.asset,"snapshot_at":x.snapshot_at,"cohort_state":x.cohort_state,
        "evidence_hash":evidence_hash,"condition_hash":condition_hash,
        "outcome_attached":False,"probability":None,"direction":None,
    })
    return x.evidence_hash==evidence_hash and x.condition_hash==condition_hash and x.experience_hash==experience_hash
