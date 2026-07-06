from qseries_v2.oracle_intelligence.universal_market_adapter_query_replay_certification_engine import (
    READ_ONLY_GUARDRAILS,
    UniversalMarketAdapterQueryReplayCertificationEngine,
    create_query_replay_certification_engine,
)


def test_oi_189_query_replay_certification_engine():
    engine = create_query_replay_certification_engine("oracle.test")
    validation = {
        "validation_id": "oi188.validation.good",
        "manifest_id": "oi187.manifest.good",
        "manifest_hash": "a" * 64,
        "validation_hash": "b" * 64,
        "chain_hash": "c" * 64,
        "entry_count": 2,
        "passed": True,
        "critical_or_error_count": 0,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
    }
    manifest = {
        "manifest_id": "oi187.manifest.good",
        "manifest_hash": "a" * 64,
        "chain_hash": "c" * 64,
        "entry_count": 2,
        "read_only_guardrails": READ_ONLY_GUARDRAILS,
    }
    record = engine.certify_validation(validation, manifest=manifest, certification_context={"certification_scope": "replay"})
    assert record.module_id == "OI-189"
    assert record.certified is True
    assert record.certification_level == "certified"
    assert record.validation_passed is True
    assert record.blocker_count == 0
    assert len(record.certification_hash) == 64
    assert record.read_only_guardrails == READ_ONLY_GUARDRAILS

    warning_record = engine.certify_validation(validation)
    assert warning_record.certified is True
    assert warning_record.certification_level == "certified_with_warnings"
    assert any(f.code == "MANIFEST_NOT_ATTACHED" for f in warning_record.findings)

    bad_validation = {
        "validation_id": "oi188.validation.bad",
        "manifest_id": "oi187.manifest.bad",
        "manifest_hash": "short",
        "validation_hash": "bad",
        "chain_hash": "bad",
        "entry_count": 1,
        "passed": False,
        "critical_or_error_count": 2,
        "read_only_guardrails": {
            "oracle_read_only": False,
            "executes_trades": True,
            "routes_orders": True,
            "submits_orders": True,
            "manages_positions": True,
            "execution_owner": "ORACLE",
        },
    }
    bad = engine.certify_validation(bad_validation, certification_context={"certification_scope": "execution"})
    codes = {finding.code for finding in bad.findings}
    assert bad.certified is False
    assert bad.certification_level == "not_certified"
    assert "VALIDATION_NOT_PASSED" in codes
    assert "VALIDATION_HASH_INVALID" in codes
    assert "MANIFEST_HASH_INVALID" in codes
    assert "CHAIN_HASH_INVALID" in codes
    assert "VALIDATION_BLOCKERS_PRESENT" in codes
    assert "READ_ONLY_GUARDRAIL_MISMATCH" in codes
    assert "INVALID_CERTIFICATION_SCOPE" in codes

    many = engine.certify_many([
        {
            "validation_id": "oi188.validation.batch",
            "manifest_id": "oi187.manifest.batch",
            "manifest_hash": "d" * 64,
            "validation_hash": "e" * 64,
            "chain_hash": "f" * 64,
            "entry_count": 1,
            "passed": True,
            "critical_or_error_count": 0,
            "read_only_guardrails": READ_ONLY_GUARDRAILS,
        }
    ])
    assert len(many) == 1
    assert many[0].certified is True

    snapshot = engine.telemetry_snapshot()
    assert snapshot["certification_count"] == 4
    assert snapshot["certified_count"] == 3
    assert snapshot["not_certified_count"] == 1
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    payload = engine.certification_registry_payload()
    assert payload["module_id"] == "OI-189"
    assert payload["certification_count"] == 4
    assert len(payload["certifications"]) == 4

    empty = UniversalMarketAdapterQueryReplayCertificationEngine("oracle.empty")
    assert empty.telemetry_snapshot()["certification_count"] == 0


if __name__ == "__main__":
    test_oi_189_query_replay_certification_engine()
    print("[PASS] OI-189 Universal Market Adapter Query Replay Certification Engine")
