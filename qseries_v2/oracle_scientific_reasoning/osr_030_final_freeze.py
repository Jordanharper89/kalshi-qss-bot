from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_026_reasoning_calibration import verify_osr_026_reasoning_calibration_engine
from .osr_027_meta_reasoning_quality import verify_osr_027_meta_reasoning_quality_evaluation
from .osr_028_cross_capability_synthesis import verify_osr_028_cross_capability_scientific_reasoning_synthesis
from .osr_029_intelligence_state import verify_osr_029_oracle_scientific_intelligence_state

OSR_030_BUILD_ID = "OSR-030"
OSR_030_REVISION = "OSR_030_SCIENTIFIC_REASONING_FINAL_CERTIFICATION_FREEZE_V1"

@dataclass(frozen=True)
class ScientificReasoningFinalFreeze:
    certified_builds: tuple[str, ...]
    subsystem: str
    capability: str
    downstream_boundary: str
    freeze_hash: str
    certified: bool = True
    frozen: bool = True
    defect_corrections_only: bool = True

def certify_and_freeze_osr_001_through_030():
    checks = (
        verify_osr_026_reasoning_calibration_engine(),
        verify_osr_027_meta_reasoning_quality_evaluation(),
        verify_osr_028_cross_capability_scientific_reasoning_synthesis(),
        verify_osr_029_oracle_scientific_intelligence_state(),
    )
    if not all(checks):
        raise RuntimeError("OSR final certification failed")

    builds = tuple("OSR-%03d" % i for i in range(1, 31))
    raw = {
        "certified_builds": builds,
        "subsystem": "Oracle Scientific Reasoning",
        "capability": "scientific_reasoning_to_oracle_intelligence_state",
        "downstream_boundary": "oracle_intelligence_state_read_only_consumption",
        "frozen": True,
        "defect_corrections_only": True,
    }

    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return ScientificReasoningFinalFreeze(
        builds,
        raw["subsystem"],
        raw["capability"],
        raw["downstream_boundary"],
        digest,
    )

def build_osr_030_certification_manifest():
    c = certify_and_freeze_osr_001_through_030()
    return MappingProxyType({
        "build_id": OSR_030_BUILD_ID,
        "revision": OSR_030_REVISION,
        "certified_build_count": len(c.certified_builds),
        "subsystem": c.subsystem,
        "capability": c.capability,
        "downstream_boundary": c.downstream_boundary,
        "frozen": c.frozen,
        "defect_corrections_only": c.defect_corrections_only,
        "execution": False,
        "publication": False,
    })

def verify_osr_030_scientific_reasoning_final_certification_freeze():
    c = certify_and_freeze_osr_001_through_030()
    return (
        c.certified
        and c.frozen
        and c.defect_corrections_only
        and len(c.certified_builds) == 30
        and c.downstream_boundary == "oracle_intelligence_state_read_only_consumption"
    )
