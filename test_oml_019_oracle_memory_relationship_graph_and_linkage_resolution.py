from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    build_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
    build_oracle_memory_entity_resolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    OracleMemoryRelationshipGraphInvariantError,
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
    verify_oracle_memory_relationship_graph,
)


def load_module(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)

    if specification is None or specification.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")

    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryRelationshipGraphInvariantError:
        return

    raise AssertionError(f"tampered OML-019 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-019 TEST")
    print(" RELATIONSHIP GRAPH AND LINKAGE RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_019",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_019",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_btc = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:bitcoin",
        entity_key="Bitcoin",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "crypto_asset"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.90,
        uncertainty=0.10,
        contradiction_count=0,
    )

    candidate_etf = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:bitcoin-etf",
        entity_key="Bitcoin ETF",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "financial_product"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.88,
        uncertainty=0.12,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate_btc, candidate_etf),
    )

    entities = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate_btc.candidate_hash: ("BTC", "XBT"),
            candidate_etf.candidate_hash: ("Spot Bitcoin ETF",),
        },
    )

    bitcoin = next(
        item for item in entities.entities
        if item.normalized_name == "bitcoin"
    )
    bitcoin_etf = next(
        item for item in entities.entities
        if item.normalized_name == "bitcoin etf"
    )

    relationship = build_oracle_memory_entity_relationship(
        source_entity=bitcoin_etf,
        target_entity=bitcoin,
        relationship_type="tracks underlying asset",
        evidence_hashes=("3" * 64, "4" * 64),
        confidence=0.97,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    assert graph.schema_version == "OML-019"
    assert graph.engine_id == "OML-019"
    assert graph.upstream_schema_version == "OML-018"
    assert graph.upstream_engine_id == "OML-018"
    assert graph.entity_count == 2
    assert graph.relationship_count == 1
    assert graph.canonical_entity_order_verified
    assert graph.canonical_relationship_order_verified
    assert graph.entity_identity_uniqueness_verified
    assert graph.relationship_identity_uniqueness_verified
    assert graph.self_links_rejected
    assert graph.dangling_links_rejected
    assert graph.duplicate_links_rejected
    assert graph.deterministic_graph_hashing_verified
    assert not graph.persistence_enabled
    assert not graph.learning_updates_enabled
    assert not graph.runtime_activation_enabled
    assert not graph.publication_enabled
    assert not graph.action_authorization_enabled
    assert not graph.qseries_execution_enabled
    assert graph.graph_ready
    assert graph.next_certification_authorized
    assert graph.read_only

    replay = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    assert replay == graph
    assert verify_oracle_memory_relationship_graph(graph)

    expect_rejection(
        lambda: build_oracle_memory_relationship_graph(
            entity_batch=entities,
            relationships=(relationship, relationship),
        ),
        "duplicate relationship",
    )

    expect_rejection(
        lambda: verify_oracle_memory_relationship_graph(
            replace(graph, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_relationship_graph(
            replace(graph, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-018 entity resolution consumed")
    print("[PASS] Canonical entity identities retained")
    print("[PASS] Evidence-backed relationship created")
    print("[PASS] Stable relationship identity generated")
    print("[PASS] Self-links rejected")
    print("[PASS] Dangling links rejected")
    print("[PASS] Duplicate links rejected")
    print("[PASS] Canonical graph ordering verified")
    print("[PASS] Relationship graph deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered graphs rejected")
    print("[DONE] OML-019 RELATIONSHIP GRAPH AND LINKAGE RESOLUTION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
