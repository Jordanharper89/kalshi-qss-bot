from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_callable_binding_execution_authorization_consumption_activation_gate import (
    verify_callable_binding_execution_authorization_activation,
)

ENGINE_ID = "OSR-012"
SCHEMA_VERSION = "OSR-012.v1"
ALGORITHM_VERSION = "deterministic-callable-binding-execution-envelope.v1"
ENVELOPE_STATUS = (
    "callable_binding_execution_envelope_materialized_not_imported_"
    "not_loaded_not_bound_not_executed"
)


class OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(ValueError):
    """Raised when an OSR-012 execution-envelope invariant fails."""


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
    raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
        "execution-activation object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            f"missing execution-activation field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class DeterministicCallableBindingExecutionEnvelope:
    envelope_id: str
    source_execution_activation_id: str
    source_execution_activation_hash: str
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
    execution_activation_verified: bool
    exact_activation_hash_scope_preserved: bool
    bounded_binding_scope_preserved: bool
    deterministic_binding_required: bool
    immutable_binding_result_required: bool
    deterministic_execution_order_required: bool
    isolated_callable_context_required: bool
    fail_closed_required: bool
    implementation_import_allowed: bool
    implementation_symbol_load_allowed: bool
    callable_binding_allowed: bool
    callable_invocation_allowed: bool
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
    envelope_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    envelope_hash: str


def materialize_callable_binding_execution_envelope(
    *,
    activation: Any,
) -> DeterministicCallableBindingExecutionEnvelope:
    try:
        verify_callable_binding_execution_authorization_activation(activation)
    except Exception as exc:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "OSR-011 execution activation verification failed"
        ) from exc

    snapshot = _snapshot(activation)

    if snapshot.get("read_only") is not True:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "OSR-011 execution activation must remain read-only"
        )
    if snapshot.get("callable_binding_execution_activation_enabled") is not True:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "callable-binding execution activation is not enabled"
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
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "OSR-011 activation violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_execution_activation_id": str(
            _required(snapshot, "activation_id")
        ),
        "source_execution_activation_hash": str(
            _required(snapshot, "activation_hash")
        ),
        "source_execution_authorization_id": str(
            _required(snapshot, "source_execution_authorization_id")
        ),
        "source_execution_authorization_hash": str(
            _required(snapshot, "source_execution_authorization_hash")
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
        "execution_activation_verified": True,
        "exact_activation_hash_scope_preserved": True,
        "bounded_binding_scope_preserved": True,
        "deterministic_binding_required": True,
        "immutable_binding_result_required": True,
        "deterministic_execution_order_required": True,
        "isolated_callable_context_required": True,
        "fail_closed_required": True,
        "implementation_import_allowed": False,
        "implementation_symbol_load_allowed": False,
        "callable_binding_allowed": False,
        "callable_invocation_allowed": False,
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
        "envelope_status": ENVELOPE_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    envelope_hash = stable_hash(body)

    return DeterministicCallableBindingExecutionEnvelope(
        envelope_id="callable-binding-execution-envelope:" + envelope_hash,
        **body,
        envelope_hash=envelope_hash,
    )


def verify_deterministic_callable_binding_execution_envelope(
    envelope: DeterministicCallableBindingExecutionEnvelope,
) -> bool:
    if not isinstance(
        envelope,
        DeterministicCallableBindingExecutionEnvelope,
    ):
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "invalid deterministic callable-binding execution envelope"
        )

    body = {
        key: value
        for key, value in asdict(envelope).items()
        if key not in {"envelope_id", "envelope_hash"}
    }
    expected_hash = stable_hash(body)

    if envelope.envelope_hash != expected_hash:
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "callable-binding execution-envelope hash mismatch"
        )
    if envelope.envelope_id != (
        "callable-binding-execution-envelope:" + expected_hash
    ):
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "callable-binding execution-envelope identity mismatch"
        )

    forbidden = (
        envelope.implementation_import_allowed,
        envelope.implementation_symbol_load_allowed,
        envelope.callable_binding_allowed,
        envelope.callable_invocation_allowed,
        envelope.reasoning_execution_allowed,
        envelope.probability_estimation_allowed,
        envelope.final_intelligence_conclusion_allowed,
        envelope.publication_allowed,
        envelope.alerting_allowed,
        envelope.qseries_handoff_allowed,
        envelope.qseries_execution_allowed,
        envelope.order_creation_allowed,
        envelope.funds_movement_allowed,
        envelope.portfolio_mutation_allowed,
    )
    if (
        envelope.engine_id != ENGINE_ID
        or envelope.schema_version != SCHEMA_VERSION
        or envelope.algorithm_version != ALGORITHM_VERSION
        or envelope.envelope_status != ENVELOPE_STATUS
        or envelope.execution_activation_verified is not True
        or envelope.exact_activation_hash_scope_preserved is not True
        or envelope.bounded_binding_scope_preserved is not True
        or envelope.deterministic_binding_required is not True
        or envelope.immutable_binding_result_required is not True
        or envelope.deterministic_execution_order_required is not True
        or envelope.isolated_callable_context_required is not True
        or envelope.fail_closed_required is not True
        or envelope.read_only is not True
        or envelope.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleDeterministicCallableBindingExecutionEnvelopeInvariantError(
            "OSR-012 permanent safety boundary violated"
        )
    return True


def serialize_deterministic_callable_binding_execution_envelope(
    envelope: DeterministicCallableBindingExecutionEnvelope,
) -> str:
    verify_deterministic_callable_binding_execution_envelope(envelope)
    return canonical_json(envelope)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "ENVELOPE_STATUS",
    "OracleDeterministicCallableBindingExecutionEnvelopeInvariantError",
    "DeterministicCallableBindingExecutionEnvelope",
    "materialize_callable_binding_execution_envelope",
    "verify_deterministic_callable_binding_execution_envelope",
    "serialize_deterministic_callable_binding_execution_envelope",
]
