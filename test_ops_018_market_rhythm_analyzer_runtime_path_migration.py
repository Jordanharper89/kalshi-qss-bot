
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.market_rhythm_analyzer import (
    MarketRhythmAnalyzer,
    create_market_rhythm_analyzer,
    market_rhythm_analyzer,
    oracle_market_rhythm_analyzer,
    oracle_rhythm_analyzer,
    oracle_rhythm_engine,
)


def test_ops_018_market_rhythm_analyzer_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        analyzer = create_market_rhythm_analyzer()

        assert isinstance(analyzer, MarketRhythmAnalyzer)
        assert market_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_market_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_rhythm_analyzer is create_market_rhythm_analyzer
        assert oracle_rhythm_engine is create_market_rhythm_analyzer

        assert analyzer.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(analyzer.db_path).replace("\\", "/")

        missing = analyzer.analyze_rhythm("UNKNOWN")
        assert missing.rhythm_type == "insufficient_data"
        assert missing.sample_count == 0

        for price in [40, 42, 41, 44, 42, 45, 43]:
            analyzer.record_market_sample(
                market_id="KXTEST-RHYTHM",
                price=price,
                liquidity=1000,
                volume=250,
            )

        samples = analyzer.load_samples("KXTEST-RHYTHM")
        assert len(samples) == 7
        assert samples[0]["price"] == 40.0

        rhythm = analyzer.analyze_rhythm("KXTEST-RHYTHM")
        assert rhythm.market_id == "KXTEST-RHYTHM"
        assert rhythm.sample_count == 7
        assert rhythm.confidence >= 0.0
        assert rhythm.rhythm_type in {
            "choppy_reversal_rhythm",
            "steady_upward_rhythm",
            "steady_downward_rhythm",
            "quiet_range_rhythm",
            "mixed_rhythm",
        }

        analysis = analyzer.analyze_market("KXTEST-RHYTHM")
        assert analysis["status"] == "ok"
        assert analysis["rhythm"]["market_id"] == "KXTEST-RHYTHM"

        health = analyzer.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-018 Market Rhythm Analyzer Runtime Path Migration")
        print(health)

        del missing
        del samples
        del rhythm
        del analysis
        del health
        del analyzer
        gc.collect()

    finally:
        if old is None:
            os.environ.pop(RuntimePaths.ENV_RUNTIME_ROOT, None)
        else:
            os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = old

        gc.collect()
        tmp_obj.cleanup()


if __name__ == "__main__":
    test_ops_018_market_rhythm_analyzer_runtime_path_migration()
