
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
