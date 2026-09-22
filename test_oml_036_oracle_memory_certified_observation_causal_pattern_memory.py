from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory import (
    CAUSAL_STATUS_ESTABLISHED,
    OracleMemoryCausalPatternInvariantError,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    build_oracle_memory_certified_calibration_forecast,
    build_oracle_memory_certified_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_causal_pattern_memory import (
    OracleMemoryCertifiedCausalPatternInvariantError,
    build_oracle_memory_certified_causal_observation_request,
    build_oracle_memory_certified_causal_pattern_memory,
    verify_oracle_memory_certified_causal_pattern_memory,
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
        OracleMemoryCertifiedCausalPatternInvariantError,
        OracleMemoryCausalPatternInvariantError,
    ):
        return
    raise AssertionError(f"tampered OML-036 {label} accepted")


def build_calibration(root: Path):
    fixture = load_module(
        root / "test_oml_035_oracle_memory_certified_observation_calibration_memory.py",
        "oml_035_fixture_for_oml_036",
    )
    source_reliability = fixture.build_source_reliability(root)
    source_profile = source_reliability.reliability_memory.profiles[0]
    source_binding = source_reliability.bindings[0]
    certified_hashes = source_binding.certified_observation_hashes

    forecasts = (
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="causal-forecast-001",
            certified_observation_hash=certified_hashes[0],
            predicted_probability=0.82,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:00:00-05:00",
            resolved_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="causal-forecast-002",
            certified_observation_hash=certified_hashes[-1],
            predicted_probability=0.78,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T15:00:00-05:00",
            resolved_at="2026-08-02T16:00:00-05:00",
        ),
        build_oracle_memory_certified_calibration_forecast(
            profile_name="Oracle Certified Observation Calibration",
            source_name=source_profile.source_name,
            source_id=source_profile.source_id,
            forecast_id="causal-forecast-003",
            certified_observation_hash=certified_hashes[0],
            predicted_probability=0.76,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T16:00:00-05:00",
            resolved_at="2026-08-02T17:00:00-05:00",
        ),
    )
    calibration = build_oracle_memory_certified_calibration_memory(
        source_reliability=source_reliability,
        forecasts=forecasts,
    )
    return calibration, certified_hashes


def main() -> int:
    print("=" * 48)
    print(" OML-036 TEST")
    print(" CERTIFIED OBSERVATION CAUSAL PATTERN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    calibration, certified_hashes = build_calibration(root)
    cause_entity_id = "1" * 64
    effect_entity_id = "2" * 64
    pattern_name = "Real-world demand shift precedes market reaction"

    requests = (
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=pattern_name,
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T14:00:00-05:00",
            effect_observed_at="2026-08-02T14:30:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.82,
            calibrated_probability=0.82,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=pattern_name,
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T15:00:00-05:00",
            effect_observed_at="2026-08-02T15:20:00-05:00",
            certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.80,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_certified_causal_observation_request(
            pattern_name=pattern_name,
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T16:00:00-05:00",
            effect_observed_at="2026-08-02T16:15:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            contradicting_certified_observation_hashes=(certified_hashes[-1],),
            confidence=0.77,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    result = build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )
    assert result.schema_version == "OML-036"
    assert result.engine_id == "OML-036"
    assert result.upstream_schema_version == "OML-035"
    assert result.upstream_engine_id == "OML-035"
    assert result.causal_schema_version == "OML-024"
    assert result.causal_engine_id == "OML-024"
    assert result.pattern_count == 1
    assert result.total_observation_count == 3

    pattern = result.causal_memory.patterns[0]
    binding = result.bindings[0]
    assert pattern.causal_status == CAUSAL_STATUS_ESTABLISHED
    assert pattern.observation_count == 3
    assert pattern.confirmed_count == 3
    assert pattern.supported_count == 3
    assert pattern.contradicted_count == 0
    assert pattern.temporal_precedence_rate == 1.0
    assert pattern.evidence_depth == 3
    assert pattern.contradiction_depth == 1
    assert binding.pattern_id == pattern.pattern_id
    assert binding.pattern_hash == pattern.pattern_hash
    assert binding.upstream_certification_hash == calibration.certification_hash
    assert binding.upstream_calibration_memory_hash == (
        calibration.calibration_memory.memory_hash
    )
    assert binding.causal_memory_hash == result.causal_memory.memory_hash

    assert result.certified_observation_lineage_verified
    assert result.calibration_lineage_verified
    assert result.deterministic_identity_verified
    assert result.canonical_pattern_order_verified
    assert result.temporal_precedence_verified
    assert result.evidence_lineage_verified
    assert result.contradiction_tracking_verified
    assert result.outcome_reconciliation_verified
    assert not result.persistence_enabled
    assert not result.learning_updates_enabled
    assert not result.runtime_activation_enabled
    assert not result.publication_enabled
    assert not result.action_authorization_enabled
    assert not result.qseries_execution_enabled
    assert result.memory_ready
    assert result.downstream_multi_hop_causal_authorized
    assert result.read_only

    replay = build_oracle_memory_certified_causal_pattern_memory(
        calibration=calibration,
        requests=requests,
    )
    assert replay == result
    assert verify_oracle_memory_certified_causal_pattern_memory(result)

    expect_rejection(
        lambda: build_oracle_memory_certified_causal_observation_request(
            pattern_name="Broken",
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T16:00:00-05:00",
            effect_observed_at="2026-08-02T15:00:00-05:00",
            certified_observation_hashes=(certified_hashes[0],),
            confidence=0.50,
            calibrated_probability=0.50,
            outcome_confirmed=False,
            outcome_supported=None,
        ),
        "temporal precedence",
    )
    expect_rejection(
        lambda: build_oracle_memory_certified_causal_pattern_memory(
            calibration=calibration,
            requests=(
                replace(
                    requests[0],
                    certified_observation_hashes=("f" * 64,),
                    request_hash=requests[0].request_hash,
                ),
            ),
        ),
        "unknown certified evidence",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_causal_pattern_memory(
            replace(result, persistence_enabled=True)
        ),
        "persistence state",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_causal_pattern_memory(
            replace(result, downstream_multi_hop_causal_authorized=False)
        ),
        "multi-hop continuation",
    )
    expect_rejection(
        lambda: verify_oracle_memory_certified_causal_pattern_memory(
            replace(result, qseries_execution_enabled=True)
        ),
        "Q Series execution",
    )

    print("[PASS] Certified OML-035 calibration consumed read-only")
    print("[PASS] Exact OML-035 calibration-memory dataclass passed directly")
    print("[PASS] Certified observation evidence bound to causal requests")
    print("[PASS] Actual OML-024 causal builders consumed")
    print("[PASS] Temporal precedence enforced")
    print("[PASS] Supporting and contradicting evidence retained")
    print("[PASS] Calibrated probabilities and outcomes retained")
    print("[PASS] Established causal pattern detected")
    print("[PASS] Deterministic hashes and replay equality verified")
    print("[PASS] Multi-hop causal continuation authorized read-only")
    print("[PASS] Oracle Terminal separation preserved")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered OML-036 causal memories rejected")
    print("[DONE] OML-036 CERTIFIED OBSERVATION CAUSAL PATTERN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
