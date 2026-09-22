from __future__ import annotations
from dataclasses import dataclass
from .olr_016_production_learned_state_adapter import ProductionLearnedStateSnapshot

OLR_017_BUILD_ID="OLR-017"
OLR_017_REVISION="OLR_017_MARKET_FEEDBACK_RESOLVER_V1"

@dataclass(frozen=True)
class MarketFeedbackResolution:
    market_ticker:str
    learned_records:int
    total_learned_records:int
    experience_weight:float
    eligible:bool
    directional_signal_available:bool=False
    execution_authority:bool=False

def resolve_market_feedback(snapshot:ProductionLearnedStateSnapshot,market_ticker:str,min_records=1):
    counts=dict(snapshot.learned_market_counts)
    count=int(counts.get(str(market_ticker),0))
    weight=min(1.0,count/25.0)
    return MarketFeedbackResolution(
        str(market_ticker),count,snapshot.learned_records,weight,
        count>=int(min_records),False,False
    )

def verify_olr_017_market_feedback_resolver():
    s=ProductionLearnedStateSnapshot("s","l",1,2,2,"h",2,2,(("KX",2),),True)
    x=resolve_market_feedback(s,"KX")
    return x.eligible and not x.directional_signal_available and not x.execution_authority
