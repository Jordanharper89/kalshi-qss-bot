from __future__ import annotations
from dataclasses import dataclass
from typing import Any

OLR_021_BUILD_ID="OLR-021"
OLR_021_REVISION="OLR_021_PRE_SETTLEMENT_PROBABILITY_RECOVERY_V1"

PROBABILITY_KEYS=(
    "probability","yes_probability","market_probability",
    "yes_price","last_price","price","yes_bid","yes_ask"
)

@dataclass(frozen=True)
class ProbabilityRecovery:
    probability:float|None
    source_key:str
    raw_value:object
    recovered:bool
    abstain_reason:str

def _normalize_probability(value:Any):
    try:
        x=float(value)
    except Exception:
        return None
    if 0.0 <= x <= 1.0:
        return x
    if 1.0 < x <= 100.0:
        return x/100.0
    return None

def _walk(obj,prefix=""):
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=f"{prefix}.{k}" if prefix else str(k)
            yield key,k,v
            yield from _walk(v,key)
    elif isinstance(obj,(list,tuple)):
        for i,v in enumerate(obj):
            key=f"{prefix}[{i}]"
            yield from _walk(v,key)

def recover_pre_settlement_probability(observation:dict):
    candidates=[]
    for path,key,value in _walk(observation):
        lk=str(key).lower()
        if lk in PROBABILITY_KEYS:
            p=_normalize_probability(value)
            if p is not None:
                candidates.append((path,lk,p,value))
    if not candidates:
        return ProbabilityRecovery(None,"",None,False,"no_defensible_probability_field")
    # Prefer explicit probability fields, then yes_price/last_price, then bid/ask.
    rank={k:i for i,k in enumerate(PROBABILITY_KEYS)}
    candidates.sort(key=lambda x:(rank.get(x[1],999),x[0]))
    path,_,p,raw=candidates[0]
    return ProbabilityRecovery(p,path,raw,True,"")

def verify_olr_021_pre_settlement_probability_recovery():
    a=recover_pre_settlement_probability({"payload":{"yes_price":63}})
    b=recover_pre_settlement_probability({"payload":{"foo":"bar"}})
    return a.recovered and abs(a.probability-.63)<1e-12 and not b.recovered
