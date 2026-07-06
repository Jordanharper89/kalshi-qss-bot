from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingEngine,
    rank_replay_recommendations,
)


def test_ranking_orders_best_candidate_first():
    engine = UniversalMarketAdapterReplayRecommendationRankingEngine()

    candidates = [
        {
            "recommendation_id": "weak",
            "market_id": "MARKET-B",
            "adapter_id": "adp.test",
            "confidence": 0.60,
            "edge_pct": 4,
            "replay_quality": 0.55,
            "stability": 0.50,
            "explainability": 0.50,
        },
        {
            "recommendation_id": "strong",
            "market_id": "MARKET-A",
            "adapter_id": "adp.test",
            "confidence": 0.95,
            "edge_pct": 24,
            "replay_quality": 0.90,
            "stability": 0.85,
            "explainability": 0.80,
        },
    ]

    result = engine.rank(candidates)

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 2
    assert result.ranked_count == 2
    assert result.rankings[0].recommendation_id == "strong"
    assert result.rankings[0].rank == 1
    assert result.rankings[0].score > result.rankings[1].score
    assert "READ_ONLY_ORACLE_RECOMMENDATION" in result.rankings[0].reason_codes
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.rankings[0].reason_codes
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"


def test_function_wrapper_and_limit():
    result = rank_replay_recommendations(
        [
            {
                "id": "one",
                "market": "M1",
                "adapter": "adp.test",
                "confidence_score": 88,
                "expected_edge": 18,
                "replay_score": 91,
                "stability_score": 80,
                "explainability_score": 79,
            },
            {
                "id": "two",
                "market": "M2",
                "adapter": "adp.test",
                "confidence_score": 70,
                "expected_edge": 8,
                "replay_score": 65,
                "stability_score": 65,
                "explainability_score": 60,
            },
        ],
        limit=1,
    )

    assert result.ranked_count == 1
    assert result.rankings[0].recommendation_id == "one"
    assert result.rankings[0].market_id == "M1"
    assert result.rankings[0].adapter_id == "adp.test"


def test_empty_input_is_safe_and_read_only():
    engine = UniversalMarketAdapterReplayRecommendationRankingEngine()
    result = engine.rank([])

    assert result.status == "empty"
    assert result.input_count == 0
    assert result.ranked_count == 0
    assert result.rankings == ()
    assert result.telemetry["read_only"] is True


if __name__ == "__main__":
    test_ranking_orders_best_candidate_first()
    test_function_wrapper_and_limit()
    test_empty_input_is_safe_and_read_only()
    print("[PASS] OI-198 Universal Market Adapter Replay Recommendation Ranking Engine")
    print(rank_replay_recommendations([
        {
            "recommendation_id": "demo",
            "market_id": "DEMO-MARKET",
            "adapter_id": "adp.demo",
            "confidence": 0.91,
            "edge_pct": 17,
            "replay_quality": 0.88,
            "stability": 0.82,
            "explainability": 0.80,
        }
    ]).to_dict())
