from dataclasses import dataclass

OIS_024_BUILD_ID="OIS-024"
OIS_024_REVISION="OIS_024_24X7_SERVICE_ACTIVATION_HEALTH_BOUNDARY_V1"

@dataclass(frozen=True)
class OracleServiceState:
    active:bool
    healthy:bool
    lag_seconds:float
    restart_required:bool
    terminal_dependency:bool=False

def evaluate_oracle_service(active,db_ok,pipeline_ok,recovery_ok,lag_seconds,max_lag_seconds=30.0):
    lag=float(lag_seconds)
    if lag<0: raise ValueError("lag must be non-negative")
    healthy=bool(active and db_ok and pipeline_ok and recovery_ok and lag<=max_lag_seconds)
    restart=bool(active and (not db_ok or not pipeline_ok or not recovery_ok))
    return OracleServiceState(bool(active),healthy,lag,restart,False)

def verify_ois_024_24x7_service_activation_health_boundary():
    h=evaluate_oracle_service(True,True,True,True,1.0)
    d=evaluate_oracle_service(True,False,True,True,1.0)
    return h.healthy and not h.terminal_dependency and d.restart_required
