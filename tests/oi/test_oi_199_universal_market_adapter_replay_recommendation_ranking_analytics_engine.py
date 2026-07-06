from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_analytics_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine,
    analyze_replay_recommendation_rankings,
)


def test_analyzes_ranking_dict_output():
    ranking_output = {
        "rankings": [
            {
                "rank": 1,
                "recommendation_id": "strong",
                "market_id": "MARKET-A",
                "adapter_id": "adp.test",
                "score": 0.91,
                "grade": "A",
                "confidence": 0.93,
                "priority": "high",
                "reason_codes": [
                    "READ_ONLY_ORACLE_RECOMMENDATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                    "STRONG_CONFIDENCE",
                ],
                "telemetry": {
                    "read_only": True,
                    "execution_owner": "Q Series",
                },
            },
            {
                "rank": 2,
                "recommendation_id": "medium",
                "market_id": "MARKET-B",
                "adapter_id": "adp.test",
                "score": 0.74,
                "grade": "B+",
                "confidence": 0.77,
                "priority": "medium",
                "reason_codes": [
                    "READ_ONLY_ORACLE_RECOMMENDATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                ],
                "telemetry": {
                    "read_only": True,
                    "execution_owner": "Q Series",
                },
            },
        ]
    }

    engine = UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine()
    result = engine.analyze(ranking_output)

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 2
    assert result.analyzed_count == 2
    assert result.score_summary["count"] == 2
    assert result.score_summary["max"] == 0.91
    assert result.confidence_summary["mean"] == 0.85
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert any(bucket.name == "adp.test" and bucket.count == 2 for bucket in result.adapter_distribution)
    assert any(finding.finding_id == "OI199_STRONG_AVERAGE_CONFIDENCE" for finding in result.findings)


def test_wrapper_accepts_iterable_rankings():
    rankings = [
        {
            "rank": 1,
            "recommendation_id": "one",
            "market_id": "M1",
            "adapter_id": "adp.one",
            "score": 88,
            "grade": "A",
            "confidence": 91,
            "priority": "high",
            "reason_codes": ["READ_ONLY_ORACLE_RECOMMENDATION", "Q_SERIES_EXECUTION_REQUIRED"],
            "telemetry": {"read_only": True, "execution_owner": "Q Series"},
        }
    ]

    result = analyze_replay_recommendation_rankings(rankings)

    assert result.status == "ok"
    assert result.analyzed_count == 1
    assert result.score_summary["mean"] == 0.88
    assert result.confidence_summary["mean"] == 0.91
    assert result.grade_distribution[0].name == "A"


def test_empty_input_is_safe():
    engine = UniversalMarketAdapterReplayRecommendationRankingAnalyticsEngine()
    result = engine.analyze([])

    assert result.status == "empty"
    assert result.input_count == 0
    assert result.analyzed_count == 0
    assert result.telemetry["read_only"] is True
    assert result.findings[0].finding_id == "OI199_EMPTY_INPUT"


if __name__ == "__main__":
    test_analyzes_ranking_dict_output()
    test_wrapper_accepts_iterable_rankings()
    test_empty_input_is_safe()

    print("[PASS] OI-199 Universal Market Adapter Replay Recommendation Ranking Analytics Engine")
    print(
        analyze_replay_recommendation_rankings(
            {
                "rankings": [
                    {
                        "rank": 1,
                        "recommendation_id": "demo",
                        "market_id": "DEMO-MARKET",
                        "adapter_id": "adp.demo",
                        "score": 0.86,
                        "grade": "A",
                        "confidence": 0.9,
                        "priority": "high",
                        "reason_codes": [
                            "READ_ONLY_ORACLE_RECOMMENDATION",
                            "Q_SERIES_EXECUTION_REQUIRED",
                            "STRONG_CONFIDENCE",
                        ],
                        "telemetry": {
                            "read_only": True,
                            "execution_owner": "Q Series",
                        },
                    }
                ]
            }
        ).to_dict()
    )
