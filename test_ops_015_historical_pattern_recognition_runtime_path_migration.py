
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.historical_pattern_recognition_engine import (
    HistoricalPatternRecognitionEngine,
    create_historical_pattern_recognition_engine,
    historical_pattern_recognition_engine,
    oracle_pattern_recognition_engine,
    oracle_historical_pattern_recognition_engine,
    oracle_pattern_engine,
)


def test_ops_015_historical_pattern_recognition_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_historical_pattern_recognition_engine()

        assert isinstance(engine, HistoricalPatternRecognitionEngine)
        assert historical_pattern_recognition_engine is create_historical_pattern_recognition_engine
        assert oracle_pattern_recognition_engine is create_historical_pattern_recognition_engine
        assert oracle_historical_pattern_recognition_engine is create_historical_pattern_recognition_engine
        assert oracle_pattern_engine is create_historical_pattern_recognition_engine
        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        for price in [40, 42, 44, 47, 50, 54]:
            engine.record_price_sample("KXTEST-UP", price=price, liquidity=1000)

        prices = engine.load_price_series("KXTEST-UP")
        assert prices == [40.0, 42.0, 44.0, 47.0, 50.0, 54.0]

        patterns = engine.detect_patterns("KXTEST-UP")
        pattern_types = {pattern.pattern_type for pattern in patterns}

        assert "uptrend" in pattern_types
        assert "regime_shift" in pattern_types

        strongest = engine.strongest_pattern("KXTEST-UP")
        assert strongest is not None
        assert strongest.confidence > 0

        analysis = engine.analyze_market("KXTEST-UP")
        assert analysis["status"] == "ok"
        assert analysis["pattern_count"] >= 1
        assert analysis["strongest_pattern"] is not None

        empty_analysis = engine.analyze_market("UNKNOWN")
        assert empty_analysis["status"] == "ok"
        assert empty_analysis["pattern_count"] == 0
        assert empty_analysis["strongest_pattern"] is None

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-015 Historical Pattern Recognition Runtime Path Migration")
        print(health)

        del prices
        del patterns
        del strongest
        del analysis
        del empty_analysis
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
    test_ops_015_historical_pattern_recognition_runtime_path_migration()
