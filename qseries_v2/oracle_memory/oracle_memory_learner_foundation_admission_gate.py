from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    ENGINE_ID as OML_001_ENGINE_ID,
    MEMORY_DOMAINS,
    POLICY_ID as OML_001_POLICY_ID,
    SCHEMA_VERSION as OML_001_SCHEMA_VERSION,
    SUBSYSTEM_ID,
    OracleMemoryLearnerFoundationReport,
    verify_oracle_memory_learner_foundation_report,
)

SCHEMA_VERSION = "OML-002"
ENGINE_ID = "OML-002"
POLICY_ID = "oracle-memory-learner.foundation-admission-gate.v1"

UPSTREAM_SCHEMA_VERSION = "OML-001"
UPSTREAM_ENGINE_ID = "OML-001"
UPSTREAM_POLICY_ID = (
    "oracle-memory-continuous-intelligence-learner.foundation.v1"
)

ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryLearnerFoundationAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryLearnerFoundationAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    repository_root: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_report_hash: str
    upstream_certification_hash: str
    upstream_oit_report_hash: str
    upstream_oit_runner_sha256: str
    configured_memory_domains: tuple[str, ...]
    foundation_verified: bool
    subsystem_identity_verified: bool
    package_separation_verified: bool
    certified_read_only_consumption_verified: bool
    deterministic_contract_verified: bool
    replay_contract_verified: bool
    immutable_lineage_verified: bool
    auditability_verified: bool
    memory_domains_verified: bool
    no_persistent_memory_verified: bool
    no_learning_update_verified: bool
    no_learner_execution_verified: bool
    no_memory_write_verified: bool
    no_database_access_verified: bool
    no_networking_verified: bool
    no_runtime_mutation_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
    foundation_ready_verified: bool
    upstream_continuation_authorized: bool
    admission_status: str
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

    raise OracleMemoryLearnerFoundationAdmissionInvariantError(
        "unsupported OML-002 value type: "
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
    raise OracleMemoryLearnerFoundationAdmissionInvariantError(reason)


def build_oracle_memory_learner_foundation_admission_decision(
    repository_root: str | Path,
    *,
    foundation_report: OracleMemoryLearnerFoundationReport,
) -> OracleMemoryLearnerFoundationAdmissionDecision:
    root = Path(repository_root).resolve()

    verify_oracle_memory_learner_foundation_report(
        foundation_report
    )

    if OML_001_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-002 upstream schema constant mismatch")

    if OML_001_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-002 upstream engine constant mismatch")

    if OML_001_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-002 upstream policy constant mismatch")

    upstream = foundation_report.upstream_certification

    checks = {
        "foundation_verified": True,
        "subsystem_identity_verified": (
            foundation_report.subsystem_id == SUBSYSTEM_ID
        ),
        "package_separation_verified": (
            foundation_report.package_separate_from_oracle_terminal
        ),
        "certified_read_only_consumption_verified": (
            foundation_report.certified_read_only_upstream_consumption_only
        ),
        "deterministic_contract_verified": (
            foundation_report.deterministic_contract_enabled
        ),
        "replay_contract_verified": (
            foundation_report.replay_verification_enabled
        ),
        "immutable_lineage_verified": (
            foundation_report.immutable_lineage_required
        ),
        "auditability_verified": (
            foundation_report.auditability_required
        ),
        "memory_domains_verified": (
            tuple(foundation_report.configured_memory_domains)
            == MEMORY_DOMAINS
        ),
        "no_persistent_memory_verified": (
            not foundation_report.persistent_memory_enabled
        ),
        "no_learning_update_verified": (
            not foundation_report.learning_update_enabled
        ),
        "no_learner_execution_verified": (
            not foundation_report.learner_execution_performed
        ),
        "no_memory_write_verified": (
            not foundation_report.memory_write_performed
        ),
        "no_database_access_verified": (
            not foundation_report.database_access_performed
        ),
        "no_networking_verified": (
            not foundation_report.networking_performed
        ),
        "no_runtime_mutation_verified": (
            not foundation_report.runtime_artifact_created
            and not foundation_report.runtime_artifact_modified
        ),
        "publication_disabled_verified": (
            not foundation_report.publication_allowed
        ),
        "action_authorization_disabled_verified": (
            not foundation_report.action_authorization_allowed
        ),
        "qseries_execution_disabled_verified": (
            not foundation_report.qseries_execution_allowed
        ),
        "foundation_ready_verified": (
            foundation_report.foundation_ready
        ),
        "upstream_continuation_authorized": (
            foundation_report.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if failed:
        _reject(
            "OML-002 foundation admission failed: "
            + ", ".join(failed)
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "repository_root": str(root),
        "upstream_schema_version": foundation_report.schema_version,
        "upstream_engine_id": foundation_report.engine_id,
        "upstream_policy_id": foundation_report.policy_id,
        "upstream_report_hash": foundation_report.report_hash,
        "upstream_certification_hash": upstream.certification_hash,
        "upstream_oit_report_hash": upstream.upstream_report_hash,
        "upstream_oit_runner_sha256": upstream.upstream_runner_sha256,
        "configured_memory_domains": MEMORY_DOMAINS,
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = OracleMemoryLearnerFoundationAdmissionDecision(
        **body,
        decision_hash=_stable_hash(body),
    )

    verify_oracle_memory_learner_foundation_admission_decision(
        decision
    )
    return decision


def verify_oracle_memory_learner_foundation_admission_decision(
    decision: OracleMemoryLearnerFoundationAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-002 admission decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-002 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-002 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-002 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-002 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-002 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-002 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-002 admitted upstream policy mismatch")

    hashes = (
        decision.upstream_report_hash,
        decision.upstream_certification_hash,
        decision.upstream_oit_report_hash,
        decision.upstream_oit_runner_sha256,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in hashes):
        _reject("OML-002 lineage hash length invalid")

    if tuple(decision.configured_memory_domains) != MEMORY_DOMAINS:
        _reject("OML-002 memory-domain lineage mismatch")

    required_true = (
        decision.foundation_verified,
        decision.subsystem_identity_verified,
        decision.package_separation_verified,
        decision.certified_read_only_consumption_verified,
        decision.deterministic_contract_verified,
        decision.replay_contract_verified,
        decision.immutable_lineage_verified,
        decision.auditability_verified,
        decision.memory_domains_verified,
        decision.no_persistent_memory_verified,
        decision.no_learning_update_verified,
        decision.no_learner_execution_verified,
        decision.no_memory_write_verified,
        decision.no_database_access_verified,
        decision.no_networking_verified,
        decision.no_runtime_mutation_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.foundation_ready_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )

    if not all(required_true):
        _reject("OML-002 admitted decision missing required guarantee")

    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-002 admission status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-002 admitted decision contains failure reason")

    return True
