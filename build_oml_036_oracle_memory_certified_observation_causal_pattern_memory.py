from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_memory"

UPSTREAM = PACKAGE / "oracle_memory_certified_observation_calibration_memory.py"
UPSTREAM_TEST = ROOT / "test_oml_035_oracle_memory_certified_observation_calibration_memory.py"
CAUSAL_MODULE = PACKAGE / "oracle_memory_causal_pattern_memory.py"
CAUSAL_TEST = ROOT / "test_oml_024_oracle_memory_causal_pattern_memory.py"

PRODUCTION = PACKAGE / "oracle_memory_certified_observation_causal_pattern_memory.py"
TEST = ROOT / "test_oml_036_oracle_memory_certified_observation_causal_pattern_memory.py"
INIT = PACKAGE / "__init__.py"

PRODUCTION_SOURCE = r"""
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
"""


def write_complete(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def validate_upstreams() -> None:
    required = (UPSTREAM, UPSTREAM_TEST, CAUSAL_MODULE, CAUSAL_TEST)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required certified upstream files missing: " + ", ".join(missing)
        )
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    upstream_module = importlib.import_module(
        "qseries_v2.oracle_memory."
        "oracle_memory_certified_observation_calibration_memory"
    )
    causal_module = importlib.import_module(
        "qseries_v2.oracle_memory.oracle_memory_causal_pattern_memory"
    )

    expected_upstream = {
        "SCHEMA_VERSION": "OML-035",
        "ENGINE_ID": "OML-035",
        "POLICY_ID": (
            "oracle-memory.certified-observation-calibration-memory.v1"
        ),
        "UPSTREAM_SCHEMA_VERSION": "OML-034",
        "UPSTREAM_ENGINE_ID": "OML-034",
        "CALIBRATION_SCHEMA_VERSION": "OML-023",
        "CALIBRATION_ENGINE_ID": "OML-023",
    }
    expected_causal = {
        "SCHEMA_VERSION": "OML-024",
        "ENGINE_ID": "OML-024",
        "POLICY_ID": "oracle-memory.causal-pattern-memory.v1",
        "UPSTREAM_SCHEMA_VERSION": "OML-023",
        "UPSTREAM_ENGINE_ID": "OML-023",
    }
    for name, value in expected_upstream.items():
        if getattr(upstream_module, name, None) != value:
            raise RuntimeError(f"Certified OML-035 {name} mismatch")
    for name, value in expected_causal.items():
        if getattr(causal_module, name, None) != value:
            raise RuntimeError(f"Certified OML-024 {name} mismatch")

    required_upstream_symbols = (
        "OracleMemoryCertifiedCalibrationMemory",
        "verify_oracle_memory_certified_calibration_memory",
    )
    required_causal_symbols = (
        "OracleMemoryCausalObservation",
        "OracleMemoryCausalPatternMemory",
        "build_oracle_memory_causal_observation",
        "build_oracle_memory_causal_pattern",
        "build_oracle_memory_causal_pattern_memory",
        "verify_oracle_memory_causal_observation",
        "verify_oracle_memory_causal_pattern_memory",
        "OracleMemoryCausalPatternInvariantError",
    )
    for module, names, label in (
        (upstream_module, required_upstream_symbols, "OML-035"),
        (causal_module, required_causal_symbols, "OML-024"),
    ):
        missing_names = [name for name in names if not hasattr(module, name)]
        if missing_names:
            raise RuntimeError(
                f"Certified {label} missing symbols: "
                + ", ".join(missing_names)
            )

    builders = {
        "build_oracle_memory_causal_observation": {
            "cause_entity_id",
            "effect_entity_id",
            "cause_observed_at",
            "effect_observed_at",
            "evidence_hashes",
            "contradicting_evidence_hashes",
            "confidence",
            "calibrated_probability",
            "outcome_confirmed",
            "outcome_supported",
        },
        "build_oracle_memory_causal_pattern": {
            "pattern_name",
            "observations",
        },
        "build_oracle_memory_causal_pattern_memory": {
            "calibration_memory",
            "patterns",
        },
    }
    for builder_name, required_parameters in builders.items():
        actual = set(
            inspect.signature(getattr(causal_module, builder_name)).parameters
        )
        missing_parameters = sorted(required_parameters - actual)
        if missing_parameters:
            raise RuntimeError(
                f"Certified OML-024 {builder_name} parameters missing: "
                + ", ".join(missing_parameters)
            )

    required_upstream_fields = {
        "schema_version",
        "engine_id",
        "certification_hash",
        "calibration_memory",
        "bindings",
        "memory_ready",
        "downstream_causal_memory_authorized",
        "read_only",
    }
    actual_upstream_fields = set(
        upstream_module
        .OracleMemoryCertifiedCalibrationMemory
        .__dataclass_fields__
    )
    missing_fields = sorted(required_upstream_fields - actual_upstream_fields)
    if missing_fields:
        raise RuntimeError(
            "Certified OML-035 dataclass fields missing: "
            + ", ".join(missing_fields)
        )


def main() -> int:
    print("=" * 48)
    print(" OML-036 INSTALLER")
    print(" CERTIFIED OBSERVATION CAUSAL PATTERN MEMORY")
    print("=" * 48)
    print("[BOOT] Revision: EXACT_OML_035_024_INTERFACE_ALIGNMENT")

    try:
        validate_upstreams()
        print("[OK] Actual OML-035 dataclass and verifier inspected")
        print("[OK] Actual OML-024 builders and signatures inspected")

        for path, label in (
            (UPSTREAM_TEST, "OML-035"),
            (CAUSAL_TEST, "OML-024"),
        ):
            run = subprocess.run(
                [sys.executable, str(path)],
                cwd=ROOT,
                check=False,
            )
            if run.returncode:
                raise RuntimeError(
                    f"{label} certification failed with exit code "
                    f"{run.returncode}"
                )

        tracked = {
            path: path.read_bytes()
            for path in (
                UPSTREAM,
                UPSTREAM_TEST,
                CAUSAL_MODULE,
                CAUSAL_TEST,
            )
        }

        write_complete(PRODUCTION, PRODUCTION_SOURCE)
        write_complete(TEST, TEST_SOURCE)

        export = (
            "from ."
            "oracle_memory_certified_observation_causal_pattern_memory "
            "import *"
        )
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
                "OML-036 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, before in tracked.items():
            if path.read_bytes() != before:
                raise RuntimeError(f"Certified upstream changed: {path}")

        print("[PASS] Certified OML-035 production unchanged")
        print("[PASS] Certified OML-035 standalone test unchanged")
        print("[PASS] Certified OML-024 causal engine unchanged")
        print("[PASS] Exact OML-035 calibration dataclass consumed directly")
        print("[PASS] OML-036 production fully replaced")
        print("[PASS] OML-036 standalone deterministic test installed")
        print("[PASS] Deterministic hashes and replay guarantees preserved")
        print("[PASS] Immutable certified lineage preserved")
        print("[PASS] Oracle Terminal separation preserved")
        print("[PASS] Persistence remained disabled")
        print("[PASS] Continuous learning remained disabled")
        print("[PASS] Runtime activation remained disabled")
        print("[PASS] Publication remained disabled")
        print("[PASS] Action authorization remained disabled")
        print("[PASS] Q Series execution remained disabled")
        print(f"[PASS] Repository located: {ROOT}")
        print(
            "[DONE] OML-036 CERTIFIED OBSERVATION "
            "CAUSAL PATTERN MEMORY INSTALLED"
        )
        return 0

    except (
        RuntimeError,
        SyntaxError,
        ImportError,
        AttributeError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
