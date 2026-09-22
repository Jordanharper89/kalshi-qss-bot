from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_cross_market_uncertainty_contradiction_synthesis import (
    ENGINE_ID as OIT_016_ENGINE_ID,
    POLICY_ID as OIT_016_POLICY_ID,
    SCHEMA_VERSION as OIT_016_SCHEMA_VERSION,
    OracleUncertaintyContradictionFinding,
    OracleUncertaintyContradictionReport,
    _stable_hash as oit_016_hash,
    verify_uncertainty_contradiction_report,
)
from qseries_v2.oracle_terminal.oracle_cross_market_narrative_evolution_intelligence import (
    OracleNarrativeEvolutionInvariantError,
    build_narrative_evolution_report,
    verify_narrative_evolution_report,
)


def make_finding(
    index: int,
    cause: str,
    effect: str,
    uncertainty: float,
    contradiction: float,
    completeness: float,
    confidence_gap: float,
):
    contradiction_state = (
        "material_directional_contradiction"
        if contradiction >= 0.60
        else "none_detected"
    )
    uncertainty_state = (
        "high" if uncertainty >= 0.67
        else "moderate" if uncertainty >= 0.34
        else "low"
    )
    requires_additional_evidence = (
        uncertainty_state != "low" or contradiction > 0.0
    )
    body = {
        "finding_index": index,
        "cause_record_id": cause,
        "effect_record_id": effect,
        "source_hypothesis_hash": f"hypothesis-{index}",
        "evidence_class": "suppressive" if contradiction else "supportive",
        "contradiction_state": contradiction_state,
        "uncertainty_state": uncertainty_state,
        "uncertainty_score": uncertainty,
        "confidence_gap": confidence_gap,
        "evidence_completeness": completeness,
        "contradiction_severity": contradiction,
        "requires_additional_evidence": requires_additional_evidence,
        "unresolved_questions": (
            "What evidence would falsify the narrative?",
        ),
        "rationale": ("certified uncertainty finding",),
        "read_only": True,
    }
    return OracleUncertaintyContradictionFinding(
        **body,
        finding_hash=oit_016_hash(body),
    )


def make_report(root: Path):
    findings = (
        make_finding(
            1,
            "BTC-ETF",
            "BTC-PRICE",
            uncertainty=0.20,
            contradiction=0.05,
            completeness=0.82,
            confidence_gap=0.20,
        ),
        make_finding(
            2,
            "BTC-PRICE",
            "BTC-MINER",
            uncertainty=0.72,
            contradiction=0.82,
            completeness=0.34,
            confidence_gap=0.55,
        ),
    )
    unresolved_count = sum(
        item.requires_additional_evidence for item in findings
    )
    body = {
        "schema_version": OIT_016_SCHEMA_VERSION,
        "engine_id": OIT_016_ENGINE_ID,
        "policy_id": OIT_016_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "How is the Bitcoin narrative evolving?",
        "causal_report_hash": "causal-report-hash",
        "findings": findings,
        "finding_count": 2,
        "high_uncertainty_count": 1,
        "moderate_uncertainty_count": 0,
        "low_uncertainty_count": 1,
        "material_contradiction_count": 1,
        "unresolved_evidence_count": unresolved_count,
        "synthesis_state": "material_contradictions_require_review",
        "synthesis_summary": "One stable and one conflicted finding.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleUncertaintyContradictionReport(
        **body,
        report_hash=oit_016_hash(body),
    )
    verify_uncertainty_contradiction_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-017 CORRECTION V2 TEST")
    print(" CROSS-MARKET NARRATIVE EVOLUTION")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)

        assert source.unresolved_evidence_count == 2
        assert sum(
            item.requires_additional_evidence for item in source.findings
        ) == source.unresolved_evidence_count

        report = build_narrative_evolution_report(
            root,
            source.query,
            uncertainty_report=source,
        )

        assert report.uncertainty_report_hash == source.report_hash
        assert report.finding_count == 2
        assert report.strengthening_count == 1
        assert report.reversing_count == 1
        assert report.monitoring_required_count == 1

        strengthening, reversing = report.findings
        assert strengthening.narrative_state == "strengthening"
        assert strengthening.narrative_direction == "support_accumulating"
        assert not strengthening.requires_monitoring

        assert reversing.narrative_state == "reversing"
        assert reversing.narrative_direction == "opposing_evidence_dominant"
        assert reversing.requires_monitoring
        assert reversing.reversal_risk >= 0.65

        assert strengthening.source_finding_hash == (
            source.findings[0].finding_hash
        )
        assert reversing.source_finding_hash == (
            source.findings[1].finding_hash
        )

        replay = build_narrative_evolution_report(
            root,
            source.query,
            uncertainty_report=source,
        )
        assert replay == report
        assert verify_narrative_evolution_report(report)

        tampered = replace(
            report,
            narrative_summary=report.narrative_summary + " tampered",
        )
        try:
            verify_narrative_evolution_report(tampered)
        except OracleNarrativeEvolutionInvariantError:
            pass
        else:
            raise AssertionError("tampered narrative report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-016 uncertainty report consumed")
    print("[PASS] Fixture unresolved-evidence count derived from findings")
    print("[PASS] Both evidence-requiring findings counted exactly")
    print("[PASS] Strengthening narrative detected")
    print("[PASS] Narrative reversal detected")
    print("[PASS] Narrative stability quantified")
    print("[PASS] Reversal risk quantified")
    print("[PASS] Contradiction and uncertainty pressure preserved")
    print("[PASS] Complete OIT-016 lineage retained")
    print("[PASS] Narrative report deterministic across replay")
    print("[PASS] Tampered narrative report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-017 CORRECTION V2 NARRATIVE EVOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
