from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_021_unified_learner_state import verify_ocl_021_unified_learner_state_aggregation
from .ocl_022_learning_maturity import verify_ocl_022_learning_confidence_evidence_maturity
from .ocl_023_meta_learning_performance import verify_ocl_023_meta_learning_performance_evaluation
from .ocl_024_adaptive_learning_weight import verify_ocl_024_adaptive_learning_weight_model

OCL_025_BUILD_ID="OCL-025"
OCL_025_REVISION="OCL_025_LEARNER_STATE_META_LEARNING_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerStateMetaLearningCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ocl_021_through_025():
    checks=(
        verify_ocl_021_unified_learner_state_aggregation(),
        verify_ocl_022_learning_confidence_evidence_maturity(),
        verify_ocl_023_meta_learning_performance_evaluation(),
        verify_ocl_024_adaptive_learning_weight_model(),
    )
    if not all(checks): raise RuntimeError("capability certification failed")
    builds=tuple("OCL-%03d"%i for i in range(21,26))
    raw={
        "builds":builds,
        "capability":"learner_state_aggregation_and_meta_learning",
        "next_capability":"continuous_learner_runtime_and_scientific_reasoning_handoff",
        "certified":True,
    }
    return LearnerStateMetaLearningCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_ocl_025_certification_manifest():
    c=certify_ocl_021_through_025()
    return MappingProxyType({
        "build_id":OCL_025_BUILD_ID,
        "revision":OCL_025_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
        "self_modifying_code":False,
    })

def verify_ocl_025_learner_state_meta_learning_certification_gate():
    c=certify_ocl_021_through_025()
    return c.certified and len(c.builds)==5 and c.next_capability=="continuous_learner_runtime_and_scientific_reasoning_handoff"
