from qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_manifest_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryReplayManifestEngine,
    create_query_replay_manifest_engine,
)


class FakeIndexEngine:
    def __init__(self, entries):
        self._entries = entries

    def entries(self):
        return list(self._entries)


def test_oi_187_query_replay_manifest_engine():
    engine = create_query_replay_manifest_engine("oracle.test")

    records = [
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
            "source_hash": "s" * 64,
            "finding_codes": ["EXECUTION_BOUNDARY_VIOLATION"],
        },
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
            "source_hash": "r" * 64,
            "finding_codes": [],
        },
    ]

    manifest = engine.build_manifest(
        records,
        manifest_context={
            "environment": "test",
            "architecture": "oracle-read-only",
        },
        dependency_map={
            "replay-002": ["replay-001"],
        },
    )

    assert manifest.module_id == "OI-187"
    assert manifest.entry_count == 2
    assert manifest.passed_count == 1
    assert manifest.failed_count == 1
    assert manifest.adapter_count == 1
    assert manifest.query_count == 2
    assert manifest.dependency_count == 1
    assert len(manifest.manifest_hash) == 64
    assert len(manifest.chain_hash) == 64
    assert manifest.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert manifest.entries[0].replay_key == "replay-001"
    assert manifest.entries[1].replay_key == "replay-002"
    assert manifest.entries[1].dependency_keys == ["replay-001"]
    assert any(f.code == "EXECUTION_BOUNDARY_REPLAY_ALERT" for f in manifest.findings)
    assert manifest.passed is False

    package = engine.replay_package()
    assert package["package_status"] == "ready"
    assert package["manifest_id"] == manifest.manifest_id
    assert package["manifest_hash"] == manifest.manifest_hash
    assert len(package["entries"]) == 2
    assert package["read_only_guardrails"]["execution_owner"] == "Q_SERIES_ONLY"

    snapshot = engine.telemetry_snapshot()
    assert snapshot["manifest_count"] == 1
    assert snapshot["latest_manifest_id"] == manifest.manifest_id
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    empty_engine = UniversalMarketAdapterQueryReplayManifestEngine("oracle.empty")
    empty_package = empty_engine.replay_package()
    assert empty_package["package_status"] == "empty"
    assert empty_package["entries"] == []

    duplicate_manifest = engine.build_manifest([
        {
            "audit_id": "audit-003",
            "adapter_id": "adp.test",
            "query_id": "q-003",
            "replay_key": "same-key",
            "passed": True,
            "query_hash": "x",
            "resolver_hash": "y",
        },
        {
            "audit_id": "audit-004",
            "adapter_id": "adp.test",
            "query_id": "q-004",
            "replay_key": "same-key",
            "passed": True,
            "query_hash": "x",
            "resolver_hash": "y",
        },
    ])

    assert any(f.code == "DUPLICATE_REPLAY_KEYS" for f in duplicate_manifest.findings)

    index_manifest = engine.build_from_index_engine(FakeIndexEngine(records))
    assert index_manifest.entry_count == 2
    assert index_manifest.entries[0].replay_key == "replay-001"


if __name__ == "__main__":
    test_oi_187_query_replay_manifest_engine()
    print("[PASS] OI-187 Universal Market Adapter Query Replay Manifest Engine")
