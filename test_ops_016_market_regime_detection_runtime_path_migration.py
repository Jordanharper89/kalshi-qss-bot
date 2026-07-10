
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.market_regime_detection_engine import (
    MarketRegimeDetectionEngine,
    create_market_regime_detection_engine,
    market_regime_detection_engine,
    oracle_regime_detection_engine,
    oracle_market_regime_detection_engine,
    oracle_regime_engine,
)


def test_ops_016_market_regime_detection_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_market_regime_detection_engine()

        assert isinstance(engine, MarketRegimeDetectionEngine)
        assert market_regime_detection_engine is create_market_regime_detection_engine
        assert oracle_regime_detection_engine is create_market_regime_detection_engine
        assert oracle_market_regime_detection_engine is create_market_regime_detection_engine
        assert oracle_regime_engine is create_market_regime_detection_engine

        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        missing = engine.detect_regime("UNKNOWN")
        assert missing.regime == "insufficient_data"
        assert missing.sample_count == 0

        for price in [40, 42, 44, 46, 48, 50]:
            engine.record_market_sample(
                market_id="KXTEST-BULL",
                price=price,
                liquidity=1000,
                volume=200,
            )

        samples = engine.load_samples("KXTEST-BULL")
        assert len(samples) == 6
        assert samples[0]["price"] == 40.0

        regime = engine.detect_regime("KXTEST-BULL")
        assert regime.market_id == "KXTEST-BULL"
        assert regime.regime in {"bullish_trend", "volatile"}
        assert regime.sample_count == 6
        assert regime.confidence > 0

        analysis = engine.analyze_market("KXTEST-BULL")
        assert analysis["status"] == "ok"
        assert analysis["regime"]["market_id"] == "KXTEST-BULL"

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-016 Market Regime Detection Runtime Path Migration")
        print(health)

        del missing
        del samples
        del regime
        del analysis
        del health
        del engine
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_016_market_regime_detection_runtime_path_migration()
