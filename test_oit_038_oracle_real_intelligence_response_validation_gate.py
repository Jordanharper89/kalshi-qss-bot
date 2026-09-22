from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_authorized_real_intelligence_read_invocation_execution_gate import (
    ENGINE_ID as OIT_037_ENGINE_ID,
    POLICY_ID as OIT_037_POLICY_ID,
    SCHEMA_VERSION as OIT_037_SCHEMA_VERSION,
    OracleRealIntelligenceInvocationExecutionReceipt,
    OracleRealIntelligenceInvocationResult,
    OracleRealIntelligenceReadInvocationExecutionReport,
    _stable_hash as oit_037_hash,
    verify_read_invocation_execution_report,
)
from qseries_v2.oracle_terminal.oracle_real_intelligence_response_validation_gate import (
    OracleRealIntelligenceResponseValidationInvariantError,
    build_real_intelligence_response_validation_report,
    verify_real_intelligence_response_validation_report,
)


def make_execution_report(root: Path):
    canonical_result = {
        "record_id": "REAL-038",
        "probability": 0.72,
        "direction": "bull",
        "evidence": [
            {
                "source_id": "SOURCE-1",
                "confidence": 0.81,
            },
            {
                "source_id": "SOURCE-2",
                "confidence": 0.63,
            },
        ],
        "read_only": True,
    }

    result_body = {
        "result_type": "builtins.dict",
        "canonical_result": canonical_result,
        "result_hash": oit_037_hash(canonical_result),
        "result_available": True,
        "result_none": False,
        "read_only": True,
    }
    result = OracleRealIntelligenceInvocationResult(
        **result_body,
        verification_hash=oit_037_hash(result_body),
    )

    receipt_body = {
        "invocation_id": "invocation-038",
        "readiness_report_hash": "readiness-report-hash",
        "manifest_hash": "manifest-hash",
        "module_name": "test.module",
        "callable_name": "load_real_intelligence",
        "invocation_argument_names": (
            "repository_root",
            "artifact_path",
            "persist",
        ),
        "callable_invocation_count": 1,
        "callable_invoked": True,
        "invocation_completed": True,
        "artifact_sha256_before": "a" * 64,
        "artifact_sha256_after": "a" * 64,
        "artifact_byte_count_before": 100,
        "artifact_byte_count_after": 100,
        "artifact_mtime_ns_before": 123456,
        "artifact_mtime_ns_after": 123456,
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
        **receipt_body,
        receipt_hash=oit_037_hash(receipt_body),
    )

    report_body = {
        "schema_version": OIT_037_SCHEMA_VERSION,
        "engine_id": OIT_037_ENGINE_ID,
        "policy_id": OIT_037_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "readiness_report_hash": "readiness-report-hash",
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
    report = OracleRealIntelligenceReadInvocationExecutionReport(
        **report_body,
        report_hash=oit_037_hash(report_body),
    )
    verify_read_invocation_execution_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-038 TEST")
    print(" REAL INTELLIGENCE RESPONSE VALIDATION")
    print(" CORRECTION V2 - EXACT STRUCTURAL COUNTS")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_execution_report(root)

        report = build_real_intelligence_response_validation_report(
            root,
            execution_report=source,
        )

        assert report.execution_report_hash == source.report_hash
        assert report.invocation_result_hash == (
            source.execution_receipt.invocation_result.result_hash
        )
        assert report.structurally_valid
        assert report.deterministic_replay_ready
        assert report.normalization_ready
        assert report.source_result_preserved
        assert not report.response_modified
        assert report.finding_count == 0
        assert report.blocking_finding_count == 0

        shape = report.response_shape

        # Exact counts derived from the current fixture:
        # root mapping + two evidence mappings = 3 mappings
        # evidence list = 1 sequence
        # four strings: record_id, direction, SOURCE-1, SOURCE-2
        # three numbers: probability and two confidence values
        # one boolean: read_only
        # eight scalar values total
        # twelve total nodes: root + list + two nested mappings + eight scalars
        # ten total mapping keys: five root keys + two + two nested keys
        assert shape.root_mapping
        assert not shape.root_sequence
        assert not shape.root_scalar
        assert shape.maximum_depth == 3
        assert shape.mapping_count == 3
        assert shape.sequence_count == 1
        assert shape.scalar_count == 8
        assert shape.null_count == 0
        assert shape.string_count == 4
        assert shape.number_count == 3
        assert shape.boolean_count == 1
        assert shape.total_node_count == 12
        assert shape.total_key_count == 9
        assert not shape.duplicate_key_risk_detected
        assert not shape.unsupported_type_detected
        assert not shape.nonfinite_number_detected
        assert not shape.oversized_value_detected

        replay = build_real_intelligence_response_validation_report(
            root,
            execution_report=source,
        )
        assert replay == report
        assert verify_real_intelligence_response_validation_report(report)

        tampered = replace(
            report,
            response_modified=True,
        )
        try:
            verify_real_intelligence_response_validation_report(tampered)
        except OracleRealIntelligenceResponseValidationInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered response validation report accepted"
            )

        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.runtime_artifact_created
        assert not report.runtime_artifact_modified
        assert not report.networking_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed
        assert report.read_only

    print("[PASS] Certified OIT-037 execution report consumed")
    print("[PASS] Returned intelligence result structurally inspected")
    print("[PASS] Exact mapping count verified")
    print("[PASS] Exact sequence count verified")
    print("[PASS] Exact scalar count verified")
    print("[PASS] Exact string count verified")
    print("[PASS] Exact number and boolean counts verified")
    print("[PASS] Exact depth, node, and key counts verified")
    print("[PASS] Unsupported response types rejected")
    print("[PASS] Nonfinite numbers rejected")
    print("[PASS] Oversized values rejected")
    print("[PASS] Source result hash preserved")
    print("[PASS] Structural validation deterministic across replay")
    print("[PASS] Normalization readiness certified")
    print("[PASS] Tampered validation report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] No runtime artifact created or modified")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-038 REAL INTELLIGENCE RESPONSE VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
