from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_intelligence_interface_contract.py"
TEST = ROOT / "test_int_001_oracle_intelligence_interface_contract.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Protocol, runtime_checkable


@dataclass(frozen=True)
class OracleEngineMetadata:
    engine_id: str
    name: str
    version: str
    description: str
    oracle_read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OracleEngineCapability:
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OraclePredictionRequest:
    market_id: str
    payload: Dict[str, Any]
    requested_at: str

    @staticmethod
    def create(market_id: str, payload: Dict[str, Any] | None = None) -> "OraclePredictionRequest":
        return OraclePredictionRequest(
            market_id=market_id,
            payload=payload or {},
            requested_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OraclePredictionResult:
    engine_id: str
    market_id: str
    prediction: str
    confidence: float
    score: float
    features: Dict[str, Any]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OracleExplanation:
    engine_id: str
    market_id: str
    summary: str
    reasons: List[str]
    evidence: Dict[str, Any]
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OracleEngineHealth:
    engine_id: str
    status: str
    details: Dict[str, Any]
    checked_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@runtime_checkable
class OracleIntelligenceEngineContract(Protocol):
    """
    INT-001 canonical Oracle Intelligence interface.

    Oracle engines are read-only intelligence providers.
    They may analyze, explain, score, and predict.
    They must not execute trades.
    """

    def metadata(self) -> OracleEngineMetadata:
        ...

    def capabilities(self) -> List[OracleEngineCapability]:
        ...

    def schema(self) -> Dict[str, Any]:
        ...

    def health(self) -> OracleEngineHealth:
        ...

    def predict(self, request: OraclePredictionRequest) -> OraclePredictionResult:
        ...

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        ...


class OracleIntelligenceContractValidator:
    REQUIRED_METHODS = [
        "metadata",
        "capabilities",
        "schema",
        "health",
        "predict",
        "explain",
    ]

    @classmethod
    def validate(cls, engine: Any) -> Dict[str, Any]:
        missing = [
            method for method in cls.REQUIRED_METHODS
            if not hasattr(engine, method) or not callable(getattr(engine, method))
        ]

        return {
            "status": "ok" if not missing else "error",
            "missing_methods": missing,
            "required_methods": list(cls.REQUIRED_METHODS),
            "is_contract_like": not missing,
        }


__all__ = [
    "OracleEngineMetadata",
    "OracleEngineCapability",
    "OraclePredictionRequest",
    "OraclePredictionResult",
    "OracleExplanation",
    "OracleEngineHealth",
    "OracleIntelligenceEngineContract",
    "OracleIntelligenceContractValidator",
]
'''

test_code = r'''
from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionRequest,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
    OracleIntelligenceEngineContract,
    OracleIntelligenceContractValidator,
)


class DummyOracleEngine:
    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id="oracle.dummy",
            name="Dummy Oracle Engine",
            version="1.0.0",
            description="Test engine",
        )

    def capabilities(self) -> List[OracleEngineCapability]:
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predicts market direction",
                inputs=["market_id", "payload"],
                outputs=["prediction", "confidence", "score"],
            )
        ]

    def schema(self) -> Dict[str, Any]:
        return {
            "request": ["market_id", "payload"],
            "response": ["prediction", "confidence", "score", "features"],
        }

    def health(self) -> OracleEngineHealth:
        return OracleEngineHealth(
            engine_id="oracle.dummy",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request: OraclePredictionRequest) -> OraclePredictionResult:
        return OraclePredictionResult(
            engine_id="oracle.dummy",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.75,
            score=0.18,
            features={"signal": "test"},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        return OracleExplanation(
            engine_id="oracle.dummy",
            market_id=request.market_id,
            summary="Dummy explanation",
            reasons=["Test reason"],
            evidence={"sample": True},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


class BrokenEngine:
    def metadata(self):
        return {}


def test_int_001_oracle_intelligence_interface_contract():
    engine = DummyOracleEngine()

    assert isinstance(engine, OracleIntelligenceEngineContract)

    validation = OracleIntelligenceContractValidator.validate(engine)
    assert validation["status"] == "ok"
    assert validation["missing_methods"] == []

    broken = OracleIntelligenceContractValidator.validate(BrokenEngine())
    assert broken["status"] == "error"
    assert "predict" in broken["missing_methods"]

    metadata = engine.metadata()
    assert metadata.engine_id == "oracle.dummy"
    assert metadata.oracle_read_only is True

    capabilities = engine.capabilities()
    assert len(capabilities) == 1
    assert capabilities[0].name == "predict_market"

    request = OraclePredictionRequest.create("KXTEST-001", {"price": 42})
    assert request.market_id == "KXTEST-001"

    prediction = engine.predict(request)
    assert prediction.market_id == "KXTEST-001"
    assert prediction.prediction == "YES"
    assert prediction.confidence == 0.75

    explanation = engine.explain(request)
    assert explanation.summary == "Dummy explanation"
    assert explanation.reasons == ["Test reason"]

    health = engine.health()
    assert health.ok is True

    print("[PASS] INT-001 Oracle Intelligence Interface Contract")
    print({
        "engine_id": metadata.engine_id,
        "contract_status": validation["status"],
        "capabilities": [item.to_dict() for item in capabilities],
    })


if __name__ == "__main__":
    test_int_001_oracle_intelligence_interface_contract()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
init_path.parent.mkdir(parents=True, exist_ok=True)

existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_intelligence_interface_contract import "
    "OracleEngineMetadata, OracleEngineCapability, OraclePredictionRequest, "
    "OraclePredictionResult, OracleExplanation, OracleEngineHealth, "
    "OracleIntelligenceEngineContract, OracleIntelligenceContractValidator\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-001 INSTALLER")
print(" Oracle Intelligence Interface Contract")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-001 installed")
print("")
print("Run:")
print("py test_int_001_oracle_intelligence_interface_contract.py")