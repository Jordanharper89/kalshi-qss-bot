from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge


def test_oi_043_oracle_memory_persistence_bridge():
    test_db = Path("qseries_v2") / "data" / "test_oracle_memory_bridge.sqlite3"

    if test_db.exists():
        test_db.unlink()

    engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(engine, store)

    saved = bridge.remember_and_persist(
        memory_type="pattern",
        market_ticker="TEST-OI043",
        title="Pattern memory: bridge_test",
        summary="Bridge persisted a pattern memory record.",
        confidence=83.0,
        importance=79.0,
        tags=["bridge", "pattern_memory"],
        source_module="test_oi_043",
        payload={"pattern_name": "bridge_test", "observations": 12},
    )

    assert saved["memory_type"] == "pattern"

    persistent = bridge.recall_persistent(market_ticker="TEST-OI043")
    assert len(persistent) == 1

    search = bridge.search_persistent_memory("bridge_test")
    assert len(search) >= 1

    hydrate_result = bridge.hydrate_engine_from_store(market_ticker="TEST-OI043")
    assert hydrate_result["hydrated"] == 1

    persisted_existing = bridge.persist_existing_engine_memory()
    assert persisted_existing["persisted"] >= 1

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-043 Oracle Memory Persistence Bridge")
    print(status)


if __name__ == "__main__":
    test_oi_043_oracle_memory_persistence_bridge()
