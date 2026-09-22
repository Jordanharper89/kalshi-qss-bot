from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (
    OracleTerminalIntelligenceAnswer,
    OracleTerminalIntelligenceAnswerLine,
    _stable_hash as oit_042_hash,
)
from qseries_v2.oracle_terminal.oracle_final_intelligence_answer_assembly import (
    ENGINE_ID as OIT_046_ENGINE_ID,
    POLICY_ID as OIT_046_POLICY_ID,
    SCHEMA_VERSION as OIT_046_SCHEMA_VERSION,
    OracleFinalIntelligenceAnswerAssemblyReport,
    OracleFinalIntelligenceAnswerLineage,
    OracleFinalIntelligenceAnswerPackage,
    _stable_hash as oit_046_hash,
    verify_final_intelligence_answer_assembly_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (
    ENGINE_ID as OIT_042_ENGINE_ID,
    POLICY_ID as OIT_042_POLICY_ID,
    SCHEMA_VERSION as OIT_042_SCHEMA_VERSION,
    OracleTerminalIntelligenceAnswerGenerationReport,
)
from qseries_v2.oracle_terminal.oracle_conversation_response_rendering import (
    OracleConversationResponseRenderingInvariantError,
    build_conversation_response_rendering_report,
    verify_conversation_response_rendering_report,
)


def answer_line(
    index: int,
    line_type: str,
    text: str,
    source_path: str,
):
    body = {
        "line_index": index,
        "line_type": line_type,
        "text": text,
        "source_field_paths": (source_path,),
        "source_field_hashes": (f"field-hash-{index}",),
        "evidence_linked": True,
    }
    return OracleTerminalIntelligenceAnswerLine(
        **body,
        line_hash=oit_042_hash(body),
    )


def make_assembly_report(root: Path):
    lines = (
        answer_line(
            0,
            "summary",
            "Oracle found 3 certified context fields relevant to the query.",
            "$.direction",
        ),
        answer_line(
            1,
            "fact",
            "direction: bull",
            "$.direction",
        ),
        answer_line(
            2,
            "evidence",
            "evidence.0.source_id: SOURCE-047",
            "$.evidence[0].source_id",
        ),
        answer_line(
            3,
            "uncertainty",
            "Uncertainty remains bounded by probability 0.81.",
            "$.probability",
        ),
    )

    answer_body = {
        "answer_id": "answer-047",
        "source_projection_hash": "projection-hash-047",
        "source_projection_report_hash": "projection-report-hash-047",
        "query": "Has it changed now?",
        "answer_lines": lines,
        "answer_line_count": len(lines),
        "evidence_line_count": 1,
        "summary_line_count": 1,
        "uncertainty_line_count": 1,
        "all_claims_evidence_linked": True,
        "deterministic_ordering_applied": True,
        "bounded_answer": True,
        "answer_ready": True,
        "read_only": True,
    }
    answer = OracleTerminalIntelligenceAnswer(
        **answer_body,
        answer_hash=oit_042_hash(answer_body),
    )

    answer_report_body = {
        "schema_version": OIT_042_SCHEMA_VERSION,
        "engine_id": OIT_042_ENGINE_ID,
        "policy_id": OIT_042_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "projection_report_hash": "projection-report-hash-047",
        "answer": answer,
        "answer_generated": True,
        "answer_render_ready": True,
        "unsupported_claims_generated": False,
        "free_form_generation_used": False,
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
    answer_report = OracleTerminalIntelligenceAnswerGenerationReport(
        **answer_report_body,
        report_hash=oit_042_hash(answer_report_body),
    )

    lineage_body = {
        "source_reentry_report_hash": "reentry-report-hash-047",
        "source_follow_up_resolution_report_hash": "follow-up-report-hash-047",
        "source_context_assembly_report_hash": "context-report-hash-047",
        "source_projection_report_hash": "projection-report-hash-047",
        "source_projection_hash": "projection-hash-047",
        "source_answer_generation_report_hash": answer_report.report_hash,
        "source_answer_hash": answer.answer_hash,
        "source_session_context_hash": "session-context-hash-047",
        "primary_reference_turn_index": 1,
        "exact_lineage_verified": True,
    }
    lineage = OracleFinalIntelligenceAnswerLineage(
        **lineage_body,
        lineage_hash=oit_046_hash(lineage_body),
    )

    package_body = {
        "package_id": "package-047",
        "query": "Has it changed now?",
        "resolved_query": (
            "Has it changed now? [context from prior query: "
            "What evidence supports the bull direction?]"
        ),
        "follow_up_detected": True,
        "resolution_confidence": 0.70,
        "answer": answer,
        "lineage": lineage,
        "answer_line_count": len(lines),
        "all_claims_evidence_linked": True,
        "deterministic_assembly": True,
        "bounded_answer": True,
        "terminal_render_ready": True,
        "read_only": True,
    }
    package = OracleFinalIntelligenceAnswerPackage(
        **package_body,
        package_hash=oit_046_hash(package_body),
    )

    report_body = {
        "schema_version": OIT_046_SCHEMA_VERSION,
        "engine_id": OIT_046_ENGINE_ID,
        "policy_id": OIT_046_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "reentry_report_hash": "reentry-report-hash-047",
        "answer_generation_report": answer_report,
        "final_answer_package": package,
        "final_answer_assembled": True,
        "conversation_rendering_ready": True,
        "unsupported_claims_generated": False,
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
    report = OracleFinalIntelligenceAnswerAssemblyReport(
        **report_body,
        report_hash=oit_046_hash(report_body),
    )
    verify_final_intelligence_answer_assembly_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-047 TEST")
    print(" CONVERSATION RESPONSE RENDERING")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        assembly = make_assembly_report(root)

        report = build_conversation_response_rendering_report(
            root,
            final_answer_assembly_report=assembly,
        )

        assert report.rendering_completed
        assert report.interactive_pipeline_ready
        assert report.exact_answer_text_preserved
        assert not report.unsupported_content_generated

        frame = report.response_frame
        assert frame.terminal_display_ready
        assert frame.frame_type == "oracle_conversation_response"
        assert frame.title == "Oracle Intelligence Response"
        assert "follow-up context resolved" in frame.subtitle
        assert frame.line_count == 4
        assert frame.bounded_frame
        assert frame.deterministic_ordering_applied
        assert frame.source_package_hash == (
            assembly.final_answer_package.package_hash
        )
        assert frame.source_answer_hash == (
            assembly.final_answer_package.answer.answer_hash
        )
        assert frame.source_lineage_hash == (
            assembly.final_answer_package.lineage.lineage_hash
        )

        original_text = tuple(
            line.text
            for line in assembly.final_answer_package.answer.answer_lines
        )
        rendered_text = tuple(
            line.text for line in frame.lines
        )
        assert rendered_text == original_text

        assert tuple(
            line.render_type for line in frame.lines
        ) == (
            "summary",
            "fact",
            "evidence",
            "uncertainty",
        )

        assert all(line.evidence_linked for line in frame.lines)
        assert all(
            line.source_answer_line_hashes
            for line in frame.lines
        )
        assert all(
            line.source_field_paths
            for line in frame.lines
        )

        replay = build_conversation_response_rendering_report(
            root,
            final_answer_assembly_report=assembly,
        )
        assert replay == report
        assert verify_conversation_response_rendering_report(
            report
        )

        tampered = replace(
            report,
            unsupported_content_generated=True,
        )
        try:
            verify_conversation_response_rendering_report(
                tampered
            )
        except OracleConversationResponseRenderingInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered OIT-047 report accepted"
            )

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

    print("[PASS] Certified OIT-046 final answer consumed")
    print("[PASS] Conversation response frame materialized")
    print("[PASS] Exact answer text preserved")
    print("[PASS] Summary, fact, evidence, and uncertainty lines rendered")
    print("[PASS] Answer-line hashes retained")
    print("[PASS] Source field paths retained")
    print("[PASS] Final package and lineage hashes retained")
    print("[PASS] Follow-up context surfaced in frame subtitle")
    print("[PASS] Deterministic render ordering certified")
    print("[PASS] Bounded frame limit enforced")
    print("[PASS] Interactive pipeline readiness certified")
    print("[PASS] Rendering deterministic across replay")
    print("[PASS] Tampered rendering report rejected")
    print("[PASS] Persistent memory and learning remained disabled")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-047 CONVERSATION RESPONSE RENDERING PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
