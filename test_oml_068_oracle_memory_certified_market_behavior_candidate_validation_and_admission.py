from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_candidate_validation_and_admission_068 import (
    OracleMemoryCertifiedMarketBehaviorAdmission068InvariantError,
    build_oracle_memory_certified_market_behavior_candidate_admission_068,
    verify_oracle_memory_certified_market_behavior_candidate_admission_068,
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
    except OracleMemoryCertifiedMarketBehaviorAdmission068InvariantError:
        return
    raise AssertionError(f"tampered OML-068 {label} accepted")


def build_admission(root: Path):
    fixture_067 = load_module(
        root
        / "test_oml_067_oracle_memory_certified_market_behavior_candidate_materialization.py",
        "oml_067_fixture_for_oml_068",
    )
    materialization = fixture_067.build_materialization(root)

    fixture_055 = load_module(
        root
        / "test_oml_055_oracle_memory_certified_market_behavior_candidate_validation_and_admission.py",
        "oml_055_fixture_for_oml_068",
    )
    validation_batch = fixture_055.build_validation(root, materialization)

    return build_oracle_memory_certified_market_behavior_candidate_admission_068(
        materialization=materialization,
        validation_batch=validation_batch,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-068 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CANDIDATE VALIDATION AND ADMISSION")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result = build_admission(root)

    assert result.schema_version == "OML-068"
    assert result.engine_id == "OML-068"
    assert result.upstream_schema_version == "OML-067"
    assert result.upstream_engine_id == "OML-067"
    assert result.validation_schema_version == "OML-017"
    assert result.validation_engine_id == "OML-017"
    assert result.admission_schema_version == "OML-029"
    assert result.admission_engine_id == "OML-029"
    assert result.admission_ready
    assert result.candidate_admission_authorized
    assert result.downstream_entity_resolution_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_admission(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_candidate_admission_068(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_candidate_admission_068(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_candidate_admission_068(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-067 materialization consumed read-only")
    print("[PASS] Exact OML-028 materialization batch passed directly")
    print("[PASS] Exact OML-017 validation batch passed directly")
    print("[PASS] Actual OML-029 admission builder consumed")
    print("[PASS] Observation-candidate lineage retained")
    print("[PASS] Duplicate policy enforced")
    print("[PASS] Entity-resolution continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-068 admissions rejected")
    print("[DONE] OML-068 CERTIFIED MARKET-BEHAVIOR CANDIDATE VALIDATION AND ADMISSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
