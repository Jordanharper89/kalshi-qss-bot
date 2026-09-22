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
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
    build_oracle_memory_narrative,
    build_oracle_memory_narrative_evolution_batch,
    verify_oracle_memory_narrative_evolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
    build_oracle_memory_entity_relationship,
    build_oracle_memory_relationship_graph,
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
    except OracleMemoryNarrativeInvariantError:
        return

    raise AssertionError(f"tampered OML-020 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-020 TEST")
    print(" NARRATIVE DETECTION AND EVOLUTION ENGINE")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_020",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_020",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_consumer = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:consumer-demand",
        entity_key="Consumer Demand",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "real_world_behavior"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.88,
        uncertainty=0.12,
        contradiction_count=0,
    )

    candidate_market = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:market-reaction",
        entity_key="Market Reaction",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:46:00-05:00",
        effective_at="2026-08-02T14:46:00-05:00",
        payload={"entity_type": "financial_response"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.84,
        uncertainty=0.16,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate_consumer, candidate_market),
    )

    entities = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={
            candidate_consumer.candidate_hash: (
                "Demand Shift",
                "Consumer Behavior",
            ),
            candidate_market.candidate_hash: (
                "Price Reaction",
                "Financial Market Response",
            ),
        },
    )

    consumer = next(
        item for item in entities.entities
        if item.normalized_name == "consumer demand"
    )
    market = next(
        item for item in entities.entities
        if item.normalized_name == "market reaction"
    )

    relationship = build_oracle_memory_entity_relationship(
        source_entity=consumer,
        target_entity=market,
        relationship_type="precedes",
        evidence_hashes=("3" * 64, "4" * 64),
        confidence=0.91,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    narrative = build_oracle_memory_narrative(
        graph=graph,
        title="Consumer demand shifting before market reaction",
        participating_entity_ids=(
            consumer.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "5" * 64,
            "6" * 64,
            "7" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T14:40:00-05:00",
        last_observed_at="2026-08-02T14:46:00-05:00",
        evolution_index=1,
    )

    assert narrative.stage == NARRATIVE_STAGE_STRENGTHENING
    assert narrative.contradiction_count == 0
    assert narrative.entity_lineage_verified
    assert narrative.relationship_lineage_verified
    assert narrative.evidence_lineage_verified
    assert narrative.deterministic_identity_verified
    assert narrative.canonical_order_verified
    assert not narrative.persistence_authorized
    assert not narrative.learning_update_authorized
    assert not narrative.runtime_activation_authorized
    assert not narrative.publication_authorized
    assert not narrative.action_authorization_enabled
    assert not narrative.qseries_execution_authorized
    assert narrative.read_only

    batch = build_oracle_memory_narrative_evolution_batch(
        graph=graph,
        narratives=(narrative,),
    )

    assert batch.schema_version == "OML-020"
    assert batch.engine_id == "OML-020"
    assert batch.upstream_schema_version == "OML-019"
    assert batch.upstream_engine_id == "OML-019"
    assert batch.narrative_count == 1
    assert batch.strengthening_count == 1
    assert batch.emerging_count == 0
    assert batch.weakening_count == 0
    assert batch.resolved_count == 0
    assert batch.canonical_order_verified
    assert batch.deterministic_detection_verified
    assert batch.deterministic_evolution_verified
    assert batch.entity_lineage_verified
    assert batch.relationship_lineage_verified
    assert batch.supporting_evidence_verified
    assert batch.contradiction_tracking_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.batch_ready
    assert batch.next_certification_authorized
    assert batch.read_only

    replay = build_oracle_memory_narrative_evolution_batch(
        graph=graph,
        narratives=(narrative,),
    )

    assert replay == batch
    assert verify_oracle_memory_narrative_evolution_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, narrative_count=2)
        ),
        "narrative count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_evolution_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-019 relationship graph consumed")
    print("[PASS] Participating entity lineage retained")
    print("[PASS] Relationship lineage retained")
    print("[PASS] Supporting evidence lineage retained")
    print("[PASS] Contradicting evidence tracking enabled")
    print("[PASS] Stable narrative identity generated")
    print("[PASS] Narrative stage detected deterministically")
    print("[PASS] Narrative evolution index retained")
    print("[PASS] Canonical narrative ordering verified")
    print("[PASS] Narrative batch deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered narrative batches rejected")
    print("[DONE] OML-020 NARRATIVE DETECTION AND EVOLUTION ENGINE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
