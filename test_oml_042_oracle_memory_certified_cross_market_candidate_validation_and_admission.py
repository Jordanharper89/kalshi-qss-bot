from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    build_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_validation_and_admission import (
    OracleMemoryCertifiedCrossMarketAdmissionInvariantError,
    build_oracle_memory_certified_cross_market_candidate_admission,
    verify_oracle_memory_certified_cross_market_candidate_admission,
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
    except OracleMemoryCertifiedCrossMarketAdmissionInvariantError:
        return
    raise AssertionError(f"tampered OML-042 {label} accepted")


def build_materialization(root: Path):
    fixture_040 = load_module(
        root
        / "test_oml_040_oracle_memory_certified_cross_market_candidate_materialization_authorization_gate.py",
        "oml_040_fixture_for_oml_042",
    )
    bridge = fixture_040.build_bridge(root)

    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization_authorization_gate import (
        build_oracle_memory_cross_market_materialization_authorization_decision,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_candidate_materialization import (
        build_oracle_memory_certified_cross_market_candidate_materialization,
    )

    authorization = (
        build_oracle_memory_cross_market_materialization_authorization_decision(
            bridge=bridge,
        )
    )

    fixture_028 = load_module(
        root
        / "test_oml_028_oracle_memory_certified_observation_candidate_materialization.py",
        "oml_028_fixture_for_oml_042",
    )
    registry_gate_decision, _ = fixture_028.build_intake_batch(root)

    return build_oracle_memory_certified_cross_market_candidate_materialization(
        authorization=authorization,
        bridge=bridge,
        registry_gate_decision=registry_gate_decision,
    )


def build_validation(root: Path, materialization):
    fixture_016 = load_module(
        root
        / "test_oml_016_oracle_memory_ledger_integrity_and_replay_certification.py",
        "oml_016_fixture_for_oml_042",
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

    return build_oracle_memory_candidate_validation_batch(
        ledger_certification=ledger_certification,
        candidates=materialization.materialization_batch.candidates,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-042 TEST")
    print(" CERTIFIED CROSS-MARKET CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    materialization = build_materialization(root)
    validation_batch = build_validation(root, materialization)

    result = build_oracle_memory_certified_cross_market_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )

    assert result.schema_version == "OML-042"
    assert result.engine_id == "OML-042"
    assert result.upstream_schema_version == "OML-041"
    assert result.upstream_engine_id == "OML-041"
    assert result.validation_schema_version == "OML-017"
    assert result.validation_engine_id == "OML-017"
    assert result.admission_schema_version == "OML-029"
    assert result.admission_engine_id == "OML-029"
    assert result.upstream_certification_hash == materialization.certification_hash
    assert result.upstream_materialization_batch_hash == (
        materialization.materialization_batch.batch_hash
    )
    assert result.validation_batch_hash == validation_batch.batch_hash
    assert result.candidate_count == validation_batch.candidate_count
    assert result.unique_candidate_count == validation_batch.unique_candidate_count
    assert result.duplicate_candidate_count == (
        validation_batch.duplicate_candidate_count
    )
    assert result.admission_count == result.admission_batch.admission_count
    assert result.admitted_count == result.admission_batch.admitted_count
    assert result.rejected_duplicate_count == (
        result.admission_batch.rejected_duplicate_count
    )
    assert result.candidate_admission_authorized
    assert result.admission_ready
    assert result.downstream_entity_resolution_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_candidate_admission(
        materialization=materialization,
        validation_batch=validation_batch,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_candidate_admission(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, downstream_entity_resolution_authorized=False)
        ),
        "entity-resolution continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_candidate_admission(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-041 materialization consumed read-only")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-029 admission builder consumed")
    print("[PASS] Observation-candidate lineage retained")
    print("[PASS] Validation-result lineage retained")
    print("[PASS] Duplicate policy enforced")
    print("[PASS] Candidate admission authorized read-only")
    print("[PASS] Entity-resolution continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-042 admissions rejected")
    print(
        "[DONE] OML-042 CERTIFIED CROSS-MARKET "
        "CANDIDATE VALIDATION AND ADMISSION PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
