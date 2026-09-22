from __future__ import annotations
from dataclasses import dataclass
from math import log

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def normalized_entropy(shares):
    xs=[max(0.0,float(x)) for x in shares]
    total=sum(xs)
    if total<=0: return 1.0
    ps=[x/total for x in xs if x>0]
    if len(ps)<=1: return 0.0
    h=-sum(p*log(p) for p in ps)
    return h/log(3.0)

def contradiction_ratio(positive_share,negative_share):
    p=max(0.0,float(positive_share)); n=max(0.0,float(negative_share))
    d=p+n
    return (2.0*min(p,n)/d) if d>0 else 0.0

@dataclass(frozen=True,slots=True)
class HistoricalOutcomeUncertainty:
    asset:str
    horizon_seconds:int
    raw_sample_size:int
    effective_sample_size:float
    positive_share:float
    negative_share:float
    unchanged_share:float
    contradiction_ratio:float
    normalized_outcome_entropy:float
    contradiction_state:str
    evidence_state:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def build_historical_outcome_uncertainty(recency_stats):
    out=[]
    for s in tuple(recency_stats):
        cr=contradiction_ratio(s.weighted_positive_share,s.weighted_negative_share)
        ent=normalized_entropy((s.weighted_positive_share,s.weighted_negative_share,s.weighted_unchanged_share))
        if cr>=0.66: cs="HIGH_CONTRADICTION"
        elif cr>=0.33: cs="MODERATE_CONTRADICTION"
        else: cs="LOW_CONTRADICTION"
        ess=float(s.effective_sample_size)
        if ess<5: ev="INSUFFICIENT_EFFECTIVE_SAMPLE"
        elif ent>=0.75: ev="HIGH_OUTCOME_UNCERTAINTY"
        elif ent>=0.40: ev="MIXED_OUTCOME_HISTORY"
        else: ev="CONCENTRATED_OUTCOME_HISTORY"
        out.append(HistoricalOutcomeUncertainty(
            s.asset,int(s.horizon_seconds),int(s.raw_sample_size),ess,
            float(s.weighted_positive_share),float(s.weighted_negative_share),float(s.weighted_unchanged_share),
            cr,ent,cs,ev,False,False,False
        ))
    return tuple(out)
