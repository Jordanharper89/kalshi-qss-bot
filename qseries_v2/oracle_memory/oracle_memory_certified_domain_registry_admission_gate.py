from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_certified_domain_registry import (
    ENGINE_ID as OML_003_ENGINE_ID,
    POLICY_ID as OML_003_POLICY_ID,
    REGISTRY_STATUS_CERTIFIED,
    SCHEMA_VERSION as OML_003_SCHEMA_VERSION,
    OracleMemoryCertifiedDomainRegistry,
    verify_oracle_memory_certified_domain_registry,
)
from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)

SCHEMA_VERSION = "OML-004"
ENGINE_ID = "OML-004"
POLICY_ID = "oracle-memory.certified-domain-registry-admission-gate.v1"

UPSTREAM_SCHEMA_VERSION = "OML-003"
UPSTREAM_ENGINE_ID = "OML-003"
UPSTREAM_POLICY_ID = "oracle-memory.certified-domain-registry.v1"

ADMISSION_STATUS_ADMITTED = "admitted"


class OracleMemoryDomainRegistryAdmissionInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryDomainRegistryAdmissionDecision:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_policy_id: str
    upstream_registry_hash: str
    upstream_admission_decision_hash: str
    upstream_foundation_report_hash: str
    upstream_oit_report_hash: str
    upstream_oit_runner_sha256: str
    upstream_registry_status: str
    admitted_domain_ids: tuple[str, ...]
    admitted_domain_hashes: tuple[str, ...]
    admitted_domain_count: int
    registry_verified: bool
    upstream_identity_verified: bool
    upstream_lineage_verified: bool
    domain_count_verified: bool
    domain_identity_set_verified: bool
    domain_order_verified: bool
    domain_identity_uniqueness_verified: bool
    domain_definition_hashes_verified: bool
    all_domains_inactive_verified: bool
    all_domains_non_writing_verified: bool
    all_domains_read_only_verified: bool
    persistent_storage_disabled_verified: bool
    learning_updates_disabled_verified: bool
    runtime_activation_disabled_verified: bool
    database_access_disabled_verified: bool
    networking_disabled_verified: bool
    publication_disabled_verified: bool
    action_authorization_disabled_verified: bool
    qseries_execution_disabled_verified: bool
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

    raise OracleMemoryDomainRegistryAdmissionInvariantError(
        "unsupported OML-004 value type: "
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
    raise OracleMemoryDomainRegistryAdmissionInvariantError(reason)


def build_oracle_memory_domain_registry_admission_decision(
    *,
    registry: OracleMemoryCertifiedDomainRegistry,
) -> OracleMemoryDomainRegistryAdmissionDecision:
    verify_oracle_memory_certified_domain_registry(registry)

    if OML_003_SCHEMA_VERSION != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-004 upstream schema constant mismatch")

    if OML_003_ENGINE_ID != UPSTREAM_ENGINE_ID:
        _reject("OML-004 upstream engine constant mismatch")

    if OML_003_POLICY_ID != UPSTREAM_POLICY_ID:
        _reject("OML-004 upstream policy constant mismatch")

    if registry.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-004 upstream registry schema mismatch")

    if registry.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-004 upstream registry engine mismatch")

    if registry.policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-004 upstream registry policy mismatch")

    domain_ids = tuple(item.domain_id for item in registry.domains)
    domain_hashes = tuple(item.definition_hash for item in registry.domains)

    checks = {
        "registry_verified": True,
        "upstream_identity_verified": (
            registry.subsystem_id == SUBSYSTEM_ID
        ),
        "upstream_lineage_verified": all(
            len(value) == 64
            for value in (
                registry.registry_hash,
                registry.upstream_decision_hash,
                registry.upstream_foundation_report_hash,
                registry.upstream_oit_report_hash,
                registry.upstream_oit_runner_sha256,
            )
        ),
        "domain_count_verified": (
            registry.domain_count == len(MEMORY_DOMAINS)
            and len(registry.domains) == len(MEMORY_DOMAINS)
        ),
        "domain_identity_set_verified": (
            set(domain_ids) == set(MEMORY_DOMAINS)
        ),
        "domain_order_verified": domain_ids == MEMORY_DOMAINS,
        "domain_identity_uniqueness_verified": (
            len(set(domain_ids)) == len(domain_ids)
        ),
        "domain_definition_hashes_verified": (
            len(domain_hashes) == len(MEMORY_DOMAINS)
            and len(set(domain_hashes)) == len(domain_hashes)
            and all(len(value) == 64 for value in domain_hashes)
        ),
        "all_domains_inactive_verified": (
            registry.all_domains_inactive
            and all(
                not item.runtime_activation_authorized
                for item in registry.domains
            )
        ),
        "all_domains_non_writing_verified": (
            registry.all_domains_non_writing
            and all(
                not item.persistent_storage_authorized
                and not item.learning_update_authorized
                for item in registry.domains
            )
        ),
        "all_domains_read_only_verified": (
            registry.all_domains_read_only
            and all(item.read_only for item in registry.domains)
        ),
        "persistent_storage_disabled_verified": all(
            not item.persistent_storage_authorized
            for item in registry.domains
        ),
        "learning_updates_disabled_verified": all(
            not item.learning_update_authorized
            for item in registry.domains
        ),
        "runtime_activation_disabled_verified": all(
            not item.runtime_activation_authorized
            for item in registry.domains
        ),
        "database_access_disabled_verified": (
            registry.no_database_access_authorized
            and all(
                not item.database_access_authorized
                for item in registry.domains
            )
        ),
        "networking_disabled_verified": (
            registry.no_networking_authorized
            and all(
                not item.networking_authorized
                for item in registry.domains
            )
        ),
        "publication_disabled_verified": (
            registry.publication_disabled
            and all(
                not item.publication_authorized
                for item in registry.domains
            )
        ),
        "action_authorization_disabled_verified": (
            registry.action_authorization_disabled
            and all(
                not item.action_authorization_enabled
                for item in registry.domains
            )
        ),
        "qseries_execution_disabled_verified": (
            registry.qseries_execution_disabled
            and all(
                not item.qseries_execution_authorized
                for item in registry.domains
            )
        ),
        "upstream_continuation_authorized": (
            registry.next_certification_authorized
        ),
    }

    failed = [name for name, passed in checks.items() if not passed]

    if registry.registry_status != REGISTRY_STATUS_CERTIFIED:
        failed.append("registry_status")

    if failed:
        _reject(
            "OML-004 registry admission failed: "
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
        "upstream_admission_decision_hash": (
            registry.upstream_decision_hash
        ),
        "upstream_foundation_report_hash": (
            registry.upstream_foundation_report_hash
        ),
        "upstream_oit_report_hash": registry.upstream_oit_report_hash,
        "upstream_oit_runner_sha256": registry.upstream_oit_runner_sha256,
        "upstream_registry_status": registry.registry_status,
        "admitted_domain_ids": domain_ids,
        "admitted_domain_hashes": domain_hashes,
        "admitted_domain_count": len(domain_ids),
        **checks,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admitted": True,
        "next_certification_authorized": True,
        "read_only": True,
        "failure_reason": None,
    }

    decision = OracleMemoryDomainRegistryAdmissionDecision(
        **body,
        decision_hash=_stable_hash(body),
    )

    verify_oracle_memory_domain_registry_admission_decision(decision)
    return decision


def verify_oracle_memory_domain_registry_admission_decision(
    decision: OracleMemoryDomainRegistryAdmissionDecision,
) -> bool:
    body = asdict(decision)
    supplied = body.pop("decision_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-004 decision hash mismatch")

    if decision.schema_version != SCHEMA_VERSION:
        _reject("OML-004 schema mismatch")

    if decision.engine_id != ENGINE_ID:
        _reject("OML-004 engine mismatch")

    if decision.policy_id != POLICY_ID:
        _reject("OML-004 policy mismatch")

    if decision.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-004 subsystem mismatch")

    if decision.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-004 admitted upstream schema mismatch")

    if decision.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-004 admitted upstream engine mismatch")

    if decision.upstream_policy_id != UPSTREAM_POLICY_ID:
        _reject("OML-004 admitted upstream policy mismatch")

    if decision.upstream_registry_status != REGISTRY_STATUS_CERTIFIED:
        _reject("OML-004 admitted registry status mismatch")

    lineage_hashes = (
        decision.upstream_registry_hash,
        decision.upstream_admission_decision_hash,
        decision.upstream_foundation_report_hash,
        decision.upstream_oit_report_hash,
        decision.upstream_oit_runner_sha256,
        decision.decision_hash,
    )

    if any(len(value) != 64 for value in lineage_hashes):
        _reject("OML-004 lineage hash length invalid")

    if decision.admitted_domain_ids != MEMORY_DOMAINS:
        _reject("OML-004 admitted domain identity mismatch")

    if decision.admitted_domain_count != len(MEMORY_DOMAINS):
        _reject("OML-004 admitted domain count mismatch")

    if len(decision.admitted_domain_hashes) != len(MEMORY_DOMAINS):
        _reject("OML-004 admitted domain hash count mismatch")

    if len(set(decision.admitted_domain_hashes)) != len(
        decision.admitted_domain_hashes
    ):
        _reject("OML-004 admitted domain hashes not unique")

    if any(len(value) != 64 for value in decision.admitted_domain_hashes):
        _reject("OML-004 admitted domain hash length invalid")

    required_true = (
        decision.registry_verified,
        decision.upstream_identity_verified,
        decision.upstream_lineage_verified,
        decision.domain_count_verified,
        decision.domain_identity_set_verified,
        decision.domain_order_verified,
        decision.domain_identity_uniqueness_verified,
        decision.domain_definition_hashes_verified,
        decision.all_domains_inactive_verified,
        decision.all_domains_non_writing_verified,
        decision.all_domains_read_only_verified,
        decision.persistent_storage_disabled_verified,
        decision.learning_updates_disabled_verified,
        decision.runtime_activation_disabled_verified,
        decision.database_access_disabled_verified,
        decision.networking_disabled_verified,
        decision.publication_disabled_verified,
        decision.action_authorization_disabled_verified,
        decision.qseries_execution_disabled_verified,
        decision.upstream_continuation_authorized,
        decision.admitted,
        decision.next_certification_authorized,
        decision.read_only,
    )

    if not all(required_true):
        _reject("OML-004 admitted decision missing required guarantee")

    if decision.admission_status != ADMISSION_STATUS_ADMITTED:
        _reject("OML-004 admission status mismatch")

    if decision.failure_reason is not None:
        _reject("OML-004 admitted decision contains failure reason")

    return True
