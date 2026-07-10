
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
from qseries_v2.oracle_intelligence.historical_outcome_tracking_engine import (
    create_historical_outcome_tracking_engine,
)


class HistoricalOutcomeTrackingEngineAdapter:
    def __init__(self, engine: Any = None) -> None:
        self.engine = engine or create_historical_outcome_tracking_engine()
        self.engine_id = "oracle.historical_outcome_tracking"

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def metadata(self) -> OracleEngineMetadata:
        return OracleEngineMetadata(
            engine_id=self.engine_id,
            name="Historical Outcome Tracking Engine",
            version="1.0.0",
            description="Tracks historical prediction outcomes and converts accuracy into Oracle predictions.",
            oracle_read_only=True,
        )

    def capabilities(self) -> List[OracleEngineCapability]:
        return [
            OracleEngineCapability(
                name="track_historical_outcomes",
                description="Uses historical win/loss accuracy to produce confidence-adjusted Oracle predictions.",
                inputs=["market_id", "payload"],
                outputs=["prediction", "confidence", "score", "features"],
            )
        ]

    def schema(self) -> Dict[str, Any]:
        return {
            "request": {
                "market_id": "str",
                "payload": {
                    "optional_seed_outcomes": "list[dict]",
                    "fallback_prediction": "YES | NO | HOLD",
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
        status = "ok"
        details: Dict[str, Any] = {}

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
        self._seed_optional_outcomes(request)

        accuracy = self.engine.accuracy(request.market_id)

        total = int(accuracy.get("total", 0))
        wins = int(accuracy.get("wins", 0))
        losses = int(accuracy.get("losses", 0))
        acc = float(accuracy.get("accuracy", 0.0))

        fallback = str(request.payload.get("fallback_prediction", "HOLD")).upper()

        if total == 0:
            prediction = "HOLD"
            confidence = 0.0
            score = 0.0
            risk = 1.0
        else:
            if acc >= 0.60:
                prediction = fallback if fallback in {"YES", "NO"} else "YES"
            elif acc <= 0.40:
                prediction = "NO" if fallback == "YES" else "YES" if fallback == "NO" else "HOLD"
            else:
                prediction = "HOLD"

            confidence = abs(acc - 0.5) * 2
            score = (acc - 0.5) * 0.20
            risk = max(0.0, 1.0 - confidence)

        features = {
            "accuracy": accuracy,
            "total": total,
            "wins": wins,
            "losses": losses,
            "historical_accuracy": acc,
            "probability": acc if total else 0.5,
            "expected_value": score,
            "risk": risk,
        }

        return OraclePredictionResult(
            engine_id=self.engine_id,
            market_id=request.market_id,
            prediction=prediction,
            confidence=float(confidence),
            score=float(score),
            features=features,
            generated_at=self.now_iso(),
        )

    def explain(self, request: OraclePredictionRequest) -> OracleExplanation:
        accuracy = self.engine.accuracy(request.market_id)

        total = int(accuracy.get("total", 0))
        acc = float(accuracy.get("accuracy", 0.0))

        if total == 0:
            summary = "No historical outcomes available for this market"
            reasons = ["No prior outcome records found"]
        else:
            summary = f"Historical outcome accuracy is {acc:.2f} across {total} outcomes"
            reasons = [
                f"Wins: {accuracy.get('wins', 0)}",
                f"Losses: {accuracy.get('losses', 0)}",
                f"Accuracy: {acc:.2f}",
            ]

        return OracleExplanation(
            engine_id=self.engine_id,
            market_id=request.market_id,
            summary=summary,
            reasons=reasons,
            evidence=accuracy,
            generated_at=self.now_iso(),
        )

    def _seed_optional_outcomes(self, request: OraclePredictionRequest) -> None:
        outcomes = request.payload.get("seed_outcomes") or request.payload.get("optional_seed_outcomes")

        if not outcomes:
            return

        for item in outcomes:
            self.engine.record_outcome(
                market_id=request.market_id,
                prediction=str(item.get("prediction", "YES")),
                outcome=str(item.get("outcome", "YES")),
                confidence=float(item.get("confidence", 0.0)),
                metadata=dict(item.get("metadata", {})),
            )


def create_historical_outcome_tracking_engine_adapter(
    engine: Any = None,
) -> HistoricalOutcomeTrackingEngineAdapter:
    return HistoricalOutcomeTrackingEngineAdapter(engine=engine)


historical_outcome_tracking_engine_adapter = create_historical_outcome_tracking_engine_adapter
oracle_outcome_tracking_adapter = create_historical_outcome_tracking_engine_adapter
oracle_outcome_adapter = create_historical_outcome_tracking_engine_adapter


__all__ = [
    "HistoricalOutcomeTrackingEngineAdapter",
    "create_historical_outcome_tracking_engine_adapter",
    "historical_outcome_tracking_engine_adapter",
    "oracle_outcome_tracking_adapter",
    "oracle_outcome_adapter",
]
