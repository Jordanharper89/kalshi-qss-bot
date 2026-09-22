from dataclasses import dataclass

OIS_048_BUILD_ID="OIS-048"
OIS_048_REVISION="OIS_048_RUNTIME_SERVICE_REGISTRY_HEALTH_AGGREGATION_V1"

@dataclass(frozen=True)
class RuntimeServiceHealth:
    service_id:str
    required:bool
    healthy:bool
    lag_seconds:float
    status:str

@dataclass(frozen=True)
class OracleAggregateHealth:
    required_services:int
    healthy_required_services:int
    degraded_services:tuple[str,...]
    max_lag_seconds:float
    status:str

def build_runtime_service_health(service_id,required,healthy,lag_seconds,status=None):
    lag=float(lag_seconds)
    if not service_id or lag<0:
        raise ValueError("valid service health required")
    st=status or ("HEALTHY" if healthy else "DEGRADED")
    return RuntimeServiceHealth(service_id,bool(required),bool(healthy),lag,st)

def aggregate_runtime_health(services,max_allowed_lag_seconds=30.0):
    rows=tuple(sorted(services,key=lambda x:x.service_id))
    if not rows:
        raise ValueError("runtime services required")
    required=tuple(x for x in rows if x.required)
    healthy=sum(1 for x in required if x.healthy and x.lag_seconds<=max_allowed_lag_seconds)
    degraded=tuple(x.service_id for x in rows if (not x.healthy or x.lag_seconds>max_allowed_lag_seconds))
    max_lag=max(x.lag_seconds for x in rows)
    status="HEALTHY" if healthy==len(required) else "DEGRADED"
    return OracleAggregateHealth(len(required),healthy,degraded,max_lag,status)

def verify_ois_048_runtime_service_registry_health_aggregation():
    services=(
        build_runtime_service_health("live_shadow",True,True,.1),
        build_runtime_service_health("postgresql",True,True,.1),
        build_runtime_service_health("oi",True,True,.2),
        build_runtime_service_health("umd",True,True,.2),
        build_runtime_service_health("oml",True,True,.2),
        build_runtime_service_health("ocl",True,True,.3),
        build_runtime_service_health("osr",True,True,.3),
        build_runtime_service_health("ois",True,True,.1),
    )
    x=aggregate_runtime_health(services)
    return x.status=="HEALTHY" and x.required_services==8 and not x.degraded_services
