from __future__ import annotations
from dataclasses import dataclass
import inspect
from .oad_386_solana_ocl026_runtime_admission import build_ocl026_solana_runtime_batch
from .oad_389_solana_production_learning_runner_resolution import resolve_production_learning_runner
from .oad_390_solana_production_learner_state_baseline import capture_learner_state_baseline

READ_ONLY=True
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ProductionLearnerAdmissionContract:
    runtime_inputs:int
    runner_path:str
    runner_callables:tuple
    durable_counter_count:int
    ready:bool
    execution_authority:bool=False

def build_production_learner_admission_contract(root=None):
    admission,rows,batch=build_ocl026_solana_runtime_batch(root=root,sequence_start=1)
    runner=resolve_production_learning_runner(root)
    state=capture_learner_state_baseline(root)
    ready=admission.runtime_inputs>0 and runner.resolved and len(state.counters)>0
    return ProductionLearnerAdmissionContract(admission.runtime_inputs,runner.runner_path or "",runner.callable_names,len(state.counters),ready,False),batch
