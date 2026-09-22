from dataclasses import dataclass
from hashlib import sha256
import json

OIS_031_BUILD_ID="OIS-031"
OIS_031_REVISION="OIS_031_LOW_LATENCY_CANONICAL_EVENT_INTAKE_V1"

@dataclass(frozen=True)
class CanonicalMarketEvent:
    venue_id:str
    adapter_id:str
    market_id:str
    event_type:str
    venue_event_ns:int
    oracle_receive_ns:int
    sequence:int
    payload_hash:str
    event_hash:str

def build_canonical_market_event(venue_id,adapter_id,market_id,event_type,venue_event_ns,oracle_receive_ns,sequence,payload_hash):
    if not all((venue_id,adapter_id,market_id,event_type)):
        raise ValueError("complete event identity required")
    if venue_event_ns<0 or oracle_receive_ns<0 or sequence<0 or len(payload_hash)!=64:
        raise ValueError("valid timestamps, sequence, and payload hash required")
    if oracle_receive_ns < venue_event_ns:
        raise ValueError("receive time cannot precede venue event time")
    raw={"venue_id":venue_id,"adapter_id":adapter_id,"market_id":market_id,"event_type":event_type,
         "venue_event_ns":int(venue_event_ns),"oracle_receive_ns":int(oracle_receive_ns),
         "sequence":int(sequence),"payload_hash":payload_hash}
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return CanonicalMarketEvent(venue_id,adapter_id,market_id,event_type,int(venue_event_ns),int(oracle_receive_ns),int(sequence),payload_hash,h)

def verify_ois_031_low_latency_canonical_event_intake():
    e=build_canonical_market_event("kalshi","kalshi_ws","m1","trade",100,120,1,"a"*64)
    return e.oracle_receive_ns-e.venue_event_ns==20 and len(e.event_hash)==64
