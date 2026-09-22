from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_REAL_WORLD,
    OracleMemoryObservationIntakeInvariantError,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
    verify_oracle_memory_observation_intake_batch,
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
    except OracleMemoryObservationIntakeInvariantError:
        return

    raise AssertionError(f"tampered OML-027 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-027 TEST")
    print(" CERTIFIED OBSERVATION INTAKE CONTRACT")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture = load_module(
        root / "test_oml_026_oracle_memory_cross_market_dependency_memory.py",
        "oml_026_fixture_for_oml_027",
    )

    chain_memory, _ = fixture.build_chain_memory(root)

    cross_market_memory = build_oracle_memory_cross_market_dependency_memory(
        causal_chain_memory=chain_memory,
        dependencies=(),
    )

    observation = build_oracle_memory_certified_observation(
        observation_kind=OBSERVATION_KIND_REAL_WORLD,
        domain_id=(
            "market_behavior_memory"
            if "market_behavior_memory"
            in fixture.__dict__.get("MEMORY_DOMAINS", ())
            else __import__(
                "qseries_v2.oracle_memory."
                "oracle_memory_continuous_intelligence_learner_foundation",
                fromlist=["MEMORY_DOMAINS"],
            ).MEMORY_DOMAINS[0]
        ),
        entity_key="Bitcoin",
        source_key="oracle-live-shadow",
        observed_at="2026-08-02T15:00:00-05:00",
        effective_at="2026-08-02T15:00:00-05:00",
        payload={
            "observation": (
                "Real-world liquidity conditions changed before "
                "the financial-market reaction."
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

    batch = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )

    assert batch.schema_version == "OML-027"
    assert batch.engine_id == "OML-027"
    assert batch.upstream_schema_version == "OML-026"
    assert batch.upstream_engine_id == "OML-026"
    assert batch.observation_count == 2
    assert batch.unique_observation_count == 1
    assert batch.duplicate_observation_count == 1
    assert batch.canonical_order_verified
    assert batch.deterministic_hashing_verified
    assert batch.duplicate_detection_verified
    assert batch.evidence_lineage_verified
    assert batch.source_certification_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.intake_ready
    assert not batch.candidate_materialization_authorized
    assert batch.read_only

    replay = build_oracle_memory_observation_intake_batch(
        cross_market_memory=cross_market_memory,
        observations=(observation, observation),
    )

    assert replay == batch
    assert verify_oracle_memory_observation_intake_batch(batch)

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, observation_count=3)
        ),
        "observation count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, candidate_materialization_authorized=True)
        ),
        "candidate materialization boundary",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_intake_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-026 cross-market memory consumed")
    print("[PASS] Real-world observation intake contract created")
    print("[PASS] Observation payload canonicalized")
    print("[PASS] Evidence and source-certification lineage retained")
    print("[PASS] Deterministic observation identity generated")
    print("[PASS] Duplicate observation detected")
    print("[PASS] Candidate materialization remained unauthorized")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Intake batch deterministic across replay")
    print("[PASS] Tampered observation batches rejected")
    print("[DONE] OML-027 CERTIFIED OBSERVATION INTAKE CONTRACT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
