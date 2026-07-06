from qseries_v2.oracle_intelligence.institutional_intelligence_score import institutional_intelligence_score


def test_oi_079_institutional_intelligence_score():
    packet = {
        "market_ticker": "INST-TEST",
        "summary": {
            "market_ticker": "INST-TEST",
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "consensus_score_pct": 90,
            "agreement_pct": 92,
            "research_certainty_index": 89,
            "research_stability": "high",
            "risk_level": "low",
            "tail_risk_level": "low",
            "analog_count": 35,
            "graph_nodes": 30,
            "top_analog": {"market_ticker": "ANALOG-1", "similarity_pct": 89},
            "outlier_engines": [],
        },
        "signals": {
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "risk_level": "low",
            "tail_risk_level": "low",
            "final_research_grade": "A",
            "execution_enabled": False,
        },
        "consensus": {
            "consensus_side": "YES",
            "consensus_score_pct": 90,
            "agreement_pct": 92,
            "research_certainty_index": 89,
            "research_stability": "high",
            "outlier_engines": [],
        },
        "consensus_votes": [
            {"engine": "case_reasoning_engine", "side": "YES", "confidence": 90, "weight": 0.24},
            {"engine": "outcome_distribution_engine", "side": "YES", "confidence": 86, "weight": 0.24},
            {"engine": "market_dna_engine", "side": "YES", "confidence": 82, "weight": 0.10},
        ],
    }

    quality = {
        "research_quality_score": 88.27,
        "grade": "A-",
        "institutional_ready": True,
        "missing_evidence": [],
        "penalties": {"drift_penalty": 0.0, "risk_penalty": 0.0},
    }

    meta = {
        "overall_health": 86,
        "research_quality": "strong",
        "best_engine": "case_reasoning_engine",
        "weakest_engine": "analog_retrieval_engine",
    }

    weights = {
        "optimized_weights": {
            "case_reasoning_engine": 0.28,
            "outcome_distribution_engine": 0.24,
            "analog_retrieval_engine": 0.16,
            "adaptive_confidence_engine": 0.14,
            "market_dna_engine": 0.10,
            "knowledge_graph_engine": 0.08,
        },
        "weight_deltas": {
            "case_reasoning_engine": 0.04,
            "outcome_distribution_engine": 0.0,
            "analog_retrieval_engine": -0.02,
            "adaptive_confidence_engine": -0.02,
            "market_dna_engine": 0.0,
            "knowledge_graph_engine": 0.0,
        },
    }

    attribution = {
        "attribution": {
            "alpha_added": 68,
            "noise_score": 8,
            "positive_support_count": 3,
            "negative_support_count": 0,
            "largest_positive_contributor": "case_reasoning_engine",
        }
    }

    agreement = {
        "pair_count": 3,
        "consensus_diversity": {
            "diversity_level": "high",
            "diversity_score": 84,
        },
        "summary": {
            "agreement_pairs": 3,
            "disagreement_pairs": 0,
        },
    }

    runtime = {
        "health": "healthy",
        "metrics": {"errors": 0},
    }

    portfolio = {
        "portfolio_state": {"state": "strong_alignment"},
        "risk_summary": {"high_risk_signals": 0},
        "drift_summary": {"counts": {"side_changed": 0}},
    }

    result = institutional_intelligence_score.score(
        packet=packet,
        quality_report=quality,
        meta_report=meta,
        weight_report=weights,
        attribution_report=attribution,
        agreement_report=agreement,
        runtime_status=runtime,
        portfolio_report=portfolio,
    )

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["q_series_interface"]["execution_enabled"] is False
    assert result["q_series_interface"]["execution_owner"] == "Q Series"
    assert result["institutional_intelligence_score"] >= 80
    assert result["institutional_grade"] in {"A+", "A", "A-", "B+"}
    assert result["deployment_readiness"] in {"institutional_strong", "institutional_ready", "validation_required"}

    status = institutional_intelligence_score.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-079 Institutional Intelligence Score")
    print({
        "score": result["institutional_intelligence_score"],
        "grade": result["institutional_grade"],
        "ready": result["institutional_ready"],
        "summary": result["summary"],
    })


if __name__ == "__main__":
    test_oi_079_institutional_intelligence_score()
