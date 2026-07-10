
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionRequest,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.oracle_intelligence.historical_pattern_recognition_engine import (
    create_historical_pattern_recognition_engine,
)


class HistoricalPatternRecognitionEngineAdapter:
    """
    OEM-001 adapter.

    Wraps the historical pattern recognition engine in the canonical
    OracleIntelligenceEngineContract.
    """

    def __init__(self, engine: Any = None) -> None:
        self.engine = engine or create_historical_pattern_recognition_engine()
        self.engine_id = "oracle.historical_pattern_recognition"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id=self.engine_id,
            name="Historical Pattern Recognition Engine",
            version="1.0.0",
            description="Detects historical market patterns and converts them into canonical Oracle predictions.",
            oracle_read_only=True,
        )

    def capabilities(self) -> List[OracleEngineCapability]:
        return [
            OracleEngineCapability(
                name="detect_historical_patterns",
                description="Detects uptrend, downtrend, range-bound, and regime-shift historical patterns.",
                inputs=["market_id", "payload"],
                outputs=["prediction", "confidence", "score", "features"],
            )
        ]

    def schema(self) -> Dict[str, Any]:
        return {
            "request": {
                "market_id": "str",
                "payload": {
                    "optional_price_samples": "list[float]",
                },
            },
            "response": {
                "prediction": "YES | NO | HOLD",
                "confidence": "float",
                "score": "float",
                "features": "dict",
            },
        }

    def health(self) -> OracleEngineHealth:
        details = {}
        status = "ok"

        try:
            if hasattr(self.engine, "health"):
                details = self.engine.health()
        except Exception as exc:
            status = "error"
            details = {"error": str(exc)}

        return OracleEngineHealth(
            engine_id=self.engine_id,
            status=status,
            details=details,
            checked_at=self.now_iso(),
        )

    def predict(self, request: OraclePredictionRequest) -> OraclePredictionResult:
        self._seed_optional_samples(request)

        analysis = self.engine.analyze_market(request.market_id)

        strongest = analysis.get("strongest_pattern")
        pattern_count = int(analysis.get("pattern_count", 0))

        prediction = "HOLD"
        confidence = 0.0
        score = 0.0
        risk = 1.0

        if strongest:
            pattern_type = strongest.get("pattern_type")
            confidence = float(strongest.get("confidence", 0.0))

            if pattern_type in {"uptrend", "regime_shift"}:
                prediction = "YES"
            elif pattern_type == "downtrend":
                prediction = "NO"
            else:
                prediction = "HOLD"

            score = confidence * 0.10
            risk = max(0.0, 1.0 - confidence)

        features = {
            "pattern_count": pattern_count,
            "strongest_pattern": strongest,
            "raw_analysis": analysis,
            "probability": confidence,
            "expected_value": score,
            "risk": risk,
        }

        return OraclePredictionResult(
            engine_id=self.engine_id,
            market_id=request.market_id,
            prediction=prediction,
            confidence=confidence,
            score=score,
            features=features,
            generated_at=self.now_iso(),
        )

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        analysis = self.engine.analyze_market(request.market_id)
        strongest = analysis.get("strongest_pattern")

        if strongest:
            summary = f"Detected historical pattern: {strongest.get('pattern_type')}"
            reasons = [
                f"Pattern confidence: {strongest.get('confidence')}",
                f"Sample count: {strongest.get('sample_count')}",
            ]
        else:
            summary = "No strong historical pattern detected"
            reasons = ["Pattern count was zero or insufficient"]

        return OracleExplanation(
            engine_id=self.engine_id,
            market_id=request.market_id,
            summary=summary,
            reasons=reasons,
            evidence=analysis,
            generated_at=self.now_iso(),
        )

    def _seed_optional_samples(self, request: OraclePredictionRequest) -> None:
        samples = request.payload.get("price_samples") or request.payload.get("optional_price_samples")

        if not samples:
            return

        for price in samples:
            self.engine.record_price_sample(
                market_id=request.market_id,
                price=float(price),
                liquidity=float(request.payload.get("liquidity", 0.0)),
            )


def create_historical_pattern_recognition_engine_adapter(
    engine: Any = None,
) -> HistoricalPatternRecognitionEngineAdapter:
    return HistoricalPatternRecognitionEngineAdapter(engine=engine)


historical_pattern_recognition_engine_adapter = create_historical_pattern_recognition_engine_adapter
oracle_pattern_adapter = create_historical_pattern_recognition_engine_adapter


__all__ = [
    "HistoricalPatternRecognitionEngineAdapter",
    "create_historical_pattern_recognition_engine_adapter",
    "historical_pattern_recognition_engine_adapter",
    "oracle_pattern_adapter",
]
