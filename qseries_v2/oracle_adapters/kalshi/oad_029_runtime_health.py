from dataclasses import dataclass
from types import MappingProxyType

OAD_029_BUILD_ID="OAD-029"
OAD_029_REVISION="OAD_029_ORACLE_RUNTIME_ADAPTER_HEALTH_LATENCY_SUPERVISION_V1"

@dataclass(frozen=True)
class KalshiRuntimeHealth:
    connected:bool
    subscribed:bool
    live_event_age_ms:float
    p95_latency_ms:float
    persistence_ready:bool
    status:str

def evaluate_runtime_health(connected,subscribed,live_event_age_ms,p95_latency_ms,persistence_ready,
                            max_event_age_ms=1000.0,max_p95_latency_ms=250.0):
    age=float(live_event_age_ms); p95=float(p95_latency_ms)
    if age<0 or p95<0: raise ValueError("non-negative health metrics required")
    if not connected: status="DOWN"
    elif not subscribed: status="DEGRADED"
    elif not persistence_ready: status="PERSISTENCE_BLOCKED"
    elif age>max_event_age_ms: status="STALE"
    elif p95>max_p95_latency_ms: status="LAGGING"
    else: status="LIVE_READY"
    return KalshiRuntimeHealth(bool(connected),bool(subscribed),age,p95,bool(persistence_ready),status)

def verify_oad_029_oracle_runtime_adapter_health_latency_supervision():
    x=evaluate_runtime_health(True,True,50,25,True)
    return x.status=="LIVE_READY"
