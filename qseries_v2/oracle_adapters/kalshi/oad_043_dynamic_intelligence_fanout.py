from dataclasses import dataclass
OAD_043_BUILD_ID="OAD-043"
OAD_043_REVISION="OAD_043_DYNAMIC_SURVEILLANCE_FANOUT_V1"

@dataclass(frozen=True)
class IntelligenceFanoutDecision:
    market_ticker:str
    surveillance_tier:str
    acquisition_lane:str
    intelligence_lane:str
    priority:int

def route_intelligence_fanout(market_ticker,surveillance_tier):
    tier=str(surveillance_tier).upper()
    mapping={
        "ULTRA_HOT":("FAST_PATH","IMMEDIATE",100),
        "HOT":("FAST_PATH","IMMEDIATE",90),
        "ACTIVE":("FAST_PATH","STANDARD",70),
        "WARM":("BROAD_SURVEILLANCE","BACKGROUND",40),
        "COLD":("BROAD_SURVEILLANCE","BACKGROUND",20),
        "DORMANT":("BROAD_SURVEILLANCE","BACKGROUND",10),
        "DEAD":("ARCHIVE","ARCHIVE",0),
    }
    if tier not in mapping:
        raise ValueError("unknown surveillance tier")
    acquisition,intelligence,priority=mapping[tier]
    return IntelligenceFanoutDecision(str(market_ticker),tier,acquisition,intelligence,priority)

def verify_oad_043_dynamic_surveillance_fanout():
    return route_intelligence_fanout("A","HOT").priority==90 and route_intelligence_fanout("B","DEAD").priority==0
