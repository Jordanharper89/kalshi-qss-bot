from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_detection,
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_lifecycle_tracking import (
    OracleMemoryObservationNarrativeLifecycleInvariantError,
    build_oracle_memory_observation_narrative_lifecycle_tracking,
    verify_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
    build_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    OracleMemoryNarrativeTemporalInvariantError,
    TRANSITION_STRENGTHENED,
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
    except (
        OracleMemoryObservationNarrativeLifecycleInvariantError,
        OracleMemoryNarrativeInvariantError,
        OracleMemoryNarrativeTemporalInvariantError,
    ):
        return

    raise AssertionError(f"tampered OML-033 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-033 TEST")
    print(" CERTIFIED OBSERVATION NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_031 = load_module(
        root
        / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py",
        "oml_031_fixture_for_oml_033",
    )

    resolution = fixture_031.build_resolution(root)

    liquidity = next(
        item
        for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item
        for item in resolution.entities
        if item.normalized_name == "bitcoin"
    )

    relationship_request = (
        build_oracle_memory_observation_relationship_request(
            source_entity_id=liquidity.canonical_entity_id,
            target_entity_id=bitcoin.canonical_entity_id,
            relationship_type="precedes market repricing",
            evidence_hashes=("5" * 64, "6" * 64),
            confidence=0.84,
            contradiction_count=0,
            directed=True,
        )
    )

    graph_materialization = (
        build_oracle_memory_observation_relationship_graph_materialization(
            resolution=resolution,
            requests=(relationship_request,),
        )
    )

    relationship = graph_materialization.graph.relationships[0]

    prior_narrative = build_oracle_memory_narrative(
        graph=graph_materialization.graph,
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=("7" * 64,),
        contradicting_evidence_hashes=(),
        confidence=0.58,
        uncertainty=0.42,
        first_observed_at="2026-08-02T14:50:00-05:00",
        last_observed_at="2026-08-02T15:00:00-05:00",
        evolution_index=1,
    )

    assert prior_narrative.stage == NARRATIVE_STAGE_EMERGING

    current_request = build_oracle_memory_observation_narrative_request(
        title="Stablecoin liquidity precedes Bitcoin repricing",
        participating_entity_ids=(
            liquidity.canonical_entity_id,
            bitcoin.canonical_entity_id,
        ),
        relationship_ids=(relationship.relationship_id,),
        supporting_evidence_hashes=(
            "7" * 64,
            "8" * 64,
            "9" * 64,
        ),
        contradicting_evidence_hashes=(),
        confidence=0.82,
        uncertainty=0.18,
        first_observed_at="2026-08-02T14:50:00-05:00",
        last_observed_at="2026-08-02T15:10:00-05:00",
        evolution_index=2,
        prior_stage=prior_narrative.stage,
    )

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(current_request,),
    )

    current_narrative = detection.narratives[0]

    assert current_narrative.stage == NARRATIVE_STAGE_STRENGTHENING
    assert current_narrative.narrative_id == prior_narrative.narrative_id

    tracking = (
        build_oracle_memory_observation_narrative_lifecycle_tracking(
            detection=detection,
            prior_histories={
                current_narrative.narrative_id: (prior_narrative,)
            },
        )
    )

    assert tracking.schema_version == "OML-033"
    assert tracking.engine_id == "OML-033"
    assert tracking.upstream_schema_version == "OML-032"
    assert tracking.upstream_engine_id == "OML-032"
    assert tracking.narrative_count == 1
    assert tracking.snapshot_count == 2
    assert tracking.transition_count == 1
    assert tracking.lifecycle_memory.transitions[0].transition_type == (
        TRANSITION_STRENGTHENED
    )
    assert tracking.lifecycle_memory.transitions[0].confidence_delta > 0
    assert tracking.lifecycle_memory.transitions[0].uncertainty_delta < 0
    assert tracking.lifecycle_memory.transitions[0].evidence_growth == 2
    assert tracking.bindings[0].observation_lineage_verified
    assert tracking.certified_detection_lineage_verified
    assert tracking.observation_lifecycle_lineage_verified
    assert tracking.canonical_temporal_order_verified
    assert tracking.deterministic_lifecycle_tracking_verified
    assert tracking.entity_lineage_preserved
    assert tracking.relationship_lineage_preserved
    assert tracking.evidence_growth_tracked
    assert tracking.contradiction_growth_tracked
    assert not tracking.persistence_enabled
    assert not tracking.learning_updates_enabled
    assert not tracking.runtime_activation_enabled
    assert not tracking.publication_enabled
    assert not tracking.action_authorization_enabled
    assert not tracking.qseries_execution_enabled
    assert tracking.lifecycle_ready
    assert tracking.downstream_source_reliability_authorized
    assert tracking.read_only

    replay = build_oracle_memory_observation_narrative_lifecycle_tracking(
        detection=detection,
        prior_histories={
            current_narrative.narrative_id: (prior_narrative,)
        },
    )

    assert replay == tracking
    assert (
        verify_oracle_memory_observation_narrative_lifecycle_tracking(
            tracking
        )
    )

    expect_rejection(
        lambda: build_oracle_memory_observation_narrative_lifecycle_tracking(
            detection=detection,
            prior_histories={
                "f" * 64: (prior_narrative,)
            },
        ),
        "unknown history",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(tracking, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(
                tracking,
                downstream_source_reliability_authorized=False,
            )
        ),
        "source reliability authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_lifecycle_tracking(
            replace(tracking, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-032 narrative detection consumed")
    print("[PASS] Certified OML-021 lifecycle engine consumed")
    print("[PASS] Prior and current narrative history assembled")
    print("[PASS] Narrative identity preserved across evolution")
    print("[PASS] Monotonic evolution index enforced")
    print("[PASS] Strengthened lifecycle transition created")
    print("[PASS] Confidence and uncertainty deltas tracked")
    print("[PASS] Evidence growth tracked")
    print("[PASS] Source observation lineage retained")
    print("[PASS] Lifecycle tracking deterministic across replay")
    print("[PASS] Source reliability continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered lifecycle tracking rejected")
    print(
        "[DONE] OML-033 CERTIFIED OBSERVATION "
        "NARRATIVE LIFECYCLE TRACKING PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
