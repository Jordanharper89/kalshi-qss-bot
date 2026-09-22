from dataclasses import dataclass
from .ois_026_universal_surveillance import SURVEILLANCE_TIERS
from .ois_027_full_universe_state import MarketSurveillanceState

OIS_028_BUILD_ID="OIS-028"
OIS_028_REVISION="OIS_028_SURVEILLANCE_TIER_CLASSIFICATION_V1"

@dataclass(frozen=True)
class SurveillanceTierDecision:
    venue_id:str
    market_id:str
    tier:str
    reason:str
    reevaluate_on_event:bool
    max_scheduled_refresh_seconds:float|None

def classify_surveillance_tier(state,near_qseries_threshold=False,catalyst=False,dislocation=False):
    if not isinstance(state,MarketSurveillanceState):
        raise ValueError("certified market surveillance state required")

    if not state.tradable:
        return SurveillanceTierDecision(state.venue_id,state.market_id,"DEAD","not_tradable",False,None)

    if near_qseries_threshold:
        return SurveillanceTierDecision(state.venue_id,state.market_id,"ULTRA_HOT","near_qseries_threshold",True,0.1)

    if catalyst or dislocation or state.activity_score>=.85:
        reason="catalyst" if catalyst else ("dislocation" if dislocation else "high_activity")
        return SurveillanceTierDecision(state.venue_id,state.market_id,"HOT",reason,True,0.25)

    if state.activity_score>=.50 or state.liquidity_score>=.60:
        return SurveillanceTierDecision(state.venue_id,state.market_id,"ACTIVE","active_market",True,1.0)

    if state.activity_score>=.25:
        return SurveillanceTierDecision(state.venue_id,state.market_id,"WARM","moderate_activity",True,5.0)

    if state.liquidity_score>0 or state.activity_score>0:
        return SurveillanceTierDecision(state.venue_id,state.market_id,"COLD","low_activity",True,30.0)

    return SurveillanceTierDecision(state.venue_id,state.market_id,"DORMANT","inactive_open_market",True,120.0)

def verify_ois_028_surveillance_tier_classification():
    from .ois_027_full_universe_state import build_market_surveillance_state
    a=build_market_surveillance_state("kalshi","A","x",True,1,1,.8,.9)
    d=classify_surveillance_tier(a)
    return d.tier=="HOT" and d.reevaluate_on_event and d.tier in SURVEILLANCE_TIERS
