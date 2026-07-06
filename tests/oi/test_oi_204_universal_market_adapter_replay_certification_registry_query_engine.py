from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_query_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryQueryEngine,
    query_replay_certification_registry,
)


def sample_registry():
    return {
        "engine_id": "OI-203",
        "records": [
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
                "certified": False,
                "certification_level": "review_required",
                "status": "review",
                "intelligence_score": 0.40,
                "signal_count": 1,
                "decision_count": 1,
                "reason_codes": ["WARNING_SIGNALS_PRESENT"],
                "explanation": "Review sample.",
            },
        ],
    }


def test_query_by_registry_id():
    result = UniversalMarketAdapterReplayCertificationRegistryQueryEngine().query(
        sample_registry(),
        registry_id="rec-1",
    )

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 2
    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-1"
    assert result.matches[0].certified is True
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_query_by_level_and_score_range():
    result = query_replay_certification_registry(
        sample_registry(),
        certification_level="certified",
        min_intelligence_score=0.60,
    )

    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-1"
    assert result.matches[0].intelligence_score == 0.64


def test_query_by_reason_code_and_limit():
    result = query_replay_certification_registry(
        sample_registry(),
        reason_code="WARNING_SIGNALS_PRESENT",
        limit=1,
    )

    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[0].status == "review"


def test_empty_query_is_safe_read_only():
    result = query_replay_certification_registry(sample_registry(), status="missing")

    assert result.status == "empty"
    assert result.match_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_query_by_registry_id()
    test_query_by_level_and_score_range()
    test_query_by_reason_code_and_limit()
    test_empty_query_is_safe_read_only()

    print("[PASS] OI-204 Universal Market Adapter Replay Certification Registry Query Engine")
    print(query_replay_certification_registry(sample_registry(), certified=True).to_dict())
