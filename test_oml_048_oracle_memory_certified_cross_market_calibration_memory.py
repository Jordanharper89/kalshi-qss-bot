from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_calibration_memory import (
    OracleMemoryCertifiedCrossMarketCalibrationInvariantError,
    build_oracle_memory_certified_cross_market_calibration_memory,
    verify_oracle_memory_certified_cross_market_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    build_oracle_memory_certified_calibration_forecast,
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
    except OracleMemoryCertifiedCrossMarketCalibrationInvariantError:
        return
    raise AssertionError(f"tampered OML-048 {label} accepted")


def main() -> int:
    print("=" * 48)
    print(" OML-048 TEST")
    print(" CERTIFIED CROSS-MARKET CALIBRATION MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    fixture = load_module(
        root
        / "test_oml_047_oracle_memory_certified_cross_market_source_reliability.py",
        "oml_047_fixture_for_oml_048",
    )
    lifecycle = fixture.build_lifecycle(root)

    observation_hashes = tuple(sorted({
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }))

    from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
        build_oracle_memory_certified_source_outcome,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_cross_market_source_reliability import (
        build_oracle_memory_certified_cross_market_source_reliability,
    )

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Cross-Market Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=(index % 2 == 0),
            contradiction_count=0 if index % 2 == 0 else 1,
            confidence_at_observation=0.85 - (index * 0.05),
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    reliability = build_oracle_memory_certified_cross_market_source_reliability(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )

    source_profile = reliability.source_reliability.reliability_memory.profiles[0]
    source_binding = reliability.source_reliability.bindings[0]
    certified_hashes = source_binding.certified_observation_hashes

    forecasts = tuple(
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Cross-Market Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id=f"cross-market-forecast-{index + 1:03d}",
            certified_observation_hash=value,
            predicted_probability=0.80 - (index * 0.10),
            outcome_confirmed=True,
            outcome_value=1 if index % 2 == 0 else 0,
            observed_at=f"2026-08-02T16:{10 + index:02d}:00-05:00",
            resolved_at=f"2026-08-02T17:{30 + index:02d}:00-05:00",
        )
        for index, value in enumerate(certified_hashes)
    )

    result = build_oracle_memory_certified_cross_market_calibration_memory(
        reliability=reliability,
        forecasts=forecasts,
    )

    assert result.schema_version == "OML-048"
    assert result.engine_id == "OML-048"
    assert result.upstream_schema_version == "OML-047"
    assert result.upstream_engine_id == "OML-047"
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
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_cross_market_calibration_memory(
        reliability=reliability,
        forecasts=forecasts,
    )
    assert replay == result
    assert verify_oracle_memory_certified_cross_market_calibration_memory(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, downstream_causal_memory_authorized=False)
        ),
        "causal continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_cross_market_calibration_memory(
            replace(result, certification_hash="f" * 64)
        ),
        "certification hash",
    )

    print("[PASS] Certified OML-047 reliability consumed read-only")
    print("[PASS] Exact OML-034 reliability object passed directly")
    print("[PASS] Actual OML-035 calibration builder consumed")
    print("[PASS] Forecasts bound only to certified observation hashes")
    print("[PASS] Reliability and calibration lineage retained")
    print("[PASS] Probability bounds and outcomes verified")
    print("[PASS] Calibration buckets reconciled")
    print("[PASS] Causal-memory continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-048 calibration records rejected")
    print("[DONE] OML-048 CERTIFIED CROSS-MARKET CALIBRATION MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
