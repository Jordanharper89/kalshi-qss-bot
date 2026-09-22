from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory_074 import (
    OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError,
    build_oracle_memory_certified_market_behavior_calibration_memory_074,
    verify_oracle_memory_certified_market_behavior_calibration_memory_074,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    build_oracle_memory_certified_calibration_forecast,
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
    except OracleMemoryCertifiedMarketBehaviorCalibration074InvariantError:
        return
    raise AssertionError(f"tampered OML-074 {label} accepted")


def build_calibration(root: Path):
    fixture_073 = load_module(
        root
        / "test_oml_073_oracle_memory_certified_market_behavior_source_reliability.py",
        "oml_073_fixture_for_oml_074",
    )
    reliability, lifecycle, outcomes = fixture_073.build_reliability(root)

    source_profile = (
        reliability.source_reliability.reliability_memory.profiles[0]
    )
    source_binding = reliability.source_reliability.bindings[0]
    certified_hashes = source_binding.certified_observation_hashes
    assert certified_hashes

    forecasts = tuple(
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Market-Behavior Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id=f"market-behavior-forecast-{index + 1:03d}",
            certified_observation_hash=value,
            predicted_probability=max(0.05, 0.80 - (index * 0.10)),
            outcome_confirmed=True,
            outcome_value=1 if index % 2 == 0 else 0,
            observed_at=f"2026-08-04T14:{10 + index:02d}:00-05:00",
            resolved_at=f"2026-08-04T15:{30 + index:02d}:00-05:00",
        )
        for index, value in enumerate(certified_hashes)
    )

    result = build_oracle_memory_certified_market_behavior_calibration_memory_074(
        reliability=reliability,
        forecasts=forecasts,
    )
    return result, reliability, forecasts


def main() -> int:
    print("=" * 48)
    print(" OML-074 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CALIBRATION MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result, reliability, forecasts = build_calibration(root)

    assert result.schema_version == "OML-074"
    assert result.engine_id == "OML-074"
    assert result.upstream_schema_version == "OML-073"
    assert result.upstream_engine_id == "OML-073"
    assert result.calibration_schema_version == "OML-035"
    assert result.calibration_engine_id == "OML-035"
    assert result.profile_count == 1
    assert result.total_observation_count == len(forecasts)
    assert result.total_confirmed_count == len(forecasts)
    assert result.upstream_certification_hash == reliability.certification_hash
    assert result.upstream_reliability_certification_hash == (
        reliability.source_reliability.certification_hash
    )
    assert result.upstream_reliability_memory_hash == (
        reliability.source_reliability.reliability_memory.memory_hash
    )
    assert result.source_reliability_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.calibration_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.canonical_profile_order_verified
    assert result.probability_bounds_verified
    assert result.outcome_lineage_verified
    assert result.calibration_bucket_reconciliation_verified
    assert result.calibration_ready
    assert result.downstream_causal_memory_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    replay, _, _ = build_calibration(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_calibration_memory_074(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(
            replace(result, downstream_causal_memory_authorized=False)
        ),
        "causal continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_calibration_memory_074(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-073 reliability consumed read-only")
    print("[PASS] Exact OML-034 reliability object passed directly")
    print("[PASS] Actual OML-035 calibration builder consumed")
    print("[PASS] Forecasts bound only to certified observation hashes")
    print("[PASS] Reliability and calibration lineage retained")
    print("[PASS] Probability bounds and outcomes verified")
    print("[PASS] Calibration buckets reconciled")
    print("[PASS] Causal-memory continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-074 calibration objects rejected")
    print("[DONE] OML-074 CERTIFIED MARKET-BEHAVIOR CALIBRATION MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
