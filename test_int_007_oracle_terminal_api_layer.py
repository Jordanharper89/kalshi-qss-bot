
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
