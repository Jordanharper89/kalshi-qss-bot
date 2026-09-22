from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .oracle_scientific_reasoning_callable_registry import (
    APPROVED_DISCIPLINES,
    ScientificReasoningCallableDescriptor,
    ScientificReasoningCallableRegistry,
    verify_scientific_reasoning_callable_descriptor,
    verify_scientific_reasoning_callable_registry,
)

ENGINE_ID = "OSR-002"
SCHEMA_VERSION = "OSR-002.v1"
ALGORITHM_VERSION = "certified-callable-admission-gate.v1"

ADMISSION_STATUS_ADMITTED = "admitted_inactive_unresolved_unbound"
REGISTRY_STATUS_ADMITTED = "certified_registry_admitted_read_only"


class OracleCertifiedCallableAdmissionInvariantError(ValueError):
    """Raised when an OSR-002 callable-admission invariant is violated."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CertifiedCallableAdmissionPolicy:
    policy_id: str
    allowed_disciplines: tuple[str, ...]
    require_read_only: bool
    require_inactive: bool
    require_unresolved: bool
    require_unbound: bool
    require_non_executable: bool
    exact_registry_hash_only: bool
    policy_hash: str


@dataclass(frozen=True)
class CertifiedCallableAdmissionRecord:
    discipline_id: str
    callable_id: str
    source_descriptor_hash: str
    implementation_module: str
    implementation_symbol: str
    admitted: bool
    admission_status: str
    admission_reason: str
    active: bool
    resolved: bool
    bound: bool
    executable: bool
    read_only: bool
    admission_record_hash: str


@dataclass(frozen=True)
class CertifiedCallableAdmissionPackage:
    admission_package_id: str
    source_registry_id: str
    source_registry_hash: str
    source_oii015_certification_hash: str
    source_frozen_evidence_set_hash: str
    policy: CertifiedCallableAdmissionPolicy
    admission_records: tuple[CertifiedCallableAdmissionRecord, ...]
    admitted_disciplines: tuple[str, ...]
    admitted_callable_count: int
    rejected_callable_count: int
    registry_admitted: bool
    admission_status: str
    admission_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    callable_activation_allowed: bool
    callable_resolution_allowed: bool
    callable_binding_allowed: bool
    reasoning_execution_allowed: bool
    probability_estimation_allowed: bool
    final_intelligence_conclusion_allowed: bool
    publication_allowed: bool
    alerting_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def build_certified_callable_admission_policy(
    *,
    allowed_disciplines: Sequence[str] = APPROVED_DISCIPLINES,
) -> CertifiedCallableAdmissionPolicy:
    normalized = tuple(sorted({item.strip().lower() for item in allowed_disciplines}))
    if normalized != APPROVED_DISCIPLINES:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission policy must contain the exact approved discipline set"
        )

    body = {
        "allowed_disciplines": normalized,
        "require_read_only": True,
        "require_inactive": True,
        "require_unresolved": True,
        "require_unbound": True,
        "require_non_executable": True,
        "exact_registry_hash_only": True,
    }
    policy_hash = stable_hash(body)
    return CertifiedCallableAdmissionPolicy(
        policy_id="certified-callable-admission-policy:" + policy_hash,
        **body,
        policy_hash=policy_hash,
    )


def verify_certified_callable_admission_policy(
    policy: CertifiedCallableAdmissionPolicy,
) -> bool:
    if not isinstance(policy, CertifiedCallableAdmissionPolicy):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "invalid admission policy"
        )
    body = {
        key: value
        for key, value in asdict(policy).items()
        if key not in {"policy_id", "policy_hash"}
    }
    expected_hash = stable_hash(body)
    if policy.policy_hash != expected_hash:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission policy hash verification failed"
        )
    if policy.policy_id != "certified-callable-admission-policy:" + expected_hash:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission policy identity verification failed"
        )
    if (
        policy.allowed_disciplines != APPROVED_DISCIPLINES
        or not policy.require_read_only
        or not policy.require_inactive
        or not policy.require_unresolved
        or not policy.require_unbound
        or not policy.require_non_executable
        or not policy.exact_registry_hash_only
    ):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission policy boundary violated"
        )
    return True


def _admit_descriptor(
    *,
    descriptor: ScientificReasoningCallableDescriptor,
    policy: CertifiedCallableAdmissionPolicy,
) -> CertifiedCallableAdmissionRecord:
    try:
        verify_scientific_reasoning_callable_descriptor(descriptor)
    except Exception as exc:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor verification failed: {descriptor.discipline_id}"
        ) from exc

    if descriptor.discipline_id not in policy.allowed_disciplines:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"discipline not allowed by policy: {descriptor.discipline_id}"
        )
    if policy.require_read_only and descriptor.read_only is not True:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor is not read-only: {descriptor.callable_id}"
        )
    if policy.require_inactive and descriptor.active:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor is active before admission: {descriptor.callable_id}"
        )
    if policy.require_unresolved and descriptor.resolved:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor is resolved before admission: {descriptor.callable_id}"
        )
    if policy.require_unbound and descriptor.bound:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor is bound before admission: {descriptor.callable_id}"
        )
    if policy.require_non_executable and descriptor.executable:
        raise OracleCertifiedCallableAdmissionInvariantError(
            f"descriptor is executable before admission: {descriptor.callable_id}"
        )

    body = {
        "discipline_id": descriptor.discipline_id,
        "callable_id": descriptor.callable_id,
        "source_descriptor_hash": descriptor.descriptor_hash,
        "implementation_module": descriptor.implementation_module,
        "implementation_symbol": descriptor.implementation_symbol,
        "admitted": True,
        "admission_status": ADMISSION_STATUS_ADMITTED,
        "admission_reason":
            "certified_registry_descriptor_satisfies_read_only_policy",
        "active": False,
        "resolved": False,
        "bound": False,
        "executable": False,
        "read_only": True,
    }
    return CertifiedCallableAdmissionRecord(
        **body,
        admission_record_hash=stable_hash(body),
    )


def admit_certified_scientific_reasoning_callables(
    *,
    registry: ScientificReasoningCallableRegistry,
    policy: CertifiedCallableAdmissionPolicy | None = None,
) -> CertifiedCallableAdmissionPackage:
    try:
        verify_scientific_reasoning_callable_registry(registry)
    except Exception as exc:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "OSR-001 registry verification failed"
        ) from exc

    selected_policy = policy or build_certified_callable_admission_policy()
    verify_certified_callable_admission_policy(selected_policy)

    records = tuple(
        _admit_descriptor(descriptor=item, policy=selected_policy)
        for item in sorted(
            registry.callable_descriptors,
            key=lambda descriptor: descriptor.discipline_id,
        )
    )
    admitted_disciplines = tuple(item.discipline_id for item in records)

    if admitted_disciplines != APPROVED_DISCIPLINES:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admitted discipline lineage is incomplete or out of order"
        )
    if not all(item.admitted for item in records):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "one or more callable descriptors were not admitted"
        )

    body = {
        "source_registry_id": registry.registry_id,
        "source_registry_hash": registry.registry_hash,
        "source_oii015_certification_hash":
            registry.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            registry.source_frozen_evidence_set_hash,
        "policy": selected_policy,
        "admission_records": records,
        "admitted_disciplines": admitted_disciplines,
        "admitted_callable_count": len(records),
        "rejected_callable_count": 0,
        "registry_admitted": True,
        "admission_status": REGISTRY_STATUS_ADMITTED,
    }
    admission_hash = stable_hash(body)

    return CertifiedCallableAdmissionPackage(
        admission_package_id=(
            "certified-callable-admission-package:" + admission_hash
        ),
        **body,
        admission_hash=admission_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        callable_activation_allowed=False,
        callable_resolution_allowed=False,
        callable_binding_allowed=False,
        reasoning_execution_allowed=False,
        probability_estimation_allowed=False,
        final_intelligence_conclusion_allowed=False,
        publication_allowed=False,
        alerting_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def verify_certified_callable_admission_record(
    record: CertifiedCallableAdmissionRecord,
) -> bool:
    if not isinstance(record, CertifiedCallableAdmissionRecord):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "invalid admission record"
        )
    body = {
        key: value
        for key, value in asdict(record).items()
        if key != "admission_record_hash"
    }
    if stable_hash(body) != record.admission_record_hash:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission record hash verification failed"
        )
    if (
        record.discipline_id not in APPROVED_DISCIPLINES
        or record.admitted is not True
        or record.admission_status != ADMISSION_STATUS_ADMITTED
        or record.active
        or record.resolved
        or record.bound
        or record.executable
        or record.read_only is not True
    ):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission record safety boundary violated"
        )
    return True


def verify_certified_callable_admission_package(
    package: CertifiedCallableAdmissionPackage,
) -> bool:
    if not isinstance(package, CertifiedCallableAdmissionPackage):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "invalid admission package"
        )

    verify_certified_callable_admission_policy(package.policy)
    for record in package.admission_records:
        verify_certified_callable_admission_record(record)

    if package.admitted_disciplines != APPROVED_DISCIPLINES:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admitted discipline set mismatch"
        )
    if package.admitted_callable_count != len(package.admission_records):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admitted callable count mismatch"
        )
    if package.rejected_callable_count != 0:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "rejected callable count must remain zero"
        )

    body = {
        "source_registry_id": package.source_registry_id,
        "source_registry_hash": package.source_registry_hash,
        "source_oii015_certification_hash":
            package.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            package.source_frozen_evidence_set_hash,
        "policy": package.policy,
        "admission_records": package.admission_records,
        "admitted_disciplines": package.admitted_disciplines,
        "admitted_callable_count": package.admitted_callable_count,
        "rejected_callable_count": package.rejected_callable_count,
        "registry_admitted": package.registry_admitted,
        "admission_status": package.admission_status,
    }
    if stable_hash(body) != package.admission_hash:
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission package hash verification failed"
        )
    if package.admission_package_id != (
        "certified-callable-admission-package:" + package.admission_hash
    ):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "admission package identity verification failed"
        )

    forbidden = (
        package.callable_activation_allowed,
        package.callable_resolution_allowed,
        package.callable_binding_allowed,
        package.reasoning_execution_allowed,
        package.probability_estimation_allowed,
        package.final_intelligence_conclusion_allowed,
        package.publication_allowed,
        package.alerting_allowed,
        package.qseries_handoff_allowed,
        package.qseries_execution_allowed,
        package.order_creation_allowed,
        package.funds_movement_allowed,
        package.portfolio_mutation_allowed,
    )
    if (
        package.engine_id != ENGINE_ID
        or package.registry_admitted is not True
        or package.admission_status != REGISTRY_STATUS_ADMITTED
        or package.read_only is not True
        or any(forbidden)
    ):
        raise OracleCertifiedCallableAdmissionInvariantError(
            "OSR-002 permanent safety boundary violated"
        )
    return True


def serialize_certified_callable_admission_package(
    package: CertifiedCallableAdmissionPackage,
) -> str:
    verify_certified_callable_admission_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ADMISSION_STATUS_ADMITTED",
    "REGISTRY_STATUS_ADMITTED",
    "OracleCertifiedCallableAdmissionInvariantError",
    "CertifiedCallableAdmissionPolicy",
    "CertifiedCallableAdmissionRecord",
    "CertifiedCallableAdmissionPackage",
    "build_certified_callable_admission_policy",
    "verify_certified_callable_admission_policy",
    "admit_certified_scientific_reasoning_callables",
    "verify_certified_callable_admission_record",
    "verify_certified_callable_admission_package",
    "serialize_certified_callable_admission_package",
]
