from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_certified_callable_binding_execution_authorization_gate import (
    verify_certified_callable_binding_execution_authorization,
)

ENGINE_ID = "OSR-011"
SCHEMA_VERSION = "OSR-011.v1"
ALGORITHM_VERSION = (
    "callable-binding-execution-authorization-consumption-activation.v1"
)
ACTIVATION_STATUS = (
    "callable_binding_execution_authorization_consumed_and_activated_"
    "not_bound_not_executed"
)


class OracleCallableBindingExecutionAuthorizationActivationInvariantError(ValueError):
    """Raised when an OSR-011 authorization-consumption invariant fails."""


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
    raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
        "execution-authorization object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            f"missing execution-authorization field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class CallableBindingExecutionAuthorizationActivation:
    activation_id: str
    source_execution_authorization_id: str
    source_execution_authorization_hash: str
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
    execution_authorization_verified: bool
    execution_authorization_consumed: bool
    authorization_consumption_single_use: bool
    exact_authorization_hash_scope_preserved: bool
    bounded_binding_scope_preserved: bool
    deterministic_binding_required: bool
    immutable_binding_result_required: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_execution_activation_enabled: bool
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


def activate_callable_binding_execution_authorization(
    *,
    authorization: Any,
) -> CallableBindingExecutionAuthorizationActivation:
    try:
        verify_certified_callable_binding_execution_authorization(authorization)
    except Exception as exc:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "OSR-010 callable-binding execution authorization verification failed"
        ) from exc

    snapshot = _snapshot(authorization)

    if snapshot.get("read_only") is not True:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "OSR-010 execution authorization must remain read-only"
        )
    if snapshot.get("callable_binding_execution_authorized") is not True:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "callable-binding execution authorization is not enabled"
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
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "OSR-010 authorization violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_execution_authorization_id": str(
            _required(snapshot, "authorization_id")
        ),
        "source_execution_authorization_hash": str(
            _required(snapshot, "authorization_hash")
        ),
        "source_execution_readiness_id": str(
            _required(snapshot, "source_execution_readiness_id")
        ),
        "source_execution_readiness_hash": str(
            _required(snapshot, "source_execution_readiness_hash")
        ),
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
        "execution_authorization_verified": True,
        "execution_authorization_consumed": True,
        "authorization_consumption_single_use": True,
        "exact_authorization_hash_scope_preserved": True,
        "bounded_binding_scope_preserved": True,
        "deterministic_binding_required": True,
        "immutable_binding_result_required": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_execution_activation_enabled": True,
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

    return CallableBindingExecutionAuthorizationActivation(
        activation_id=(
            "callable-binding-execution-authorization-activation:"
            + activation_hash
        ),
        **body,
        activation_hash=activation_hash,
    )


def verify_callable_binding_execution_authorization_activation(
    activation: CallableBindingExecutionAuthorizationActivation,
) -> bool:
    if not isinstance(
        activation,
        CallableBindingExecutionAuthorizationActivation,
    ):
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "invalid callable-binding execution authorization activation"
        )

    body = {
        key: value
        for key, value in asdict(activation).items()
        if key not in {"activation_id", "activation_hash"}
    }
    expected_hash = stable_hash(body)

    if activation.activation_hash != expected_hash:
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "execution-authorization activation hash mismatch"
        )
    if activation.activation_id != (
        "callable-binding-execution-authorization-activation:" + expected_hash
    ):
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "execution-authorization activation identity mismatch"
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
        or activation.execution_authorization_verified is not True
        or activation.execution_authorization_consumed is not True
        or activation.authorization_consumption_single_use is not True
        or activation.exact_authorization_hash_scope_preserved is not True
        or activation.bounded_binding_scope_preserved is not True
        or activation.deterministic_binding_required is not True
        or activation.immutable_binding_result_required is not True
        or activation.callable_binding_execution_activation_enabled is not True
        or activation.read_only is not True
        or activation.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCallableBindingExecutionAuthorizationActivationInvariantError(
            "OSR-011 permanent safety boundary violated"
        )
    return True


def serialize_callable_binding_execution_authorization_activation(
    activation: CallableBindingExecutionAuthorizationActivation,
) -> str:
    verify_callable_binding_execution_authorization_activation(activation)
    return canonical_json(activation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ACTIVATION_STATUS",
    "OracleCallableBindingExecutionAuthorizationActivationInvariantError",
    "CallableBindingExecutionAuthorizationActivation",
    "activate_callable_binding_execution_authorization",
    "verify_callable_binding_execution_authorization_activation",
    "serialize_callable_binding_execution_authorization_activation",
]
