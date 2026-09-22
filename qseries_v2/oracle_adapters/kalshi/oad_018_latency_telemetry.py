from dataclasses import dataclass
from statistics import median
from types import MappingProxyType
from .oad_013_market_data_normalization import NormalizedKalshiMarketData

OAD_018_BUILD_ID="OAD-018"
OAD_018_REVISION="OAD_018_KALSHI_END_TO_END_LATENCY_TELEMETRY_V1"

@dataclass(frozen=True)
class KalshiLatencySample:
    source_to_oracle_ms:float
    oracle_to_shadow_ms:float
    shadow_to_routing_ms:float
    end_to_end_ms:float

@dataclass(frozen=True)
class KalshiLatencySummary:
    count:int
    p50_ms:float
    p95_ms:float
    max_ms:float

def build_latency_sample(source_event_ns,oracle_receive_ns,shadow_commit_ns,routing_ns):
    times=tuple(int(x) for x in (source_event_ns,oracle_receive_ns,shadow_commit_ns,routing_ns))
    if any(x<0 for x in times) or any(b<a for a,b in zip(times,times[1:])):
        raise ValueError("monotonic non-negative latency timestamps required")
    a=(times[1]-times[0])/1_000_000
    b=(times[2]-times[1])/1_000_000
    c=(times[3]-times[2])/1_000_000
    return KalshiLatencySample(a,b,c,(times[3]-times[0])/1_000_000)

def summarize_latency(samples):
    xs=sorted(float(x.end_to_end_ms) for x in samples)
    if not xs: raise ValueError("latency samples required")
    idx=max(0,min(len(xs)-1,int(round(0.95*(len(xs)-1)))))
    return KalshiLatencySummary(len(xs),float(median(xs)),xs[idx],xs[-1])

def build_oad_018_certification_manifest():
    return MappingProxyType({"build_id":OAD_018_BUILD_ID,"revision":OAD_018_REVISION,
        "segments":("source_to_oracle","oracle_to_shadow","shadow_to_routing"),"p95":True,"execution":False})

def verify_oad_018_kalshi_end_to_end_latency_telemetry():
    s1=build_latency_sample(0,10_000_000,20_000_000,30_000_000)
    s2=build_latency_sample(0,20_000_000,30_000_000,40_000_000)
    x=summarize_latency((s1,s2))
    return s1.end_to_end_ms==30.0 and x.count==2 and x.max_ms==40.0
