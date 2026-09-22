from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from math import exp,log

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
DEFAULT_HALF_LIFE_SECONDS=7*24*60*60

def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

def regime_tokens(case):
    tokens=set()
    for x in tuple(case.condition_vector):
        if len(tuple(x))>=4:
            tokens.add(("condition",str(x[0]),str(x[1]),str(x[3])))
    for x in tuple(case.temporal_vector):
        if len(tuple(x))>=6 and bool(tuple(x)[5]):
            tokens.add(("temporal",str(x[0]),str(x[1]),str(x[2])))
    return frozenset(tokens)

def jaccard_similarity(a,b):
    a,b=set(a),set(b)
    if not a and not b: return 1.0
    if not a or not b: return 0.0
    return len(a & b)/len(a | b)

@dataclass(frozen=True,slots=True)
class RegimeWeightedOutcomeProfile:
    asset:str
    horizon_seconds:int
    reference_experience_id:str
    historical_case_count:int
    nonzero_relevance_cases:int
    total_combined_weight:float
    effective_sample_size:float
    weighted_positive_share:float
    weighted_negative_share:float
    weighted_unchanged_share:float
    weighted_mean_return_percent:float
    mean_regime_similarity:float
    half_life_seconds:int
    reference_time:str
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def build_regime_relevance_weighted_profile(
    reference_case,
    historical_cases,
    reference_time=None,
    half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS,
    unchanged_epsilon_percent:float=0.000001,
):
    if int(half_life_seconds)<=0: raise ValueError("half_life_seconds must be > 0")
    ref_time=_dt(reference_time or datetime.now(timezone.utc))
    ref_tokens=regime_tokens(reference_case)
    pool=[c for c in tuple(historical_cases)
          if c.asset==reference_case.asset and int(c.horizon_seconds)==int(reference_case.horizon_seconds)]
    weighted=[]
    sims=[]
    for c in pool:
        sim=jaccard_similarity(ref_tokens,regime_tokens(c))
        age=max(0.0,(ref_time-_dt(c.outcome_observed_at)).total_seconds())
        recency=exp(-log(2.0)*age/float(half_life_seconds))
        w=sim*recency
        sims.append(sim)
        weighted.append((c,w))
    sw=sum(w for _,w in weighted); sw2=sum(w*w for _,w in weighted)
    pos=sum(w for c,w in weighted if float(c.return_percent)>unchanged_epsilon_percent)
    neg=sum(w for c,w in weighted if float(c.return_percent)<-unchanged_epsilon_percent)
    un=sw-pos-neg
    mean_ret=sum(float(c.return_percent)*w for c,w in weighted)/sw if sw>0 else 0.0
    ess=(sw*sw/sw2) if sw2>0 else 0.0
    return RegimeWeightedOutcomeProfile(
        reference_case.asset,int(reference_case.horizon_seconds),reference_case.experience_id,
        len(pool),sum(1 for _,w in weighted if w>0),sw,ess,
        pos/sw if sw>0 else 0.0,neg/sw if sw>0 else 0.0,un/sw if sw>0 else 0.0,
        mean_ret,sum(sims)/len(sims) if sims else 0.0,int(half_life_seconds),ref_time.isoformat(),
        False,False,False
    )

def build_latest_regime_profiles(cases,reference_time=None,half_life_seconds:int=DEFAULT_HALF_LIFE_SECONDS):
    rows=tuple(cases)
    latest={}
    for c in rows:
        key=(c.asset,int(c.horizon_seconds))
        if key not in latest or str(c.outcome_observed_at)>str(latest[key].outcome_observed_at):
            latest[key]=c
    return tuple(build_regime_relevance_weighted_profile(
        latest[k],rows,reference_time,half_life_seconds
    ) for k in sorted(latest))
