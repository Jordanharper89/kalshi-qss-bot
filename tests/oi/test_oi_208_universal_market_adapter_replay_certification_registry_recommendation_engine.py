from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_recommendation_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine,
    recommend_replay_certification_registry_actions,
)


def test_strength_signal_creates_promote_recommendation():
    intelligence = {
        "engine_id": "OI-207",
        "status": "good",
        "intelligence_score": 0.72,
        "signals": [
            {
                "signal_id": "SIG_STRENGTH",
                "category": "strength",
                "severity": "positive",
                "score": 0.90,
                "title": "Certified cohort strength.",
                "explanation": "Registry cohort is constructive.",
                "recommendation": "Forward to review.",
            }
        ],
    }

    result = UniversalMarketAdapterReplayCertificationRegistryRecommendationEngine().recommend(intelligence)

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "promote"
    assert result.recommendations[0].priority == "high"
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.recommendations[0].reason_codes
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-207"


def test_warning_signal_creates_review_recommendation():
    result = recommend_replay_certification_registry_actions(
        {
            "engine_id": "OI-207",
            "status": "review",
            "intelligence_score": 0.38,
            "signals": [
                {
                    "signal_id": "SIG_RISK",
                    "category": "risk",
                    "severity": "warning",
                    "score": 0.30,
                    "title": "Weak registry cohort.",
                    "explanation": "Registry cohort requires review.",
                    "recommendation": "Hold.",
                }
            ],
        }
    )

    assert result.status == "review"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "review"
    assert result.recommendations[0].priority == "high"
    assert "REGISTRY_RISK_SIGNAL" in result.recommendations[0].reason_codes


def test_empty_signals_create_hold_recommendation():
    result = recommend_replay_certification_registry_actions(
        {"engine_id": "OI-207", "status": "review", "intelligence_score": 0.50, "signals": []}
    )

    assert result.status == "monitor"
    assert result.recommendation_count == 1
    assert result.recommendations[0].recommendation_type == "hold"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


def test_limit_is_respected():
    result = recommend_replay_certification_registry_actions(
        {
            "engine_id": "OI-207",
            "intelligence_score": 0.70,
            "signals": [
                {"signal_id": "S1", "category": "strength", "severity": "positive", "score": 0.90, "title": "A"},
                {"signal_id": "S2", "category": "context", "severity": "info", "score": 0.60, "title": "B"},
            ],
        },
        limit=1,
    )

    assert result.recommendation_count == 1


if __name__ == "__main__":
    test_strength_signal_creates_promote_recommendation()
    test_warning_signal_creates_review_recommendation()
    test_empty_signals_create_hold_recommendation()
    test_limit_is_respected()

    print("[PASS] OI-208 Universal Market Adapter Replay Certification Registry Recommendation Engine")
    print(
        recommend_replay_certification_registry_actions(
            {
                "engine_id": "OI-207",
                "status": "good",
                "intelligence_score": 0.72,
                "signals": [
                    {
                        "signal_id": "SIG_DEMO",
                        "category": "strength",
                        "severity": "positive",
                        "score": 0.90,
                        "title": "Demo registry strength.",
                        "explanation": "Replay certification registry intelligence is constructive.",
                        "recommendation": "Forward to read-only Oracle review.",
                    }
                ],
            }
        ).to_dict()
    )
