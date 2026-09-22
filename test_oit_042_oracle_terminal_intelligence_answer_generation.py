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
    verify_natural_language_intelligence_projection_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (
    OracleTerminalIntelligenceAnswerInvariantError,
    build_terminal_intelligence_answer_generation_report,
    verify_terminal_intelligence_answer_generation_report,
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


def make_projection_report(root: Path):
    intent_body = {
        "raw_query": "What evidence supports the bull direction?",
        "normalized_query": "What evidence supports the bull direction?",
        "query_terms": (
            "what",
            "evidence",
            "supports",
            "the",
            "bull",
            "direction",
        ),
        "distinctive_terms": (
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
            "SOURCE-ALPHA",
            "SOURCE-ALPHA",
            ("evidence",),
            35,
            "distinctive_term_match+evidence_request",
            1,
        ),
        projected_field(
            "evidence.0.confidence",
            "$.evidence[0].confidence",
            "number",
            0.84,
            "0.84",
            ("evidence",),
            35,
            "distinctive_term_match+evidence_request",
            2,
        ),
        projected_field(
            "probability",
            "$.probability",
            "number",
            0.78,
            "0.78",
            (),
            1,
            "root_context",
            3,
        ),
    )

    projection_body = {
        "projection_id": "projection-042",
        "source_context_hash": "context-hash",
        "source_context_report_hash": "context-report-hash",
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

    report_body = {
        "schema_version": OIT_041_SCHEMA_VERSION,
        "engine_id": OIT_041_ENGINE_ID,
        "policy_id": OIT_041_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "context_assembly_report_hash": "context-report-hash",
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
    report = OracleNaturalLanguageIntelligenceProjectionReport(
        **report_body,
        report_hash=oit_041_hash(report_body),
    )
    verify_natural_language_intelligence_projection_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-042 TEST")
    print(" TERMINAL INTELLIGENCE ANSWER GENERATION")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        projection = make_projection_report(root)

        report = build_terminal_intelligence_answer_generation_report(
            root,
            projection_report=projection,
        )

        assert report.answer_generated
        assert report.answer_render_ready
        assert not report.unsupported_claims_generated
        assert not report.free_form_generation_used

        answer = report.answer
        assert answer.answer_ready
        assert answer.bounded_answer
        assert answer.all_claims_evidence_linked
        assert answer.summary_line_count == 1
        assert answer.evidence_line_count == 2
        assert answer.uncertainty_line_count == 1
        assert answer.answer_line_count == 6

        texts = tuple(line.text for line in answer.answer_lines)
        assert texts[0] == (
            "Oracle found 4 certified context fields relevant to the query."
        )
        assert "direction: bull" in texts
        assert "evidence.0.source_id: SOURCE-ALPHA" in texts
        assert "evidence.0.confidence: 0.84" in texts
        assert "probability: 0.78" in texts
        assert texts[-1].startswith(
            "Uncertainty remains bounded"
        )

        for line in answer.answer_lines:
            assert line.evidence_linked
            assert line.source_field_paths
            assert line.source_field_hashes

        replay = build_terminal_intelligence_answer_generation_report(
            root,
            projection_report=projection,
        )
        assert replay == report
        assert verify_terminal_intelligence_answer_generation_report(
            report
        )

        tampered = replace(
            report,
            unsupported_claims_generated=True,
        )
        try:
            verify_terminal_intelligence_answer_generation_report(
                tampered
            )
        except OracleTerminalIntelligenceAnswerInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered answer generation report accepted"
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

    print("[PASS] Certified OIT-041 projection consumed")
    print("[PASS] Deterministic answer summary generated")
    print("[PASS] Projected facts rendered")
    print("[PASS] Evidence fields rendered")
    print("[PASS] Probability and confidence uncertainty surfaced")
    print("[PASS] Every answer line bound to source fields")
    print("[PASS] Unsupported claims remained forbidden")
    print("[PASS] Free-form generation remained disabled")
    print("[PASS] Bounded answer line limit enforced")
    print("[PASS] Answer deterministic across replay")
    print("[PASS] Tampered answer report rejected")
    print("[PASS] Multi-turn memory and learning remained disabled")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-042 TERMINAL INTELLIGENCE ANSWER GENERATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
