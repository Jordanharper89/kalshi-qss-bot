from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryEngine,
    register_replay_certifications,
)


def sample_certification():
    return {
        "engine_id": "OI-201",
        "status": "certified",
        "certified": True,
        "certification_level": "certified",
        "intelligence_score": 0.64,
        "signal_count": 1,
        "decisions": [
            {
                "decision_id": "D1",
                "certified": True,
                "certification_level": "certified",
                "confidence": 0.64,
                "reason_codes": [
                    "READ_ONLY_ORACLE_CERTIFICATION",
                    "Q_SERIES_EXECUTION_REQUIRED",
                    "PASSING_INTELLIGENCE_SCORE",
                ],
            }
        ],
        "telemetry": {"read_only": True, "execution_owner": "Q Series"},
        "explanation": "Demo certification.",
    }


def test_registers_valid_certification():
    result = UniversalMarketAdapterReplayCertificationRegistryEngine().register(sample_certification())

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.registered_count == 1
    assert result.rejected_count == 0
    assert result.duplicate_count == 0
    assert result.records[0].source_engine_id == "OI-201"
    assert result.records[0].certified is True
    assert result.records[0].certification_level == "certified"
    assert "READ_ONLY_ORACLE_CERTIFICATION" in result.records[0].reason_codes
    assert "Q_SERIES_EXECUTION_REQUIRED" in result.records[0].reason_codes
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_duplicate_certifications_are_ignored():
    cert = sample_certification()
    result = register_replay_certifications([cert, cert])

    assert result.registered_count == 1
    assert result.duplicate_count == 1
    assert result.rejected_count == 0


def test_distinct_certifications_both_register():
    cert_one = sample_certification()
    cert_two = sample_certification()
    cert_two["intelligence_score"] = 0.82
    cert_two["certification_level"] = "strong_certified"

    result = register_replay_certifications([cert_one, cert_two])

    assert result.registered_count == 2
    assert result.duplicate_count == 0
    assert result.rejected_count == 0
    assert result.records[0].registry_id != result.records[1].registry_id


def test_invalid_certification_is_rejected_safely():
    result = register_replay_certifications([{"engine_id": "BAD"}])

    assert result.status == "empty"
    assert result.registered_count == 0
    assert result.rejected_count == 1
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_registers_valid_certification()
    test_duplicate_certifications_are_ignored()
    test_distinct_certifications_both_register()
    test_invalid_certification_is_rejected_safely()

    print("[PASS] OI-203 Universal Market Adapter Replay Certification Registry Engine")
    print(register_replay_certifications(sample_certification()).to_dict())
