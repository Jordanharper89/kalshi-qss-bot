from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_analytics_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine,
    analyze_replay_certification_registry,
)


def sample_records():
    return [
        {
            "registry_id": "rec-1",
            "source_engine_id": "OI-201",
            "certified": True,
            "certification_level": "certified",
            "status": "certified",
            "intelligence_score": 0.64,
            "signal_count": 1,
            "decision_count": 1,
            "reason_codes": ["READ_ONLY_ORACLE_CERTIFICATION", "Q_SERIES_EXECUTION_REQUIRED"],
        },
        {
            "registry_id": "rec-2",
            "source_engine_id": "OI-201",
            "certified": True,
            "certification_level": "strong_certified",
            "status": "certified",
            "intelligence_score": 0.88,
            "signal_count": 3,
            "decision_count": 2,
            "reason_codes": ["READ_ONLY_ORACLE_CERTIFICATION", "STRONG_INTELLIGENCE_SCORE"],
        },
        {
            "registry_id": "rec-3",
            "source_engine_id": "OI-201",
            "certified": False,
            "certification_level": "review_required",
            "status": "review",
            "intelligence_score": 0.40,
            "signal_count": 1,
            "decision_count": 1,
            "reason_codes": ["WARNING_SIGNALS_PRESENT"],
        },
    ]


def test_analyzes_registry_records():
    result = UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine().analyze(
        {"records": sample_records()}
    )

    assert result.engine_id == ENGINE_ID
    assert result.input_count == 3
    assert result.analyzed_count == 3
    assert result.score_summary["mean"] == 0.64
    assert result.level_distribution["certified"] == 1
    assert result.level_distribution["strong_certified"] == 1
    assert result.status_distribution["review"] == 1
    assert result.reason_code_distribution["READ_ONLY_ORACLE_CERTIFICATION"] == 2
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_analyzes_filter_matches_payload():
    result = analyze_replay_certification_registry({"matches": sample_records()[:2]})

    assert result.status == "ok"
    assert result.input_count == 2
    assert result.analyzed_count == 2
    assert result.score_summary["mean"] == 0.76
    assert any(f.finding_id == "OI206_STRONG_AVERAGE_CERTIFICATION_SCORE" for f in result.findings)


def test_empty_input_is_safe_read_only():
    result = analyze_replay_certification_registry([])

    assert result.status == "empty"
    assert result.input_count == 0
    assert result.analyzed_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True
    assert result.findings[0].finding_id == "OI206_EMPTY_REGISTRY_ANALYTICS"


if __name__ == "__main__":
    test_analyzes_registry_records()
    test_analyzes_filter_matches_payload()
    test_empty_input_is_safe_read_only()

    print("[PASS] OI-206 Universal Market Adapter Replay Certification Registry Analytics Engine")
    print(analyze_replay_certification_registry({"records": sample_records()}).to_dict())
