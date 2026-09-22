from dataclasses import dataclass
from hashlib import sha256
import json
from .ois_046_runtime_state import OracleLiveRuntimeState
from .ois_048_service_health_aggregation import OracleAggregateHealth

OIS_049_BUILD_ID="OIS-049"
OIS_049_REVISION="OIS_049_ORACLE_RUNTIME_STATUS_READ_MODEL_V1"

@dataclass(frozen=True)
class OracleRuntimeStatusReadModel:
    runtime_state:str
    runtime_sequence:int
    aggregate_health:str
    required_services:int
    healthy_required_services:int
    max_lag_seconds:float
    adapter_count:int
    read_model_generation:int
    status_hash:str
    read_only:bool=True

def build_runtime_status_read_model(runtime_state,aggregate_health,adapter_count,read_model_generation):
    if not isinstance(runtime_state,OracleLiveRuntimeState) or not isinstance(aggregate_health,OracleAggregateHealth):
        raise ValueError("certified runtime state and aggregate health required")
    if int(adapter_count)<0 or int(read_model_generation)<0:
        raise ValueError("non-negative runtime counters required")
    raw={
        "runtime_state":runtime_state.state,
        "runtime_sequence":runtime_state.sequence,
        "aggregate_health":aggregate_health.status,
        "required_services":aggregate_health.required_services,
        "healthy_required_services":aggregate_health.healthy_required_services,
        "max_lag_seconds":aggregate_health.max_lag_seconds,
        "adapter_count":int(adapter_count),
        "read_model_generation":int(read_model_generation),
    }
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return OracleRuntimeStatusReadModel(
        runtime_state.state,runtime_state.sequence,aggregate_health.status,
        aggregate_health.required_services,aggregate_health.healthy_required_services,
        aggregate_health.max_lag_seconds,int(adapter_count),int(read_model_generation),h,True
    )

def verify_ois_049_oracle_runtime_status_read_model():
    from .ois_046_runtime_state import build_oracle_live_runtime_state
    from .ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health
    r=build_oracle_live_runtime_state("RUNNING",2,True,True)
    h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,.1),))
    x=build_runtime_status_read_model(r,h,0,10)
    return x.read_only and x.runtime_state=="RUNNING" and len(x.status_hash)==64
