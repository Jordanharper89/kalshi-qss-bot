from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_027_BUILD_ID = "OSR-027"
OSR_027_REVISION = "OSR_027_META_REASONING_QUALITY_EVALUATION_V1"

@dataclass(frozen=True)
class ReasoningQualityInput:
    capability_id: str
    evidence_coverage: float
    contradiction_control: float
    calibration_quality: float
    replay_integrity: float

@dataclass(frozen=True)
class MetaReasoningAssessment:
    capability_id: str
    quality_score: float
    weakest_dimension: str
    status: str
    abstain: bool

def evaluate_reasoning_quality(x, minimum_quality=0.65):
    vals = {
        "evidence_coverage": float(x.evidence_coverage),
        "contradiction_control": float(x.contradiction_control),
        "calibration_quality": float(x.calibration_quality),
        "replay_integrity": float(x.replay_integrity),
    }
    if any(not 0 <= v <= 1 for v in vals.values()):
        raise ValueError("normalized quality values required")

    score = sum(vals.values()) / len(vals)
    weakest = sorted(vals.items(), key=lambda p: (p[1], p[0]))[0][0]
    abstain = score < minimum_quality

    return MetaReasoningAssessment(
        x.capability_id,
        score,
        weakest,
        "trusted" if not abstain else "insufficient",
        abstain,
    )

def build_osr_027_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_027_BUILD_ID,
        "revision": OSR_027_REVISION,
        "purpose": "reasoning_quality_self_evaluation",
        "abstention": True,
        "execution": False,
    })

def verify_osr_027_meta_reasoning_quality_evaluation():
    x = ReasoningQualityInput("scientific", 1.0, 0.9, 0.9, 1.0)
    return not evaluate_reasoning_quality(x).abstain
