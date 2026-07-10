
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceContractValidator,
    OraclePredictionRequest,
)
from qseries_v2.integration.historical_outcome_tracking_engine_adapter import (
    HistoricalOutcomeTrackingEngineAdapter,
    create_historical_outcome_tracking_engine_adapter,
    historical_outcome_tracking_engine_adapter,
    oracle_outcome_tracking_adapter,
    oracle_outcome_adapter,
)
from qseries_v2.integration.oracle_intelligence_runtime import create_oracle_intelligence_runtime


def test_oem_002_historical_outcome_tracking_engine_adapter():
    tmp_obj = tempfile.TemporaryDirectory()
    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp_obj.name) / "runtime")

    try:
        adapter = create_historical_outcome_tracking_engine_adapter()

        assert isinstance(adapter, HistoricalOutcomeTrackingEngineAdapter)
        assert historical_outcome_tracking_engine_adapter is create_historical_outcome_tracking_engine_adapter
        assert oracle_outcome_tracking_adapter is create_historical_outcome_tracking_engine_adapter
        assert oracle_outcome_adapter is create_historical_outcome_tracking_engine_adapter

        validation = OracleIntelligenceContractValidator.validate(adapter)
        assert validation["status"] == "ok"

        request = OraclePredictionRequest.create(
            "KX-OEM-002",
            {
                "fallback_prediction": "YES",
                "seed_outcomes": [
                    {"prediction": "YES", "outcome": "YES", "confidence": 0.80},
                    {"prediction": "YES", "outcome": "YES", "confidence": 0.75},
                    {"prediction": "YES", "outcome": "NO", "confidence": 0.60},
                ],
            },
        )

        prediction = adapter.predict(request)

        assert prediction.engine_id == "oracle.historical_outcome_tracking"
        assert prediction.market_id == "KX-OEM-002"
        assert prediction.prediction in {"YES", "NO", "HOLD"}
        assert prediction.features["total"] == 3
        assert prediction.features["wins"] == 2
        assert prediction.features["losses"] == 1
        assert prediction.features["historical_accuracy"] == 2 / 3

        explanation = adapter.explain(request)
        assert explanation.engine_id == "oracle.historical_outcome_tracking"
        assert explanation.market_id == "KX-OEM-002"
        assert explanation.summary

        health = adapter.health()
        assert health.status == "ok"

        runtime = create_oracle_intelligence_runtime()
        registered = runtime.register_engine(adapter)
        assert registered.status == "ok"

        runtime.start()
        result = runtime.run_market(
            "KX-OEM-003",
            {
                "fallback_prediction": "YES",
                "seed_outcomes": [
                    {"prediction": "YES", "outcome": "YES", "confidence": 0.80},
                    {"prediction": "YES", "outcome": "YES", "confidence": 0.75},
                    {"prediction": "YES", "outcome": "NO", "confidence": 0.60},
                ],
            },
        )

        assert result.status == "ok"
        assert result.payload["market_id"] == "KX-OEM-003"
        assert result.payload["canonical_prediction"]["identity"]["engine_id"] == "oracle.multi_engine_aggregator"

        print("[PASS] OEM-002 Historical Outcome Tracking Engine Adapter")
        print({
            "prediction": prediction.to_dict(),
            "runtime_result": result.to_dict(),
        })

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        tmp_obj.cleanup()


if __name__ == "__main__":
    test_oem_002_historical_outcome_tracking_engine_adapter()
