from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_admission_registry import (
    ENGINE_ID as OML_007_ENGINE_ID,
    POLICY_ID as OML_007_POLICY_ID,
    REGISTRY_STATUS_CERTIFIED,
    SCHEMA_VERSION as OML_007_SCHEMA_VERSION,
    OracleMemoryCanonicalRecordAdmissionRegistry,
    verify_oracle_memory_canonical_record_admission_registry,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-008"
ENGINE_ID = "OML-008"
POLICY_ID = "oracle-memory.canonical-record-admission-registry-gate.v1"

UPSTREAM_SCHEMA_VERSION = "OML-007"
UPSTREAM_ENGINE_ID = "OML-007"
UPSTREAM_POLICY_ID = (
    "oracle-memory.canonical-record-admission-registry.v1"
)

GATE_STATUS_ADMITTED = "admitted"


class OracleMemoryCanonicalRecordAdmissionRegistryGateInvariantError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class OracleMemoryCanonicalRecordAdmissionRegistryGateDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_registry_hash: str
    upstream_decision_hash: str
    upstream_certification_hash: str
    upstream_admission_hash: str
    upstream_domain_registry_hash: str
    admitted_domain_ids: tuple[str, ...]
    admitted_entry_hashes: tuple[str, ...]
    admitted_entry_count: int
    registry_verified: bool
    registry_status_verified: bool
    upstream_identity_verified: bool
    upstream_lineage_verified: bool
    domain_count_verified: bool
    domain_order_verified: bool
    domain_uniqueness_verified: bool
    entry_hashes_verified: bool
    contracts_admitted_verified: bool
    entries_inactive_verified: bool
    entries_non_writing_verified: bool
    entries_read_only_verified: bool
    persistent_storage_disabled_verified: bool
    learning_updates_disabled_verified: bool
    runtime_activation_disabled_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
    upstream_continuation_authorized: bool
    gate_status: str
    admitted: bool
    next_certification_authorized: bool
    read_only: bool
    failure_reason: str | None
    decision_hash: str


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

    raise OracleMemoryCanonicalRecordAdmissionRegistryGateInvariantError(
        "unsupported OML-008 value type: "
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
    raise OracleMemoryCanonicalRecordAdmissionRegistryGateInvariantError(
        reason
    )


def build_oracle_memory_canonical_record_admission_registry_gate_decision(
    *,
    registry: OracleMemoryCanonicalRecordAdmissionRegistry,
) -> OracleMemoryCanonicalRecordAdmissionRegistryGateDecision:
    verify_oracle_memory_canonical_record_admission_registry(registry)

    if OML_007_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-008 upstream schema constant mismatch")

    if OML_007_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-008 upstream engine constant mismatch")

    if OML_007_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-008 upstream policy constant mismatch")

    if registry.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-008 upstream registry schema mismatch")

    if registry.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-008 upstream registry engine mismatch")

    if registry.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-008 upstream registry policy mismatch")

    domain_ids = tuple(entry.domain_id for entry in registry.entries)
    entry_hashes = tuple(entry.entry_hash for entry in registry.entries)

    checks = {
        "registry_verified": True,
        "registry_status_verified": (
            registry.registry_status == REGISTRY_STATUS_CERTIFIED
        ),
        "upstream_identity_verified": (
            registry.subsystem_id == SUBSYSTEM_ID
        ),
        "upstream_lineage_verified": all(
            len(value) == 64
            for value in (
                registry.registry_hash,
                registry.upstream_decision_hash,
                registry.upstream_certification_hash,
                registry.upstream_admission_hash,
                registry.upstream_registry_hash,
            )
        ),
        "domain_count_verified": (
            registry.entry_count == len(MEMORY_DOMAINS)
            and len(registry.entries) == len(MEMORY_DOMAINS)
        ),
        "domain_order_verified": domain_ids == MEMORY_DOMAINS,
        "domain_uniqueness_verified": (
            len(set(domain_ids)) == len(domain_ids)
        ),
        "entry_hashes_verified": (
            len(entry_hashes) == len(MEMORY_DOMAINS)
            and len(set(entry_hashes)) == len(entry_hashes)
            and all(len(value) == 64 for value in entry_hashes)
        ),
        "contracts_admitted_verified": (
            registry.all_contracts_admitted
            and all(
                entry.canonical_record_contract_admitted
                for entry in registry.entries
            )
        ),
        "entries_inactive_verified": (
            registry.all_entries_inactive
            and all(
                not entry.runtime_activation_authorized
                for entry in registry.entries
            )
        ),
        "entries_non_writing_verified": (
            registry.all_entries_non_writing
            and all(
                not entry.persistent_storage_authorized
                and not entry.learning_update_authorized
                for entry in registry.entries
            )
        ),
        "entries_read_only_verified": (
            registry.all_entries_read_only
            and all(entry.read_only for entry in registry.entries)
        ),
        "persistent_storage_disabled_verified": all(
            not entry.persistent_storage_authorized
            for entry in registry.entries
        ),
        "learning_updates_disabled_verified": all(
            not entry.learning_update_authorized
            for entry in registry.entries
        ),
        "runtime_activation_disabled_verified": all(
            not entry.runtime_activation_authorized
            for entry in registry.entries
        ),
        "publication_disabled_verified": (
            registry.publication_disabled
            and all(
                not entry.publication_authorized
                for entry in registry.entries
            )
        ),
        "action_authorization_disabled_verified": (
            registry.action_authorization_disabled
            and all(
                not entry.action_authorization_enabled
                for entry in registry.entries
            )
        ),
        "qseries_execution_disabled_verified": (
            registry.qseries_execution_disabled
            and all(
                not entry.qseries_execution_authorized
                for entry in registry.entries
            )
        ),
        "upstream_continuation_authorized": (
            registry.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if failed:
        _reject(
            "OML-008 admission registry gate failed: "
            + ", ".join(failed)
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": registry.schema_version,
        "upstream_engine_id": registry.engine_id,
        "upstream_policy_id": registry.policy_id,
        "upstream_registry_hash": registry.registry_hash,
        "upstream_decision_hash": registry.upstream_decision_hash,
        "upstream_certification_hash": (
            registry.upstream_certification_hash
        ),
        "upstream_admission_hash": registry.upstream_admission_hash,
        "upstream_domain_registry_hash": registry.upstream_registry_hash,
        "admitted_domain_ids": domain_ids,
        "admitted_entry_hashes": entry_hashes,
        "admitted_entry_count": len(registry.entries),
        **checks,
        "gate_status": GATE_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = OracleMemoryCanonicalRecordAdmissionRegistryGateDecision(
        **body,
        decision_hash=_stable_hash(body),
    )

    verify_oracle_memory_canonical_record_admission_registry_gate_decision(
        decision
    )
    return decision


def verify_oracle_memory_canonical_record_admission_registry_gate_decision(
    decision: OracleMemoryCanonicalRecordAdmissionRegistryGateDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-008 decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-008 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-008 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-008 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-008 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-008 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-008 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-008 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_registry_hash,
        decision.upstream_decision_hash,
        decision.upstream_certification_hash,
        decision.upstream_admission_hash,
        decision.upstream_domain_registry_hash,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-008 lineage hash length invalid")

    if decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-008 admitted domain identity mismatch")

    if decision.admitted_entry_count != len(MEMORY_DOMAINS):
        _reject("OML-008 admitted entry count mismatch")

    if len(decision.admitted_entry_hashes) != len(MEMORY_DOMAINS):
        _reject("OML-008 admitted entry hash count mismatch")

    if len(set(decision.admitted_entry_hashes)) != len(
        decision.admitted_entry_hashes
    ):
        _reject("OML-008 admitted entry hashes not unique")

    if any(len(value) != 64 for value in decision.admitted_entry_hashes):
        _reject("OML-008 admitted entry hash length invalid")

    required_true = (
        decision.registry_verified,
        decision.registry_status_verified,
        decision.upstream_identity_verified,
        decision.upstream_lineage_verified,
        decision.domain_count_verified,
        decision.domain_order_verified,
        decision.domain_uniqueness_verified,
        decision.entry_hashes_verified,
        decision.contracts_admitted_verified,
        decision.entries_inactive_verified,
        decision.entries_non_writing_verified,
        decision.entries_read_only_verified,
        decision.persistent_storage_disabled_verified,
        decision.learning_updates_disabled_verified,
        decision.runtime_activation_disabled_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )

    if not all(required_true):
        _reject("OML-008 admitted decision missing required guarantee")

    if decision.gate_status != GATE_STATUS_ADMITTED:
        _reject("OML-008 gate status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-008 admitted decision contains failure reason")

    return True
