from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_callable_binding_authorization_consumption_activation_gate import (
    verify_callable_binding_authorization_activation,
)

ENGINE_ID = "OSR-009"
SCHEMA_VERSION = "OSR-009.v1"
ALGORITHM_VERSION = "callable-binding-execution-readiness.v1"
READINESS_STATUS = "callable_binding_execution_ready_not_authorized_not_executed"


class OracleCallableBindingExecutionReadinessInvariantError(ValueError):
    """Raised when an OSR-009 execution-readiness invariant fails."""


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
    raise OracleCallableBindingExecutionReadinessInvariantError(
        "binding activation object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            f"missing binding activation field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class CallableBindingExecutionReadiness:
    readiness_id: str
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
    binding_activation_verified: bool
    exact_activation_hash_scope_preserved: bool
    bounded_binding_scope: bool
    deterministic_binding_required: bool
    immutable_binding_result_required: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_execution_ready: bool
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
    readiness_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    readiness_hash: str


def certify_callable_binding_execution_readiness(
    *,
    activation: Any,
) -> CallableBindingExecutionReadiness:
    try:
        verify_callable_binding_authorization_activation(activation)
    except Exception as exc:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "OSR-008 callable-binding activation verification failed"
        ) from exc

    snapshot = _snapshot(activation)

    if snapshot.get("read_only") is not True:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "OSR-008 activation must remain read-only"
        )
    if snapshot.get("callable_binding_activation_enabled") is not True:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "callable-binding activation is not enabled"
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
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "OSR-008 activation violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_binding_activation_id": str(_required(snapshot, "activation_id")),
        "source_binding_activation_hash": str(_required(snapshot, "activation_hash")),
        "source_binding_authorization_id": str(
            _required(snapshot, "source_binding_authorization_id")
        ),
        "source_binding_authorization_hash": str(
            _required(snapshot, "source_binding_authorization_hash")
        ),
        "source_binding_readiness_id": str(
            _required(snapshot, "source_readiness_id")
        ),
        "source_binding_readiness_hash": str(
            _required(snapshot, "source_readiness_hash")
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
        "binding_activation_verified": True,
        "exact_activation_hash_scope_preserved": True,
        "bounded_binding_scope": True,
        "deterministic_binding_required": True,
        "immutable_binding_result_required": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_execution_ready": True,
        "callable_binding_execution_authorized": False,
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
        "readiness_status": READINESS_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    readiness_hash = stable_hash(body)

    return CallableBindingExecutionReadiness(
        readiness_id="callable-binding-execution-readiness:" + readiness_hash,
        **body,
        readiness_hash=readiness_hash,
    )


def verify_callable_binding_execution_readiness(
    readiness: CallableBindingExecutionReadiness,
) -> bool:
    if not isinstance(readiness, CallableBindingExecutionReadiness):
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "invalid callable-binding execution-readiness record"
        )

    body = {
        key: value
        for key, value in asdict(readiness).items()
        if key not in {"readiness_id", "readiness_hash"}
    }
    expected_hash = stable_hash(body)

    if readiness.readiness_hash != expected_hash:
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "callable-binding execution-readiness hash mismatch"
        )
    if readiness.readiness_id != (
        "callable-binding-execution-readiness:" + expected_hash
    ):
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "callable-binding execution-readiness identity mismatch"
        )

    forbidden = (
        readiness.implementation_import_allowed,
        readiness.implementation_symbol_load_allowed,
        readiness.callable_binding_execution_authorized,
        readiness.callable_binding_allowed,
        readiness.reasoning_execution_allowed,
        readiness.probability_estimation_allowed,
        readiness.final_intelligence_conclusion_allowed,
        readiness.publication_allowed,
        readiness.alerting_allowed,
        readiness.qseries_handoff_allowed,
        readiness.qseries_execution_allowed,
        readiness.order_creation_allowed,
        readiness.funds_movement_allowed,
        readiness.portfolio_mutation_allowed,
    )
    if (
        readiness.engine_id != ENGINE_ID
        or readiness.schema_version != SCHEMA_VERSION
        or readiness.algorithm_version != ALGORITHM_VERSION
        or readiness.readiness_status != READINESS_STATUS
        or readiness.binding_activation_verified is not True
        or readiness.exact_activation_hash_scope_preserved is not True
        or readiness.bounded_binding_scope is not True
        or readiness.deterministic_binding_required is not True
        or readiness.immutable_binding_result_required is not True
        or readiness.callable_binding_execution_ready is not True
        or readiness.read_only is not True
        or readiness.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCallableBindingExecutionReadinessInvariantError(
            "OSR-009 permanent safety boundary violated"
        )
    return True


def serialize_callable_binding_execution_readiness(
    readiness: CallableBindingExecutionReadiness,
) -> str:
    verify_callable_binding_execution_readiness(readiness)
    return canonical_json(readiness)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "READINESS_STATUS",
    "OracleCallableBindingExecutionReadinessInvariantError",
    "CallableBindingExecutionReadiness",
    "certify_callable_binding_execution_readiness",
    "verify_callable_binding_execution_readiness",
    "serialize_callable_binding_execution_readiness",
]
