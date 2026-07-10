from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_terminal_api_layer.py"
TEST = ROOT / "test_int_007_oracle_terminal_api_layer.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
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
'''

test_code = r'''
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleEngineMetadata,
    OracleEngineCapability,
    OraclePredictionResult,
    OracleExplanation,
    OracleEngineHealth,
)
from qseries_v2.integration.oracle_terminal_api_layer import (
    OracleTerminalApiLayer,
    create_oracle_terminal_api_layer,
    oracle_terminal_api_layer,
)


class TerminalDummyEngine:
    def metadata(self):
        return OracleEngineMetadata(
            engine_id="oracle.terminal.test",
            name="Terminal Test Engine",
            version="1.0.0",
            description="Terminal API test engine",
            oracle_read_only=True,
        )

    def capabilities(self):
        return [
            OracleEngineCapability(
                name="predict_market",
                description="Predict terminal test market",
                inputs=["market_id"],
                outputs=["prediction"],
            )
        ]

    def schema(self):
        return {"request": ["market_id"], "response": ["prediction"]}

    def health(self):
        return OracleEngineHealth(
            engine_id="oracle.terminal.test",
            status="ok",
            details={"ready": True},
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def predict(self, request):
        return OraclePredictionResult(
            engine_id="oracle.terminal.test",
            market_id=request.market_id,
            prediction="YES",
            confidence=0.88,
            score=0.10,
            features={
                "probability": 0.74,
                "expected_value": 0.08,
                "risk": 0.20,
            },
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def explain(self, request):
        return OracleExplanation(
            engine_id="oracle.terminal.test",
            market_id=request.market_id,
            summary="Terminal test signal",
            reasons=["High confidence", "Positive EV"],
            evidence={"sample_count": 12},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


def test_int_007_oracle_terminal_api_layer():
    api = create_oracle_terminal_api_layer()

    assert isinstance(api, OracleTerminalApiLayer)
    assert oracle_terminal_api_layer is create_oracle_terminal_api_layer

    register = api.register_engine(TerminalDummyEngine())
    assert register.ok is True
    assert register.payload["engine_count"] == 1

    health = api.health()
    assert health.ok is True
    assert health.payload["api"] == "oracle_terminal_api_layer"

    engines = api.engines()
    assert engines.ok is True
    assert engines.payload["engine_count"] == 1
    assert engines.payload["engines"][0]["metadata"]["engine_id"] == "oracle.terminal.test"

    prediction = api.predict("KX-TERMINAL-001")
    assert prediction.ok is True
    assert prediction.payload["aggregate"]["direction"] == "YES"
    assert prediction.payload["canonical_prediction"]["direction"] == "YES"

    explanation = api.explain("KX-TERMINAL-001")
    assert explanation.ok is True
    assert explanation.payload["explanation"]["summary"] == "Consensus from 1 Oracle engines"

    decision = api.decision("KX-TERMINAL-001")
    assert decision.ok is True
    assert decision.payload["execution_decision"]["status"] == "APPROVED"

    missing = api.predict("")
    assert missing.ok is False
    assert "market_id_required" in missing.errors

    pipeline = api.pipeline_status()
    assert pipeline.ok is True
    assert len(pipeline.payload["stages"]) == 5

    print("[PASS] INT-007 Oracle Terminal API Layer")
    print(decision.to_dict())


if __name__ == "__main__":
    test_int_007_oracle_terminal_api_layer()
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_terminal_api_layer import "
    "OracleTerminalApiResponse, OracleTerminalApiLayer, "
    "create_oracle_terminal_api_layer, oracle_terminal_api_layer\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-007 INSTALLER")
print(" Oracle Terminal API Layer")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-007 installed")
print("")
print("Run:")
print("py test_int_007_oracle_terminal_api_layer.py")