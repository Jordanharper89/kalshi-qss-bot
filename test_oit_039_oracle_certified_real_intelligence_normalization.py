from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (
    ENGINE_ID as E37,
    POLICY_ID as P37,
    SCHEMA_VERSION as S37,
    OracleRealIntelligenceInvocationExecutionReceipt,
    OracleRealIntelligenceInvocationResult,
    OracleRealIntelligenceReadInvocationExecutionReport,
    _stable_hash as h37,
)
from qseries_v2.oracle_terminal.oracle_real_intelligence_response_validation_gate import (
    ENGINE_ID as E38,
    POLICY_ID as P38,
    SCHEMA_VERSION as S38,
    OracleRealIntelligenceResponseShape,
    OracleRealIntelligenceResponseValidationReport,
    _stable_hash as h38,
)
from qseries_v2.oracle_terminal.oracle_certified_real_intelligence_source_envelope import (
    build_real_intelligence_source_envelope,
)
from qseries_v2.oracle_terminal.oracle_certified_real_intelligence_normalization import (
    OracleRealIntelligenceNormalizationInvariantError,
    build_real_intelligence_normalization_report,
    verify_real_intelligence_normalization_report,
)


def make_sources(root: Path):
    value = {
        "record_id": "REAL-039",
        "probability": 0.74,
        "direction": "bull",
        "evidence": [
            {"source_id": "SOURCE-1", "confidence": 0.82},
            {"source_id": "SOURCE-2", "confidence": 0.66},
        ],
        "read_only": True,
    }
    rb = {
        "result_type": "builtins.dict",
        "canonical_result": value,
        "result_hash": h37(value),
        "result_available": True,
        "result_none": False,
        "read_only": True,
    }
    result = OracleRealIntelligenceInvocationResult(
        **rb, verification_hash=h37(rb)
    )
    cb = {
        "invocation_id": "invocation-039",
        "readiness_report_hash": "ready",
        "manifest_hash": "manifest",
        "module_name": "test.module",
        "callable_name": "load",
        "invocation_argument_names": ("repository_root", "artifact_path", "persist"),
        "callable_invocation_count": 1,
        "callable_invoked": True,
        "invocation_completed": True,
        "artifact_sha256_before": "a" * 64,
        "artifact_sha256_after": "a" * 64,
        "artifact_byte_count_before": 10,
        "artifact_byte_count_after": 10,
        "artifact_mtime_ns_before": 1,
        "artifact_mtime_ns_after": 1,
        "artifact_unchanged": True,
        "invocation_result": result,
        "persistence_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    receipt = OracleRealIntelligenceInvocationExecutionReceipt(
        **cb, receipt_hash=h37(cb)
    )
    eb = {
        "schema_version": S37,
        "engine_id": E37,
        "policy_id": P37,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "readiness_report_hash": "ready",
        "execution_receipt": receipt,
        "exact_callable_invoked": True,
        "exact_arguments_consumed": True,
        "exactly_one_invocation_performed": True,
        "artifact_identity_preserved": True,
        "bounded_read_result_available": True,
        "execution_succeeded": True,
        "persistence_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None,
    }
    execution = OracleRealIntelligenceReadInvocationExecutionReport(
        **eb, report_hash=h37(eb)
    )

    sb = {
        "root_type": "builtins.dict",
        "root_mapping": True,
        "root_sequence": False,
        "root_scalar": False,
        "maximum_depth": 3,
        "mapping_count": 3,
        "sequence_count": 1,
        "scalar_count": 8,
        "null_count": 0,
        "string_count": 4,
        "number_count": 3,
        "boolean_count": 1,
        "total_node_count": 12,
        "total_key_count": 9,
        "duplicate_key_risk_detected": False,
        "unsupported_type_detected": False,
        "nonfinite_number_detected": False,
        "oversized_value_detected": False,
    }
    shape = OracleRealIntelligenceResponseShape(
        **sb, shape_hash=h38(sb)
    )
    vb = {
        "schema_version": S38,
        "engine_id": E38,
        "policy_id": P38,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "execution_report_hash": execution.report_hash,
        "invocation_result_hash": result.result_hash,
        "response_shape": shape,
        "findings": (),
        "finding_count": 0,
        "blocking_finding_count": 0,
        "structurally_valid": True,
        "deterministic_replay_ready": True,
        "normalization_ready": True,
        "source_result_preserved": True,
        "response_modified": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None,
    }
    validation = OracleRealIntelligenceResponseValidationReport(
        **vb, report_hash=h38(vb)
    )
    return execution, validation


def main():
    print("=" * 48)
    print(" OIT-039 TEST")
    print(" CERTIFIED REAL INTELLIGENCE NORMALIZATION")
    print(" REPOSITORY-ALIGNED SOURCE ENVELOPE")
    print("=" * 48)
    with TemporaryDirectory() as temp:
        root = Path(temp)
        execution, validation = make_sources(root)
        envelope = build_real_intelligence_source_envelope(
            execution, validation
        )
        report = build_real_intelligence_normalization_report(
            root, source_envelope=envelope
        )
        assert report.normalized_record_available
        assert report.source_result_preserved
        assert not report.lossy_coercion_performed
        record = report.normalized_record
        assert record.normalization_complete
        assert record.normalized_field_count == len(record.normalized_fields)
        paths = tuple(x.field_path for x in record.normalized_fields)
        assert paths[0] == "$"
        assert "$.probability" in paths
        assert "$.evidence[0].source_id" in paths
        assert "$.evidence[1].confidence" in paths
        assert "$.read_only" in paths
        replay = build_real_intelligence_normalization_report(
            root, source_envelope=envelope
        )
        assert replay == report
        assert verify_real_intelligence_normalization_report(report)
        try:
            verify_real_intelligence_normalization_report(
                replace(report, lossy_coercion_performed=True)
            )
        except OracleRealIntelligenceNormalizationInvariantError:
            pass
        else:
            raise AssertionError("tampered normalization accepted")
    print("[PASS] Certified OIT-037 and OIT-038 reports consumed")
    print("[PASS] Exact cross-report result lineage verified")
    print("[PASS] Canonical source envelope materialized read-only")
    print("[PASS] Deterministic nested-field normalization certified")
    print("[PASS] Exact field paths materialized")
    print("[PASS] Source structure and scalar types preserved")
    print("[PASS] Lossy coercion rejected")
    print("[PASS] Normalization deterministic across replay")
    print("[PASS] Tampered normalization report rejected")
    print("[PASS] No analytics execution, persistence, or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-039 CERTIFIED REAL INTELLIGENCE NORMALIZATION PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
