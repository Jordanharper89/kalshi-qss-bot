from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_candidate_validation_and_deduplication import (
    STATUS_VALID,
    OracleMemoryCandidateValidationBatch,
    OracleMemoryCandidateValidationResult,
    verify_oracle_memory_candidate_validation_batch,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-018"
ENGINE_ID = "OML-018"
POLICY_ID = "oracle-memory.entity-resolution.v1"

UPSTREAM_SCHEMA_VERSION = "OML-017"
UPSTREAM_ENGINE_ID = "OML-017"

RESOLUTION_STATUS_RESOLVED = "resolved"
RESOLUTION_STATUS_REJECTED_DUPLICATE = "rejected_duplicate"


class OracleMemoryEntityResolutionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryEntityAlias:
    alias: str
    normalized_alias: str
    alias_hash: str


@dataclass(frozen=True)
class OracleMemoryResolvedEntity:
    canonical_entity_id: str
    domain_id: str
    canonical_name: str
    normalized_name: str
    aliases: tuple[OracleMemoryEntityAlias, ...]
    source_candidate_hash: str
    source_validation_result_hash: str
    resolution_status: str
    deterministic_identity_verified: bool
    alias_uniqueness_verified: bool
    canonical_name_verified: bool
    duplicate_candidate_rejected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    entity_hash: str


@dataclass(frozen=True)
class OracleMemoryEntityResolutionBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_batch_hash: str
    entities: tuple[OracleMemoryResolvedEntity, ...]
    resolved_entity_count: int
    rejected_duplicate_count: int
    canonical_order_verified: bool
    deterministic_resolution_verified: bool
    alias_normalization_verified: bool
    entity_identity_uniqueness_verified: bool
    duplicate_candidates_excluded: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    batch_ready: bool
    next_certification_authorized: bool
    read_only: bool
    batch_hash: str


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

    raise OracleMemoryEntityResolutionInvariantError(
        "unsupported OML-018 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def _reject(reason: str) -> None:
    raise OracleMemoryEntityResolutionInvariantError(reason)


def _normalize(value: str) -> str:
    normalized = " ".join(value.strip().lower().split())

    if not normalized:
        _reject("OML-018 normalized value cannot be empty")

    return normalized


def _build_alias(value: str) -> OracleMemoryEntityAlias:
    normalized = _normalize(value)

    body = {
        "alias": value.strip(),
        "normalized_alias": normalized,
    }

    return OracleMemoryEntityAlias(
        **body,
        alias_hash=_stable_hash(body),
    )


def verify_oracle_memory_entity_alias(
    alias: OracleMemoryEntityAlias,
) -> bool:
    body = asdict(alias)
    supplied = body.pop("alias_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 alias hash mismatch")

    if alias.normalized_alias != _normalize(alias.alias):
        _reject("OML-018 alias normalization mismatch")

    return True


def _build_entity(
    result: OracleMemoryCandidateValidationResult,
    *,
    aliases: Sequence[str],
) -> OracleMemoryResolvedEntity:
    if result.status != STATUS_VALID:
        _reject("OML-018 only valid candidates can resolve entities")

    if result.domain_id not in MEMORY_DOMAINS:
        _reject("OML-018 unknown memory domain")

    canonical_name = result.entity_key.strip()
    normalized_name = _normalize(canonical_name)

    alias_values = tuple(
        sorted(
            {
                canonical_name,
                *(
                    alias.strip()
                    for alias in aliases
                    if isinstance(alias, str) and alias.strip()
                ),
            },
            key=lambda item: _normalize(item),
        )
    )

    alias_objects = tuple(_build_alias(item) for item in alias_values)
    normalized_aliases = tuple(
        item.normalized_alias for item in alias_objects
    )

    canonical_entity_id = hashlib.sha256(
        (
            f"{result.domain_id}|{normalized_name}"
        ).encode("utf-8")
    ).hexdigest()

    body = {
        "canonical_entity_id": canonical_entity_id,
        "domain_id": result.domain_id,
        "canonical_name": canonical_name,
        "normalized_name": normalized_name,
        "aliases": alias_objects,
        "source_candidate_hash": result.candidate_hash,
        "source_validation_result_hash": result.result_hash,
        "resolution_status": RESOLUTION_STATUS_RESOLVED,
        "deterministic_identity_verified": True,
        "alias_uniqueness_verified": (
            len(set(normalized_aliases)) == len(normalized_aliases)
        ),
        "canonical_name_verified": (
            normalized_name in normalized_aliases
        ),
        "duplicate_candidate_rejected": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    entity = OracleMemoryResolvedEntity(
        **body,
        entity_hash=_stable_hash(body),
    )

    verify_oracle_memory_resolved_entity(entity)
    return entity


def verify_oracle_memory_resolved_entity(
    entity: OracleMemoryResolvedEntity,
) -> bool:
    body = asdict(entity)
    supplied = body.pop("entity_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 entity hash mismatch")

    if entity.domain_id not in MEMORY_DOMAINS:
        _reject("OML-018 entity domain mismatch")

    if entity.normalized_name != _normalize(entity.canonical_name):
        _reject("OML-018 canonical-name normalization mismatch")

    expected_id = hashlib.sha256(
        (
            f"{entity.domain_id}|{entity.normalized_name}"
        ).encode("utf-8")
    ).hexdigest()

    if entity.canonical_entity_id != expected_id:
        _reject("OML-018 canonical entity identity mismatch")

    for alias in entity.aliases:
        verify_oracle_memory_entity_alias(alias)

    normalized_aliases = tuple(
        alias.normalized_alias for alias in entity.aliases
    )

    if len(set(normalized_aliases)) != len(normalized_aliases):
        _reject("OML-018 duplicate aliases detected")

    if entity.normalized_name not in normalized_aliases:
        _reject("OML-018 canonical name missing from aliases")

    required_true = (
        entity.deterministic_identity_verified,
        entity.alias_uniqueness_verified,
        entity.canonical_name_verified,
        entity.duplicate_candidate_rejected,
        entity.read_only,
    )

    if not all(required_true):
        _reject("OML-018 entity resolution guarantee missing")

    forbidden = (
        entity.persistence_authorized,
        entity.learning_update_authorized,
        entity.runtime_activation_authorized,
        entity.publication_authorized,
        entity.action_authorization_enabled,
        entity.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-018 forbidden entity capability enabled")

    return True


def build_oracle_memory_entity_resolution_batch(
    *,
    validation_batch: OracleMemoryCandidateValidationBatch,
    aliases_by_candidate_hash: Mapping[str, Sequence[str]] | None = None,
) -> OracleMemoryEntityResolutionBatch:
    verify_oracle_memory_candidate_validation_batch(validation_batch)

    if validation_batch.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-018 upstream schema mismatch")

    if validation_batch.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-018 upstream engine mismatch")

    if not validation_batch.batch_ready:
        _reject("OML-018 upstream validation batch not ready")

    if not validation_batch.next_certification_authorized:
        _reject("OML-018 upstream continuation not authorized")

    if not validation_batch.read_only:
        _reject("OML-018 upstream read-only guarantee missing")

    alias_map = aliases_by_candidate_hash or {}

    valid_results = tuple(
        result
        for result in validation_batch.results
        if result.status == STATUS_VALID
    )

    entities = tuple(
        sorted(
            (
                _build_entity(
                    result,
                    aliases=alias_map.get(result.candidate_hash, ()),
                )
                for result in valid_results
            ),
            key=lambda item: (
                MEMORY_DOMAINS.index(item.domain_id),
                item.normalized_name,
                item.canonical_entity_id,
            ),
        )
    )

    entity_ids = tuple(
        entity.canonical_entity_id for entity in entities
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": validation_batch.schema_version,
        "upstream_engine_id": validation_batch.engine_id,
        "upstream_batch_hash": validation_batch.batch_hash,
        "entities": entities,
        "resolved_entity_count": len(entities),
        "rejected_duplicate_count": (
            validation_batch.duplicate_candidate_count
        ),
        "canonical_order_verified": True,
        "deterministic_resolution_verified": True,
        "alias_normalization_verified": True,
        "entity_identity_uniqueness_verified": (
            len(set(entity_ids)) == len(entity_ids)
        ),
        "duplicate_candidates_excluded": (
            len(valid_results)
            + validation_batch.duplicate_candidate_count
            == validation_batch.candidate_count
        ),
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "batch_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    batch = OracleMemoryEntityResolutionBatch(
        **body,
        batch_hash=_stable_hash(body),
    )

    verify_oracle_memory_entity_resolution_batch(batch)
    return batch


def verify_oracle_memory_entity_resolution_batch(
    batch: OracleMemoryEntityResolutionBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-018 batch hash mismatch")

    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-018 batch schema mismatch")

    if batch.engine_id != ENGINE_ID:
        _reject("OML-018 batch engine mismatch")

    if batch.policy_id != POLICY_ID:
        _reject("OML-018 batch policy mismatch")

    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-018 batch subsystem mismatch")

    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-018 upstream schema lineage mismatch")

    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-018 upstream engine lineage mismatch")

    if batch.resolved_entity_count != len(batch.entities):
        _reject("OML-018 resolved entity count mismatch")

    for entity in batch.entities:
        verify_oracle_memory_resolved_entity(entity)

    entity_ids = tuple(
        entity.canonical_entity_id for entity in batch.entities
    )

    if len(set(entity_ids)) != len(entity_ids):
        _reject("OML-018 duplicate canonical entity identities")

    required_true = (
        batch.canonical_order_verified,
        batch.deterministic_resolution_verified,
        batch.alias_normalization_verified,
        batch.entity_identity_uniqueness_verified,
        batch.duplicate_candidates_excluded,
        batch.batch_ready,
        batch.next_certification_authorized,
        batch.read_only,
    )

    if not all(required_true):
        _reject("OML-018 batch guarantee missing")

    forbidden = (
        batch.persistence_enabled,
        batch.learning_updates_enabled,
        batch.runtime_activation_enabled,
        batch.publication_enabled,
        batch.action_authorization_enabled,
        batch.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-018 forbidden batch capability enabled")

    return True
