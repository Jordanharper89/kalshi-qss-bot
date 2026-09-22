from dataclasses import dataclass
from .ois_046_runtime_state import OracleLiveRuntimeState
from .ois_047_runtime_activation import transition_runtime

OIS_053_BUILD_ID="OIS-053"
OIS_053_REVISION="OIS_053_24X7_RUNTIME_SUPERVISION_AUTOMATIC_RECOVERY_V1"

@dataclass(frozen=True)
class RuntimeSupervisionDecision:
    action:str
    next_state:str
    restart_required:bool
    reason:str

def supervise_runtime(runtime_state,aggregate_healthy,recovery_ready):
    if not isinstance(runtime_state,OracleLiveRuntimeState):
        raise ValueError("certified runtime state required")

    if runtime_state.state=="STOPPED":
        return RuntimeSupervisionDecision("HOLD","STOPPED",False,"stopped")

    if aggregate_healthy:
        if runtime_state.state in ("DEGRADED","RECOVERING","STARTING"):
            return RuntimeSupervisionDecision("PROMOTE_RUNNING","RUNNING",False,"healthy")
        return RuntimeSupervisionDecision("CONTINUE","RUNNING",False,"healthy")

    if recovery_ready:
        return RuntimeSupervisionDecision("ENTER_RECOVERY","RECOVERING",False,"degraded_recoverable")

    return RuntimeSupervisionDecision("RESTART","DEGRADED",True,"recovery_not_ready")

def apply_supervision_decision(runtime_state,decision):
    if decision.next_state==runtime_state.state:
        return runtime_state
    accepting=decision.next_state=="RUNNING"
    serving=decision.next_state in ("RUNNING","DEGRADED","RECOVERING")
    return transition_runtime(runtime_state,decision.next_state,accepting,serving)

def verify_ois_053_24x7_runtime_supervision_automatic_recovery():
    from .ois_046_runtime_state import build_oracle_live_runtime_state
    r=build_oracle_live_runtime_state("RUNNING",5,True,True)
    d=supervise_runtime(r,False,True)
    x=apply_supervision_decision(r,d)
    return d.action=="ENTER_RECOVERY" and x.state=="RECOVERING" and not d.restart_required
