from dataclasses import dataclass

OIS_052_BUILD_ID="OIS-052"
OIS_052_REVISION="OIS_052_RUNTIME_STARTUP_DEPENDENCY_READINESS_GATE_V1"

REQUIRED_SERVICES=("live_shadow","postgresql","observation_intelligence","umd","oml","ocl","osr","ois")

@dataclass(frozen=True)
class StartupDependencyState:
    service_id:str
    ready:bool
    certified:bool

@dataclass(frozen=True)
class StartupReadinessDecision:
    required_services:tuple[str,...]
    missing_or_unready:tuple[str,...]
    permitted_to_run:bool

def evaluate_startup_readiness(states):
    rows={x.service_id:x for x in states}
    missing=[]
    for service in REQUIRED_SERVICES:
        x=rows.get(service)
        if x is None or not x.ready or not x.certified:
            missing.append(service)
    return StartupReadinessDecision(REQUIRED_SERVICES,tuple(missing),not missing)

def verify_ois_052_runtime_startup_dependency_readiness_gate():
    states=tuple(StartupDependencyState(x,True,True) for x in REQUIRED_SERVICES)
    d=evaluate_startup_readiness(states)
    return d.permitted_to_run and not d.missing_or_unready and len(d.required_services)==8
