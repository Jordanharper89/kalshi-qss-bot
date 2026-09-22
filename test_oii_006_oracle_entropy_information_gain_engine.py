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
    OracleEntropyInformationGainInvariantError,
    analyze_entropy_and_information_gain,
    serialize_entropy_information_gain_package,
    verify_entropy_information_gain_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleEntropyInformationGainInvariantError:
        return
    raise AssertionError("expected OII-006 invariant rejection")


def build_oii005(reverse: bool = False):
    now = datetime(2026, 7, 28, 0, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=6)

    primary = build_source_node(
        source_id="source.primary",
        source_class="regulatory_filing",
        source_locator="sec://filing/primary",
        source_identity_hash=stable_hash("source.primary"),
        observed_at=now,
    )
    publisher_a = build_source_node(
        source_id="source.publisher.a",
        source_class="news",
        source_locator="news://a/article",
        source_identity_hash=stable_hash("source.publisher.a"),
        observed_at=now,
    )
    publisher_b = build_source_node(
        source_id="source.publisher.b",
        source_class="news",
        source_locator="news://b/article",
        source_identity_hash=stable_hash("source.publisher.b"),
        observed_at=now,
    )
    independent = build_source_node(
        source_id="source.independent",
        source_class="social",
        source_locator="social://independent/thread",
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
        claim_ids=("claim.shared",),
    )
    e_a = build_evidence_node(
        evidence_id="evidence.publisher.a",
        source_id=publisher_a.source_id,
        observation_id="obs.publisher.a",
        content_hash=stable_hash("a-content"),
        replay_hash=stable_hash("a-replay"),
        chain_hash=stable_hash("a-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.shared",),
    )
    e_b = build_evidence_node(
        evidence_id="evidence.publisher.b",
        source_id=publisher_b.source_id,
        observation_id="obs.publisher.b",
        content_hash=stable_hash("b-content"),
        replay_hash=stable_hash("b-replay"),
        chain_hash=stable_hash("b-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.shared",),
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
        claim_ids=("claim.unique",),
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
            from_node_id=e_a.node_id,
            to_node_id=publisher_a.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_a.evidence_id,
            observed_at=now,
            confidence_basis="publisher acquisition",
        ),
        build_provenance_edge(
            from_node_id=publisher_a.node_id,
            to_node_id=primary.node_id,
            relationship="quotes",
            asserted_by_evidence_id=e_a.evidence_id,
            observed_at=now,
            confidence_basis="primary citation",
        ),
        build_provenance_edge(
            from_node_id=e_b.node_id,
            to_node_id=publisher_b.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_b.evidence_id,
            observed_at=now,
            confidence_basis="publisher acquisition",
        ),
        build_provenance_edge(
            from_node_id=publisher_b.node_id,
            to_node_id=primary.node_id,
            relationship="same_primary_origin",
            asserted_by_evidence_id=e_b.evidence_id,
            observed_at=now,
            confidence_basis="same primary origin",
        ),
        build_provenance_edge(
            from_node_id=e_independent.node_id,
            to_node_id=independent.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_independent.evidence_id,
            observed_at=now,
            confidence_basis="independent source",
        ),
    )

    sources = (primary, publisher_a, publisher_b, independent)
    evidence = (e_primary, e_a, e_b, e_independent)
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
    return analyze_redundancy_and_novelty(
        source_independence_package=oii004
    )


def main() -> None:
    oii005_a = build_oii005(False)
    oii005_b = build_oii005(True)

    first = analyze_entropy_and_information_gain(
        redundancy_novelty_package=oii005_a
    )
    second = analyze_entropy_and_information_gain(
        redundancy_novelty_package=oii005_b
    )

    assert first == second
    assert first.package_hash == second.package_hash
    assert verify_entropy_information_gain_package(first)

    gains = {
        item.evidence_id: item
        for item in first.information_gain_assessments
    }
    entropy = {
        item.evidence_id: item
        for item in first.entropy_assessments
    }

    independent_gain = float(
        gains["evidence.independent"].effective_information_gain_score
    )
    publisher_gain = float(
        gains["evidence.publisher.a"].effective_information_gain_score
    )
    assert independent_gain > publisher_gain

    assert (
        float(entropy["evidence.independent"].posterior_uncertainty_score)
        < float(entropy["evidence.independent"].prior_uncertainty_score)
    )
    assert first.information_gain_ranking[0].rank == 1
    assert (
        first.information_gain_ranking[0].evidence_id
        == "evidence.independent"
    )

    payload = json.loads(
        serialize_entropy_information_gain_package(first)
    )
    assert payload["engine_id"] == "OII-006"
    assert payload["probability_estimation_allowed"] is False
    assert payload["final_intelligence_conclusion_allowed"] is False
    assert first.read_only
    assert not any(
        (
            first.publication_allowed,
            first.alerting_allowed,
            first.final_intelligence_conclusion_allowed,
            first.probability_estimation_allowed,
            first.qseries_handoff_allowed,
            first.qseries_execution_allowed,
            first.order_creation_allowed,
            first.funds_movement_allowed,
            first.portfolio_mutation_allowed,
        )
    )

    rejected(
        lambda: verify_entropy_information_gain_package(
            replace(first, package_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_entropy_information_gain_package(
            replace(first, probability_estimation_allowed=True)
        )
    )
    rejected(
        lambda: analyze_entropy_and_information_gain(
            redundancy_novelty_package=replace(
                oii005_a,
                package_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-006 TEST")
    print(" ENTROPY / INFORMATION GAIN ENGINE")
    print("========================================")
    print("[PASS] Actual OII-005 redundancy/novelty package consumed")
    print("[PASS] OII-005 identity and hashes verified")
    print("[PASS] Prior and posterior uncertainty measured")
    print("[PASS] Entropy reduction measured deterministically")
    print("[PASS] Redundancy discounts information gain")
    print("[PASS] Novel independent evidence ranks higher")
    print("[PASS] Information-gain ranking deterministic")
    print("[PASS] Input ordering cannot alter package identity")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-006 ENTROPY / INFORMATION GAIN CERTIFIED")


if __name__ == "__main__":
    main()
