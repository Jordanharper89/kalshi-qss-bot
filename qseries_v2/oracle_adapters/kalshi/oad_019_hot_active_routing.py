from dataclasses import dataclass
from types import MappingProxyType

OAD_019_BUILD_ID="OAD-019"
OAD_019_REVISION="OAD_019_KALSHI_HOT_ACTIVE_SURVEILLANCE_ROUTING_V1"

ROUTING_TIERS=("ULTRA_HOT","HOT","ACTIVE","WARM","COLD","DORMANT","DEAD")

@dataclass(frozen=True)
class KalshiRoutingDecision:
    market_ticker:str
    tier:str
    route:str
    max_scheduled_refresh_seconds:float|None
    event_driven:bool
    reason:str

def route_market(market_ticker,tradable,activity_score,liquidity_score,
                 near_qseries_threshold=False,catalyst=False,dislocation=False):
    if not market_ticker: raise ValueError("market_ticker required")
    a=float(activity_score); l=float(liquidity_score)
    if not 0<=a<=1 or not 0<=l<=1: raise ValueError("normalized scores required")
    if not tradable:
        return KalshiRoutingDecision(market_ticker,"DEAD","ARCHIVE",None,False,"not_tradable")
    if near_qseries_threshold:
        return KalshiRoutingDecision(market_ticker,"ULTRA_HOT","FAST_PATH",0.1,True,"near_qseries_threshold")
    if catalyst or dislocation or a>=.85:
        why="catalyst" if catalyst else ("dislocation" if dislocation else "high_activity")
        return KalshiRoutingDecision(market_ticker,"HOT","FAST_PATH",0.25,True,why)
    if a>=.50 or l>=.60:
        return KalshiRoutingDecision(market_ticker,"ACTIVE","FAST_PATH",1.0,True,"active_market")
    if a>=.25:
        return KalshiRoutingDecision(market_ticker,"WARM","BROAD_SURVEILLANCE",5.0,True,"moderate_activity")
    if a>0 or l>0:
        return KalshiRoutingDecision(market_ticker,"COLD","BROAD_SURVEILLANCE",30.0,True,"low_activity")
    return KalshiRoutingDecision(market_ticker,"DORMANT","BROAD_SURVEILLANCE",120.0,True,"inactive_open_market")

def build_oad_019_certification_manifest():
    return MappingProxyType({"build_id":OAD_019_BUILD_ID,"revision":OAD_019_REVISION,
        "tiers":ROUTING_TIERS,"active_max_refresh_seconds":1.0,"hot_event_driven":True,
        "ultra_hot_event_driven":True,"execution":False})

def verify_oad_019_kalshi_hot_active_surveillance_routing():
    h=route_market("A",True,.9,.5)
    a=route_market("B",True,.6,.7)
    d=route_market("C",False,0,0)
    return h.tier=="HOT" and h.event_driven and a.tier=="ACTIVE" and a.max_scheduled_refresh_seconds==1.0 and d.route=="ARCHIVE"
