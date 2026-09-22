from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from qseries_v2.oracle_memory.oracle_memory_continuous_intelligence_learner_foundation import (
    MEMORY_DOMAINS,
    SUBSYSTEM_ID,
)
from qseries_v2.oracle_memory.oracle_memory_learner_foundation_admission_gate import (
    OracleMemoryLearnerFoundationAdmissionDecision,
    verify_oracle_memory_learner_foundation_admission_decision,
)

SCHEMA_VERSION = "OML-003"
ENGINE_ID = "OML-003"
POLICY_ID = "oracle-memory.certified-domain-registry.v1"

UPSTREAM_SCHEMA_VERSION = "OML-002"
UPSTREAM_ENGINE_ID = "OML-002"
REGISTRY_STATUS_CERTIFIED = "certified_inactive"
DOMAIN_KIND_MEMORY = "memory"


class OracleMemoryDomainRegistryInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleMemoryDomainDefinition:
    domain_id: str
    domain_kind: str
    ordinal: int
    persistent_storage_authorized: bool
    learning_update_authorized: bool
    runtime_activation_authorized: bool
    database_access_authorized: bool
    networking_authorized: bool
    publication_authorized: bool
    action_authorization_enabled: bool
    qseries_execution_authorized: bool
    read_only: bool
    definition_hash: str


@dataclass(frozen=True)
class OracleMemoryCertifiedDomainRegistry:
    schema_version: str
    engine_id: str
    policy_id: str
    subsystem_id: str
    upstream_schema_version: str
    upstream_engine_id: str
    upstream_decision_hash: str
    upstream_foundation_report_hash: str
    upstream_oit_report_hash: str
    upstream_oit_runner_sha256: str
    registry_status: str
    domains: tuple[OracleMemoryDomainDefinition, ...]
    domain_count: int
    registry_complete: bool
    domain_order_canonical: bool
    identities_unique: bool
    all_domains_inactive: bool
    all_domains_non_writing: bool
    all_domains_read_only: bool
    no_database_access_authorized: bool
    no_networking_authorized: bool
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

    raise OracleMemoryDomainRegistryInvariantError(
        "unsupported OML-003 value type: "
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
    raise OracleMemoryDomainRegistryInvariantError(reason)


def _build_domain(
    domain_id: str,
    ordinal: int,
) -> OracleMemoryDomainDefinition:
    body = {
        "domain_id": domain_id,
        "domain_kind": DOMAIN_KIND_MEMORY,
        "ordinal": ordinal,
        "persistent_storage_authorized": False,
        "learning_update_authorized": False,
        "runtime_activation_authorized": False,
        "database_access_authorized": False,
        "networking_authorized": False,
        "publication_authorized": False,
        "action_authorization_enabled": False,
        "qseries_execution_authorized": False,
        "read_only": True,
    }

    return OracleMemoryDomainDefinition(
        **body,
        definition_hash=_stable_hash(body),
    )


def verify_oracle_memory_domain_definition(
    definition: OracleMemoryDomainDefinition,
) -> bool:
    body = asdict(definition)
    supplied = body.pop("definition_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-003 domain definition hash mismatch")

    if definition.domain_id not in MEMORY_DOMAINS:
        _reject("OML-003 unknown memory domain")

    expected_ordinal = MEMORY_DOMAINS.index(definition.domain_id) + 1

    if definition.ordinal != expected_ordinal:
        _reject("OML-003 memory domain ordinal mismatch")

    if definition.domain_kind != DOMAIN_KIND_MEMORY:
        _reject("OML-003 memory domain kind mismatch")

    forbidden = (
        definition.persistent_storage_authorized,
        definition.learning_update_authorized,
        definition.runtime_activation_authorized,
        definition.database_access_authorized,
        definition.networking_authorized,
        definition.publication_authorized,
        definition.action_authorization_enabled,
        definition.qseries_execution_authorized,
    )

    if any(forbidden):
        _reject("OML-003 forbidden domain capability enabled")

    if not definition.read_only:
        _reject("OML-003 memory domain is not read-only")

    return True


def build_oracle_memory_certified_domain_registry(
    *,
    admission_decision: OracleMemoryLearnerFoundationAdmissionDecision,
) -> OracleMemoryCertifiedDomainRegistry:
    verify_oracle_memory_learner_foundation_admission_decision(
        admission_decision
    )

    if admission_decision.schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-003 upstream schema mismatch")

    if admission_decision.engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-003 upstream engine mismatch")

    if not admission_decision.admitted:
        _reject("OML-003 upstream admission not granted")

    if not admission_decision.next_certification_authorized:
        _reject("OML-003 upstream continuation not authorized")

    if not admission_decision.read_only:
        _reject("OML-003 upstream read-only guarantee missing")

    if tuple(admission_decision.configured_memory_domains) != MEMORY_DOMAINS:
        _reject("OML-003 upstream memory-domain lineage mismatch")

    domains = tuple(
        _build_domain(domain_id, index)
        for index, domain_id in enumerate(MEMORY_DOMAINS, start=1)
    )

    for definition in domains:
        verify_oracle_memory_domain_definition(definition)

    domain_ids = tuple(item.domain_id for item in domains)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "subsystem_id": SUBSYSTEM_ID,
        "upstream_schema_version": admission_decision.schema_version,
        "upstream_engine_id": admission_decision.engine_id,
        "upstream_decision_hash": admission_decision.decision_hash,
        "upstream_foundation_report_hash": (
            admission_decision.upstream_report_hash
        ),
        "upstream_oit_report_hash": (
            admission_decision.upstream_oit_report_hash
        ),
        "upstream_oit_runner_sha256": (
            admission_decision.upstream_oit_runner_sha256
        ),
        "registry_status": REGISTRY_STATUS_CERTIFIED,
        "domains": domains,
        "domain_count": len(domains),
        "registry_complete": len(domains) == len(MEMORY_DOMAINS),
        "domain_order_canonical": domain_ids == MEMORY_DOMAINS,
        "identities_unique": len(set(domain_ids)) == len(domain_ids),
        "all_domains_inactive": all(
            not item.runtime_activation_authorized
            for item in domains
        ),
        "all_domains_non_writing": all(
            not item.persistent_storage_authorized
            and not item.learning_update_authorized
            for item in domains
        ),
        "all_domains_read_only": all(
            item.read_only
            for item in domains
        ),
        "no_database_access_authorized": all(
            not item.database_access_authorized
            for item in domains
        ),
        "no_networking_authorized": all(
            not item.networking_authorized
            for item in domains
        ),
        "publication_disabled": all(
            not item.publication_authorized
            for item in domains
        ),
        "action_authorization_disabled": all(
            not item.action_authorization_enabled
            for item in domains
        ),
        "qseries_execution_disabled": all(
            not item.qseries_execution_authorized
            for item in domains
        ),
        "next_certification_authorized": True,
    }

    registry = OracleMemoryCertifiedDomainRegistry(
        **body,
        registry_hash=_stable_hash(body),
    )

    verify_oracle_memory_certified_domain_registry(registry)
    return registry


def verify_oracle_memory_certified_domain_registry(
    registry: OracleMemoryCertifiedDomainRegistry,
) -> bool:
    body = asdict(registry)
    supplied = body.pop("registry_hash")

    if _stable_hash(body) != supplied:
        _reject("OML-003 registry hash mismatch")

    if registry.schema_version != SCHEMA_VERSION:
        _reject("OML-003 schema mismatch")

    if registry.engine_id != ENGINE_ID:
        _reject("OML-003 engine mismatch")

    if registry.policy_id != POLICY_ID:
        _reject("OML-003 policy mismatch")

    if registry.subsystem_id != SUBSYSTEM_ID:
        _reject("OML-003 subsystem mismatch")

    if registry.upstream_schema_version != UPSTREAM_SCHEMA_VERSION:
        _reject("OML-003 certified upstream schema mismatch")

    if registry.upstream_engine_id != UPSTREAM_ENGINE_ID:
        _reject("OML-003 certified upstream engine mismatch")

    lineage_hashes = (
        registry.upstream_decision_hash,
        registry.upstream_foundation_report_hash,
        registry.upstream_oit_report_hash,
        registry.upstream_oit_runner_sha256,
        registry.registry_hash,
    )

    if any(len(value) != 64 for value in lineage_hashes):
        _reject("OML-003 lineage hash length invalid")

    if registry.registry_status != REGISTRY_STATUS_CERTIFIED:
        _reject("OML-003 registry status mismatch")

    if registry.domain_count != len(MEMORY_DOMAINS):
        _reject("OML-003 domain count mismatch")

    if tuple(item.domain_id for item in registry.domains) != MEMORY_DOMAINS:
        _reject("OML-003 domain identity or order mismatch")

    for definition in registry.domains:
        verify_oracle_memory_domain_definition(definition)

    required_true = (
        registry.registry_complete,
        registry.domain_order_canonical,
        registry.identities_unique,
        registry.all_domains_inactive,
        registry.all_domains_non_writing,
        registry.all_domains_read_only,
        registry.no_database_access_authorized,
        registry.no_networking_authorized,
        registry.publication_disabled,
        registry.action_authorization_disabled,
        registry.qseries_execution_disabled,
        registry.next_certification_authorized,
    )

    if not all(required_true):
        _reject("OML-003 registry guarantee missing")

    return True
