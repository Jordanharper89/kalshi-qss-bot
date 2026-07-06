from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine
from qseries_v2.oracle_intelligence.market_dna_fingerprinting_engine import MarketDNAFingerprintingEngine
from qseries_v2.oracle_intelligence.analog_market_retrieval_engine import AnalogMarketRetrievalEngine


def test_oi_047_analog_market_retrieval_engine():
    test_db = Path("qseries_v2") / "data" / "test_analog_market_retrieval.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)
    similarity = OracleSimilarityIntelligenceEngine(bridge)
    dna = MarketDNAFingerprintingEngine()
    retrieval = AnalogMarketRetrievalEngine(similarity, dna)

    bridge.remember_and_persist(
        memory_type="market",
        market_ticker="ANALOG-STRONG",
        title="Strong analog case",
        summary="Strong crypto momentum resolved YES.",
        confidence=92,
        importance=90,
        tags=["momentum", "yes"],
        source_module="test_oi_047",
        payload={
            "ticker": "ANALOG-STRONG",
            "price": 79,
            "implied_probability": 79,
            "volume": 12000,
            "liquidity": 25000,
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

    bridge.remember_and_persist(
        memory_type="market",
        market_ticker="ANALOG-WEAK",
        title="Weak analog case",
        summary="Weak weather chop resolved NO.",
        confidence=55,
        importance=50,
        tags=["weak", "no"],
        source_module="test_oi_047",
        payload={
            "ticker": "ANALOG-WEAK",
            "price": 31,
            "implied_probability": 31,
            "volume": 700,
            "liquidity": 900,
            "spread": 12,
            "momentum": -4,
            "volatility": 10,
            "time_to_expiration_minutes": 600,
            "category": "weather",
            "regime": "chop",
            "pattern_name": "weak_reversal",
            "outcome": {"result": "NO"},
        },
    )

    current = {
        "ticker": "CURRENT",
        "price": 80,
        "implied_probability": 80,
        "volume": 11800,
        "liquidity": 25500,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 175,
        "category": "crypto",
        "regime": "trend",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = retrieval.retrieve_analogs(current, limit=2)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["analog_count"] >= 2
    assert result["top_analogs"][0]["memory"]["market_ticker"] == "ANALOG-STRONG"
    assert result["top_analogs"][0]["retrieval_score"] > result["top_analogs"][1]["retrieval_score"]
    assert result["summary"]["count"] == 2

    status = retrieval.status()
    assert status["status"] == "ok"

    print("[PASS] OI-047 Analog Market Retrieval Engine")
    print({
        "top_analog": result["top_analogs"][0]["memory"]["market_ticker"],
        "retrieval_score_pct": result["top_analogs"][0]["retrieval_score_pct"],
        "summary": result["summary"],
    })


if __name__ == "__main__":
    test_oi_047_analog_market_retrieval_engine()
