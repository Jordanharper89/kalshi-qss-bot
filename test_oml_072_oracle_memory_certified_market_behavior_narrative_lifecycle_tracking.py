from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking_072 import (
    OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError,
    build_oracle_memory_certified_market_behavior_narrative_lifecycle_072,
    verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    build_oracle_memory_narrative,
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
    except OracleMemoryCertifiedMarketBehaviorLifecycle072InvariantError:
        return
    raise AssertionError(f"tampered OML-072 {label} accepted")


def build_lifecycle(root: Path):
    fixture_071 = load_module(
        root
        / "test_oml_071_oracle_memory_certified_market_behavior_"
        "narrative_detection_and_evolution.py",
        "oml_071_fixture_for_oml_072_full_rewrite",
    )
    detection = fixture_071.build_detection(root)
    current = detection.narrative_detection.narratives[0]

    fixture_070 = load_module(
        root
        / "test_oml_070_oracle_memory_certified_market_behavior_"
        "relationship_graph.py",
        "oml_070_fixture_for_oml_072_full_rewrite",
    )
    resolution = fixture_070.build_resolution(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_relationship_graph_070 import (
        build_oracle_memory_certified_market_behavior_relationship_graph_070,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
        build_oracle_memory_observation_relationship_request,
    )

    entities = {
        entity.normalized_name: entity
        for entity in resolution.resolution.entities
    }
    liquidity = entities["stablecoin liquidity"]
    bitcoin = entities["bitcoin"]

    relationship_request = build_oracle_memory_observation_relationship_request(
        source_entity_id=liquidity.canonical_entity_id,
        target_entity_id=bitcoin.canonical_entity_id,
        relationship_type="precedes market repricing",
        evidence_hashes=("5" * 64, "6" * 64),
        confidence=0.84,
        contradiction_count=0,
        directed=True,
    )
    graph_wrapper = (
        build_oracle_memory_certified_market_behavior_relationship_graph_070(
            resolution=resolution,
            requests=(relationship_request,),
        )
    )
    graph = graph_wrapper.graph_materialization.graph

    graph_entity_ids = tuple(
        sorted(entity.canonical_entity_id for entity in graph.entities)
    )
    graph_relationship_ids = tuple(
        sorted(item.relationship_id for item in graph.relationships)
    )

    assert current.participating_entity_ids == graph_entity_ids
    assert current.relationship_ids == graph_relationship_ids

    prior = build_oracle_memory_narrative(
        graph=graph,
        title=current.title,
        participating_entity_ids=current.participating_entity_ids,
        relationship_ids=current.relationship_ids,
        supporting_evidence_hashes=("7" * 64,),
        contradicting_evidence_hashes=(),
        confidence=0.58,
        uncertainty=0.42,
        first_observed_at=current.first_observed_at,
        last_observed_at="2026-08-04T12:05:00-05:00",
        evolution_index=1,
    )

    return build_oracle_memory_certified_market_behavior_narrative_lifecycle_072(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )


def main() -> int:
    print("=" * 48)
    print(" OML-072 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR NARRATIVE LIFECYCLE")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result = build_lifecycle(root)

    assert result.schema_version == "OML-072"
    assert result.engine_id == "OML-072"
    assert result.upstream_schema_version == "OML-071"
    assert result.upstream_engine_id == "OML-071"
    assert result.lifecycle_schema_version == "OML-033"
    assert result.lifecycle_engine_id == "OML-033"
    assert result.narrative_count == 1
    assert result.snapshot_count >= 2
    assert result.transition_count >= 1
    assert result.detection_lineage_verified
    assert result.observation_lifecycle_lineage_verified
    assert result.entity_lineage_preserved
    assert result.relationship_lineage_preserved
    assert result.canonical_temporal_order_verified
    assert result.deterministic_lifecycle_tracking_verified
    assert result.evidence_growth_tracked
    assert result.contradiction_growth_tracked
    assert result.lifecycle_ready
    assert result.downstream_source_reliability_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    replay = build_lifecycle(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_narrative_lifecycle_072(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-071 detection consumed read-only")
    print("[PASS] Exact OML-032 detection object passed directly")
    print("[PASS] OML-070 graph rebuilt through exact certified builders")
    print("[PASS] Canonical entity ordering consumed from certified narrative")
    print("[PASS] Exact relationship lineage consumed from certified narrative")
    print("[PASS] Actual OML-033 lifecycle builder consumed")
    print("[PASS] Temporal evolution indexes remained monotonic")
    print("[PASS] Evidence and contradiction growth retained")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-072 lifecycle objects rejected")
    print("[DONE] OML-072 FULL REWRITE CERTIFIED PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
