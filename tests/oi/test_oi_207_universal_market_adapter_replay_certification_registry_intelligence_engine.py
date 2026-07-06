from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_intelligence_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine,
    evaluate_replay_certification_registry_intelligence,
)


def test_positive_registry_analytics_produces_good_intelligence():
    analytics = {
        "engine_id": "OI-206",
        "findings": [
            {
                "finding_id": "OI206_CERTIFIED_COHORT_MAJORITY",
                "severity": "positive",
                "title": "Certified records are the majority.",
                "detail": "Most records are certified.",
                "recommendation": "Continue monitoring.",
            },
            {
                "finding_id": "OI206_REVIEW_STATUS_PRESENT",
                "severity": "info",
                "title": "Review records present.",
                "detail": "Some records require review.",
                "recommendation": "Inspect review records.",
            },
        ],
    }

    result = UniversalMarketAdapterReplayCertificationRegistryIntelligenceEngine().evaluate(analytics)

    assert result.engine_id == ENGINE_ID
    assert result.status == "good"
    assert result.intelligence_score == 0.64
    assert result.signal_count == 2
    assert result.signals[0].category == "strength"
    assert result.signals[1].category == "context"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert result.telemetry["input_engine_id"] == "OI-206"


def test_warning_registry_analytics_requires_review():
    result = evaluate_replay_certification_registry_intelligence(
        {
            "engine_id": "OI-206",
            "findings": [
                {
                    "finding_id": "OI206_WEAK_AVERAGE_CERTIFICATION_SCORE",
                    "severity": "warning",
                    "title": "Weak average score.",
                    "detail": "Average score is weak.",
                    "recommendation": "Hold for review.",
                }
            ],
        }
    )

    assert result.status == "review"
    assert result.intelligence_score == 0.38
    assert result.signal_count == 1
    assert result.signals[0].category == "risk"
    assert result.signals[0].severity == "warning"


def test_empty_analytics_is_safe_read_only():
    result = evaluate_replay_certification_registry_intelligence(
        {"engine_id": "OI-206", "findings": []}
    )

    assert result.status == "review"
    assert result.intelligence_score == 0.50
    assert result.signal_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_positive_registry_analytics_produces_good_intelligence()
    test_warning_registry_analytics_requires_review()
    test_empty_analytics_is_safe_read_only()

    print("[PASS] OI-207 Universal Market Adapter Replay Certification Registry Intelligence Engine")
    print(
        evaluate_replay_certification_registry_intelligence(
            {
                "engine_id": "OI-206",
                "findings": [
                    {
                        "finding_id": "DEMO_CERTIFIED_COHORT",
                        "severity": "positive",
                        "title": "Demo certified registry cohort.",
                        "detail": "The replay certification registry cohort is constructive.",
                        "recommendation": "Forward to read-only Oracle recommendation review.",
                    }
                ],
            }
        ).to_dict()
    )
