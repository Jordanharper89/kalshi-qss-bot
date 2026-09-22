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
    build_oracle_memory_observation_narrative_lifecycle_tracking,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_relationship_graph_materialization import (
    build_oracle_memory_observation_relationship_graph_materialization,
    build_oracle_memory_observation_relationship_request,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    OracleMemoryCertifiedSourceReliabilityInvariantError,
    build_oracle_memory_certified_source_outcome,
    build_oracle_memory_certified_source_reliability,
    verify_oracle_memory_certified_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_narrative_detection_and_evolution_engine import (
    NARRATIVE_STAGE_EMERGING,
    NARRATIVE_STAGE_STRENGTHENING,
    build_oracle_memory_narrative,
)
from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    SOURCE_STATUS_RELIABLE,
    OracleMemorySourceReliabilityInvariantError,
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
    except (
        OracleMemoryCertifiedSourceReliabilityInvariantError,
        OracleMemorySourceReliabilityInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-034 {label} accepted")


def build_tracking(root: Path):
    fixture_031 = load_module(
        root
        / "test_oml_031_oracle_memory_certified_observation_relationship_graph_materialization.py",
        "oml_031_fixture_for_oml_034",
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

    return build_oracle_memory_observation_narrative_lifecycle_tracking(
        detection=detection,
        prior_histories={
            current_narrative.narrative_id: (prior_narrative,)
        },
    )


def main() -> int:
    print("=" * 48)
    print(" OML-034 CORRECTION V2 TEST")
    print(" CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    tracking = build_tracking(root)
    observation_hashes = tracking.bindings[0].source_observation_hashes
    assert len(observation_hashes) >= 2

    outcomes = (
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.82,
            observed_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[1],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.79,
            observed_at="2026-08-02T15:10:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=1,
            confidence_at_observation=0.76,
            observed_at="2026-08-02T15:20:00-05:00",
        ),
    )

    result = build_oracle_memory_certified_source_reliability(
        tracking=tracking,
        outcomes=outcomes,
    )

    assert result.schema_version == "OML-034"
    assert result.engine_id == "OML-034"
    assert result.upstream_schema_version == "OML-033"
    assert result.upstream_engine_id == "OML-033"
    assert result.source_count == 1
    assert result.total_observation_count == 3
    assert result.reliability_memory.profiles[0].source_status == SOURCE_STATUS_RELIABLE
    assert result.reliability_memory.profiles[0].reliability_score == 1.0
    assert result.bindings[0].observation_lineage_verified
    assert result.certified_lifecycle_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.source_identity_uniqueness_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_tracking_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_calibration_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_source_reliability(
        tracking=tracking,
        outcomes=outcomes,
    )
    assert replay == result
    assert verify_oracle_memory_certified_source_reliability(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_source_outcome(
            source_name="Bad Source",
            observation_hash="f" * 64,
            outcome_confirmed=False,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.50,
            observed_at="2026-08-02T15:00:00-05:00",
        ),
        "invalid outcome",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, downstream_calibration_authorized=False)
        ),
        "calibration authorization",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_source_reliability(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-033 lifecycle tracking consumed")
    print("[PASS] Certified OML-022 source reliability engine consumed")
    print("[PASS] Exact lifecycle-memory dataclass passed directly")
    print("[PASS] Source outcomes bound to certified observations")
    print("[PASS] Reliable source profile created")
    print("[PASS] Reliability and calibration error calculated")
    print("[PASS] Contradiction tracking retained")
    print("[PASS] Source reliability deterministic across replay")
    print("[PASS] Calibration continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered source reliability rejected")
    print("[DONE] OML-034 CORRECTION V2 CERTIFIED OBSERVATION SOURCE RELIABILITY MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
