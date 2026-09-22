from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_certified_callable_binding_authorization_gate import (
    verify_certified_callable_binding_authorization,
)

ENGINE_ID = "OSR-008"
SCHEMA_VERSION = "OSR-008.v1"
ALGORITHM_VERSION = "callable-binding-authorization-consumption-activation.v1"
ACTIVATION_STATUS = "callable_binding_authorization_consumed_and_activated_not_bound"


class OracleCallableBindingAuthorizationActivationInvariantError(ValueError):
    """Raised when an OSR-008 binding-authorization activation invariant fails."""


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
    raise OracleCallableBindingAuthorizationActivationInvariantError(
        "authorization object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            f"missing authorization field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class CallableBindingAuthorizationActivation:
    activation_id: str
    source_binding_authorization_id: str
    source_binding_authorization_hash: str
    source_readiness_id: str
    source_readiness_hash: str
    source_resolution_activation_id: str
    source_resolution_activation_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    authorization_verified: bool
    authorization_consumed: bool
    authorization_consumption_single_use: bool
    exact_authorization_hash_scope_preserved: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_activation_enabled: bool
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
    activation_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    activation_hash: str


def activate_callable_binding_authorization(
    *,
    authorization: Any,
) -> CallableBindingAuthorizationActivation:
    try:
        verify_certified_callable_binding_authorization(authorization)
    except Exception as exc:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "OSR-007 callable-binding authorization verification failed"
        ) from exc

    snapshot = _snapshot(authorization)

    if snapshot.get("read_only") is not True:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "OSR-007 authorization must remain read-only"
        )
    if snapshot.get("callable_binding_authorized") is not True:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "callable binding authorization is not enabled"
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
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "OSR-007 authorization violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_binding_authorization_id": str(
            _required(snapshot, "authorization_id")
        ),
        "source_binding_authorization_hash": str(
            _required(snapshot, "authorization_hash")
        ),
        "source_readiness_id": str(_required(snapshot, "source_readiness_id")),
        "source_readiness_hash": str(_required(snapshot, "source_readiness_hash")),
        "source_resolution_activation_id": str(
            _required(snapshot, "source_activation_id")
        ),
        "source_resolution_activation_hash": str(
            _required(snapshot, "source_activation_hash")
        ),
        "source_resolution_authorization_id": str(
            _required(snapshot, "source_authorization_id")
        ),
        "source_resolution_authorization_hash": str(
            _required(snapshot, "source_authorization_hash")
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
        "authorization_verified": True,
        "authorization_consumed": True,
        "authorization_consumption_single_use": True,
        "exact_authorization_hash_scope_preserved": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_activation_enabled": True,
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
        "activation_status": ACTIVATION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    activation_hash = stable_hash(body)

    return CallableBindingAuthorizationActivation(
        activation_id="callable-binding-activation:" + activation_hash,
        **body,
        activation_hash=activation_hash,
    )


def verify_callable_binding_authorization_activation(
    activation: CallableBindingAuthorizationActivation,
) -> bool:
    if not isinstance(activation, CallableBindingAuthorizationActivation):
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "invalid callable-binding authorization activation"
        )

    body = {
        key: value
        for key, value in asdict(activation).items()
        if key not in {"activation_id", "activation_hash"}
    }
    expected_hash = stable_hash(body)

    if activation.activation_hash != expected_hash:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "callable-binding activation hash mismatch"
        )
    if activation.activation_id != "callable-binding-activation:" + expected_hash:
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "callable-binding activation identity mismatch"
        )

    forbidden = (
        activation.implementation_import_allowed,
        activation.implementation_symbol_load_allowed,
        activation.callable_binding_allowed,
        activation.reasoning_execution_allowed,
        activation.probability_estimation_allowed,
        activation.final_intelligence_conclusion_allowed,
        activation.publication_allowed,
        activation.alerting_allowed,
        activation.qseries_handoff_allowed,
        activation.qseries_execution_allowed,
        activation.order_creation_allowed,
        activation.funds_movement_allowed,
        activation.portfolio_mutation_allowed,
    )
    if (
        activation.engine_id != ENGINE_ID
        or activation.schema_version != SCHEMA_VERSION
        or activation.algorithm_version != ALGORITHM_VERSION
        or activation.activation_status != ACTIVATION_STATUS
        or activation.authorization_verified is not True
        or activation.authorization_consumed is not True
        or activation.authorization_consumption_single_use is not True
        or activation.exact_authorization_hash_scope_preserved is not True
        or activation.callable_binding_activation_enabled is not True
        or activation.read_only is not True
        or activation.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCallableBindingAuthorizationActivationInvariantError(
            "OSR-008 permanent safety boundary violated"
        )
    return True


def serialize_callable_binding_authorization_activation(
    activation: CallableBindingAuthorizationActivation,
) -> str:
    verify_callable_binding_authorization_activation(activation)
    return canonical_json(activation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ACTIVATION_STATUS",
    "OracleCallableBindingAuthorizationActivationInvariantError",
    "CallableBindingAuthorizationActivation",
    "activate_callable_binding_authorization",
    "verify_callable_binding_authorization_activation",
    "serialize_callable_binding_authorization_activation",
]
