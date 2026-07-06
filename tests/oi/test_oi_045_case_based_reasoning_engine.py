from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine
from qseries_v2.oracle_intelligence.case_based_reasoning_engine import CaseBasedReasoningEngine


def test_oi_045_case_based_reasoning_engine():
    test_db = Path("qseries_v2") / "data" / "test_case_based_reasoning.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)
    similarity_engine = OracleSimilarityIntelligenceEngine(bridge)
    cbr = CaseBasedReasoningEngine(similarity_engine)

    for i in range(12):
        bridge.remember_and_persist(
            memory_type="market",
            market_ticker=f"CBR-YES-{i}",
            title=f"CBR YES case {i}",
            summary="Strong momentum historical YES case.",
            confidence=88,
            importance=84,
            tags=["momentum", "yes"],
            source_module="test_oi_045",
            payload={
                "ticker": f"CBR-YES-{i}",
                "price": 78 + (i % 3),
                "implied_probability": 78 + (i % 3),
                "volume": 10000 + i * 100,
                "liquidity": 24000,
                "spread": 2,
                "momentum": 8,
                "volatility": 4,
                "time_to_expiration_minutes": 180,
                "category": "crypto",
                "regime": "trend",
                "pattern_name": "strong_momentum",
                "outcome": {"result": "YES"},
            },
        )

    for i in range(3):
        bridge.remember_and_persist(
            memory_type="market",
            market_ticker=f"CBR-NO-{i}",
            title=f"CBR NO case {i}",
            summary="Similar but failed case.",
            confidence=62,
            importance=55,
            tags=["momentum", "no"],
            source_module="test_oi_045",
            payload={
                "ticker": f"CBR-NO-{i}",
                "price": 76,
                "implied_probability": 76,
                "volume": 9000,
                "liquidity": 21000,
                "spread": 3,
                "momentum": 7,
                "volatility": 5,
                "time_to_expiration_minutes": 190,
                "category": "crypto",
                "regime": "trend",
                "pattern_name": "strong_momentum",
                "outcome": {"result": "NO"},
            },
        )

    current = {
        "price": 79,
        "implied_probability": 79,
        "volume": 10100,
        "liquidity": 24000,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 180,
        "category": "crypto",
        "regime": "trend",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = cbr.reason_from_cases(current, limit=15)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["case_count"] == 15
    assert result["expected_resolution"] == "YES"
    assert result["expected_probability"] is not None
    assert result["expected_probability"] > 0.70
    assert len(result["clusters"]) >= 1
    assert len(result["reasoning"]) >= 2

    status = cbr.status()
    assert status["status"] == "ok"

    print("[PASS] OI-045 Case-Based Reasoning Engine")
    print({
        "expected_resolution": result["expected_resolution"],
        "expected_probability": result["expected_probability"],
        "risk_level": result["risk_level"],
        "top_cluster": result["clusters"][0],
        "reasoning": result["reasoning"],
    })


if __name__ == "__main__":
    test_oi_045_case_based_reasoning_engine()
