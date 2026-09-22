from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_deterministic_callable_binding_execution_result_record_gate import (
    verify_deterministic_callable_binding_execution_result_record,
)

ENGINE_ID = "OSR-014"
SCHEMA_VERSION = "OSR-014.v1"
ALGORITHM_VERSION = "oracle-scientific-reasoning-runtime-terminal-freeze.v1"
TERMINAL_STATUS = (
    "oracle_scientific_reasoning_runtime_terminally_certified_and_frozen"
)


class OracleScientificReasoningRuntimeTerminalFreezeInvariantError(ValueError):
    """Raised when an OSR-014 terminal certification invariant fails."""


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
    raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
        "OSR-013 execution-result object cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            f"missing OSR-013 execution-result field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class OracleScientificReasoningRuntimeTerminalCertification:
    terminal_certification_id: str
    source_execution_result_id: str
    source_execution_result_hash: str
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
    execution_result_verified: bool
    exact_result_hash_scope_preserved: bool
    complete_osr_lineage_preserved: bool
    deterministic_replay_required: bool
    immutable_terminal_record: bool
    subsystem_frozen: bool
    further_certification_layers_required: bool
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
    terminal_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    terminal_certification_hash: str


def certify_and_freeze_oracle_scientific_reasoning_runtime(
    *,
    result: Any,
) -> OracleScientificReasoningRuntimeTerminalCertification:
    try:
        verify_deterministic_callable_binding_execution_result_record(result)
    except Exception as exc:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-013 deterministic execution-result verification failed"
        ) from exc

    snapshot = _snapshot(result)

    if snapshot.get("read_only") is not True:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-013 execution result must remain read-only"
        )
    if snapshot.get("envelope_verified") is not True:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-013 execution envelope is not verified"
        )
    if snapshot.get("exact_envelope_hash_scope_preserved") is not True:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-013 exact envelope hash scope was not preserved"
        )

    forbidden_performed = (
        bool(snapshot.get("execution_attempted", False)),
        bool(snapshot.get("implementation_import_performed", False)),
        bool(snapshot.get("implementation_symbol_load_performed", False)),
        bool(snapshot.get("callable_binding_performed", False)),
        bool(snapshot.get("callable_invocation_performed", False)),
        bool(snapshot.get("reasoning_execution_performed", False)),
        bool(snapshot.get("probability_estimation_performed", False)),
        bool(snapshot.get("final_intelligence_conclusion_produced", False)),
        bool(snapshot.get("publication_performed", False)),
        bool(snapshot.get("alerting_performed", False)),
        bool(snapshot.get("qseries_handoff_performed", False)),
        bool(snapshot.get("qseries_execution_performed", False)),
        bool(snapshot.get("order_creation_performed", False)),
        bool(snapshot.get("funds_movement_performed", False)),
        bool(snapshot.get("portfolio_mutation_performed", False)),
    )
    if any(forbidden_performed):
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-013 result records forbidden execution or mutation"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_execution_result_id": str(_required(snapshot, "result_id")),
        "source_execution_result_hash": str(_required(snapshot, "result_hash")),
        "source_execution_envelope_id": str(
            _required(snapshot, "source_execution_envelope_id")
        ),
        "source_execution_envelope_hash": str(
            _required(snapshot, "source_execution_envelope_hash")
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
        "execution_result_verified": True,
        "exact_result_hash_scope_preserved": True,
        "complete_osr_lineage_preserved": True,
        "deterministic_replay_required": True,
        "immutable_terminal_record": True,
        "subsystem_frozen": True,
        "further_certification_layers_required": False,
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
        "terminal_status": TERMINAL_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    terminal_hash = stable_hash(body)

    return OracleScientificReasoningRuntimeTerminalCertification(
        terminal_certification_id=(
            "oracle-scientific-reasoning-runtime-terminal:" + terminal_hash
        ),
        **body,
        terminal_certification_hash=terminal_hash,
    )


def verify_oracle_scientific_reasoning_runtime_terminal_certification(
    certification: OracleScientificReasoningRuntimeTerminalCertification,
) -> bool:
    if not isinstance(
        certification,
        OracleScientificReasoningRuntimeTerminalCertification,
    ):
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "invalid OSR terminal certification"
        )

    body = {
        key: value
        for key, value in asdict(certification).items()
        if key not in {
            "terminal_certification_id",
            "terminal_certification_hash",
        }
    }
    expected_hash = stable_hash(body)

    if certification.terminal_certification_hash != expected_hash:
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR terminal certification hash mismatch"
        )
    if certification.terminal_certification_id != (
        "oracle-scientific-reasoning-runtime-terminal:" + expected_hash
    ):
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR terminal certification identity mismatch"
        )

    forbidden_performed = (
        certification.implementation_import_performed,
        certification.implementation_symbol_load_performed,
        certification.callable_binding_performed,
        certification.callable_invocation_performed,
        certification.reasoning_execution_performed,
        certification.probability_estimation_performed,
        certification.final_intelligence_conclusion_produced,
        certification.publication_performed,
        certification.alerting_performed,
        certification.qseries_handoff_performed,
        certification.qseries_execution_performed,
        certification.order_creation_performed,
        certification.funds_movement_performed,
        certification.portfolio_mutation_performed,
    )
    if (
        certification.engine_id != ENGINE_ID
        or certification.schema_version != SCHEMA_VERSION
        or certification.algorithm_version != ALGORITHM_VERSION
        or certification.terminal_status != TERMINAL_STATUS
        or certification.execution_result_verified is not True
        or certification.exact_result_hash_scope_preserved is not True
        or certification.complete_osr_lineage_preserved is not True
        or certification.deterministic_replay_required is not True
        or certification.immutable_terminal_record is not True
        or certification.subsystem_frozen is not True
        or certification.further_certification_layers_required is not False
        or certification.read_only is not True
        or certification.callable_count <= 0
        or any(forbidden_performed)
    ):
        raise OracleScientificReasoningRuntimeTerminalFreezeInvariantError(
            "OSR-014 terminal safety boundary violated"
        )
    return True


def serialize_oracle_scientific_reasoning_runtime_terminal_certification(
    certification: OracleScientificReasoningRuntimeTerminalCertification,
) -> str:
    verify_oracle_scientific_reasoning_runtime_terminal_certification(
        certification
    )
    return canonical_json(certification)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "TERMINAL_STATUS",
    "OracleScientificReasoningRuntimeTerminalFreezeInvariantError",
    "OracleScientificReasoningRuntimeTerminalCertification",
    "certify_and_freeze_oracle_scientific_reasoning_runtime",
    "verify_oracle_scientific_reasoning_runtime_terminal_certification",
    "serialize_oracle_scientific_reasoning_runtime_terminal_certification",
]
