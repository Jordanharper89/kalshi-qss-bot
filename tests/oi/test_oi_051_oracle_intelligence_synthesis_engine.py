from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine
from qseries_v2.oracle_intelligence.case_based_reasoning_engine import CaseBasedReasoningEngine
from qseries_v2.oracle_intelligence.market_dna_fingerprinting_engine import MarketDNAFingerprintingEngine
from qseries_v2.oracle_intelligence.analog_market_retrieval_engine import AnalogMarketRetrievalEngine
from qseries_v2.oracle_intelligence.outcome_distribution_engine import OutcomeDistributionEngine
from qseries_v2.oracle_intelligence.adaptive_confidence_learning_engine import AdaptiveConfidenceLearningEngine
from qseries_v2.oracle_intelligence.oracle_knowledge_graph import OracleKnowledgeGraph
from qseries_v2.oracle_intelligence.oracle_intelligence_synthesis_engine import OracleIntelligenceSynthesisEngine


def test_oi_051_oracle_intelligence_synthesis_engine():
    test_db = Path("qseries_v2") / "data" / "test_oracle_synthesis.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)

    similarity = OracleSimilarityIntelligenceEngine(bridge)
    reasoning = CaseBasedReasoningEngine(similarity)
    dna = MarketDNAFingerprintingEngine()
    retrieval = AnalogMarketRetrievalEngine(similarity, dna)
    distribution = OutcomeDistributionEngine(retrieval)
    confidence = AdaptiveConfidenceLearningEngine(bridge)
    graph = OracleKnowledgeGraph(bridge)

    synthesis = OracleIntelligenceSynthesisEngine(
        similarity_engine=similarity,
        reasoning_engine=reasoning,
        dna_engine=dna,
        retrieval_engine=retrieval,
        distribution_engine=distribution,
        confidence_engine=confidence,
        knowledge_graph=graph,
    )

    for i in range(8):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"SYN-YES-{i}",
            title=f"Synthesis YES case {i}",
            summary="Synthesis historical YES case.",
            confidence=86,
            importance=84,
            tags=["momentum", "yes"],
            source_module="test_oi_051",
            payload={
                "ticker": f"SYN-YES-{i}",
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
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 86,
                    "probability": 0.86,
                },
                "outcome": {
                    "result": "YES",
                    "move_pct": 5 + i,
                    "time_to_resolution_minutes": 30 + i,
                },
            },
        )

    for i in range(2):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"SYN-NO-{i}",
            title=f"Synthesis NO case {i}",
            summary="Synthesis historical NO case.",
            confidence=74,
            importance=68,
            tags=["momentum", "no"],
            source_module="test_oi_051",
            payload={
                "ticker": f"SYN-NO-{i}",
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
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 74,
                    "probability": 0.74,
                },
                "outcome": {
                    "result": "NO",
                    "move_pct": -4,
                    "time_to_resolution_minutes": 42,
                },
            },
        )

    current = {
        "ticker": "SYN-CURRENT",
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
        "strategy": "momentum",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = synthesis.synthesize(current, limit=10)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["summary"]["research_ready"] is True
    assert result["summary"]["analog_count"] == 10
    assert result["summary"]["expected_resolution"] == "YES"
    assert result["summary"]["adjusted_confidence"] is not None
    assert result["market_dna"]["dna_id"].startswith("dna_")
    assert result["analog_retrieval"]["top_analogs"]
    assert result["case_reasoning"]["expected_resolution"] == "YES"
    assert result["outcome_distribution"]["resolution_distribution"]["expected_resolution"] == "YES"

    status = synthesis.status()
    assert status["status"] == "ok"

    print("[PASS] OI-051 Oracle Intelligence Synthesis Engine")
    print(result["summary"])


if __name__ == "__main__":
    test_oi_051_oracle_intelligence_synthesis_engine()
