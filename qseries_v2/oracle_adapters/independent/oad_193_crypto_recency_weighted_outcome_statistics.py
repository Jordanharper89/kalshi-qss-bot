from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from math import exp,log
from .oad_190_crypto_comparable_condition_outcome_statistics import condition_signature

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
DEFAULT_HALF_LIFE_SECONDS=7*24*60*60

def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def _weight(age_seconds,half_life_seconds):
    return exp(-log(2.0)*max(0.0,float(age_seconds))/float(half_life_seconds))

@dataclass(frozen=True,slots=True)
class RecencyWeightedOutcomeStats:
    asset:str
    horizon_seconds:int
    condition_signature:tuple
    raw_sample_size:int
    total_weight:float
    effective_sample_size:float
    weighted_positive_share:float
    weighted_negative_share:float
    weighted_unchanged_share:float
    weighted_mean_return_percent:float
    half_life_seconds:int
    reference_time:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def build_recency_weighted_outcome_statistics(
    cases,
    reference_time=None,
    half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS,
    unchanged_epsilon_percent:float=0.000001,
):
    if int(half_life_seconds)<=0: raise ValueError("half_life_seconds must be > 0")
    ref=_dt(reference_time or datetime.now(timezone.utc))
    groups={}
    for c in tuple(cases):
        groups.setdefault((c.asset,int(c.horizon_seconds),condition_signature(c)),[]).append(c)
    out=[]
    for (asset,horizon,sig),rows in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],str(x[0][2]))):
        weighted=[]
        for c in rows:
            age=(ref-_dt(c.outcome_observed_at)).total_seconds()
            w=_weight(age,half_life_seconds)
            weighted.append((c,w))
        sw=sum(w for _,w in weighted)
        sw2=sum(w*w for _,w in weighted)
        if sw<=0: raise RuntimeError("recency weighting produced zero total weight")
        pos=sum(w for c,w in weighted if float(c.return_percent)>unchanged_epsilon_percent)
        neg=sum(w for c,w in weighted if float(c.return_percent)<-unchanged_epsilon_percent)
        un=sw-pos-neg
        mean_ret=sum(float(c.return_percent)*w for c,w in weighted)/sw
        ess=(sw*sw/sw2) if sw2>0 else 0.0
        out.append(RecencyWeightedOutcomeStats(
            asset,horizon,sig,len(rows),sw,ess,pos/sw,neg/sw,un/sw,mean_ret,
            int(half_life_seconds),ref.isoformat(),False,False,False
        ))
    return tuple(out)
