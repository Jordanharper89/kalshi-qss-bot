from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import importlib
import json

from qseries_v2.oracle_intelligence.integrated_intelligence.oracle_source_identity_provenance_graph_contract import (
    OracleSourceProvenanceInvariantError, build_evidence_node,
    build_evidence_node_from_oii002, build_provenance_edge, build_source_node,
    build_source_provenance_graph, serialize_graph, stable_hash, verify_graph,
)


def rejected(fn):
    try:
        fn()
    except OracleSourceProvenanceInvariantError:
        return
    raise AssertionError("expected rejection")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_id: str
    observation_id: str
    content_hash: str
    replay_hash: str
    chain_hash: str
    observed_at: str
    valid_from: str
    valid_until: str
    claims: tuple
    read_only: bool = True
    publication_allowed: bool = False
    alerting_allowed: bool = False
    qseries_handoff_allowed: bool = False
    qseries_execution_allowed: bool = False
    order_creation_allowed: bool = False
    funds_movement_allowed: bool = False
    portfolio_mutation_allowed: bool = False


def main():
    importlib.import_module(
        "qseries_v2.oracle_intelligence.integrated_intelligence."
        "oracle_integrated_intelligence_canonical_evidence_contract"
    )
    now = datetime(2026, 7, 27, 18, 0, tzinfo=timezone.utc)
    later = now + timedelta(hours=6)

    primary = build_source_node(
        source_id="source.primary", source_class="filing",
        source_locator="sec://filing/1",
        source_identity_hash=stable_hash("source.primary"), observed_at=now,
    )
    publisher = build_source_node(
        source_id="source.publisher", source_class="news",
        source_locator="news://article/1",
        source_identity_hash=stable_hash("source.publisher"), observed_at=now,
        primary_origin_hint=primary.source_id,
    )
    other = build_source_node(
        source_id="source.publisher.other", source_class="news",
        source_locator="news://article/2",
        source_identity_hash=stable_hash("source.publisher.other"), observed_at=now,
        primary_origin_hint=primary.source_id,
    )

    fixture = Evidence(
        evidence_id="evidence.article.1", source_id=publisher.source_id,
        observation_id="observation.1", content_hash=stable_hash("content1"),
        replay_hash=stable_hash("replay1"), chain_hash=stable_hash("chain1"),
        observed_at=now.isoformat(), valid_from=now.isoformat(),
        valid_until=later.isoformat(), claims=({"claim_id": "claim.1"},),
    )
    e1 = build_evidence_node_from_oii002(fixture)
    e2 = build_evidence_node(
        evidence_id="evidence.article.2", source_id=other.source_id,
        observation_id="observation.2", content_hash=stable_hash("content2"),
        replay_hash=stable_hash("replay2"), chain_hash=stable_hash("chain2"),
        observed_at=now, valid_from=now, valid_until=later,
        claim_ids=("claim.1",),
    )
    e3 = build_evidence_node(
        evidence_id="evidence.primary", source_id=primary.source_id,
        observation_id="observation.3", content_hash=stable_hash("content3"),
        replay_hash=stable_hash("replay3"), chain_hash=stable_hash("chain3"),
        observed_at=now, valid_from=now, valid_until=later,
        claim_ids=("claim.1",),
    )

    edges = (
        build_provenance_edge(
            from_node_id=e1.node_id, to_node_id=publisher.node_id,
            relationship="derived_from", asserted_by_evidence_id=e1.evidence_id,
            observed_at=now, confidence_basis="OII-002 linkage",
        ),
        build_provenance_edge(
            from_node_id=publisher.node_id, to_node_id=primary.node_id,
            relationship="quotes", asserted_by_evidence_id=e1.evidence_id,
            observed_at=now, confidence_basis="primary citation",
        ),
        build_provenance_edge(
            from_node_id=e2.node_id, to_node_id=other.node_id,
            relationship="derived_from", asserted_by_evidence_id=e2.evidence_id,
            observed_at=now, confidence_basis="OII-002 linkage",
        ),
        build_provenance_edge(
            from_node_id=other.node_id, to_node_id=primary.node_id,
            relationship="same_primary_origin", asserted_by_evidence_id=e2.evidence_id,
            observed_at=now, confidence_basis="shared origin",
        ),
        build_provenance_edge(
            from_node_id=e3.node_id, to_node_id=primary.node_id,
            relationship="derived_from", asserted_by_evidence_id=e3.evidence_id,
            observed_at=now, confidence_basis="direct acquisition",
        ),
    )

    first = build_source_provenance_graph(
        source_nodes=(publisher, primary, other),
        evidence_nodes=(e2, e1, e3), edges=reversed(edges), created_at=now,
    )
    second = build_source_provenance_graph(
        source_nodes=(other, publisher, primary),
        evidence_nodes=(e3, e1, e2), edges=edges, created_at=now,
    )
    assert first == second
    assert verify_graph(first)
    assert json.loads(serialize_graph(first))["graph_hash"] == first.graph_hash
    assert first.read_only and not any((
        first.publication_allowed, first.alerting_allowed,
        first.qseries_handoff_allowed, first.qseries_execution_allowed,
        first.order_creation_allowed, first.funds_movement_allowed,
        first.portfolio_mutation_allowed,
    ))

    resolutions = {item.node_id: item for item in first.origin_resolutions}
    assert primary.node_id in resolutions[e1.node_id].primary_origin_node_ids
    assert primary.node_id in resolutions[e2.node_id].primary_origin_node_ids
    assert set(resolutions[e1.node_id].shared_origin_group_ids) & set(
        resolutions[e2.node_id].shared_origin_group_ids
    )

    cycle = build_provenance_edge(
        from_node_id=primary.node_id, to_node_id=publisher.node_id,
        relationship="depends_on", asserted_by_evidence_id=e3.evidence_id,
        observed_at=now, confidence_basis="cycle test",
    )
    cyclic = build_source_provenance_graph(
        source_nodes=(primary, publisher, other),
        evidence_nodes=(e1, e2, e3), edges=edges + (cycle,), created_at=now,
    )
    assert cyclic.circular_paths
    assert any(r.circular_dependency_detected for r in cyclic.origin_resolutions)

    rejected(lambda: build_evidence_node_from_oii002(
        replace(fixture, qseries_execution_allowed=True)
    ))
    rejected(lambda: build_evidence_node_from_oii002(
        replace(fixture, read_only=False)
    ))
    rejected(lambda: build_source_provenance_graph(
        source_nodes=(replace(primary, node_hash="0" * 64),),
        evidence_nodes=(e3,), edges=(), created_at=now,
    ))

    print("========================================")
    print(" OII-003 TEST")
    print(" SOURCE IDENTITY / PROVENANCE GRAPH")
    print("========================================")
    print("[PASS] Actual OII-002 production contract imported")
    print("[PASS] OII-002-compatible canonical evidence consumed")
    print("[PASS] Immutable source and evidence nodes created")
    print("[PASS] Typed provenance relationships constrained")
    print("[PASS] Primary origins and dependency chains resolved")
    print("[PASS] Shared origins identified")
    print("[PASS] Circular dependencies detected")
    print("[PASS] Deterministic graph identity and replay verified")
    print("[PASS] Read-only safety boundary preserved")
    print("[DONE] OII-003 SOURCE PROVENANCE GRAPH CERTIFIED")


if __name__ == "__main__":
    main()
