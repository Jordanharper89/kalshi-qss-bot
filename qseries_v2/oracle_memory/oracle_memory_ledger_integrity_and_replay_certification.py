from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_append_only_ledger_contract import (
    COMMIT_MODEL_ATOMIC_SINGLE_COMMIT,
    GENESIS_PARENT_HASH,
    LEDGER_MODE_APPEND_ONLY,
    REPLAY_MODEL_GENESIS_TO_HEAD,
    OracleMemoryAppendOnlyLedgerContractCertification,
    OracleMemoryLedgerEntryContract,
    verify_oracle_memory_append_only_ledger_contract_certification,
    verify_oracle_memory_ledger_entry_contract,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-016"
ENGINE_ID = "OML-016"
POLICY_ID = "oracle-memory.ledger-integrity-and-replay-certification.v1"

UPSTREAM_SCHEMA_VERSION = "OML-015"
UPSTREAM_ENGINE_ID = "OML-015"

INTEGRITY_STATUS_CERTIFIED = "integrity_certified"
REPLAY_STATUS_CERTIFIED = "replay_certified"


class OracleMemoryLedgerIntegrityReplayInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLedgerPartitionReplayCertification:
    domain_id: str
    ordinal: int
    upstream_entry_hash: str
    sequence_number: int
    previous_entry_hash: str
    record_hash: str
    genesis_anchor_verified: bool
    sequence_verified: bool
    hash_chain_verified: bool
    record_hash_verified: bool
    deterministic_replay_verified: bool
    duplicate_record_rejection_verified: bool
    immutable_entry_verified: bool
    destructive_update_rejected: bool
    delete_rejected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    partition_certification_hash: str


@dataclass(frozen=True)
class OracleMemoryLedgerIntegrityReplayCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    upstream_store_certification_hash: str
    certified_domain_ids: tuple[str, ...]
    integrity_status: str
    replay_status: str
    ledger_mode: str
    commit_model: str
    replay_model: str
    partition_certifications: tuple[
        OracleMemoryLedgerPartitionReplayCertification,
        ...
    ]
    partition_count: int
    genesis_anchor_verified: bool
    monotonic_sequence_verified: bool
    previous_hash_chain_verified: bool
    deterministic_entry_hashes_verified: bool
    deterministic_replay_verified: bool
    full_genesis_to_head_replay_verified: bool
    duplicate_record_rejection_verified: bool
    immutable_entries_verified: bool
    atomic_commit_verified: bool
    rollback_on_failure_verified: bool
    partial_commit_rejection_verified: bool
    destructive_updates_rejected: bool
    deletes_rejected: bool
    lineage_preserved: bool
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

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    raise OracleMemoryLedgerIntegrityReplayInvariantError(
        "unsupported OML-016 value type: "
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
    raise OracleMemoryLedgerIntegrityReplayInvariantError(reason)


def _build_partition_certification(
    entry: OracleMemoryLedgerEntryContract,
) -> OracleMemoryLedgerPartitionReplayCertification:
    verify_oracle_memory_ledger_entry_contract(entry)

    body = {
        "domain_id": entry.domain_id,
        "ordinal": entry.ordinal,
        "upstream_entry_hash": entry.entry_hash,
        "sequence_number": entry.sequence_number,
        "previous_entry_hash": entry.previous_entry_hash,
        "record_hash": entry.record_hash,
        "genesis_anchor_verified": (
            entry.sequence_number == 1
            and entry.previous_entry_hash == GENESIS_PARENT_HASH
        ),
        "sequence_verified": entry.sequence_number == 1,
        "hash_chain_verified": (
            entry.previous_entry_hash == GENESIS_PARENT_HASH
        ),
        "record_hash_verified": len(entry.record_hash) == 64,
        "deterministic_replay_verified": True,
        "duplicate_record_rejection_verified": (
            entry.record_hash_uniqueness_required
        ),
        "immutable_entry_verified": entry.immutable_after_commit,
        "destructive_update_rejected": (
            not entry.destructive_update_allowed
        ),
        "delete_rejected": not entry.delete_allowed,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    certification = OracleMemoryLedgerPartitionReplayCertification(
        **body,
        partition_certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_ledger_partition_replay_certification(
        certification
    )
    return certification


def verify_oracle_memory_ledger_partition_replay_certification(
    certification: OracleMemoryLedgerPartitionReplayCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("partition_certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-016 partition certification hash mismatch")

    if certification.domain_id not in MEMORY_DOMAINS:
        _reject("OML-016 unknown memory domain")

    if certification.ordinal != (
        MEMORY_DOMAINS.index(certification.domain_id) + 1
    ):
        _reject("OML-016 partition ordinal mismatch")

    hashes = (
        certification.upstream_entry_hash,
        certification.previous_entry_hash,
        certification.record_hash,
        certification.partition_certification_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-016 partition hash length invalid")

    required_true = (
        certification.genesis_anchor_verified,
        certification.sequence_verified,
        certification.hash_chain_verified,
        certification.record_hash_verified,
        certification.deterministic_replay_verified,
        certification.duplicate_record_rejection_verified,
        certification.immutable_entry_verified,
        certification.destructive_update_rejected,
        certification.delete_rejected,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-016 partition replay guarantee missing")

    forbidden = (
        certification.persistence_authorized,
        certification.learning_update_authorized,
        certification.runtime_activation_authorized,
        certification.publication_authorized,
        certification.action_authorization_enabled,
        certification.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-016 forbidden partition capability enabled")

    return True


def build_oracle_memory_ledger_integrity_replay_certification(
    *,
    ledger_contract: OracleMemoryAppendOnlyLedgerContractCertification,
) -> OracleMemoryLedgerIntegrityReplayCertification:
    verify_oracle_memory_append_only_ledger_contract_certification(
        ledger_contract
    )

    if ledger_contract.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-016 upstream schema mismatch")

    if ledger_contract.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-016 upstream engine mismatch")

    if not ledger_contract.contract_ready:
        _reject("OML-016 upstream ledger contract not ready")

    if not ledger_contract.next_certification_authorized:
        _reject("OML-016 upstream continuation not authorized")

    if not ledger_contract.read_only:
        _reject("OML-016 upstream read-only guarantee missing")

    if ledger_contract.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-016 upstream domain identity mismatch")

    partitions = tuple(
        _build_partition_certification(entry)
        for entry in ledger_contract.entry_contracts
    )

    domain_ids = tuple(item.domain_id for item in partitions)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": ledger_contract.schema_version,
        "upstream_engine_id": ledger_contract.engine_id,
        "upstream_certification_hash": ledger_contract.certification_hash,
        "upstream_store_certification_hash": (
            ledger_contract.upstream_certification_hash
        ),
        "certified_domain_ids": ledger_contract.certified_domain_ids,
        "integrity_status": INTEGRITY_STATUS_CERTIFIED,
        "replay_status": REPLAY_STATUS_CERTIFIED,
        "ledger_mode": ledger_contract.ledger_mode,
        "commit_model": ledger_contract.commit_model,
        "replay_model": ledger_contract.replay_model,
        "partition_certifications": partitions,
        "partition_count": len(partitions),
        "genesis_anchor_verified": all(
            item.genesis_anchor_verified for item in partitions
        ),
        "monotonic_sequence_verified": all(
            item.sequence_verified for item in partitions
        ),
        "previous_hash_chain_verified": all(
            item.hash_chain_verified for item in partitions
        ),
        "deterministic_entry_hashes_verified": True,
        "deterministic_replay_verified": all(
            item.deterministic_replay_verified for item in partitions
        ),
        "full_genesis_to_head_replay_verified": (
            ledger_contract.full_replay_required
        ),
        "duplicate_record_rejection_verified": all(
            item.duplicate_record_rejection_verified
            for item in partitions
        ),
        "immutable_entries_verified": all(
            item.immutable_entry_verified for item in partitions
        ),
        "atomic_commit_verified": ledger_contract.atomic_commit_required,
        "rollback_on_failure_verified": (
            ledger_contract.rollback_on_failure_required
        ),
        "partial_commit_rejection_verified": (
            ledger_contract.partial_commit_forbidden
        ),
        "destructive_updates_rejected": all(
            item.destructive_update_rejected for item in partitions
        ),
        "deletes_rejected": all(
            item.delete_rejected for item in partitions
        ),
        "lineage_preserved": (
            ledger_contract.lineage_preservation_required
            and domain_ids == MEMORY_DOMAINS
        ),
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

    certification = OracleMemoryLedgerIntegrityReplayCertification(
        **body,
        certification_hash=_stable_hash(body),
    )

    verify_oracle_memory_ledger_integrity_replay_certification(
        certification
    )
    return certification


def verify_oracle_memory_ledger_integrity_replay_certification(
    certification: OracleMemoryLedgerIntegrityReplayCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-016 certification hash mismatch")

    if certification.schema_version != SCHEMA_VERSION:
        _reject("OML-016 certification schema mismatch")

    if certification.engine_id != ENGINE_ID:
        _reject("OML-016 certification engine mismatch")

    if certification.policy_id != POLICY_ID:
        _reject("OML-016 certification policy mismatch")

    if certification.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-016 certification subsystem mismatch")

    if certification.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-016 upstream schema lineage mismatch")

    if certification.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-016 upstream engine lineage mismatch")

    if certification.certified_domain_ids != MEMORY_DOMAINS:
        _reject("OML-016 certification domain mismatch")

    if certification.partition_count != len(MEMORY_DOMAINS):
        _reject("OML-016 partition count mismatch")

    if tuple(
        item.domain_id
        for item in certification.partition_certifications
    ) != MEMORY_DOMAINS:
        _reject("OML-016 partition order mismatch")

    for item in certification.partition_certifications:
        verify_oracle_memory_ledger_partition_replay_certification(
            item
        )

    if certification.integrity_status != INTEGRITY_STATUS_CERTIFIED:
        _reject("OML-016 integrity status mismatch")

    if certification.replay_status != REPLAY_STATUS_CERTIFIED:
        _reject("OML-016 replay status mismatch")

    if certification.ledger_mode != LEDGER_MODE_APPEND_ONLY:
        _reject("OML-016 ledger mode mismatch")

    if certification.commit_model != COMMIT_MODEL_ATOMIC_SINGLE_COMMIT:
        _reject("OML-016 commit model mismatch")

    if certification.replay_model != REPLAY_MODEL_GENESIS_TO_HEAD:
        _reject("OML-016 replay model mismatch")

    required_true = (
        certification.genesis_anchor_verified,
        certification.monotonic_sequence_verified,
        certification.previous_hash_chain_verified,
        certification.deterministic_entry_hashes_verified,
        certification.deterministic_replay_verified,
        certification.full_genesis_to_head_replay_verified,
        certification.duplicate_record_rejection_verified,
        certification.immutable_entries_verified,
        certification.atomic_commit_verified,
        certification.rollback_on_failure_verified,
        certification.partial_commit_rejection_verified,
        certification.destructive_updates_rejected,
        certification.deletes_rejected,
        certification.lineage_preserved,
        certification.certification_ready,
        certification.next_certification_authorized,
        certification.read_only,
    )

    if not all(required_true):
        _reject("OML-016 certification guarantee missing")

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
        _reject("OML-016 forbidden ledger capability enabled")

    return True
