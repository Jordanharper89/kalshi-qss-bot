from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_certified_observation_cross_market_dependency_memory import (
    OracleMemoryCertifiedCrossMarketDependencyMemory,
    verify_oracle_memory_certified_cross_market_dependency_memory,
)
from qseries_v2.oracle_memory.oracle_memory_certified_observation_intake_contract import (
    OBSERVATION_KIND_MARKET,
    OracleMemoryCertifiedObservation,
    OracleMemoryObservationIntakeBatch,
    build_oracle_memory_certified_observation,
    build_oracle_memory_observation_intake_batch,
    verify_oracle_memory_certified_observation,
    verify_oracle_memory_observation_intake_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-039"
ENGINE_ID = "OML-039"
POLICY_ID = "oracle-memory.certified-cross-market-observation-intake-bridge.v1"
UPSTREAM_SCHEMA_VERSION = "OML-038"
UPSTREAM_ENGINE_ID = "OML-038"
INTAKE_SCHEMA_VERSION = "OML-027"
INTAKE_ENGINE_ID = "OML-027"
STATE_READ_ONLY = "read_only_intake_bridge"


class OracleMemoryCertifiedCrossMarketIntakeInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketIntakeRequest:
    dependency_id: str
    domain_id: str
    entity_key: str
    source_key: str
    observed_at: str
    effective_at: str
    payload: Mapping[str, Any]
    confidence: float
    uncertainty: float
    request_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedCrossMarketIntakeBinding:
    dependency_id: str
    dependency_hash: str
    observation_id: str
    observation_hash: str
    chain_ids: tuple[str, ...]
    certified_observation_hashes: tuple[str, ...]
    causal_observation_hashes: tuple[str, ...]
    cross_market_observation_hashes: tuple[str, ...]
    upstream_certification_hash: str
    upstream_dependency_memory_hash: str
    intake_batch_hash: str
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    observation_lineage_verified: bool
    source_certification_verified: bool
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
class OracleMemoryCertifiedCrossMarketIntakeBridge:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_dependency_memory_hash: str
    intake_schema_version: str
    intake_engine_id: str
    intake_batch: OracleMemoryObservationIntakeBatch
    bindings: tuple[OracleMemoryCertifiedCrossMarketIntakeBinding, ...]
    dependency_count: int
    observation_count: int
    unique_observation_count: int
    duplicate_observation_count: int
    state: str
    dependency_lineage_verified: bool
    chain_lineage_verified: bool
    certified_observation_lineage_verified: bool
    deterministic_hashing_verified: bool
    canonical_order_verified: bool
    duplicate_detection_verified: bool
    source_certification_verified: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    bridge_ready: bool
    downstream_candidate_materialization_authorized: bool
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
    raise OracleMemoryCertifiedCrossMarketIntakeInvariantError(
        "unsupported OML-039 value type"
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
    raise OracleMemoryCertifiedCrossMarketIntakeInvariantError(reason)


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        _reject(f"OML-039 invalid {label} length")
    try:
        int(value, 16)
    except ValueError as exc:
        raise OracleMemoryCertifiedCrossMarketIntakeInvariantError(
            f"OML-039 invalid {label} hexadecimal value"
        ) from exc


def build_oracle_memory_certified_cross_market_intake_request(
    *,
    dependency_id: str,
    domain_id: str,
    entity_key: str,
    source_key: str,
    observed_at: str,
    effective_at: str,
    payload: Mapping[str, Any],
    confidence: float,
    uncertainty: float,
) -> OracleMemoryCertifiedCrossMarketIntakeRequest:
    _require_hash(dependency_id, "dependency id")
    if domain_id not in MEMORY_DOMAINS:
        _reject("OML-039 unknown memory domain")
    for label, value in (
        ("entity_key", entity_key),
        ("source_key", source_key),
        ("observed_at", observed_at),
        ("effective_at", effective_at),
    ):
        if not isinstance(value, str) or not value.strip():
            _reject(f"OML-039 {label} required")
    if not isinstance(payload, Mapping):
        _reject("OML-039 payload must be a mapping")
    confidence = float(confidence)
    uncertainty = float(uncertainty)
    if not 0.0 <= confidence <= 1.0:
        _reject("OML-039 confidence outside [0, 1]")
    if not 0.0 <= uncertainty <= 1.0:
        _reject("OML-039 uncertainty outside [0, 1]")
    body = {
        "dependency_id": dependency_id,
        "domain_id": domain_id,
        "entity_key": entity_key.strip(),
        "source_key": source_key.strip(),
        "observed_at": observed_at.strip(),
        "effective_at": effective_at.strip(),
        "payload": _canonical(payload),
        "confidence": confidence,
        "uncertainty": uncertainty,
    }
    result = OracleMemoryCertifiedCrossMarketIntakeRequest(
        **body,
        request_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_intake_request(result)
    return result


def verify_oracle_memory_certified_cross_market_intake_request(
    request: OracleMemoryCertifiedCrossMarketIntakeRequest,
) -> bool:
    body = asdict(request)
    supplied = body.pop("request_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-039 request hash mismatch")
    _require_hash(request.dependency_id, "dependency id")
    _require_hash(request.request_hash, "request hash")
    if request.domain_id not in MEMORY_DOMAINS:
        _reject("OML-039 request domain invalid")
    return True


def _build_binding(
    *,
    dependency,
    upstream_binding,
    observation: OracleMemoryCertifiedObservation,
    upstream: OracleMemoryCertifiedCrossMarketDependencyMemory,
    intake_batch: OracleMemoryObservationIntakeBatch,
) -> OracleMemoryCertifiedCrossMarketIntakeBinding:
    body = {
        "dependency_id": dependency.dependency_id,
        "dependency_hash": dependency.dependency_hash,
        "observation_id": observation.observation_id,
        "observation_hash": observation.observation_hash,
        "chain_ids": upstream_binding.chain_ids,
        "certified_observation_hashes": upstream_binding.certified_observation_hashes,
        "causal_observation_hashes": upstream_binding.causal_observation_hashes,
        "cross_market_observation_hashes": upstream_binding.cross_market_observation_hashes,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_dependency_memory_hash": upstream.dependency_memory.memory_hash,
        "intake_batch_hash": intake_batch.batch_hash,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "observation_lineage_verified": True,
        "source_certification_verified": True,
        "deterministic_binding_verified": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketIntakeBinding(
        **body,
        binding_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_intake_binding(result)
    return result


def verify_oracle_memory_certified_cross_market_intake_binding(
    binding: OracleMemoryCertifiedCrossMarketIntakeBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-039 binding hash mismatch")
    for value in (
        binding.dependency_id,
        binding.dependency_hash,
        binding.observation_id,
        binding.observation_hash,
        binding.upstream_certification_hash,
        binding.upstream_dependency_memory_hash,
        binding.intake_batch_hash,
        binding.binding_hash,
        *binding.chain_ids,
        *binding.certified_observation_hashes,
        *binding.causal_observation_hashes,
        *binding.cross_market_observation_hashes,
    ):
        _require_hash(value, "binding lineage hash")
    if not all((
        binding.dependency_lineage_verified,
        binding.chain_lineage_verified,
        binding.observation_lineage_verified,
        binding.source_certification_verified,
        binding.deterministic_binding_verified,
        binding.read_only,
    )):
        _reject("OML-039 binding guarantee missing")
    if any((
        binding.persistence_authorized,
        binding.learning_update_authorized,
        binding.runtime_activation_authorized,
        binding.publication_authorized,
        binding.action_authorization_enabled,
        binding.qseries_execution_authorized,
    )):
        _reject("OML-039 forbidden binding capability enabled")
    return True


def build_oracle_memory_certified_cross_market_intake_bridge(
    *,
    dependencies: OracleMemoryCertifiedCrossMarketDependencyMemory,
    requests: Sequence[OracleMemoryCertifiedCrossMarketIntakeRequest],
) -> OracleMemoryCertifiedCrossMarketIntakeBridge:
    verify_oracle_memory_certified_cross_market_dependency_memory(dependencies)
    if dependencies.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-039 upstream schema mismatch")
    if dependencies.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-039 upstream engine mismatch")
    if not dependencies.memory_ready:
        _reject("OML-039 upstream dependency memory not ready")
    if not dependencies.downstream_market_behavior_authorized:
        _reject("OML-039 downstream continuation not authorized")
    if not dependencies.read_only:
        _reject("OML-039 upstream dependency memory not read-only")

    dependency_by_id = {
        item.dependency_id: item
        for item in dependencies.dependency_memory.dependencies
    }
    binding_by_id = {
        item.dependency_id: item for item in dependencies.bindings
    }
    if set(dependency_by_id) != set(binding_by_id):
        _reject("OML-039 upstream dependency/binding mismatch")

    observations = []
    lineage_by_observation_hash = {}
    seen_requests = set()

    for request in requests:
        verify_oracle_memory_certified_cross_market_intake_request(request)
        if request.request_hash in seen_requests:
            _reject("OML-039 duplicate intake request")
        seen_requests.add(request.request_hash)

        dependency = dependency_by_id.get(request.dependency_id)
        upstream_binding = binding_by_id.get(request.dependency_id)
        if dependency is None or upstream_binding is None:
            _reject("OML-039 unknown dependency id")

        evidence = tuple(sorted(set(
            upstream_binding.certified_observation_hashes
            + upstream_binding.cross_market_observation_hashes
        )))
        parents = tuple(sorted(set(
            upstream_binding.causal_observation_hashes
        )))
        payload = {
            **dict(request.payload),
            "dependency_id": dependency.dependency_id,
            "dependency_hash": dependency.dependency_hash,
            "dependency_name": dependency.dependency_name,
            "dependency_status": dependency.dependency_status,
            "source_market_id": dependency.source_market_id,
            "target_market_id": dependency.target_market_id,
            "average_lag_seconds": dependency.average_lag_seconds,
            "empirical_support_rate": dependency.empirical_support_rate,
            "chain_ids": upstream_binding.chain_ids,
        }

        observation = build_oracle_memory_certified_observation(
            observation_kind=OBSERVATION_KIND_MARKET,
            domain_id=request.domain_id,
            entity_key=request.entity_key,
            source_key=request.source_key,
            observed_at=request.observed_at,
            effective_at=request.effective_at,
            payload=payload,
            evidence_hashes=evidence,
            parent_observation_hashes=parents,
            source_certification_hash=dependencies.certification_hash,
            confidence=request.confidence,
            uncertainty=request.uncertainty,
            contradiction_count=dependency.total_contradiction_depth,
        )
        verify_oracle_memory_certified_observation(observation)
        observations.append(observation)
        lineage_by_observation_hash[observation.observation_hash] = (
            dependency,
            upstream_binding,
        )

    if not observations:
        _reject("OML-039 at least one intake request required")

    intake_batch = build_oracle_memory_observation_intake_batch(
        cross_market_memory=dependencies.dependency_memory,
        observations=tuple(observations),
    )
    verify_oracle_memory_observation_intake_batch(intake_batch)

    if intake_batch.schema_version != INTAKE_SCHEMA_VERSION:
        _reject("OML-039 intake schema mismatch")
    if intake_batch.engine_id != INTAKE_ENGINE_ID:
        _reject("OML-039 intake engine mismatch")

    bindings = tuple(
        _build_binding(
            dependency=lineage_by_observation_hash[item.observation_hash][0],
            upstream_binding=lineage_by_observation_hash[item.observation_hash][1],
            observation=item,
            upstream=dependencies,
            intake_batch=intake_batch,
        )
        for item in intake_batch.observations
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": dependencies.schema_version,
        "upstream_engine_id": dependencies.engine_id,
        "upstream_certification_hash": dependencies.certification_hash,
        "upstream_dependency_memory_hash": dependencies.dependency_memory.memory_hash,
        "intake_schema_version": intake_batch.schema_version,
        "intake_engine_id": intake_batch.engine_id,
        "intake_batch": intake_batch,
        "bindings": bindings,
        "dependency_count": len(dependency_by_id),
        "observation_count": intake_batch.observation_count,
        "unique_observation_count": intake_batch.unique_observation_count,
        "duplicate_observation_count": intake_batch.duplicate_observation_count,
        "state": STATE_READ_ONLY,
        "dependency_lineage_verified": True,
        "chain_lineage_verified": True,
        "certified_observation_lineage_verified": True,
        "deterministic_hashing_verified": intake_batch.deterministic_hashing_verified,
        "canonical_order_verified": intake_batch.canonical_order_verified,
        "duplicate_detection_verified": intake_batch.duplicate_detection_verified,
        "source_certification_verified": intake_batch.source_certification_verified,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "bridge_ready": True,
        "downstream_candidate_materialization_authorized": False,
        "read_only": True,
    }
    result = OracleMemoryCertifiedCrossMarketIntakeBridge(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_oracle_memory_certified_cross_market_intake_bridge(result)
    return result


def verify_oracle_memory_certified_cross_market_intake_bridge(
    result: OracleMemoryCertifiedCrossMarketIntakeBridge,
) -> bool:
    body = asdict(result)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        _reject("OML-039 certification hash mismatch")
    if result.schema_version != SCHEMA_VERSION:
        _reject("OML-039 schema mismatch")
    if result.engine_id != ENGINE_ID:
        _reject("OML-039 engine mismatch")
    if result.policy_id != POLICY_ID:
        _reject("OML-039 policy mismatch")
    if result.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-039 subsystem mismatch")
    if result.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-039 upstream schema lineage mismatch")
    if result.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-039 upstream engine lineage mismatch")
    if result.intake_schema_version != INTAKE_SCHEMA_VERSION:
        _reject("OML-039 intake schema lineage mismatch")
    if result.intake_engine_id != INTAKE_ENGINE_ID:
        _reject("OML-039 intake engine lineage mismatch")

    verify_oracle_memory_observation_intake_batch(result.intake_batch)

    if result.upstream_dependency_memory_hash != (
        result.intake_batch.upstream_memory_hash
    ):
        _reject("OML-039 dependency-to-intake lineage mismatch")
    if result.observation_count != len(result.bindings):
        _reject("OML-039 observation/binding count mismatch")
    if result.observation_count != result.intake_batch.observation_count:
        _reject("OML-039 observation count mismatch")

    observation_ids = tuple(
        item.observation_id for item in result.intake_batch.observations
    )
    binding_ids = tuple(item.observation_id for item in result.bindings)
    if observation_ids != binding_ids:
        _reject("OML-039 observation binding order mismatch")

    for binding in result.bindings:
        verify_oracle_memory_certified_cross_market_intake_binding(binding)
        if binding.upstream_certification_hash != (
            result.upstream_certification_hash
        ):
            _reject("OML-039 binding certification lineage mismatch")
        if binding.upstream_dependency_memory_hash != (
            result.upstream_dependency_memory_hash
        ):
            _reject("OML-039 binding dependency lineage mismatch")
        if binding.intake_batch_hash != result.intake_batch.batch_hash:
            _reject("OML-039 binding intake lineage mismatch")

    if not all((
        result.dependency_lineage_verified,
        result.chain_lineage_verified,
        result.certified_observation_lineage_verified,
        result.deterministic_hashing_verified,
        result.canonical_order_verified,
        result.duplicate_detection_verified,
        result.source_certification_verified,
        result.bridge_ready,
        result.read_only,
    )):
        _reject("OML-039 guarantee missing")
    if result.state != STATE_READ_ONLY:
        _reject("OML-039 state invalid")
    if result.downstream_candidate_materialization_authorized:
        _reject("OML-039 candidate materialization must remain disabled")
    if any((
        result.persistence_enabled,
        result.learning_updates_enabled,
        result.runtime_activation_enabled,
        result.publication_enabled,
        result.action_authorization_enabled,
        result.qseries_execution_enabled,
    )):
        _reject("OML-039 forbidden capability enabled")
    return True
