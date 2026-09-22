from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_natural_language_intelligence_response_projection import (
    ENGINE_ID as OIT_041_ENGINE_ID,
    POLICY_ID as OIT_041_POLICY_ID,
    SCHEMA_VERSION as OIT_041_SCHEMA_VERSION,
    OracleIntelligenceQueryIntent,
    OracleNaturalLanguageIntelligenceProjection,
    OracleNaturalLanguageIntelligenceProjectionReport,
    OracleProjectedIntelligenceField,
    _stable_hash as oit_041_hash,
)
from qseries_v2.oracle_terminal.oracle_resolved_follow_up_projection_reentry_gate import (
    ENGINE_ID as OIT_045_ENGINE_ID,
    POLICY_ID as OIT_045_POLICY_ID,
    SCHEMA_VERSION as OIT_045_SCHEMA_VERSION,
    OracleResolvedFollowUpProjectionBinding,
    OracleResolvedFollowUpProjectionReentryReport,
    _stable_hash as oit_045_hash,
    verify_resolved_follow_up_projection_reentry_report,
)
from qseries_v2.oracle_terminal.oracle_final_intelligence_answer_assembly import (
    OracleFinalIntelligenceAnswerAssemblyInvariantError,
    build_final_intelligence_answer_assembly_report,
    verify_final_intelligence_answer_assembly_report,
)


def projected_field(
    key: str,
    path: str,
    field_type: str,
    value,
    text: str,
    terms: tuple[str, ...],
    score: int,
    reason: str,
    ordinal: int,
):
    body = {
        "context_key": key,
        "source_field_path": path,
        "source_context_field_hash": f"context-field-{ordinal}",
        "field_type": field_type,
        "canonical_value": value,
        "searchable_text": text,
        "match_terms": terms,
        "match_score": score,
        "selection_reason": reason,
        "projection_ordinal": ordinal,
    }
    return OracleProjectedIntelligenceField(
        **body,
        projected_field_hash=oit_041_hash(body),
    )


def make_reentry_report(root: Path):
    resolved_query = (
        "Has it changed now? "
        "[context from prior query: "
        "What evidence supports the bull direction?]"
    )

    intent_body = {
        "raw_query": resolved_query,
        "normalized_query": resolved_query,
        "query_terms": (
            "has",
            "it",
            "changed",
            "now",
            "context",
            "from",
            "prior",
            "query",
            "what",
            "evidence",
            "supports",
            "the",
            "bull",
            "direction",
        ),
        "distinctive_terms": (
            "has",
            "changed",
            "now",
            "context",
            "prior",
            "query",
            "evidence",
            "supports",
            "bull",
            "direction",
        ),
        "requested_field_names": ("direction",),
        "broad_context_requested": False,
        "evidence_requested": True,
        "query_valid": True,
    }
    intent = OracleIntelligenceQueryIntent(
        **intent_body,
        intent_hash=oit_041_hash(intent_body),
    )

    fields = (
        projected_field(
            "direction",
            "$.direction",
            "string",
            "bull",
            "bull",
            ("bull", "direction"),
            120,
            "exact_field_request",
            0,
        ),
        projected_field(
            "evidence.0.source_id",
            "$.evidence[0].source_id",
            "string",
            "SOURCE-046",
            "SOURCE-046",
            ("evidence",),
            35,
            "distinctive_term_match+evidence_request",
            1,
        ),
        projected_field(
            "evidence.0.confidence",
            "$.evidence[0].confidence",
            "number",
            0.87,
            "0.87",
            ("evidence",),
            35,
            "distinctive_term_match+evidence_request",
            2,
        ),
        projected_field(
            "probability",
            "$.probability",
            "number",
            0.80,
            "0.80",
            (),
            1,
            "root_context",
            3,
        ),
    )

    projection_body = {
        "projection_id": "projection-046",
        "source_context_hash": "intelligence-context-046",
        "source_context_report_hash": "context-report-046",
        "query_intent": intent,
        "projected_fields": fields,
        "projected_field_count": len(fields),
        "evidence_field_count": 2,
        "exact_field_match_count": 1,
        "term_match_count": 3,
        "bounded_projection": True,
        "source_lineage_preserved": True,
        "deterministic_ordering_applied": True,
        "projection_ready": True,
        "read_only": True,
    }
    projection = OracleNaturalLanguageIntelligenceProjection(
        **projection_body,
        projection_hash=oit_041_hash(projection_body),
    )

    projection_report_body = {
        "schema_version": OIT_041_SCHEMA_VERSION,
        "engine_id": OIT_041_ENGINE_ID,
        "policy_id": OIT_041_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "context_assembly_report_hash": "context-report-046",
        "projection": projection,
        "query_accepted": True,
        "relevant_context_found": True,
        "answer_generation_ready": True,
        "free_form_answer_generated": False,
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
    projection_report = OracleNaturalLanguageIntelligenceProjectionReport(
        **projection_report_body,
        report_hash=oit_041_hash(projection_report_body),
    )

    binding_body = {
        "source_follow_up_report_hash": "follow-up-report-046",
        "source_context_assembly_report_hash": "context-report-046",
        "source_session_context_hash": "volatile-session-context-046",
        "resolved_query": resolved_query,
        "normalized_query": "Has it changed now?",
        "follow_up_detected": True,
        "primary_reference_turn_index": 1,
        "resolution_confidence": 0.70,
        "projection_report_hash": projection_report.report_hash,
        "projection_hash": projection.projection_hash,
        "projected_field_count": len(fields),
        "relevant_context_found": True,
        "exact_cross_stage_lineage_verified": True,
        "read_only": True,
    }
    binding = OracleResolvedFollowUpProjectionBinding(
        **binding_body,
        binding_hash=oit_045_hash(binding_body),
    )

    reentry_body = {
        "schema_version": OIT_045_SCHEMA_VERSION,
        "engine_id": OIT_045_ENGINE_ID,
        "policy_id": OIT_045_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "follow_up_resolution_report_hash": "follow-up-report-046",
        "context_assembly_report_hash": "context-report-046",
        "projection_report": projection_report,
        "projection_binding": binding,
        "reentry_performed": True,
        "answer_generation_ready": True,
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
    reentry = OracleResolvedFollowUpProjectionReentryReport(
        **reentry_body,
        report_hash=oit_045_hash(reentry_body),
    )
    verify_resolved_follow_up_projection_reentry_report(reentry)
    return reentry


def main() -> int:
    print("=" * 48)
    print(" OIT-046 TEST")
    print(" FINAL INTELLIGENCE ANSWER ASSEMBLY")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        reentry = make_reentry_report(root)

        report = build_final_intelligence_answer_assembly_report(
            root,
            reentry_report=reentry,
        )

        assert report.final_answer_assembled
        assert report.conversation_rendering_ready
        assert not report.unsupported_claims_generated

        package = report.final_answer_package
        assert package.terminal_render_ready
        assert package.deterministic_assembly
        assert package.bounded_answer
        assert package.all_claims_evidence_linked
        assert package.follow_up_detected
        assert package.resolution_confidence == 0.70
        assert package.lineage.exact_lineage_verified
        assert (
            package.lineage.source_reentry_report_hash
            == reentry.report_hash
        )
        assert (
            package.lineage.source_follow_up_resolution_report_hash
            == reentry.follow_up_resolution_report_hash
        )
        assert (
            package.lineage.source_context_assembly_report_hash
            == reentry.context_assembly_report_hash
        )
        assert (
            package.lineage.source_projection_report_hash
            == reentry.projection_report.report_hash
        )
        assert (
            package.lineage.source_projection_hash
            == reentry.projection_report.projection.projection_hash
        )
        assert (
            package.lineage.source_answer_generation_report_hash
            == report.answer_generation_report.report_hash
        )
        assert (
            package.lineage.source_answer_hash
            == package.answer.answer_hash
        )
        assert (
            package.lineage.source_session_context_hash
            == reentry.projection_binding.source_session_context_hash
        )
        assert package.lineage.primary_reference_turn_index == 1

        assert package.answer_line_count == (
            package.answer.answer_line_count
        )
        assert package.answer_line_count == 6
        assert package.answer.summary_line_count == 1
        assert package.answer.evidence_line_count == 2
        assert package.answer.uncertainty_line_count == 1

        replay = build_final_intelligence_answer_assembly_report(
            root,
            reentry_report=reentry,
        )
        assert replay == report
        assert verify_final_intelligence_answer_assembly_report(
            report
        )

        tampered = replace(
            report,
            persistent_memory_enabled=True,
        )
        try:
            verify_final_intelligence_answer_assembly_report(
                tampered
            )
        except OracleFinalIntelligenceAnswerAssemblyInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered OIT-046 report accepted"
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

    print("[PASS] Certified OIT-045 reentry report consumed")
    print("[PASS] Certified OIT-042 answer generator invoked")
    print("[PASS] Final evidence-linked answer assembled")
    print("[PASS] Follow-up and resolution metadata preserved")
    print("[PASS] OIT-043 volatile-session lineage preserved")
    print("[PASS] OIT-040 intelligence-context lineage preserved")
    print("[PASS] OIT-041 projection lineage preserved")
    print("[PASS] OIT-042 answer lineage preserved")
    print("[PASS] Exact cross-stage hashes verified")
    print("[PASS] Conversation-rendering readiness certified")
    print("[PASS] Assembly deterministic across replay")
    print("[PASS] Tampered assembly report rejected")
    print("[PASS] Persistent memory and learning remained disabled")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-046 FINAL INTELLIGENCE ANSWER ASSEMBLY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
