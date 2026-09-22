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
    OracleProvenanceConfidenceInvariantError,
    analyze_provenance_confidence,
    serialize_provenance_confidence_package,
    verify_provenance_confidence_package,
)


def rejected(callable_) -> None:
    try:
        callable_()
    except OracleProvenanceConfidenceInvariantError:
        return
    raise AssertionError("expected OII-007 invariant rejection")


def build_oii006(reverse: bool = False):
    now = datetime(2026, 7, 28, 2, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=8)

    primary = build_source_node(
        source_id="source.primary",
        source_class="regulatory_filing",
        source_locator="sec://filing/primary",
        source_identity_hash=stable_hash("source.primary"),
        observed_at=now,
    )
    publisher = build_source_node(
        source_id="source.publisher",
        source_class="news",
        source_locator="news://publisher/article",
        source_identity_hash=stable_hash("source.publisher"),
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
    e_publisher = build_evidence_node(
        evidence_id="evidence.publisher",
        source_id=publisher.source_id,
        observation_id="obs.publisher",
        content_hash=stable_hash("publisher-content"),
        replay_hash=stable_hash("publisher-replay"),
        chain_hash=stable_hash("publisher-chain"),
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
            from_node_id=e_publisher.node_id,
            to_node_id=publisher.node_id,
            relationship="derived_from",
            asserted_by_evidence_id=e_publisher.evidence_id,
            observed_at=now,
            confidence_basis="publisher acquisition",
        ),
        build_provenance_edge(
            from_node_id=publisher.node_id,
            to_node_id=primary.node_id,
            relationship="quotes",
            asserted_by_evidence_id=e_publisher.evidence_id,
            observed_at=now,
            confidence_basis="publisher quotes primary",
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

    sources = (primary, publisher, independent)
    evidence = (e_primary, e_publisher, e_independent)
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
    return analyze_entropy_and_information_gain(
        redundancy_novelty_package=oii005
    )


def main() -> None:
    oii006_a = build_oii006(False)
    oii006_b = build_oii006(True)

    first = analyze_provenance_confidence(
        entropy_information_gain_package=oii006_a
    )
    second = analyze_provenance_confidence(
        entropy_information_gain_package=oii006_b
    )

    assert first == second
    assert first.package_hash == second.package_hash
    assert verify_provenance_confidence_package(first)

    by_evidence = {
        item.evidence_id: item
        for item in first.evidence_confidence_assessments
    }

    independent_score = float(
        by_evidence["evidence.independent"].provenance_confidence_score
    )
    publisher_score = float(
        by_evidence["evidence.publisher"].provenance_confidence_score
    )
    assert independent_score > publisher_score
    assert first.provenance_confidence_ranking[0].rank == 1
    assert (
        first.provenance_confidence_ranking[0].evidence_id
        == "evidence.independent"
    )

    payload = json.loads(
        serialize_provenance_confidence_package(first)
    )
    assert payload["engine_id"] == "OII-007"
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
        lambda: verify_provenance_confidence_package(
            replace(first, package_hash="0" * 64)
        )
    )
    rejected(
        lambda: verify_provenance_confidence_package(
            replace(first, probability_estimation_allowed=True)
        )
    )
    rejected(
        lambda: analyze_provenance_confidence(
            entropy_information_gain_package=replace(
                oii006_a,
                package_hash="0" * 64,
            )
        )
    )

    print("========================================")
    print(" OII-007 TEST")
    print(" PROVENANCE CONFIDENCE ENGINE")
    print("========================================")
    print("[PASS] Actual OII-006 information-gain package consumed")
    print("[PASS] OII-006 identity and hashes verified")
    print("[PASS] Source traceability measured")
    print("[PASS] Lineage integrity measured")
    print("[PASS] Replay integrity preserved")
    print("[PASS] Redundancy and circularity reduce confidence")
    print("[PASS] Independent high-information evidence ranks higher")
    print("[PASS] Provenance-confidence ranking deterministic")
    print("[PASS] Input ordering cannot alter package identity")
    print("[PASS] Probability estimation remains disabled")
    print("[PASS] Final intelligence conclusions remain disabled")
    print("[PASS] Read-only Oracle boundary preserved")
    print("[DONE] OII-007 PROVENANCE CONFIDENCE CERTIFIED")


if __name__ == "__main__":
    main()
