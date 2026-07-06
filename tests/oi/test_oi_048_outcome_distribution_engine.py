from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine
from qseries_v2.oracle_intelligence.market_dna_fingerprinting_engine import MarketDNAFingerprintingEngine
from qseries_v2.oracle_intelligence.analog_market_retrieval_engine import AnalogMarketRetrievalEngine
from qseries_v2.oracle_intelligence.outcome_distribution_engine import OutcomeDistributionEngine


def test_oi_048_outcome_distribution_engine():
    test_db = Path("qseries_v2") / "data" / "test_outcome_distribution.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)
    similarity = OracleSimilarityIntelligenceEngine(bridge)
    dna = MarketDNAFingerprintingEngine()
    retrieval = AnalogMarketRetrievalEngine(similarity, dna)
    distribution = OutcomeDistributionEngine(retrieval)

    for i in range(8):
        bridge.remember_and_persist(
            memory_type="market",
            market_ticker=f"DIST-YES-{i}",
            title=f"Distribution YES case {i}",
            summary="Strong analog resolved YES.",
            confidence=90,
            importance=86,
            tags=["momentum", "yes"],
            source_module="test_oi_048",
            payload={
                "ticker": f"DIST-YES-{i}",
                "price": 78 + (i % 3),
                "implied_probability": 78 + (i % 3),
                "volume": 12000 + i * 100,
                "liquidity": 25000,
                "spread": 2,
                "momentum": 8,
                "volatility": 4,
                "time_to_expiration_minutes": 180,
                "category": "crypto",
                "regime": "trend",
                "pattern_name": "strong_momentum",
                "outcome": {
                    "result": "YES",
                    "move_pct": 4.0 + i,
                    "time_to_resolution_minutes": 30 + i,
                },
            },
        )

    for i in range(2):
        bridge.remember_and_persist(
            memory_type="market",
            market_ticker=f"DIST-NO-{i}",
            title=f"Distribution NO case {i}",
            summary="Similar analog resolved NO.",
            confidence=70,
            importance=64,
            tags=["momentum", "no"],
            source_module="test_oi_048",
            payload={
                "ticker": f"DIST-NO-{i}",
                "price": 76,
                "implied_probability": 76,
                "volume": 10000,
                "liquidity": 22000,
                "spread": 3,
                "momentum": 7,
                "volatility": 5,
                "time_to_expiration_minutes": 190,
                "category": "crypto",
                "regime": "trend",
                "pattern_name": "strong_momentum",
                "outcome": {
                    "result": "NO",
                    "move_pct": -3.0 - i,
                    "time_to_resolution_minutes": 42 + i,
                },
            },
        )

    current = {
        "ticker": "DIST-CURRENT",
        "price": 79,
        "implied_probability": 79,
        "volume": 12100,
        "liquidity": 25000,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 180,
        "category": "crypto",
        "regime": "trend",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = distribution.build_distribution(current, limit=10)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["analog_count"] == 10
    assert result["resolution_distribution"]["expected_resolution"] == "YES"
    assert result["resolution_distribution"]["yes_probability"] > 0.70
    assert result["movement_distribution"]["count"] == 10
    assert result["timing_distribution_minutes"]["count"] == 10
    assert result["confidence_interval"]["lower"] is not None
    assert result["tail_risk"]["tail_risk_level"] in {"low", "medium", "high"}

    status = distribution.status()
    assert status["status"] == "ok"

    print("[PASS] OI-048 Outcome Distribution Engine")
    print({
        "resolution": result["resolution_distribution"],
        "movement": result["movement_distribution"],
        "timing": result["timing_distribution_minutes"],
        "confidence_interval": result["confidence_interval"],
        "tail_risk": result["tail_risk"],
    })


if __name__ == "__main__":
    test_oi_048_outcome_distribution_engine()
