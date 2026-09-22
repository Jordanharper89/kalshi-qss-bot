from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_bounded_multi_turn_intelligence_session_context import (
    OracleBoundedMultiTurnSessionContext,
    OracleIntelligenceConversationTurn,
    _stable_hash as oit_043_hash,
    verify_multi_turn_session_context,
)
from qseries_v2.oracle_terminal.oracle_multi_turn_follow_up_query_context_resolution import (
    OracleFollowUpQueryResolutionInvariantError,
    resolve_multi_turn_follow_up_query,
    verify_follow_up_query_resolution_report,
)


def make_turn(
    index: int,
    query: str,
    answer_id: str,
) -> OracleIntelligenceConversationTurn:
    body = {
        "turn_index": index,
        "query": query,
        "answer_id": answer_id,
        "answer_hash": f"answer-hash-{index}",
        "answer_line_count": 2,
        "source_answer_report_hash": (
            f"answer-report-hash-{index}"
        ),
        "source_projection_report_hash": (
            f"projection-report-hash-{index}"
        ),
        "evidence_linked": True,
        "read_only": True,
    }
    return OracleIntelligenceConversationTurn(
        **body,
        turn_hash=oit_043_hash(body),
    )


def make_session() -> OracleBoundedMultiTurnSessionContext:
    turns = (
        make_turn(
            0,
            "What is the market direction?",
            "answer-044-0",
        ),
        make_turn(
            1,
            "What evidence supports the bull direction?",
            "answer-044-1",
        ),
    )

    body = {
        "session_id": "session-044",
        "turns": turns,
        "turn_count": len(turns),
        "total_answer_line_count": 4,
        "latest_turn_index": 1,
        "bounded_turn_count": True,
        "bounded_line_count": True,
        "deterministic_ordering_applied": True,
        "complete_lineage_preserved": True,
        "volatile_memory_only": True,
        "persistent_memory_enabled": False,
        "learning_enabled": False,
        "session_active": True,
        "read_only": True,
    }
    context = OracleBoundedMultiTurnSessionContext(
        **body,
        context_hash=oit_043_hash(body),
    )
    verify_multi_turn_session_context(context)
    return context


def main() -> int:
    print("=" * 48)
    print(" OIT-044 TEST")
    print(" MULTI-TURN FOLLOW-UP QUERY CONTEXT RESOLUTION")
    print(" OIT-043 CORRECTION V2 BASELINE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        session = make_session()

        follow_up = resolve_multi_turn_follow_up_query(
            root,
            session_context=session,
            query="Has it changed now?",
        )

        assert follow_up.context_resolution_performed
        assert follow_up.downstream_projection_ready

        resolved = follow_up.resolved_follow_up_query
        assert resolved.follow_up_detected
        assert not resolved.standalone_query
        assert resolved.referenced_turn_count >= 1
        assert resolved.primary_reference_turn_index == 1
        assert (
            "What evidence supports the bull direction?"
            in resolved.resolved_query
        )
        assert 0.5 <= resolved.resolution_confidence <= 1.0
        assert resolved.session_lineage_preserved
        assert resolved.resolution_ready

        standalone = resolve_multi_turn_follow_up_query(
            root,
            session_context=session,
            query="Show probability for REAL-044",
        )

        standalone_resolved = (
            standalone.resolved_follow_up_query
        )
        assert not standalone.context_resolution_performed
        assert standalone.downstream_projection_ready
        assert standalone_resolved.standalone_query
        assert not standalone_resolved.follow_up_detected
        assert standalone_resolved.referenced_turn_count == 0
        assert standalone_resolved.resolved_query == (
            "Show probability for REAL-044"
        )
        assert standalone_resolved.resolution_confidence == 1.0

        replay = resolve_multi_turn_follow_up_query(
            root,
            session_context=session,
            query="Has it changed now?",
        )
        assert replay == follow_up
        assert verify_follow_up_query_resolution_report(
            follow_up
        )

        tampered = replace(
            follow_up,
            persistent_memory_enabled=True,
        )
        try:
            verify_follow_up_query_resolution_report(tampered)
        except OracleFollowUpQueryResolutionInvariantError:
            pass
        else:
            raise AssertionError(
                "tampered follow-up resolution report accepted"
            )

        assert not follow_up.learning_update_performed
        assert not follow_up.analytics_execution_performed
        assert not follow_up.database_access_performed
        assert not follow_up.runtime_artifact_created
        assert not follow_up.runtime_artifact_modified
        assert not follow_up.networking_performed
        assert not follow_up.publication_allowed
        assert not follow_up.action_authorization_allowed
        assert not follow_up.qseries_execution_allowed
        assert follow_up.read_only

    print("[PASS] Certified OIT-043 Correction V2 session consumed")
    print("[PASS] Short contextual follow-up detected")
    print("[PASS] Latest relevant prior turn selected")
    print("[PASS] Prior query context appended deterministically")
    print("[PASS] Resolution confidence bounded")
    print("[PASS] Standalone query preserved unchanged")
    print("[PASS] Exact turn and answer lineage retained")
    print("[PASS] Downstream projection readiness certified")
    print("[PASS] Persistent memory remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Resolution deterministic across replay")
    print("[PASS] Tampered resolution report rejected")
    print("[PASS] No analytics execution or runtime mutation performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-044 FOLLOW-UP QUERY CONTEXT RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
