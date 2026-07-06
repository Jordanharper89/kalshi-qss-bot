
from qseries_v2.oracle_intelligence.universal_market_adapter_query_resolver_engine import (
    ENGINE_ID,
    Q_SERIES_EXECUTION_OWNER,
    AdapterQueryRequest,
    UniversalMarketAdapterQueryResolverEngine,
    architecture_contract,
    demo_index,
    resolve_queries,
    resolve_query,
    snapshot_to_json,
)


def test_query_resolver_candidate_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["candidate_id"] == "demo.prediction"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == Q_SERIES_EXECUTION_OWNER


def test_query_resolver_market_type_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="prediction_markets", query_type="market_type"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["market_type"] == "prediction_markets"


def test_query_resolver_namespace_lookup():
    result = resolve_query(
        demo_index(),
        AdapterQueryRequest(query="oracle.adapters.prediction_markets", query_type="namespace"),
        resolved_at=1760000000.0,
    )

    assert result.matched is True
    assert result.match_count == 1
    assert result.records[0]["registry_namespace"] == "oracle.adapters.prediction_markets"


def test_query_resolver_registry_and_lookup_key():
    index = demo_index()
    registry_id = list(index["records_by_registry_id"].keys())[0]
    lookup_key = list(index["registry_id_by_lookup_key"].keys())[0]

    by_registry = resolve_query(index, AdapterQueryRequest(query=registry_id, query_type="registry_id"), resolved_at=1760000000.0)
    by_lookup = resolve_query(index, AdapterQueryRequest(query=lookup_key, query_type="lookup_key"), resolved_at=1760000000.0)

    assert by_registry.matched is True
    assert by_lookup.matched is True
    assert by_registry.records[0]["registry_id"] == by_lookup.records[0]["registry_id"]


def test_query_resolver_snapshot_contract():
    snapshot = resolve_queries(
        demo_index(),
        (
            AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),
            AdapterQueryRequest(query="missing", query_type="candidate_id"),
        ),
        resolved_at=1760000000.0,
    )

    assert snapshot.engine_id == ENGINE_ID
    assert snapshot.query_count == 2
    assert snapshot.matched_query_count == 1
    assert snapshot.architecture["oracle_mode"] == "read_only"
    assert snapshot.architecture["execution_owner"] == Q_SERIES_EXECUTION_OWNER
    assert snapshot.replay_hash


def test_engine_history_and_json():
    engine = UniversalMarketAdapterQueryResolverEngine()
    snapshot = engine.resolve_many(
        demo_index(),
        (AdapterQueryRequest(query="prediction", query_type="generic"),),
        resolved_at=1760000000.0,
    )

    assert engine.latest_snapshot() == snapshot
    assert len(engine.history()) == 1

    text = snapshot_to_json(snapshot)
    assert "Oracle Universal Market Adapter Query Resolver Engine" in text
    assert "read_only" in text


def test_architecture_contract():
    contract = architecture_contract()

    assert contract["oracle_mode"] == "read_only"
    assert contract["universal_market_model"] is True
    assert contract["adapter_based_expansion"] is True
    assert contract["explainability_by_default"] is True
    assert contract["replayability_by_default"] is True
    assert contract["institutional_telemetry"] is True
    assert contract["adapter_query_resolver_ready"] is True
    assert contract["execution_owner"] == Q_SERIES_EXECUTION_OWNER


if __name__ == "__main__":
    test_query_resolver_candidate_lookup()
    test_query_resolver_market_type_lookup()
    test_query_resolver_namespace_lookup()
    test_query_resolver_registry_and_lookup_key()
    test_query_resolver_snapshot_contract()
    test_engine_history_and_json()
    test_architecture_contract()
    print("[PASS] OI-184 Universal Market Adapter Query Resolver Engine")
    print(resolve_queries(demo_index(), (AdapterQueryRequest(query="demo.prediction", query_type="candidate_id"),), resolved_at=1760000000.0).to_dict())
