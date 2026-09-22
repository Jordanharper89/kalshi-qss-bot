from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_terminal.oracle_cross_market_intelligence_relationship_analysis import (
    ENGINE_ID as OIT_014_ENGINE_ID,
    POLICY_ID as OIT_014_POLICY_ID,
    SCHEMA_VERSION as OIT_014_SCHEMA_VERSION,
    OracleCrossMarketIntelligenceReport,
    OracleCrossMarketRecordProfile,
    OracleCrossMarketRelationship,
    _stable_hash as oit_014_hash,
    verify_cross_market_intelligence_report,
)
from qseries_v2.oracle_terminal.oracle_cross_market_causal_intelligence_analysis import (
    MAX_CAUSAL_CONFIDENCE,
    OracleCausalIntelligenceInvariantError,
    build_causal_intelligence_report,
    verify_causal_intelligence_report,
)


def make_profile(index: int, record_id: str, entity: str):
    body = {
        "profile_index": index,
        "evidence_index": index,
        "record_id": record_id,
        "title": record_id,
        "entities": (entity,),
        "venue": "Kalshi",
        "category": "Crypto",
        "probability": 0.60,
        "direction": "positive",
        "timestamp_utc": f"2026-07-30T0{index}:00:00Z",
        "epoch_seconds": 1000 + index,
        "artifact_relative_path": "runtime/certified.json",
        "artifact_sha256": "a" * 64,
        "record_hash": f"record-{index}",
        "evidence_hash": f"evidence-{index}",
        "inspection_hash": f"inspection-{index}",
        "temporal_event_hash": f"temporal-{index}",
        "source_record_locator": f"$.records[{index - 1}]",
        "read_only": True,
    }
    return OracleCrossMarketRecordProfile(
        **body,
        profile_hash=oit_014_hash(body),
    )


def make_relationship(
    index: int,
    left: str,
    right: str,
    temporal: str,
    directional: str,
    score: float,
):
    body = {
        "relationship_index": index,
        "left_profile_index": index,
        "right_profile_index": index + 1,
        "left_record_id": left,
        "right_record_id": right,
        "shared_entities": ("Bitcoin",),
        "shared_entity_count": 1,
        "elapsed_seconds": 3600,
        "temporal_relationship": temporal,
        "directional_relationship": directional,
        "probability_distance": 0.10,
        "evidence_dependence": "independent_evidence",
        "relationship_score": score,
        "relationship_strength": "strong" if score >= 0.70 else "moderate",
        "rationale": ("certified relationship",),
        "read_only": True,
    }
    return OracleCrossMarketRelationship(
        **body,
        relationship_hash=oit_014_hash(body),
    )


def make_report(root: Path):
    profiles = (
        make_profile(1, "BTC-ETF", "Bitcoin"),
        make_profile(2, "BTC-PRICE", "Bitcoin"),
        make_profile(3, "BTC-MINER", "Bitcoin"),
    )
    relationships = (
        make_relationship(
            1,
            "BTC-ETF",
            "BTC-PRICE",
            "left_leads_right",
            "aligned",
            0.80,
        ),
        make_relationship(
            2,
            "BTC-PRICE",
            "BTC-MINER",
            "left_leads_right",
            "contradictory",
            0.72,
        ),
    )
    body = {
        "schema_version": OIT_014_SCHEMA_VERSION,
        "engine_id": OIT_014_ENGINE_ID,
        "policy_id": OIT_014_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": "What is causing the cross-market Bitcoin movement?",
        "answer_hash": "answer-hash",
        "query_plan_hash": "plan-hash",
        "query_result_hash": "result-hash",
        "temporal_report_hash": "temporal-report-hash",
        "profiles": profiles,
        "relationships": relationships,
        "profile_count": 3,
        "relationship_count": 2,
        "connected_profile_count": 3,
        "independent_profile_count": 0,
        "strong_relationship_count": 2,
        "moderate_relationship_count": 0,
        "weak_relationship_count": 0,
        "lead_lag_relationship_count": 2,
        "contradictory_direction_count": 1,
        "relationship_state": "connected_cross_market_evidence",
        "relationship_summary": "Two certified relationships.",
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleCrossMarketIntelligenceReport(
        **body,
        report_hash=oit_014_hash(body),
    )
    verify_cross_market_intelligence_report(report)
    return report


def main() -> int:
    print("=" * 40)
    print(" OIT-015 TEST")
    print(" CROSS-MARKET CAUSAL INTELLIGENCE")
    print("=" * 40)

    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = make_report(root)
        report = build_causal_intelligence_report(
            root,
            source.query,
            cross_market_report=source,
        )

        assert report.cross_market_report_hash == source.report_hash
        assert report.hypothesis_count == 2
        assert report.supportive_hypothesis_count == 1
        assert report.suppressive_hypothesis_count == 1
        assert report.associative_hypothesis_count == 0
        assert report.insufficient_hypothesis_count == 0

        supportive, suppressive = report.hypotheses
        assert supportive.cause_record_id == "BTC-ETF"
        assert supportive.effect_record_id == "BTC-PRICE"
        assert supportive.evidence_class == "supportive"
        assert supportive.supports_causation
        assert not supportive.contradicts_causation

        assert suppressive.cause_record_id == "BTC-PRICE"
        assert suppressive.effect_record_id == "BTC-MINER"
        assert suppressive.evidence_class == "suppressive"
        assert suppressive.supports_causation
        assert suppressive.contradicts_causation

        assert all(
            item.causal_confidence <= MAX_CAUSAL_CONFIDENCE
            for item in report.hypotheses
        )
        assert all(
            "observational evidence cannot establish causation by itself"
            in item.limitations
            for item in report.hypotheses
        )

        replay = build_causal_intelligence_report(
            root,
            source.query,
            cross_market_report=source,
        )
        assert replay == report
        assert verify_causal_intelligence_report(report)

        tampered = replace(
            report,
            causal_summary=report.causal_summary + " tampered",
        )
        try:
            verify_causal_intelligence_report(tampered)
        except OracleCausalIntelligenceInvariantError:
            pass
        else:
            raise AssertionError("tampered causal report was accepted")

        assert report.read_only
        assert not report.analytics_execution_performed
        assert not report.database_access_performed
        assert not report.publication_allowed
        assert not report.qseries_execution_allowed

    print("[PASS] Certified OIT-014 cross-market report consumed")
    print("[PASS] Supportive causal hypothesis classified")
    print("[PASS] Suppressive causal hypothesis classified")
    print("[PASS] Temporal cause and effect ordering preserved")
    print("[PASS] Causal confidence bounded below certainty")
    print("[PASS] Correlation never represented as causal proof")
    print("[PASS] Complete source relationship lineage retained")
    print("[PASS] Causal report deterministic across replay")
    print("[PASS] Tampered causal report rejected")
    print("[PASS] No analytics execution or database access performed")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] OIT-015 CROSS-MARKET CAUSAL INTELLIGENCE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
