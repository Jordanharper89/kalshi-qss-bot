from dataclasses import dataclass
from .ois_049_runtime_status_read_model import OracleRuntimeStatusReadModel

OIS_054_BUILD_ID="OIS-054"
OIS_054_REVISION="OIS_054_ORACLE_RUNTIME_OPERATOR_STATUS_BOUNDARY_V1"

@dataclass(frozen=True)
class OperatorRuntimeStatus:
    runtime_state:str
    health:str
    services_ready:str
    max_lag_seconds:float
    adapter_count:int
    read_model_generation:int
    read_only:bool=True

def project_operator_runtime_status(status):
    if not isinstance(status,OracleRuntimeStatusReadModel):
        raise ValueError("certified runtime status read model required")
    services=f"{status.healthy_required_services}/{status.required_services}"
    return OperatorRuntimeStatus(
        status.runtime_state,
        status.aggregate_health,
        services,
        status.max_lag_seconds,
        status.adapter_count,
        status.read_model_generation,
        True,
    )

def verify_ois_054_oracle_runtime_operator_status_boundary():
    from .ois_046_runtime_state import build_oracle_live_runtime_state
    from .ois_048_service_health_aggregation import build_runtime_service_health,aggregate_runtime_health
    from .ois_049_runtime_status_read_model import build_runtime_status_read_model
    r=build_oracle_live_runtime_state("RUNNING",1,True,True)
    h=aggregate_runtime_health((build_runtime_service_health("ois",True,True,.1),))
    s=build_runtime_status_read_model(r,h,0,5)
    p=project_operator_runtime_status(s)
    return p.read_only and p.runtime_state=="RUNNING" and p.services_ready=="1/1"
