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
    ADMISSION_STATUS_ADMITTED,
    ADMISSION_STATUS_REJECTED_DUPLICATE,
    OracleMemoryObservationCandidateAdmissionInvariantError,
    build_oracle_memory_observation_candidate_admission_batch,
    verify_oracle_memory_observation_candidate_admission_batch,
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
    except OracleMemoryObservationCandidateAdmissionInvariantError:
        return

    raise AssertionError(f"tampered OML-029 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-029 CORRECTION V2 TEST")
    print(" CERTIFIED OBSERVATION CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)

    root = Path(__file__).resolve().parent

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_029",
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
        "oml_016_fixture_for_oml_029",
    )

    ledger_contract = fixture_016.build_oml_015_contract(root)

    from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
        build_oracle_memory_ledger_integrity_replay_certification,
    )

    ledger_certification = (
        build_oracle_memory_ledger_integrity_replay_certification(
            ledger_contract=ledger_contract,
        )
    )

    validation_batch = build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger_certification,
        candidates=materialization_batch.candidates,
    )

    batch = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
    )

    assert batch.schema_version == "OML-029"
    assert batch.engine_id == "OML-029"
    assert batch.upstream_schema_version == "OML-028"
    assert batch.upstream_engine_id == "OML-028"
    assert batch.admission_count == 2
    assert batch.admitted_count == 1
    assert batch.rejected_duplicate_count == 1

    statuses = tuple(
        item.admission_status for item in batch.admissions
    )

    assert ADMISSION_STATUS_ADMITTED in statuses
    assert ADMISSION_STATUS_REJECTED_DUPLICATE in statuses
    assert batch.canonical_order_verified
    assert batch.deterministic_admission_verified
    assert batch.materialization_lineage_verified
    assert batch.validation_lineage_verified
    assert batch.duplicate_policy_verified
    assert not batch.persistence_enabled
    assert not batch.learning_updates_enabled
    assert not batch.runtime_activation_enabled
    assert not batch.publication_enabled
    assert not batch.action_authorization_enabled
    assert not batch.qseries_execution_enabled
    assert batch.admission_ready
    assert batch.downstream_entity_resolution_authorized
    assert batch.read_only

    replay = build_oracle_memory_observation_candidate_admission_batch(
        materialization_batch=materialization_batch,
        validation_batch=validation_batch,
    )

    assert replay == batch
    assert verify_oracle_memory_observation_candidate_admission_batch(
        batch
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, admitted_count=2)
        ),
        "admission count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(
                batch,
                downstream_entity_resolution_authorized=False,
            )
        ),
        "entity-resolution authorization",
    )

    expect_rejection(
        lambda: verify_oracle_memory_observation_candidate_admission_batch(
            replace(batch, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-028 materialization consumed")
    print("[PASS] Certified OML-017 validation engine consumed")
    print("[PASS] Observation-candidate lineage retained")
    print("[PASS] Validation-result lineage retained")
    print("[PASS] Unique candidate admitted")
    print("[PASS] Duplicate candidate rejected")
    print("[PASS] Evidence lineage retained")
    print("[PASS] Downstream entity resolution authorized read-only")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Admission deterministic across replay")
    print("[PASS] Tampered admission batches rejected")
    print(
        "[DONE] OML-029 CORRECTION V2 CERTIFIED OBSERVATION "
        "CANDIDATE VALIDATION AND ADMISSION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
