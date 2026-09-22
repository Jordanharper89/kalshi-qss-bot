from dataclasses import dataclass
from .ois_031_low_latency_event_intake import CanonicalMarketEvent

OIS_033_BUILD_ID="OIS-033"
OIS_033_REVISION="OIS_033_END_TO_END_LATENCY_TELEMETRY_V1"

@dataclass(frozen=True)
class EventLatencyTelemetry:
    venue_to_oracle_ns:int
    oracle_to_shadow_ns:int
    shadow_to_evaluation_ns:int
    evaluation_to_handoff_ns:int
    end_to_end_ns:int

def measure_event_latency(event,shadow_commit_ns,evaluation_ns,handoff_ns):
    if not isinstance(event,CanonicalMarketEvent):
        raise ValueError("canonical event required")
    times=(event.venue_event_ns,event.oracle_receive_ns,int(shadow_commit_ns),int(evaluation_ns),int(handoff_ns))
    if any(b<a for a,b in zip(times,times[1:])):
        raise ValueError("latency timestamps must be monotonic")
    return EventLatencyTelemetry(
        times[1]-times[0],
        times[2]-times[1],
        times[3]-times[2],
        times[4]-times[3],
        times[4]-times[0],
    )

def verify_ois_033_end_to_end_latency_telemetry():
    from .ois_031_low_latency_event_intake import build_canonical_market_event
    e=build_canonical_market_event("k","a","m","trade",100,120,1,"a"*64)
    x=measure_event_latency(e,130,150,170)
    return x.end_to_end_ns==70 and x.venue_to_oracle_ns==20
