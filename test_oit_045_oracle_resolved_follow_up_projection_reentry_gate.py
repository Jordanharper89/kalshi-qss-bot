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
from qseries_v2.oracle_terminal.oracle_multi_turn_follow_up_query_context_resolution import (
    ENGINE_ID as OIT_044_ENGINE_ID,
    POLICY_ID as OIT_044_POLICY_ID,
    SCHEMA_VERSION as OIT_044_SCHEMA_VERSION,
    OracleFollowUpQueryReference,
    OracleFollowUpQueryResolutionReport,
    OracleResolvedFollowUpQuery,
    _stable_hash as oit_044_hash,
    verify_follow_up_query_resolution_report,
)
from qseries_v2.oracle_terminal.oracle_resolved_follow_up_projection_reentry_gate import (
    OracleResolvedFollowUpProjectionReentryInvariantError,
    build_resolved_follow_up_projection_reentry_report,
    verify_resolved_follow_up_projection_reentry_report,
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
                "record_id": "REAL-045",
                "direction": "bull",
                "probability": 0.79,
            },
            '{"direction":"bull","probability":0.79,"record_id":"REAL-045"}',
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
            "probability",
            "$.probability",
            "number",
            0.79,
            "0.79",
            2,
        ),
        context_field(
            "evidence.0.source_id",
            "$.evidence[0].source_id",
            "string",
            "SOURCE-045",
            "SOURCE-045",
            3,
        ),
        context_field(
            "evidence.0.confidence",
            "$.evidence[0].confidence",
            "number",
            0.86,
            "0.86",
            4,
        ),
    )

    context_body = {
        "context_id": "context-045",
        "source_normalization_report_hash": "normalization-report-045",
        "source_normalized_record_hash": "normalized-record-045",
        "source_envelope_hash": "source-envelope-045",
        "source_execution_report_hash": "execution-report-045",
        "source_validation_report_hash": "validation-report-045",
        "source_invocation_result_hash": "invocation-result-045",
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
        "normalization_report_hash": "normalization-report-045",
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


def make_follow_up_report(root: Path):
    reference_body = {
        "reference_type": "latest_turn",
        "source_turn_index": 1,
        "source_turn_hash": "turn-hash-045",
        "source_query": "What evidence supports the bull direction?",
        "source_answer_id": "answer-045",
        "source_answer_hash": "answer-hash-045",
        "reference_text": (
            "turn 1: What evidence supports the bull direction?"
        ),
        "reference_score": 20,
    }
    reference = OracleFollowUpQueryReference(
        **reference_body,
        reference_hash=oit_044_hash(reference_body),
    )

    resolved_query = (
        "Has it changed now? "
        "[context from prior query: "
        "What evidence supports the bull direction?]"
    )

    resolved_body = {
        "raw_query": "Has it changed now?",
        "normalized_query": "Has it changed now?",
        "query_terms": ("has", "it", "changed", "now"),
        "follow_up_detected": True,
        "standalone_query": False,
        "referenced_turns": (reference,),
        "referenced_turn_count": 1,
        "primary_reference_turn_index": 1,
        "resolved_query": resolved_query,
        "resolution_confidence": 0.70,
        "session_lineage_preserved": True,
        "resolution_ready": True,
        "read_only": True,
    }
    resolved = OracleResolvedFollowUpQuery(
        **resolved_body,
        resolution_hash=oit_044_hash(resolved_body),
    )

    report_body = {
        "schema_version": OIT_044_SCHEMA_VERSION,
        "engine_id": OIT_044_ENGINE_ID,
        "policy_id": OIT_044_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "source_session_context_hash": "volatile-session-context-045",
        "resolved_follow_up_query": resolved,
        "context_resolution_performed": True,
        "downstream_projection_ready": True,
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
    report = OracleFollowUpQueryResolutionReport(
        **report_body,
        report_hash=oit_044_hash(report_body),
    )
    verify_follow_up_query_resolution_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-045 TEST")
    print(" RESOLVED FOLLOW-UP PROJECTION REENTRY GATE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        context_report = make_context_report(root)
        follow_up_report = make_follow_up_report(root)

        report = build_resolved_follow_up_projection_reentry_report(
            root,
            follow_up_resolution_report=follow_up_report,
            context_assembly_report=context_report,
        )

        assert report.reentry_performed
        assert report.answer_generation_ready
        assert report.projection_report.answer_generation_ready
        assert report.projection_binding.relevant_context_found
        assert (
            report.projection_binding.exact_cross_stage_lineage_verified
        )
        assert (
            report.projection_binding.source_follow_up_report_hash
            == follow_up_report.report_hash
        )
        assert (
            report.projection_binding.source_context_assembly_report_hash
            == context_report.report_hash
        )
        assert (
            report.projection_binding.source_session_context_hash
            == follow_up_report.source_session_context_hash
        )
        assert (
            report.projection_binding.resolved_query
            == follow_up_report.resolved_follow_up_query.resolved_query
        )
        assert (
            report.projection_binding.projection_report_hash
            == report.projection_report.report_hash
        )
        assert (
            report.projection_binding.projection_hash
            == report.projection_report.projection.projection_hash
        )
        assert report.projection_binding.projected_field_count > 0

        selected_paths = tuple(
            field.source_field_path
            for field in report.projection_report.projection.projected_fields
        )
        assert "$.direction" in selected_paths
        assert "$.evidence[0].source_id" in selected_paths
        assert "$.evidence[0].confidence" in selected_paths

        replay = build_resolved_follow_up_projection_reentry_report(
            root,
            follow_up_resolution_report=follow_up_report,
            context_assembly_report=context_report,
        )
        assert replay == report
        assert verify_resolved_follow_up_projection_reentry_report(
            report
        )

        tampered = replace(
            report,
            persistent_memory_enabled=True,
        )
        try:
            verify_resolved_follow_up_projection_reentry_report(
                tampered
            )
        except OracleResolvedFollowUpProjectionReentryInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered OIT-045 report accepted"
            )

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

    print("[PASS] Certified OIT-044 resolved follow-up consumed")
    print("[PASS] Certified OIT-040 intelligence context consumed")
    print("[PASS] Resolved query reentered OIT-041 projection")
    print("[PASS] OIT-043 volatile-session lineage preserved")
    print("[PASS] OIT-040 intelligence-context lineage preserved")
    print("[PASS] Distinct session and intelligence contexts retained")
    print("[PASS] Relevant projected fields recovered")
    print("[PASS] Exact cross-stage hashes verified")
    print("[PASS] Answer-generation readiness certified")
    print("[PASS] Reentry deterministic across replay")
    print("[PASS] Tampered reentry report rejected")
    print("[PASS] Persistent memory and learning remained disabled")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-045 RESOLVED FOLLOW-UP PROJECTION REENTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
