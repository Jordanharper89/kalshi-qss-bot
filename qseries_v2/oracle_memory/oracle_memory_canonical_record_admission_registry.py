from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_contract_admission_gate import (
    OracleMemoryCanonicalRecordContractAdmissionDecision,
    verify_oracle_memory_canonical_record_contract_admission_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-007"
ENGINE_ID = "OML-007"
POLICY_ID = "oracle-memory.canonical-record-admission-registry.v1"

UPSTREAM_SCHEMA_VERSION = "OML-006"
UPSTREAM_ENGINE_ID = "OML-006"
REGISTRY_STATUS_CERTIFIED = "certified_inactive"


class OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordAdmissionEntry:
    domain_id: str
    ordinal: int
    upstream_contract_admission_hash: str
    canonical_record_contract_admitted: bool
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    entry_hash: str


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordAdmissionRegistry:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_decision_hash: str
    upstream_certification_hash: str
    upstream_admission_hash: str
    upstream_registry_hash: str
    registry_status: str
    entries: tuple[OracleMemoryCanonicalRecordAdmissionEntry, ...]
    entry_count: int
    domain_order_canonical: bool
    identities_unique: bool
    all_contracts_admitted: bool
    all_entries_inactive: bool
    all_entries_non_writing: bool
    all_entries_read_only: bool
    publication_disabled: bool
    action_authorization_disabled: bool
    qseries_execution_disabled: bool
    next_certification_authorized: bool
    registry_hash: str


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

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
        "unsupported OML-007 value type: "
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
    raise OracleMemoryCanonicalRecordAdmissionRegistryInvariantError(
        reason
    )


def _build_entry(
    *,
    domain_id: str,
    ordinal: int,
    upstream_contract_admission_hash: str,
) -> OracleMemoryCanonicalRecordAdmissionEntry:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "upstream_contract_admission_hash": (
            upstream_contract_admission_hash
        ),
        "canonical_record_contract_admitted": True,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryCanonicalRecordAdmissionEntry(
        **body,
        entry_hash=_stable_hash(body),
    )


def verify_oracle_memory_canonical_record_admission_entry(
    entry: OracleMemoryCanonicalRecordAdmissionEntry,
) -> bool:
    body = asdict(entry)
    supplied = body.pop("entry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-007 admission entry hash mismatch")

    if entry.domain_id not in MEMORY_DOMAINS:
        _reject("OML-007 unknown memory domain")

    if entry.ordinal != MEMORY_DOMAINS.index(entry.domain_id) + 1:
        _reject("OML-007 domain ordinal mismatch")

    if len(entry.upstream_contract_admission_hash) != 64:
        _reject("OML-007 upstream admission hash invalid")

    if not entry.canonical_record_contract_admitted:
        _reject("OML-007 record contract not admitted")

    forbidden = (
        entry.persistent_storage_authorized,
        entry.learning_update_authorized,
        entry.runtime_activation_authorized,
        entry.publication_authorized,
        entry.action_authorization_enabled,
        entry.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-007 forbidden entry capability enabled")

    if not entry.read_only:
        _reject("OML-007 entry is not read-only")

    return True


def build_oracle_memory_canonical_record_admission_registry(
    *,
    admission_decision: OracleMemoryCanonicalRecordContractAdmissionDecision,
) -> OracleMemoryCanonicalRecordAdmissionRegistry:
    verify_oracle_memory_canonical_record_contract_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-007 upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-007 upstream engine mismatch")

    if not admission_decision.admitted:
        _reject("OML-007 upstream contract not admitted")

    if not admission_decision.next_certification_authorized:
        _reject("OML-007 upstream continuation not authorized")

    if not admission_decision.read_only:
        _reject("OML-007 upstream read-only guarantee missing")

    if admission_decision.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-007 upstream domain identity mismatch")

    entries = tuple(
        _build_entry(
            domain_id=domain_id,
            ordinal=index,
            upstream_contract_admission_hash=(
                admission_decision.decision_hash
            ),
        )
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for entry in entries:
        verify_oracle_memory_canonical_record_admission_entry(entry)

    domain_ids = tuple(entry.domain_id for entry in entries)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_decision.schema_version,
        "upstream_engine_id": admission_decision.engine_id,
        "upstream_decision_hash": admission_decision.decision_hash,
        "upstream_certification_hash": (
            admission_decision.upstream_certification_hash
        ),
        "upstream_admission_hash": (
            admission_decision.upstream_admission_hash
        ),
        "upstream_registry_hash": (
            admission_decision.upstream_registry_hash
        ),
        "registry_status": REGISTRY_STATUS_CERTIFIED,
        "entries": entries,
        "entry_count": len(entries),
        "domain_order_canonical": domain_ids == MEMORY_DOMAINS,
        "identities_unique": len(set(domain_ids)) == len(domain_ids),
        "all_contracts_admitted": all(
            entry.canonical_record_contract_admitted
            for entry in entries
        ),
        "all_entries_inactive": all(
            not entry.runtime_activation_authorized
            for entry in entries
        ),
        "all_entries_non_writing": all(
            not entry.persistent_storage_authorized
            and not entry.learning_update_authorized
            for entry in entries
        ),
        "all_entries_read_only": all(
            entry.read_only
            for entry in entries
        ),
        "publication_disabled": all(
            not entry.publication_authorized
            for entry in entries
        ),
        "action_authorization_disabled": all(
            not entry.action_authorization_enabled
            for entry in entries
        ),
        "qseries_execution_disabled": all(
            not entry.qseries_execution_authorized
            for entry in entries
        ),
        "next_certification_authorized": True,
    }

    registry = OracleMemoryCanonicalRecordAdmissionRegistry(
        **body,
        registry_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_admission_registry(registry)
    return registry


def verify_oracle_memory_canonical_record_admission_registry(
    registry: OracleMemoryCanonicalRecordAdmissionRegistry,
) -> bool:
    body = asdict(registry)
    supplied = body.pop("registry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-007 registry hash mismatch")

    if registry.schema_version != SCHEMA_VERSION:
        _reject("OML-007 schema mismatch")

    if registry.engine_id != ENGINE_ID:
        _reject("OML-007 engine mismatch")

    if registry.policy_id != POLICY_ID:
        _reject("OML-007 policy mismatch")

    if registry.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-007 subsystem mismatch")

    if registry.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-007 upstream schema lineage mismatch")

    if registry.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-007 upstream engine lineage mismatch")

    hashes = (
        registry.upstream_decision_hash,
        registry.upstream_certification_hash,
        registry.upstream_admission_hash,
        registry.upstream_registry_hash,
        registry.registry_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-007 lineage hash length invalid")

    if registry.registry_status != REGISTRY_STATUS_CERTIFIED:
        _reject("OML-007 registry status mismatch")

    if registry.entry_count != len(MEMORY_DOMAINS):
        _reject("OML-007 registry entry count mismatch")

    if tuple(entry.domain_id for entry in registry.entries) != MEMORY_DOMAINS:
        _reject("OML-007 registry domain order mismatch")

    for entry in registry.entries:
        verify_oracle_memory_canonical_record_admission_entry(entry)

    required_true = (
        registry.domain_order_canonical,
        registry.identities_unique,
        registry.all_contracts_admitted,
        registry.all_entries_inactive,
        registry.all_entries_non_writing,
        registry.all_entries_read_only,
        registry.publication_disabled,
        registry.action_authorization_disabled,
        registry.qseries_execution_disabled,
        registry.next_certification_authorized,
    )

    if not all(required_true):
        _reject("OML-007 registry guarantee missing")

    return True
