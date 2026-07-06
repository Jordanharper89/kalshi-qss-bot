from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_intelligence_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine,
    evaluate_replay_recommendation_ranking_intelligence,
)


def test_positive_and_info_findings_produce_good_status():
    analytics = {
        "engine_id": "OI-199",
        "findings": [
            {
                "finding_id": "OI199_STRONG_AVERAGE_SCORE",
                "severity": "positive",
                "title": "Strong average ranking score.",
                "detail": "Average ranking score is strong.",
                "recommendation": "Continue replay monitoring.",
            },
            {
                "finding_id": "OI199_HIGH_PRIORITY_CLUSTER",
                "severity": "info",
                "title": "High priority cluster.",
                "detail": "High-priority rankings detected.",
                "recommendation": "Review cluster for bias.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine().evaluate(analytics)

    assert result.engine_id == ENGINE_ID
    assert result.signal_count == 2
    assert result.intelligence_score == 0.64
    assert result.status == "good"
    assert result.signals[0].category == "strength"
    assert result.signals[1].category == "context"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-199"


def test_warning_findings_trigger_review():
    analytics = {
        "engine_id": "OI-199",
        "findings": [
            {
                "finding_id": "OI199_READ_ONLY_TELEMETRY_GAP",
                "severity": "warning",
                "title": "Read-only telemetry gap detected.",
                "detail": "Some rankings did not carry read-only telemetry.",
                "recommendation": "Repair upstream telemetry.",
            }
        ],
    }

    result = evaluate_replay_recommendation_ranking_intelligence(analytics)

    assert result.signal_count == 1
    assert result.intelligence_score == 0.40
    assert result.status == "review"
    assert result.signals[0].category == "risk"
    assert result.signals[0].severity == "warning"


def test_empty_input_is_safe_and_read_only():
    result = UniversalMarketAdapterReplayRecommendationRankingIntelligenceEngine().evaluate(
        {"engine_id": "OI-199", "findings": []}
    )

    assert result.signal_count == 0
    assert result.intelligence_score == 0.50
    assert result.status == "review"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_positive_and_info_findings_produce_good_status()
    test_warning_findings_trigger_review()
    test_empty_input_is_safe_and_read_only()

    print("[PASS] OI-200 Universal Market Adapter Replay Recommendation Ranking Intelligence Engine")
    print(
        evaluate_replay_recommendation_ranking_intelligence(
            {
                "engine_id": "OI-199",
                "findings": [
                    {
                        "finding_id": "DEMO_POSITIVE",
                        "severity": "positive",
                        "title": "Demo positive replay ranking intelligence.",
                        "detail": "The ranked replay recommendation analytics show constructive replay evidence.",
                        "recommendation": "Forward to read-only Oracle certification review.",
                    }
                ],
            }
        ).to_dict()
    )
