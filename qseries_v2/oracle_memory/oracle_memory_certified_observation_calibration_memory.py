from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_calibration_memory import (
    OracleMemoryCalibrationMemory,
    OracleMemoryCalibrationObservation,
    build_oracle_memory_calibration_memory,
    build_oracle_memory_calibration_observation,
    verify_oracle_memory_calibration_memory,
    verify_oracle_memory_calibration_observation,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_source_reliability_memory import (
    OracleMemoryCertifiedSourceReliability,
    verify_oracle_memory_certified_source_reliability,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-035"
ENGINE_ID = "OML-035"
POLICY_ID = "oracle-memory.certified-observation-calibration-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-034"
UPSTREAM_ENGINE_ID = "OML-034"
CALIBRATION_SCHEMA_VERSION = "OML-023"
CALIBRATION_ENGINE_ID = "OML-023"
STATE_READ_ONLY = "read_only_calibration_memory"


class OracleMemoryCertifiedCalibrationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCalibrationForecast:
    profile_name: str
    source_name: str
    source_id: str
    forecast_id: str
    certified_observation_hash: str
    predicted_probability: float
    outcome_confirmed: bool
    outcome_value: int | None
    observed_at: str
    resolved_at: str | None
    forecast_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedCalibrationBinding:
    profile_id: str
    profile_name: str
    profile_hash: str
    source_ids: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    calibration_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_reliability_memory_hash: str
    calibration_memory_hash: str
    source_reliability_lineage_verified: bool
    certified_observation_lineage_verified: bool
    calibration_lineage_verified: bool
    deterministic_binding_verified: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedCalibrationMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_reliability_memory_hash: str
    calibration_schema_version: str
    calibration_engine_id: str
    calibration_memory: OracleMemoryCalibrationMemory
    bindings: tuple[OracleMemoryCertifiedCalibrationBinding, ...]
    profile_count: int
    total_observation_count: int
    total_confirmed_count: int
    state: str
    source_reliability_lineage_verified: bool
    certified_observation_lineage_verified: bool
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
    downstream_causal_memory_authorized: bool
    read_only: bool
    certification_hash: str


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
    raise OracleMemoryCertifiedCalibrationInvariantError(
        "unsupported OML-035 value type: "
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
    raise OracleMemoryCertifiedCalibrationInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-035 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCalibrationInvariantError(
            f"OML-035 invalid {label} hexadecimal value"
        ) from exc


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        _reject("OML-035 normalized value cannot be empty")
    return normalized


def build_oracle_memory_certified_calibration_forecast(
    *,
    profile_name: str,
    source_name: str,
    source_id: str,
    forecast_id: str,
    certified_observation_hash: str,
    predicted_probability: float,
    outcome_confirmed: bool,
    outcome_value: int | None,
    observed_at: str,
    resolved_at: str | None = None,
) -> OracleMemoryCertifiedCalibrationForecast:
    if not isinstance(profile_name, str) or not profile_name.strip():
        _reject("OML-035 profile name required")
    if not isinstance(source_name, str) or not source_name.strip():
        _reject("OML-035 source name required")
    if not isinstance(forecast_id, str) or not forecast_id.strip():
        _reject("OML-035 forecast id required")
    if not isinstance(observed_at, str) or not observed_at.strip():
        _reject("OML-035 observed_at required")

    _require_hash(source_id, "source id")
    _require_hash(certified_observation_hash, "certified observation hash")

    predicted_probability = float(predicted_probability)
    if not 0.0 <= predicted_probability <= 1.0:
        _reject("OML-035 probability outside [0, 1]")

    if outcome_confirmed:
        if outcome_value not in (0, 1):
            _reject("OML-035 confirmed outcome must be 0 or 1")
        if not isinstance(resolved_at, str) or not resolved_at.strip():
            _reject("OML-035 confirmed outcome requires resolved_at")
    else:
        if outcome_value is not None:
            _reject("OML-035 unresolved outcome must be None")
        if resolved_at is not None:
            _reject("OML-035 unresolved outcome cannot have resolved_at")

    body = {
        "profile_name": profile_name.strip(),
        "source_name": source_name.strip(),
        "source_id": source_id,
        "forecast_id": forecast_id.strip(),
        "certified_observation_hash": certified_observation_hash,
        "predicted_probability": predicted_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_value": outcome_value,
        "observed_at": observed_at.strip(),
        "resolved_at": resolved_at.strip() if resolved_at else None,
    }

    result = OracleMemoryCertifiedCalibrationForecast(
        **body,
        forecast_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_calibration_forecast(result)
    return result


def verify_oracle_memory_certified_calibration_forecast(
    forecast: OracleMemoryCertifiedCalibrationForecast,
) -> bool:
    body = asdict(forecast)
    supplied = body.pop("forecast_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-035 forecast hash mismatch")

    _require_hash(forecast.source_id, "source id")
    _require_hash(
        forecast.certified_observation_hash,
        "certified observation hash",
    )
    _require_hash(forecast.forecast_hash, "forecast hash")

    if not forecast.profile_name.strip():
        _reject("OML-035 profile name missing")
    if not forecast.source_name.strip():
        _reject("OML-035 source name missing")
    if not forecast.forecast_id.strip():
        _reject("OML-035 forecast id missing")
    if not 0.0 <= forecast.predicted_probability <= 1.0:
        _reject("OML-035 forecast probability invalid")

    if forecast.outcome_confirmed:
        if forecast.outcome_value not in (0, 1):
            _reject("OML-035 confirmed outcome invalid")
        if forecast.resolved_at is None:
            _reject("OML-035 resolved_at missing")
    else:
        if forecast.outcome_value is not None:
            _reject("OML-035 unresolved outcome invalid")
        if forecast.resolved_at is not None:
            _reject("OML-035 unresolved resolved_at invalid")

    return True


def _build_binding(
    *,
    profile,
    forecasts: Sequence[OracleMemoryCertifiedCalibrationForecast],
    upstream: OracleMemoryCertifiedSourceReliability,
    calibration_memory: OracleMemoryCalibrationMemory,
) -> OracleMemoryCertifiedCalibrationBinding:
    ordered = tuple(
        sorted(
            forecasts,
            key=lambda item: (
                item.source_id,
                item.certified_observation_hash,
                item.forecast_id,
                item.forecast_hash,
            ),
        )
    )
    calibration_observation_hashes = tuple(
        item.observation_hash for item in profile.observations
    )

    body = {
        "profile_id": profile.profile_id,
        "profile_name": profile.profile_name,
        "profile_hash": profile.profile_hash,
        "source_ids": tuple(sorted({item.source_id for item in ordered})),
        "certified_observation_hashes": tuple(
            sorted({item.certified_observation_hash for item in ordered})
        ),
        "calibration_observation_hashes": calibration_observation_hashes,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_reliability_memory_hash": upstream.reliability_memory.memory_hash,
        "calibration_memory_hash": calibration_memory.memory_hash,
        "source_reliability_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "calibration_lineage_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    binding = OracleMemoryCertifiedCalibrationBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_calibration_binding(binding)
    return binding


def verify_oracle_memory_certified_calibration_binding(
    binding: OracleMemoryCertifiedCalibrationBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-035 binding hash mismatch")

    for value in (
        binding.profile_id,
        binding.profile_hash,
        binding.upstream_certification_hash,
        binding.upstream_reliability_memory_hash,
        binding.calibration_memory_hash,
        binding.binding_hash,
        *binding.source_ids,
        *binding.certified_observation_hashes,
        *binding.calibration_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")

    required = (
        binding.source_reliability_lineage_verified,
        binding.certified_observation_lineage_verified,
        binding.calibration_lineage_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )
    if not all(required):
        _reject("OML-035 binding guarantee missing")

    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )
    if any(forbidden):
        _reject("OML-035 forbidden binding capability enabled")

    return True


def build_oracle_memory_certified_calibration_memory(
    *,
    source_reliability: OracleMemoryCertifiedSourceReliability,
    forecasts: Sequence[OracleMemoryCertifiedCalibrationForecast],
) -> OracleMemoryCertifiedCalibrationMemory:
    verify_oracle_memory_certified_source_reliability(source_reliability)

    if source_reliability.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-035 upstream schema mismatch")
    if source_reliability.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-035 upstream engine mismatch")
    if not source_reliability.memory_ready:
        _reject("OML-035 upstream source reliability not ready")
    if not source_reliability.downstream_calibration_authorized:
        _reject("OML-035 calibration continuation not authorized")
    if not source_reliability.read_only:
        _reject("OML-035 upstream source reliability not read-only")

    profiles_by_source_id = {
        profile.source_id: profile
        for profile in source_reliability.reliability_memory.profiles
    }
    bindings_by_source_id = {
        binding.source_id: binding
        for binding in source_reliability.bindings
    }

    if set(profiles_by_source_id) != set(bindings_by_source_id):
        _reject("OML-035 upstream profile/binding identity mismatch")

    seen_forecast_ids: set[str] = set()
    forecasts_by_profile: dict[
        str,
        list[OracleMemoryCertifiedCalibrationForecast],
    ] = {}
    observations_by_profile: dict[
        str,
        list[OracleMemoryCalibrationObservation],
    ] = {}

    for forecast in forecasts:
        verify_oracle_memory_certified_calibration_forecast(forecast)

        if forecast.forecast_id in seen_forecast_ids:
            _reject("OML-035 duplicate forecast id")
        seen_forecast_ids.add(forecast.forecast_id)

        source_profile = profiles_by_source_id.get(forecast.source_id)
        source_binding = bindings_by_source_id.get(forecast.source_id)

        if source_profile is None or source_binding is None:
            _reject("OML-035 forecast references unknown certified source")
        if source_profile.source_name != forecast.source_name:
            _reject("OML-035 source name does not match certified source")
        if (
            forecast.certified_observation_hash
            not in source_binding.certified_observation_hashes
        ):
            _reject(
                "OML-035 forecast references unknown certified observation"
            )

        calibration_observation = (
            build_oracle_memory_calibration_observation(
                forecast_id=forecast.forecast_id,
                forecast_hash=forecast.certified_observation_hash,
                source_id=forecast.source_id,
                predicted_probability=forecast.predicted_probability,
                outcome_confirmed=forecast.outcome_confirmed,
                outcome_value=forecast.outcome_value,
                observed_at=forecast.observed_at,
                resolved_at=forecast.resolved_at,
            )
        )
        verify_oracle_memory_calibration_observation(
            calibration_observation
        )

        profile_key = forecast.profile_name.strip()
        forecasts_by_profile.setdefault(profile_key, []).append(forecast)
        observations_by_profile.setdefault(profile_key, []).append(
            calibration_observation
        )

    if not observations_by_profile:
        _reject("OML-035 at least one calibration forecast required")

    calibration_memory = build_oracle_memory_calibration_memory(
        source_memory=source_reliability.reliability_memory,
        observations_by_profile={
            key: tuple(value)
            for key, value in observations_by_profile.items()
        },
    )
    verify_oracle_memory_calibration_memory(calibration_memory)

    if calibration_memory.schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-035 calibration schema mismatch")
    if calibration_memory.engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-035 calibration engine mismatch")

    forecast_groups = {
        _normalize(key): tuple(value)
        for key, value in forecasts_by_profile.items()
    }

    bindings = tuple(
        _build_binding(
            profile=profile,
            forecasts=forecast_groups[profile.normalized_profile_name],
            upstream=source_reliability,
            calibration_memory=calibration_memory,
        )
        for profile in calibration_memory.profiles
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": source_reliability.schema_version,
        "upstream_engine_id": source_reliability.engine_id,
        "upstream_certification_hash": source_reliability.certification_hash,
        "upstream_reliability_memory_hash": (
            source_reliability.reliability_memory.memory_hash
        ),
        "calibration_schema_version": calibration_memory.schema_version,
        "calibration_engine_id": calibration_memory.engine_id,
        "calibration_memory": calibration_memory,
        "bindings": bindings,
        "profile_count": calibration_memory.profile_count,
        "total_observation_count": (
            calibration_memory.total_observation_count
        ),
        "total_confirmed_count": calibration_memory.total_confirmed_count,
        "state": STATE_READ_ONLY,
        "source_reliability_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_scoring_verified": (
            calibration_memory.deterministic_scoring_verified
        ),
        "profile_identity_uniqueness_verified": (
            calibration_memory.profile_identity_uniqueness_verified
        ),
        "canonical_profile_order_verified": (
            calibration_memory.canonical_profile_order_verified
        ),
        "probability_bounds_verified": (
            calibration_memory.probability_bounds_verified
        ),
        "outcome_lineage_verified": (
            calibration_memory.outcome_lineage_verified
        ),
        "calibration_bucket_reconciliation_verified": (
            calibration_memory.calibration_bucket_reconciliation_verified
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_causal_memory_authorized": True,
        "read_only": True,
    }

    result = OracleMemoryCertifiedCalibrationMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_calibration_memory(result)
    return result


def verify_oracle_memory_certified_calibration_memory(
    result: OracleMemoryCertifiedCalibrationMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-035 certification hash mismatch")

    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-035 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-035 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-035 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-035 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-035 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-035 upstream engine lineage mismatch")
    if result.calibration_schema_version != CALIBRATION_SCHEMA_VERSION:
        _reject("OML-035 calibration schema lineage mismatch")
    if result.calibration_engine_id != CALIBRATION_ENGINE_ID:
        _reject("OML-035 calibration engine lineage mismatch")

    _require_hash(
        result.upstream_certification_hash,
        "upstream certification hash",
    )
    _require_hash(
        result.upstream_reliability_memory_hash,
        "upstream reliability memory hash",
    )
    _require_hash(result.certification_hash, "certification hash")

    verify_oracle_memory_calibration_memory(result.calibration_memory)

    if (
        result.upstream_reliability_memory_hash
        != result.calibration_memory.upstream_memory_hash
    ):
        _reject("OML-035 reliability-to-calibration lineage mismatch")
    if result.profile_count != len(result.bindings):
        _reject("OML-035 profile/binding count mismatch")
    if result.profile_count != result.calibration_memory.profile_count:
        _reject("OML-035 profile count mismatch")
    if (
        result.total_observation_count
        != result.calibration_memory.total_observation_count
    ):
        _reject("OML-035 observation count mismatch")
    if (
        result.total_confirmed_count
        != result.calibration_memory.total_confirmed_count
    ):
        _reject("OML-035 confirmed count mismatch")

    profile_ids = tuple(
        profile.profile_id for profile in result.calibration_memory.profiles
    )
    binding_profile_ids = tuple(
        binding.profile_id for binding in result.bindings
    )
    if profile_ids != binding_profile_ids:
        _reject("OML-035 profile binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_calibration_binding(binding)
        if binding.upstream_certification_hash != (
            result.upstream_certification_hash
        ):
            _reject("OML-035 binding certification lineage mismatch")
        if binding.upstream_reliability_memory_hash != (
            result.upstream_reliability_memory_hash
        ):
            _reject("OML-035 binding reliability lineage mismatch")
        if binding.calibration_memory_hash != (
            result.calibration_memory.memory_hash
        ):
            _reject("OML-035 binding calibration lineage mismatch")

    required = (
        result.source_reliability_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_scoring_verified,
        result.profile_identity_uniqueness_verified,
        result.canonical_profile_order_verified,
        result.probability_bounds_verified,
        result.outcome_lineage_verified,
        result.calibration_bucket_reconciliation_verified,
        result.memory_ready,
        result.downstream_causal_memory_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-035 guarantee missing")

    if result.state != STATE_READ_ONLY:
        _reject("OML-035 state invalid")

    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-035 forbidden capability enabled")

    return True
