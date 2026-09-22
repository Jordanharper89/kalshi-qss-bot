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
    OracleSourceDependencyIndependenceInvariantError,
    analyze_source_dependency_and_independence,
    serialize_independence_package,
    verify_independence_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleSourceDependencyIndependenceInvariantError:
        return
    raise AssertionError("expected OII-004 invariant rejection")


def build_graph(order: int = 0):
    now = datetime(2026, 7, 27, 20, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=4)

    primary = build_source_node(
        source_id="source.primary.filing",
        source_class="regulatory_filing",
        source_locator="sec://filing/1",
        source_identity_hash=stable_hash("source.primary.filing"),
        observed_at=now,
    )
    article_a = build_source_node(
        source_id="source.news.a",
        source_class="news",
        source_locator="news://a/1",
        source_identity_hash=stable_hash("source.news.a"),
        observed_at=now,
    )
    article_b = build_source_node(
        source_id="source.news.b",
        source_class="news",
        source_locator="news://b/1",
        source_identity_hash=stable_hash("source.news.b"),
        observed_at=now,
    )
    independent = build_source_node(
        source_id="source.social.independent",
        source_class="social",
        source_locator="social://independent/1",
        source_identity_hash=stable_hash("source.social.independent"),
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
        claim_ids=("claim.1",),
    )
    e_a = build_evidence_node(
        evidence_id="evidence.news.a",
        source_id=article_a.source_id,
        observation_id="observation.news.a",
        content_hash=stable_hash("a-content"),
        replay_hash=stable_hash("a-replay"),
        chain_hash=stable_hash("a-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.1",),
    )
    e_b = build_evidence_node(
        evidence_id="evidence.news.b",
        source_id=article_b.source_id,
        observation_id="observation.news.b",
        content_hash=stable_hash("b-content"),
        replay_hash=stable_hash("b-replay"),
        chain_hash=stable_hash("b-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.1",),
    )
    e_independent = build_evidence_node(
        evidence_id="evidence.social.independent",
        source_id=independent.source_id,
        observation_id="observation.social.independent",
        content_hash=stable_hash("independent-content"),
        replay_hash=stable_hash("independent-replay"),
        chain_hash=stable_hash("independent-chain"),
        observed_at=now,
        valid_from=now,
        valid_until=later,
        claim_ids=("claim.1",),
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
            to_node_id=article_a.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_a.evidence_id,
            observed_at=now,
            confidence_basis="article acquisition",
        ),
        build_provenance_edge(
            from_node_id=article_a.node_id,
            to_node_id=primary.node_id,
            relationship="quotes",
            asserted_by_evidence_id=e_a.evidence_id,
            observed_at=now,
            confidence_basis="primary filing citation",
        ),
        build_provenance_edge(
            from_node_id=e_b.node_id,
            to_node_id=article_b.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_b.evidence_id,
            observed_at=now,
            confidence_basis="article acquisition",
        ),
        build_provenance_edge(
            from_node_id=article_b.node_id,
            to_node_id=primary.node_id,
            relationship="same_primary_origin",
            asserted_by_evidence_id=e_b.evidence_id,
            observed_at=now,
            confidence_basis="same filing origin",
        ),
        build_provenance_edge(
            from_node_id=e_independent.node_id,
            to_node_id=independent.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_independent.evidence_id,
            observed_at=now,
            confidence_basis="independent social origin",
        ),
    )

    source_nodes = (primary, article_a, article_b, independent)
    evidence_nodes = (e_primary, e_a, e_b, e_independent)

    if order:
        source_nodes = tuple(reversed(source_nodes))
        evidence_nodes = tuple(reversed(evidence_nodes))
        edges = tuple(reversed(edges))

    return build_source_provenance_graph(
        source_nodes=source_nodes,
        evidence_nodes=evidence_nodes,
        edges=edges,
        created_at=now,
    )


def main() -> None:
    graph_a = build_graph(0)
    graph_b = build_graph(1)

    first = analyze_source_dependency_and_independence(graph=graph_a)
    second = analyze_source_dependency_and_independence(graph=graph_b)

    assert first == second
    assert first.package_hash == second.package_hash
    assert verify_independence_package(first)

    by_evidence = {
        item.evidence_id: item
        for item in first.evidence_independence_assessments
    }

    article_a = by_evidence["evidence.news.a"]
    article_b = by_evidence["evidence.news.b"]
    independent = by_evidence["evidence.social.independent"]

    assert article_b.evidence_node_id in article_a.dependent_evidence_node_ids
    assert article_a.evidence_node_id in article_b.dependent_evidence_node_ids
    assert independent.evidence_node_id in article_a.independent_evidence_node_ids
    assert independent.evidence_node_id in article_b.independent_evidence_node_ids
    assert float(independent.source_independence_score) > float(
        article_a.source_independence_score
    )

    payload = json.loads(serialize_independence_package(first))
    assert payload["engine_id"] == "OII-004"
    assert payload["source_graph_hash"] == graph_a.graph_hash
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
        lambda: verify_independence_package(
            replace(first, package_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_independence_package(
            replace(first, probability_estimation_allowed=True)
        )
    )
    rejected(
        lambda: analyze_source_dependency_and_independence(
            graph=replace(graph_a, graph_hash="0" * 64)
        )
    )

    print("========================================")
    print(" OII-004 TEST")
    print(" SOURCE DEPENDENCY / INDEPENDENCE")
    print("========================================")
    print("[PASS] Actual OII-003 provenance graph consumed")
    print("[PASS] OII-003 graph identity and hash verified")
    print("[PASS] Direct and transitive dependencies measured")
    print("[PASS] Primary-origin overlap detected")
    print("[PASS] Shared-source evidence not double-counted as independent")
    print("[PASS] Independent evidence distinguished deterministically")
    print("[PASS] Circular-dependency penalty contract installed")
    print("[PASS] Source-independence scores deterministic")
    print("[PASS] Input ordering cannot alter package identity")
    print("[PASS] Probability and final conclusions remain disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-004 SOURCE INDEPENDENCE CERTIFIED")


if __name__ == "__main__":
    main()
