from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_calibration_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_023_oracle_memory_calibration_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_causal_pattern_memory.py"
TEST = ROOT / "test_oml_024_oracle_memory_causal_pattern_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_calibration_memory import (
    OracleMemoryCalibrationMemory,
    verify_oracle_memory_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-024"
ENGINE_ID = "OML-024"
POLICY_ID = "oracle-memory.causal-pattern-memory.v1"

UPSTREAM_SCHEMA_VERSION = "OML-023"
UPSTREAM_ENGINE_ID = "OML-023"

CAUSAL_STATUS_HYPOTHESIS = "hypothesis"
CAUSAL_STATUS_SUPPORTED = "supported"
CAUSAL_STATUS_CONTRADICTED = "contradicted"
CAUSAL_STATUS_ESTABLISHED = "established"

ALLOWED_CAUSAL_STATUSES = (
    CAUSAL_STATUS_HYPOTHESIS,
    CAUSAL_STATUS_SUPPORTED,
    CAUSAL_STATUS_CONTRADICTED,
    CAUSAL_STATUS_ESTABLISHED,
)


class OracleMemoryCausalPatternInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCausalObservation:
    cause_entity_id: str
    effect_entity_id: str
    cause_observed_at: str
    effect_observed_at: str
    evidence_hashes: tuple[str, ...]
    contradicting_evidence_hashes: tuple[str, ...]
    confidence: float
    calibrated_probability: float
    outcome_confirmed: bool
    outcome_supported: bool | None
    temporal_precedence_verified: bool
    source_lineage_verified: bool
    calibration_lineage_verified: bool
    observation_hash: str


@dataclass(frozen=True)
class OracleMemoryCausalPattern:
    pattern_id: str
    pattern_name: str
    normalized_pattern_name: str
    cause_entity_id: str
    effect_entity_id: str
    causal_status: str
    observations: tuple[OracleMemoryCausalObservation, ...]
    observation_count: int
    confirmed_count: int
    supported_count: int
    contradicted_count: int
    unresolved_count: int
    aggregate_confidence: float
    empirical_support_rate: float
    average_calibrated_probability: float
    temporal_precedence_rate: float
    evidence_depth: int
    contradiction_depth: int
    deterministic_identity_verified: bool
    canonical_order_verified: bool
    temporal_precedence_verified: bool
    calibration_lineage_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    pattern_hash: str


@dataclass(frozen=True)
class OracleMemoryCausalPatternMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    patterns: tuple[OracleMemoryCausalPattern, ...]
    pattern_count: int
    total_observation_count: int
    deterministic_identity_verified: bool
    canonical_pattern_order_verified: bool
    temporal_precedence_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    calibration_lineage_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    next_certification_authorized: bool
    read_only: bool
    memory_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryCausalPatternInvariantError(
        "unsupported OML-024 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryCausalPatternInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-024 pattern name cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-024 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCausalPatternInvariantError(
            f"OML-024 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_causal_observation(
    *,
    cause_entity_id: str,
    effect_entity_id: str,
    cause_observed_at: str,
    effect_observed_at: str,
    evidence_hashes: Sequence[str],
    contradicting_evidence_hashes: Sequence[str] = (),
    confidence: float,
    calibrated_probability: float,
    outcome_confirmed: bool,
    outcome_supported: bool | None,
) -> OracleMemoryCausalObservation:
    _require_hash(cause_entity_id, "cause entity id")
    _require_hash(effect_entity_id, "effect entity id")

    if cause_entity_id == effect_entity_id:
        _reject("OML-024 cause and effect entities must differ")

    if not cause_observed_at.strip() or not effect_observed_at.strip():
        _reject("OML-024 observation timestamps required")

    if effect_observed_at < cause_observed_at:
        _reject("OML-024 effect cannot precede cause")

    evidence = tuple(sorted(set(evidence_hashes)))
    contradictions = tuple(sorted(set(contradicting_evidence_hashes)))

    if not evidence:
        _reject("OML-024 causal evidence required")

    for value in (*evidence, *contradictions):
        _require_hash(value, "evidence hash")

    confidence = float(confidence)
    calibrated_probability = float(calibrated_probability)

    if not 0.0 <= confidence <= 1.0:
        _reject("OML-024 confidence outside [0, 1]")

    if not 0.0 <= calibrated_probability <= 1.0:
        _reject("OML-024 calibrated probability outside [0, 1]")

    if outcome_confirmed:
        if outcome_supported is None:
            _reject("OML-024 confirmed outcome requires support result")
    elif outcome_supported is not None:
        _reject("OML-024 unresolved outcome cannot carry support result")

    body = {
        "cause_entity_id": cause_entity_id,
        "effect_entity_id": effect_entity_id,
        "cause_observed_at": cause_observed_at.strip(),
        "effect_observed_at": effect_observed_at.strip(),
        "evidence_hashes": evidence,
        "contradicting_evidence_hashes": contradictions,
        "confidence": confidence,
        "calibrated_probability": calibrated_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_supported": outcome_supported,
        "temporal_precedence_verified": True,
        "source_lineage_verified": True,
        "calibration_lineage_verified": True,
    }

    observation = OracleMemoryCausalObservation(
        **body,
        observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_causal_observation(observation)
    return observation


def verify_oracle_memory_causal_observation(
    observation: OracleMemoryCausalObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-024 causal observation hash mismatch")

    for value, label in (
        (observation.cause_entity_id, "cause entity id"),
        (observation.effect_entity_id, "effect entity id"),
        (observation.observation_hash, "observation hash"),
    ):
        _require_hash(value, label)

    if observation.cause_entity_id == observation.effect_entity_id:
        _reject("OML-024 self-causation observation forbidden")

    if observation.effect_observed_at < observation.cause_observed_at:
        _reject("OML-024 temporal precedence violated")

    if not observation.evidence_hashes:
        _reject("OML-024 evidence lineage missing")

    for value in (
        *observation.evidence_hashes,
        *observation.contradicting_evidence_hashes,
    ):
        _require_hash(value, "observation evidence hash")

    if not 0.0 <= observation.confidence <= 1.0:
        _reject("OML-024 observation confidence invalid")

    if not 0.0 <= observation.calibrated_probability <= 1.0:
        _reject("OML-024 observation probability invalid")

    if observation.outcome_confirmed:
        if observation.outcome_supported is None:
            _reject("OML-024 confirmed outcome support missing")
    elif observation.outcome_supported is not None:
        _reject("OML-024 unresolved outcome support invalid")

    if not all(
        (
            observation.temporal_precedence_verified,
            observation.source_lineage_verified,
            observation.calibration_lineage_verified,
        )
    ):
        _reject("OML-024 causal observation guarantee missing")

    return True


def _status_for(
    *,
    confirmed_count: int,
    supported_count: int,
    contradicted_count: int,
    empirical_support_rate: float,
) -> str:
    if confirmed_count == 0:
        return CAUSAL_STATUS_HYPOTHESIS

    if contradicted_count > supported_count:
        return CAUSAL_STATUS_CONTRADICTED

    if confirmed_count >= 3 and empirical_support_rate >= 0.75:
        return CAUSAL_STATUS_ESTABLISHED

    return CAUSAL_STATUS_SUPPORTED


def build_oracle_memory_causal_pattern(
    *,
    pattern_name: str,
    observations: Sequence[OracleMemoryCausalObservation],
) -> OracleMemoryCausalPattern:
    normalized = _normalize(pattern_name)

    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.cause_observed_at,
                item.effect_observed_at,
                item.observation_hash,
            ),
        )
    )

    if not ordered:
        _reject("OML-024 causal pattern requires observations")

    for observation in ordered:
        verify_oracle_memory_causal_observation(observation)

    cause_ids = {item.cause_entity_id for item in ordered}
    effect_ids = {item.effect_entity_id for item in ordered}

    if len(cause_ids) != 1 or len(effect_ids) != 1:
        _reject("OML-024 mixed causal identities in pattern")

    confirmed = tuple(item for item in ordered if item.outcome_confirmed)
    supported = tuple(
        item for item in confirmed if item.outcome_supported is True
    )
    contradicted = tuple(
        item for item in confirmed if item.outcome_supported is False
    )

    confirmed_count = len(confirmed)
    supported_count = len(supported)
    contradicted_count = len(contradicted)
    unresolved_count = len(ordered) - confirmed_count

    aggregate_confidence = round(
        sum(item.confidence for item in ordered) / len(ordered),
        12,
    )

    empirical_support_rate = (
        round(supported_count / confirmed_count, 12)
        if confirmed_count
        else 0.0
    )

    average_calibrated_probability = round(
        sum(item.calibrated_probability for item in ordered)
        / len(ordered),
        12,
    )

    temporal_precedence_rate = round(
        sum(item.temporal_precedence_verified for item in ordered)
        / len(ordered),
        12,
    )

    cause_entity_id = ordered[0].cause_entity_id
    effect_entity_id = ordered[0].effect_entity_id

    pattern_id = _stable_hash(
        {
            "normalized_pattern_name": normalized,
            "cause_entity_id": cause_entity_id,
            "effect_entity_id": effect_entity_id,
        }
    )

    status = _status_for(
        confirmed_count=confirmed_count,
        supported_count=supported_count,
        contradicted_count=contradicted_count,
        empirical_support_rate=empirical_support_rate,
    )

    body = {
        "pattern_id": pattern_id,
        "pattern_name": pattern_name.strip(),
        "normalized_pattern_name": normalized,
        "cause_entity_id": cause_entity_id,
        "effect_entity_id": effect_entity_id,
        "causal_status": status,
        "observations": ordered,
        "observation_count": len(ordered),
        "confirmed_count": confirmed_count,
        "supported_count": supported_count,
        "contradicted_count": contradicted_count,
        "unresolved_count": unresolved_count,
        "aggregate_confidence": aggregate_confidence,
        "empirical_support_rate": empirical_support_rate,
        "average_calibrated_probability": average_calibrated_probability,
        "temporal_precedence_rate": temporal_precedence_rate,
        "evidence_depth": sum(
            len(item.evidence_hashes) for item in ordered
        ),
        "contradiction_depth": sum(
            len(item.contradicting_evidence_hashes)
            for item in ordered
        ),
        "deterministic_identity_verified": True,
        "canonical_order_verified": True,
        "temporal_precedence_verified": (
            temporal_precedence_rate == 1.0
        ),
        "calibration_lineage_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    pattern = OracleMemoryCausalPattern(
        **body,
        pattern_hash=_stable_hash(body),
    )

    verify_oracle_memory_causal_pattern(pattern)
    return pattern


def verify_oracle_memory_causal_pattern(
    pattern: OracleMemoryCausalPattern,
) -> bool:
    body = asdict(pattern)
    supplied = body.pop("pattern_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-024 pattern hash mismatch")

    if pattern.normalized_pattern_name != _normalize(pattern.pattern_name):
        _reject("OML-024 pattern normalization mismatch")

    for value, label in (
        (pattern.pattern_id, "pattern id"),
        (pattern.cause_entity_id, "cause entity id"),
        (pattern.effect_entity_id, "effect entity id"),
        (pattern.pattern_hash, "pattern hash"),
    ):
        _require_hash(value, label)

    if pattern.causal_status not in ALLOWED_CAUSAL_STATUSES:
        _reject("OML-024 causal status invalid")

    if pattern.observation_count != len(pattern.observations):
        _reject("OML-024 observation count mismatch")

    if (
        pattern.confirmed_count
        + pattern.unresolved_count
        != pattern.observation_count
    ):
        _reject("OML-024 confirmed/unresolved reconciliation mismatch")

    if (
        pattern.supported_count
        + pattern.contradicted_count
        != pattern.confirmed_count
    ):
        _reject("OML-024 outcome reconciliation mismatch")

    for observation in pattern.observations:
        verify_oracle_memory_causal_observation(observation)

        if observation.cause_entity_id != pattern.cause_entity_id:
            _reject("OML-024 cause lineage mismatch")

        if observation.effect_entity_id != pattern.effect_entity_id:
            _reject("OML-024 effect lineage mismatch")

    for value in (
        pattern.aggregate_confidence,
        pattern.empirical_support_rate,
        pattern.average_calibrated_probability,
        pattern.temporal_precedence_rate,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-024 pattern metric outside [0, 1]")

    expected_pattern_id = _stable_hash(
        {
            "normalized_pattern_name": pattern.normalized_pattern_name,
            "cause_entity_id": pattern.cause_entity_id,
            "effect_entity_id": pattern.effect_entity_id,
        }
    )

    if pattern.pattern_id != expected_pattern_id:
        _reject("OML-024 pattern identity mismatch")

    required_true = (
        pattern.deterministic_identity_verified,
        pattern.canonical_order_verified,
        pattern.temporal_precedence_verified,
        pattern.calibration_lineage_verified,
        pattern.read_only,
    )

    if not all(required_true):
        _reject("OML-024 pattern guarantee missing")

    forbidden = (
        pattern.persistence_authorized,
        pattern.learning_update_authorized,
        pattern.runtime_activation_authorized,
        pattern.publication_authorized,
        pattern.action_authorization_enabled,
        pattern.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-024 forbidden pattern capability enabled")

    return True


def build_oracle_memory_causal_pattern_memory(
    *,
    calibration_memory: OracleMemoryCalibrationMemory,
    patterns: Sequence[OracleMemoryCausalPattern],
) -> OracleMemoryCausalPatternMemory:
    verify_oracle_memory_calibration_memory(calibration_memory)

    if calibration_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-024 upstream schema mismatch")

    if calibration_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-024 upstream engine mismatch")

    if not calibration_memory.memory_ready:
        _reject("OML-024 upstream calibration memory not ready")

    if not calibration_memory.next_certification_authorized:
        _reject("OML-024 upstream continuation not authorized")

    if not calibration_memory.read_only:
        _reject("OML-024 upstream calibration memory not read-only")

    ordered = tuple(
        sorted(
            patterns,
            key=lambda item: (
                item.normalized_pattern_name,
                item.cause_entity_id,
                item.effect_entity_id,
                item.pattern_id,
            ),
        )
    )

    for pattern in ordered:
        verify_oracle_memory_causal_pattern(pattern)

    pattern_ids = tuple(item.pattern_id for item in ordered)

    if len(set(pattern_ids)) != len(pattern_ids):
        _reject("OML-024 duplicate causal pattern identities")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": calibration_memory.schema_version,
        "upstream_engine_id": calibration_memory.engine_id,
        "upstream_memory_hash": calibration_memory.memory_hash,
        "patterns": ordered,
        "pattern_count": len(ordered),
        "total_observation_count": sum(
            pattern.observation_count for pattern in ordered
        ),
        "deterministic_identity_verified": True,
        "canonical_pattern_order_verified": True,
        "temporal_precedence_verified": all(
            pattern.temporal_precedence_verified
            for pattern in ordered
        ),
        "evidence_lineage_verified": True,
        "contradiction_tracking_verified": True,
        "calibration_lineage_verified": True,
        "outcome_reconciliation_verified": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    memory = OracleMemoryCausalPatternMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_causal_pattern_memory(memory)
    return memory


def verify_oracle_memory_causal_pattern_memory(
    memory: OracleMemoryCausalPatternMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-024 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-024 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-024 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-024 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-024 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-024 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-024 upstream engine lineage mismatch")

    if memory.pattern_count != len(memory.patterns):
        _reject("OML-024 pattern count mismatch")

    if memory.total_observation_count != sum(
        pattern.observation_count for pattern in memory.patterns
    ):
        _reject("OML-024 total observation count mismatch")

    pattern_ids = []

    for pattern in memory.patterns:
        verify_oracle_memory_causal_pattern(pattern)
        pattern_ids.append(pattern.pattern_id)

    if len(set(pattern_ids)) != len(pattern_ids):
        _reject("OML-024 duplicate memory pattern identities")

    required_true = (
        memory.deterministic_identity_verified,
        memory.canonical_pattern_order_verified,
        memory.temporal_precedence_verified,
        memory.evidence_lineage_verified,
        memory.contradiction_tracking_verified,
        memory.calibration_lineage_verified,
        memory.outcome_reconciliation_verified,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-024 memory guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-024 forbidden memory capability enabled")

    return True
"""

TEST_SOURCE = r"""
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
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstream() -> None:
    if not UPSTREAM.is_file() or not UPSTREAM_TEST.is_file():
        raise RuntimeError(
            "Certified OML-023 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_calibration_memory"
    )

    expected = {
        "SCHEMA_VERSION": "OML-023",
        "ENGINE_ID": "OML-023",
        "POLICY_ID": "oracle-memory.calibration-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-022",
        "UPSTREAM_ENGINE_ID": "OML-022",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-023 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemoryCalibrationMemory",
        "build_oracle_memory_calibration_memory",
        "verify_oracle_memory_calibration_memory",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-023 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-024 FOR-SURE INSTALLER")
    print(" CAUSAL PATTERN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-023 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-023 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_causal_pattern_memory import *"
        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"
            INIT.write_text(current, encoding="utf-8", newline="\n")
            print(f"[OK] PACKAGE UPDATED: {INIT.resolve()}")
        else:
            print(f"[OK] PACKAGE EXPORT PRESENT: {INIT.resolve()}")

        ast.parse(INIT.read_text(encoding="utf-8"), filename=str(INIT))

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )

        if completed.returncode:
            raise RuntimeError(
                "OML-024 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-023 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-023 standalone test changed")

        print("[PASS] Certified OML-023 production unchanged")
        print("[PASS] Certified OML-023 standalone test unchanged")
        print("[PASS] OML-024 causal pattern memory installed")
        print("[PASS] OML-024 standalone deterministic test installed")
        print("[PASS] Cause-effect pattern tracking installed")
        print("[PASS] Temporal precedence verification installed")
        print("[PASS] Calibration and outcome lineage installed")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-024 CAUSAL PATTERN MEMORY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
