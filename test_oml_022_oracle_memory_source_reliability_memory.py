from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    SOURCE_STATUS_RELIABLE,
    OracleMemorySourceReliabilityInvariantError,
    build_oracle_memory_source_observation,
    build_oracle_memory_source_reliability_memory,
    verify_oracle_memory_source_reliability_memory,
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
    except OracleMemorySourceReliabilityInvariantError:
        return

    raise AssertionError(f"tampered OML-022 {label} accepted")


def build_lifecycle_memory(root: Path):
    fixture = load_module(
        root
        / "test_oml_021_oracle_memory_narrative_temporal_tracking_and_lifecycle_memory.py",
        "oml_021_fixture_for_oml_022",
    )

    # Reuse the certified test itself as the source of truth by
    # reproducing its public construction path.
    fixture.main()

    # Load its upstream OML-020 fixture and construct a minimal valid
    # lifecycle memory through the certified production functions.
    from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
        build_oracle_memory_narrative_lifecycle_memory,
    )
    from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
        build_oracle_memory_narrative,
        build_oracle_memory_narrative_evolution_batch,
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
    from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
        build_oracle_memory_ledger_integrity_replay_certification,
    )
    from qseries_v2.oracle_memory.oracle_memory_relationship_graph_and_linkage_resolution import (
        build_oracle_memory_entity_relationship,
        build_oracle_memory_relationship_graph,
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_022",
    )
    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_022",
    )
    gate = fixture_009.build_oml_008_decision(root)

    candidate_a = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:source-reliability:a",
        entity_key="Observed Reality",
        source_key="source-alpha",
        observed_at="2026-08-02T14:40:00-05:00",
        effective_at="2026-08-02T14:40:00-05:00",
        payload={"kind": "real_world_observation"},
        evidence_hashes=("1" * 64,),
        parent_record_hashes=(),
        confidence=0.75,
        uncertainty=0.25,
        contradiction_count=0,
    )

    candidate_b = build_oracle_memory_canonical_record_candidate(
        gate_decision=gate,
        domain_id=gate.admitted_domain_ids[0],
        candidate_id="candidate:source-reliability:b",
        entity_key="Market Reaction",
        source_key="source-beta",
        observed_at="2026-08-02T14:40:00-05:00",
        effective_at="2026-08-02T14:40:00-05:00",
        payload={"kind": "financial_response"},
        evidence_hashes=("2" * 64,),
        parent_record_hashes=(),
        confidence=0.75,
        uncertainty=0.25,
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

    observed = next(
        item for item in entities.entities
        if item.normalized_name == "observed reality"
    )
    market = next(
        item for item in entities.entities
        if item.normalized_name == "market reaction"
    )

    relationship = build_oracle_memory_entity_relationship(
        source_entity=observed,
        target_entity=market,
        relationship_type="precedes",
        evidence_hashes=("3" * 64,),
        confidence=0.80,
        contradiction_count=0,
        directed=True,
    )

    graph = build_oracle_memory_relationship_graph(
        entity_batch=entities,
        relationships=(relationship,),
    )

    narrative_v1 = build_oracle_memory_narrative(
        graph=graph,
        title="Observed reality precedes market reaction",
        participating_entity_ids=(
            observed.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("4" * 64,),
        confidence=0.60,
        uncertainty=0.40,
        first_observed_at="2026-08-02T14:40:00-05:00",
        last_observed_at="2026-08-02T14:40:00-05:00",
        evolution_index=1,
    )

    narrative_v2 = build_oracle_memory_narrative(
        graph=graph,
        title="Observed reality precedes market reaction",
        participating_entity_ids=(
            observed.canonical_entity_id,
            market.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "4" * 64,
            "5" * 64,
            "6" * 64,
        ),
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

    return build_oracle_memory_narrative_lifecycle_memory(
        upstream_batch=upstream_batch,
        narrative_histories={
            narrative_v1.narrative_id: (
                narrative_v1,
                narrative_v2,
            )
        },
    )


def main() -> int:
    print("=" * 48)
    print(" OML-022 TEST")
    print(" SOURCE RELIABILITY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    lifecycle_memory = build_lifecycle_memory(root)

    observations = (
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="1" * 64,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.80,
            observed_at="2026-08-02T14:40:00-05:00",
        ),
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="2" * 64,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.75,
            observed_at="2026-08-02T14:45:00-05:00",
        ),
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="3" * 64,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=1,
            confidence_at_observation=0.70,
            observed_at="2026-08-02T14:50:00-05:00",
        ),
    )

    memory = build_oracle_memory_source_reliability_memory(
        lifecycle_memory=lifecycle_memory,
        observations_by_source={
            "Source Alpha": observations,
        },
    )

    assert memory.schema_version == "OML-022"
    assert memory.engine_id == "OML-022"
    assert memory.upstream_schema_version == "OML-021"
    assert memory.upstream_engine_id == "OML-021"
    assert memory.source_count == 1
    assert memory.total_observation_count == 3

    profile = memory.profiles[0]

    assert profile.source_status == SOURCE_STATUS_RELIABLE
    assert profile.observation_count == 3
    assert profile.confirmed_outcome_count == 3
    assert profile.correct_outcome_count == 3
    assert profile.incorrect_outcome_count == 0
    assert profile.unresolved_outcome_count == 0
    assert profile.contradiction_count == 1
    assert profile.reliability_score == 1.0
    assert profile.calibration_error == 0.25
    assert profile.evidence_depth == 3
    assert profile.deterministic_scoring_verified
    assert profile.canonical_order_verified
    assert profile.source_identity_verified
    assert not profile.persistence_authorized
    assert not profile.learning_update_authorized
    assert not profile.runtime_activation_authorized
    assert not profile.publication_authorized
    assert not profile.action_authorization_enabled
    assert not profile.qseries_execution_authorized
    assert profile.read_only

    assert memory.deterministic_scoring_verified
    assert memory.source_identity_uniqueness_verified
    assert memory.canonical_source_order_verified
    assert memory.outcome_lineage_verified
    assert memory.contradiction_tracking_verified
    assert memory.calibration_tracking_verified
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_source_reliability_memory(
        lifecycle_memory=lifecycle_memory,
        observations_by_source={
            "Source Alpha": observations,
        },
    )

    assert replay == memory
    assert verify_oracle_memory_source_reliability_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_source_reliability_memory(
            replace(memory, source_count=2)
        ),
        "source count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_source_reliability_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_source_reliability_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-021 lifecycle memory consumed")
    print("[PASS] Stable source identities generated")
    print("[PASS] Source observations canonicalized")
    print("[PASS] Confirmed outcomes tracked")
    print("[PASS] Correct and incorrect outcomes reconciled")
    print("[PASS] Contradictions accumulated")
    print("[PASS] Reliability score calculated deterministically")
    print("[PASS] Calibration error calculated deterministically")
    print("[PASS] Reliable source status assigned")
    print("[PASS] Source memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered source memories rejected")
    print("[DONE] OML-022 SOURCE RELIABILITY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
