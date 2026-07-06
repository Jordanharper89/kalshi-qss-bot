from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_filter_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryFilterEngine,
    filter_replay_certification_registry,
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
            "explanation": "Certified sample.",
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
            "explanation": "Strong certified sample.",
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
            "explanation": "Review sample.",
        },
    ]


def test_filters_by_min_score_and_certified():
    result = UniversalMarketAdapterReplayCertificationRegistryFilterEngine().filter(
        {"records": sample_records()},
        min_intelligence_score=0.60,
        certified=True,
    )

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 3
    assert result.filtered_count == 2
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[1].registry_id == "rec-1"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_filters_by_required_reason_code():
    result = filter_replay_certification_registry(
        sample_records(),
        required_reason_codes=["WARNING_SIGNALS_PRESENT"],
    )

    assert result.filtered_count == 1
    assert result.matches[0].registry_id == "rec-3"
    assert result.matches[0].status == "review"


def test_filters_by_min_certification_level_and_limit():
    result = filter_replay_certification_registry(
        sample_records(),
        min_certification_level="certified",
        sort_by="certification_level",
        descending=True,
        limit=1,
    )

    assert result.filtered_count == 1
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[0].certification_level == "strong_certified"


def test_empty_filter_result_is_safe_read_only():
    result = filter_replay_certification_registry(
        sample_records(),
        min_intelligence_score=0.99,
    )

    assert result.status == "empty"
    assert result.filtered_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_filters_by_min_score_and_certified()
    test_filters_by_required_reason_code()
    test_filters_by_min_certification_level_and_limit()
    test_empty_filter_result_is_safe_read_only()

    print("[PASS] OI-205 Universal Market Adapter Replay Certification Registry Filter Engine")
    print(filter_replay_certification_registry(sample_records(), min_intelligence_score=0.60).to_dict())
