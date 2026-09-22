from dataclasses import dataclass
from hashlib import sha256
import json

OIS_027_BUILD_ID="OIS-027"
OIS_027_REVISION="OIS_027_FULL_UNIVERSE_MARKET_STATE_V1"

@dataclass(frozen=True)
class MarketSurveillanceState:
    venue_id:str
    market_id:str
    category:str
    tradable:bool
    last_event_ns:int
    last_trade_ns:int
    liquidity_score:float
    activity_score:float
    state_hash:str

def build_market_surveillance_state(venue_id,market_id,category,tradable,last_event_ns,last_trade_ns,liquidity_score,activity_score):
    if not venue_id or not market_id or not category:
        raise ValueError("market identity required")
    if last_event_ns<0 or last_trade_ns<0:
        raise ValueError("timestamps must be non-negative")
    if any(not 0<=v<=1 for v in (liquidity_score,activity_score)):
        raise ValueError("normalized market scores required")
    raw={
        "venue_id":venue_id,"market_id":market_id,"category":category,"tradable":bool(tradable),
        "last_event_ns":int(last_event_ns),"last_trade_ns":int(last_trade_ns),
        "liquidity_score":float(liquidity_score),"activity_score":float(activity_score)
    }
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return MarketSurveillanceState(
        venue_id,market_id,category,bool(tradable),int(last_event_ns),int(last_trade_ns),
        float(liquidity_score),float(activity_score),h
    )

def build_full_universe_state(states):
    rows=tuple(sorted(states,key=lambda x:(x.venue_id,x.market_id)))
    if not rows:
        raise ValueError("market universe required")
    ids=[(x.venue_id,x.market_id) for x in rows]
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate market identity")
    return rows

def verify_ois_027_full_universe_market_state():
    a=build_market_surveillance_state("kalshi","A","econ",True,1,1,.5,.8)
    b=build_market_surveillance_state("kalshi","B","weather",False,2,0,0,0)
    u=build_full_universe_state((b,a))
    return len(u)==2 and u[0].market_id=="A" and len(u[0].state_hash)==64
