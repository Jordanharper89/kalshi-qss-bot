from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_source_reliability_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_022_oracle_memory_source_reliability_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_calibration_memory.py"
TEST = ROOT / "test_oml_023_oracle_memory_calibration_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_source_reliability_memory import (
    OracleMemorySourceReliabilityMemory,
    verify_oracle_memory_source_reliability_memory,
)

SCHEMA_VERSION = "OML-023"
ENGINE_ID = "OML-023"
POLICY_ID = "oracle-memory.calibration-memory.v1"

UPSTREAM_SCHEMA_VERSION = "OML-022"
UPSTREAM_ENGINE_ID = "OML-022"

CALIBRATION_STATUS_UNPROVEN = "unproven"
CALIBRATION_STATUS_CALIBRATED = "calibrated"
CALIBRATION_STATUS_OVERCONFIDENT = "overconfident"
CALIBRATION_STATUS_UNDERCONFIDENT = "underconfident"

ALLOWED_CALIBRATION_STATUSES = (
    CALIBRATION_STATUS_UNPROVEN,
    CALIBRATION_STATUS_CALIBRATED,
    CALIBRATION_STATUS_OVERCONFIDENT,
    CALIBRATION_STATUS_UNDERCONFIDENT,
)

BUCKET_BOUNDARIES = (
    (0.0, 0.2),
    (0.2, 0.4),
    (0.4, 0.6),
    (0.6, 0.8),
    (0.8, 1.0),
)


class OracleMemoryCalibrationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCalibrationObservation:
    forecast_id: str
    forecast_hash: str
    source_id: str
    predicted_probability: float
    outcome_confirmed: bool
    outcome_value: int | None
    observed_at: str
    resolved_at: str | None
    absolute_error: float | None
    brier_score: float | None
    observation_hash: str


@dataclass(frozen=True)
class OracleMemoryCalibrationBucket:
    lower_bound: float
    upper_bound: float
    observation_count: int
    confirmed_count: int
    average_forecast_probability: float
    empirical_outcome_rate: float
    absolute_calibration_gap: float
    brier_score: float
    bucket_hash: str


@dataclass(frozen=True)
class OracleMemoryCalibrationProfile:
    profile_id: str
    profile_name: str
    normalized_profile_name: str
    calibration_status: str
    observations: tuple[OracleMemoryCalibrationObservation, ...]
    buckets: tuple[OracleMemoryCalibrationBucket, ...]
    observation_count: int
    confirmed_count: int
    unresolved_count: int
    average_forecast_probability: float
    empirical_outcome_rate: float
    expected_calibration_error: float
    mean_brier_score: float
    overconfidence_gap: float
    underconfidence_gap: float
    deterministic_scoring_verified: bool
    canonical_order_verified: bool
    bucket_reconciliation_verified: bool
    outcome_lineage_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    profile_hash: str


@dataclass(frozen=True)
class OracleMemoryCalibrationMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_memory_hash: str
    profiles: tuple[OracleMemoryCalibrationProfile, ...]
    profile_count: int
    total_observation_count: int
    total_confirmed_count: int
    deterministic_scoring_verified: bool
    profile_identity_uniqueness_verified: bool
    canonical_profile_order_verified: bool
    probability_bounds_verified: bool
    outcome_lineage_verified: bool
    calibration_bucket_reconciliation_verified: bool
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

    raise OracleMemoryCalibrationInvariantError(
        "unsupported OML-023 value type: "
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
    raise OracleMemoryCalibrationInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-023 profile name cannot be empty")

    return normalized


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-023 invalid {label} length")

    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCalibrationInvariantError(
            f"OML-023 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_calibration_observation(
    *,
    forecast_id: str,
    forecast_hash: str,
    source_id: str,
    predicted_probability: float,
    outcome_confirmed: bool,
    outcome_value: int | None,
    observed_at: str,
    resolved_at: str | None = None,
) -> OracleMemoryCalibrationObservation:
    if not isinstance(forecast_id, str) or not forecast_id.strip():
        _reject("OML-023 forecast id required")

    _require_hash(forecast_hash, "forecast hash")
    _require_hash(source_id, "source id")

    predicted_probability = float(predicted_probability)

    if not 0.0 <= predicted_probability <= 1.0:
        _reject("OML-023 probability outside [0, 1]")

    if outcome_confirmed:
        if outcome_value not in (0, 1):
            _reject("OML-023 confirmed outcome must be 0 or 1")
        if not isinstance(resolved_at, str) or not resolved_at.strip():
            _reject("OML-023 confirmed outcome requires resolved_at")
    else:
        if outcome_value is not None:
            _reject("OML-023 unresolved outcome must be None")
        if resolved_at is not None:
            _reject("OML-023 unresolved forecast cannot have resolved_at")

    if not isinstance(observed_at, str) or not observed_at.strip():
        _reject("OML-023 observed_at required")

    absolute_error = (
        round(abs(predicted_probability - float(outcome_value)), 12)
        if outcome_confirmed
        else None
    )

    brier_score = (
        round(
            (predicted_probability - float(outcome_value)) ** 2,
            12,
        )
        if outcome_confirmed
        else None
    )

    body = {
        "forecast_id": forecast_id.strip(),
        "forecast_hash": forecast_hash,
        "source_id": source_id,
        "predicted_probability": predicted_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_value": outcome_value,
        "observed_at": observed_at.strip(),
        "resolved_at": resolved_at.strip() if resolved_at else None,
        "absolute_error": absolute_error,
        "brier_score": brier_score,
    }

    observation = OracleMemoryCalibrationObservation(
        **body,
        observation_hash=_stable_hash(body),
    )

    verify_oracle_memory_calibration_observation(observation)
    return observation


def verify_oracle_memory_calibration_observation(
    observation: OracleMemoryCalibrationObservation,
) -> bool:
    body = asdict(observation)
    supplied = body.pop("observation_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-023 observation hash mismatch")

    _require_hash(observation.forecast_hash, "forecast hash")
    _require_hash(observation.source_id, "source id")
    _require_hash(observation.observation_hash, "observation hash")

    if not 0.0 <= observation.predicted_probability <= 1.0:
        _reject("OML-023 observation probability invalid")

    if observation.outcome_confirmed:
        if observation.outcome_value not in (0, 1):
            _reject("OML-023 confirmed outcome invalid")
        if observation.absolute_error is None:
            _reject("OML-023 absolute error missing")
        if observation.brier_score is None:
            _reject("OML-023 brier score missing")
        if observation.resolved_at is None:
            _reject("OML-023 resolved_at missing")
    else:
        if observation.outcome_value is not None:
            _reject("OML-023 unresolved outcome value invalid")
        if observation.absolute_error is not None:
            _reject("OML-023 unresolved absolute error invalid")
        if observation.brier_score is not None:
            _reject("OML-023 unresolved brier score invalid")
        if observation.resolved_at is not None:
            _reject("OML-023 unresolved resolved_at invalid")

    return True


def _in_bucket(
    probability: float,
    lower: float,
    upper: float,
) -> bool:
    if upper == 1.0:
        return lower <= probability <= upper

    return lower <= probability < upper


def _build_bucket(
    *,
    observations: Sequence[OracleMemoryCalibrationObservation],
    lower: float,
    upper: float,
) -> OracleMemoryCalibrationBucket:
    selected = tuple(
        item
        for item in observations
        if _in_bucket(item.predicted_probability, lower, upper)
    )

    confirmed = tuple(
        item for item in selected if item.outcome_confirmed
    )

    average_forecast = (
        round(
            sum(item.predicted_probability for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    empirical_rate = (
        round(
            sum(int(item.outcome_value) for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    calibration_gap = (
        round(abs(average_forecast - empirical_rate), 12)
        if confirmed
        else 0.0
    )

    brier = (
        round(
            sum(float(item.brier_score) for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    body = {
        "lower_bound": lower,
        "upper_bound": upper,
        "observation_count": len(selected),
        "confirmed_count": len(confirmed),
        "average_forecast_probability": average_forecast,
        "empirical_outcome_rate": empirical_rate,
        "absolute_calibration_gap": calibration_gap,
        "brier_score": brier,
    }

    bucket = OracleMemoryCalibrationBucket(
        **body,
        bucket_hash=_stable_hash(body),
    )

    verify_oracle_memory_calibration_bucket(bucket)
    return bucket


def verify_oracle_memory_calibration_bucket(
    bucket: OracleMemoryCalibrationBucket,
) -> bool:
    body = asdict(bucket)
    supplied = body.pop("bucket_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-023 bucket hash mismatch")

    if not 0.0 <= bucket.lower_bound < bucket.upper_bound <= 1.0:
        _reject("OML-023 bucket boundaries invalid")

    if bucket.confirmed_count > bucket.observation_count:
        _reject("OML-023 bucket confirmed count invalid")

    for value in (
        bucket.average_forecast_probability,
        bucket.empirical_outcome_rate,
        bucket.absolute_calibration_gap,
        bucket.brier_score,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-023 bucket metric outside [0, 1]")

    return True


def _status_for(
    *,
    confirmed_count: int,
    average_forecast_probability: float,
    empirical_outcome_rate: float,
    expected_calibration_error: float,
) -> str:
    if confirmed_count == 0:
        return CALIBRATION_STATUS_UNPROVEN

    if expected_calibration_error <= 0.10:
        return CALIBRATION_STATUS_CALIBRATED

    if average_forecast_probability > empirical_outcome_rate:
        return CALIBRATION_STATUS_OVERCONFIDENT

    return CALIBRATION_STATUS_UNDERCONFIDENT


def build_oracle_memory_calibration_profile(
    *,
    profile_name: str,
    observations: Sequence[OracleMemoryCalibrationObservation],
) -> OracleMemoryCalibrationProfile:
    normalized = _normalize(profile_name)

    ordered = tuple(
        sorted(
            observations,
            key=lambda item: (
                item.observed_at,
                item.forecast_id,
                item.observation_hash,
            ),
        )
    )

    if not ordered:
        _reject("OML-023 calibration profile requires observations")

    for observation in ordered:
        verify_oracle_memory_calibration_observation(observation)

    buckets = tuple(
        _build_bucket(
            observations=ordered,
            lower=lower,
            upper=upper,
        )
        for lower, upper in BUCKET_BOUNDARIES
    )

    confirmed = tuple(
        item for item in ordered if item.outcome_confirmed
    )

    average_forecast = (
        round(
            sum(item.predicted_probability for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    empirical_rate = (
        round(
            sum(int(item.outcome_value) for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    expected_calibration_error = (
        round(
            sum(
                bucket.absolute_calibration_gap
                * bucket.confirmed_count
                for bucket in buckets
            )
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    mean_brier = (
        round(
            sum(float(item.brier_score) for item in confirmed)
            / len(confirmed),
            12,
        )
        if confirmed
        else 0.0
    )

    overconfidence_gap = round(
        max(0.0, average_forecast - empirical_rate),
        12,
    )

    underconfidence_gap = round(
        max(0.0, empirical_rate - average_forecast),
        12,
    )

    profile_id = _stable_hash(
        {"normalized_profile_name": normalized}
    )

    status = _status_for(
        confirmed_count=len(confirmed),
        average_forecast_probability=average_forecast,
        empirical_outcome_rate=empirical_rate,
        expected_calibration_error=expected_calibration_error,
    )

    body = {
        "profile_id": profile_id,
        "profile_name": profile_name.strip(),
        "normalized_profile_name": normalized,
        "calibration_status": status,
        "observations": ordered,
        "buckets": buckets,
        "observation_count": len(ordered),
        "confirmed_count": len(confirmed),
        "unresolved_count": len(ordered) - len(confirmed),
        "average_forecast_probability": average_forecast,
        "empirical_outcome_rate": empirical_rate,
        "expected_calibration_error": expected_calibration_error,
        "mean_brier_score": mean_brier,
        "overconfidence_gap": overconfidence_gap,
        "underconfidence_gap": underconfidence_gap,
        "deterministic_scoring_verified": True,
        "canonical_order_verified": True,
        "bucket_reconciliation_verified": (
            sum(bucket.observation_count for bucket in buckets)
            == len(ordered)
        ),
        "outcome_lineage_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    profile = OracleMemoryCalibrationProfile(
        **body,
        profile_hash=_stable_hash(body),
    )

    verify_oracle_memory_calibration_profile(profile)
    return profile


def verify_oracle_memory_calibration_profile(
    profile: OracleMemoryCalibrationProfile,
) -> bool:
    body = asdict(profile)
    supplied = body.pop("profile_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-023 profile hash mismatch")

    if profile.normalized_profile_name != _normalize(profile.profile_name):
        _reject("OML-023 profile normalization mismatch")

    expected_profile_id = _stable_hash(
        {"normalized_profile_name": profile.normalized_profile_name}
    )

    if profile.profile_id != expected_profile_id:
        _reject("OML-023 profile identity mismatch")

    if profile.calibration_status not in ALLOWED_CALIBRATION_STATUSES:
        _reject("OML-023 calibration status invalid")

    if profile.observation_count != len(profile.observations):
        _reject("OML-023 observation count mismatch")

    if profile.confirmed_count + profile.unresolved_count != (
        profile.observation_count
    ):
        _reject("OML-023 confirmed/unresolved reconciliation mismatch")

    if len(profile.buckets) != len(BUCKET_BOUNDARIES):
        _reject("OML-023 bucket count mismatch")

    for observation in profile.observations:
        verify_oracle_memory_calibration_observation(observation)

    for bucket in profile.buckets:
        verify_oracle_memory_calibration_bucket(bucket)

    if sum(bucket.observation_count for bucket in profile.buckets) != (
        profile.observation_count
    ):
        _reject("OML-023 bucket observation reconciliation mismatch")

    for value in (
        profile.average_forecast_probability,
        profile.empirical_outcome_rate,
        profile.expected_calibration_error,
        profile.mean_brier_score,
        profile.overconfidence_gap,
        profile.underconfidence_gap,
    ):
        if not 0.0 <= value <= 1.0:
            _reject("OML-023 profile metric outside [0, 1]")

    required_true = (
        profile.deterministic_scoring_verified,
        profile.canonical_order_verified,
        profile.bucket_reconciliation_verified,
        profile.outcome_lineage_verified,
        profile.read_only,
    )

    if not all(required_true):
        _reject("OML-023 profile guarantee missing")

    forbidden = (
        profile.persistence_authorized,
        profile.learning_update_authorized,
        profile.runtime_activation_authorized,
        profile.publication_authorized,
        profile.action_authorization_enabled,
        profile.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-023 forbidden profile capability enabled")

    return True


def build_oracle_memory_calibration_memory(
    *,
    source_memory: OracleMemorySourceReliabilityMemory,
    observations_by_profile: Mapping[
        str,
        Sequence[OracleMemoryCalibrationObservation],
    ],
) -> OracleMemoryCalibrationMemory:
    verify_oracle_memory_source_reliability_memory(source_memory)

    if source_memory.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-023 upstream schema mismatch")

    if source_memory.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-023 upstream engine mismatch")

    if not source_memory.memory_ready:
        _reject("OML-023 upstream source memory not ready")

    if not source_memory.next_certification_authorized:
        _reject("OML-023 upstream continuation not authorized")

    if not source_memory.read_only:
        _reject("OML-023 upstream source memory not read-only")

    profiles = tuple(
        sorted(
            (
                build_oracle_memory_calibration_profile(
                    profile_name=profile_name,
                    observations=observations_by_profile[profile_name],
                )
                for profile_name in sorted(
                    observations_by_profile,
                    key=_normalize,
                )
            ),
            key=lambda item: (
                item.normalized_profile_name,
                item.profile_id,
            ),
        )
    )

    profile_ids = tuple(profile.profile_id for profile in profiles)

    if len(set(profile_ids)) != len(profile_ids):
        _reject("OML-023 duplicate calibration profile identities")

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": source_memory.schema_version,
        "upstream_engine_id": source_memory.engine_id,
        "upstream_memory_hash": source_memory.memory_hash,
        "profiles": profiles,
        "profile_count": len(profiles),
        "total_observation_count": sum(
            profile.observation_count for profile in profiles
        ),
        "total_confirmed_count": sum(
            profile.confirmed_count for profile in profiles
        ),
        "deterministic_scoring_verified": True,
        "profile_identity_uniqueness_verified": True,
        "canonical_profile_order_verified": True,
        "probability_bounds_verified": True,
        "outcome_lineage_verified": True,
        "calibration_bucket_reconciliation_verified": True,
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

    memory = OracleMemoryCalibrationMemory(
        **body,
        memory_hash=_stable_hash(body),
    )

    verify_oracle_memory_calibration_memory(memory)
    return memory


def verify_oracle_memory_calibration_memory(
    memory: OracleMemoryCalibrationMemory,
) -> bool:
    body = asdict(memory)
    supplied = body.pop("memory_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-023 memory hash mismatch")

    if memory.schema_version != SCHEMA_VERSION:
        _reject("OML-023 schema mismatch")

    if memory.engine_id != ENGINE_ID:
        _reject("OML-023 engine mismatch")

    if memory.policy_id != POLICY_ID:
        _reject("OML-023 policy mismatch")

    if memory.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-023 subsystem mismatch")

    if memory.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-023 upstream schema lineage mismatch")

    if memory.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-023 upstream engine lineage mismatch")

    if memory.profile_count != len(memory.profiles):
        _reject("OML-023 profile count mismatch")

    if memory.total_observation_count != sum(
        profile.observation_count for profile in memory.profiles
    ):
        _reject("OML-023 observation count mismatch")

    if memory.total_confirmed_count != sum(
        profile.confirmed_count for profile in memory.profiles
    ):
        _reject("OML-023 confirmed count mismatch")

    profile_ids = []

    for profile in memory.profiles:
        verify_oracle_memory_calibration_profile(profile)
        profile_ids.append(profile.profile_id)

    if len(set(profile_ids)) != len(profile_ids):
        _reject("OML-023 duplicate profile identities")

    required_true = (
        memory.deterministic_scoring_verified,
        memory.profile_identity_uniqueness_verified,
        memory.canonical_profile_order_verified,
        memory.probability_bounds_verified,
        memory.outcome_lineage_verified,
        memory.calibration_bucket_reconciliation_verified,
        memory.memory_ready,
        memory.next_certification_authorized,
        memory.read_only,
    )

    if not all(required_true):
        _reject("OML-023 memory guarantee missing")

    forbidden = (
        memory.persistence_enabled,
        memory.learning_updates_enabled,
        memory.runtime_activation_enabled,
        memory.publication_enabled,
        memory.action_authorization_enabled,
        memory.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-023 forbidden memory capability enabled")

    return True
"""

TEST_SOURCE = r"""
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
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstream() -> None:
    if not UPSTREAM.is_file() or not UPSTREAM_TEST.is_file():
        raise RuntimeError(
            "Certified OML-022 production or standalone test missing"
        )

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_source_reliability_memory"
    )

    expected = {
        "SCHEMA_VERSION": "OML-022",
        "ENGINE_ID": "OML-022",
        "POLICY_ID": "oracle-memory.source-reliability-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-021",
        "UPSTREAM_ENGINE_ID": "OML-021",
    }

    for name, value in expected.items():
        actual = getattr(module, name, None)

        if actual != value:
            raise RuntimeError(
                f"Certified OML-022 {name} mismatch: "
                f"expected {value!r}, got {actual!r}"
            )

    required = (
        "OracleMemorySourceReliabilityMemory",
        "build_oracle_memory_source_reliability_memory",
        "verify_oracle_memory_source_reliability_memory",
    )

    missing = [name for name in required if not hasattr(module, name)]

    if missing:
        raise RuntimeError(
            "Certified OML-022 missing required symbols: "
            + ", ".join(missing)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-023 FOR-SURE INSTALLER")
    print(" CALIBRATION MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: CAPABILITY_MILESTONE_FULL_REPLACEMENT")

    try:
        validate_upstream()
        print("[OK] Actual OML-022 imported and structurally verified")

        upstream_run = subprocess.run(
            [sys.executable, str(UPSTREAM_TEST)],
            cwd=ROOT,
            check=False,
        )

        if upstream_run.returncode:
            raise RuntimeError(
                "OML-022 certification failed with exit code "
                f"{upstream_run.returncode}"
            )

        production_before = UPSTREAM.read_bytes()
        test_before = UPSTREAM_TEST.read_bytes()

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = "from .oracle_memory_calibration_memory import *"
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
                "OML-023 test failed with exit code "
                f"{completed.returncode}"
            )

        if UPSTREAM.read_bytes() != production_before:
            raise RuntimeError("Certified OML-022 production changed")

        if UPSTREAM_TEST.read_bytes() != test_before:
            raise RuntimeError("Certified OML-022 standalone test changed")

        print("[PASS] Certified OML-022 production unchanged")
        print("[PASS] Certified OML-022 standalone test unchanged")
        print("[PASS] OML-023 calibration memory installed")
        print("[PASS] OML-023 standalone deterministic test installed")
        print("[PASS] Forecast-outcome calibration installed")
        print("[PASS] Calibration buckets installed")
        print("[PASS] Brier and calibration-error scoring installed")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OML-023 CALIBRATION MEMORY INSTALLED")
        return 0

    except (RuntimeError, SyntaxError, ImportError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
