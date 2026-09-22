from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability import (
    OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError,
    build_oracle_memory_certified_market_behavior_source_reliability,
    verify_oracle_memory_certified_market_behavior_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    build_oracle_memory_certified_source_outcome,
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
    except OracleMemoryCertifiedMarketBehaviorReliabilityInvariantError:
        return
    raise AssertionError(f"tampered OML-060 {label} accepted")


def build_lifecycle(root: Path):
    fixture = load_module(
        root
        / "test_oml_058_oracle_memory_certified_market_behavior_narrative_detection_and_evolution.py",
        "oml_058_fixture_for_oml_060",
    )
    graph, liquidity, bitcoin = fixture.build_graph(root)
    relationship = graph.graph_materialization.graph.relationships[0]

    from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
        build_oracle_memory_narrative,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_narrative_detection_and_evolution import (
        build_oracle_memory_observation_narrative_request,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_detection_and_evolution import (
        build_oracle_memory_certified_market_behavior_narrative_detection,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_narrative_lifecycle_tracking import (
        build_oracle_memory_certified_market_behavior_narrative_lifecycle,
    )

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

    request = build_oracle_memory_observation_narrative_request(
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

    detection = (
        build_oracle_memory_certified_market_behavior_narrative_detection(
            graph=graph,
            requests=(request,),
        )
    )
    current = detection.narrative_detection.narratives[0]

    return build_oracle_memory_certified_market_behavior_narrative_lifecycle(
        detection=detection,
        prior_histories={current.narrative_id: (prior,)},
    )


def main() -> int:
    print("=" * 48)
    print(" OML-060 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    lifecycle = build_lifecycle(root)

    observation_hashes = tuple(sorted({
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }))
    assert observation_hashes

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Cross-Market Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=(index % 2 == 0),
            contradiction_count=0 if index % 2 == 0 else 1,
            confidence_at_observation=0.80 - (index * 0.05),
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    result = build_oracle_memory_certified_market_behavior_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )

    assert result.schema_version == "OML-060"
    assert result.engine_id == "OML-060"
    assert result.upstream_schema_version == "OML-059"
    assert result.upstream_engine_id == "OML-059"
    assert result.reliability_schema_version == "OML-034"
    assert result.reliability_engine_id == "OML-034"
    assert result.source_count == 1
    assert result.total_observation_count == len(outcomes)
    assert result.upstream_certification_hash == lifecycle.certification_hash
    assert result.upstream_lifecycle_tracking_hash == (
        lifecycle.lifecycle_tracking.tracking_hash
    )
    assert result.lifecycle_lineage_verified
    assert result.narrative_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.source_identity_uniqueness_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_tracking_verified
    assert result.reliability_ready
    assert result.downstream_calibration_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_source_reliability(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, downstream_calibration_authorized=False)
        ),
        "calibration continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-059 lifecycle consumed read-only")
    print("[PASS] Exact OML-033 lifecycle-tracking dataclass passed directly")
    print("[PASS] Actual OML-034 source-reliability builder consumed")
    print("[PASS] Outcomes bound only to certified observation hashes")
    print("[PASS] Narrative and lifecycle lineage retained")
    print("[PASS] Reliability and calibration tracking retained")
    print("[PASS] Calibration continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-060 reliability records rejected")
    print("[DONE] OML-060 CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
