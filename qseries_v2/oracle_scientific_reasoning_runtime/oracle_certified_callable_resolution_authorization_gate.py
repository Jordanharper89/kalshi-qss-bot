from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_scientific_reasoning_callable_resolution_engine import (
    ScientificReasoningCallableResolutionPackage,
    verify_scientific_reasoning_callable_resolution_package,
)

ENGINE_ID = "OSR-004"
SCHEMA_VERSION = "OSR-004.v1"
ALGORITHM_VERSION = "certified-callable-resolution-authorization-gate.v1"

AUTHORIZATION_STATUS = (
    "certified_callable_resolution_authorized_read_only_single_scope"
)


class OracleCertifiedCallableResolutionAuthorizationInvariantError(ValueError):
    """Raised when an OSR-004 authorization invariant is violated."""


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
class CertifiedCallableResolutionAuthorization:
    authorization_id: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    source_registry_id: str
    source_registry_hash: str
    source_oii015_certification_hash: str
    source_frozen_evidence_set_hash: str
    authorized_disciplines: tuple[str, ...]
    authorized_callable_count: int
    callable_resolution_authorized: bool
    authorization_scope: str
    authorization_status: str
    authorization_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    callable_activation_allowed: bool
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


def authorize_certified_callable_resolution(
    *,
    resolution_package: ScientificReasoningCallableResolutionPackage,
) -> CertifiedCallableResolutionAuthorization:
    try:
        verify_scientific_reasoning_callable_resolution_package(
            resolution_package
        )
    except Exception as exc:
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "OSR-003 resolution package verification failed"
        ) from exc

    if resolution_package.resolved_callable_count <= 0:
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "resolution package contains no resolved callables"
        )
    if resolution_package.unresolved_callable_count != 0:
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "unresolved callables cannot be authorized"
        )
    if not resolution_package.resolved_disciplines:
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "resolved discipline lineage is empty"
        )

    body = {
        "source_resolution_package_id":
            resolution_package.resolution_package_id,
        "source_resolution_hash": resolution_package.resolution_hash,
        "source_admission_package_id":
            resolution_package.source_admission_package_id,
        "source_admission_hash":
            resolution_package.source_admission_hash,
        "source_registry_id": resolution_package.source_registry_id,
        "source_registry_hash": resolution_package.source_registry_hash,
        "source_oii015_certification_hash":
            resolution_package.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            resolution_package.source_frozen_evidence_set_hash,
        "authorized_disciplines":
            resolution_package.resolved_disciplines,
        "authorized_callable_count":
            resolution_package.resolved_callable_count,
        "callable_resolution_authorized": True,
        "authorization_scope":
            "consume_exact_osr003_resolution_hash_once",
        "authorization_status": AUTHORIZATION_STATUS,
    }
    authorization_hash = stable_hash(body)

    return CertifiedCallableResolutionAuthorization(
        authorization_id=(
            "certified-callable-resolution-authorization:"
            + authorization_hash
        ),
        **body,
        authorization_hash=authorization_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        callable_activation_allowed=False,
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


def verify_certified_callable_resolution_authorization(
    authorization: CertifiedCallableResolutionAuthorization,
) -> bool:
    if not isinstance(
        authorization,
        CertifiedCallableResolutionAuthorization,
    ):
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "invalid resolution authorization"
        )

    body = {
        "source_resolution_package_id":
            authorization.source_resolution_package_id,
        "source_resolution_hash": authorization.source_resolution_hash,
        "source_admission_package_id":
            authorization.source_admission_package_id,
        "source_admission_hash": authorization.source_admission_hash,
        "source_registry_id": authorization.source_registry_id,
        "source_registry_hash": authorization.source_registry_hash,
        "source_oii015_certification_hash":
            authorization.source_oii015_certification_hash,
        "source_frozen_evidence_set_hash":
            authorization.source_frozen_evidence_set_hash,
        "authorized_disciplines": authorization.authorized_disciplines,
        "authorized_callable_count":
            authorization.authorized_callable_count,
        "callable_resolution_authorized":
            authorization.callable_resolution_authorized,
        "authorization_scope": authorization.authorization_scope,
        "authorization_status": authorization.authorization_status,
    }
    expected_hash = stable_hash(body)

    if authorization.authorization_hash != expected_hash:
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "resolution authorization hash verification failed"
        )
    if authorization.authorization_id != (
        "certified-callable-resolution-authorization:" + expected_hash
    ):
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "resolution authorization identity verification failed"
        )
    if (
        authorization.authorized_callable_count
        != len(authorization.authorized_disciplines)
        or authorization.authorized_callable_count <= 0
    ):
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "authorized callable count mismatch"
        )
    if len(set(authorization.authorized_disciplines)) != len(
        authorization.authorized_disciplines
    ):
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "duplicate authorized discipline detected"
        )

    forbidden = (
        authorization.callable_activation_allowed,
        authorization.callable_binding_allowed,
        authorization.reasoning_execution_allowed,
        authorization.probability_estimation_allowed,
        authorization.final_intelligence_conclusion_allowed,
        authorization.publication_allowed,
        authorization.alerting_allowed,
        authorization.qseries_handoff_allowed,
        authorization.qseries_execution_allowed,
        authorization.order_creation_allowed,
        authorization.funds_movement_allowed,
        authorization.portfolio_mutation_allowed,
    )
    if (
        authorization.engine_id != ENGINE_ID
        or authorization.read_only is not True
        or authorization.callable_resolution_authorized is not True
        or authorization.authorization_scope
        != "consume_exact_osr003_resolution_hash_once"
        or authorization.authorization_status != AUTHORIZATION_STATUS
        or any(forbidden)
    ):
        raise OracleCertifiedCallableResolutionAuthorizationInvariantError(
            "OSR-004 permanent safety boundary violated"
        )
    return True


def serialize_certified_callable_resolution_authorization(
    authorization: CertifiedCallableResolutionAuthorization,
) -> str:
    verify_certified_callable_resolution_authorization(authorization)
    return canonical_json(authorization)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "AUTHORIZATION_STATUS",
    "OracleCertifiedCallableResolutionAuthorizationInvariantError",
    "CertifiedCallableResolutionAuthorization",
    "authorize_certified_callable_resolution",
    "verify_certified_callable_resolution_authorization",
    "serialize_certified_callable_resolution_authorization",
]
