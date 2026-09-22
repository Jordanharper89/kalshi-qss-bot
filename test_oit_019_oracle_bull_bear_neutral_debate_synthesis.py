from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_narrative_challenge_self_critique_intelligence import (
    ENGINE_ID as OIT_018_ENGINE_ID,
    POLICY_ID as OIT_018_POLICY_ID,
    SCHEMA_VERSION as OIT_018_SCHEMA_VERSION,
    OracleNarrativeChallengeFinding,
    OracleNarrativeChallengeReport,
    _stable_hash as oit_018_hash,
    verify_narrative_challenge_report,
)
from qseries_v2.oracle_terminal.oracle_bull_bear_neutral_debate_synthesis import (
    OracleDebateSynthesisInvariantError,
    build_debate_synthesis_report,
    verify_debate_synthesis_report,
)


def make_challenge(
    index: int,
    cause: str,
    effect: str,
    *,
    narrative_state: str,
    challenge_state: str,
    fragility: float,
    counter: float,
    assumption: float,
    falsifiability: float,
    survival: float,
):
    body = {
        "finding_index": index,
        "cause_record_id": cause,
        "effect_record_id": effect,
        "source_narrative_hash": f"narrative-{index}",
        "original_narrative_state": narrative_state,
        "challenge_state": challenge_state,
        "fragility_score": fragility,
        "counter_evidence_pressure": counter,
        "assumption_risk": assumption,
        "falsifiability_score": falsifiability,
        "surviving_confidence": survival,
        "challenge_passed": challenge_state == "passed",
        "fragile_assumptions": (
            "the observed relationship persists out of sample",
        ),
        "counter_arguments": (
            "an alternative interpretation remains possible",
        ),
        "falsification_tests": (
            "recalculate after the next certified temporal update",
        ),
        "critique_rationale": (
            "certified challenge finding",
        ),
        "read_only": True,
    }
    return OracleNarrativeChallengeFinding(
        **body,
        finding_hash=oit_018_hash(body),
    )


def make_report(root: Path):
    findings = (
        make_challenge(
            1,
            "ETF-FLOW",
            "BTC-PRICE",
            narrative_state="strengthening",
            challenge_state="passed",
            fragility=0.18,
            counter=0.12,
            assumption=0.20,
            falsifiability=0.80,
            survival=0.82,
        ),
        make_challenge(
            2,
            "MINER-STRESS",
            "BTC-PRICE",
            narrative_state="reversing",
            challenge_state="failed",
            fragility=0.82,
            counter=0.88,
            assumption=0.76,
            falsifiability=0.70,
            survival=0.18,
        ),
        make_challenge(
            3,
            "MACRO-LIQUIDITY",
            "BTC-PRICE",
            narrative_state="fragmented",
            challenge_state="weakened",
            fragility=0.50,
            counter=0.48,
            assumption=0.62,
            falsifiability=0.55,
            survival=0.48,
        ),
    )
    body = {
        "schema_version": OIT_018_SCHEMA_VERSION,
        "engine_id": OIT_018_ENGINE_ID,
        "policy_id": OIT_018_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Debate the Bitcoin market direction.",
        "narrative_report_hash": "narrative-report-hash",
        "findings": findings,
        "finding_count": len(findings),
        "passed_count": sum(
            item.challenge_state == "passed" for item in findings
        ),
        "weakened_count": sum(
            item.challenge_state == "weakened" for item in findings
        ),
        "failed_count": sum(
            item.challenge_state == "failed" for item in findings
        ),
        "fragile_count": sum(
            item.fragility_score >= 0.45 for item in findings
        ),
        "monitoring_required_count": sum(
            item.challenge_state != "passed"
            or item.fragility_score >= 0.45
            for item in findings
        ),
        "challenge_state": "one_or_more_narratives_failed_challenge",
        "challenge_summary": "Passed, failed, and weakened narratives present.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleNarrativeChallengeReport(
        **body,
        report_hash=oit_018_hash(body),
    )
    verify_narrative_challenge_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-019 TEST")
    print(" BULL BEAR NEUTRAL DEBATE SYNTHESIS")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        report = build_debate_synthesis_report(
            root,
            source.query,
            challenge_report=source,
        )

        assert report.challenge_report_hash == source.report_hash
        assert report.finding_count == 3
        assert report.bull_leading_count >= 1
        assert report.bear_leading_count >= 1
        assert (
            report.bull_leading_count
            + report.bear_leading_count
            + report.neutral_leading_count
            == report.finding_count
        )

        first, second, third = report.findings
        assert first.leading_position == "bull"
        assert second.leading_position == "bear"
        assert first.bull.score > first.bear.score
        assert second.bear.score > second.bull.score

        for finding in report.findings:
            assert finding.bull.position == "bull"
            assert finding.bear.position == "bear"
            assert finding.neutral.position == "neutral"
            assert finding.source_challenge_hash
            assert finding.adjudication_rationale
            assert 0.0 <= finding.debate_margin <= 1.0
            assert 0.0 <= finding.debate_conflict <= 1.0
            assert 0.0 <= finding.adjudicated_confidence <= 1.0

        assert third.original_narrative_state == "fragmented"
        assert report.aggregate_leading_position in {
            "bull", "bear", "neutral"
        }
        assert 0.0 <= report.aggregate_confidence <= 1.0

        replay = build_debate_synthesis_report(
            root,
            source.query,
            challenge_report=source,
        )
        assert replay == report
        assert verify_debate_synthesis_report(report)

        tampered = replace(
            report,
            debate_summary=report.debate_summary + " tampered",
        )
        try:
            verify_debate_synthesis_report(tampered)
        except OracleDebateSynthesisInvariantError:
            pass
        else:
            raise AssertionError("tampered debate report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-018 challenge report consumed")
    print("[PASS] Bull case constructed and scored")
    print("[PASS] Bear case constructed and scored")
    print("[PASS] Neutral case constructed and scored")
    print("[PASS] Strong surviving narrative produces bull lead")
    print("[PASS] Failed fragile narrative produces bear lead")
    print("[PASS] Debate margin and conflict quantified")
    print("[PASS] Aggregate position adjudicated deterministically")
    print("[PASS] Complete OIT-018 lineage retained")
    print("[PASS] Debate report deterministic across replay")
    print("[PASS] Tampered debate report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-019 BULL BEAR NEUTRAL DEBATE SYNTHESIS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
