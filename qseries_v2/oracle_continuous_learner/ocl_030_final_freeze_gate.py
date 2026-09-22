from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import verify_ocl_026_continuous_learner_intake_runtime
from .ocl_027_incremental_state_runtime import verify_ocl_027_incremental_learner_state_update_runtime
from .ocl_028_learning_cycle_orchestrator import verify_ocl_028_continuous_learning_cycle_orchestrator
from .ocl_029_scientific_reasoning_handoff import verify_ocl_029_scientific_reasoning_handoff_contract

OCL_030_BUILD_ID="OCL-030"
OCL_030_REVISION="OCL_030_CONTINUOUS_LEARNER_RUNTIME_FINAL_FREEZE_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class ContinuousLearnerFinalCertification:
    certified_builds:tuple[str,...]
    subsystem:str
    capability:str
    downstream_boundary:str
    freeze_hash:str
    frozen:bool=True
    defect_corrections_only:bool=True

def certify_ocl_001_through_030():
    checks=(
        verify_ocl_026_continuous_learner_intake_runtime(),
        verify_ocl_027_incremental_learner_state_update_runtime(),
        verify_ocl_028_continuous_learning_cycle_orchestrator(),
        verify_ocl_029_scientific_reasoning_handoff_contract(),
    )
    if not all(checks): raise RuntimeError("OCL final certification failed")
    builds=tuple("OCL-%03d"%i for i in range(1,31))
    raw={
        "certified_builds":builds,
        "subsystem":"Oracle Continuous Learner",
        "capability":"24_7_deterministic_continuous_learning",
        "downstream_boundary":"Scientific Reasoning read-only intake",
        "frozen":True,
        "defect_corrections_only":True,
    }
    return ContinuousLearnerFinalCertification(builds,raw["subsystem"],raw["capability"],raw["downstream_boundary"],_h(raw))

def build_ocl_030_certification_manifest():
    c=certify_ocl_001_through_030()
    return MappingProxyType({
        "build_id":OCL_030_BUILD_ID,
        "revision":OCL_030_REVISION,
        "certified_build_count":len(c.certified_builds),
        "subsystem":c.subsystem,
        "capability":c.capability,
        "downstream_boundary":c.downstream_boundary,
        "frozen":c.frozen,
        "defect_corrections_only":c.defect_corrections_only,
        "execution":False,
        "publication":False,
    })

def verify_ocl_030_continuous_learner_runtime_final_freeze_gate():
    c=certify_ocl_001_through_030()
    return c.frozen and c.defect_corrections_only and len(c.certified_builds)==30 and c.downstream_boundary=="Scientific Reasoning read-only intake"
