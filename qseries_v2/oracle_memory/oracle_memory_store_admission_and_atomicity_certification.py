from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_store_contract import (
    ATOMICITY_MODEL_SINGLE_COMMIT,
    REPLAY_MODEL_FULL_LEDGER_REPLAY,
    STORE_MODE_APPEND_ONLY,
    STORE_STATE_CONTRACT_ONLY,
    OracleMemoryStoreContractCertification,
    verify_oracle_memory_store_contract_certification,
)

SCHEMA_VERSION = "OML-014"
ENGINE_ID = "OML-014"
POLICY_ID = "oracle-memory.store-admission-and-atomicity-certification.v1"

UPSTREAM_SCHEMA_VERSION = "OML-013"
UPSTREAM_ENGINE_ID = "OML-013"

ADMISSION_STATUS_CERTIFIED = "certified"
ATOMICITY_STATUS_CERTIFIED = "single_commit_atomicity_certified"


class OracleMemoryStoreAdmissionAtomicityInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryStorePartitionAdmission:
    domain_id: str
    ordinal: int
    upstream_partition_hash: str
    partition_key: str
    append_only_admitted: bool
    deterministic_order_admitted: bool
    immutable_record_hash_admitted: bool
    parent_lineage_admitted: bool
    evidence_lineage_admitted: bool
    duplicate_record_rejection_admitted: bool
    destructive_update_rejected: bool
    delete_rejected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    admission_hash: str


@dataclass(frozen=True)
class OracleMemoryStoreAdmissionAtomicityCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    admission_status: str
    atomicity_status: str
    store_mode: str
    atomicity_model: str
    replay_model: str
    partition_admissions: tuple[OracleMemoryStorePartitionAdmission, ...]
    partition_count: int
    append_only_admitted: bool
    deterministic_commit_hashing_admitted: bool
    immutable_ledger_admitted: bool
    atomic_single_commit_admitted: bool
    full_replay_admitted: bool
    lineage_preservation_admitted: bool
    duplicate_record_rejection_admitted: bool
    destructive_updates_rejected: bool
    deletes_rejected: bool
    rollback_on_failure_required: bool
    partial_commit_forbidden: bool
    commit_order_canonical: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    database_access_enabled: bool
    networking_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    certification_ready: bool
    next_certification_authorized: bool
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

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise OracleMemoryStoreAdmissionAtomicityInvariantError(
        "unsupported OML-014 value type: "
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
    raise OracleMemoryStoreAdmissionAtomicityInvariantError(reason)


def _build_partition_admission(
    *,
    domain_id: str,
    ordinal: int,
    upstream_partition_hash: str,
    partition_key: str,
) -> OracleMemoryStorePartitionAdmission:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "upstream_partition_hash": upstream_partition_hash,
        "partition_key": partition_key,
        "append_only_admitted": True,
        "deterministic_order_admitted": True,
        "immutable_record_hash_admitted": True,
        "parent_lineage_admitted": True,
        "evidence_lineage_admitted": True,
        "duplicate_record_rejection_admitted": True,
        "destructive_update_rejected": True,
        "delete_rejected": True,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryStorePartitionAdmission(
        **body,
        admission_hash=_stable_hash(body),
    )


def verify_oracle_memory_store_partition_admission(
    admission: OracleMemoryStorePartitionAdmission,
) -> bool:
    body = asdict(admission)
    supplied = body.pop("admission_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-014 partition admission hash mismatch")

    if admission.domain_id not in MEMORY_DOMAINS:
        _reject("OML-014 unknown memory domain")

    if admission.ordinal != MEMORY_DOMAINS.index(admission.domain_id) + 1:
        _reject("OML-014 partition ordinal mismatch")

    if len(admission.upstream_partition_hash) != 64:
        _reject("OML-014 upstream partition hash invalid")

    if admission.partition_key != f"oracle-memory:{admission.domain_id}":
        _reject("OML-014 partition key mismatch")

    required_true = (
        admission.append_only_admitted,
        admission.deterministic_order_admitted,
        admission.immutable_record_hash_admitted,
        admission.parent_lineage_admitted,
        admission.evidence_lineage_admitted,
        admission.duplicate_record_rejection_admitted,
        admission.destructive_update_rejected,
        admission.delete_rejected,
        admission.read_only,
    )

    if not all(required_true):
        _reject("OML-014 partition admission guarantee missing")

    forbidden = (
        admission.persistence_authorized,
        admission.learning_update_authorized,
        admission.runtime_activation_authorized,
        admission.publication_authorized,
        admission.action_authorization_enabled,
        admission.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-014 forbidden partition capability enabled")

    return True


def build_oracle_memory_store_admission_atomicity_certification(
    *,
    store_contract: OracleMemoryStoreContractCertification,
) -> OracleMemoryStoreAdmissionAtomicityCertification:
    verify_oracle_memory_store_contract_certification(store_contract)

    if store_contract.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-014 upstream schema mismatch")

    if store_contract.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-014 upstream engine mismatch")

    if not store_contract.contract_ready:
        _reject("OML-014 upstream store contract not ready")

    if not store_contract.next_certification_authorized:
        _reject("OML-014 upstream continuation not authorized")

    if not store_contract.read_only:
        _reject("OML-014 upstream read-only guarantee missing")

    if store_contract.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-014 upstream domain identity mismatch")

    admissions = tuple(
        _build_partition_admission(
            domain_id=partition.domain_id,
            ordinal=partition.ordinal,
            upstream_partition_hash=partition.partition_hash,
            partition_key=partition.partition_key,
        )
        for partition in store_contract.partitions
    )

    for admission in admissions:
        verify_oracle_memory_store_partition_admission(admission)

    domain_ids = tuple(item.domain_id for item in admissions)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": store_contract.schema_version,
        "upstream_engine_id": store_contract.engine_id,
        "upstream_certification_hash": store_contract.certification_hash,
        "upstream_gate_decision_hash": (
            store_contract.upstream_gate_decision_hash
        ),
        "upstream_registry_hash": store_contract.upstream_registry_hash,
        "certified_domain_ids": store_contract.certified_domain_ids,
        "admission_status": ADMISSION_STATUS_CERTIFIED,
        "atomicity_status": ATOMICITY_STATUS_CERTIFIED,
        "store_mode": store_contract.store_mode,
        "atomicity_model": store_contract.atomicity_model,
        "replay_model": store_contract.replay_model,
        "partition_admissions": admissions,
        "partition_count": len(admissions),
        "append_only_admitted": store_contract.append_only_required,
        "deterministic_commit_hashing_admitted": (
            store_contract.deterministic_commit_hashing_required
        ),
        "immutable_ledger_admitted": (
            store_contract.immutable_ledger_required
        ),
        "atomic_single_commit_admitted": (
            store_contract.atomic_commit_required
        ),
        "full_replay_admitted": (
            store_contract.replay_verification_required
        ),
        "lineage_preservation_admitted": (
            store_contract.lineage_preservation_required
        ),
        "duplicate_record_rejection_admitted": (
            store_contract.duplicate_record_hashes_forbidden
        ),
        "destructive_updates_rejected": (
            store_contract.destructive_updates_forbidden
        ),
        "deletes_rejected": store_contract.deletes_forbidden,
        "rollback_on_failure_required": True,
        "partial_commit_forbidden": True,
        "commit_order_canonical": domain_ids == MEMORY_DOMAINS,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "database_access_enabled": False,
        "networking_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "certification_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryStoreAdmissionAtomicityCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_store_admission_atomicity_certification(
        certification
    )
    return certification


def verify_oracle_memory_store_admission_atomicity_certification(
    certification: OracleMemoryStoreAdmissionAtomicityCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-014 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-014 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-014 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-014 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-014 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-014 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-014 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-014 certification domain mismatch")

    if certification.partition_count != len(MEMORY_DOMAINS):
        _reject("OML-014 partition count mismatch")

    if tuple(
        item.domain_id
        for item in certification.partition_admissions
    ) != MEMORY_DOMAINS:
        _reject("OML-014 partition admission order mismatch")

    for admission in certification.partition_admissions:
        verify_oracle_memory_store_partition_admission(admission)

    if certification.admission_status != ADMISSION_STATUS_CERTIFIED:
        _reject("OML-014 admission status mismatch")

    if certification.atomicity_status != ATOMICITY_STATUS_CERTIFIED:
        _reject("OML-014 atomicity status mismatch")

    if certification.store_mode != STORE_MODE_APPEND_ONLY:
        _reject("OML-014 store mode mismatch")

    if certification.atomicity_model != ATOMICITY_MODEL_SINGLE_COMMIT:
        _reject("OML-014 atomicity model mismatch")

    if certification.replay_model != REPLAY_MODEL_FULL_LEDGER_REPLAY:
        _reject("OML-014 replay model mismatch")

    required_true = (
        certification.append_only_admitted,
        certification.deterministic_commit_hashing_admitted,
        certification.immutable_ledger_admitted,
        certification.atomic_single_commit_admitted,
        certification.full_replay_admitted,
        certification.lineage_preservation_admitted,
        certification.duplicate_record_rejection_admitted,
        certification.destructive_updates_rejected,
        certification.deletes_rejected,
        certification.rollback_on_failure_required,
        certification.partial_commit_forbidden,
        certification.commit_order_canonical,
        certification.certification_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-014 certification guarantee missing")

    forbidden = (
        certification.persistence_enabled,
        certification.learning_updates_enabled,
        certification.runtime_activation_enabled,
        certification.database_access_enabled,
        certification.networking_enabled,
        certification.publication_enabled,
        certification.action_authorization_enabled,
        certification.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-014 forbidden store capability enabled")

    return True
