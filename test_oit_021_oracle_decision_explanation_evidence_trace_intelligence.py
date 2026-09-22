from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_decision_readiness_abstention_intelligence import (
    ENGINE_ID as OIT_020_ENGINE_ID,
    POLICY_ID as OIT_020_POLICY_ID,
    SCHEMA_VERSION as OIT_020_SCHEMA_VERSION,
    OracleDecisionReadinessFinding,
    OracleDecisionReadinessReport,
    _stable_hash as oit_020_hash,
    verify_decision_readiness_report,
)
from qseries_v2.oracle_terminal.oracle_decision_explanation_evidence_trace_intelligence import (
    OracleDecisionExplanationInvariantError,
    build_decision_explanation_report,
    verify_decision_explanation_report,
)


def readiness_finding(index: int, state: str, direction: str):
    values = {
        "ready": (0.78, 0.24, False, 1),
        "observe": (0.48, 0.52, False, 2),
        "abstain": (0.20, 0.82, True, 3),
    }
    readiness, abstention, review, minimum = values[state]
    body = {
        "finding_index": index,
        "cause_record_id": f"CAUSE-{index}",
        "effect_record_id": f"EFFECT-{index}",
        "source_debate_hash": f"debate-{index}",
        "leading_position": direction,
        "debate_margin": 0.40 if state == "ready" else 0.12 if state == "observe" else 0.03,
        "debate_conflict": 0.20 if state == "ready" else 0.55 if state == "observe" else 0.90,
        "adjudicated_confidence": 0.80 if state == "ready" else 0.50 if state == "observe" else 0.25,
        "requires_human_review": review,
        "readiness_score": readiness,
        "abstention_pressure": abstention,
        "readiness_state": state,
        "directional_interpretation": direction if state == "ready" else f"non_actionable_{direction}",
        "minimum_confirmation_count": minimum,
        "required_confirmations": (
            "confirm directional persistence",
            "confirm margin stability",
        ),
        "disqualifying_conditions": (
            "direction changes",
            "lineage verification fails",
        ),
        "rationale": ("certified readiness rationale",),
        "read_only": True,
    }
    return OracleDecisionReadinessFinding(
        **body,
        finding_hash=oit_020_hash(body),
    )


def make_report(root: Path):
    findings = (
        readiness_finding(1, "ready", "bull"),
        readiness_finding(2, "observe", "bear"),
        readiness_finding(3, "abstain", "neutral"),
    )
    body = {
        "schema_version": OIT_020_SCHEMA_VERSION,
        "engine_id": OIT_020_ENGINE_ID,
        "policy_id": OIT_020_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Explain decision readiness.",
        "debate_report_hash": "debate-report-hash",
        "findings": findings,
        "finding_count": 3,
        "ready_count": 1,
        "observe_count": 1,
        "abstain_count": 1,
        "human_review_count": 1,
        "aggregate_state": "abstain",
        "aggregate_direction": "bull",
        "aggregate_readiness": 0.486667,
        "aggregate_abstention_pressure": 0.526667,
        "readiness_summary": "Synthetic readiness report.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    report = OracleDecisionReadinessReport(
        **body,
        report_hash=oit_020_hash(body),
    )
    verify_decision_readiness_report(report)
    return report


def main() -> int:
    print("=" * 48)
    print(" OIT-021 TEST")
    print(" DECISION EXPLANATION AND EVIDENCE TRACE")
    print("=" * 48)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        report = build_decision_explanation_report(
            root,
            source.query,
            readiness_report=source,
        )

        assert report.readiness_report_hash == source.report_hash
        assert report.finding_count == 3
        assert report.explained_count == 3
        assert report.ready_explained_count == 1
        assert report.observe_explained_count == 1
        assert report.abstain_explained_count == 1
        assert report.operator_attention_count == 1
        assert report.explanation_state == "complete"

        ready, observe, abstain = report.findings
        assert "ready for operator consideration" in ready.concise_explanation
        assert "remains observational" in observe.concise_explanation
        assert "blocked by abstention" in abstain.concise_explanation
        assert not ready.operator_attention_required
        assert abstain.operator_attention_required

        for finding in report.findings:
            assert finding.explanation_complete
            assert len(finding.evidence_trace) == 6
            assert finding.confirmation_plan
            assert finding.blocking_conditions
            assert finding.source_readiness_hash
            for trace in finding.evidence_trace:
                assert trace.readiness_finding_hash == finding.source_readiness_hash

        replay = build_decision_explanation_report(
            root,
            source.query,
            readiness_report=source,
        )
        assert replay == report
        assert verify_decision_explanation_report(report)

        tampered = replace(
            report,
            explanation_summary=report.explanation_summary + " tampered",
        )
        try:
            verify_decision_explanation_report(tampered)
        except OracleDecisionExplanationInvariantError:
            pass
        else:
            raise AssertionError("tampered explanation report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed
        assert not report.action_authorization_allowed

    print("[PASS] Certified OIT-020 readiness report consumed")
    print("[PASS] Ready-state explanation materialized")
    print("[PASS] Observe-state explanation materialized")
    print("[PASS] Abstain-state explanation materialized")
    print("[PASS] Evidence trace bound to readiness and debate lineage")
    print("[PASS] Confirmation plan preserved")
    print("[PASS] Blocking conditions preserved")
    print("[PASS] Operator-attention requirement surfaced")
    print("[PASS] Complete OIT-020 lineage retained")
    print("[PASS] Explanation report deterministic across replay")
    print("[PASS] Tampered explanation report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-021 DECISION EXPLANATION AND EVIDENCE TRACE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
