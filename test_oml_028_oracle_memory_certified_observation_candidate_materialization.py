from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    MATERIALIZATION_STATUS_DUPLICATE,
    MATERIALIZATION_STATUS_READY,
    OracleMemoryObservationMaterializationInvariantError,
    build_oracle_memory_observation_candidate_materialization_batch,
    verify_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_REAL_WORLD,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
)
from qseries_v2.oracle_memory.oracle_memory_cross_market_dependency_memory import (
    build_oracle_memory_cross_market_dependency_memory,
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
    except OracleMemoryObservationMaterializationInvariantError:
        return

    raise AssertionError(f"tampered OML-028 {label} accepted")


def build_intake_batch(root: Path):
    fixture_026 = load_module(
        root
        / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_028_v2",
    )

    chain_memory, _ = fixture_026.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=MEMORY_DOMAINS[0],
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={
            "observation": (
                "Stablecoin liquidity increased before Bitcoin "
                "market repricing."
            ),
            "observation_type": "liquidity_shift",
            "market": "bitcoin",
        },
        evidence_hashes=("1" * 64, "2" * 64),
        source_certification_hash="3" * 64,
        confidence=0.81,
        uncertainty=0.19,
        contradiction_count=0,
    )

    intake_batch = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )

    fixture_009 = load_module(
        root
        / "test_oml_009_oracle_memory_canonical_record_candidate_contract.py",
        "oml_009_fixture_for_oml_028_v2",
    )
    gate_decision = fixture_009.build_oml_008_decision(root)

    return gate_decision, intake_batch


def main() -> int:
    print("=" * 48)
    print(" OML-028 CORRECTION V2 TEST")
    print(" CERTIFIED OBSERVATION CANDIDATE MATERIALIZATION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    gate_decision, intake_batch = build_intake_batch(root)

    batch = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake_batch,
        )
    )

    assert batch.schema_version == "OML-028"
    assert batch.engine_id == "OML-028"
    assert batch.upstream_schema_version == "OML-027"
    assert batch.upstream_engine_id == "OML-027"
    assert batch.upstream_gate_decision_hash == gate_decision.decision_hash
    assert batch.observation_count == 2
    assert batch.candidate_count == 2
    assert batch.unique_candidate_count == 1
    assert batch.duplicate_candidate_count == 1

    assert batch.bindings[0].materialization_status == (
        MATERIALIZATION_STATUS_READY
    )
    assert batch.bindings[1].materialization_status == (
        MATERIALIZATION_STATUS_DUPLICATE
    )

    assert (
        batch.bindings[1].duplicate_of_candidate_hash
        == batch.candidates[0].candidate_hash
    )

    candidate = batch.candidates[0]

    assert candidate.schema_version == "OML-009"
    assert candidate.engine_id == "OML-009"
    assert candidate.policy_id == (
        "oracle-memory.canonical-record-candidate-contract.v1"
    )
    assert candidate.subsystem_id == batch.subsystem_id
    assert candidate.upstream_gate_decision_hash == (
        gate_decision.decision_hash
    )
    assert not candidate.admission_authorized
    assert not candidate.persistent_storage_authorized
    assert not candidate.learning_update_authorized
    assert not candidate.runtime_activation_authorized
    assert not candidate.publication_authorized
    assert not candidate.action_authorization_enabled
    assert not candidate.qseries_execution_authorized
    assert candidate.read_only

    assert candidate.payload["observation_hash"] == (
        intake_batch.observations[0].observation_hash
    )
    assert candidate.evidence_hashes == (
        intake_batch.observations[0].evidence_hashes
    )
    assert candidate.parent_record_hashes == (
        intake_batch.observations[0].parent_observation_hashes
    )
    assert candidate.payload["source_certification_hash"] == (
        intake_batch.observations[0].source_certification_hash
    )

    assert batch.canonical_order_verified
    assert batch.deterministic_materialization_verified
    assert batch.observation_candidate_lineage_verified
    assert batch.source_certification_lineage_verified
    assert batch.gate_decision_lineage_verified
    assert batch.duplicate_detection_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.materialization_ready
    assert batch.downstream_validation_authorized
    assert batch.read_only

    replay = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake_batch,
        )
    )

    assert replay == batch
    assert (
        verify_oracle_memory_observation_candidate_materialization_batch(
            batch
        )
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, candidate_count=3)
            )
        ),
        "candidate count",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, persistence_enabled=True)
            )
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, gate_decision_lineage_verified=False)
            )
        ),
        "gate decision lineage",
    )

    expect_rejection(
        lambda: (
            verify_oracle_memory_observation_candidate_materialization_batch(
                replace(batch, qseries_execution_enabled=True)
            )
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-027 intake batch consumed")
    print("[PASS] Certified OML-008 gate decision consumed")
    print("[PASS] Certified OML-009 builder consumed")
    print("[PASS] All six missing candidate fields populated")
    print("[PASS] Candidate admission remained disabled")
    print("[PASS] Observation payload lineage retained")
    print("[PASS] Evidence and parent lineage retained")
    print("[PASS] Source-certification lineage retained")
    print("[PASS] Duplicate candidate detected")
    print("[PASS] Downstream validation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Materialization deterministic across replay")
    print("[PASS] Tampered materialization batches rejected")
    print(
        "[DONE] OML-028 CORRECTION V2 "
        "CERTIFIED OBSERVATION CANDIDATE MATERIALIZATION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
