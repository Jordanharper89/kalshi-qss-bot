from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_intelligence_session_context_assembly import (
    ENGINE_ID as OIT_040_ENGINE_ID,
    POLICY_ID as OIT_040_POLICY_ID,
    SCHEMA_VERSION as OIT_040_SCHEMA_VERSION,
    OracleIntelligenceContextField,
    OracleIntelligenceSessionContext,
    OracleIntelligenceSessionContextAssemblyReport,
    _stable_hash as oit_040_hash,
    verify_intelligence_session_context_assembly_report,
)
from qseries_v2.oracle_terminal.oracle_natural_language_intelligence_response_projection import (
    OracleIntelligenceResponseProjectionInvariantError,
    build_natural_language_intelligence_projection_report,
    verify_natural_language_intelligence_projection_report,
)


def context_field(
    key: str,
    path: str,
    field_type: str,
    value,
    text: str,
    ordinal: int,
):
    body = {
        "context_key": key,
        "source_field_path": path,
        "source_field_hash": f"source-field-{ordinal}",
        "field_type": field_type,
        "canonical_value": value,
        "searchable_text": text,
        "ordinal": ordinal,
    }
    return OracleIntelligenceContextField(
        **body,
        context_field_hash=oit_040_hash(body),
    )


def make_context_report(root: Path):
    fields = (
        context_field(
            "root",
            "$",
            "mapping",
            {
                "record_id": "REAL-041",
                "probability": 0.78,
                "direction": "bull",
            },
            '{"direction":"bull","probability":0.78,"record_id":"REAL-041"}',
            0,
        ),
        context_field(
            "direction",
            "$.direction",
            "string",
            "bull",
            "bull",
            1,
        ),
        context_field(
            "evidence.0.source_id",
            "$.evidence[0].source_id",
            "string",
            "SOURCE-ALPHA",
            "SOURCE-ALPHA",
            2,
        ),
        context_field(
            "evidence.0.confidence",
            "$.evidence[0].confidence",
            "number",
            0.84,
            "0.84",
            3,
        ),
        context_field(
            "probability",
            "$.probability",
            "number",
            0.78,
            "0.78",
            4,
        ),
        context_field(
            "record_id",
            "$.record_id",
            "string",
            "REAL-041",
            "REAL-041",
            5,
        ),
    )

    context_body = {
        "context_id": "context-041",
        "source_normalization_report_hash": "normalization-report-hash",
        "source_normalized_record_hash": "normalized-record-hash",
        "source_envelope_hash": "source-envelope-hash",
        "source_execution_report_hash": "execution-report-hash",
        "source_validation_report_hash": "validation-report-hash",
        "source_invocation_result_hash": "invocation-result-hash",
        "context_fields": fields,
        "context_field_count": len(fields),
        "searchable_field_count": len(fields),
        "root_field_present": True,
        "deterministic_ordering_applied": True,
        "full_lineage_preserved": True,
        "bounded_context": True,
        "context_ready": True,
        "read_only": True,
    }
    context = OracleIntelligenceSessionContext(
        **context_body,
        context_hash=oit_040_hash(context_body),
    )

    report_body = {
        "schema_version": OIT_040_SCHEMA_VERSION,
        "engine_id": OIT_040_ENGINE_ID,
        "policy_id": OIT_040_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "normalization_report_hash": "normalization-report-hash",
        "session_context": context,
        "context_assembled": True,
        "query_planning_ready": True,
        "multi_turn_memory_enabled": False,
        "persistent_memory_enabled": False,
        "learning_update_performed": False,
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
    report = OracleIntelligenceSessionContextAssemblyReport(
        **report_body,
        report_hash=oit_040_hash(report_body),
    )
    verify_intelligence_session_context_assembly_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-041 TEST")
    print(" NATURAL-LANGUAGE INTELLIGENCE RESPONSE PROJECTION")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        context_report = make_context_report(root)

        report = build_natural_language_intelligence_projection_report(
            root,
            context_assembly_report=context_report,
            query="What evidence supports the bull direction?",
        )

        assert report.query_accepted
        assert report.relevant_context_found
        assert report.answer_generation_ready
        assert not report.free_form_answer_generated

        projection = report.projection
        assert projection.projection_ready
        assert projection.bounded_projection
        assert projection.source_lineage_preserved
        assert projection.deterministic_ordering_applied
        assert projection.projected_field_count > 0
        assert projection.evidence_field_count >= 2
        assert projection.term_match_count >= 1

        selected_paths = tuple(
            field.source_field_path
            for field in projection.projected_fields
        )
        assert "$.direction" in selected_paths
        assert "$.evidence[0].source_id" in selected_paths
        assert "$.evidence[0].confidence" in selected_paths

        first = projection.projected_fields[0]
        assert first.match_score >= (
            projection.projected_fields[-1].match_score
        )

        exact_report = build_natural_language_intelligence_projection_report(
            root,
            context_assembly_report=context_report,
            query="Show probability",
        )
        assert exact_report.projection.exact_field_match_count == 1
        assert exact_report.projection.projected_fields[0].context_key == (
            "probability"
        )

        broad_report = build_natural_language_intelligence_projection_report(
            root,
            context_assembly_report=context_report,
            query="Give me an overview",
        )
        assert broad_report.projection.projected_field_count == 6

        replay = build_natural_language_intelligence_projection_report(
            root,
            context_assembly_report=context_report,
            query="What evidence supports the bull direction?",
        )
        assert replay == report
        assert verify_natural_language_intelligence_projection_report(
            report
        )

        tampered = replace(
            report,
            free_form_answer_generated=True,
        )
        try:
            verify_natural_language_intelligence_projection_report(
                tampered
            )
        except OracleIntelligenceResponseProjectionInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered projection report accepted"
            )

        assert not report.multi_turn_memory_enabled
        assert not report.persistent_memory_enabled
        assert not report.learning_update_performed
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.runtime_artifact_created
        assert not report.runtime_artifact_modified
        assert not report.networking_performed
        assert not report.publication_allowed
        assert not report.action_authorization_allowed
        assert not report.qseries_execution_allowed
        assert report.read_only

    print("[PASS] Certified OIT-040 session context consumed")
    print("[PASS] Natural-language query normalized")
    print("[PASS] Distinctive query terms extracted")
    print("[PASS] Exact field requests detected")
    print("[PASS] Evidence-related context prioritized")
    print("[PASS] Broad overview projection supported")
    print("[PASS] Deterministic field scoring and ordering certified")
    print("[PASS] Full source context lineage retained")
    print("[PASS] Bounded projection enforced")
    print("[PASS] Answer-generation readiness certified")
    print("[PASS] Free-form answer generation remained disabled")
    print("[PASS] Multi-turn memory and learning remained disabled")
    print("[PASS] Projection deterministic across replay")
    print("[PASS] Tampered projection report rejected")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-041 NATURAL-LANGUAGE RESPONSE PROJECTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
