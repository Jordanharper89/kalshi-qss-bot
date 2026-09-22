from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig, LiveObservationRuntimeState, RUNTIME_STATUS_IDLE, RUNTIME_STATUS_RUNNING, RUNTIME_STATUS_STOPPED

BUILD_ID='OAR-005'
OAR_005_REVISION='OAR_005_RUNTIME_LIFECYCLE_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class RuntimeLifecycleRecord:
    runtime_id:str
    prior_status:str
    new_status:str
    prior_iteration_number:int
    new_iteration_number:int
    occurred_at:datetime
    reason:str
    read_only:bool
    execution_allowed:bool

class LiveObservationRuntimeLifecycle:
    read_only=True
    execution_allowed=False
    def _validate(self,config,state,occurred_at):
        if not isinstance(config,LiveObservationRuntimeConfig): raise TypeError('config must be LiveObservationRuntimeConfig')
        if not isinstance(state,LiveObservationRuntimeState): raise TypeError('state must be LiveObservationRuntimeState')
        if config.runtime_id!=state.runtime_id: raise ValueError('config/state runtime_id mismatch')
        if not isinstance(occurred_at,datetime) or occurred_at.tzinfo is None: raise ValueError('occurred_at must be timezone-aware datetime')
    def _record(self,state,new_state,occurred_at,reason):
        return RuntimeLifecycleRecord(state.runtime_id,state.status,new_state.status,state.iteration_number,new_state.iteration_number,occurred_at.astimezone(timezone.utc),reason,True,False)
    def start(self,*,config,state,occurred_at):
        self._validate(config,state,occurred_at)
        if state.status!=RUNTIME_STATUS_IDLE: raise ValueError('runtime can start only from idle')
        n=LiveObservationRuntimeState(state.runtime_id,RUNTIME_STATUS_RUNNING,state.iteration_number,state.consecutive_failures,False,True,False)
        return n,self._record(state,n,occurred_at,'runtime_started')
    def advance(self,*,config,state,occurred_at,iteration_succeeded:bool):
        self._validate(config,state,occurred_at)
        if state.status!=RUNTIME_STATUS_RUNNING: raise ValueError('runtime can advance only while running')
        failures=0 if iteration_succeeded else state.consecutive_failures+1
        stop=failures>=config.max_adapter_failures
        status=RUNTIME_STATUS_STOPPED if stop else RUNTIME_STATUS_RUNNING
        n=LiveObservationRuntimeState(state.runtime_id,status,state.iteration_number+1,failures,stop,True,False)
        reason='failure_limit_reached' if stop else ('iteration_succeeded' if iteration_succeeded else 'iteration_failed')
        return n,self._record(state,n,occurred_at,reason)
    def stop(self,*,config,state,occurred_at):
        self._validate(config,state,occurred_at)
        if state.status==RUNTIME_STATUS_STOPPED: raise ValueError('runtime is already stopped')
        n=LiveObservationRuntimeState(state.runtime_id,RUNTIME_STATUS_STOPPED,state.iteration_number,state.consecutive_failures,True,True,False)
        return n,self._record(state,n,occurred_at,'operator_stop_requested')

def verify_runtime_lifecycle()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False
    return True
