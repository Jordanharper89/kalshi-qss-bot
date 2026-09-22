from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory import (
    CAUSAL_STATUS_ESTABLISHED,
    OracleMemoryCausalPatternInvariantError,
    build_oracle_memory_causal_observation,
    build_oracle_memory_causal_pattern,
    build_oracle_memory_causal_pattern_memory,
    verify_oracle_memory_causal_pattern_memory,
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
    except OracleMemoryCausalPatternInvariantError:
        return

    raise AssertionError(f"tampered OML-024 {label} accepted")


def build_calibration_memory(root: Path):
    fixture = load_module(
        root / "test_oml_023_oracle_memory_calibration_memory.py",
        "oml_023_fixture_for_oml_024",
    )

    source_memory = fixture.build_source_memory(root)
    source_id = source_memory.profiles[0].source_id

    from qseries_v2.oracle_memory.oracle_memory_calibration_memory import (
        build_oracle_memory_calibration_memory,
        build_oracle_memory_calibration_observation,
    )

    observations = (
        build_oracle_memory_calibration_observation(
            forecast_id="forecast-001",
            forecast_hash="a" * 64,
            source_id=source_id,
            predicted_probability=0.80,
            outcome_confirmed=True,
            outcome_value=1,
            observed_at="2026-08-02T14:00:00-05:00",
            resolved_at="2026-08-02T15:00:00-05:00",
        ),
        build_oracle_memory_calibration_observation(
            forecast_id="forecast-002",
            forecast_hash="b" * 64,
            source_id=source_id,
            predicted_probability=0.75,
            outcome_confirmed=True,
            outcome_value=1,
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

    return build_oracle_memory_calibration_memory(
        source_memory=source_memory,
        observations_by_profile={
            "Oracle Forecast Calibration": observations,
        },
    )


def main() -> int:
    print("=" * 48)
    print(" OML-024 TEST")
    print(" CAUSAL PATTERN MEMORY")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    calibration_memory = build_calibration_memory(root)

    cause_entity_id = "1" * 64
    effect_entity_id = "2" * 64

    observations = (
        build_oracle_memory_causal_observation(
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T14:00:00-05:00",
            effect_observed_at="2026-08-02T14:30:00-05:00",
            evidence_hashes=("3" * 64, "4" * 64),
            contradicting_evidence_hashes=(),
            confidence=0.82,
            calibrated_probability=0.78,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T15:00:00-05:00",
            effect_observed_at="2026-08-02T15:20:00-05:00",
            evidence_hashes=("5" * 64,),
            contradicting_evidence_hashes=(),
            confidence=0.80,
            calibrated_probability=0.76,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
        build_oracle_memory_causal_observation(
            cause_entity_id=cause_entity_id,
            effect_entity_id=effect_entity_id,
            cause_observed_at="2026-08-02T16:00:00-05:00",
            effect_observed_at="2026-08-02T16:15:00-05:00",
            evidence_hashes=("6" * 64,),
            contradicting_evidence_hashes=("7" * 64,),
            confidence=0.77,
            calibrated_probability=0.74,
            outcome_confirmed=True,
            outcome_supported=True,
        ),
    )

    pattern = build_oracle_memory_causal_pattern(
        pattern_name="Real-world demand shift precedes market reaction",
        observations=observations,
    )

    assert pattern.causal_status == CAUSAL_STATUS_ESTABLISHED
    assert pattern.observation_count == 3
    assert pattern.confirmed_count == 3
    assert pattern.supported_count == 3
    assert pattern.contradicted_count == 0
    assert pattern.unresolved_count == 0
    assert pattern.empirical_support_rate == 1.0
    assert pattern.temporal_precedence_rate == 1.0
    assert pattern.evidence_depth == 4
    assert pattern.contradiction_depth == 1
    assert pattern.deterministic_identity_verified
    assert pattern.canonical_order_verified
    assert pattern.temporal_precedence_verified
    assert pattern.calibration_lineage_verified
    assert not pattern.persistence_authorized
    assert not pattern.learning_update_authorized
    assert not pattern.runtime_activation_authorized
    assert not pattern.publication_authorized
    assert not pattern.action_authorization_enabled
    assert not pattern.qseries_execution_authorized
    assert pattern.read_only

    memory = build_oracle_memory_causal_pattern_memory(
        calibration_memory=calibration_memory,
        patterns=(pattern,),
    )

    assert memory.schema_version == "OML-024"
    assert memory.engine_id == "OML-024"
    assert memory.upstream_schema_version == "OML-023"
    assert memory.upstream_engine_id == "OML-023"
    assert memory.pattern_count == 1
    assert memory.total_observation_count == 3
    assert memory.deterministic_identity_verified
    assert memory.canonical_pattern_order_verified
    assert memory.temporal_precedence_verified
    assert memory.evidence_lineage_verified
    assert memory.contradiction_tracking_verified
    assert memory.calibration_lineage_verified
    assert memory.outcome_reconciliation_verified
    assert not memory.persistence_enabled
    assert not memory.learning_updates_enabled
    assert not memory.runtime_activation_enabled
    assert not memory.publication_enabled
    assert not memory.action_authorization_enabled
    assert not memory.qseries_execution_enabled
    assert memory.memory_ready
    assert memory.next_certification_authorized
    assert memory.read_only

    replay = build_oracle_memory_causal_pattern_memory(
        calibration_memory=calibration_memory,
        patterns=(pattern,),
    )

    assert replay == memory
    assert verify_oracle_memory_causal_pattern_memory(memory)

    expect_rejection(
        lambda: verify_oracle_memory_causal_pattern_memory(
            replace(memory, pattern_count=2)
        ),
        "pattern count",
    )

    expect_rejection(
        lambda: verify_oracle_memory_causal_pattern_memory(
            replace(memory, persistence_enabled=True)
        ),
        "persistence state",
    )

    expect_rejection(
        lambda: verify_oracle_memory_causal_pattern_memory(
            replace(memory, qseries_execution_enabled=True)
        ),
        "Q Series execution state",
    )

    print("[PASS] Certified OML-023 calibration memory consumed")
    print("[PASS] Cause and effect identities retained")
    print("[PASS] Temporal precedence enforced")
    print("[PASS] Supporting evidence lineage retained")
    print("[PASS] Contradicting evidence tracked")
    print("[PASS] Calibrated probabilities retained")
    print("[PASS] Confirmed outcomes reconciled")
    print("[PASS] Empirical causal support rate calculated")
    print("[PASS] Established causal pattern detected")
    print("[PASS] Causal pattern memory deterministic across replay")
    print("[PASS] Persistence remained disabled")
    print("[PASS] Learning updates remained disabled")
    print("[PASS] Runtime activation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Action authorization remained disabled")
    print("[PASS] Q Series execution remained disabled")
    print("[PASS] Tampered causal memories rejected")
    print("[DONE] OML-024 CAUSAL PATTERN MEMORY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
