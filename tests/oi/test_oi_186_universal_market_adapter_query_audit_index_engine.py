from qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_index_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryAuditIndexEngine,
    create_query_audit_index_engine,
)


def test_oi_186_query_audit_index_engine():
    engine = create_query_audit_index_engine("oracle.test")

    records = [
        {
            "audit_id": "audit-001",
            "created_at": "2026-01-01T00:00:00+00:00",
            "adapter_id": "adp.kalshi",
            "query_id": "q-001",
            "replay_key": "replay-001",
            "passed": True,
            "query_hash": "a" * 64,
            "resolver_hash": "b" * 64,
            "market_model_hash": "c" * 64,
            "findings": [],
        },
        {
            "audit_id": "audit-002",
            "created_at": "2026-01-01T00:01:00+00:00",
            "adapter_id": "adp.kalshi",
            "query_id": "q-002",
            "replay_key": "replay-002",
            "passed": False,
            "query_hash": "d" * 64,
            "resolver_hash": "e" * 64,
            "market_model_hash": "f" * 64,
            "findings": [
                {
                    "code": "EXECUTION_BOUNDARY_VIOLATION",
                    "severity": "critical",
                    "message": "Execution boundary crossed.",
                }
            ],
        },
        {
            "audit_id": "audit-003",
            "created_at": "2026-01-01T00:02:00+00:00",
            "adapter_id": "adp.polymarket",
            "query_id": "q-001",
            "replay_key": "replay-003",
            "passed": True,
            "query_hash": "g" * 64,
            "resolver_hash": "h" * 64,
            "market_model_hash": "i" * 64,
            "findings": [
                {
                    "code": "TELEMETRY_MINIMAL",
                    "severity": "info",
                    "message": "Minimal telemetry.",
                }
            ],
        },
    ]

    summary = engine.index_records(records)

    assert summary.entry_count == 3
    assert summary.passed_count == 2
    assert summary.failed_count == 1
    assert summary.adapter_count == 2
    assert summary.query_count == 2
    assert summary.replay_key_count == 3
    assert len(summary.integrity_hash) == 64
    assert summary.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert summary.telemetry["oracle_instance_id"] == "oracle.test"

    assert engine.lookup_by_audit_id("audit-001").query_id == "q-001"
    assert engine.lookup_by_replay_key("replay-002").audit_id == "audit-002"
    assert len(engine.lookup_by_adapter("adp.kalshi")) == 2
    assert len(engine.lookup_by_query("q-001")) == 2
    assert len(engine.lookup_failed()) == 1
    assert len(engine.lookup_passed()) == 2

    boundary = engine.lookup_by_finding_code("EXECUTION_BOUNDARY_VIOLATION")
    assert len(boundary) == 1
    assert boundary[0].audit_id == "audit-002"

    manifest = engine.replay_manifest()
    assert manifest["module_id"] == "OI-186"
    assert manifest["index_id"] == summary.index_id
    assert len(manifest["entries"]) == 3

    engine.index_record({
        "audit_id": "audit-002",
        "adapter_id": "adp.kalshi",
        "query_id": "q-002",
        "replay_key": "replay-002b",
        "passed": True,
        "findings": [],
    })

    updated = engine.index_summary()
    assert updated.entry_count == 3
    assert updated.failed_count == 0
    assert engine.lookup_by_replay_key("replay-002") is None
    assert engine.lookup_by_replay_key("replay-002b").passed is True


if __name__ == "__main__":
    test_oi_186_query_audit_index_engine()
    print("[PASS] OI-186 Universal Market Adapter Query Audit Index Engine")
