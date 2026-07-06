
from qseries_v2.oracle_intelligence.universal_market_adapter_registry_validation_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterRegistryValidationRecord,
    UniversalMarketAdapterRegistryValidationEngine,
    architecture_contract,
    demo_records,
    record_from_enrollment_record,
    snapshot_to_json,
    validate_records,
)


def test_validation_snapshot_contract():
    snapshot = validate_records(demo_records(), validated_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.valid_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_valid_record_passes_core_gates():
    snapshot = validate_records(demo_records(), validated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.valid is True
    assert decision.validation_status == "validated_registry_available"
    assert decision.gates["read_only_boundary_validated"] is True
    assert decision.gates["q_series_execution_boundary_validated"] is True
    assert decision.gates["registry_id_validated"] is True
    assert decision.gates["namespace_validated"] is True
    assert decision.explanation["q_series_boundary"] == "Q Series remains the sole execution owner."


def test_invalid_record_has_blockers():
    weak = AdapterRegistryValidationRecord(
        registry_id="",
        candidate_id="weak.adapter",
        name="Weak Adapter Record",
        market_type="unknown",
        source_kind="manual_note",
        registry_namespace="",
        registry_version="",
        registry_owner="",
        enrollment_status="not_enrolled",
        enrollment_score=0.0,
        promotion_hash="",
        replay_hash="",
        enrollment_hash="",
        enrolled_at=1760000000.0,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    snapshot = validate_records([weak], validated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.valid is False
    assert decision.validation_status == "not_validated"
    assert "registry_id_validated" in decision.blockers
    assert "namespace_validated" in decision.blockers
    assert "version_validated" in decision.blockers
    assert "owner_validated" in decision.blockers


def test_record_from_enrollment_record_mapping():
    enrollment_record = {
        "registry_id": "oracle.adapters.weather.weather.promoted.weather.v1.0.0",
        "candidate_id": "promoted.weather",
        "name": "Promoted Weather Registry Record",
        "market_type": "weather",
        "source_kind": "registry_item",
        "registry_namespace": "oracle.adapters.weather",
        "registry_version": "1.0.0",
        "registry_owner": "oracle_intelligence",
        "enrollment_status": "enrolled_registry_ready",
        "enrollment_score": 0.94,
        "promotion_hash": "weather-promotion-hash",
        "replay_hash": "weather-replay-hash",
        "enrollment_hash": "weather-enrollment-hash-123456789",
        "enrolled_at": 1760000000.0,
        "read_only": True,
        "execution_owner": Q_SERIES_EXECUTION_OWNER,
    }

    record = record_from_enrollment_record(enrollment_record)
    snapshot = validate_records([record], validated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert record.candidate_id == "promoted.weather"
    assert decision.valid is True
    assert decision.gates["enrollment_hash_validated"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterRegistryValidationEngine()
    snapshot = engine.validate(demo_records(), validated_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Registry Validation Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_registry_validation_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_validation_snapshot_contract()
    test_valid_record_passes_core_gates()
    test_invalid_record_has_blockers()
    test_record_from_enrollment_record_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-181 Universal Market Adapter Registry Validation Engine")
    print(validate_records(demo_records(), validated_at=1760000000.0).to_dict())
