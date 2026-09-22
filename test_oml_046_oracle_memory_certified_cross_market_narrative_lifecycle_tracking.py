from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_lifecycle_tracking import (
    OracleMemoryCertifiedCrossMarketLifecycleInvariantError,
    build_oracle_memory_certified_cross_market_narrative_lifecycle,
    verify_oracle_memory_certified_cross_market_narrative_lifecycle,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
    build_oracle_memory_observation_narrative_request,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    build_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_temporal_tracking_and_lifecycle_memory import (
    TRANSITION_STRENGTHENED,
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load fixture: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_rejection(callable_object, label: str) -> None:
    try:
        callable_object()
    except OracleMemoryCertifiedCrossMarketLifecycleInvariantError:
        return
    raise AssertionError(f"tampered OML-046 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-046 TEST")
    print(" CERTIFIED CROSS-MARKET NARRATIVE LIFECYCLE TRACKING")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_045_oracle_memory_certified_cross_market_narrative_detection_and_evolution.py",
        "oml_045_fixture_for_oml_046",
    )
    graph, liquidity, bitcoin = fixture.build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    prior = build_oracle_memory_narrative(
        graph=graph.graph_materialization.graph,
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
        first_observed_at="2026-08-02T16:50:00-05:00",
        last_observed_at="2026-08-02T17:00:00-05:00",
        evolution_index=1,
    )
    assert prior.stage == NARRATIVE_STAGE_EMERGING

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
        first_observed_at="2026-08-02T16:50:00-05:00",
        last_observed_at="2026-08-02T17:10:00-05:00",
        evolution_index=2,
        prior_stage=prior.stage,
    )

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_narrative_detection_and_evolution import (
        build_oracle_memory_certified_cross_market_narrative_detection,
    )

    detection = build_oracle_memory_certified_cross_market_narrative_detection(
        graph=graph,
        requests=(current_request,),
    )
    current = detection.narrative_detection.narratives[0]
    assert current.stage == NARRATIVE_STAGE_STRENGTHENING
    assert current.narrative_id == prior.narrative_id

    result = build_oracle_memory_certified_cross_market_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )

    assert result.schema_version == "OML-046"
    assert result.engine_id == "OML-046"
    assert result.upstream_schema_version == "OML-045"
    assert result.upstream_engine_id == "OML-045"
    assert result.lifecycle_schema_version == "OML-033"
    assert result.lifecycle_engine_id == "OML-033"
    assert result.narrative_count == 1
    assert result.snapshot_count == 2
    assert result.transition_count == 1
    transition = result.lifecycle_tracking.lifecycle_memory.transitions[0]
    assert transition.transition_type == TRANSITION_STRENGTHENED
    assert transition.confidence_delta > 0
    assert transition.uncertainty_delta < 0
    assert transition.evidence_growth == 2
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
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_narrative_lifecycle(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, downstream_source_reliability_authorized=False)
        ),
        "source reliability continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_narrative_lifecycle(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-045 narrative detection consumed read-only")
    print("[PASS] Exact OML-032 detection dataclass passed directly")
    print("[PASS] Actual OML-033 lifecycle builder consumed")
    print("[PASS] Narrative identity preserved across evolution")
    print("[PASS] Strengthened lifecycle transition created")
    print("[PASS] Confidence and uncertainty deltas tracked")
    print("[PASS] Evidence growth tracked")
    print("[PASS] Entity and relationship lineage preserved")
    print("[PASS] Source-reliability continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-046 lifecycle records rejected")
    print(
        "[DONE] OML-046 CERTIFIED CROSS-MARKET "
        "NARRATIVE LIFECYCLE TRACKING PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
