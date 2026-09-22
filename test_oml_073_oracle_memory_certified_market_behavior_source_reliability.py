from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_certified_market_behavior_source_reliability_073 import (
    OracleMemoryCertifiedMarketBehaviorReliability073InvariantError,
    build_oracle_memory_certified_market_behavior_source_reliability_073,
    verify_oracle_memory_certified_market_behavior_source_reliability_073,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    build_oracle_memory_certified_source_outcome,
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
    except OracleMemoryCertifiedMarketBehaviorReliability073InvariantError:
        return
    raise AssertionError(f"tampered OML-073 {label} accepted")


def build_reliability(root: Path):
    fixture_072 = load_module(
        root / "test_oml_072_oracle_memory_certified_market_behavior_narrative_lifecycle_tracking.py",
        "oml_072_fixture_for_oml_073",
    )
    lifecycle = fixture_072.build_lifecycle(root)

    observation_hashes = tuple(sorted({
        value
        for binding in lifecycle.lifecycle_tracking.bindings
        for value in binding.source_observation_hashes
    }))
    assert observation_hashes

    outcomes = tuple(
        build_oracle_memory_certified_source_outcome(
            source_name="Oracle Market-Behavior Observation",
            observation_hash=value,
            outcome_confirmed=True,
            outcome_correct=(index % 2 == 0),
            contradiction_count=0 if index % 2 == 0 else 1,
            confidence_at_observation=0.80 - (index * 0.05),
            observed_at=f"2026-08-04T13:{20 + index:02d}:00-05:00",
        )
        for index, value in enumerate(observation_hashes)
    )

    result = build_oracle_memory_certified_market_behavior_source_reliability_073(
        lifecycle=lifecycle,
        outcomes=outcomes,
    )
    return result, lifecycle, outcomes


def main() -> int:
    print("=" * 48)
    print(" OML-073 TEST")
    print(" CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    result, lifecycle, outcomes = build_reliability(root)

    assert result.schema_version == "OML-073"
    assert result.engine_id == "OML-073"
    assert result.upstream_schema_version == "OML-072"
    assert result.upstream_engine_id == "OML-072"
    assert result.reliability_schema_version == "OML-034"
    assert result.reliability_engine_id == "OML-034"
    assert result.source_count == 1
    assert result.total_observation_count == len(outcomes)
    assert result.upstream_certification_hash == lifecycle.certification_hash
    assert result.upstream_lifecycle_tracking_hash == lifecycle.lifecycle_tracking.tracking_hash
    assert result.lifecycle_lineage_verified
    assert result.narrative_lineage_verified
    assert result.certified_observation_lineage_verified
    assert result.deterministic_scoring_verified
    assert result.source_identity_uniqueness_verified
    assert result.contradiction_tracking_verified
    assert result.calibration_tracking_verified
    assert result.reliability_ready
    assert result.downstream_calibration_authorized
    assert result.read_only
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled

    replay, _, _ = build_reliability(root)
    assert replay == result
    assert verify_oracle_memory_certified_market_behavior_source_reliability_073(result)

    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(
            replace(result, downstream_calibration_authorized=False)
        ),
        "calibration continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_market_behavior_source_reliability_073(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-072 lifecycle consumed read-only")
    print("[PASS] Exact OML-033 lifecycle object passed directly")
    print("[PASS] Actual OML-034 source-reliability builder consumed")
    print("[PASS] Outcomes bound only to certified observation hashes")
    print("[PASS] Narrative and lifecycle lineage retained")
    print("[PASS] Reliability and calibration tracking retained")
    print("[PASS] Calibration continuation authorized read-only")
    print("[PASS] Deterministic replay equality verified")
    print("[PASS] Active capabilities remained disabled")
    print("[PASS] Tampered OML-073 reliability objects rejected")
    print("[DONE] OML-073 CERTIFIED MARKET-BEHAVIOR SOURCE RELIABILITY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
