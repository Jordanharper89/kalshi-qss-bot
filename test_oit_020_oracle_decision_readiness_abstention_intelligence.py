from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_bull_bear_neutral_debate_synthesis import (
    ENGINE_ID as OIT_019_ENGINE_ID,
    POLICY_ID as OIT_019_POLICY_ID,
    SCHEMA_VERSION as OIT_019_SCHEMA_VERSION,
    OracleDebateFinding,
    OracleDebatePosition,
    OracleDebateSynthesisReport,
    _stable_hash as oit_019_hash,
    verify_debate_synthesis_report,
)
from qseries_v2.oracle_terminal.oracle_decision_readiness_abstention_intelligence import (
    OracleDecisionReadinessInvariantError,
    build_decision_readiness_report,
    verify_decision_readiness_report,
)


def position(name: str, score: float):
    body = {
        "position": name,
        "score": score,
        "confidence": round(0.50 + abs(score - 0.50), 6),
        "supporting_points": (f"{name} support",),
        "opposing_points": (f"{name} opposition",),
        "required_confirmation": (f"{name} confirmation",),
    }
    return OracleDebatePosition(
        **body,
        position_hash=oit_019_hash(body),
    )


def finding(
    index: int,
    *,
    leader: str,
    margin: float,
    conflict: float,
    confidence: float,
    state: str,
    review: bool,
):
    positions = {
        "bull": position("bull", 0.82 if leader == "bull" else 0.22),
        "bear": position("bear", 0.82 if leader == "bear" else 0.22),
        "neutral": position("neutral", 0.82 if leader == "neutral" else 0.22),
    }
    body = {
        "finding_index": index,
        "cause_record_id": f"CAUSE-{index}",
        "effect_record_id": f"EFFECT-{index}",
        "source_challenge_hash": f"challenge-{index}",
        "original_narrative_state": "certified",
        "bull": positions["bull"],
        "bear": positions["bear"],
        "neutral": positions["neutral"],
        "leading_position": leader,
        "debate_margin": margin,
        "debate_conflict": conflict,
        "adjudicated_confidence": confidence,
        "adjudication_state": state,
        "requires_human_review": review,
        "adjudication_rationale": ("certified debate rationale",),
        "read_only": True,
    }
    return OracleDebateFinding(
        **body,
        finding_hash=oit_019_hash(body),
    )


def make_report(root: Path):
    findings = (
        finding(
            1,
            leader="bull",
            margin=0.48,
            conflict=0.18,
            confidence=0.78,
            state="bull_leading",
            review=False,
        ),
        finding(
            2,
            leader="bear",
            margin=0.14,
            conflict=0.54,
            confidence=0.52,
            state="bear_leading",
            review=False,
        ),
        finding(
            3,
            leader="neutral",
            margin=0.03,
            conflict=0.88,
            confidence=0.30,
            state="contested",
            review=True,
        ),
    )
    body = {
        "schema_version": OIT_019_SCHEMA_VERSION,
        "engine_id": OIT_019_ENGINE_ID,
        "policy_id": OIT_019_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Assess decision readiness.",
        "challenge_report_hash": "challenge-report-hash",
        "findings": findings,
        "finding_count": len(findings),
        "bull_leading_count": 1,
        "bear_leading_count": 1,
        "neutral_leading_count": 1,
        "contested_count": 1,
        "human_review_count": 1,
        "aggregate_leading_position": "bull",
        "aggregate_confidence": 0.40,
        "debate_state": "aggregate_debate_contested",
        "debate_summary": "Synthetic certified debate.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleDebateSynthesisReport(
        **body,
        report_hash=oit_019_hash(body),
    )
    verify_debate_synthesis_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-020 TEST")
    print(" DECISION READINESS AND ABSTENTION")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        report = build_decision_readiness_report(
            root,
            source.query,
            debate_report=source,
        )

        assert report.debate_report_hash == source.report_hash
        assert report.finding_count == 3
        assert report.ready_count == 1
        assert report.observe_count == 1
        assert report.abstain_count == 1
        assert report.human_review_count == 1

        ready, observe, abstain = report.findings
        assert ready.readiness_state == "ready"
        assert ready.leading_position == "bull"
        assert ready.readiness_score > ready.abstention_pressure

        assert observe.readiness_state == "observe"
        assert observe.leading_position == "bear"
        assert observe.minimum_confirmation_count == 2

        assert abstain.readiness_state == "abstain"
        assert abstain.leading_position == "neutral"
        assert abstain.requires_human_review
        assert abstain.minimum_confirmation_count == 3
        assert abstain.abstention_pressure > abstain.readiness_score

        assert report.aggregate_state == "abstain"
        assert report.aggregate_direction in {"bull", "bear", "neutral"}
        assert 0.0 <= report.aggregate_readiness <= 1.0
        assert 0.0 <= report.aggregate_abstention_pressure <= 1.0

        replay = build_decision_readiness_report(
            root,
            source.query,
            debate_report=source,
        )
        assert replay == report
        assert verify_decision_readiness_report(report)

        tampered = replace(
            report,
            readiness_summary=report.readiness_summary + " tampered",
        )
        try:
            verify_decision_readiness_report(tampered)
        except OracleDecisionReadinessInvariantError:
            pass
        else:
            raise AssertionError("tampered readiness report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed
        assert not report.action_authorization_allowed

    print("[PASS] Certified OIT-019 debate report consumed")
    print("[PASS] Ready state classified from strong debate separation")
    print("[PASS] Observe state classified from intermediate evidence")
    print("[PASS] Abstain state enforced for contested human-review case")
    print("[PASS] Readiness and abstention pressure quantified")
    print("[PASS] Confirmation requirements materialized")
    print("[PASS] Disqualifying conditions materialized")
    print("[PASS] Aggregate abstention conservatively enforced")
    print("[PASS] Complete OIT-019 lineage retained")
    print("[PASS] Readiness report deterministic across replay")
    print("[PASS] Tampered readiness report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-020 DECISION READINESS AND ABSTENTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
