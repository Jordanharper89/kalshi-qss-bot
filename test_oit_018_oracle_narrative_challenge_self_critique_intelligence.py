from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (
    ENGINE_ID as OIT_017_ENGINE_ID,
    POLICY_ID as OIT_017_POLICY_ID,
    SCHEMA_VERSION as OIT_017_SCHEMA_VERSION,
    OracleNarrativeEvolutionFinding,
    OracleNarrativeEvolutionReport,
    _stable_hash as oit_017_hash,
    verify_narrative_evolution_report,
)
from qseries_v2.oracle_terminal.oracle_narrative_challenge_self_critique_intelligence import (
    OracleNarrativeChallengeInvariantError,
    build_narrative_challenge_report,
    verify_narrative_challenge_report,
)


def make_narrative(
    index: int,
    cause: str,
    effect: str,
    *,
    state: str,
    strength: float,
    stability: float,
    reversal: float,
    contradiction: float,
    uncertainty: float,
    support: float,
    monitoring: bool,
):
    body = {
        "finding_index": index,
        "cause_record_id": cause,
        "effect_record_id": effect,
        "source_finding_hash": f"uncertainty-{index}",
        "narrative_state": state,
        "narrative_direction": (
            "support_accumulating"
            if state == "strengthening"
            else "opposing_evidence_dominant"
        ),
        "narrative_strength": strength,
        "narrative_stability": stability,
        "reversal_risk": reversal,
        "contradiction_pressure": contradiction,
        "uncertainty_pressure": uncertainty,
        "evidence_support": support,
        "requires_monitoring": monitoring,
        "evolution_signals": ("certified narrative signal",),
        "rationale": ("certified narrative rationale",),
        "read_only": True,
    }
    return OracleNarrativeEvolutionFinding(
        **body,
        finding_hash=oit_017_hash(body),
    )


def make_report(root: Path):
    findings = (
        make_narrative(
            1,
            "BTC-ETF",
            "BTC-PRICE",
            state="strengthening",
            strength=0.82,
            stability=0.80,
            reversal=0.15,
            contradiction=0.05,
            uncertainty=0.20,
            support=0.86,
            monitoring=False,
        ),
        make_narrative(
            2,
            "BTC-PRICE",
            "BTC-MINER",
            state="reversing",
            strength=0.78,
            stability=0.22,
            reversal=0.84,
            contradiction=0.82,
            uncertainty=0.72,
            support=0.30,
            monitoring=True,
        ),
    )
    body = {
        "schema_version": OIT_017_SCHEMA_VERSION,
        "engine_id": OIT_017_ENGINE_ID,
        "policy_id": OIT_017_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Challenge the current Bitcoin narratives.",
        "uncertainty_report_hash": "uncertainty-report-hash",
        "findings": findings,
        "finding_count": len(findings),
        "strengthening_count": sum(
            item.narrative_state == "strengthening" for item in findings
        ),
        "weakening_count": sum(
            item.narrative_state == "weakening" for item in findings
        ),
        "fragmented_count": sum(
            item.narrative_state == "fragmented" for item in findings
        ),
        "reversing_count": sum(
            item.narrative_state == "reversing" for item in findings
        ),
        "stable_count": sum(
            item.narrative_state == "stable" for item in findings
        ),
        "monitoring_required_count": sum(
            item.requires_monitoring for item in findings
        ),
        "narrative_state": "narrative_reversal_detected",
        "narrative_summary": "One strengthening and one reversing narrative.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleNarrativeEvolutionReport(
        **body,
        report_hash=oit_017_hash(body),
    )
    verify_narrative_evolution_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-018 CORRECTION V2 TEST")
    print(" NARRATIVE CHALLENGE AND SELF-CRITIQUE")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)

        assert source.finding_count == 2
        assert source.strengthening_count == 1
        assert source.reversing_count == 1
        assert source.monitoring_required_count == 1

        report = build_narrative_challenge_report(
            root,
            source.query,
            narrative_report=source,
        )

        assert report.narrative_report_hash == source.report_hash
        assert report.finding_count == 2
        assert report.passed_count == 1
        assert report.failed_count == 1
        assert report.fragile_count == 1
        assert report.monitoring_required_count == 1

        passed, failed = report.findings
        assert passed.challenge_state == "passed"
        assert passed.challenge_passed
        assert passed.surviving_confidence >= 0.50

        assert failed.challenge_state == "failed"
        assert not failed.challenge_passed
        assert failed.fragility_score >= 0.70
        assert failed.counter_evidence_pressure > (
            passed.counter_evidence_pressure
        )

        assert passed.source_narrative_hash == (
            source.findings[0].finding_hash
        )
        assert failed.source_narrative_hash == (
            source.findings[1].finding_hash
        )

        assert all(item.fragile_assumptions for item in report.findings)
        assert all(item.counter_arguments for item in report.findings)
        assert all(item.falsification_tests for item in report.findings)

        replay = build_narrative_challenge_report(
            root,
            source.query,
            narrative_report=source,
        )
        assert replay == report
        assert verify_narrative_challenge_report(report)

        tampered = replace(
            report,
            challenge_summary=report.challenge_summary + " tampered",
        )
        try:
            verify_narrative_challenge_report(tampered)
        except OracleNarrativeChallengeInvariantError:
            pass
        else:
            raise AssertionError("tampered challenge report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Corrected certified OIT-017 narrative report consumed")
    print("[PASS] OIT-017 fixture counts derived from narrative findings")
    print("[PASS] Strong narrative survived bounded challenge")
    print("[PASS] Fragile narrative failed bounded challenge")
    print("[PASS] Counter-evidence pressure quantified")
    print("[PASS] Fragile assumptions surfaced")
    print("[PASS] Counter-arguments generated")
    print("[PASS] Falsification tests generated")
    print("[PASS] Complete corrected OIT-017 lineage retained")
    print("[PASS] Challenge report deterministic across replay")
    print("[PASS] Tampered challenge report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-018 CORRECTION V2 SELF-CRITIQUE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
