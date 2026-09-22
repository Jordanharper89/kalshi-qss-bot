\

from __future__ import annotations
from dataclasses import dataclass
from math import isfinite
from .oad_374_solana_temporal_case_bridge import SolanaTemporalLearningCase

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaVerifiedForwardOutcome:
    case_id:str
    horizon_seconds:int
    anchor_price:float
    forward_price:float
    return_fraction:float
    outcome:str
    verified:bool
    evidence_source:str
    execution_authority:bool=False

def attribute_verified_forward_outcome(case:SolanaTemporalLearningCase,horizon_seconds,anchor_price,forward_price,evidence_source="SOLANA_CANONICAL_HISTORY"):
    h=int(horizon_seconds)
    if h not in case.horizons_seconds:
        raise ValueError("horizon not present in temporal case")
    a=float(anchor_price); f=float(forward_price)
    if a<=0 or not isfinite(a) or not isfinite(f):
        raise ValueError("invalid price evidence")
    ret=(f-a)/a
    eps=1e-9
    outcome="UP" if ret>eps else ("DOWN" if ret<-eps else "FLAT")
    return SolanaVerifiedForwardOutcome(case.case_id,h,a,f,ret,outcome,True,str(evidence_source),False)

