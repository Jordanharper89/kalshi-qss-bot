from dataclasses import dataclass

OIS_046_BUILD_ID="OIS-046"
OIS_046_REVISION="OIS_046_ORACLE_LIVE_RUNTIME_STATE_MODEL_V1"

RUNTIME_STATES=("STARTING","RUNNING","DEGRADED","RECOVERING","STOPPED")

@dataclass(frozen=True)
class OracleLiveRuntimeState:
    state:str
    sequence:int
    active:bool
    accepting_intelligence:bool
    serving_read_models:bool
    terminal_dependency:bool=False
    execution_authority:bool=False

def build_oracle_live_runtime_state(state,sequence,accepting_intelligence,serving_read_models):
    if state not in RUNTIME_STATES or int(sequence)<0:
        raise ValueError("valid Oracle runtime state and sequence required")
    active=state in ("STARTING","RUNNING","DEGRADED","RECOVERING")
    return OracleLiveRuntimeState(
        state,int(sequence),active,bool(accepting_intelligence),bool(serving_read_models),False,False
    )

def verify_ois_046_oracle_live_runtime_state_model():
    x=build_oracle_live_runtime_state("RUNNING",1,True,True)
    return x.active and not x.terminal_dependency and not x.execution_authority and x.state=="RUNNING"
