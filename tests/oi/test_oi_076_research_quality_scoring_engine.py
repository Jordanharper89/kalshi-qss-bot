from qseries_v2.oracle_intelligence.research_quality_scoring_engine import research_quality_scoring_engine


def test_oi_076_research_quality_scoring_engine():
    packet = {
        "summary": {
            "market_ticker": "QUALITY-TEST",
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "agreement_pct": 92,
            "research_stability": "high",
            "risk_level": "low",
            "tail_risk_level": "low",
            "analog_count": 35,
            "graph_nodes": 30,
            "graph_edges": 80,
            "dna_id": "dna_test",
            "dna_family": "family_test",
            "top_analog": {
                "market_ticker": "ANALOG-1",
                "retrieval_score_pct": 91,
                "similarity_pct": 89,
            },
            "outlier_engines": [],
        },
        "signals": {
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "risk_level": "low",
            "tail_risk_level": "low",
            "execution_enabled": False,
        },
        "consensus": {
            "agreement_pct": 92,
            "research_stability": "high",
        },
        "consensus_votes": [
            {"engine": "case_reasoning", "side": "YES", "confidence": 88},
            {"engine": "outcome_distribution", "side": "YES", "confidence": 86},
            {"engine": "market_dna", "side": "YES", "confidence": 82},
        ],
    }

    meta = {
        "overall_health": 88,
        "research_quality": "strong",
    }

    weights = {
        "optimized_weights": {
            "case_reasoning_engine": 0.28,
            "outcome_distribution_engine": 0.24,
            "analog_retrieval_engine": 0.16,
            "adaptive_confidence_engine": 0.14,
            "market_dna_engine": 0.10,
            "knowledge_graph_engine": 0.08,
        }
    }

    runtime = {"health": "healthy"}

    result = research_quality_scoring_engine.score_packet(packet, meta, weights, runtime)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["execution_enabled"] is False
    assert result["execution_owner"] == "Q Series"
    assert result["research_quality_score"] >= 80
    assert result["grade"] in {"A+", "A", "A-", "B+"}
    assert result["dimensions"]["agreement"] == 92.0

    status = research_quality_scoring_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-076 Research Quality Scoring Engine")
    print({
        "score": result["research_quality_score"],
        "grade": result["grade"],
        "institutional_ready": result["institutional_ready"],
        "summary": result["summary"],
    })


if __name__ == "__main__":
    test_oi_076_research_quality_scoring_engine()
