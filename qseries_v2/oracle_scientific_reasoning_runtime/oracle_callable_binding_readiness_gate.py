from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_resolution_authorization_consumption_activation_gate import (
    verify_callable_resolution_activation,
)

ENGINE_ID = "OSR-006"
SCHEMA_VERSION = "OSR-006.v1"
ALGORITHM_VERSION = "callable-binding-readiness.v1"
READINESS_STATUS = "callable_binding_readiness_certified_not_bound"


class OracleCallableBindingReadinessInvariantError(ValueError):
    """Raised when an OSR-006 callable-binding readiness invariant fails."""


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
    raise OracleCallableBindingReadinessInvariantError(
        "activation object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in snapshot:
            return snapshot[name]
    raise OracleCallableBindingReadinessInvariantError(
        "missing activation field: " + " or ".join(names)
    )


@dataclass(frozen=True)
class CallableBindingReadinessRecord:
    readiness_id: str
    source_activation_id: str
    source_activation_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    callable_count: int
    resolution_activation_verified: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_ready: bool
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


def certify_callable_binding_readiness(
    *,
    activation: Any,
) -> CallableBindingReadinessRecord:
    try:
        verify_callable_resolution_activation(activation)
    except Exception as exc:
        raise OracleCallableBindingReadinessInvariantError(
            "OSR-005 callable resolution activation verification failed"
        ) from exc

    snapshot = _snapshot(activation)

    source_activation_id = str(
        _required(snapshot, "activation_id")
    )
    source_activation_hash = str(
        _required(snapshot, "activation_hash")
    )
    source_authorization_id = str(
        _required(snapshot, "source_authorization_id")
    )
    source_authorization_hash = str(
        _required(snapshot, "source_authorization_hash")
    )
    source_resolution_package_id = str(
        _required(snapshot, "source_resolution_package_id")
    )
    source_resolution_hash = str(
        _required(snapshot, "source_resolution_hash")
    )
    source_admission_package_id = str(
        _required(snapshot, "source_admission_package_id")
    )
    source_admission_hash = str(
        _required(snapshot, "source_admission_hash")
    )
    callable_count = int(
        _required(snapshot, "activated_callable_count")
    )

    if callable_count <= 0:
        raise OracleCallableBindingReadinessInvariantError(
            "activated callable count must be positive"
        )
    if snapshot.get("read_only") is not True:
        raise OracleCallableBindingReadinessInvariantError(
            "OSR-005 activation must remain read-only"
        )
    if snapshot.get("callable_resolution_allowed") is not True:
        raise OracleCallableBindingReadinessInvariantError(
            "callable resolution activation is not certified"
        )

    forbidden_source_flags = (
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
        raise OracleCallableBindingReadinessInvariantError(
            "OSR-005 activation violates permanent safety boundaries"
        )

    body = {
        "source_activation_id": source_activation_id,
        "source_activation_hash": source_activation_hash,
        "source_authorization_id": source_authorization_id,
        "source_authorization_hash": source_authorization_hash,
        "source_resolution_package_id": source_resolution_package_id,
        "source_resolution_hash": source_resolution_hash,
        "source_admission_package_id": source_admission_package_id,
        "source_admission_hash": source_admission_hash,
        "callable_count": callable_count,
        "resolution_activation_verified": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_ready": True,
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

    return CallableBindingReadinessRecord(
        readiness_id="callable-binding-readiness:" + readiness_hash,
        **body,
        readiness_hash=readiness_hash,
    )


def verify_callable_binding_readiness(
    readiness: CallableBindingReadinessRecord,
) -> bool:
    if not isinstance(readiness, CallableBindingReadinessRecord):
        raise OracleCallableBindingReadinessInvariantError(
            "invalid callable-binding readiness record"
        )

    body = {
        key: value
        for key, value in asdict(readiness).items()
        if key not in {"readiness_id", "readiness_hash"}
    }
    expected_hash = stable_hash(body)
    if readiness.readiness_hash != expected_hash:
        raise OracleCallableBindingReadinessInvariantError(
            "callable-binding readiness hash mismatch"
        )
    if readiness.readiness_id != "callable-binding-readiness:" + expected_hash:
        raise OracleCallableBindingReadinessInvariantError(
            "callable-binding readiness identity mismatch"
        )

    forbidden = (
        readiness.implementation_import_allowed,
        readiness.implementation_symbol_load_allowed,
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
        or readiness.resolution_activation_verified is not True
        or readiness.callable_binding_ready is not True
        or readiness.read_only is not True
        or readiness.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleCallableBindingReadinessInvariantError(
            "OSR-006 permanent safety boundary violated"
        )
    return True


def serialize_callable_binding_readiness(
    readiness: CallableBindingReadinessRecord,
) -> str:
    verify_callable_binding_readiness(readiness)
    return canonical_json(readiness)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "READINESS_STATUS",
    "OracleCallableBindingReadinessInvariantError",
    "CallableBindingReadinessRecord",
    "certify_callable_binding_readiness",
    "verify_callable_binding_readiness",
    "serialize_callable_binding_readiness",
]
