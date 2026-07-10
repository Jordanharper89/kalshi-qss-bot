
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.historical_market_baseline_engine import (
    HistoricalMarketBaselineEngine,
    create_historical_market_baseline_engine,
    historical_market_baseline_engine,
    oracle_market_baseline_engine,
)


def test_ops_013_historical_market_baseline_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_historical_market_baseline_engine()

        assert isinstance(engine, HistoricalMarketBaselineEngine)
        assert historical_market_baseline_engine is create_historical_market_baseline_engine
        assert oracle_market_baseline_engine is create_historical_market_baseline_engine
        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        engine.record_sample("KXTEST-001", price=40, liquidity=1000, source="oracle")
        engine.record_sample("KXTEST-001", price=50, liquidity=2000, source="adapter")
        engine.record_sample("KXTEST-001", price=60, liquidity=3000, source="oracle")

        baseline = engine.build_baseline("KXTEST-001")

        assert baseline is not None
        assert baseline.market_id == "KXTEST-001"
        assert baseline.sample_count == 3
        assert baseline.avg_price == 50.0
        assert baseline.min_price == 40.0
        assert baseline.max_price == 60.0
        assert baseline.avg_liquidity == 2000.0
        assert baseline.sources == ["adapter", "oracle"]

        comparison = engine.compare_to_baseline("KXTEST-001", current_price=55)
        assert comparison["status"] == "ok"
        assert comparison["above_baseline"] is True
        assert comparison["delta"] == 5.0

        missing = engine.compare_to_baseline("UNKNOWN", current_price=55)
        assert missing["status"] == "no_baseline"

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-013 Historical Market Baseline Runtime Path Migration")
        print(health)

        del baseline
        del comparison
        del missing
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
    test_ops_013_historical_market_baseline_runtime_path_migration()
