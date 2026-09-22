from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_callable_binding_execution_readiness_gate import (
    verify_callable_binding_execution_readiness,
)

ENGINE_ID = "OSR-010"
SCHEMA_VERSION = "OSR-010.v1"
ALGORITHM_VERSION = "certified-callable-binding-execution-authorization.v1"
AUTHORIZATION_STATUS = (
    "callable_binding_execution_authorized_not_consumed_not_executed"
)


class OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(ValueError):
    """Raised when an OSR-010 execution-authorization invariant fails."""


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
    raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
        "execution-readiness object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            f"missing execution-readiness field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class CertifiedCallableBindingExecutionAuthorization:
    authorization_id: str
    source_execution_readiness_id: str
    source_execution_readiness_hash: str
    source_binding_activation_id: str
    source_binding_activation_hash: str
    source_binding_authorization_id: str
    source_binding_authorization_hash: str
    source_binding_readiness_id: str
    source_binding_readiness_hash: str
    source_resolution_activation_id: str
    source_resolution_activation_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    execution_readiness_verified: bool
    exact_readiness_hash_scope_preserved: bool
    bounded_binding_scope_preserved: bool
    deterministic_binding_required: bool
    immutable_binding_result_required: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_execution_authorized: bool
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


def authorize_callable_binding_execution(
    *,
    readiness: Any,
) -> CertifiedCallableBindingExecutionAuthorization:
    try:
        verify_callable_binding_execution_readiness(readiness)
    except Exception as exc:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "OSR-009 callable-binding execution readiness verification failed"
        ) from exc

    snapshot = _snapshot(readiness)

    if snapshot.get("read_only") is not True:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "OSR-009 execution readiness must remain read-only"
        )
    if snapshot.get("callable_binding_execution_ready") is not True:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "callable-binding execution readiness is not certified"
        )
    if snapshot.get("callable_binding_execution_authorized") is not False:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "OSR-009 must not already authorize execution"
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
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "OSR-009 readiness violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_execution_readiness_id": str(_required(snapshot, "readiness_id")),
        "source_execution_readiness_hash": str(_required(snapshot, "readiness_hash")),
        "source_binding_activation_id": str(
            _required(snapshot, "source_binding_activation_id")
        ),
        "source_binding_activation_hash": str(
            _required(snapshot, "source_binding_activation_hash")
        ),
        "source_binding_authorization_id": str(
            _required(snapshot, "source_binding_authorization_id")
        ),
        "source_binding_authorization_hash": str(
            _required(snapshot, "source_binding_authorization_hash")
        ),
        "source_binding_readiness_id": str(
            _required(snapshot, "source_binding_readiness_id")
        ),
        "source_binding_readiness_hash": str(
            _required(snapshot, "source_binding_readiness_hash")
        ),
        "source_resolution_activation_id": str(
            _required(snapshot, "source_resolution_activation_id")
        ),
        "source_resolution_activation_hash": str(
            _required(snapshot, "source_resolution_activation_hash")
        ),
        "source_resolution_authorization_id": str(
            _required(snapshot, "source_resolution_authorization_id")
        ),
        "source_resolution_authorization_hash": str(
            _required(snapshot, "source_resolution_authorization_hash")
        ),
        "source_resolution_package_id": str(
            _required(snapshot, "source_resolution_package_id")
        ),
        "source_resolution_hash": str(
            _required(snapshot, "source_resolution_hash")
        ),
        "source_admission_package_id": str(
            _required(snapshot, "source_admission_package_id")
        ),
        "source_admission_hash": str(
            _required(snapshot, "source_admission_hash")
        ),
        "callable_count": callable_count,
        "execution_readiness_verified": True,
        "exact_readiness_hash_scope_preserved": True,
        "bounded_binding_scope_preserved": True,
        "deterministic_binding_required": True,
        "immutable_binding_result_required": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_execution_authorized": True,
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

    return CertifiedCallableBindingExecutionAuthorization(
        authorization_id=(
            "callable-binding-execution-authorization:" + authorization_hash
        ),
        **body,
        authorization_hash=authorization_hash,
    )


def verify_certified_callable_binding_execution_authorization(
    authorization: CertifiedCallableBindingExecutionAuthorization,
) -> bool:
    if not isinstance(
        authorization,
        CertifiedCallableBindingExecutionAuthorization,
    ):
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "invalid callable-binding execution authorization"
        )

    body = {
        key: value
        for key, value in asdict(authorization).items()
        if key not in {"authorization_id", "authorization_hash"}
    }
    expected_hash = stable_hash(body)

    if authorization.authorization_hash != expected_hash:
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "callable-binding execution authorization hash mismatch"
        )
    if authorization.authorization_id != (
        "callable-binding-execution-authorization:" + expected_hash
    ):
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "callable-binding execution authorization identity mismatch"
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
        or authorization.execution_readiness_verified is not True
        or authorization.exact_readiness_hash_scope_preserved is not True
        or authorization.bounded_binding_scope_preserved is not True
        or authorization.deterministic_binding_required is not True
        or authorization.immutable_binding_result_required is not True
        or authorization.callable_binding_execution_authorized is not True
        or authorization.read_only is not True
        or authorization.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCertifiedCallableBindingExecutionAuthorizationInvariantError(
            "OSR-010 permanent safety boundary violated"
        )
    return True


def serialize_certified_callable_binding_execution_authorization(
    authorization: CertifiedCallableBindingExecutionAuthorization,
) -> str:
    verify_certified_callable_binding_execution_authorization(authorization)
    return canonical_json(authorization)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "AUTHORIZATION_STATUS",
    "OracleCertifiedCallableBindingExecutionAuthorizationInvariantError",
    "CertifiedCallableBindingExecutionAuthorization",
    "authorize_callable_binding_execution",
    "verify_certified_callable_binding_execution_authorization",
    "serialize_certified_callable_binding_execution_authorization",
]
