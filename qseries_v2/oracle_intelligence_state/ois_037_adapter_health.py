from dataclasses import dataclass
from .ois_036_adapter_registry import AdapterRegistration

OIS_037_BUILD_ID="OIS-037"
OIS_037_REVISION="OIS_037_ADAPTER_READINESS_HEALTH_V1"

@dataclass(frozen=True)
class AdapterHealth:
    adapter_id:str
    connected:bool
    universe_ready:bool
    event_stream_ready:bool
    lag_seconds:float
    status:str

def evaluate_adapter_health(registration,connected,universe_ready,event_stream_ready,lag_seconds,max_lag_seconds=5.0):
    if not isinstance(registration,AdapterRegistration):
        raise ValueError("registered adapter required")
    lag=float(lag_seconds)
    if lag<0:
        raise ValueError("lag must be non-negative")
    if not registration.enabled:
        status="DISABLED"
    elif not connected:
        status="DOWN"
    elif registration.supports_full_universe and not universe_ready:
        status="DEGRADED"
    elif registration.supports_event_stream and not event_stream_ready:
        status="DEGRADED"
    elif lag>max_lag_seconds:
        status="LAGGING"
    else:
        status="READY"
    return AdapterHealth(registration.adapter_id,bool(connected),bool(universe_ready),bool(event_stream_ready),lag,status)

def verify_ois_037_adapter_readiness_health():
    from .ois_036_adapter_registry import register_adapter
    a=register_adapter("kalshi_universal","kalshi")
    return evaluate_adapter_health(a,True,True,True,1.0).status=="READY"
