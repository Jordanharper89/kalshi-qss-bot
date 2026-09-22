from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_certified_callable_resolution_authorization_gate import (
    verify_certified_callable_resolution_authorization,
)

ENGINE_ID = "OSR-005"
SCHEMA_VERSION = "OSR-005.v1"
ALGORITHM_VERSION = "resolution-authorization-consumption-activation.v1"

ACTIVATION_STATUS = (
    "resolution_authorization_consumed_activation_materialized"
)


class OracleResolutionAuthorizationConsumptionInvariantError(ValueError):
    """Raised when an OSR-005 activation invariant is violated."""


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
    raise OracleResolutionAuthorizationConsumptionInvariantError(
        "authorization object cannot be snapshotted"
    )


def _required(
    snapshot: Mapping[str, Any],
    *names: str,
) -> Any:
    for name in names:
        if name in snapshot:
            return snapshot[name]
    raise OracleResolutionAuthorizationConsumptionInvariantError(
        "missing authorization field: " + " or ".join(names)
    )


@dataclass(frozen=True)
class CallableResolutionAuthorizationConsumptionReceipt:
    receipt_id: str
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    authorized_callable_count: int
    authorization_consumed: bool
    single_use_consumption: bool
    receipt_status: str
    receipt_hash: str


@dataclass(frozen=True)
class CallableResolutionActivation:
    activation_id: str
    authorization_consumption_receipt: CallableResolutionAuthorizationConsumptionReceipt
    source_authorization_id: str
    source_authorization_hash: str
    source_resolution_package_id: str
    source_resolution_hash: str
    source_admission_package_id: str
    source_admission_hash: str
    activated_callable_count: int
    activation_status: str
    activation_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
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


def consume_resolution_authorization_and_activate(
    *,
    authorization: Any,
) -> CallableResolutionActivation:
    try:
        verify_certified_callable_resolution_authorization(authorization)
    except Exception as exc:
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "OSR-004 resolution authorization verification failed"
        ) from exc

    snapshot = _snapshot(authorization)

    authorization_id = str(
        _required(
            snapshot,
            "authorization_id",
            "resolution_authorization_id",
        )
    )
    authorization_hash = str(
        _required(
            snapshot,
            "authorization_hash",
            "resolution_authorization_hash",
        )
    )
    resolution_package_id = str(
        _required(
            snapshot,
            "source_resolution_package_id",
            "resolution_package_id",
        )
    )
    resolution_hash = str(
        _required(
            snapshot,
            "source_resolution_hash",
            "resolution_hash",
        )
    )
    admission_package_id = str(
        _required(
            snapshot,
            "source_admission_package_id",
            "admission_package_id",
        )
    )
    admission_hash = str(
        _required(
            snapshot,
            "source_admission_hash",
            "admission_hash",
        )
    )
    authorized_callable_count = int(
        _required(
            snapshot,
            "authorized_callable_count",
            "resolved_callable_count",
            "callable_count",
        )
    )

    if authorized_callable_count <= 0:
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "authorized callable count must be positive"
        )

    authorization_allowed = snapshot.get(
        "callable_resolution_authorized",
        snapshot.get("resolution_authorized", True),
    )
    if authorization_allowed is not True:
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "OSR-004 authorization is not active"
        )

    forbidden_source_flags = (
        bool(snapshot.get("callable_binding_allowed", False)),
        bool(snapshot.get("reasoning_execution_allowed", False)),
        bool(snapshot.get("qseries_execution_allowed", False)),
        bool(snapshot.get("order_creation_allowed", False)),
        bool(snapshot.get("funds_movement_allowed", False)),
        bool(snapshot.get("portfolio_mutation_allowed", False)),
    )
    if any(forbidden_source_flags):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "OSR-004 authorization violates permanent safety boundaries"
        )

    receipt_body = {
        "source_authorization_id": authorization_id,
        "source_authorization_hash": authorization_hash,
        "source_resolution_package_id": resolution_package_id,
        "source_resolution_hash": resolution_hash,
        "source_admission_package_id": admission_package_id,
        "source_admission_hash": admission_hash,
        "authorized_callable_count": authorized_callable_count,
        "authorization_consumed": True,
        "single_use_consumption": True,
        "receipt_status":
            "resolution_authorization_consumed_once_read_only",
    }
    receipt_hash = stable_hash(receipt_body)
    receipt = CallableResolutionAuthorizationConsumptionReceipt(
        receipt_id=(
            "callable-resolution-authorization-consumption:" + receipt_hash
        ),
        **receipt_body,
        receipt_hash=receipt_hash,
    )

    activation_body = {
        "authorization_consumption_receipt": receipt,
        "source_authorization_id": authorization_id,
        "source_authorization_hash": authorization_hash,
        "source_resolution_package_id": resolution_package_id,
        "source_resolution_hash": resolution_hash,
        "source_admission_package_id": admission_package_id,
        "source_admission_hash": admission_hash,
        "activated_callable_count": authorized_callable_count,
        "activation_status": ACTIVATION_STATUS,
    }
    activation_hash = stable_hash(activation_body)

    return CallableResolutionActivation(
        activation_id="callable-resolution-activation:" + activation_hash,
        **activation_body,
        activation_hash=activation_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        callable_resolution_allowed=True,
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


def verify_resolution_authorization_consumption_receipt(
    receipt: CallableResolutionAuthorizationConsumptionReceipt,
) -> bool:
    if not isinstance(
        receipt,
        CallableResolutionAuthorizationConsumptionReceipt,
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "invalid authorization consumption receipt"
        )

    body = {
        key: value
        for key, value in asdict(receipt).items()
        if key not in {"receipt_id", "receipt_hash"}
    }
    expected_hash = stable_hash(body)
    if receipt.receipt_hash != expected_hash:
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "authorization consumption receipt hash mismatch"
        )
    if receipt.receipt_id != (
        "callable-resolution-authorization-consumption:" + expected_hash
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "authorization consumption receipt identity mismatch"
        )
    if (
        receipt.authorization_consumed is not True
        or receipt.single_use_consumption is not True
        or receipt.authorized_callable_count <= 0
        or receipt.receipt_status
        != "resolution_authorization_consumed_once_read_only"
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "authorization consumption receipt boundary violated"
        )
    return True


def verify_callable_resolution_activation(
    activation: CallableResolutionActivation,
) -> bool:
    if not isinstance(activation, CallableResolutionActivation):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "invalid callable resolution activation"
        )

    verify_resolution_authorization_consumption_receipt(
        activation.authorization_consumption_receipt
    )

    body = {
        "authorization_consumption_receipt":
            activation.authorization_consumption_receipt,
        "source_authorization_id": activation.source_authorization_id,
        "source_authorization_hash": activation.source_authorization_hash,
        "source_resolution_package_id":
            activation.source_resolution_package_id,
        "source_resolution_hash": activation.source_resolution_hash,
        "source_admission_package_id":
            activation.source_admission_package_id,
        "source_admission_hash": activation.source_admission_hash,
        "activated_callable_count": activation.activated_callable_count,
        "activation_status": activation.activation_status,
    }
    expected_hash = stable_hash(body)
    if activation.activation_hash != expected_hash:
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "activation hash mismatch"
        )
    if activation.activation_id != (
        "callable-resolution-activation:" + expected_hash
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "activation identity mismatch"
        )

    receipt = activation.authorization_consumption_receipt
    if (
        activation.source_authorization_id
        != receipt.source_authorization_id
        or activation.source_authorization_hash
        != receipt.source_authorization_hash
        or activation.source_resolution_package_id
        != receipt.source_resolution_package_id
        or activation.source_resolution_hash
        != receipt.source_resolution_hash
        or activation.source_admission_package_id
        != receipt.source_admission_package_id
        or activation.source_admission_hash
        != receipt.source_admission_hash
        or activation.activated_callable_count
        != receipt.authorized_callable_count
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "activation lineage mismatch"
        )

    forbidden = (
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
        or activation.read_only is not True
        or activation.callable_resolution_allowed is not True
        or activation.activation_status != ACTIVATION_STATUS
        or any(forbidden)
    ):
        raise OracleResolutionAuthorizationConsumptionInvariantError(
            "OSR-005 permanent safety boundary violated"
        )
    return True


def serialize_callable_resolution_activation(
    activation: CallableResolutionActivation,
) -> str:
    verify_callable_resolution_activation(activation)
    return canonical_json(activation)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ACTIVATION_STATUS",
    "OracleResolutionAuthorizationConsumptionInvariantError",
    "CallableResolutionAuthorizationConsumptionReceipt",
    "CallableResolutionActivation",
    "consume_resolution_authorization_and_activate",
    "verify_resolution_authorization_consumption_receipt",
    "verify_callable_resolution_activation",
    "serialize_callable_resolution_activation",
]
