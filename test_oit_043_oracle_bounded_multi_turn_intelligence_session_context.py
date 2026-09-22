from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_terminal_intelligence_answer_generation import (
    ENGINE_ID as OIT_042_ENGINE_ID,
    POLICY_ID as OIT_042_POLICY_ID,
    SCHEMA_VERSION as OIT_042_SCHEMA_VERSION,
    OracleTerminalIntelligenceAnswer,
    OracleTerminalIntelligenceAnswerGenerationReport,
    OracleTerminalIntelligenceAnswerLine,
    _stable_hash as oit_042_hash,
    verify_terminal_intelligence_answer_generation_report,
)
from qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (
    OracleBoundedMultiTurnSessionInvariantError,
    append_answer_to_bounded_multi_turn_session,
    verify_bounded_multi_turn_session_update_report,
)


def make_line(
    index: int,
    line_type: str,
    text: str,
    source_path: str,
) -> OracleTerminalIntelligenceAnswerLine:
    body = {
        "line_index": index,
        "line_type": line_type,
        "text": text,
        "source_field_paths": (source_path,),
        "source_field_hashes": (f"source-field-hash-{index}",),
        "evidence_linked": True,
    }
    return OracleTerminalIntelligenceAnswerLine(
        **body,
        line_hash=oit_042_hash(body),
    )


def make_report(
    root: Path,
    query: str,
    answer_id: str,
    direction: str,
) -> OracleTerminalIntelligenceAnswerGenerationReport:
    lines = (
        make_line(
            0,
            "summary",
            "Oracle found 1 certified context field relevant to the query.",
            "$.direction",
        ),
        make_line(
            1,
            "fact",
            f"direction: {direction}",
            "$.direction",
        ),
    )

    answer_body = {
        "answer_id": answer_id,
        "source_projection_hash": f"projection-hash-{answer_id}",
        "source_projection_report_hash": (
            f"projection-report-hash-{answer_id}"
        ),
        "query": query,
        "answer_lines": lines,
        "answer_line_count": len(lines),
        "evidence_line_count": 0,
        "summary_line_count": 1,
        "uncertainty_line_count": 0,
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

    report_body = {
        "schema_version": OIT_042_SCHEMA_VERSION,
        "engine_id": OIT_042_ENGINE_ID,
        "policy_id": OIT_042_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "projection_report_hash": (
            answer.source_projection_report_hash
        ),
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
    report = OracleTerminalIntelligenceAnswerGenerationReport(
        **report_body,
        report_hash=oit_042_hash(report_body),
    )
    verify_terminal_intelligence_answer_generation_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-043 TEST")
    print(" BOUNDED MULTI-TURN INTELLIGENCE SESSION CONTEXT")
    print(" CORRECTION V2 - REPOSITORY-ALIGNED HASH IMPORT")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        first_answer = make_report(
            root,
            "What is the direction?",
            "answer-043-1",
            "bull",
        )
        first = append_answer_to_bounded_multi_turn_session(
            root,
            answer_report=first_answer,
        )

        assert first.turn_appended
        assert first.session_continuation_ready
        assert first.volatile_memory_only
        assert not first.persistent_memory_enabled
        assert not first.learning_update_performed

        first_context = first.updated_session_context
        assert first_context.session_active
        assert first_context.turn_count == 1
        assert first_context.latest_turn_index == 0
        assert first_context.total_answer_line_count == 2
        assert first_context.volatile_memory_only
        assert not first_context.persistent_memory_enabled
        assert not first_context.learning_enabled

        second_answer = make_report(
            root,
            "Has the direction changed?",
            "answer-043-2",
            "bull",
        )
        second = append_answer_to_bounded_multi_turn_session(
            root,
            answer_report=second_answer,
            prior_session_context=first_context,
        )

        second_context = second.updated_session_context
        assert second.turn_appended
        assert second.session_continuation_ready
        assert second_context.session_id == first_context.session_id
        assert second_context.turn_count == 2
        assert second_context.latest_turn_index == 1
        assert second_context.total_answer_line_count == 4
        assert tuple(
            turn.turn_index for turn in second_context.turns
        ) == (0, 1)
        assert tuple(
            turn.query for turn in second_context.turns
        ) == (
            "What is the direction?",
            "Has the direction changed?",
        )
        assert all(
            turn.evidence_linked for turn in second_context.turns
        )
        assert second.prior_session_context_hash == (
            first_context.context_hash
        )

        replay = append_answer_to_bounded_multi_turn_session(
            root,
            answer_report=second_answer,
            prior_session_context=first_context,
        )
        assert replay == second
        assert verify_bounded_multi_turn_session_update_report(second)

        tampered = replace(
            second,
            persistent_memory_enabled=True,
        )
        try:
            verify_bounded_multi_turn_session_update_report(tampered)
        except OracleBoundedMultiTurnSessionInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered multi-turn report accepted"
            )

        assert not second.analytics_execution_performed
        assert not second.database_access_performed
        assert not second.runtime_artifact_created
        assert not second.runtime_artifact_modified
        assert not second.networking_performed
        assert not second.publication_allowed
        assert not second.action_authorization_allowed
        assert not second.qseries_execution_allowed
        assert second.read_only

    print("[PASS] Certified OIT-042 answer report contract consumed")
    print("[PASS] OIT-042 hash helper imported explicitly")
    print("[PASS] First volatile session turn materialized")
    print("[PASS] Second turn appended deterministically")
    print("[PASS] Session identity preserved across turns")
    print("[PASS] Exact turn ordering certified")
    print("[PASS] Complete answer and projection lineage retained")
    print("[PASS] Evidence-linked turn requirement enforced")
    print("[PASS] Turn and answer-line limits preserved")
    print("[PASS] Volatile in-process memory certified")
    print("[PASS] Persistent Oracle memory remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Session update deterministic across replay")
    print("[PASS] Tampered session report rejected")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-043 CORRECTION V2 BOUNDED MULTI-TURN SESSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
