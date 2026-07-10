
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceEngineContract,
    OraclePredictionRequest,
)
from qseries_v2.integration.multi_engine_oracle_aggregator import (
    MultiEngineOracleAggregator,
    AggregatedOracleSignal,
)
from qseries_v2.integration.qseries_execution_gateway import (
    QSeriesExecutionGateway,
    ExecutionDecision,
)


@dataclass(frozen=True)
class OracleTerminalApiResponse:
    status: str
    endpoint: str
    payload: Dict[str, Any]
    errors: List[str]
    generated_at: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleTerminalApiLayer:
    """
    INT-007 Oracle Terminal API Layer.

    Stable internal API for web terminal, dashboard, Telegram, REST,
    and future client surfaces.

    This layer exposes intelligence and execution decisions.
    It does not place trades directly.
    """

    def __init__(
        self,
        aggregator: Optional[MultiEngineOracleAggregator] = None,
        execution_gateway: Optional[QSeriesExecutionGateway] = None,
    ) -> None:
        self.aggregator = aggregator or MultiEngineOracleAggregator()
        self.execution_gateway = execution_gateway or QSeriesExecutionGateway()

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _response(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        errors: Optional[List[str]] = None,
    ) -> OracleTerminalApiResponse:
        errors = errors or []
        return OracleTerminalApiResponse(
            status="ok" if not errors else "error",
            endpoint=endpoint,
            payload=payload,
            errors=errors,
            generated_at=self.now_iso(),
        )

    def register_engine(self, engine: OracleIntelligenceEngineContract) -> OracleTerminalApiResponse:
        self.aggregator.register_engine(engine)
        metadata = engine.metadata()
        return self._response(
            endpoint="register_engine",
            payload={
                "registered": True,
                "engine": metadata.to_dict(),
                "engine_count": len(self.aggregator.engines),
            },
        )

    def health(self) -> OracleTerminalApiResponse:
        return self._response(
            endpoint="health",
            payload={
                "api": "oracle_terminal_api_layer",
                "aggregator": self.aggregator.health(),
                "execution_gateway": self.execution_gateway.health(),
            },
        )

    def engines(self) -> OracleTerminalApiResponse:
        engine_payloads = []
        errors = []

        for engine in self.aggregator.engines:
            try:
                metadata = engine.metadata()
                health = engine.health()
                engine_payloads.append({
                    "metadata": metadata.to_dict(),
                    "health": health.to_dict(),
                    "capabilities": [cap.to_dict() for cap in engine.capabilities()],
                    "schema": engine.schema(),
                })
            except Exception as exc:
                errors.append(str(exc))

        return self._response(
            endpoint="engines",
            payload={
                "engine_count": len(engine_payloads),
                "engines": engine_payloads,
            },
            errors=errors,
        )

    def predict(self, market_id: str, payload: Optional[Dict[str, Any]] = None) -> OracleTerminalApiResponse:
        if not market_id:
            return self._response("predict", {}, ["market_id_required"])

        request = OraclePredictionRequest.create(market_id, payload or {})
        aggregate = self.aggregator.aggregate(request)
        canonical = self.aggregator.to_canonical_prediction(aggregate)

        return self._response(
            endpoint="predict",
            payload={
                "market_id": market_id,
                "aggregate": aggregate.to_dict(),
                "canonical_prediction": canonical.to_dict(),
            },
        )

    def decision(self, market_id: str, payload: Optional[Dict[str, Any]] = None) -> OracleTerminalApiResponse:
        if not market_id:
            return self._response("decision", {}, ["market_id_required"])

        request = OraclePredictionRequest.create(market_id, payload or {})
        aggregate = self.aggregator.aggregate(request)
        canonical = self.aggregator.to_canonical_prediction(aggregate)
        decision = self.execution_gateway.evaluate(canonical)

        return self._response(
            endpoint="decision",
            payload={
                "market_id": market_id,
                "aggregate": aggregate.to_dict(),
                "canonical_prediction": canonical.to_dict(),
                "execution_decision": decision.to_dict(),
            },
        )

    def explain(self, market_id: str, payload: Optional[Dict[str, Any]] = None) -> OracleTerminalApiResponse:
        prediction_response = self.predict(market_id, payload)

        if not prediction_response.ok:
            return prediction_response

        canonical = prediction_response.payload["canonical_prediction"]
        explanation = canonical.get("explanation")

        return self._response(
            endpoint="explain",
            payload={
                "market_id": market_id,
                "explanation": explanation,
                "canonical_prediction": canonical,
            },
        )

    def pipeline_status(self) -> OracleTerminalApiResponse:
        return self._response(
            endpoint="pipeline_status",
            payload={
                "stages": [
                    {"name": "oracle_engines", "status": "ok", "count": len(self.aggregator.engines)},
                    {"name": "multi_engine_aggregator", "status": self.aggregator.health()["status"]},
                    {"name": "canonical_prediction_contract", "status": "ok"},
                    {"name": "qseries_execution_gateway", "status": self.execution_gateway.health()["status"]},
                    {"name": "oracle_terminal_api_layer", "status": "ok"},
                ]
            },
        )


def create_oracle_terminal_api_layer(
    aggregator: Optional[MultiEngineOracleAggregator] = None,
    execution_gateway: Optional[QSeriesExecutionGateway] = None,
) -> OracleTerminalApiLayer:
    return OracleTerminalApiLayer(
        aggregator=aggregator,
        execution_gateway=execution_gateway,
    )


oracle_terminal_api_layer = create_oracle_terminal_api_layer


__all__ = [
    "OracleTerminalApiResponse",
    "OracleTerminalApiLayer",
    "create_oracle_terminal_api_layer",
    "oracle_terminal_api_layer",
]
