from dataclasses import dataclass
from .ois_028_tier_classification import SurveillanceTierDecision

OIS_034_BUILD_ID="OIS-034"
OIS_034_REVISION="OIS_034_FRESHNESS_STALENESS_ENFORCEMENT_V1"

@dataclass(frozen=True)
class FreshnessDecision:
    tier:str
    age_seconds:float
    max_age_seconds:float|None
    fresh:bool
    stale:bool
    block_handoff:bool

def evaluate_market_freshness(tier_decision,age_seconds):
    if not isinstance(tier_decision,SurveillanceTierDecision):
        raise ValueError("certified tier decision required")
    age=float(age_seconds)
    if age<0:
        raise ValueError("age must be non-negative")
    max_age=tier_decision.max_scheduled_refresh_seconds
    if tier_decision.tier=="DEAD":
        return FreshnessDecision("DEAD",age,None,True,False,True)
    if max_age is None:
        return FreshnessDecision(tier_decision.tier,age,None,True,False,False)
    fresh=age<=max_age
    return FreshnessDecision(tier_decision.tier,age,max_age,fresh,not fresh,not fresh)

def verify_ois_034_freshness_staleness_enforcement():
    d=SurveillanceTierDecision("k","m","ACTIVE","active_market",True,1.0)
    return evaluate_market_freshness(d,.8).fresh and evaluate_market_freshness(d,1.2).block_handoff
