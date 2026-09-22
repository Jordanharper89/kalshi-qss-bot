from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    OracleMemoryObservationNarrativeInvariantError,
    build_oracle_memory_observation_narrative_detection,
    build_oracle_memory_observation_narrative_request,
    verify_oracle_memory_observation_narrative_detection,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_STRENGTHENING,
    OracleMemoryNarrativeInvariantError,
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
        OracleMemoryObservationNarrativeInvariantError,
        OracleMemoryNarrativeInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-032 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-032 TEST")
    print(" CERTIFIED OBSERVATION NARRATIVE DETECTION AND EVOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture_031 = load_module(
        root
        / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py",
        "oml_031_fixture_for_oml_032",
    )

    resolution = fixture_031.build_resolution(root)
    liquidity = next(
        item for item in resolution.entities
        if item.normalized_name == "stablecoin liquidity"
    )
    bitcoin = next(
        item for item in resolution.entities
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

    narrative_request = build_oracle_memory_observation_narrative_request(
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
        first_observed_at="2026-08-02T15:00:00-05:00",
        last_observed_at="2026-08-02T15:10:00-05:00",
        evolution_index=1,
    )

    detection = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(narrative_request,),
    )

    assert detection.schema_version == "OML-032"
    assert detection.engine_id == "OML-032"
    assert detection.upstream_schema_version == "OML-031"
    assert detection.upstream_engine_id == "OML-031"
    assert detection.narrative_count == 1
    assert detection.strengthening_count == 1
    assert detection.narratives[0].stage == (
        NARRATIVE_STAGE_STRENGTHENING
    )
    assert detection.bindings[0].observation_lineage_verified
    assert detection.certified_graph_lineage_verified
    assert detection.observation_narrative_lineage_verified
    assert detection.canonical_order_verified
    assert detection.deterministic_detection_verified
    assert detection.contradiction_tracking_verified
    assert not detection.persistence_enabled
    assert not detection.learning_updates_enabled
    assert not detection.runtime_activation_enabled
    assert not detection.publication_enabled
    assert not detection.action_authorization_enabled
    assert not detection.qseries_execution_enabled
    assert detection.detection_ready
    assert detection.downstream_lifecycle_tracking_authorized
    assert detection.read_only

    replay = build_oracle_memory_observation_narrative_detection(
        materialization=graph_materialization,
        requests=(narrative_request,),
    )
    assert replay == detection
    assert verify_oracle_memory_observation_narrative_detection(detection)

    expect_rejection(
        lambda: build_oracle_memory_observation_narrative_request(
            title="Invalid",
            participating_entity_ids=(),
            relationship_ids=(relationship.relationship_id,),
            supporting_evidence_hashes=("a" * 64,),
            confidence=0.5,
            uncertainty=0.5,
            first_observed_at="2026-08-02T15:00:00-05:00",
            last_observed_at="2026-08-02T15:10:00-05:00",
        ),
        "empty entity lineage",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(detection, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(
                detection,
                downstream_lifecycle_tracking_authorized=False,
            )
        ),
        "lifecycle authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_narrative_detection(
            replace(detection, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-031 graph materialization consumed")
    print("[PASS] Certified OML-020 narrative engine consumed")
    print("[PASS] Exact OML-019 graph dataclass passed directly")
    print("[PASS] Observation-backed narrative created")
    print("[PASS] Strengthening narrative stage detected")
    print("[PASS] Entity and relationship lineage retained")
    print("[PASS] Source observation lineage retained")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Narrative detection deterministic across replay")
    print("[PASS] Lifecycle continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered narrative detections rejected")
    print(
        "[DONE] OML-032 CERTIFIED OBSERVATION "
        "NARRATIVE DETECTION AND EVOLUTION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
