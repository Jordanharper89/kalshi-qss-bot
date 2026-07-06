from qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_lookup_engine import (
    READ_ONLY_GUARDRAILS,
    ReplayRegistryLookupEntry,
    ReplayRegistryLookupLoadResult,
    UniversalMarketAdapterReplayRegistryLookupEngine,
    create_replay_registry_lookup_engine,
)


def test_oi_191_replay_registry_lookup_engine():
    engine = create_replay_registry_lookup_engine("oracle.test")
    records = [
        {
            "registration_id": "reg-001", "registry_id": "registry-main", "certification_id": "cert-001",
            "validation_id": "val-001", "manifest_id": "manifest-001", "certification_hash": "a" * 64,
            "validation_hash": "b" * 64, "manifest_hash": "c" * 64, "chain_hash": "d" * 64,
            "registry_hash": "e" * 64, "adapter_id": "adp.kalshi", "market_id": "umm.market.001",
            "query_id": "query-001", "status": "registered", "certified": True,
            "certification_level": "certified", "telemetry": {"source": "unit_test"},
        },
        {
            "registration_id": "reg-002", "registry_id": "registry-main", "certification_id": "cert-002",
            "validation_id": "val-002", "manifest_id": "manifest-002", "adapter_id": "adp.kalshi",
            "market_id": "umm.market.002", "query_id": "query-002", "status": "registered",
            "certified": True, "certification_level": "certified_with_warnings",
        },
        {
            "registration_id": "reg-003", "registry_id": "registry-main", "certification_id": "cert-003",
            "validation_id": "val-003", "manifest_id": "manifest-003", "adapter_id": "adp.polymarket",
            "market_id": "umm.market.003", "query_id": "query-003", "status": "rejected",
            "certified": False, "certification_level": "not_certified",
        },
    ]
    load = engine.load_registry_records(records)
    assert isinstance(load, ReplayRegistryLookupLoadResult)
    assert load.module_id == "OI-191"
    assert load.entry_count == 3
    assert load.registration_id_count == 3
    assert load.certification_id_count == 3
    assert load.manifest_id_count == 3
    assert load.validation_id_count == 3
    assert load.adapter_id_count == 2
    assert load.market_id_count == 3
    assert load.query_id_count == 3
    assert len(load.integrity_hash) == 64
    assert load.read_only_guardrails == READ_ONLY_GUARDRAILS
    reg = engine.lookup_by_registration_id("reg-001")
    assert isinstance(reg, ReplayRegistryLookupEntry)
    assert reg.certification_id == "cert-001"
    assert reg.passed is True
    assert len(engine.lookup_by_registry_id("registry-main")) == 3
    assert len(engine.lookup_by_certification_id("cert-002")) == 1
    assert len(engine.lookup_by_validation_id("val-002")) == 1
    assert len(engine.lookup_by_manifest_id("manifest-003")) == 1
    assert len(engine.lookup_by_adapter_id("adp.kalshi")) == 2
    assert len(engine.lookup_by_adapter_id("adp.polymarket")) == 1
    assert len(engine.lookup_by_market_id("umm.market.002")) == 1
    assert len(engine.lookup_by_query_id("query-003")) == 1
    assert len(engine.lookup_by_status("registered")) == 2
    assert len(engine.lookup_by_status("rejected")) == 1
    assert len(engine.lookup_certified()) == 2
    assert len(engine.lookup_rejected()) == 1
    snapshot = engine.snapshot()
    assert snapshot.entry_count == 3
    assert snapshot.telemetry["certified_count"] == 2
    assert snapshot.telemetry["rejected_count"] == 1
    telemetry = engine.telemetry_snapshot()
    assert telemetry["entry_count"] == 3
    assert telemetry["certified_count"] == 2
    assert telemetry["read_only_guardrails"] == READ_ONLY_GUARDRAILS
    manifest = engine.replay_lookup_manifest()
    assert manifest["module_id"] == "OI-191"
    assert manifest["entry_count"] == 3
    assert len(manifest["entries"]) == 3

    class RegistryLike:
        def records(self):
            return records

    engine2 = UniversalMarketAdapterReplayRegistryLookupEngine("oracle.test2")
    load2 = engine2.load_from_registry_engine(RegistryLike())
    assert load2.entry_count == 3
    assert engine2.lookup_by_registration_id("reg-001").certification_id == "cert-001"


if __name__ == "__main__":
    test_oi_191_replay_registry_lookup_engine()
    print("[PASS] OI-191 Universal Market Adapter Replay Registry Lookup Engine")
