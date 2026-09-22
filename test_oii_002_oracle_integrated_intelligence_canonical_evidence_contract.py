from __future__ import annotations

from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_canonical_evidence_contract import (
    CONTRACT_STATUS,
    CONTRACT_TYPE,
    OracleCanonicalEvidenceInvariantError,
    OracleCanonicalIntelligenceEvidenceBuilder,
    stable_hash,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_integrated_intelligence_scientific_model_registry import REQUIRED_MODEL_IDS


def without_hash(value, field):
    return {k: v for k, v in value.__dict__.items() if k != field}


def main() -> int:
    print("=" * 56)
    print(" OII-002 TEST")
    print(" CANONICAL INTELLIGENCE EVIDENCE CONTRACT")
    print("=" * 56)

    builder = OracleCanonicalIntelligenceEvidenceBuilder()
    now = datetime(2026, 7, 27, 13, 0, tzinfo=timezone.utc)

    origin = builder.origin(
        source_id="source.kalshi.market_data",
        source_class="primary",
        source_name="Kalshi public market data",
        source_locator="/markets",
        source_observation_id="kalshi.market.example.001",
        source_content_hash="content-001",
        source_replay_hash="replay-001",
        source_chain_hash="chain-001",
        source_adapter_id="adapter.oracle.kalshi.public_markets.shadow",
        source_environment="production",
        acquired_at=now,
        observed_at=now - timedelta(seconds=5),
        authentication_used=False,
        public_source=True,
        shadow_mode=True,
    )
    assert origin.read_only
    assert origin.origin_hash == stable_hash(without_hash(origin, "origin_hash"))

    quality = builder.quality(
        source_reliability=0.99,
        source_independence=0.95,
        relevance=1.0,
        specificity=0.98,
        freshness=1.0,
        completeness=0.92,
        manipulation_risk=0.05,
        contradiction_risk=0.10,
        uncertainty=0.08,
    )
    assert quality.quality_hash == stable_hash(without_hash(quality, "quality_hash"))

    claim = builder.claim(
        claim_text="The canonical snapshot reports a YES ask of 0.61.",
        claim_direction="supports",
        claim_target_id="market.example.001",
        claim_probability=0.99,
        claim_uncertainty=0.01,
        causal_claim=False,
    )
    assert claim.claim_hash == stable_hash(without_hash(claim, "claim_hash"))

    evidence = builder.evidence(
        evidence_type="market_observation",
        subject_id="market.example.001",
        subject_type="prediction_contract",
        title="Canonical market snapshot",
        summary="Read-only evidence for integrated intelligence models.",
        payload={
            "venue_id": "venue.kalshi",
            "yes_bid_dollars": "0.60",
            "yes_ask_dollars": "0.61",
            "liquidity_dollars": "5000.00",
        },
        origin=origin,
        quality=quality,
        claims=(claim,),
        model_eligibility=REQUIRED_MODEL_IDS,
        parent_evidence_ids=(),
        contradictory_evidence_ids=("counterevidence.001",),
        created_at=now,
        valid_from=now,
        valid_until=now + timedelta(minutes=5),
    )
    repeated = builder.evidence(
        evidence_type="market_observation",
        subject_id="market.example.001",
        subject_type="prediction_contract",
        title="Canonical market snapshot",
        summary="Read-only evidence for integrated intelligence models.",
        payload={
            "liquidity_dollars": "5000.00",
            "yes_ask_dollars": "0.61",
            "yes_bid_dollars": "0.60",
            "venue_id": "venue.kalshi",
        },
        origin=origin,
        quality=quality,
        claims=(claim,),
        model_eligibility=tuple(reversed(REQUIRED_MODEL_IDS)),
        parent_evidence_ids=(),
        contradictory_evidence_ids=("counterevidence.001",),
        created_at=now,
        valid_from=now,
        valid_until=now + timedelta(minutes=5),
    )
    assert evidence == repeated
    assert evidence.evidence_hash == stable_hash(without_hash(evidence, "evidence_hash"))
    assert evidence.immutable and evidence.replayable and evidence.explainable
    assert evidence.source_lineage_verified and evidence.uncertainty_explicit
    assert evidence.adversarial_review_required and evidence.calibration_tracking_required
    assert evidence.read_only
    assert not any(
        (
            evidence.publication_allowed,
            evidence.alerting_allowed,
            evidence.qseries_handoff_allowed,
            evidence.qseries_execution_allowed,
            evidence.order_creation_allowed,
            evidence.funds_movement_allowed,
            evidence.portfolio_mutation_allowed,
        )
    )

    contract = builder.contract()
    assert contract.contract_status == CONTRACT_STATUS
    assert contract.contract_type == CONTRACT_TYPE
    assert contract.required_model_ids == REQUIRED_MODEL_IDS
    assert contract.contract_hash == stable_hash(without_hash(contract, "contract_hash"))
    assert contract.source_origin_required
    assert contract.quality_required
    assert contract.claims_required
    assert contract.uncertainty_required
    assert contract.lineage_required
    assert contract.replay_hash_required
    assert contract.chain_hash_required
    assert contract.contradiction_linkage_supported
    assert contract.causal_controls_required
    assert contract.adversarial_review_required
    assert contract.calibration_tracking_required
    assert contract.deterministic_hashing_required
    assert contract.immutable_evidence_required
    assert contract.read_only_boundary_required
    assert not any(
        (
            contract.publication_allowed,
            contract.alerting_allowed,
            contract.qseries_handoff_allowed,
            contract.qseries_execution_allowed,
            contract.order_creation_allowed,
            contract.funds_movement_allowed,
            contract.portfolio_mutation_allowed,
        )
    )

    try:
        builder.claim(
            claim_text="Invalid causal claim",
            claim_direction="supports",
            claim_target_id="market.example.001",
            claim_probability=0.75,
            claim_uncertainty=0.25,
            causal_claim=True,
        )
    except OracleCanonicalEvidenceInvariantError:
        pass
    else:
        raise AssertionError("causal claim controls not enforced")

    print("[PASS] Actual OII-001 scientific model registry consumed")
    print("[PASS] Canonical source-origin lineage verified")
    print("[PASS] Evidence quality and uncertainty contract verified")
    print("[PASS] Canonical claims and contradiction linkage verified")
    print("[PASS] Causal claims require mechanism and counterfactual")
    print("[PASS] All nine scientific models supported")
    print("[PASS] Deterministic evidence identity and hashing verified")
    print("[PASS] Immutable, replayable, explainable read-only evidence verified")
    print("[PASS] Publication, alerting, handoff, and execution remain disabled")
    print("[PASS] Orders, funds movement, and portfolio mutation remain disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
