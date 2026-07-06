from qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_validation_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryReplayValidationEngine,
    create_query_replay_validation_engine,
)


def _valid_entry(sequence, audit_id, replay_key, passed=True, finding_codes=None, dependency_keys=None):
    finding_codes = finding_codes or []
    dependency_keys = dependency_keys or []
    entry = {
        "sequence": sequence,
        "audit_id": audit_id,
        "adapter_id": "adp.kalshi",
        "query_id": "q-" + audit_id[-3:],
        "replay_key": replay_key,
        "passed": passed,
        "query_hash": "a" * 64,
        "resolver_hash": "b" * 64,
        "market_model_hash": "c" * 64,
        "source_hash": "d" * 64,
        "finding_codes": finding_codes,
        "dependency_keys": dependency_keys,
        "lineage": {},
        "integrity_hash": "e" * 64,
    }
    entry["lineage"] = {
        "audit_id": entry["audit_id"],
        "adapter_id": entry["adapter_id"],
        "query_id": entry["query_id"],
        "replay_key": entry["replay_key"],
        "query_hash": entry["query_hash"],
        "resolver_hash": entry["resolver_hash"],
        "market_model_hash": entry["market_model_hash"],
        "source_hash": entry["source_hash"],
        "raw_hash": "f" * 64,
    }
    return entry


def _valid_manifest():
    entries = [
        _valid_entry(1, "audit-001", "replay-001"),
        _valid_entry(2, "audit-002", "replay-002", dependency_keys=["replay-001"]),
    ]
    return {
        "manifest_id": "oi187.manifest.test",
        "created_at": "2026-01-01T00:00:00+00:00",
        "oracle_instance_id": "oracle.test",
        "module_id": "OI-187",
        "module_name": "Oracle Universal Market Adapter Query Replay Manifest Engine",
        "manifest_version": "1.0",
        "entry_count": 2,
        "passed_count": 2,
        "failed_count": 0,
        "adapter_count": 1,
        "query_count": 2,
        "dependency_count": 1,
        "manifest_hash": "1" * 64,
        "chain_hash": "2" * 64,
        "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        "entries": entries,
        "findings": [],
        "telemetry": {
            "oracle_instance_id": "oracle.test",
            "module_id": "OI-187",
            "module_name": "Oracle Universal Market Adapter Query Replay Manifest Engine",
            "entry_count": 2,
            "passed_count": 2,
            "failed_count": 0,
        },
        "explainability": {
            "purpose": "Create deterministic replay manifest.",
            "read_only_reason": "Oracle is read-only.",
            "execution_boundary": "Q Series is the only execution engine.",
            "ordering_method": "Deterministic ordering.",
            "integrity_method": "SHA-256 integrity hashing.",
        },
    }


def test_oi_188_query_replay_validation_engine():
    engine = create_query_replay_validation_engine("oracle.test")
    manifest = _valid_manifest()

    report = engine.validate_manifest(manifest)

    assert report.module_id == "OI-188"
    assert report.target_manifest_id == "oi187.manifest.test"
    assert report.target_manifest_hash == "1" * 64
    assert report.target_chain_hash == "2" * 64
    assert report.passed is True
    assert report.score > 80
    assert report.check_count >= 10
    assert report.critical_count == 0
    assert report.error_count == 0
    assert report.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert len(report.replay_validation_hash) == 64

    snapshot = engine.telemetry_snapshot()
    assert snapshot["report_count"] == 1
    assert snapshot["latest_validation_id"] == report.validation_id
    assert snapshot["latest_passed"] is True
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    registry = engine.validation_registry_record()
    assert registry["record_status"] == "ready"
    assert registry["validation_id"] == report.validation_id
    assert registry["passed"] is True

    bad = _valid_manifest()
    bad["read_only_guardrails"]["executes_trades"] = True
    bad["entries"][1]["finding_codes"] = ["EXECUTION_BOUNDARY_VIOLATION"]
    bad["findings"] = [
        {"code": "EXECUTION_BOUNDARY_REPLAY_ALERT", "severity": "critical", "message": "Boundary alert."}
    ]

    bad_report = engine.validate_manifest(bad)
    assert bad_report.passed is False
    assert bad_report.critical_count >= 1
    assert any(f.code == "READ_ONLY_GUARDRAILS_MISMATCH" for f in bad_report.findings)
    assert any(f.code == "EXECUTION_BOUNDARY_REPLAY_VALIDATION_FAILURE" for f in bad_report.findings)

    count_bad = _valid_manifest()
    count_bad["entry_count"] = 99
    count_report = engine.validate_manifest(count_bad)
    assert count_report.passed is False
    assert any(f.code == "MANIFEST_SUMMARY_COUNT_MISMATCH" for f in count_report.findings)

    empty_engine = UniversalMarketAdapterQueryReplayValidationEngine("oracle.empty")
    empty_registry = empty_engine.validation_registry_record()
    assert empty_registry["record_status"] == "empty"

    reports = engine.validate_many([_valid_manifest(), _valid_manifest()])
    assert len(reports) == 2
    assert all(item.module_id == "OI-188" for item in reports)


if __name__ == "__main__":
    test_oi_188_query_replay_validation_engine()
    print("[PASS] OI-188 Universal Market Adapter Query Replay Validation Engine")
