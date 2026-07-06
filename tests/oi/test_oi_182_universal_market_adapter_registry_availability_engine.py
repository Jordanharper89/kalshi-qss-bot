
from qseries_v2.oracle_intelligence.universal_market_adapter_registry_availability_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterRegistryAvailabilityRecord,
    UniversalMarketAdapterRegistryAvailabilityEngine,
    architecture_contract,
    demo_records,
    evaluate_records,
    record_from_validation_decision,
    snapshot_to_json,
)


def test_availability_snapshot_contract():
    snapshot = evaluate_records(demo_records(), evaluated_at=1760000000.0)

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.decision_count == 2
    assert snapshot.available_count == 1
    assert len(snapshot.lookup_index) == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_available_record_passes_core_gates():
    snapshot = evaluate_records(demo_records(), evaluated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.available is True
    assert decision.availability_status == "available_for_oracle_lookup"
    assert decision.gates["read_only_boundary_available"] is True
    assert decision.gates["q_series_execution_boundary_available"] is True
    assert decision.gates["validation_status_available"] is True
    assert decision.gates["lookup_namespace_available"] is True
    assert decision.explanation["q_series_boundary"] == "Q Series remains the sole execution owner."


def test_unavailable_record_has_blockers():
    weak = AdapterRegistryAvailabilityRecord(
        registry_id="",
        candidate_id="weak.adapter",
        name="Weak Adapter Availability Record",
        market_type="unknown",
        source_kind="manual_note",
        registry_namespace="",
        registry_version="",
        registry_owner="",
        validation_status="not_validated",
        validation_score=0.10,
        validation_hash="",
        replay_hash="",
        telemetry_ready=False,
        enabled_for_lookup=False,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    snapshot = evaluate_records([weak], evaluated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert decision.available is False
    assert decision.availability_status == "not_available"
    assert "validation_status_available" in decision.blockers
    assert "registry_identity_available" in decision.blockers
    assert "lookup_namespace_available" in decision.blockers


def test_record_from_validation_decision_mapping():
    validation_decision = {
        "record": {
            "registry_id": "oracle.adapters.weather.weather.promoted.weather.v1.0.0",
            "candidate_id": "promoted.weather",
            "name": "Promoted Weather Registry Record",
            "market_type": "weather",
            "source_kind": "registry_item",
            "registry_namespace": "oracle.adapters.weather",
            "registry_version": "1.0.0",
            "registry_owner": "oracle_intelligence",
            "replay_hash": "weather-replay-hash",
            "metadata": {"fixture": True},
        },
        "valid": True,
        "validation_status": "validated_registry_available",
        "validation_score": 0.95,
        "validation_hash": "weather-validation-hash-123456789",
        "telemetry": {
            "valid": True,
            "validation_status": "validated_registry_available",
            "validation_score": 0.95,
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
    }

    record = record_from_validation_decision(validation_decision)
    snapshot = evaluate_records([record], evaluated_at=1760000000.0)
    decision = snapshot.decisions[0]

    assert record.candidate_id == "promoted.weather"
    assert decision.available is True
    assert decision.gates["validation_hash_available"] is True


def test_engine_history_and_json():
    engine = UniversalMarketAdapterRegistryAvailabilityEngine()
    snapshot = engine.evaluate(demo_records(), evaluated_at=1760000000.0)

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Registry Availability Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_registry_availability_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_availability_snapshot_contract()
    test_available_record_passes_core_gates()
    test_unavailable_record_has_blockers()
    test_record_from_validation_decision_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-182 Universal Market Adapter Registry Availability Engine")
    print(evaluate_records(demo_records(), evaluated_at=1760000000.0).to_dict())
