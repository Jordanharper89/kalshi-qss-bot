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
    OracleRedundancyNoveltyInvariantError,
    analyze_redundancy_and_novelty,
    serialize_redundancy_novelty_package,
    verify_redundancy_novelty_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleRedundancyNoveltyInvariantError:
        return
    raise AssertionError("expected OII-005 invariant rejection")


def build_oii004_package(reverse: bool = False):
    now = datetime(2026, 7, 27, 22, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=8)

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
        source_locator="news://publisher/a",
        source_identity_hash=stable_hash("source.publisher.a"),
        observed_at=now,
    )
    publisher_b = build_source_node(
        source_id="source.publisher.b",
        source_class="news",
        source_locator="news://publisher/b",
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
        observation_id="observation.primary",
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
        observation_id="observation.publisher.a",
        content_hash=stable_hash("publisher-a-content"),
        replay_hash=stable_hash("publisher-a-replay"),
        chain_hash=stable_hash("publisher-a-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.shared",),
    )
    e_b = build_evidence_node(
        evidence_id="evidence.publisher.b",
        source_id=publisher_b.source_id,
        observation_id="observation.publisher.b",
        content_hash=stable_hash("publisher-b-content"),
        replay_hash=stable_hash("publisher-b-replay"),
        chain_hash=stable_hash("publisher-b-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.shared",),
    )
    e_independent = build_evidence_node(
        evidence_id="evidence.independent",
        source_id=independent.source_id,
        observation_id="observation.independent",
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
            confidence_basis="direct source",
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
            confidence_basis="quotes same primary source",
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
            confidence_basis="same primary source",
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
    return analyze_source_dependency_and_independence(graph=graph)


def main() -> None:
    package_a = build_oii004_package(False)
    package_b = build_oii004_package(True)

    first = analyze_redundancy_and_novelty(
        source_independence_package=package_a
    )
    second = analyze_redundancy_and_novelty(
        source_independence_package=package_b
    )

    assert first == second
    assert first.package_hash == second.package_hash
    assert verify_redundancy_novelty_package(first)

    redundancy = {
        item.evidence_id: item
        for item in first.evidence_redundancy_assessments
    }
    novelty = {
        item.evidence_id: item
        for item in first.evidence_novelty_assessments
    }

    assert (
        redundancy["evidence.publisher.a"].redundancy_classification
        in {"moderate_redundancy", "high_redundancy"}
    )
    assert (
        redundancy["evidence.publisher.b"].redundancy_classification
        in {"moderate_redundancy", "high_redundancy"}
    )
    assert (
        float(novelty["evidence.independent"].novelty_score)
        > float(novelty["evidence.publisher.a"].novelty_score)
    )
    assert first.cluster_count >= 1
    assert first.redundancy_clusters

    payload = json.loads(
        serialize_redundancy_novelty_package(first)
    )
    assert payload["engine_id"] == "OII-005"
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
        lambda: verify_redundancy_novelty_package(
            replace(first, package_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_redundancy_novelty_package(
            replace(first, probability_estimation_allowed=True)
        )
    )
    rejected(
        lambda: analyze_redundancy_and_novelty(
            source_independence_package=replace(
                package_a,
                package_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-005 TEST")
    print(" REDUNDANCY / NOVELTY ENGINE")
    print("========================================")
    print("[PASS] Actual OII-004 independence package consumed")
    print("[PASS] OII-004 identity and hashes verified")
    print("[PASS] Reused primary origins detected")
    print("[PASS] Dependency-based redundancy measured")
    print("[PASS] Redundant evidence clusters materialized")
    print("[PASS] Independent evidence receives stronger novelty")
    print("[PASS] Redundancy cannot masquerade as new information")
    print("[PASS] Novelty and redundancy scores deterministic")
    print("[PASS] Input ordering cannot alter package identity")
    print("[PASS] Probability and final conclusions remain disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-005 REDUNDANCY / NOVELTY CERTIFIED")


if __name__ == "__main__":
    main()
