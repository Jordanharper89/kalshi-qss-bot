from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (
    ENGINE_ID as OIT_015_ENGINE_ID,
    POLICY_ID as OIT_015_POLICY_ID,
    SCHEMA_VERSION as OIT_015_SCHEMA_VERSION,
    OracleCausalHypothesis,
    OracleCausalIntelligenceReport,
    _stable_hash as oit_015_hash,
    verify_causal_intelligence_report,
)
from qseries_v2.oracle_terminal.oracle_cross_market_uncertainty_contradiction_synthesis import (
    OracleUncertaintyContradictionInvariantError,
    build_uncertainty_contradiction_report,
    verify_uncertainty_contradiction_report,
)


def make_hypothesis(
    index: int,
    cause: str,
    effect: str,
    evidence_class: str,
    confidence: float,
    *,
    contradicts: bool,
):
    limitations = (
        "observational evidence cannot establish causation by itself",
        "unobserved confounders may explain the relationship",
        "mechanism has not yet been independently verified",
    )
    body = {
        "hypothesis_index": index,
        "cause_record_id": cause,
        "effect_record_id": effect,
        "shared_entities": ("Bitcoin",),
        "temporal_order": "left_precedes_right",
        "causal_direction": f"{cause}->{effect}",
        "causal_type": (
            "candidate_inhibitory_influence"
            if contradicts
            else "candidate_influence"
        ),
        "evidence_class": evidence_class,
        "probability_distance": 0.10,
        "relationship_score": 0.80,
        "causal_confidence": confidence,
        "supports_causation": True,
        "contradicts_causation": contradicts,
        "limitations": limitations,
        "rationale": ("certified causal hypothesis",),
        "source_relationship_hash": f"relationship-{index}",
        "read_only": True,
    }
    return OracleCausalHypothesis(
        **body,
        hypothesis_hash=oit_015_hash(body),
    )


def make_report(root: Path):
    hypotheses = (
        make_hypothesis(
            1,
            "BTC-ETF",
            "BTC-PRICE",
            "supportive",
            0.76,
            contradicts=False,
        ),
        make_hypothesis(
            2,
            "BTC-PRICE",
            "BTC-MINER",
            "suppressive",
            0.58,
            contradicts=True,
        ),
    )
    body = {
        "schema_version": OIT_015_SCHEMA_VERSION,
        "engine_id": OIT_015_ENGINE_ID,
        "policy_id": OIT_015_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "Where are the uncertainty and contradictions?",
        "cross_market_report_hash": "cross-market-report-hash",
        "hypotheses": hypotheses,
        "hypothesis_count": 2,
        "supportive_hypothesis_count": 1,
        "suppressive_hypothesis_count": 1,
        "associative_hypothesis_count": 0,
        "insufficient_hypothesis_count": 0,
        "causal_state": "bounded_causal_hypotheses_present",
        "causal_summary": "Two bounded hypotheses.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleCausalIntelligenceReport(
        **body,
        report_hash=oit_015_hash(body),
    )
    verify_causal_intelligence_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-016 TEST")
    print(" UNCERTAINTY AND CONTRADICTION SYNTHESIS")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        report = build_uncertainty_contradiction_report(
            root,
            source.query,
            causal_report=source,
        )

        assert report.causal_report_hash == source.report_hash
        assert report.finding_count == 2
        assert report.material_contradiction_count == 1
        assert report.unresolved_evidence_count >= 1

        supportive, suppressive = report.findings
        assert supportive.contradiction_state == "none_detected"
        assert suppressive.contradiction_state == (
            "material_directional_contradiction"
        )
        assert suppressive.contradiction_severity >= 0.60
        assert suppressive.requires_additional_evidence
        assert supportive.source_hypothesis_hash == (
            source.hypotheses[0].hypothesis_hash
        )
        assert suppressive.source_hypothesis_hash == (
            source.hypotheses[1].hypothesis_hash
        )

        assert all(
            0.0 <= item.uncertainty_score <= 1.0
            for item in report.findings
        )
        assert all(item.unresolved_questions for item in report.findings)

        replay = build_uncertainty_contradiction_report(
            root,
            source.query,
            causal_report=source,
        )
        assert replay == report
        assert verify_uncertainty_contradiction_report(report)

        tampered = replace(
            report,
            synthesis_summary=report.synthesis_summary + " tampered",
        )
        try:
            verify_uncertainty_contradiction_report(tampered)
        except OracleUncertaintyContradictionInvariantError:
            pass
        else:
            raise AssertionError("tampered uncertainty report accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-015 causal report consumed")
    print("[PASS] Confidence gaps quantified deterministically")
    print("[PASS] Evidence completeness calculated")
    print("[PASS] Material directional contradiction detected")
    print("[PASS] Incomplete evidence separated from contradiction")
    print("[PASS] Unresolved intelligence questions generated")
    print("[PASS] Complete causal hypothesis lineage retained")
    print("[PASS] Synthesis deterministic across replay")
    print("[PASS] Tampered synthesis report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-016 UNCERTAINTY CONTRADICTION SYNTHESIS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
