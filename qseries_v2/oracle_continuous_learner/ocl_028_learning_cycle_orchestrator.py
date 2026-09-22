from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import LearnerRuntimeBatch,verify_runtime_batch
from .ocl_027_incremental_state_runtime import IncrementalLearnerState,apply_runtime_batch,verify_incremental_state

OCL_028_BUILD_ID="OCL-028"
OCL_028_REVISION="OCL_028_CONTINUOUS_LEARNING_CYCLE_ORCHESTRATOR_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class LearningCycleResult:
    cycle_sequence:int
    input_batch_hash:str
    prior_state_hash:str
    new_state_hash:str
    processed_through_sequence:int
    cycle_hash:str
    terminal_dependency:bool=False

def run_learning_cycle(cycle_sequence,state,batch):
    if cycle_sequence<1 or not verify_incremental_state(state) or not verify_runtime_batch(batch):
        raise ValueError("invalid cycle inputs")
    new_state=apply_runtime_batch(state,batch)
    raw={"cycle_sequence":cycle_sequence,"input_batch_hash":batch.batch_hash,"prior_state_hash":state.state_hash,"new_state_hash":new_state.state_hash,"processed_through_sequence":new_state.applied_through_sequence}
    result=LearningCycleResult(cycle_sequence,batch.batch_hash,state.state_hash,new_state.state_hash,new_state.applied_through_sequence,_h(raw),False)
    return result,new_state

def verify_learning_cycle_result(x):
    raw={"cycle_sequence":x.cycle_sequence,"input_batch_hash":x.input_batch_hash,"prior_state_hash":x.prior_state_hash,"new_state_hash":x.new_state_hash,"processed_through_sequence":x.processed_through_sequence}
    return not x.terminal_dependency and x.cycle_hash==_h(raw)

def build_ocl_028_certification_manifest():
    return MappingProxyType({"build_id":OCL_028_BUILD_ID,"revision":OCL_028_REVISION,"mode":"24_7_cycle_ready","terminal_dependency":False,"idempotency":"sequence_and_hash_chain","execution":False})

def verify_ocl_028_continuous_learning_cycle_orchestrator():
    from .ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
    from .ocl_027_incremental_state_runtime import genesis_incremental_state
    b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
    r,s=run_learning_cycle(1,genesis_incremental_state(),b)
    return verify_learning_cycle_result(r) and verify_incremental_state(s)
