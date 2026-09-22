from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from qseries_v2.oracle_memory.oracle_memory_canonical_record_candidate_contract import (
    OracleMemoryCanonicalRecordCandidate,
    verify_oracle_memory_canonical_record_candidate,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_ledger_integrity_and_replay_certification import (
    OracleMemoryLedgerIntegrityReplayCertification,
    verify_oracle_memory_ledger_integrity_replay_certification,
)

SCHEMA_VERSION = "OML-017"
ENGINE_ID = "OML-017"
POLICY_ID = "oracle-memory.candidate-validation-and-deduplication.v1"
UPSTREAM_SCHEMA_VERSION = "OML-016"
UPSTREAM_ENGINE_ID = "OML-016"

STATUS_VALID = "valid"
STATUS_DUPLICATE = "duplicate"


class OracleMemoryCandidateValidationInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryCandidateValidationResult:
    candidate_hash: str
    candidate_id: str
    domain_id: str
    entity_key: str
    status: str
    duplicate_of_candidate_hash: str | None
    candidate_verified: bool
    lineage_verified: bool
    bounds_verified: bool
    duplicate_detected: bool
    persistence_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    result_hash: str


@dataclass(frozen=True)
class OracleMemoryCandidateValidationBatch:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_certification_hash: str
    results: tuple[OracleMemoryCandidateValidationResult, ...]
    candidate_count: int
    unique_candidate_count: int
    duplicate_candidate_count: int
    canonical_ordering_verified: bool
    deterministic_validation_verified: bool
    duplicate_detection_verified: bool
    duplicate_persistence_forbidden: bool
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
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleMemoryCandidateValidationInvariantError(
        f"unsupported OML-017 value type: {type(value).__qualname__}"
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
    raise OracleMemoryCandidateValidationInvariantError(reason)


def _result(
    candidate: OracleMemoryCanonicalRecordCandidate,
    duplicate_of: str | None,
) -> OracleMemoryCandidateValidationResult:
    verify_oracle_memory_canonical_record_candidate(candidate)

    duplicate = duplicate_of is not None
    body = {
        "candidate_hash": candidate.candidate_hash,
        "candidate_id": candidate.candidate_id,
        "domain_id": candidate.domain_id,
        "entity_key": candidate.entity_key,
        "status": STATUS_DUPLICATE if duplicate else STATUS_VALID,
        "duplicate_of_candidate_hash": duplicate_of,
        "candidate_verified": True,
        "lineage_verified": (
            len(set(candidate.evidence_hashes)) == len(candidate.evidence_hashes)
            and len(set(candidate.parent_record_hashes))
            == len(candidate.parent_record_hashes)
        ),
        "bounds_verified": (
            0.0 <= candidate.confidence <= 1.0
            and 0.0 <= candidate.uncertainty <= 1.0
            and candidate.contradiction_count >= 0
        ),
        "duplicate_detected": duplicate,
        "persistence_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    result = OracleMemoryCandidateValidationResult(
        **body,
        result_hash=_stable_hash(body),
    )
    verify_oracle_memory_candidate_validation_result(result)
    return result


def verify_oracle_memory_candidate_validation_result(
    result: OracleMemoryCandidateValidationResult,
) -> bool:
    body = asdict(result)
    supplied = body.pop("result_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-017 result hash mismatch")
    if result.domain_id not in MEMORY_DOMAINS:
        _reject("OML-017 unknown domain")
    if result.status not in (STATUS_VALID, STATUS_DUPLICATE):
        _reject("OML-017 invalid status")
    if result.duplicate_detected != (result.status == STATUS_DUPLICATE):
        _reject("OML-017 duplicate status mismatch")
    if result.duplicate_detected != (
        result.duplicate_of_candidate_hash is not None
    ):
        _reject("OML-017 duplicate lineage mismatch")
    if not all(
        (
            result.candidate_verified,
            result.lineage_verified,
            result.bounds_verified,
            result.read_only,
        )
    ):
        _reject("OML-017 validation guarantee missing")
    if any(
        (
            result.persistence_authorized,
            result.learning_update_authorized,
            result.runtime_activation_authorized,
            result.publication_authorized,
            result.action_authorization_enabled,
            result.qseries_execution_authorized,
        )
    ):
        _reject("OML-017 forbidden capability enabled")
    return True


def build_oracle_memory_candidate_validation_batch(
    *,
    ledger_certification: OracleMemoryLedgerIntegrityReplayCertification,
    candidates: Sequence[OracleMemoryCanonicalRecordCandidate],
) -> OracleMemoryCandidateValidationBatch:
    verify_oracle_memory_ledger_integrity_replay_certification(
        ledger_certification
    )

    if ledger_certification.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-017 upstream schema mismatch")
    if ledger_certification.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-017 upstream engine mismatch")
    if not ledger_certification.certification_ready:
        _reject("OML-017 upstream certification not ready")
    if not ledger_certification.next_certification_authorized:
        _reject("OML-017 continuation not authorized")
    if not ledger_certification.read_only:
        _reject("OML-017 upstream read-only guarantee missing")

    ordered = tuple(
        sorted(
            candidates,
            key=lambda item: (
                MEMORY_DOMAINS.index(item.domain_id),
                item.entity_key,
                item.candidate_id,
                item.candidate_hash,
            ),
        )
    )

    seen: set[str] = set()
    results = []
    for candidate in ordered:
        duplicate_of = (
            candidate.candidate_hash
            if candidate.candidate_hash in seen
            else None
        )
        results.append(_result(candidate, duplicate_of))
        seen.add(candidate.candidate_hash)

    result_tuple = tuple(results)
    duplicate_count = sum(item.duplicate_detected for item in result_tuple)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": ledger_certification.schema_version,
        "upstream_engine_id": ledger_certification.engine_id,
        "upstream_certification_hash": ledger_certification.certification_hash,
        "results": result_tuple,
        "candidate_count": len(result_tuple),
        "unique_candidate_count": len(result_tuple) - duplicate_count,
        "duplicate_candidate_count": duplicate_count,
        "canonical_ordering_verified": True,
        "deterministic_validation_verified": True,
        "duplicate_detection_verified": True,
        "duplicate_persistence_forbidden": True,
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

    batch = OracleMemoryCandidateValidationBatch(
        **body,
        batch_hash=_stable_hash(body),
    )
    verify_oracle_memory_candidate_validation_batch(batch)
    return batch


def verify_oracle_memory_candidate_validation_batch(
    batch: OracleMemoryCandidateValidationBatch,
) -> bool:
    body = asdict(batch)
    supplied = body.pop("batch_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-017 batch hash mismatch")
    if batch.schema_version != SCHEMA_VERSION:
        _reject("OML-017 schema mismatch")
    if batch.engine_id != ENGINE_ID:
        _reject("OML-017 engine mismatch")
    if batch.policy_id != POLICY_ID:
        _reject("OML-017 policy mismatch")
    if batch.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-017 subsystem mismatch")
    if batch.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-017 upstream schema lineage mismatch")
    if batch.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-017 upstream engine lineage mismatch")
    if batch.candidate_count != len(batch.results):
        _reject("OML-017 candidate count mismatch")
    if (
        batch.unique_candidate_count + batch.duplicate_candidate_count
        != batch.candidate_count
    ):
        _reject("OML-017 count reconciliation mismatch")

    for result in batch.results:
        verify_oracle_memory_candidate_validation_result(result)

    if not all(
        (
            batch.canonical_ordering_verified,
            batch.deterministic_validation_verified,
            batch.duplicate_detection_verified,
            batch.duplicate_persistence_forbidden,
            batch.batch_ready,
            batch.next_certification_authorized,
            batch.read_only,
        )
    ):
        _reject("OML-017 batch guarantee missing")
    if any(
        (
            batch.persistence_enabled,
            batch.learning_updates_enabled,
            batch.runtime_activation_enabled,
            batch.publication_enabled,
            batch.action_authorization_enabled,
            batch.qseries_execution_enabled,
        )
    ):
        _reject("OML-017 forbidden batch capability enabled")
    return True
