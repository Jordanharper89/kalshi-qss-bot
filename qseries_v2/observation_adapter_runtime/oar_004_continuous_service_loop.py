from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import CertifiedDefaultAdapterBundle
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig
from .oar_002_adapter_scheduler import DeterministicAdapterScheduler
from .oar_003_multi_adapter_runner import MultiAdapterObservationRunner, MultiAdapterRunResult

BUILD_ID='OAR-004'
OAR_004_REVISION='OAR_004_CONTINUOUS_SERVICE_LOOP_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False
ORDER_PLACEMENT_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ContinuousServiceLoopResult:
    runtime_id:str
    iterations_requested:int
    iterations_completed:int
    run_results:tuple[MultiAdapterRunResult,...]
    stopped:bool
    read_only:bool
    execution_allowed:bool

class ContinuousObservationServiceLoop:
    read_only=True
    execution_allowed=False
    order_placement_allowed=False

    def run(self,*,config:LiveObservationRuntimeConfig,bundle:CertifiedDefaultAdapterBundle,iterations:int,clock_callable:Callable[[],datetime],sleep_callable:Callable[[float],None],stop_requested_callable:Callable[[],bool],subject_hints:dict[str,str|None]|None=None)->ContinuousServiceLoopResult:
        if not isinstance(config,LiveObservationRuntimeConfig): raise TypeError('config must be LiveObservationRuntimeConfig')
        if not isinstance(bundle,CertifiedDefaultAdapterBundle): raise TypeError('bundle must be CertifiedDefaultAdapterBundle')
        if not isinstance(iterations,int) or iterations<1: raise ValueError('iterations must be positive')
        if not callable(clock_callable) or not callable(sleep_callable) or not callable(stop_requested_callable): raise TypeError('runtime callables must be callable')
        scheduler=DeterministicAdapterScheduler(); runner=MultiAdapterObservationRunner(); results=[]; stopped=False
        for n in range(1,iterations+1):
            if stop_requested_callable(): stopped=True; break
            at=clock_callable()
            if not isinstance(at,datetime) or at.tzinfo is None: raise ValueError('clock must return timezone-aware datetime')
            schedule=scheduler.schedule(bundle=bundle,iteration_number=n,scheduled_at=at.astimezone(timezone.utc),subject_hints=subject_hints)
            results.append(runner.run(bundle=bundle,schedule=schedule,clock_callable=clock_callable))
            if n<iterations:
                if stop_requested_callable(): stopped=True; break
                sleep_callable(float(config.tick_interval_seconds))
        return ContinuousServiceLoopResult(config.runtime_id,iterations,len(results),tuple(results),stopped,True,False)

def verify_continuous_service_loop()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and ORDER_PLACEMENT_ALLOWED is False
    return True
