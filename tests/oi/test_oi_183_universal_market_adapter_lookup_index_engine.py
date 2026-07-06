
from qseries_v2.oracle_intelligence.universal_market_adapter_lookup_index_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterLookupIndexRecord,
    UniversalMarketAdapterLookupIndexEngine,
    architecture_contract,
    build_lookup_index,
    demo_records,
    index_to_json,
    record_from_availability_decision,
)


def test_lookup_index_contract():
    index = build_lookup_index(demo_records(), indexed_at=1760000000.0)

    assert index.engine_id == ENGINE_ID
    assert index.record_count == 1
    assert index.available_count == 1
    assert index.architecture["oracle_mode"] == "read_only"
    assert index.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert index.replay_hash


def test_lookup_methods_work():
    index = build_lookup_index(demo_records(), indexed_at=1760000000.0)
    record = demo_records()[0]

    assert index.get_by_registry_id(record.registry_id)["candidate_id"] == "demo.prediction"
    assert index.get_by_lookup_key(record.lookup_key)["registry_id"] == record.registry_id
    assert index.get_by_candidate_id("demo.prediction")["name"] == "Demo Prediction Lookup Record"
    assert len(index.list_market_type("prediction_markets")) == 1
    assert len(index.list_namespace("oracle.adapters.prediction_markets")) == 1


def test_non_indexable_record_is_excluded():
    weak = AdapterLookupIndexRecord(
        registry_id="",
        candidate_id="weak.adapter",
        name="Weak Adapter Lookup Record",
        market_type="unknown",
        source_kind="manual_note",
        registry_namespace="",
        registry_version="",
        registry_owner="",
        availability_status="not_available",
        availability_score=0.0,
        availability_hash="",
        replay_hash="",
        lookup_key="",
        available=False,
        read_only=True,
        execution_owner=Q_SERIES_EXECUTION_OWNER,
    )

    index = build_lookup_index([weak], indexed_at=1760000000.0)

    assert index.record_count == 0
    assert index.available_count == 0
    assert index.get_by_candidate_id("weak.adapter") is None


def test_record_from_availability_decision_mapping():
    availability_decision = {
        "record": {
            "registry_id": "oracle.adapters.weather.weather.promoted.weather.v1.0.0",
            "candidate_id": "promoted.weather",
            "name": "Promoted Weather Lookup Record",
            "market_type": "weather",
            "source_kind": "registry_item",
            "registry_namespace": "oracle.adapters.weather",
            "registry_version": "1.0.0",
            "registry_owner": "oracle_intelligence",
            "replay_hash": "weather-replay-hash",
            "metadata": {"fixture": True},
        },
        "available": True,
        "availability_status": "available_for_oracle_lookup",
        "availability_score": 0.95,
        "availability_hash": "weather-availability-hash",
        "explanation": {
            "lookup_key": "weather::oracle.adapters.weather::oracle.adapters.weather.weather.promoted.weather.v1.0.0"
        },
        "telemetry": {
            "available": True,
            "availability_status": "available_for_oracle_lookup",
            "availability_score": 0.95,
            "lookup_key": "weather::oracle.adapters.weather::oracle.adapters.weather.weather.promoted.weather.v1.0.0",
            "read_only": True,
            "execution_owner": Q_SERIES_EXECUTION_OWNER,
        },
    }

    record = record_from_availability_decision(availability_decision)
    index = build_lookup_index([record], indexed_at=1760000000.0)

    assert record.candidate_id == "promoted.weather"
    assert index.record_count == 1
    assert index.get_by_candidate_id("promoted.weather")["market_type"] == "weather"


def test_engine_history_and_json():
    engine = UniversalMarketAdapterLookupIndexEngine()
    index = engine.build(demo_records(), indexed_at=1760000000.0)

    assert engine.latest_index() == index
    assert len(engine.history()) == 1

    text = index_to_json(index)
    assert "oi.183.universal_market_adapter_lookup_index" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_lookup_index_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_lookup_index_contract()
    test_lookup_methods_work()
    test_non_indexable_record_is_excluded()
    test_record_from_availability_decision_mapping()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-183 Universal Market Adapter Lookup Index Engine")
    print(build_lookup_index(demo_records(), indexed_at=1760000000.0).to_dict())
