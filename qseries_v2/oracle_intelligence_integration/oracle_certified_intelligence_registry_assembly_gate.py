from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

ENGINE_ID = "INT-OII-001"
SCHEMA_VERSION = "INT-OII-001.v1"
ALGORITHM_VERSION = "oracle-certified-intelligence-registry-assembly.v1"
REGISTRY_STATUS = "oracle_certified_intelligence_registry_assembled"


class OracleCertifiedIntelligenceRegistryInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _snapshot(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    data = getattr(value, "__dict__", None)
    if isinstance(data, dict):
        return dict(data)
    raise OracleCertifiedIntelligenceRegistryInvariantError("record cannot be snapshotted")


def _identity(snapshot: Mapping[str, Any]) -> tuple[str, str]:
    id_names = (
        "terminal_certification_id", "consumption_id", "certification_id",
        "freeze_id", "record_id", "registry_id",
    )
    hash_names = (
        "terminal_certification_hash", "consumption_hash", "certification_hash",
        "freeze_hash", "record_hash", "registry_hash",
    )
    record_id = next((str(snapshot[n]) for n in id_names if snapshot.get(n)), "")
    record_hash = next((str(snapshot[n]) for n in hash_names if snapshot.get(n)), "")
    if not record_id or not record_hash:
        raise OracleCertifiedIntelligenceRegistryInvariantError("source identity/hash unavailable")
    return record_id, record_hash


@dataclass(frozen=True)
class OracleCertifiedIntelligenceRegistryEntry:
    subsystem_key: str
    engine_id: str
    source_record_id: str
    source_record_hash: str
    verified: bool
    read_only_verified: bool
    mutation_allowed: bool
    execution_allowed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    entry_hash: str


@dataclass(frozen=True)
class OracleCertifiedIntelligenceRegistry:
    registry_id: str
    entries: tuple[OracleCertifiedIntelligenceRegistryEntry, ...]
    entry_count: int
    deterministic_registration_order: bool
    exact_source_hashes_preserved: bool
    duplicate_subsystems_rejected: bool
    immutable_registry: bool
    downstream_read_only_consumption_allowed: bool
    registry_mutation_allowed: bool
    oracle_execution_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    read_only: bool
    registry_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    registry_hash: str


def _entry(*, subsystem_key: str, record: Any, verifier) -> OracleCertifiedIntelligenceRegistryEntry:
    try:
        verdict = verifier(record)
    except Exception as exc:
        raise OracleCertifiedIntelligenceRegistryInvariantError(
            f"{subsystem_key} source verification failed"
        ) from exc
    if verdict is False:
        raise OracleCertifiedIntelligenceRegistryInvariantError(
            f"{subsystem_key} source verifier returned false"
        )
    snapshot = _snapshot(record)
    if snapshot.get("read_only") is not True:
        raise OracleCertifiedIntelligenceRegistryInvariantError(
            f"{subsystem_key} source is not read-only"
        )
    source_id, source_hash = _identity(snapshot)
    body = {
        "subsystem_key": subsystem_key,
        "engine_id": str(snapshot.get("engine_id", subsystem_key)),
        "source_record_id": source_id,
        "source_record_hash": source_hash,
        "verified": True,
        "read_only_verified": True,
        "mutation_allowed": False,
        "execution_allowed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
    }
    return OracleCertifiedIntelligenceRegistryEntry(**body, entry_hash=stable_hash(body))


def assemble_oracle_certified_intelligence_registry(
    *,
    oii_terminal_certification: Any,
    oii_terminal_verifier,
    osr_terminal_consumption: Any,
    osr_terminal_consumption_verifier,
) -> OracleCertifiedIntelligenceRegistry:
    entries = tuple(sorted((
        _entry(
            subsystem_key="oracle_intelligence_integration",
            record=oii_terminal_certification,
            verifier=oii_terminal_verifier,
        ),
        _entry(
            subsystem_key="oracle_scientific_reasoning_runtime",
            record=osr_terminal_consumption,
            verifier=osr_terminal_consumption_verifier,
        ),
    ), key=lambda e: e.subsystem_key))

    keys = [entry.subsystem_key for entry in entries]
    if len(keys) != len(set(keys)):
        raise OracleCertifiedIntelligenceRegistryInvariantError("duplicate subsystem registration")

    body = {
        "entries": entries,
        "entry_count": len(entries),
        "deterministic_registration_order": True,
        "exact_source_hashes_preserved": True,
        "duplicate_subsystems_rejected": True,
        "immutable_registry": True,
        "downstream_read_only_consumption_allowed": True,
        "registry_mutation_allowed": False,
        "oracle_execution_allowed": False,
        "publication_allowed": False,
        "alerting_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "read_only": True,
        "registry_status": REGISTRY_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    registry_hash = stable_hash(body)
    return OracleCertifiedIntelligenceRegistry(
        registry_id="oracle-certified-intelligence-registry:" + registry_hash,
        **body,
        registry_hash=registry_hash,
    )


def verify_oracle_certified_intelligence_registry(
    registry: OracleCertifiedIntelligenceRegistry,
) -> bool:
    if not isinstance(registry, OracleCertifiedIntelligenceRegistry):
        raise OracleCertifiedIntelligenceRegistryInvariantError("invalid registry record")
    if registry.entries != tuple(sorted(registry.entries, key=lambda e: e.subsystem_key)):
        raise OracleCertifiedIntelligenceRegistryInvariantError("registry order mismatch")
    if len({e.subsystem_key for e in registry.entries}) != len(registry.entries):
        raise OracleCertifiedIntelligenceRegistryInvariantError("duplicate registry entries")

    for entry in registry.entries:
        body = {k: v for k, v in asdict(entry).items() if k != "entry_hash"}
        if entry.entry_hash != stable_hash(body):
            raise OracleCertifiedIntelligenceRegistryInvariantError("entry hash mismatch")
        if (
            entry.verified is not True
            or entry.read_only_verified is not True
            or entry.mutation_allowed
            or entry.execution_allowed
            or entry.publication_allowed
            or entry.qseries_execution_allowed
        ):
            raise OracleCertifiedIntelligenceRegistryInvariantError("entry safety boundary violated")

    body = {k: v for k, v in asdict(registry).items() if k not in {"registry_id", "registry_hash"}}
    expected_hash = stable_hash(body)
    if registry.registry_hash != expected_hash:
        raise OracleCertifiedIntelligenceRegistryInvariantError("registry hash mismatch")
    if registry.registry_id != "oracle-certified-intelligence-registry:" + expected_hash:
        raise OracleCertifiedIntelligenceRegistryInvariantError("registry identity mismatch")

    forbidden = (
        registry.registry_mutation_allowed,
        registry.oracle_execution_allowed,
        registry.publication_allowed,
        registry.alerting_allowed,
        registry.qseries_execution_allowed,
        registry.order_creation_allowed,
        registry.funds_movement_allowed,
        registry.portfolio_mutation_allowed,
    )
    if (
        registry.entry_count != 2
        or registry.entry_count != len(registry.entries)
        or registry.deterministic_registration_order is not True
        or registry.exact_source_hashes_preserved is not True
        or registry.duplicate_subsystems_rejected is not True
        or registry.immutable_registry is not True
        or registry.downstream_read_only_consumption_allowed is not True
        or registry.read_only is not True
        or registry.engine_id != ENGINE_ID
        or registry.schema_version != SCHEMA_VERSION
        or registry.algorithm_version != ALGORITHM_VERSION
        or registry.registry_status != REGISTRY_STATUS
        or any(forbidden)
    ):
        raise OracleCertifiedIntelligenceRegistryInvariantError("INT-OII-001 safety boundary violated")
    return True


def serialize_oracle_certified_intelligence_registry(
    registry: OracleCertifiedIntelligenceRegistry,
) -> str:
    verify_oracle_certified_intelligence_registry(registry)
    return canonical_json(registry)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "REGISTRY_STATUS",
    "OracleCertifiedIntelligenceRegistryInvariantError",
    "OracleCertifiedIntelligenceRegistryEntry",
    "OracleCertifiedIntelligenceRegistry",
    "assemble_oracle_certified_intelligence_registry",
    "verify_oracle_certified_intelligence_registry",
    "serialize_oracle_certified_intelligence_registry",
]
