from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_deterministic_callable_binding_execution_envelope_gate import (
    verify_deterministic_callable_binding_execution_envelope,
)

ENGINE_ID = "OSR-013"
SCHEMA_VERSION = "OSR-013.v1"
ALGORITHM_VERSION = "deterministic-callable-binding-execution-result-record.v1"
RESULT_STATUS = (
    "execution_result_record_materialized_no_import_no_load_no_bind_no_invoke"
)


class OracleDeterministicCallableBindingExecutionResultInvariantError(ValueError):
    """Raised when an OSR-013 execution-result invariant fails."""


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
    raise OracleDeterministicCallableBindingExecutionResultInvariantError(
        "execution-envelope object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            f"missing execution-envelope field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class DeterministicCallableBindingExecutionResultRecord:
    result_id: str
    source_execution_envelope_id: str
    source_execution_envelope_hash: str
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
    envelope_verified: bool
    exact_envelope_hash_scope_preserved: bool
    deterministic_execution_order_required: bool
    isolated_callable_context_required: bool
    fail_closed_required: bool
    execution_attempted: bool
    implementation_import_performed: bool
    implementation_symbol_load_performed: bool
    callable_binding_performed: bool
    callable_invocation_performed: bool
    reasoning_execution_performed: bool
    probability_estimation_performed: bool
    final_intelligence_conclusion_produced: bool
    publication_performed: bool
    alerting_performed: bool
    qseries_handoff_performed: bool
    qseries_execution_performed: bool
    order_creation_performed: bool
    funds_movement_performed: bool
    portfolio_mutation_performed: bool
    read_only: bool
    result_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    result_hash: str


def materialize_deterministic_callable_binding_execution_result_record(
    *,
    envelope: Any,
) -> DeterministicCallableBindingExecutionResultRecord:
    try:
        verify_deterministic_callable_binding_execution_envelope(envelope)
    except Exception as exc:
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "OSR-012 deterministic execution-envelope verification failed"
        ) from exc

    snapshot = _snapshot(envelope)

    if snapshot.get("read_only") is not True:
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "OSR-012 execution envelope must remain read-only"
        )

    forbidden_source_flags = (
        bool(snapshot.get("implementation_import_allowed", False)),
        bool(snapshot.get("implementation_symbol_load_allowed", False)),
        bool(snapshot.get("callable_binding_allowed", False)),
        bool(snapshot.get("callable_invocation_allowed", False)),
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
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "OSR-012 envelope violates permanent safety boundaries"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_execution_envelope_id": str(_required(snapshot, "envelope_id")),
        "source_execution_envelope_hash": str(
            _required(snapshot, "envelope_hash")
        ),
        "source_execution_activation_id": str(
            _required(snapshot, "source_execution_activation_id")
        ),
        "source_execution_activation_hash": str(
            _required(snapshot, "source_execution_activation_hash")
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
        "envelope_verified": True,
        "exact_envelope_hash_scope_preserved": True,
        "deterministic_execution_order_required": True,
        "isolated_callable_context_required": True,
        "fail_closed_required": True,
        "execution_attempted": False,
        "implementation_import_performed": False,
        "implementation_symbol_load_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "reasoning_execution_performed": False,
        "probability_estimation_performed": False,
        "final_intelligence_conclusion_produced": False,
        "publication_performed": False,
        "alerting_performed": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "read_only": True,
        "result_status": RESULT_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    result_hash = stable_hash(body)

    return DeterministicCallableBindingExecutionResultRecord(
        result_id="callable-binding-execution-result:" + result_hash,
        **body,
        result_hash=result_hash,
    )


def verify_deterministic_callable_binding_execution_result_record(
    result: DeterministicCallableBindingExecutionResultRecord,
) -> bool:
    if not isinstance(
        result,
        DeterministicCallableBindingExecutionResultRecord,
    ):
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "invalid deterministic callable-binding execution result"
        )

    body = {
        key: value
        for key, value in asdict(result).items()
        if key not in {"result_id", "result_hash"}
    }
    expected_hash = stable_hash(body)

    if result.result_hash != expected_hash:
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "callable-binding execution-result hash mismatch"
        )
    if result.result_id != (
        "callable-binding-execution-result:" + expected_hash
    ):
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "callable-binding execution-result identity mismatch"
        )

    forbidden_performed = (
        result.execution_attempted,
        result.implementation_import_performed,
        result.implementation_symbol_load_performed,
        result.callable_binding_performed,
        result.callable_invocation_performed,
        result.reasoning_execution_performed,
        result.probability_estimation_performed,
        result.final_intelligence_conclusion_produced,
        result.publication_performed,
        result.alerting_performed,
        result.qseries_handoff_performed,
        result.qseries_execution_performed,
        result.order_creation_performed,
        result.funds_movement_performed,
        result.portfolio_mutation_performed,
    )
    if (
        result.engine_id != ENGINE_ID
        or result.schema_version != SCHEMA_VERSION
        or result.algorithm_version != ALGORITHM_VERSION
        or result.result_status != RESULT_STATUS
        or result.envelope_verified is not True
        or result.exact_envelope_hash_scope_preserved is not True
        or result.deterministic_execution_order_required is not True
        or result.isolated_callable_context_required is not True
        or result.fail_closed_required is not True
        or result.read_only is not True
        or result.callable_count <= 0
        or any(forbidden_performed)
    ):
        raise OracleDeterministicCallableBindingExecutionResultInvariantError(
            "OSR-013 permanent safety boundary violated"
        )
    return True


def serialize_deterministic_callable_binding_execution_result_record(
    result: DeterministicCallableBindingExecutionResultRecord,
) -> str:
    verify_deterministic_callable_binding_execution_result_record(result)
    return canonical_json(result)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "RESULT_STATUS",
    "OracleDeterministicCallableBindingExecutionResultInvariantError",
    "DeterministicCallableBindingExecutionResultRecord",
    "materialize_deterministic_callable_binding_execution_result_record",
    "verify_deterministic_callable_binding_execution_result_record",
    "serialize_deterministic_callable_binding_execution_result_record",
]
