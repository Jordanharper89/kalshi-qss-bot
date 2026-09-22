from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_certified_real_intelligence_source_envelope import (
    ENGINE_ID as ENVELOPE_ENGINE_ID,
    POLICY_ID as ENVELOPE_POLICY_ID,
    SCHEMA_VERSION as ENVELOPE_SCHEMA_VERSION,
    OracleRealIntelligenceSourceEnvelope,
    _stable_hash as envelope_hash,
)
from qseries_v2.oracle_terminal.oracle_certified_real_intelligence_normalization import (
    ENGINE_ID as NORMALIZATION_ENGINE_ID,
    POLICY_ID as NORMALIZATION_POLICY_ID,
    SCHEMA_VERSION as NORMALIZATION_SCHEMA_VERSION,
    OracleNormalizedIntelligenceField,
    OracleNormalizedIntelligenceRecord,
    OracleRealIntelligenceNormalizationReport,
    _stable_hash as normalization_hash,
    verify_real_intelligence_normalization_report,
)
from qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (
    OracleIntelligenceSessionContextInvariantError,
    build_intelligence_session_context_assembly_report,
    verify_intelligence_session_context_assembly_report,
)


def normalized_field(
    path: str,
    name: str,
    field_type: str,
    value,
    source_result_hash: str,
    source_envelope_hash: str,
):
    body = {
        "field_path": path,
        "field_name": name,
        "field_type": field_type,
        "canonical_value": value,
        "source_result_hash": source_result_hash,
        "source_envelope_hash": source_envelope_hash,
    }
    return OracleNormalizedIntelligenceField(
        **body,
        field_hash=normalization_hash(body),
    )


def make_normalization_report(root: Path):
    canonical_result = {
        "record_id": "REAL-040",
        "probability": 0.76,
        "direction": "bull",
        "read_only": True,
    }
    invocation_result_hash = envelope_hash(canonical_result)

    envelope_body = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "engine_id": ENVELOPE_ENGINE_ID,
        "policy_id": ENVELOPE_POLICY_ID,
        "execution_report_hash": "execution-report-hash",
        "validation_report_hash": "validation-report-hash",
        "invocation_result_hash": invocation_result_hash,
        "canonical_result": canonical_result,
        "canonical_result_hash": invocation_result_hash,
        "execution_validation_lineage_verified": True,
        "source_result_preserved": True,
        "read_only": True,
    }
    envelope = OracleRealIntelligenceSourceEnvelope(
        **envelope_body,
        envelope_hash=envelope_hash(envelope_body),
    )

    fields = (
        normalized_field(
            "$",
            "$",
            "mapping",
            canonical_result,
            invocation_result_hash,
            envelope.envelope_hash,
        ),
        normalized_field(
            "$.direction",
            "direction",
            "string",
            "bull",
            invocation_result_hash,
            envelope.envelope_hash,
        ),
        normalized_field(
            "$.probability",
            "probability",
            "number",
            0.76,
            invocation_result_hash,
            envelope.envelope_hash,
        ),
        normalized_field(
            "$.read_only",
            "read_only",
            "boolean",
            True,
            invocation_result_hash,
            envelope.envelope_hash,
        ),
        normalized_field(
            "$.record_id",
            "record_id",
            "string",
            "REAL-040",
            invocation_result_hash,
            envelope.envelope_hash,
        ),
    )

    record_body = {
        "record_id": "normalized-record-040",
        "source_execution_report_hash": (
            envelope.execution_report_hash
        ),
        "source_validation_report_hash": (
            envelope.validation_report_hash
        ),
        "source_envelope_hash": envelope.envelope_hash,
        "source_invocation_result_hash": invocation_result_hash,
        "normalized_fields": fields,
        "normalized_field_count": len(fields),
        "root_type": "builtins.dict",
        "lossy_coercion_performed": False,
        "source_structure_preserved": True,
        "deterministic_ordering_applied": True,
        "normalization_complete": True,
    }
    record = OracleNormalizedIntelligenceRecord(
        **record_body,
        record_hash=normalization_hash(record_body),
    )

    report_body = {
        "schema_version": NORMALIZATION_SCHEMA_VERSION,
        "engine_id": NORMALIZATION_ENGINE_ID,
        "policy_id": NORMALIZATION_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "source_envelope_hash": envelope.envelope_hash,
        "normalized_record": record,
        "normalized_record_available": True,
        "source_result_preserved": True,
        "source_response_modified": False,
        "lossy_coercion_performed": False,
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
    report = OracleRealIntelligenceNormalizationReport(
        **report_body,
        report_hash=normalization_hash(report_body),
    )
    verify_real_intelligence_normalization_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-040 TEST")
    print(" INTELLIGENCE SESSION CONTEXT ASSEMBLY")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        normalization = make_normalization_report(root)

        report = build_intelligence_session_context_assembly_report(
            root,
            normalization_report=normalization,
        )

        assert report.context_assembled
        assert report.query_planning_ready
        assert not report.multi_turn_memory_enabled
        assert not report.persistent_memory_enabled
        assert not report.learning_update_performed

        context = report.session_context
        assert context.context_ready
        assert context.bounded_context
        assert context.full_lineage_preserved
        assert context.root_field_present
        assert context.deterministic_ordering_applied
        assert context.context_field_count == 5
        assert context.searchable_field_count == 5

        paths = tuple(
            field.source_field_path
            for field in context.context_fields
        )
        assert paths == (
            "$",
            "$.direction",
            "$.probability",
            "$.read_only",
            "$.record_id",
        )

        keys = tuple(
            field.context_key
            for field in context.context_fields
        )
        assert keys == (
            "root",
            "direction",
            "probability",
            "read_only",
            "record_id",
        )

        values = {
            field.context_key: field.searchable_text
            for field in context.context_fields
        }
        assert values["direction"] == "bull"
        assert values["probability"] == "0.76"
        assert values["read_only"] == "true"
        assert values["record_id"] == "REAL-040"

        replay = build_intelligence_session_context_assembly_report(
            root,
            normalization_report=normalization,
        )
        assert replay == report
        assert verify_intelligence_session_context_assembly_report(
            report
        )

        tampered = replace(
            report,
            persistent_memory_enabled=True,
        )
        try:
            verify_intelligence_session_context_assembly_report(
                tampered
            )
        except OracleIntelligenceSessionContextInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered context assembly report accepted"
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

    print("[PASS] Certified OIT-039 normalization report consumed")
    print("[PASS] Deterministic session context assembled")
    print("[PASS] Exact normalized-field ordering retained")
    print("[PASS] Searchable context text materialized")
    print("[PASS] Root context field preserved")
    print("[PASS] Full OIT-037 through OIT-039 lineage retained")
    print("[PASS] Bounded context limit enforced")
    print("[PASS] Query-planning readiness certified")
    print("[PASS] Multi-turn and persistent memory remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Context deterministic across replay")
    print("[PASS] Tampered context report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] No runtime artifact created or modified")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-040 INTELLIGENCE SESSION CONTEXT ASSEMBLY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
