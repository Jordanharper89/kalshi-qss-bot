from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "canonical_prediction_contract.py"
TEST = ROOT / "test_int_003_canonical_prediction_contract.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class PredictionDirection(str, Enum):
    YES = "YES"
    NO = "NO"
    HOLD = "HOLD"


@dataclass(frozen=True)
class PredictionIdentity:
    prediction_id: str
    engine_id: str
    market_id: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionMetrics:
    confidence: float
    score: float
    probability: float
    expected_value: float
    risk: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionExplanation:
    summary: str
    reasons: List[str]
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalPrediction:
    identity: PredictionIdentity
    direction: PredictionDirection
    metrics: PredictionMetrics
    features: Dict[str, Any]
    explanation: Optional[PredictionExplanation]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "direction": self.direction.value,
            "metrics": self.metrics.to_dict(),
            "features": dict(self.features),
            "explanation": (
                self.explanation.to_dict()
                if self.explanation
                else None
            ),
        }


class CanonicalPredictionFactory:

    @staticmethod
    def create(
        *,
        engine_id: str,
        market_id: str,
        direction: PredictionDirection,
        confidence: float,
        score: float,
        probability: float,
        expected_value: float,
        risk: float,
        features: Optional[Dict[str, Any]] = None,
        explanation: Optional[PredictionExplanation] = None,
    ) -> CanonicalPrediction:

        identity = PredictionIdentity(
            prediction_id=f"{engine_id}:{market_id}:{datetime.now(timezone.utc).timestamp()}",
            engine_id=engine_id,
            market_id=market_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        metrics = PredictionMetrics(
            confidence=float(confidence),
            score=float(score),
            probability=float(probability),
            expected_value=float(expected_value),
            risk=float(risk),
        )

        return CanonicalPrediction(
            identity=identity,
            direction=direction,
            metrics=metrics,
            features=features or {},
            explanation=explanation,
        )


class CanonicalPredictionValidator:

    @staticmethod
    def validate(prediction: CanonicalPrediction) -> Dict[str, Any]:

        errors = []

        if not 0.0 <= prediction.metrics.confidence <= 1.0:
            errors.append("confidence")

        if not 0.0 <= prediction.metrics.probability <= 1.0:
            errors.append("probability")

        if prediction.direction not in PredictionDirection:
            errors.append("direction")

        return {
            "status": "ok" if not errors else "error",
            "errors": errors,
            "valid": not errors,
        }


__all__ = [
    "PredictionDirection",
    "PredictionIdentity",
    "PredictionMetrics",
    "PredictionExplanation",
    "CanonicalPrediction",
    "CanonicalPredictionFactory",
    "CanonicalPredictionValidator",
]
'''

test = r'''
from qseries_v2.integration.canonical_prediction_contract import *

def test_int_003():

    explanation = PredictionExplanation(
        summary="Bullish edge",
        reasons=["Momentum","Liquidity"],
        evidence={"sample":5},
    )

    prediction = CanonicalPredictionFactory.create(
        engine_id="oracle.pattern",
        market_id="KX-001",
        direction=PredictionDirection.YES,
        confidence=0.86,
        score=0.23,
        probability=0.71,
        expected_value=0.12,
        risk=0.18,
        features={"pattern":"breakout"},
        explanation=explanation,
    )

    validation = CanonicalPredictionValidator.validate(prediction)

    assert validation["status"] == "ok"
    assert prediction.direction == PredictionDirection.YES
    assert prediction.metrics.confidence == 0.86
    assert prediction.identity.engine_id == "oracle.pattern"
    assert prediction.explanation.summary == "Bullish edge"

    print("[PASS] INT-003 Canonical Prediction Contract")
    print(prediction.to_dict())

if __name__ == "__main__":
    test_int_003()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test, encoding="utf-8")

init = ROOT / "qseries_v2" / "integration" / "__init__.py"

existing = init.read_text(encoding="utf-8") if init.exists() else ""

export = (
    "from .canonical_prediction_contract import *\n"
)

if export not in existing:
    init.write_text(existing.rstrip()+"\n"+export, encoding="utf-8")

print("========================================")
print(" INT-003 INSTALLER")
print(" Canonical Prediction Contract")
print("========================================")
print("[OK] Wrote", TARGET)
print("[OK] Wrote", TEST)
print("[OK] Updated", init)
print()
print("[DONE] INT-003 installed")
print()
print("Run:")
print("py test_int_003_canonical_prediction_contract.py")