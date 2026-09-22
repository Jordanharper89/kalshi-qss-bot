from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_026_BUILD_ID = "OSR-026"
OSR_026_REVISION = "OSR_026_REASONING_CALIBRATION_ENGINE_V1"

@dataclass(frozen=True)
class CalibrationObservation:
    prediction_id: str
    confidence: float
    outcome: float
    evidence_quality: float

@dataclass(frozen=True)
class CalibrationAssessment:
    count: int
    brier_score: float
    weighted_error: float
    calibration_quality: float
    status: str

def assess_reasoning_calibration(observations):
    rows = tuple(observations)
    if not rows:
        raise ValueError("calibration observations required")

    for x in rows:
        if any(not 0 <= v <= 1 for v in (x.confidence, x.outcome, x.evidence_quality)):
            raise ValueError("normalized calibration values required")

    brier = sum((x.confidence - x.outcome) ** 2 for x in rows) / len(rows)
    weighted = sum(
        abs(x.confidence - x.outcome) * (1 + x.evidence_quality) / 2
        for x in rows
    ) / len(rows)

    quality = max(0.0, 1.0 - weighted)
    status = "calibrated" if quality >= 0.80 else ("watch" if quality >= 0.60 else "poor")

    return CalibrationAssessment(len(rows), brier, weighted, quality, status)

def build_osr_026_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_026_BUILD_ID,
        "revision": OSR_026_REVISION,
        "method": "brier_plus_evidence_weighted_error",
        "execution": False,
        "publication": False,
    })

def verify_osr_026_reasoning_calibration_engine():
    rows = (
        CalibrationObservation("a", 0.9, 1.0, 1.0),
        CalibrationObservation("b", 0.1, 0.0, 1.0),
    )
    result = assess_reasoning_calibration(rows)
    return result.count == 2 and result.status == "calibrated"
