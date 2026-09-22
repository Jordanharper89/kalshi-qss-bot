from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_decision_explanation_evidence_trace_intelligence import (
    ENGINE_ID as OIT_021_ENGINE_ID,
    POLICY_ID as OIT_021_POLICY_ID,
    SCHEMA_VERSION as OIT_021_SCHEMA_VERSION,
    OracleDecisionEvidenceTrace,
    OracleDecisionExplanationFinding,
    OracleDecisionExplanationReport,
    _stable_hash as oit_021_hash,
    verify_decision_explanation_report,
)
from qseries_v2.oracle_terminal.oracle_operator_decision_brief_assembly import (
    OracleOperatorDecisionBriefInvariantError,
    build_operator_decision_brief,
    verify_operator_decision_brief,
)


def trace(index: int, finding_hash: str, state: str):
    body = {
        "trace_index": index,
        "source_debate_hash": f"debate-{finding_hash}",
        "readiness_finding_hash": finding_hash,
        "evidence_role": "metric",
        "evidence_statement": f"evidence statement {index}",
        "supports_state": state,
    }
    return OracleDecisionEvidenceTrace(
        **body,
        trace_hash=oit_021_hash(body),
    )


def explanation_finding(index: int, state: str, direction: str):
    readiness_hash = f"readiness-{index}"
    body = {
        "finding_index": index,
        "cause_record_id": f"CAUSE-{index}",
        "effect_record_id": f"EFFECT-{index}",
        "source_readiness_hash": readiness_hash,
        "readiness_state": state,
        "directional_interpretation": (
            direction if state == "ready" else f"non_actionable_{direction}"
        ),
        "readiness_score": 0.80 if state == "ready" else 0.50 if state == "observe" else 0.20,
        "abstention_pressure": 0.20 if state == "ready" else 0.50 if state == "observe" else 0.85,
        "concise_explanation": f"{state} explanation for {direction}",
        "evidence_trace": (
            trace(1, readiness_hash, state),
            trace(2, readiness_hash, state),
        ),
        "confirmation_plan": (
            "confirm directional persistence",
            "confirm evidence remains current",
        ),
        "blocking_conditions": (
            "direction changes",
            "lineage verification fails",
        ),
        "explanation_complete": True,
        "operator_attention_required": state == "abstain",
        "read_only": True,
    }
    return OracleDecisionExplanationFinding(
        **body,
        finding_hash=oit_021_hash(body),
    )


def make_report(root: Path):
    findings = (
        explanation_finding(1, "ready", "bull"),
        explanation_finding(2, "observe", "bear"),
        explanation_finding(3, "abstain", "neutral"),
    )
    body = {
        "schema_version": OIT_021_SCHEMA_VERSION,
        "engine_id": OIT_021_ENGINE_ID,
        "policy_id": OIT_021_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Assemble an operator decision brief.",
        "readiness_report_hash": "readiness-report-hash",
        "findings": findings,
        "finding_count": 3,
        "explained_count": 3,
        "ready_explained_count": 1,
        "observe_explained_count": 1,
        "abstain_explained_count": 1,
        "operator_attention_count": 1,
        "aggregate_state": "abstain",
        "aggregate_direction": "bull",
        "explanation_state": "complete",
        "explanation_summary": "Synthetic explanation report.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    report = OracleDecisionExplanationReport(
        **body,
        report_hash=oit_021_hash(body),
    )
    verify_decision_explanation_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-022 TEST")
    print(" OPERATOR DECISION BRIEF ASSEMBLY")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        brief = build_operator_decision_brief(
            root,
            source.query,
            explanation_report=source,
        )

        assert brief.explanation_report_hash == source.report_hash
        assert brief.item_count == 3
        assert brief.ready_item_count == 1
        assert brief.observe_item_count == 1
        assert brief.abstain_item_count == 1
        assert brief.operator_attention_count == 1
        assert brief.primary_state == "abstain"
        assert brief.primary_direction == "bull"
        assert brief.terminal_consumption_ready

        assert brief.brief_items[0].readiness_state == "abstain"
        assert brief.brief_items[1].readiness_state == "observe"
        assert brief.brief_items[2].readiness_state == "ready"

        for item in brief.brief_items:
            assert item.headline
            assert item.explanation
            assert item.evidence_points
            assert item.confirmation_actions
            assert item.blocking_conditions
            assert item.source_explanation_hash
            assert item.read_only

        assert brief.operator_next_steps
        assert brief.unresolved_blockers
        assert "cannot authorize action" in brief.executive_summary

        replay = build_operator_decision_brief(
            root,
            source.query,
            explanation_report=source,
        )
        assert replay == brief
        assert verify_operator_decision_brief(brief)

        tampered = replace(
            brief,
            executive_summary=brief.executive_summary + " tampered",
        )
        try:
            verify_operator_decision_brief(tampered)
        except OracleOperatorDecisionBriefInvariantError:
            pass
        else:
            raise AssertionError("tampered operator brief accepted")

        assert brief.read_only
        assert not brief.analytics_execution_performed
        assert not brief.database_access_performed
        assert not brief.publication_allowed
        assert not brief.qseries_execution_allowed
        assert not brief.action_authorization_allowed

    print("[PASS] Certified OIT-021 explanation report consumed")
    print("[PASS] Ready, observe, and abstain items assembled")
    print("[PASS] Operator attention items prioritized first")
    print("[PASS] Evidence points materialized for terminal consumption")
    print("[PASS] Confirmation actions consolidated")
    print("[PASS] Unresolved blockers consolidated")
    print("[PASS] Executive summary materialized")
    print("[PASS] Terminal-consumption readiness certified")
    print("[PASS] Complete OIT-021 lineage retained")
    print("[PASS] Operator brief deterministic across replay")
    print("[PASS] Tampered operator brief rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-022 OPERATOR DECISION BRIEF ASSEMBLY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
