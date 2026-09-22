from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import importlib,json

OCR_001_BUILD_ID="OCR-001"
OCR_001_REVISION="OCR_001_CONTINUOUS_REASONING_RUNTIME_FOUNDATION_V1"

FROZEN_BOUNDARIES=(
    ("qseries_v2.oracle_continuous_intake.oci_010_capability_certification","verify_oci_010_continuous_intake_capability_certification_gate","OCI-010"),
    ("qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate","verify_ocl_030_continuous_learner_runtime_final_freeze_gate","OCL-030"),
    ("qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze","verify_osr_030_scientific_reasoning_final_certification_freeze","OSR-030"),
    ("qseries_v2.oracle_intelligence_state.ois_055_final_freeze","verify_ois_055_final_production_certification_freeze","OIS-055"),
)

@dataclass(frozen=True)
class ContinuousReasoningFoundation:
    frozen_boundaries:tuple[str,...]
    mode:str
    terminal_dependency:bool
    execution_authority:bool
    upstream_mutation:bool
    foundation_hash:str

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def verify_frozen_reasoning_boundaries():
    verified=[]
    for module_name,verifier_name,label in FROZEN_BOUNDARIES:
        module=importlib.import_module(module_name)
        verifier=getattr(module,verifier_name,None)
        if not callable(verifier) or verifier() is not True:
            raise RuntimeError("Frozen boundary failed: "+label)
        verified.append(label)
    return tuple(verified)

def build_continuous_reasoning_foundation():
    boundaries=verify_frozen_reasoning_boundaries()
    raw={"boundaries":boundaries,"mode":"continuous_read_only_reasoning_activation","terminal_dependency":False,
         "execution_authority":False,"upstream_mutation":False}
    return ContinuousReasoningFoundation(boundaries,raw["mode"],False,False,False,_h(raw))

def verify_ocr_001_continuous_reasoning_runtime_foundation():
    f=build_continuous_reasoning_foundation()
    return f.frozen_boundaries==("OCI-010","OCL-030","OSR-030","OIS-055") and not f.execution_authority and not f.upstream_mutation
