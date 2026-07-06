from pathlib import Path
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore


def test_oi_042_oracle_persistent_memory_store():
    test_db = Path("qseries_v2") / "data" / "test_oracle_memory.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OraclePersistentMemoryStore(test_db)

    record = {
        "memory_id": "mem_test_042",
        "memory_type": "market",
        "market_ticker": "TEST-OI042",
        "title": "Market memory: TEST-OI042",
        "summary": "Persistent memory test record.",
        "confidence": 80.0,
        "importance": 75.0,
        "tags": ["test", "persistent_memory"],
        "source_module": "test_oi_042",
        "payload": {"price": 42, "volume": 1000},
    }

    saved = store.upsert(record)
    assert saved["memory_id"] == "mem_test_042"

    loaded = store.get("mem_test_042")
    assert loaded is not None
    assert loaded["market_ticker"] == "TEST-OI042"

    recalled = store.recall(market_ticker="TEST-OI042")
    assert len(recalled) == 1

    searched = store.search_text("persistent_memory")
    assert len(searched) >= 1

    status = store.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["memory_records"] == 1

    print("[PASS] OI-042 Oracle Persistent Memory Store")
    print(status)


if __name__ == "__main__":
    test_oi_042_oracle_persistent_memory_store()
