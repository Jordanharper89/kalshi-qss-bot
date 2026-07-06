from qseries_v2.oracle_intelligence.universal_market_adapter_replay_recommendation_engine import (
    READ_ONLY_GUARDRAILS,
    create_replay_recommendation_engine,
)


def as_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return dict(obj)


def test_oi_197_replay_recommendation_engine():
    engine = create_replay_recommendation_engine("oracle.test")

    records = [
        {
            "registration_id": "reg-001",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "certified": True,
            "certification_level": "certified",
            "confidence": 0.91,
        },
        {
            "registration_id": "reg-002",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "certified": True,
            "certification_level": "certified_with_warnings",
            "confidence": 0.74,
        },
        {
            "registration_id": "reg-003",
            "adapter_id": "adp.polymarket",
            "market_type": "prediction_market",
            "certified": False,
            "certification_level": "not_certified",
            "confidence": 0.42,
        },
    ]

    result = engine.recommend(records, context={"gate": "unit"})
    data = as_dict(result)

    assert data["module_id"] == "OI-197"
    assert data["passed"] is True
    assert data["status"] == "ok"
    assert data["record_count"] >= 1
    assert data["read_only_guardrails"] == READ_ONLY_GUARDRAILS
    assert data["read_only_guardrails"]["execution_owner"] == "Q_SERIES_ONLY"

    recommendation_types = {record["recommendation_type"] for record in data["records"]}
    assert "high_confidence_replay_review" in recommendation_types
    assert "certified_replay_baseline" in recommendation_types

    latest = engine.latest_report()
    assert latest is not None
    assert len(engine.reports()) == 1

    empty = engine.recommend([])
    empty_data = as_dict(empty)
    assert empty_data["passed"] is True
    assert empty_data["record_count"] == 1
    assert empty_data["records"][0]["recommendation_type"] == "operator_review"

    snapshot = engine.telemetry_snapshot()
    assert snapshot["module_id"] == "OI-197"
    assert snapshot["report_count"] == 2
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS


if __name__ == "__main__":
    test_oi_197_replay_recommendation_engine()
    print("[PASS] OI-197 Universal Market Adapter Replay Recommendation Engine")
