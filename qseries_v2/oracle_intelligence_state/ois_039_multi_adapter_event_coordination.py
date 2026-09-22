from dataclasses import dataclass
from .ois_031_low_latency_event_intake import CanonicalMarketEvent

OIS_039_BUILD_ID="OIS-039"
OIS_039_REVISION="OIS_039_MULTI_ADAPTER_EVENT_STREAM_COORDINATION_V1"

@dataclass(frozen=True)
class CoordinatedAdapterEvent:
    adapter_id:str
    venue_id:str
    market_id:str
    sequence:int
    oracle_receive_ns:int
    event_hash:str

def coordinate_adapter_events(events):
    rows=tuple(sorted(events,key=lambda x:(x.oracle_receive_ns,x.adapter_id,x.market_id,x.sequence,x.event_hash)))
    seen=set()
    out=[]
    for x in rows:
        if not isinstance(x,CanonicalMarketEvent):
            raise ValueError("canonical market events required")
        key=(x.adapter_id,x.market_id,x.sequence)
        if key in seen:
            raise ValueError("duplicate adapter event sequence")
        seen.add(key)
        out.append(CoordinatedAdapterEvent(x.adapter_id,x.venue_id,x.market_id,x.sequence,x.oracle_receive_ns,x.event_hash))
    return tuple(out)

def verify_ois_039_multi_adapter_event_stream_coordination():
    from .ois_031_low_latency_event_intake import build_canonical_market_event
    a=build_canonical_market_event("kalshi","kalshi_ws","A","trade",1,3,1,"a"*64)
    b=build_canonical_market_event("coinbase","coinbase_ws","BTC-USD","trade",1,2,1,"b"*64)
    c=coordinate_adapter_events((a,b))
    return c[0].adapter_id=="coinbase_ws" and c[1].adapter_id=="kalshi_ws"
