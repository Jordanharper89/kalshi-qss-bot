from __future__ import annotations
from dataclasses import dataclass

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

DEFAULT_PRELIMINARY_MIN=5
DEFAULT_DEVELOPING_MIN=20
DEFAULT_MATURE_MIN=100

@dataclass(frozen=True,slots=True)
class ComparableCaseSufficiency:
    asset:str
    horizon_seconds:int
    condition_signature:tuple
    sample_size:int
    sufficiency_state:str
    threshold_to_next_state:int
    cases_needed_to_next_state:int
    descriptive_statistics_usable:bool
    predictive_probability_eligible:bool=False
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def classify_sample_sufficiency(
    sample_size:int,
    preliminary_min:int=DEFAULT_PRELIMINARY_MIN,
    developing_min:int=DEFAULT_DEVELOPING_MIN,
    mature_min:int=DEFAULT_MATURE_MIN,
):
    n=int(sample_size)
    if n<0: raise ValueError("sample_size must be >= 0")
    a,b,c=int(preliminary_min),int(developing_min),int(mature_min)
    if not (1 <= a < b < c):
        raise ValueError("sufficiency thresholds must satisfy 1 <= preliminary < developing < mature")
    if n<a:
        return "INSUFFICIENT",a,a-n
    if n<b:
        return "PRELIMINARY",b,b-n
    if n<c:
        return "DEVELOPING",c,c-n
    return "MATURE_DESCRIPTIVE",c,0

def assess_comparable_case_sufficiency(
    stats,
    preliminary_min:int=DEFAULT_PRELIMINARY_MIN,
    developing_min:int=DEFAULT_DEVELOPING_MIN,
    mature_min:int=DEFAULT_MATURE_MIN,
):
    out=[]
    for s in tuple(stats):
        state,next_threshold,needed=classify_sample_sufficiency(
            s.sample_size,preliminary_min,developing_min,mature_min
        )
        out.append(ComparableCaseSufficiency(
            s.asset,int(s.horizon_seconds),tuple(s.condition_signature),int(s.sample_size),
            state,next_threshold,needed,bool(s.sample_size>0),
            False,False,False,False
        ))
    return tuple(out)
