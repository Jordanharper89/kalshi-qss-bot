from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory import (
    OracleMemoryCausalObservation,
    OracleMemoryCausalPatternMemory,
    build_oracle_memory_causal_observation,
    build_oracle_memory_causal_pattern,
    build_oracle_memory_causal_pattern_memory,
    verify_oracle_memory_causal_observation,
    verify_oracle_memory_causal_pattern_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_calibration_memory import (
    OracleMemoryCertifiedCalibrationMemory,
    verify_oracle_memory_certified_calibration_memory,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-036"
ENGINE_ID = "OML-036"
POLICY_ID = "oracle-memory.certified-observation-causal-pattern-memory.v1"
UPSTREAM_SCHEMA_VERSION = "OML-035"
UPSTREAM_ENGINE_ID = "OML-035"
CAUSAL_SCHEMA_VERSION = "OML-024"
CAUSAL_ENGINE_ID = "OML-024"
STATE_READ_ONLY = "read_only_causal_pattern_memory"


class OracleMemoryCertifiedCausalPatternInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCausalObservationRequest:
    pattern_name: str
    cause_entity_id: str
    effect_entity_id: str
    cause_observed_at: str
    effect_observed_at: str
    certified_observation_hashes: tuple[str, ...]
    contradicting_certified_observation_hashes: tuple[str, ...]
    confidence: float
    calibrated_probability: float
    outcome_confirmed: bool
    outcome_supported: bool | None
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedCausalPatternBinding:
    pattern_id: str
    pattern_name: str
    pattern_hash: str
    cause_entity_id: str
    effect_entity_id: str
    certified_observation_hashes: tuple[str, ...]
    calibration_observation_hashes: tuple[str, ...]
    causal_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_calibration_memory_hash: str
    causal_memory_hash: str
    certified_observation_lineage_verified: bool
    calibration_lineage_verified: bool
    temporal_precedence_verified: bool
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
class OracleMemoryCertifiedCausalPatternMemory:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_calibration_memory_hash: str
    causal_schema_version: str
    causal_engine_id: str
    causal_memory: OracleMemoryCausalPatternMemory
    bindings: tuple[OracleMemoryCertifiedCausalPatternBinding, ...]
    pattern_count: int
    total_observation_count: int
    state: str
    certified_observation_lineage_verified: bool
    calibration_lineage_verified: bool
    deterministic_identity_verified: bool
    canonical_pattern_order_verified: bool
    temporal_precedence_verified: bool
    evidence_lineage_verified: bool
    contradiction_tracking_verified: bool
    outcome_reconciliation_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    memory_ready: bool
    downstream_multi_hop_causal_authorized: bool
    read_only: bool
    certification_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCertifiedCausalPatternInvariantError(
        "unsupported OML-036 value type: "
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
    raise OracleMemoryCertifiedCausalPatternInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-036 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCausalPatternInvariantError(
            f"OML-036 invalid {label} hexadecimal value"
        ) from exc


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())
    if not normalized:
        _reject("OML-036 normalized value cannot be empty")
    return normalized


def build_oracle_memory_certified_causal_observation_request(
    *,
    pattern_name: str,
    cause_entity_id: str,
    effect_entity_id: str,
    cause_observed_at: str,
    effect_observed_at: str,
    certified_observation_hashes: Sequence[str],
    contradicting_certified_observation_hashes: Sequence[str] = (),
    confidence: float,
    calibrated_probability: float,
    outcome_confirmed: bool,
    outcome_supported: bool | None,
) -> OracleMemoryCertifiedCausalObservationRequest:
    if not isinstance(pattern_name, str) or not pattern_name.strip():
        _reject("OML-036 pattern name required")
    _require_hash(cause_entity_id, "cause entity id")
    _require_hash(effect_entity_id, "effect entity id")
    if cause_entity_id == effect_entity_id:
        _reject("OML-036 cause and effect entities must differ")
    if not cause_observed_at.strip() or not effect_observed_at.strip():
        _reject("OML-036 observation timestamps required")
    if effect_observed_at < cause_observed_at:
        _reject("OML-036 effect cannot precede cause")

    evidence = tuple(sorted(set(certified_observation_hashes)))
    contradictions = tuple(
        sorted(set(contradicting_certified_observation_hashes))
    )
    if not evidence:
        _reject("OML-036 certified causal evidence required")
    for value in (*evidence, *contradictions):
        _require_hash(value, "certified observation hash")

    confidence = float(confidence)
    calibrated_probability = float(calibrated_probability)
    if not 0.0 <= confidence <= 1.0:
        _reject("OML-036 confidence outside [0, 1]")
    if not 0.0 <= calibrated_probability <= 1.0:
        _reject("OML-036 calibrated probability outside [0, 1]")
    if outcome_confirmed:
        if outcome_supported is None:
            _reject("OML-036 confirmed outcome requires support result")
    elif outcome_supported is not None:
        _reject("OML-036 unresolved outcome cannot carry support result")

    body = {
        "pattern_name": pattern_name.strip(),
        "cause_entity_id": cause_entity_id,
        "effect_entity_id": effect_entity_id,
        "cause_observed_at": cause_observed_at.strip(),
        "effect_observed_at": effect_observed_at.strip(),
        "certified_observation_hashes": evidence,
        "contradicting_certified_observation_hashes": contradictions,
        "confidence": confidence,
        "calibrated_probability": calibrated_probability,
        "outcome_confirmed": bool(outcome_confirmed),
        "outcome_supported": outcome_supported,
    }
    result = OracleMemoryCertifiedCausalObservationRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_causal_observation_request(result)
    return result


def verify_oracle_memory_certified_causal_observation_request(
    request: OracleMemoryCertifiedCausalObservationRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-036 request hash mismatch")
    for value in (
        request.cause_entity_id,
        request.effect_entity_id,
        request.request_hash,
        *request.certified_observation_hashes,
        *request.contradicting_certified_observation_hashes,
    ):
        _require_hash(value, "request lineage hash")
    if request.cause_entity_id == request.effect_entity_id:
        _reject("OML-036 self-causation request forbidden")
    if request.effect_observed_at < request.cause_observed_at:
        _reject("OML-036 temporal precedence violated")
    if not request.certified_observation_hashes:
        _reject("OML-036 request evidence missing")
    if not 0.0 <= request.confidence <= 1.0:
        _reject("OML-036 request confidence invalid")
    if not 0.0 <= request.calibrated_probability <= 1.0:
        _reject("OML-036 request probability invalid")
    if request.outcome_confirmed:
        if request.outcome_supported is None:
            _reject("OML-036 confirmed outcome support missing")
    elif request.outcome_supported is not None:
        _reject("OML-036 unresolved outcome support invalid")
    return True


def _build_binding(
    *,
    pattern,
    requests: Sequence[OracleMemoryCertifiedCausalObservationRequest],
    upstream: OracleMemoryCertifiedCalibrationMemory,
    causal_memory: OracleMemoryCausalPatternMemory,
) -> OracleMemoryCertifiedCausalPatternBinding:
    calibration_hashes = {
        item.observation_hash
        for profile in upstream.calibration_memory.profiles
        for item in profile.observations
    }
    certified_hashes = tuple(
        sorted({
            value
            for request in requests
            for value in (
                *request.certified_observation_hashes,
                *request.contradicting_certified_observation_hashes,
            )
        })
    )
    body = {
        "pattern_id": pattern.pattern_id,
        "pattern_name": pattern.pattern_name,
        "pattern_hash": pattern.pattern_hash,
        "cause_entity_id": pattern.cause_entity_id,
        "effect_entity_id": pattern.effect_entity_id,
        "certified_observation_hashes": certified_hashes,
        "calibration_observation_hashes": tuple(sorted(calibration_hashes)),
        "causal_observation_hashes": tuple(
            item.observation_hash for item in pattern.observations
        ),
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_calibration_memory_hash": upstream.calibration_memory.memory_hash,
        "causal_memory_hash": causal_memory.memory_hash,
        "certified_observation_lineage_verified": True,
        "calibration_lineage_verified": True,
        "temporal_precedence_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCausalPatternBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_causal_pattern_binding(result)
    return result


def verify_oracle_memory_certified_causal_pattern_binding(
    binding: OracleMemoryCertifiedCausalPatternBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-036 binding hash mismatch")
    for value in (
        binding.pattern_id,
        binding.pattern_hash,
        binding.cause_entity_id,
        binding.effect_entity_id,
        binding.upstream_certification_hash,
        binding.upstream_calibration_memory_hash,
        binding.causal_memory_hash,
        binding.binding_hash,
        *binding.certified_observation_hashes,
        *binding.calibration_observation_hashes,
        *binding.causal_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    required = (
        binding.certified_observation_lineage_verified,
        binding.calibration_lineage_verified,
        binding.temporal_precedence_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )
    if not all(required):
        _reject("OML-036 binding guarantee missing")
    forbidden = (
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )
    if any(forbidden):
        _reject("OML-036 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_causal_pattern_memory(
    *,
    calibration: OracleMemoryCertifiedCalibrationMemory,
    requests: Sequence[OracleMemoryCertifiedCausalObservationRequest],
) -> OracleMemoryCertifiedCausalPatternMemory:
    verify_oracle_memory_certified_calibration_memory(calibration)
    if calibration.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-036 upstream schema mismatch")
    if calibration.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-036 upstream engine mismatch")
    if not calibration.memory_ready:
        _reject("OML-036 upstream calibration not ready")
    if not calibration.downstream_causal_memory_authorized:
        _reject("OML-036 causal continuation not authorized")
    if not calibration.read_only:
        _reject("OML-036 upstream calibration not read-only")

    allowed_certified_hashes = {
        value
        for binding in calibration.bindings
        for value in binding.certified_observation_hashes
    }
    allowed_calibration_hashes = {
        item.observation_hash
        for profile in calibration.calibration_memory.profiles
        for item in profile.observations
    }
    if not allowed_certified_hashes or not allowed_calibration_hashes:
        _reject("OML-036 upstream calibration lineage empty")

    grouped_requests: dict[
        str, list[OracleMemoryCertifiedCausalObservationRequest]
    ] = {}
    grouped_observations: dict[str, list[OracleMemoryCausalObservation]] = {}
    seen_request_hashes: set[str] = set()

    for request in requests:
        verify_oracle_memory_certified_causal_observation_request(request)
        if request.request_hash in seen_request_hashes:
            _reject("OML-036 duplicate causal request")
        seen_request_hashes.add(request.request_hash)

        referenced = set(request.certified_observation_hashes)
        contradicted = set(
            request.contradicting_certified_observation_hashes
        )
        if not referenced.issubset(allowed_certified_hashes):
            _reject("OML-036 unknown certified causal evidence")
        if not contradicted.issubset(allowed_certified_hashes):
            _reject("OML-036 unknown certified contradiction evidence")

        causal_observation = build_oracle_memory_causal_observation(
            cause_entity_id=request.cause_entity_id,
            effect_entity_id=request.effect_entity_id,
            cause_observed_at=request.cause_observed_at,
            effect_observed_at=request.effect_observed_at,
            evidence_hashes=request.certified_observation_hashes,
            contradicting_evidence_hashes=(
                request.contradicting_certified_observation_hashes
            ),
            confidence=request.confidence,
            calibrated_probability=request.calibrated_probability,
            outcome_confirmed=request.outcome_confirmed,
            outcome_supported=request.outcome_supported,
        )
        verify_oracle_memory_causal_observation(causal_observation)
        key = request.pattern_name.strip()
        grouped_requests.setdefault(key, []).append(request)
        grouped_observations.setdefault(key, []).append(causal_observation)

    if not grouped_observations:
        _reject("OML-036 at least one causal request required")

    patterns = tuple(
        build_oracle_memory_causal_pattern(
            pattern_name=name,
            observations=tuple(observations),
        )
        for name, observations in sorted(
            grouped_observations.items(),
            key=lambda pair: _normalize(pair[0]),
        )
    )
    causal_memory = build_oracle_memory_causal_pattern_memory(
        calibration_memory=calibration.calibration_memory,
        patterns=patterns,
    )
    verify_oracle_memory_causal_pattern_memory(causal_memory)

    if causal_memory.schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-036 causal schema mismatch")
    if causal_memory.engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-036 causal engine mismatch")

    request_groups = {
        _normalize(name): tuple(values)
        for name, values in grouped_requests.items()
    }
    bindings = tuple(
        _build_binding(
            pattern=pattern,
            requests=request_groups[pattern.normalized_pattern_name],
            upstream=calibration,
            causal_memory=causal_memory,
        )
        for pattern in causal_memory.patterns
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": calibration.schema_version,
        "upstream_engine_id": calibration.engine_id,
        "upstream_certification_hash": calibration.certification_hash,
        "upstream_calibration_memory_hash": calibration.calibration_memory.memory_hash,
        "causal_schema_version": causal_memory.schema_version,
        "causal_engine_id": causal_memory.engine_id,
        "causal_memory": causal_memory,
        "bindings": bindings,
        "pattern_count": causal_memory.pattern_count,
        "total_observation_count": causal_memory.total_observation_count,
        "state": STATE_READ_ONLY,
        "certified_observation_lineage_verified": True,
        "calibration_lineage_verified": True,
        "deterministic_identity_verified": causal_memory.deterministic_identity_verified,
        "canonical_pattern_order_verified": causal_memory.canonical_pattern_order_verified,
        "temporal_precedence_verified": causal_memory.temporal_precedence_verified,
        "evidence_lineage_verified": causal_memory.evidence_lineage_verified,
        "contradiction_tracking_verified": causal_memory.contradiction_tracking_verified,
        "outcome_reconciliation_verified": causal_memory.outcome_reconciliation_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "memory_ready": True,
        "downstream_multi_hop_causal_authorized": True,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCausalPatternMemory(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_causal_pattern_memory(result)
    return result


def verify_oracle_memory_certified_causal_pattern_memory(
    result: OracleMemoryCertifiedCausalPatternMemory,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-036 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-036 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-036 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-036 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-036 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-036 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-036 upstream engine lineage mismatch")
    if result.causal_schema_version != CAUSAL_SCHEMA_VERSION:
        _reject("OML-036 causal schema lineage mismatch")
    if result.causal_engine_id != CAUSAL_ENGINE_ID:
        _reject("OML-036 causal engine lineage mismatch")

    for value in (
        result.upstream_certification_hash,
        result.upstream_calibration_memory_hash,
        result.certification_hash,
    ):
        _require_hash(value, "certification lineage hash")

    verify_oracle_memory_causal_pattern_memory(result.causal_memory)
    if result.upstream_calibration_memory_hash != (
        result.causal_memory.upstream_memory_hash
    ):
        _reject("OML-036 calibration-to-causal lineage mismatch")
    if result.pattern_count != len(result.bindings):
        _reject("OML-036 pattern/binding count mismatch")
    if result.pattern_count != result.causal_memory.pattern_count:
        _reject("OML-036 pattern count mismatch")
    if result.total_observation_count != (
        result.causal_memory.total_observation_count
    ):
        _reject("OML-036 observation count mismatch")

    pattern_ids = tuple(
        pattern.pattern_id for pattern in result.causal_memory.patterns
    )
    binding_ids = tuple(binding.pattern_id for binding in result.bindings)
    if pattern_ids != binding_ids:
        _reject("OML-036 pattern binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_causal_pattern_binding(binding)
        if binding.upstream_certification_hash != result.upstream_certification_hash:
            _reject("OML-036 binding certification lineage mismatch")
        if binding.upstream_calibration_memory_hash != (
            result.upstream_calibration_memory_hash
        ):
            _reject("OML-036 binding calibration lineage mismatch")
        if binding.causal_memory_hash != result.causal_memory.memory_hash:
            _reject("OML-036 binding causal lineage mismatch")

    required = (
        result.certified_observation_lineage_verified,
        result.calibration_lineage_verified,
        result.deterministic_identity_verified,
        result.canonical_pattern_order_verified,
        result.temporal_precedence_verified,
        result.evidence_lineage_verified,
        result.contradiction_tracking_verified,
        result.outcome_reconciliation_verified,
        result.memory_ready,
        result.downstream_multi_hop_causal_authorized,
        result.read_only,
    )
    if not all(required):
        _reject("OML-036 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-036 state invalid")
    forbidden = (
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )
    if any(forbidden):
        _reject("OML-036 forbidden capability enabled")
    return True
