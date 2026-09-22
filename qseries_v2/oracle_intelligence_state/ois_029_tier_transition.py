from dataclasses import dataclass
from .ois_028_tier_classification import SurveillanceTierDecision

OIS_029_BUILD_ID="OIS-029"
OIS_029_REVISION="OIS_029_SURVEILLANCE_PROMOTION_DEMOTION_ENGINE_V1"

TIER_ORDER=("DEAD","DORMANT","COLD","WARM","ACTIVE","HOT","ULTRA_HOT")

@dataclass(frozen=True)
class TierTransition:
    venue_id:str
    market_id:str
    previous_tier:str
    next_tier:str
    direction:str
    reason:str

def transition_surveillance_tier(previous_tier,next_decision):
    if previous_tier not in TIER_ORDER or not isinstance(next_decision,SurveillanceTierDecision):
        raise ValueError("valid tier transition required")
    p=TIER_ORDER.index(previous_tier)
    n=TIER_ORDER.index(next_decision.tier)
    direction="PROMOTE" if n>p else ("DEMOTE" if n<p else "HOLD")
    return TierTransition(
        next_decision.venue_id,next_decision.market_id,previous_tier,next_decision.tier,direction,next_decision.reason
    )

def should_interrupt_schedule(transition):
    return transition.direction=="PROMOTE" and transition.next_tier in ("HOT","ULTRA_HOT")

def verify_ois_029_surveillance_promotion_demotion_engine():
    d=SurveillanceTierDecision("kalshi","A","HOT","dislocation",True,.25)
    t=transition_surveillance_tier("ACTIVE",d)
    return t.direction=="PROMOTE" and should_interrupt_schedule(t)
