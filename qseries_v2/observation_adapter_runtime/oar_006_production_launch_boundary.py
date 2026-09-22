from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from qseries_v2.observation_adapters.oad_006_default_adapter_bundle import CertifiedDefaultAdapterBundle
from .oar_001_runtime_foundation import LiveObservationRuntimeConfig, initial_runtime_state
from .oar_004_continuous_service_loop import ContinuousObservationServiceLoop, ContinuousServiceLoopResult
from .oar_005_runtime_lifecycle import LiveObservationRuntimeLifecycle

BUILD_ID='OAR-006'
OAR_006_REVISION='OAR_006_PRODUCTION_LAUNCH_BOUNDARY_V1'
READ_ONLY=True
EXECUTION_ALLOWED=False
ORDER_PLACEMENT_ALLOWED=False
PUBLICATION_ALLOWED=False

@dataclass(frozen=True, slots=True)
class ProductionLaunchRecord:
    runtime_id:str
    adapter_ids:tuple[str,...]
    provider_ids:tuple[str,...]
    iterations_completed:int
    stopped:bool
    read_only:bool
    execution_allowed:bool
    order_placement_allowed:bool
    publication_allowed:bool

class ProductionLiveObservationLauncher:
    read_only=True
    execution_allowed=False
    order_placement_allowed=False
    publication_allowed=False
    def launch(self,*,config:LiveObservationRuntimeConfig,bundle:CertifiedDefaultAdapterBundle,iterations:int,clock_callable:Callable[[],datetime],sleep_callable:Callable[[float],None],stop_requested_callable:Callable[[],bool],subject_hints:dict[str,str|None]|None=None)->tuple[ProductionLaunchRecord,ContinuousServiceLoopResult]:
        if config.read_only is not True or config.execution_allowed is not False: raise ValueError('unsafe runtime config')
        if bundle.read_only is not True or bundle.execution_allowed is not False: raise ValueError('unsafe adapter bundle')
        state=initial_runtime_state(config)
        state,_=LiveObservationRuntimeLifecycle().start(config=config,state=state,occurred_at=clock_callable())
        result=ContinuousObservationServiceLoop().run(config=config,bundle=bundle,iterations=iterations,clock_callable=clock_callable,sleep_callable=sleep_callable,stop_requested_callable=stop_requested_callable,subject_hints=subject_hints)
        if state.execution_allowed is not False: raise RuntimeError('runtime lifecycle exposed execution')
        record=ProductionLaunchRecord(config.runtime_id,bundle.adapter_ids,bundle.provider_ids,result.iterations_completed,result.stopped,True,False,False,False)
        return record,result

def verify_production_launch_boundary()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and ORDER_PLACEMENT_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
