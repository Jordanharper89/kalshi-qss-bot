from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import LearnerRuntimeBatch,verify_runtime_batch

OCL_027_BUILD_ID="OCL-027"
OCL_027_REVISION="OCL_027_INCREMENTAL_LEARNER_STATE_UPDATE_RUNTIME_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class IncrementalLearnerState:
    applied_through_sequence:int
    applied_batches:int
    last_batch_hash:str
    parent_state_hash:str
    state_hash:str

def genesis_incremental_state():
    raw={"applied_through_sequence":0,"applied_batches":0,"last_batch_hash":"0"*64,"parent_state_hash":"0"*64}
    return IncrementalLearnerState(0,0,"0"*64,"0"*64,_h(raw))

def apply_runtime_batch(previous,batch):
    if not verify_runtime_batch(batch): raise ValueError("invalid runtime batch")
    if batch.start_sequence <= previous.applied_through_sequence:
        raise ValueError("replay or overlap rejected")
    raw={"applied_through_sequence":batch.end_sequence,"applied_batches":previous.applied_batches+1,"last_batch_hash":batch.batch_hash,"parent_state_hash":previous.state_hash}
    return IncrementalLearnerState(batch.end_sequence,previous.applied_batches+1,batch.batch_hash,previous.state_hash,_h(raw))

def verify_incremental_state(x):
    raw={"applied_through_sequence":x.applied_through_sequence,"applied_batches":x.applied_batches,"last_batch_hash":x.last_batch_hash,"parent_state_hash":x.parent_state_hash}
    return x.state_hash==_h(raw)

def build_ocl_027_certification_manifest():
    return MappingProxyType({"build_id":OCL_027_BUILD_ID,"revision":OCL_027_REVISION,"update":"incremental_hash_chained","historical_rewrite":False,"execution":False})

def verify_ocl_027_incremental_learner_state_update_runtime():
    from .ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
    g=genesis_incremental_state()
    b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
    s=apply_runtime_batch(g,b)
    return verify_incremental_state(g) and verify_incremental_state(s) and s.parent_state_hash==g.state_hash
