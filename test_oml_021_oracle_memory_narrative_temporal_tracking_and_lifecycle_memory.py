from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    build_oracle_memory_narrative,
    build_oracle_memory_narrative_evolution_batch,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    TRANSITION_STRENGTHENED,
    OracleMemoryNarrativeTemporalInvariantError,
    build_oracle_memory_narrative_lifecycle_memory,
    verify_oracle_memory_narrative_lifecycle_memory,
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
    except OracleMemoryNarrativeTemporalInvariantError:
        return

    raise AssertionError(f"tampered OML-021 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-021 TEST")
    print(" NARRATIVE TEMPORAL TRACKING AND LIFECYCLE MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture = load_module(
        root
        / "test_oml_020_oracle_memory_narrative_detection_and_evolution_engine.py",
        "oml_020_fixture_for_oml_021",
    )

    # Rebuild the certified OML-020 graph and first narrative by reusing
    # the tested construction path.
    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_021",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)

    from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
        build_oracle_memory_ledger_integrity_replay_certification,
    )
    from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
        build_oracle_memory_candidate_validation_batch,
    )
    from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
        build_oracle_memory_canonical_record_candidate,
    )
    from qseries_v2.oracle_memory.oracle_memory_entity_resolution import (
        build_oracle_memory_entity_resolution_batch,
    )
    from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
        build_oracle_memory_entity_relationship,
        build_oracle_memory_relationship_graph,
    )

    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_021",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_a = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:consumer-demand",
        entity_key="Consumer Demand",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:40:00-05:00",
        effective_at="2026-08-02T14:40:00-05:00",
        payload={"entity_type": "real_world_behavior"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.80,
        uncertainty=0.20,
        contradiction_count=0,
    )

    candidate_b = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:entity:market-reaction",
        entity_key="Market Reaction",
        source_key="certified-observation-source",
        observed_at="2026-08-02T14:40:00-05:00",
        effective_at="2026-08-02T14:40:00-05:00",
        payload={"entity_type": "financial_response"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.80,
        uncertainty=0.20,
        contradiction_count=0,
    )

    validation = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=(candidate_a, candidate_b),
    )

    entities = build_oracle_memory_entity_resolution_batch(
        validation_batch=validation,
        aliases_by_candidate_hash={},
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
        evidence_hashes=("3" * 64,),
        confidence=0.85,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    narrative_v1 = build_oracle_memory_narrative(
        graph=graph,
        title="Consumer demand shifting before market reaction",
        participating_entity_ids=(
            consumer.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("4" * 64,),
        contradicting_evidence_hashes=(),
        confidence=0.60,
        uncertainty=0.40,
        first_observed_at="2026-08-02T14:40:00-05:00",
        last_observed_at="2026-08-02T14:40:00-05:00",
        evolution_index=1,
    )

    narrative_v2 = build_oracle_memory_narrative(
        graph=graph,
        title="Consumer demand shifting before market reaction",
        participating_entity_ids=(
            consumer.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "4" * 64,
            "5" * 64,
            "6" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T14:40:00-05:00",
        last_observed_at="2026-08-02T15:10:00-05:00",
        evolution_index=2,
        prior_stage=narrative_v1.stage,
    )

    upstream_batch = build_oracle_memory_narrative_evolution_batch(
        graph=graph,
        narratives=(narrative_v2,),
    )

    memory = build_oracle_memory_narrative_lifecycle_memory(
        upstream_batch=upstream_batch,
        narrative_histories={
            narrative_v1.narrative_id: (
                narrative_v1,
                narrative_v2,
            )
        },
    )

    assert memory.schema_version == "OML-021"
    assert memory.engine_id == "OML-021"
    assert memory.upstream_schema_version == "OML-020"
    assert memory.upstream_engine_id == "OML-020"
    assert memory.narrative_count == 1
    assert memory.snapshot_count == 2
    assert memory.transition_count == 1
    assert memory.transitions[0].transition_type == TRANSITION_STRENGTHENED
    assert memory.transitions[0].confidence_delta == 0.22
    assert memory.transitions[0].uncertainty_delta == -0.22
    assert memory.transitions[0].evidence_growth == 2
    assert memory.transitions[0].contradiction_delta == 0
    assert memory.canonical_temporal_order_verified
    assert memory.deterministic_snapshot_hashing_verified
    assert memory.deterministic_transition_hashing_verified
    assert memory.stage_transition_rules_verified
    assert memory.entity_lineage_preserved
    assert memory.relationship_lineage_preserved
    assert memory.evidence_growth_tracked
    assert memory.contradiction_growth_tracked
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_narrative_lifecycle_memory(
        upstream_batch=upstream_batch,
        narrative_histories={
            narrative_v1.narrative_id: (
                narrative_v1,
                narrative_v2,
            )
        },
    )

    assert replay == memory
    assert verify_oracle_memory_narrative_lifecycle_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_narrative_lifecycle_memory(
            replace(memory, snapshot_count=3)
        ),
        "snapshot count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_lifecycle_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_narrative_lifecycle_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-020 narrative batch consumed")
    print("[PASS] Narrative temporal snapshots created")
    print("[PASS] Narrative lifecycle transition created")
    print("[PASS] Monotonic evolution index enforced")
    print("[PASS] Temporal order verified")
    print("[PASS] Strengthening transition detected")
    print("[PASS] Confidence and uncertainty deltas tracked")
    print("[PASS] Evidence growth tracked")
    print("[PASS] Contradiction growth tracked")
    print("[PASS] Entity and relationship lineage preserved")
    print("[PASS] Lifecycle memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered lifecycle memory rejected")
    print("[DONE] OML-021 NARRATIVE TEMPORAL TRACKING AND LIFECYCLE MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
