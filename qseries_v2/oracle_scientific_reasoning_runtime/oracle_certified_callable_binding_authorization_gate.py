from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_callable_binding_readiness_gate import (
    verify_callable_binding_readiness,
)

ENGINE_ID = "OSR-007"
SCHEMA_VERSION = "OSR-007.v1"
ALGORITHM_VERSION = "certified-callable-binding-authorization.v1"
AUTHORIZATION_STATUS = "callable_binding_authorized_not_consumed"


class OracleCertifiedCallableBindingAuthorizationInvariantError(ValueError):
    """Raised when an OSR-007 callable-binding authorization invariant fails."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if is_dataclass(value):
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


def _snapshot(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    data = getattr(value, "__dict__", None)
    if isinstance(data, dict):
        return dict(data)
    raise OracleCertifiedCallableBindingAuthorizationInvariantError(
        "readiness object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            f"missing readiness field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class CertifiedCallableBindingAuthorization:
    authorization_id: str
    source_readiness_id: str
    source_readiness_hash: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    binding_readiness_verified: bool
    exact_readiness_hash_scope_preserved: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_authorized: bool
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
    read_only: bool
    authorization_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    authorization_hash: str


def authorize_callable_binding(
    *,
    readiness: Any,
) -> CertifiedCallableBindingAuthorization:
    try:
        verify_callable_binding_readiness(readiness)
    except Exception as exc:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "OSR-006 callable-binding readiness verification failed"
        ) from exc

    snapshot = _snapshot(readiness)

    if snapshot.get("read_only") is not True:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "OSR-006 readiness must remain read-only"
        )
    if snapshot.get("callable_binding_ready") is not True:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "callable binding readiness is not certified"
        )

    forbidden_source_flags = (
        bool(snapshot.get("implementation_import_allowed", False)),
        bool(snapshot.get("implementation_symbol_load_allowed", False)),
        bool(snapshot.get("callable_binding_allowed", False)),
        bool(snapshot.get("reasoning_execution_allowed", False)),
        bool(snapshot.get("probability_estimation_allowed", False)),
        bool(snapshot.get("final_intelligence_conclusion_allowed", False)),
        bool(snapshot.get("publication_allowed", False)),
        bool(snapshot.get("alerting_allowed", False)),
        bool(snapshot.get("qseries_handoff_allowed", False)),
        bool(snapshot.get("qseries_execution_allowed", False)),
        bool(snapshot.get("order_creation_allowed", False)),
        bool(snapshot.get("funds_movement_allowed", False)),
        bool(snapshot.get("portfolio_mutation_allowed", False)),
    )
    if any(forbidden_source_flags):
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "OSR-006 readiness violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_readiness_id": str(_required(snapshot, "readiness_id")),
        "source_readiness_hash": str(_required(snapshot, "readiness_hash")),
        "source_activation_id": str(_required(snapshot, "source_activation_id")),
        "source_activation_hash": str(_required(snapshot, "source_activation_hash")),
        "source_authorization_id": str(_required(snapshot, "source_authorization_id")),
        "source_authorization_hash": str(_required(snapshot, "source_authorization_hash")),
        "source_resolution_package_id": str(
            _required(snapshot, "source_resolution_package_id")
        ),
        "source_resolution_hash": str(_required(snapshot, "source_resolution_hash")),
        "source_admission_package_id": str(
            _required(snapshot, "source_admission_package_id")
        ),
        "source_admission_hash": str(_required(snapshot, "source_admission_hash")),
        "callable_count": callable_count,
        "binding_readiness_verified": True,
        "exact_readiness_hash_scope_preserved": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_authorized": True,
        "callable_binding_allowed": False,
        "reasoning_execution_allowed": False,
        "probability_estimation_allowed": False,
        "final_intelligence_conclusion_allowed": False,
        "publication_allowed": False,
        "alerting_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "read_only": True,
        "authorization_status": AUTHORIZATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    authorization_hash = stable_hash(body)

    return CertifiedCallableBindingAuthorization(
        authorization_id="callable-binding-authorization:" + authorization_hash,
        **body,
        authorization_hash=authorization_hash,
    )


def verify_certified_callable_binding_authorization(
    authorization: CertifiedCallableBindingAuthorization,
) -> bool:
    if not isinstance(authorization, CertifiedCallableBindingAuthorization):
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "invalid callable-binding authorization"
        )

    body = {
        key: value
        for key, value in asdict(authorization).items()
        if key not in {"authorization_id", "authorization_hash"}
    }
    expected_hash = stable_hash(body)
    if authorization.authorization_hash != expected_hash:
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "callable-binding authorization hash mismatch"
        )
    if authorization.authorization_id != (
        "callable-binding-authorization:" + expected_hash
    ):
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "callable-binding authorization identity mismatch"
        )

    forbidden = (
        authorization.implementation_import_allowed,
        authorization.implementation_symbol_load_allowed,
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
        or authorization.schema_version != SCHEMA_VERSION
        or authorization.algorithm_version != ALGORITHM_VERSION
        or authorization.authorization_status != AUTHORIZATION_STATUS
        or authorization.binding_readiness_verified is not True
        or authorization.exact_readiness_hash_scope_preserved is not True
        or authorization.callable_binding_authorized is not True
        or authorization.read_only is not True
        or authorization.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCertifiedCallableBindingAuthorizationInvariantError(
            "OSR-007 permanent safety boundary violated"
        )
    return True


def serialize_certified_callable_binding_authorization(
    authorization: CertifiedCallableBindingAuthorization,
) -> str:
    verify_certified_callable_binding_authorization(authorization)
    return canonical_json(authorization)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "AUTHORIZATION_STATUS",
    "OracleCertifiedCallableBindingAuthorizationInvariantError",
    "CertifiedCallableBindingAuthorization",
    "authorize_callable_binding",
    "verify_certified_callable_binding_authorization",
    "serialize_certified_callable_binding_authorization",
]
