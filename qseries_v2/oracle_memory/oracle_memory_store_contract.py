from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_admission_registry_gate import (
    OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision,
    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-013"
ENGINE_ID = "OML-013"
POLICY_ID = "oracle-memory.store-contract.v1"

UPSTREAM_SCHEMA_VERSION = "OML-012"
UPSTREAM_ENGINE_ID = "OML-012"

STORE_MODE_APPEND_ONLY = "append_only"
STORE_STATE_CONTRACT_ONLY = "contract_only"
ATOMICITY_MODEL_SINGLE_COMMIT = "single_commit"
REPLAY_MODEL_FULL_LEDGER_REPLAY = "full_ledger_replay"


class OracleMemoryStoreContractInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryStorePartitionContract:
    domain_id: str
    ordinal: int
    partition_key: str
    append_only_required: bool
    deterministic_order_required: bool
    immutable_record_hash_required: bool
    parent_lineage_required: bool
    evidence_lineage_required: bool
    duplicate_record_hashes_forbidden: bool
    destructive_update_allowed: bool
    delete_allowed: bool
    persistence_enabled: bool
    learning_update_enabled: bool
    runtime_activation_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    read_only: bool
    partition_hash: str


@dataclass(frozen=True)
class OracleMemoryStoreContractCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_gate_decision_hash: str
    upstream_registry_hash: str
    certified_domain_ids: tuple[str, ...]
    store_mode: str
    store_state: str
    atomicity_model: str
    replay_model: str
    partitions: tuple[OracleMemoryStorePartitionContract, ...]
    partition_count: int
    canonical_serialization_required: bool
    deterministic_commit_hashing_required: bool
    append_only_required: bool
    immutable_ledger_required: bool
    atomic_commit_required: bool
    replay_verification_required: bool
    lineage_preservation_required: bool
    duplicate_record_hashes_forbidden: bool
    destructive_updates_forbidden: bool
    deletes_forbidden: bool
    persistence_enabled: bool
    learning_updates_enabled: bool
    runtime_activation_enabled: bool
    database_access_enabled: bool
    networking_enabled: bool
    publication_enabled: bool
    action_authorization_enabled: bool
    qseries_execution_enabled: bool
    contract_ready: bool
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

    raise OracleMemoryStoreContractInvariantError(
        "unsupported OML-013 value type: "
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
    raise OracleMemoryStoreContractInvariantError(reason)


def _build_partition(
    *,
    domain_id: str,
    ordinal: int,
) -> OracleMemoryStorePartitionContract:
    body = {
        "domain_id": domain_id,
        "ordinal": ordinal,
        "partition_key": f"oracle-memory:{domain_id}",
        "append_only_required": True,
        "deterministic_order_required": True,
        "immutable_record_hash_required": True,
        "parent_lineage_required": True,
        "evidence_lineage_required": True,
        "duplicate_record_hashes_forbidden": True,
        "destructive_update_allowed": False,
        "delete_allowed": False,
        "persistence_enabled": False,
        "learning_update_enabled": False,
        "runtime_activation_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "read_only": True,
    }

    return OracleMemoryStorePartitionContract(
        **body,
        partition_hash=_stable_hash(body),
    )


def verify_oracle_memory_store_partition_contract(
    partition: OracleMemoryStorePartitionContract,
) -> bool:
    body = asdict(partition)
    supplied = body.pop("partition_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-013 partition hash mismatch")

    if partition.domain_id not in MEMORY_DOMAINS:
        _reject("OML-013 unknown memory domain")

    if partition.ordinal != MEMORY_DOMAINS.index(partition.domain_id) + 1:
        _reject("OML-013 partition ordinal mismatch")

    if partition.partition_key != f"oracle-memory:{partition.domain_id}":
        _reject("OML-013 partition key mismatch")

    required_true = (
        partition.append_only_required,
        partition.deterministic_order_required,
        partition.immutable_record_hash_required,
        partition.parent_lineage_required,
        partition.evidence_lineage_required,
        partition.duplicate_record_hashes_forbidden,
        partition.read_only,
    )

    if not all(required_true):
        _reject("OML-013 partition guarantee missing")

    forbidden = (
        partition.destructive_update_allowed,
        partition.delete_allowed,
        partition.persistence_enabled,
        partition.learning_update_enabled,
        partition.runtime_activation_enabled,
        partition.publication_enabled,
        partition.action_authorization_enabled,
        partition.qseries_execution_enabled,
    )

    if any(forbidden):
        _reject("OML-013 forbidden partition capability enabled")

    return True


def build_oracle_memory_store_contract_certification(
    *,
    gate_decision: OracleMemoryCanonicalRecordCandidateAdmissionRegistryGateDecision,
) -> OracleMemoryStoreContractCertification:
    verify_oracle_memory_canonical_record_candidate_admission_registry_gate_decision(
        gate_decision
    )

    if gate_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-013 upstream schema mismatch")

    if gate_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-013 upstream engine mismatch")

    if not gate_decision.admitted:
        _reject("OML-013 upstream gate not admitted")

    if not gate_decision.next_certification_authorized:
        _reject("OML-013 upstream continuation not authorized")

    if not gate_decision.read_only:
        _reject("OML-013 upstream read-only guarantee missing")

    if gate_decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-013 upstream domain identity mismatch")

    partitions = tuple(
        _build_partition(
            domain_id=domain_id,
            ordinal=index,
        )
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for partition in partitions:
        verify_oracle_memory_store_partition_contract(partition)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": gate_decision.schema_version,
        "upstream_engine_id": gate_decision.engine_id,
        "upstream_gate_decision_hash": gate_decision.decision_hash,
        "upstream_registry_hash": gate_decision.upstream_registry_hash,
        "certified_domain_ids": gate_decision.admitted_domain_ids,
        "store_mode": STORE_MODE_APPEND_ONLY,
        "store_state": STORE_STATE_CONTRACT_ONLY,
        "atomicity_model": ATOMICITY_MODEL_SINGLE_COMMIT,
        "replay_model": REPLAY_MODEL_FULL_LEDGER_REPLAY,
        "partitions": partitions,
        "partition_count": len(partitions),
        "canonical_serialization_required": True,
        "deterministic_commit_hashing_required": True,
        "append_only_required": True,
        "immutable_ledger_required": True,
        "atomic_commit_required": True,
        "replay_verification_required": True,
        "lineage_preservation_required": True,
        "duplicate_record_hashes_forbidden": True,
        "destructive_updates_forbidden": True,
        "deletes_forbidden": True,
        "persistence_enabled": False,
        "learning_updates_enabled": False,
        "runtime_activation_enabled": False,
        "database_access_enabled": False,
        "networking_enabled": False,
        "publication_enabled": False,
        "action_authorization_enabled": False,
        "qseries_execution_enabled": False,
        "contract_ready": True,
        "next_certification_authorized": True,
        "read_only": True,
    }

    certification = OracleMemoryStoreContractCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_store_contract_certification(certification)
    return certification


def verify_oracle_memory_store_contract_certification(
    certification: OracleMemoryStoreContractCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-013 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-013 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-013 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-013 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-013 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-013 certification upstream schema mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-013 certification upstream engine mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-013 certification domain mismatch")

    if certification.partition_count != len(MEMORY_DOMAINS):
        _reject("OML-013 partition count mismatch")

    if tuple(item.domain_id for item in certification.partitions) != MEMORY_DOMAINS:
        _reject("OML-013 partition order mismatch")

    for partition in certification.partitions:
        verify_oracle_memory_store_partition_contract(partition)

    if certification.store_mode != STORE_MODE_APPEND_ONLY:
        _reject("OML-013 store mode mismatch")

    if certification.store_state != STORE_STATE_CONTRACT_ONLY:
        _reject("OML-013 store state mismatch")

    if certification.atomicity_model != ATOMICITY_MODEL_SINGLE_COMMIT:
        _reject("OML-013 atomicity model mismatch")

    if certification.replay_model != REPLAY_MODEL_FULL_LEDGER_REPLAY:
        _reject("OML-013 replay model mismatch")

    required_true = (
        certification.canonical_serialization_required,
        certification.deterministic_commit_hashing_required,
        certification.append_only_required,
        certification.immutable_ledger_required,
        certification.atomic_commit_required,
        certification.replay_verification_required,
        certification.lineage_preservation_required,
        certification.duplicate_record_hashes_forbidden,
        certification.destructive_updates_forbidden,
        certification.deletes_forbidden,
        certification.contract_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-013 certification guarantee missing")

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
        _reject("OML-013 forbidden store capability enabled")

    return True
