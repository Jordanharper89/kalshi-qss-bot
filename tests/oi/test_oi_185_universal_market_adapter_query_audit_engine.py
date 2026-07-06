from qseries_v2.oracle_intelligence.universal_market_adapter_query_audit_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryAuditEngine,
    create_query_audit_engine,
)


def test_oi_185_query_audit_engine():
    engine = create_query_audit_engine("oracle.test")

    record = engine.audit_query(
        adapter_id="adp.kalshi",
        query={
            "query_id": "q-001",
            "market_type": "prediction_market",
            "symbol": "KXTEST",
        },
        resolver_output={
            "query_id": "q-001",
            "resolved": True,
            "markets": [{"universal_market_id": "umm.test.001"}],
        },
        market_model={
            "schema_version": "1.0",
            "universal_market_id": "umm.test.001",
            "market_type": "prediction_market",
        },
        telemetry={"latency_ms": 12},
    )

    assert record.passed is True
    assert record.adapter_id == "adp.kalshi"
    assert record.query_id == "q-001"
    assert len(record.query_hash) == 64
    assert len(record.resolver_hash) == 64
    assert len(record.market_model_hash) == 64
    assert len(record.replay_key) == 64
    assert record.read_only_guardrails["oracle_read_only"] is True
    assert record.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"

    bad = engine.audit_query(
        adapter_id="adp.bad",
        query={"query_id": "q-002", "market_type": "prediction_market"},
        resolver_output={"query_id": "q-002", "executed": True, "order_submitted": True},
        market_model={"market_id": "m-1"},
    )

    assert bad.passed is False
    assert any(f.code == "EXECUTION_BOUNDARY_VIOLATION" for f in bad.findings)

    snapshot = engine.telemetry_snapshot()
    assert snapshot["records"] == 2
    assert snapshot["passed"] == 1
    assert snapshot["failed"] == 1
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    manifest = engine.replay_manifest()
    assert manifest["record_count"] == 2
    assert manifest["records"][0]["query_hash"] == record.query_hash

    batch = engine.audit_many([
        {
            "adapter_id": "adp.batch",
            "query": {"query_id": "q-003", "market": "generic"},
            "resolver_output": {"result": {"ok": True}},
            "market_model": {"schema_version": "1.0", "market_type": "generic"},
        }
    ])
    assert len(batch) == 1
    assert batch[0].query_id == "q-003"


if __name__ == "__main__":
    test_oi_185_query_audit_engine()
    print("[PASS] OI-185 Universal Market Adapter Query Audit Engine")
