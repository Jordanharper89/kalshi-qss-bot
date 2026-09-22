from dataclasses import dataclass
from .ois_046_runtime_state import OracleLiveRuntimeState,build_oracle_live_runtime_state

OIS_047_BUILD_ID="OIS-047"
OIS_047_REVISION="OIS_047_ORACLE_LIVE_RUNTIME_ACTIVATION_CONTROLLER_V1"

@dataclass(frozen=True)
class RuntimeActivationDecision:
    previous_state:str
    next_state:str
    permitted:bool
    reason:str

_ALLOWED={
    "STOPPED":("STARTING",),
    "STARTING":("RUNNING","DEGRADED","STOPPED"),
    "RUNNING":("DEGRADED","RECOVERING","STOPPED"),
    "DEGRADED":("RUNNING","RECOVERING","STOPPED"),
    "RECOVERING":("RUNNING","DEGRADED","STOPPED"),
}

def evaluate_runtime_transition(current,next_state):
    if not isinstance(current,OracleLiveRuntimeState):
        raise ValueError("certified runtime state required")
    permitted=next_state in _ALLOWED.get(current.state,())
    return RuntimeActivationDecision(current.state,next_state,permitted,"allowed" if permitted else "invalid_transition")

def transition_runtime(current,next_state,accepting_intelligence,serving_read_models):
    d=evaluate_runtime_transition(current,next_state)
    if not d.permitted:
        raise ValueError("runtime transition not permitted")
    return build_oracle_live_runtime_state(next_state,current.sequence+1,accepting_intelligence,serving_read_models)

def verify_ois_047_oracle_live_runtime_activation_controller():
    s=build_oracle_live_runtime_state("STOPPED",0,False,False)
    a=transition_runtime(s,"STARTING",False,False)
    r=transition_runtime(a,"RUNNING",True,True)
    return r.state=="RUNNING" and r.sequence==2 and r.accepting_intelligence
