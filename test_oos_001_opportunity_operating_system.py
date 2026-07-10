from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.opportunity_operating_system import (
    OOS_VERSION,
    OpportunityOperatingSystem,
    build_oos,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    UniversalOpportunityFactory,
)


def _market():
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity():
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is above market ask.",
        liquidity_score=0.76,
        risk_score=0.31,
    )


def test_oos_001_intake_registers_opportunity():
    oos = build_oos()
    opportunity = _opportunity()

    result = oos.intake(opportunity, source="test")

    assert result.status == "registered"
    assert result.duplicate is False
    assert result.fingerprint == opportunity.fingerprint()
    assert len(oos.all_records()) == 1

    record = oos.get(result.fingerprint)
    assert record is not None
    assert record.opportunity == opportunity
    assert record.status == "new"
    assert record.read_only is True


def test_oos_001_duplicate_detection():
    oos = build_oos()
    opportunity = _opportunity()

    first = oos.intake(opportunity, source="engine_a")
    second = oos.intake(opportunity, source="engine_b")

    assert first.status == "registered"
    assert second.status == "duplicate"
    assert second.duplicate is True
    assert second.duplicate_count == 1
    assert len(oos.all_records()) == 1

    record = oos.get(first.fingerprint)
    assert record.duplicate_count == 1
    assert record.metadata["last_duplicate_source"] == "engine_b"


def test_oos_001_lifecycle_transitions():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    verified = oos.transition(result.fingerprint, "verified", reason="evidence_confirmed")
    ranked = oos.transition(result.fingerprint, "ranked", reason="quality_scored")
    assigned = oos.transition(result.fingerprint, "assigned", reason="decision_layer_candidate")
    executed = oos.transition(result.fingerprint, "executed", reason="q_series_ack")
    archived = oos.transition(result.fingerprint, "archived", reason="settled_reviewed")

    assert verified.status == "verified"
    assert ranked.status == "ranked"
    assert assigned.status == "assigned"
    assert executed.status == "executed"
    assert archived.status == "archived"
    assert len(archived.lifecycle) == 5
    assert archived.lifecycle[0].from_status == "new"
    assert archived.lifecycle[-1].to_status == "archived"


def test_oos_001_invalid_transition_is_blocked():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    try:
        oos.transition(result.fingerprint, "executed", reason="skip_attempt")
        raise AssertionError("Invalid lifecycle transition should fail.")
    except ValueError:
        pass


def test_oos_001_lookup_remove_and_active_archived_records():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    by_id = oos.get_by_opportunity_id(opportunity.opportunity_id)
    assert by_id is not None
    assert by_id.fingerprint == result.fingerprint

    assert len(oos.active_records()) == 1

    oos.transition(result.fingerprint, "verified")
    oos.transition(result.fingerprint, "ranked")
    oos.transition(result.fingerprint, "assigned")
    oos.transition(result.fingerprint, "executed")
    oos.transition(result.fingerprint, "archived")

    assert len(oos.active_records()) == 0
    assert len(oos.archived_records()) == 1

    removed = oos.remove(result.fingerprint)
    assert removed is not None
    assert len(oos.all_records()) == 0


def test_oos_001_telemetry_and_serialization():
    oos = build_oos()
    opportunity = _opportunity()

    result = oos.intake(opportunity)
    oos.intake(opportunity)
    oos.transition(result.fingerprint, "verified", reason="verified_for_test")

    telemetry = oos.telemetry()
    data = oos.to_dict()

    assert telemetry.total_registered == 1
    assert telemetry.active_count == 1
    assert telemetry.duplicate_count == 1
    assert telemetry.lifecycle_event_count == 1
    assert telemetry.average_quality > 0
    assert telemetry.schema_version == OOS_VERSION
    assert telemetry.read_only is True

    assert data["schema_version"] == OOS_VERSION
    assert data["read_only"] is True
    assert len(data["records"]) == 1
    assert data["records"][0]["opportunity"]["read_only"] is True


def test_oos_001_record_immutability():
    oos = OpportunityOperatingSystem()
    result = oos.intake(_opportunity())
    record = oos.get(result.fingerprint)

    try:
        record.status = "executed"
        raise AssertionError("OpportunityRecord should be immutable.")
    except FrozenInstanceError:
        pass


def test_oos_001_rejects_non_read_only_objects():
    class BadOpportunity:
        read_only = False

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    oos = build_oos()

    try:
        oos.intake(BadOpportunity())
        raise AssertionError("Non-read-only opportunity should be rejected.")
    except ValueError:
        pass


if __name__ == "__main__":
    test_oos_001_intake_registers_opportunity()
    test_oos_001_duplicate_detection()
    test_oos_001_lifecycle_transitions()
    test_oos_001_invalid_transition_is_blocked()
    test_oos_001_lookup_remove_and_active_archived_records()
    test_oos_001_telemetry_and_serialization()
    test_oos_001_record_immutability()
    test_oos_001_rejects_non_read_only_objects()

    oos = build_oos()
    opportunity = _opportunity()
    intake = oos.intake(opportunity)
    oos.intake(opportunity)
    oos.transition(intake.fingerprint, "verified", reason="test_verified")
    telemetry = oos.telemetry()

    print("[PASS] OOS-001 Opportunity Operating System")
    print(
        {
            "schema_version": telemetry.schema_version,
            "total_registered": telemetry.total_registered,
            "active_count": telemetry.active_count,
            "duplicate_count": telemetry.duplicate_count,
            "lifecycle_event_count": telemetry.lifecycle_event_count,
            "read_only": telemetry.read_only,
        }
    )
