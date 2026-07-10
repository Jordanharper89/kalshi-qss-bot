
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OracleIntelligenceContractValidator,
    OraclePredictionRequest,
)
from qseries_v2.integration.historical_pattern_recognition_engine_adapter import (
    HistoricalPatternRecognitionEngineAdapter,
    create_historical_pattern_recognition_engine_adapter,
    historical_pattern_recognition_engine_adapter,
    oracle_pattern_adapter,
)
from qseries_v2.integration.oracle_intelligence_runtime import create_oracle_intelligence_runtime


def test_oem_001_historical_pattern_recognition_engine_adapter():
    tmp_obj = tempfile.TemporaryDirectory()
    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp_obj.name) / "runtime")

    try:
        adapter = create_historical_pattern_recognition_engine_adapter()

        assert isinstance(adapter, HistoricalPatternRecognitionEngineAdapter)
        assert historical_pattern_recognition_engine_adapter is create_historical_pattern_recognition_engine_adapter
        assert oracle_pattern_adapter is create_historical_pattern_recognition_engine_adapter

        validation = OracleIntelligenceContractValidator.validate(adapter)
        assert validation["status"] == "ok"

        request = OraclePredictionRequest.create(
            "KX-OEM-001",
            {
                "price_samples": [40, 42, 44, 47, 50, 54],
                "liquidity": 1000,
            },
        )

        prediction = adapter.predict(request)
        assert prediction.engine_id == "oracle.historical_pattern_recognition"
        assert prediction.market_id == "KX-OEM-001"
        assert prediction.prediction in {"YES", "NO", "HOLD"}
        assert prediction.confidence >= 0.0
        assert "strongest_pattern" in prediction.features

        explanation = adapter.explain(request)
        assert explanation.engine_id == "oracle.historical_pattern_recognition"
        assert explanation.market_id == "KX-OEM-001"
        assert explanation.summary

        health = adapter.health()
        assert health.status == "ok"

        runtime = create_oracle_intelligence_runtime()
        registered = runtime.register_engine(adapter)
        assert registered.status == "ok"

        runtime.start()
        result = runtime.run_market(
            "KX-OEM-002",
            {
                "price_samples": [40, 42, 44, 47, 50, 54],
                "liquidity": 1000,
            },
        )

        assert result.status == "ok"
        assert result.payload["market_id"] == "KX-OEM-002"
        assert result.payload["canonical_prediction"]["identity"]["engine_id"] == "oracle.multi_engine_aggregator"

        print("[PASS] OEM-001 Historical Pattern Recognition Engine Adapter")
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
    test_oem_001_historical_pattern_recognition_engine_adapter()
