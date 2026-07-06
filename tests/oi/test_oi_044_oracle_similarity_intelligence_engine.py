from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine


def test_oi_044_oracle_similarity_intelligence_engine():
    test_db = Path("qseries_v2") / "data" / "test_oracle_similarity.sqlite3"

    if test_db.exists():
        test_db.unlink()

    engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(engine, store)
    similarity = OracleSimilarityIntelligenceEngine(bridge)

    bridge.remember_and_persist(
        memory_type="market",
        market_ticker="TEST-SIM-1",
        title="Market memory: strong momentum yes",
        summary="A strong momentum YES setup.",
        confidence=91,
        importance=88,
        tags=["momentum", "yes"],
        source_module="test_oi_044",
        payload={
            "ticker": "TEST-SIM-1",
            "price": 78,
            "implied_probability": 78,
            "volume": 10000,
            "liquidity": 25000,
            "spread": 2,
            "momentum": 9,
            "volatility": 4,
            "time_to_expiration_minutes": 180,
            "category": "crypto",
            "regime": "trend",
            "pattern_name": "strong_momentum",
            "outcome": {"result": "YES", "actual_value": 100},
        },
    )

    bridge.remember_and_persist(
        memory_type="market",
        market_ticker="TEST-SIM-2",
        title="Market memory: weak no setup",
        summary="A weak low-liquidity NO setup.",
        confidence=61,
        importance=55,
        tags=["weak", "no"],
        source_module="test_oi_044",
        payload={
            "ticker": "TEST-SIM-2",
            "price": 35,
            "implied_probability": 35,
            "volume": 800,
            "liquidity": 1200,
            "spread": 12,
            "momentum": -3,
            "volatility": 11,
            "time_to_expiration_minutes": 600,
            "category": "weather",
            "regime": "chop",
            "pattern_name": "weak_reversal",
            "outcome": {"result": "NO", "actual_value": 0},
        },
    )

    current = {
        "price": 80,
        "implied_probability": 80,
        "volume": 9800,
        "liquidity": 24000,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 170,
        "category": "crypto",
        "regime": "trend",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = similarity.find_similar_setups(current, limit=2)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["match_count"] >= 2
    assert result["top_matches"][0]["memory"]["market_ticker"] == "TEST-SIM-1"
    assert result["top_matches"][0]["similarity_pct"] > result["top_matches"][1]["similarity_pct"]
    assert result["aggregate"]["occurrences"] == 2

    status = similarity.status()
    assert status["status"] == "ok"

    print("[PASS] OI-044 Oracle Similarity Intelligence Engine")
    print({
        "top_match": result["top_matches"][0]["memory"]["market_ticker"],
        "top_similarity_pct": result["top_matches"][0]["similarity_pct"],
        "aggregate": result["aggregate"],
    })


if __name__ == "__main__":
    test_oi_044_oracle_similarity_intelligence_engine()
