from qseries_v2.oracle_intelligence.universal_market_adapter_replay_registry_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterReplayRegistryEngine,
    create_replay_registry_engine,
)


def test_oi_190_universal_market_adapter_replay_registry_engine():
    engine = create_replay_registry_engine("oracle.test")

    certification = {
        "certification_id": "cert-001",
        "certification_hash": "a" * 64,
        "certified": True,
        "manifest_id": "manifest-001",
        "manifest_hash": "b" * 64,
        "validation_id": "validation-001",
        "validation_hash": "c" * 64,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
    }
    manifest = {
        "manifest_id": "manifest-001",
        "manifest_hash": "b" * 64,
        "entries": [
            {
                "adapter_id": "adp.kalshi",
                "query_id": "q-001",
                "replay_key": "replay-001",
            },
            {
                "adapter_id": "adp.polymarket",
                "query_id": "q-002",
                "replay_key": "replay-002",
            },
        ],
    }
    validation = {
        "validation_id": "validation-001",
        "validation_hash": "c" * 64,
        "passed": True,
    }

    record = engine.register_certified_replay(
        certification=certification,
        manifest=manifest,
        validation=validation,
    )

    assert record.passed is True
    assert record.certified is True
    assert record.manifest_id == "manifest-001"
    assert record.certification_id == "cert-001"
    assert record.validation_id == "validation-001"
    assert record.entry_count == 2
    assert record.adapter_ids == ["adp.kalshi", "adp.polymarket"]
    assert record.query_ids == ["q-001", "q-002"]
    assert record.replay_keys == ["replay-001", "replay-002"]
    assert len(record.registry_hash) == 64
    assert len(record.lineage_hash) == 64
    assert record.read_only_guardrails == READ_ONLY_GUARDRAILS

    assert engine.lookup_by_registry_id(record.registry_id).manifest_id == "manifest-001"
    assert engine.lookup_by_manifest_id("manifest-001").registry_id == record.registry_id
    assert engine.lookup_by_certification_id("cert-001").registry_id == record.registry_id
    assert engine.lookup_by_validation_id("validation-001").registry_id == record.registry_id
    assert engine.lookup_by_adapter_id("adp.kalshi")[0].registry_id == record.registry_id
    assert engine.lookup_by_query_id("q-002")[0].registry_id == record.registry_id
    assert engine.lookup_by_replay_key("replay-001")[0].registry_id == record.registry_id

    bad = engine.register_certified_replay(
        certification={
            "certification_id": "cert-002",
            "certified": False,
            "manifest_id": "manifest-002",
            "manifest_hash": "bad-hash",
            "read_only_guardrails": {
                "oracle_read_only": False,
                "executes_trades": True,
                "routes_orders": True,
                "submits_orders": True,
                "manages_positions": True,
                "execution_owner": "ORACLE",
            },
        },
        manifest={
            "manifest_id": "manifest-002",
            "manifest_hash": "bad-hash",
            "entries": [
                {"adapter_id": "adp.bad", "query_id": "q-bad", "replay_key": "replay-bad"}
            ],
        },
        context={"submit_order": True},
    )
    codes = {finding.code for finding in bad.findings}
    assert bad.passed is False
    assert "CERTIFICATION_NOT_PASSED" in codes
    assert "MANIFEST_HASH_INVALID" in codes
    assert "READ_ONLY_GUARDRAIL_MISMATCH" in codes
    assert "EXECUTION_LANGUAGE_DETECTED" in codes

    snapshot = engine.snapshot()
    assert snapshot.module_id == "OI-190"
    assert snapshot.record_count == 2
    assert snapshot.certified_count == 1
    assert snapshot.failed_count == 1
    assert snapshot.adapter_count == 3
    assert snapshot.query_count == 3
    assert snapshot.replay_key_count == 3
    assert len(snapshot.registry_integrity_hash) == 64
    assert snapshot.read_only_guardrails == READ_ONLY_GUARDRAILS

    telemetry = engine.telemetry_snapshot()
    assert telemetry["record_count"] == 2
    assert telemetry["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest_out = engine.replay_registry_manifest()
    assert manifest_out["module_id"] == "OI-190"
    assert manifest_out["record_count"] == 2
    assert len(manifest_out["records"]) == 2

    integrity = engine.verify_registry_integrity()
    assert integrity["verified"] is True
    assert integrity["broken_registry_ids"] == []

    batch = engine.register_many([
        {
            "certification": {
                "certification_id": "cert-003",
                "certified": True,
                "manifest_id": "manifest-003",
                "manifest_hash": "d" * 64,
                "read_only_guardrails": READ_ONLY_GUARDRAILS,
                "replay_keys": ["replay-003"],
                "adapter_ids": ["adp.batch"],
                "query_ids": ["q-003"],
            }
        }
    ])
    assert len(batch) == 1
    assert batch[0].certification_id == "cert-003"
    assert engine.lookup_by_replay_key("replay-003")[0].certification_id == "cert-003"

    empty = UniversalMarketAdapterReplayRegistryEngine("oracle.empty")
    assert empty.snapshot().record_count == 0


if __name__ == "__main__":
    test_oi_190_universal_market_adapter_replay_registry_engine()
    print("[PASS] OI-190 Universal Market Adapter Replay Registry Engine")
