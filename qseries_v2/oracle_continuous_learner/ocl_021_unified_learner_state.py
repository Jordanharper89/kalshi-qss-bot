from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_021_BUILD_ID="OCL-021"
OCL_021_REVISION="OCL_021_UNIFIED_LEARNER_STATE_AGGREGATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerStateComponent:
    capability:str
    state_hash:str
    evidence_count:int
    confidence:float

@dataclass(frozen=True)
class UnifiedLearnerState:
    components:tuple[LearnerStateComponent,...]
    total_evidence_count:int
    mean_confidence:float
    state_hash:str

def aggregate_learner_state(components):
    rows=tuple(sorted(components,key=lambda x:x.capability))
    if not rows: raise ValueError("learner state components required")
    if len({x.capability for x in rows})!=len(rows): raise ValueError("duplicate learner capability")
    for x in rows:
        if len(x.state_hash)!=64 or x.evidence_count<0 or not 0<=x.confidence<=1:
            raise ValueError("invalid learner component")
    total=sum(x.evidence_count for x in rows)
    mean=sum(x.confidence for x in rows)/len(rows)
    raw=[{"capability":x.capability,"state_hash":x.state_hash,"evidence_count":x.evidence_count,"confidence":x.confidence} for x in rows]
    return UnifiedLearnerState(rows,total,mean,_h(raw))

def build_ocl_021_certification_manifest():
    return MappingProxyType({"build_id":OCL_021_BUILD_ID,"revision":OCL_021_REVISION,"aggregation":"deterministic","upstream_mutation":False,"execution":False})

def verify_ocl_021_unified_learner_state_aggregation():
    a=LearnerStateComponent("calibration","a"*64,10,.8)
    b=LearnerStateComponent("narrative","b"*64,20,.7)
    return aggregate_learner_state((b,a)).state_hash==aggregate_learner_state((a,b)).state_hash
