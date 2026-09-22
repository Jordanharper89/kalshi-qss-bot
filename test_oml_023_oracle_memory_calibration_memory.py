from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_calibration_memory import (
    CALIBRATION_STATUS_OVERCONFIDENT,
    OracleMemoryCalibrationInvariantError,
    build_oracle_memory_calibration_memory,
    build_oracle_memory_calibration_observation,
    verify_oracle_memory_calibration_memory,
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
    except OracleMemoryCalibrationInvariantError:
        return

    raise AssertionError(f"tampered OML-023 {label} accepted")


def build_source_memory(root: Path):
    fixture = load_module(
        root
        / "test_oml_022_oracle_memory_source_reliability_memory.py",
        "oml_022_fixture_for_oml_023",
    )

    lifecycle_memory = fixture.build_lifecycle_memory(root)

    from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
        build_oracle_memory_source_observation,
        build_oracle_memory_source_reliability_memory,
    )

    observations = (
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="1" * 64,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.80,
            observed_at="2026-08-02T14:40:00-05:00",
        ),
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="2" * 64,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.75,
            observed_at="2026-08-02T14:45:00-05:00",
        ),
        build_oracle_memory_source_observation(
            source_name="Source Alpha",
            observation_hash="3" * 64,
            outcome_confirmed=True,
            outcome_correct=False,
            contradiction_count=1,
            confidence_at_observation=0.70,
            observed_at="2026-08-02T14:50:00-05:00",
        ),
    )

    return build_oracle_memory_source_reliability_memory(
        lifecycle_memory=lifecycle_memory,
        observations_by_source={
            "Source Alpha": observations,
        },
    )


def main() -> int:
    print("=" * 48)
    print(" OML-023 TEST")
    print(" CALIBRATION MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    source_memory = build_source_memory(root)
    source_id = source_memory.profiles[0].source_id

    observations = (
        build_oracle_memory_calibration_observation(
            forecast_id="forecast-001",
            forecast_hash="a" * 64,
            source_id=source_id,
            predicted_probability=0.90,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:00:00-05:00",
            resolved_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_calibration_observation(
            forecast_id="forecast-002",
            forecast_hash="b" * 64,
            source_id=source_id,
            predicted_probability=0.80,
            outcome_confirmed=True,
            outcome_value=0,
            observed_at="2026-08-02T14:05:00-05:00",
            resolved_at="2026-08-02T15:05:00-05:00",
        ),
        build_oracle_memory_calibration_observation(
            forecast_id="forecast-003",
            forecast_hash="c" * 64,
            source_id=source_id,
            predicted_probability=0.70,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:10:00-05:00",
            resolved_at="2026-08-02T15:10:00-05:00",
        ),
    )

    memory = build_oracle_memory_calibration_memory(
        source_memory=source_memory,
        observations_by_profile={
            "Oracle Forecast Calibration": observations,
        },
    )

    assert memory.schema_version == "OML-023"
    assert memory.engine_id == "OML-023"
    assert memory.upstream_schema_version == "OML-022"
    assert memory.upstream_engine_id == "OML-022"
    assert memory.profile_count == 1
    assert memory.total_observation_count == 3
    assert memory.total_confirmed_count == 3

    profile = memory.profiles[0]

    assert profile.calibration_status == CALIBRATION_STATUS_OVERCONFIDENT
    assert profile.observation_count == 3
    assert profile.confirmed_count == 3
    assert profile.unresolved_count == 0
    assert profile.average_forecast_probability == 0.8
    assert profile.empirical_outcome_rate == round(2 / 3, 12)
    assert profile.overconfidence_gap > 0.0
    assert profile.underconfidence_gap == 0.0
    assert profile.expected_calibration_error > 0.0
    assert profile.mean_brier_score > 0.0
    assert len(profile.buckets) == 5
    assert profile.bucket_reconciliation_verified
    assert profile.deterministic_scoring_verified
    assert profile.canonical_order_verified
    assert profile.outcome_lineage_verified
    assert not profile.persistence_authorized
    assert not profile.learning_update_authorized
    assert not profile.runtime_activation_authorized
    assert not profile.publication_authorized
    assert not profile.action_authorization_enabled
    assert not profile.qseries_execution_authorized
    assert profile.read_only

    assert memory.deterministic_scoring_verified
    assert memory.profile_identity_uniqueness_verified
    assert memory.canonical_profile_order_verified
    assert memory.probability_bounds_verified
    assert memory.outcome_lineage_verified
    assert memory.calibration_bucket_reconciliation_verified
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_calibration_memory(
        source_memory=source_memory,
        observations_by_profile={
            "Oracle Forecast Calibration": observations,
        },
    )

    assert replay == memory
    assert verify_oracle_memory_calibration_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_calibration_memory(
            replace(memory, profile_count=2)
        ),
        "profile count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_calibration_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_calibration_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-022 source reliability memory consumed")
    print("[PASS] Forecast probabilities canonicalized")
    print("[PASS] Confirmed outcomes retained")
    print("[PASS] Absolute forecast error calculated")
    print("[PASS] Brier score calculated")
    print("[PASS] Calibration buckets reconciled")
    print("[PASS] Expected calibration error calculated")
    print("[PASS] Overconfidence detected")
    print("[PASS] Calibration memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered calibration memories rejected")
    print("[DONE] OML-023 CALIBRATION MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
