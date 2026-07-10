
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.historical_outcome_tracking_engine import (
    HistoricalOutcomeTrackingEngine,
    create_historical_outcome_tracking_engine,
    historical_outcome_tracking_engine,
    oracle_historical_outcome_tracking_engine,
)


def test_ops_014_historical_outcome_tracking_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_historical_outcome_tracking_engine()

        assert isinstance(engine, HistoricalOutcomeTrackingEngine)
        assert historical_outcome_tracking_engine is create_historical_outcome_tracking_engine
        assert oracle_historical_outcome_tracking_engine is create_historical_outcome_tracking_engine
        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        rec1 = engine.record_outcome(
            market_id="KXTEST-001",
            prediction="YES",
            outcome="YES",
            confidence=0.72,
            metadata={"grade": "A"},
        )

        rec2 = engine.record_outcome(
            market_id="KXTEST-001",
            prediction="NO",
            outcome="YES",
            confidence=0.55,
            metadata={"grade": "B"},
        )

        assert rec1.correct is True
        assert rec2.correct is False

        rows = engine.list_outcomes("KXTEST-001")
        assert len(rows) == 2

        acc = engine.accuracy("KXTEST-001")
        assert acc["total"] == 2
        assert acc["wins"] == 1
        assert acc["losses"] == 1
        assert acc["accuracy"] == 0.5

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-014 Historical Outcome Tracking Runtime Path Migration")
        print(health)

        del rows
        del acc
        del health
        del rec1
        del rec2
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
    test_ops_014_historical_outcome_tracking_runtime_path_migration()
