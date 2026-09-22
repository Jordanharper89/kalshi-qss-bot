from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_source_identity_provenance_graph_contract import (
    build_evidence_node,
    build_provenance_edge,
    build_source_node,
    build_source_provenance_graph,
    stable_hash,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_source_dependency_independence_engine import (
    analyze_source_dependency_and_independence,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_redundancy_novelty_engine import (
    analyze_redundancy_and_novelty,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_entropy_information_gain_engine import (
    analyze_entropy_and_information_gain,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_provenance_confidence_engine import (
    analyze_provenance_confidence,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_certified_evidence_admission_gate import (
    build_certified_evidence_admission_policy,
    certify_evidence_for_reasoning,
)
from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_scientific_reasoning_input_manifest import (
    OracleScientificReasoningInputManifestInvariantError,
    build_scientific_reasoning_input_manifest,
    build_scientific_reasoning_request,
    serialize_scientific_reasoning_input_manifest,
    verify_scientific_reasoning_input_manifest,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleScientificReasoningInputManifestInvariantError:
        return
    raise AssertionError("expected OII-009 invariant rejection")


def build_oii008(reverse: bool = False):
    now = datetime(2026, 7, 28, 6, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=8)

    primary = build_source_node(
        source_id="source.primary",
        source_class="regulatory_filing",
        source_locator="sec://filing/primary",
        source_identity_hash=stable_hash("source.primary"),
        observed_at=now,
    )
    independent = build_source_node(
        source_id="source.independent",
        source_class="expert_statement",
        source_locator="expert://independent/statement",
        source_identity_hash=stable_hash("source.independent"),
        observed_at=now,
    )

    e_primary = build_evidence_node(
        evidence_id="evidence.primary",
        source_id=primary.source_id,
        observation_id="obs.primary",
        content_hash=stable_hash("primary-content"),
        replay_hash=stable_hash("primary-replay"),
        chain_hash=stable_hash("primary-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.market_resolution",),
    )
    e_independent = build_evidence_node(
        evidence_id="evidence.independent",
        source_id=independent.source_id,
        observation_id="obs.independent",
        content_hash=stable_hash("independent-content"),
        replay_hash=stable_hash("independent-replay"),
        chain_hash=stable_hash("independent-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.market_resolution",),
    )

    edges = (
        build_provenance_edge(
            from_node_id=e_primary.node_id,
            to_node_id=primary.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_primary.evidence_id,
            observed_at=now,
            confidence_basis="direct primary acquisition",
        ),
        build_provenance_edge(
            from_node_id=e_independent.node_id,
            to_node_id=independent.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_independent.evidence_id,
            observed_at=now,
            confidence_basis="independent expert acquisition",
        ),
    )

    sources = (primary, independent)
    evidence = (e_primary, e_independent)
    if reverse:
        sources = tuple(reversed(sources))
        evidence = tuple(reversed(evidence))
        edges = tuple(reversed(edges))

    graph = build_source_provenance_graph(
        source_nodes=sources,
        evidence_nodes=evidence,
        edges=edges,
        created_at=now,
    )
    oii004 = analyze_source_dependency_and_independence(graph=graph)
    oii005 = analyze_redundancy_and_novelty(
        source_independence_package=oii004
    )
    oii006 = analyze_entropy_and_information_gain(
        redundancy_novelty_package=oii005
    )
    oii007 = analyze_provenance_confidence(
        entropy_information_gain_package=oii006
    )
    policy = build_certified_evidence_admission_policy(
        minimum_provenance_confidence_score="0.500000",
        minimum_information_gain_score="0.250000",
    )
    return certify_evidence_for_reasoning(
        provenance_confidence_package=oii007,
        policy=policy,
    )


def main() -> None:
    oii008_a = build_oii008(False)
    oii008_b = build_oii008(True)

    request = build_scientific_reasoning_request(
        subject_id="kalshi:market:test",
        question_text="What scientifically supported evidence bears on resolution?",
        requested_disciplines=(
            "bayesian_inference",
            "causal_inference",
            "calibration_science",
        ),
        requested_claim_ids=("claim.market_resolution",),
        request_context={
            "venue": "Kalshi",
            "mode": "read_only_research",
        },
    )

    first = build_scientific_reasoning_input_manifest(
        certified_evidence_package=oii008_a,
        reasoning_request=request,
    )
    second = build_scientific_reasoning_input_manifest(
        certified_evidence_package=oii008_b,
        reasoning_request=request,
    )

    assert first == second
    assert first.manifest_hash == second.manifest_hash
    assert verify_scientific_reasoning_input_manifest(first)
    assert first.certified_evidence_count == len(
        first.reasoning_evidence_inputs
    )
    assert first.certified_evidence_count >= 1
    assert first.reasoning_input_ready is True
    assert first.reasoning_execution_allowed is False
    assert all(
        item.admissible_disciplines == first.selected_disciplines
        for item in first.reasoning_evidence_inputs
    )

    payload = json.loads(
        serialize_scientific_reasoning_input_manifest(first)
    )
    assert payload["engine_id"] == "OII-009"
    assert payload["reasoning_input_ready"] is True
    assert payload["reasoning_execution_allowed"] is False
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert first.read_only

    rejected(
        lambda: build_scientific_reasoning_request(
            subject_id="market",
            question_text="test",
            requested_disciplines=("unsupported_reasoning",),
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_input_manifest(
            replace(first, manifest_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_scientific_reasoning_input_manifest(
            replace(first, reasoning_execution_allowed=True)
        )
    )
    rejected(
        lambda: build_scientific_reasoning_input_manifest(
            certified_evidence_package=replace(
                oii008_a,
                package_hash="0" * 64,
            ),
            reasoning_request=request,
        )
    )

    print("========================================")
    print(" OII-009 TEST")
    print(" SCIENTIFIC REASONING INPUT MANIFEST")
    print("========================================")
    print("[PASS] Actual OII-008 certified-evidence package consumed")
    print("[PASS] OII-008 identity and hashes verified")
    print("[PASS] Only certified evidence entered reasoning input")
    print("[PASS] Scientific discipline allowlist enforced")
    print("[PASS] Evidence weights derived deterministically")
    print("[PASS] Request, evidence, and certification lineage preserved")
    print("[PASS] Input ordering cannot alter manifest identity")
    print("[PASS] Reasoning input marked ready")
    print("[PASS] Reasoning execution remains disabled")
    print("[PASS] Probability and final conclusions remain disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-009 SCIENTIFIC REASONING INPUT CERTIFIED")


if __name__ == "__main__":
    main()
