from qseries_v2.oracle_intelligence.oracle_performance_attribution_engine import OraclePerformanceAttributionEngine


def test_oi_077_oracle_performance_attribution_engine():
    engine = OraclePerformanceAttributionEngine()

    packet = {
        "market_ticker": "ATTR-TEST",
        "summary": {
            "market_ticker": "ATTR-TEST",
            "expected_resolution": "YES",
            "consensus_score_pct": 88,
            "agreement_pct": 83,
            "research_quality_score": 91,
        },
        "signals": {
            "final_research_grade": "A",
            "expected_resolution": "YES",
        },
        "consensus": {
            "consensus_side": "YES",
            "consensus_score_pct": 88,
            "agreement_pct": 83,
        },
        "consensus_votes": [
            {"engine": "case_reasoning_engine", "side": "YES", "confidence": 90, "weight": 0.24},
            {"engine": "outcome_distribution_engine", "side": "YES", "confidence": 86, "weight": 0.24},
            {"engine": "analog_retrieval_engine", "side": "NO", "confidence": 70, "weight": 0.18},
            {"engine": "market_dna_engine", "side": "YES", "confidence": 78, "weight": 0.10},
        ],
    }

    result = engine.attribute_packet(packet, actual_side="YES")

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["market_ticker"] == "ATTR-TEST"
    assert result["predicted_side"] == "YES"
    assert result["actual_side"] == "YES"
    assert result["correct"] is True
    assert result["attribution"]["largest_positive_contributor"] == "case_reasoning_engine"
    assert result["attribution"]["largest_negative_contributor"] == "analog_retrieval_engine"
    assert result["attribution"]["positive_support_count"] == 3
    assert result["attribution"]["negative_support_count"] == 1
    assert result["execution_enabled"] is False

    summary = engine.attribution_summary()
    assert summary["status"] == "ok"
    assert summary["records_analyzed"] == 1
    assert summary["best_engine"] == "case_reasoning_engine"

    status = engine.status()
    assert status["status"] == "ok"
    assert status["records"] == 1

    print("[PASS] OI-077 Oracle Performance Attribution Engine")
    print({
        "attribution": result["attribution"],
        "summary": summary,
    })


if __name__ == "__main__":
    test_oi_077_oracle_performance_attribution_engine()
