from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_causal_pattern_memory import (
    OracleMemoryCertifiedMarketBehaviorCausalInvariantError,
    build_oracle_memory_certified_market_behavior_causal_pattern_memory,
    verify_oracle_memory_certified_market_behavior_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    build_oracle_memory_certified_causal_observation_request,
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
    except OracleMemoryCertifiedMarketBehaviorCausalInvariantError:
        return
    raise AssertionError(f"tampered OML-062 {label} accepted")


def build_calibration(root: Path):
    fixture = load_module(
        root
        / "test_oml_060_oracle_memory_certified_market_behavior_source_reliability.py",
        "oml_060_fixture_for_oml_062",
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
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability import (
        build_oracle_memory_certified_market_behavior_source_reliability,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
        build_oracle_memory_certified_calibration_forecast,
    )
    from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_calibration_memory import (
        build_oracle_memory_certified_market_behavior_calibration_memory,
    )

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Market-Behavior Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=True,
            contradiction_count=0,
            confidence_at_observation=0.80,
            observed_at=f"2026-08-02T17:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    reliability = (
        build_oracle_memory_certified_market_behavior_source_reliability(
            lifecycle=lifecycle,
            outcomes=outcomes,
        )
    )

    profile = reliability.source_reliability.reliability_memory.profiles[0]
    certified_hashes = (
        reliability.source_reliability.bindings[0].
        certified_observation_hashes
    )

    forecasts = tuple(
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Market-Behavior Calibration",
            source_name=profile.source_name,
            source_id=profile.source_id,
            forecast_id=f"causal-forecast-{index + 1:03d}",
            certified_observation_hash=value,
            predicted_probability=0.80 - (index * 0.05),
            outcome_confirmed=True,
            outcome_value=1,
            observed_at=f"2026-08-02T16:{10 + index:02d}:00-05:00",
            resolved_at=f"2026-08-02T17:{30 + index:02d}:00-05:00",
        )
        for index, value in enumerate(certified_hashes)
    )

    calibration = (
        build_oracle_memory_certified_market_behavior_calibration_memory(
            reliability=reliability,
            forecasts=forecasts,
        )
    )
    return calibration, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-062 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    calibration, certified_hashes = build_calibration(root)

    requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Liquidity shift precedes Bitcoin repricing",
            cause_entity_id="1" * 64,
            effect_entity_id="2" * 64,
            cause_observed_at="2026-08-02T17:00:00-05:00",
            effect_observed_at="2026-08-02T17:10:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.80,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name="Liquidity shift precedes Bitcoin repricing",
            cause_entity_id="1" * 64,
            effect_entity_id="2" * 64,
            cause_observed_at="2026-08-02T18:00:00-05:00",
            effect_observed_at="2026-08-02T18:08:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.75,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    result = build_oracle_memory_certified_market_behavior_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )

    assert result.schema_version == "OML-062"
    assert result.engine_id == "OML-062"
    assert result.upstream_schema_version == "OML-061"
    assert result.upstream_engine_id == "OML-061"
    assert result.causal_schema_version == "OML-036"
    assert result.causal_engine_id == "OML-036"
    assert result.pattern_count == 1
    assert result.total_observation_count == 2
    assert result.upstream_certification_hash == calibration.certification_hash
    assert result.calibration_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_pattern_order_verified
    assert result.temporal_precedence_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.outcome_reconciliation_verified
    assert result.causal_memory_ready
    assert result.downstream_multi_hop_causal_authorized
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.read_only

    replay = build_oracle_memory_certified_market_behavior_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
        result
    )

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, downstream_multi_hop_causal_authorized=False)
        ),
        "multi-hop continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_causal_pattern_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-061 calibration consumed read-only")
    print("[PASS] Exact OML-035 calibration object passed directly")
    print("[PASS] Actual OML-036 causal builder consumed")
    print("[PASS] Requests bound only to certified observation hashes")
    print("[PASS] Temporal precedence and outcomes verified")
    print("[PASS] Calibration-to-causal lineage retained")
    print("[PASS] Multi-hop continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-062 records rejected")
    print("[DONE] OML-062 CERTIFIED MARKET-BEHAVIOR CAUSAL PATTERN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
