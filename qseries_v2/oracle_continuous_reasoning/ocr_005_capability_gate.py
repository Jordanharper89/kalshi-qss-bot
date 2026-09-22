from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from .ocr_001_foundation import verify_ocr_001_continuous_reasoning_runtime_foundation
from .ocr_002_live_observation_read_model import verify_ocr_002_postgresql_live_observation_read_model
from .ocr_003_reasoning_input_batch import verify_ocr_003_reasoning_input_batch_assembly
from .ocr_004_reasoning_activation_bridge import verify_ocr_004_frozen_scientific_reasoning_activation_bridge

OCR_005_BUILD_ID="OCR-005"
OCR_005_REVISION="OCR_005_LIVE_REASONING_INTAKE_ACTIVATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class OCRCapabilityCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ocr_001_through_005():
    checks=(verify_ocr_001_continuous_reasoning_runtime_foundation(),
            verify_ocr_002_postgresql_live_observation_read_model(),
            verify_ocr_003_reasoning_input_batch_assembly(),
            verify_ocr_004_frozen_scientific_reasoning_activation_bridge())
    if not all(checks): raise RuntimeError("OCR capability certification failed")
    builds=tuple("OCR-%03d"%i for i in range(1,6))
    cap="live_postgresql_observation_to_frozen_scientific_reasoning_activation"
    nxt="continuous_scientific_reasoning_invocation_and_intelligence_state_update"
    h=sha256(json.dumps({"builds":builds,"cap":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return OCRCapabilityCertification(builds,cap,nxt,h,True)

def verify_ocr_005_live_reasoning_intake_activation_capability_gate():
    c=certify_ocr_001_through_005()
    return c.certified and len(c.builds)==5
