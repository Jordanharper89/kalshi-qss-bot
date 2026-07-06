from qseries_v2.oracle_intelligence.oracle_meta_intelligence_engine import OracleMetaIntelligenceEngine


def test_oi_074_oracle_meta_intelligence_engine():
    engine = OracleMetaIntelligenceEngine()

    for i in range(10):
        engine.record_engine_result(
            engine_name="consensus_engine",
            predicted_side="YES",
            actual_side="YES" if i < 9 else "NO",
            confidence=88,
            contribution_score=90,
            drift_score=2,
            lead_time_minutes=15,
        )

    for i in range(10):
        engine.record_engine_result(
            engine_name="analog_retrieval_engine",
            predicted_side="YES",
            actual_side="YES" if i < 6 else "NO",
            confidence=90,
            contribution_score=65,
            drift_score=18,
            lead_time_minutes=9,
        )

    report = engine.evaluate_engines()

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["engine_scores"]["consensus_engine"]["accuracy"] == 0.9
    assert report["engine_scores"]["analog_retrieval_engine"]["accuracy"] == 0.6
    assert report["engine_scores"]["consensus_engine"]["meta_score"] > report["engine_scores"]["analog_retrieval_engine"]["meta_score"]
    assert "recommended_weight_changes" in report

    packet_eval = engine.evaluate_from_consensus_votes(
        {
            "consensus_votes": [
                {"engine": "case_reasoning_engine", "side": "YES", "confidence": 84, "weight": 0.24},
                {"engine": "market_dna_engine", "side": "YES", "confidence": 78, "weight": 0.10},
            ]
        },
        actual_side="YES",
    )

    assert packet_eval["votes_recorded"] == 2

    status = engine.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-074 Oracle Meta Intelligence Engine")
    print({
        "overall_health": report["overall_health"],
        "best_engine": report["best_engine"],
        "highest_drift_engine": report["highest_drift_engine"],
        "quality": report["research_quality"],
    })


if __name__ == "__main__":
    test_oi_074_oracle_meta_intelligence_engine()
