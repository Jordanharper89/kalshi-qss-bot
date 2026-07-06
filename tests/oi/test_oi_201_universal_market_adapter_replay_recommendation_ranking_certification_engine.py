from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_ranking_certification_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayRecommendationRankingCertificationEngine,
    certify_replay_recommendation_ranking_intelligence,
)


def test_certifies_good_intelligence_without_warning_signals():
    intelligence = {
        "engine_id": "OI-200",
        "status": "good",
        "intelligence_score": 0.64,
        "signals": [
            {
                "signal_id": "SIG_POSITIVE",
                "category": "strength",
                "severity": "positive",
                "score": 0.90,
                "title": "Constructive replay intelligence.",
                "explanation": "Replay analytics are constructive.",
                "recommendation": "Promote to certification review.",
            },
            {
                "signal_id": "SIG_INFO",
                "category": "context",
                "severity": "info",
                "score": 0.60,
                "title": "Context signal.",
                "explanation": "Additional context exists.",
                "recommendation": "Review context.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayRecommendationRankingCertificationEngine().certify(intelligence)

    assert result.engine_id == ENGINE_ID
    assert result.status == "certified"
    assert result.certified is True
    assert result.certification_level == "certified"
    assert result.intelligence_score == 0.64
    assert result.signal_count == 2
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-200"
    assert result.decisions[0].certified is True
    assert "READ_ONLY_ORACLE_CERTIFICATION" in result.decisions[0].reason_codes
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.decisions[0].reason_codes

def test_warning_signal_requires_review():
    intelligence = {
        "engine_id": "OI-200",
        "status": "review",
        "intelligence_score": 0.40,
        "signals": [
            {
                "signal_id": "SIG_WARNING",
                "category": "risk",
                "severity": "warning",
                "score": 0.35,
                "title": "Telemetry gap.",
                "explanation": "Read-only telemetry gap detected.",
                "recommendation": "Repair upstream telemetry.",
            }
        ],
    }

    result = certify_replay_recommendation_ranking_intelligence(intelligence)

    assert result.status == "review"
    assert result.certified is False
    assert result.certification_level == "review_required"
    assert result.signal_count == 1
    assert result.telemetry["warning_count"] == 1
    assert "WARNING_SIGNALS_PRESENT" in result.decisions[0].reason_codes


def test_empty_intelligence_is_safe_and_not_certified():
    result = UniversalMarketAdapterReplayRecommendationRankingCertificationEngine().certify(
        {
            "engine_id": "OI-200",
            "status": "review",
            "intelligence_score": 0.50,
            "signals": [],
        }
    )

    assert result.status == "review"
    assert result.certified is False
    assert result.certification_level == "review_required"
    assert result.signal_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True
    assert "NO_INTELLIGENCE_SIGNALS" in result.decisions[0].reason_codes


if __name__ == "__main__":
    test_certifies_good_intelligence_without_warning_signals()
    test_warning_signal_requires_review()
    test_empty_intelligence_is_safe_and_not_certified()

    print("[PASS] OI-201 Universal Market Adapter Replay Recommendation Ranking Certification Engine")
    print(
        certify_replay_recommendation_ranking_intelligence(
            {
                "engine_id": "OI-200",
                "status": "good",
                "intelligence_score": 0.64,
                "signals": [
                    {
                        "signal_id": "SIG_DEMO",
                        "category": "strength",
                        "severity": "positive",
                        "score": 0.90,
                        "title": "Demo replay ranking intelligence.",
                        "explanation": "Replay ranking intelligence is constructive.",
                        "recommendation": "Promote to read-only Oracle certification review.",
                    }
                ],
            }
        ).to_dict()
    )
