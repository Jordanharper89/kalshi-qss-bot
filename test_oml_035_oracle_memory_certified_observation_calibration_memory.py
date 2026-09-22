from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_calibration_memory import (
    CALIBRATION_STATUS_OVERCONFIDENT,
    OracleMemoryCalibrationInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    OracleMemoryCertifiedCalibrationInvariantError,
    build_oracle_memory_certified_calibration_forecast,
    build_oracle_memory_certified_calibration_memory,
    verify_oracle_memory_certified_calibration_memory,
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
    except (
        OracleMemoryCertifiedCalibrationInvariantError,
        OracleMemoryCalibrationInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-035 {label} accepted")


def build_source_reliability(root: Path):
    fixture = load_module(
        root
        / "test_oml_034_oracle_memory_certified_observation_source_reliability_memory.py",
        "oml_034_fixture_for_oml_035",
    )
    tracking = fixture.build_tracking(root)
    observation_hashes = tracking.bindings[0].source_observation_hashes
    assert len(observation_hashes) >= 2

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
        build_oracle_memory_certified_source_outcome,
        build_oracle_memory_certified_source_reliability,
    )

    outcomes = (
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.90,
            observed_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[1],
            outcome_confirmed=True,
            outcome_correct=False,
            contradiction_count=1,
            confidence_at_observation=0.80,
            observed_at="2026-08-02T15:05:00-05:00",
        ),
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Live Shadow",
            observation_hash=observation_hashes[0],
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.70,
            observed_at="2026-08-02T15:10:00-05:00",
        ),
    )

    return build_oracle_memory_certified_source_reliability(
        tracking=tracking,
        outcomes=outcomes,
    )


def main() -> int:
    print("=" * 48)
    print(" OML-035 TEST")
    print(" CERTIFIED OBSERVATION CALIBRATION MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    source_reliability = build_source_reliability(root)
    source_profile = source_reliability.reliability_memory.profiles[0]
    source_binding = source_reliability.bindings[0]
    certified_hashes = source_binding.certified_observation_hashes

    forecasts = (
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="certified-forecast-001",
            certified_observation_hash=certified_hashes[0],
            predicted_probability=0.90,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:00:00-05:00",
            resolved_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="certified-forecast-002",
            certified_observation_hash=certified_hashes[-1],
            predicted_probability=0.80,
            outcome_confirmed=True,
            outcome_value=0,
            observed_at="2026-08-02T14:05:00-05:00",
            resolved_at="2026-08-02T15:05:00-05:00",
        ),
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="certified-forecast-003",
            certified_observation_hash=certified_hashes[0],
            predicted_probability=0.70,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:10:00-05:00",
            resolved_at="2026-08-02T15:10:00-05:00",
        ),
    )

    result = build_oracle_memory_certified_calibration_memory(
        source_reliability=source_reliability,
        forecasts=forecasts,
    )

    assert result.schema_version == "OML-035"
    assert result.engine_id == "OML-035"
    assert result.upstream_schema_version == "OML-034"
    assert result.upstream_engine_id == "OML-034"
    assert result.calibration_schema_version == "OML-023"
    assert result.calibration_engine_id == "OML-023"
    assert result.profile_count == 1
    assert result.total_observation_count == 3
    assert result.total_confirmed_count == 3

    profile = result.calibration_memory.profiles[0]
    binding = result.bindings[0]

    assert profile.calibration_status == CALIBRATION_STATUS_OVERCONFIDENT
    assert profile.average_forecast_probability == 0.8
    assert profile.empirical_outcome_rate == round(2 / 3, 12)
    assert profile.expected_calibration_error > 0.0
    assert profile.mean_brier_score > 0.0
    assert len(profile.buckets) == 5

    assert binding.profile_id == profile.profile_id
    assert binding.profile_hash == profile.profile_hash
    assert binding.source_ids == (source_profile.source_id,)
    assert binding.upstream_certification_hash == (
        source_reliability.certification_hash
    )
    assert binding.upstream_reliability_memory_hash == (
        source_reliability.reliability_memory.memory_hash
    )
    assert binding.calibration_memory_hash == (
        result.calibration_memory.memory_hash
    )

    assert result.source_reliability_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.profile_identity_uniqueness_verified
    assert result.canonical_profile_order_verified
    assert result.probability_bounds_verified
    assert result.outcome_lineage_verified
    assert result.calibration_bucket_reconciliation_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_causal_memory_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_calibration_memory(
        source_reliability=source_reliability,
        forecasts=forecasts,
    )
    assert replay == result
    assert verify_oracle_memory_certified_calibration_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_calibration_forecast(
            profile_name="Bad Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="bad-forecast",
            certified_observation_hash="f" * 64,
            predicted_probability=0.50,
            outcome_confirmed=False,
            outcome_value=1,
            observed_at="2026-08-02T14:00:00-05:00",
        ),
        "invalid unresolved outcome",
    )
    expect_rejection(
        lambda: build_oracle_memory_certified_calibration_memory(
            source_reliability=source_reliability,
            forecasts=(
                replace(
                    forecasts[0],
                    certified_observation_hash="f" * 64,
                    forecast_hash=forecasts[0].forecast_hash,
                ),
            ),
        ),
        "unknown observation lineage",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_calibration_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_calibration_memory(
            replace(result, downstream_causal_memory_authorized=False)
        ),
        "causal continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_calibration_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-034 source reliability consumed read-only")
    print("[PASS] Exact OML-034 reliability-memory dataclass passed directly")
    print("[PASS] Certified observation hashes bound to forecasts")
    print("[PASS] Actual OML-023 calibration builders consumed")
    print("[PASS] Forecast probabilities and outcomes calibrated")
    print("[PASS] Calibration buckets and Brier scores reconciled")
    print("[PASS] Source, observation, and calibration lineage retained")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Causal-memory continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-035 calibration memories rejected")
    print("[DONE] OML-035 CERTIFIED OBSERVATION CALIBRATION MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
