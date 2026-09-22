from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_materialization import (
    build_oracle_memory_observation_candidate_materialization_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_candidate_validation_and_admission import (
    build_oracle_memory_observation_candidate_admission_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_entity_resolution import (
    OracleMemoryObservationEntityResolutionInvariantError,
    build_oracle_memory_observation_entity_resolution,
    verify_oracle_memory_observation_entity_resolution,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    build_oracle_memory_ledger_integrity_replay_certification,
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
    except OracleMemoryObservationEntityResolutionInvariantError:
        return

    raise AssertionError(f"tampered OML-030 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-030 CORRECTION V3 TEST")
    print(" CERTIFIED OBSERVATION ENTITY RESOLUTION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_030",
    )

    gate_decision, intake_batch = fixture_028.build_intake_batch(root)

    materialization_batch = (
        build_oracle_memory_observation_candidate_materialization_batch(
            gate_decision=gate_decision,
            intake_batch=intake_batch,
        )
    )

    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_030",
    )

    ledger_contract = fixture_016.build_oml_015_contract(root)
    ledger = build_oracle_memory_ledger_integrity_replay_certification(
        ledger_contract=ledger_contract,
    )

    validation_batch = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger,
        candidates=materialization_batch.candidates,
    )

    admission_batch = (
        build_oracle_memory_observation_candidate_admission_batch(
            materialization_batch=materialization_batch,
            validation_batch=validation_batch,
        )
    )

    admitted_candidate_hash = next(
        item.candidate_hash
        for item in admission_batch.admissions
        if item.admission_status == "admitted"
    )

    resolution = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: (
                "BTC",
                "Bitcoin",
                "XBT",
            )
        },
    )

    assert resolution.schema_version == "OML-030"
    assert resolution.engine_id == "OML-030"
    assert resolution.upstream_schema_version == "OML-029"
    assert resolution.upstream_engine_id == "OML-029"
    assert resolution.admitted_candidate_count == 1
    assert resolution.rejected_duplicate_count == 1
    assert resolution.resolved_entity_count == 1
    assert resolution.entities[0].canonical_name == "Bitcoin"
    assert resolution.entities[0].normalized_name == "bitcoin"
    assert resolution.bindings[0].observation_lineage_verified
    assert resolution.bindings[0].candidate_lineage_verified
    assert resolution.bindings[0].admission_lineage_verified
    assert resolution.bindings[0].entity_lineage_verified
    assert resolution.bindings[0].duplicate_rejection_verified
    assert resolution.canonical_order_verified
    assert resolution.deterministic_resolution_verified
    assert resolution.observation_entity_lineage_verified
    assert resolution.duplicate_candidates_excluded
    assert resolution.entity_identity_uniqueness_verified
    assert not resolution.persistence_enabled
    assert not resolution.learning_updates_enabled
    assert not resolution.runtime_activation_enabled
    assert not resolution.publication_enabled
    assert not resolution.action_authorization_enabled
    assert not resolution.qseries_execution_enabled
    assert resolution.resolution_ready
    assert resolution.downstream_relationship_graph_authorized
    assert resolution.read_only

    replay = build_oracle_memory_observation_entity_resolution(
        admission_batch=admission_batch,
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
        aliases_by_candidate_hash={
            admitted_candidate_hash: (
                "XBT",
                "Bitcoin",
                "BTC",
            )
        },
    )

    assert replay == resolution
    assert verify_oracle_memory_observation_entity_resolution(
        resolution
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, resolved_entity_count=2)
        ),
        "entity count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(
                resolution,
                downstream_relationship_graph_authorized=False,
            )
        ),
        "relationship graph authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_entity_resolution(
            replace(resolution, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-029 admission batch consumed")
    print("[PASS] Certified OML-018 entity resolver consumed")
    print("[PASS] Only admitted observation candidate resolved")
    print("[PASS] Duplicate-rejected candidate excluded")
    print("[PASS] Stable canonical entity identity generated")
    print("[PASS] Alias normalization retained")
    print("[PASS] Observation-to-entity lineage retained")
    print("[PASS] Relationship graph continuation authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Resolution deterministic across replay")
    print("[PASS] Tampered resolutions rejected")
    print(
        "[DONE] OML-030 CORRECTION V3 CERTIFIED OBSERVATION "
        "ENTITY RESOLUTION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
