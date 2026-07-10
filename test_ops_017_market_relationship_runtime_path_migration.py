
import gc
import os
import tempfile
from pathlib import Path

from qseries_v2.ops.runtime_paths import RuntimePaths
from qseries_v2.oracle_intelligence.market_relationship_engine import (
    MarketRelationshipEngine,
    create_market_relationship_engine,
    market_relationship_engine,
    oracle_market_relationship_engine,
    oracle_relationship_engine,
)


def test_ops_017_market_relationship_runtime_path_migration():
    tmp_obj = tempfile.TemporaryDirectory()
    tmp = tmp_obj.name

    old = os.environ.get(RuntimePaths.ENV_RUNTIME_ROOT)
    os.environ[RuntimePaths.ENV_RUNTIME_ROOT] = str(Path(tmp) / "runtime")

    try:
        engine = create_market_relationship_engine()

        assert isinstance(engine, MarketRelationshipEngine)
        assert market_relationship_engine is create_market_relationship_engine
        assert oracle_market_relationship_engine is create_market_relationship_engine
        assert oracle_relationship_engine is create_market_relationship_engine

        assert engine.db_path == RuntimePaths.qseries_history_db()
        assert "qseries_v2/data" not in str(engine.db_path).replace("\\", "/")

        for price in [40, 42, 44, 46]:
            engine.record_market_sample("KXTEST-A", "GROUP-1", price=price, liquidity=1000)

        for price in [20, 21, 22, 23]:
            engine.record_market_sample("KXTEST-B", "GROUP-1", price=price, liquidity=800)

        for price in [70, 68, 66, 64]:
            engine.record_market_sample("KXTEST-C", "GROUP-1", price=price, liquidity=700)

        samples = engine.load_group_samples("GROUP-1")
        assert sorted(samples.keys()) == ["KXTEST-A", "KXTEST-B", "KXTEST-C"]
        assert samples["KXTEST-A"] == [40.0, 42.0, 44.0, 46.0]

        relationships = engine.detect_relationships("GROUP-1")
        assert len(relationships) == 3

        types = {item.relationship_type for item in relationships}
        assert "positive_correlation" in types
        assert "inverse_correlation" in types

        strongest = engine.strongest_relationship("GROUP-1")
        assert strongest is not None
        assert strongest.strength >= 0.0

        analysis = engine.analyze_group("GROUP-1")
        assert analysis["status"] == "ok"
        assert analysis["relationship_count"] == 3
        assert analysis["strongest_relationship"] is not None

        empty = engine.analyze_group("EMPTY")
        assert empty["status"] == "ok"
        assert empty["relationship_count"] == 0
        assert empty["strongest_relationship"] is None

        health = engine.health()
        assert health["status"] == "ok"
        assert health["uses_runtime_paths"] is True

        print("[PASS] OPS-017 Market Relationship Runtime Path Migration")
        print(health)

        del samples
        del relationships
        del strongest
        del analysis
        del empty
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
    test_ops_017_market_relationship_runtime_path_migration()
