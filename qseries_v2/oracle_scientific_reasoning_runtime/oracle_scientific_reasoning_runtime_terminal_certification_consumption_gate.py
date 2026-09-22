from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from qseries_v2.oracle_scientific_reasoning_runtime.oracle_scientific_reasoning_runtime_terminal_certification_and_freeze_gate import (
    verify_oracle_scientific_reasoning_runtime_terminal_certification,
)

ENGINE_ID = "INT-OSR-001"
SCHEMA_VERSION = "INT-OSR-001.v1"
ALGORITHM_VERSION = "osr-terminal-certification-consumption.v1"
CONSUMPTION_STATUS = (
    "osr_terminal_certification_consumed_for_read_only_integration"
)


class OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(ValueError):
    """Raised when an INT-OSR-001 integration invariant fails."""


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
    raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
        "OSR terminal certification cannot be snapshotted"
    )


def _required(snapshot: Mapping[str, Any], name: str) -> Any:
    if name not in snapshot:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            f"missing OSR terminal certification field: {name}"
        )
    return snapshot[name]


@dataclass(frozen=True)
class OracleScientificReasoningRuntimeTerminalConsumption:
    consumption_id: str
    source_terminal_certification_id: str
    source_terminal_certification_hash: str
    source_execution_result_id: str
    source_execution_result_hash: str
    callable_count: int
    terminal_certification_verified: bool
    subsystem_frozen_verified: bool
    no_further_osr_layers_verified: bool
    exact_terminal_hash_scope_preserved: bool
    read_only_integration_only: bool
    downstream_contract_materialization_allowed: bool
    downstream_read_only_consumption_allowed: bool
    scientific_reasoning_runtime_mutation_allowed: bool
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
    consumption_status: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    consumption_hash: str


def consume_oracle_scientific_reasoning_runtime_terminal_certification(
    *,
    certification: Any,
) -> OracleScientificReasoningRuntimeTerminalConsumption:
    try:
        verify_oracle_scientific_reasoning_runtime_terminal_certification(
            certification
        )
    except Exception as exc:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR-014 terminal certification verification failed"
        ) from exc

    snapshot = _snapshot(certification)

    if snapshot.get("subsystem_frozen") is not True:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR subsystem is not frozen"
        )
    if snapshot.get("further_certification_layers_required") is not False:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR terminal record still requires certification layers"
        )
    if snapshot.get("read_only") is not True:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR terminal certification must remain read-only"
        )

    forbidden_performed = (
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
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR terminal certification records forbidden activity"
        )

    callable_count = int(_required(snapshot, "callable_count"))
    if callable_count <= 0:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "callable count must be positive"
        )

    body = {
        "source_terminal_certification_id": str(
            _required(snapshot, "terminal_certification_id")
        ),
        "source_terminal_certification_hash": str(
            _required(snapshot, "terminal_certification_hash")
        ),
        "source_execution_result_id": str(
            _required(snapshot, "source_execution_result_id")
        ),
        "source_execution_result_hash": str(
            _required(snapshot, "source_execution_result_hash")
        ),
        "callable_count": callable_count,
        "terminal_certification_verified": True,
        "subsystem_frozen_verified": True,
        "no_further_osr_layers_verified": True,
        "exact_terminal_hash_scope_preserved": True,
        "read_only_integration_only": True,
        "downstream_contract_materialization_allowed": True,
        "downstream_read_only_consumption_allowed": True,
        "scientific_reasoning_runtime_mutation_allowed": False,
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
        "consumption_status": CONSUMPTION_STATUS,
        "engine_id": ENGINE_ID,
        "schema_version": SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
    }
    consumption_hash = stable_hash(body)

    return OracleScientificReasoningRuntimeTerminalConsumption(
        consumption_id="osr-terminal-consumption:" + consumption_hash,
        **body,
        consumption_hash=consumption_hash,
    )


def verify_oracle_scientific_reasoning_runtime_terminal_consumption(
    consumption: OracleScientificReasoningRuntimeTerminalConsumption,
) -> bool:
    if not isinstance(
        consumption,
        OracleScientificReasoningRuntimeTerminalConsumption,
    ):
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "invalid OSR terminal consumption record"
        )

    body = {
        key: value
        for key, value in asdict(consumption).items()
        if key not in {"consumption_id", "consumption_hash"}
    }
    expected_hash = stable_hash(body)

    if consumption.consumption_hash != expected_hash:
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR terminal consumption hash mismatch"
        )
    if consumption.consumption_id != (
        "osr-terminal-consumption:" + expected_hash
    ):
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "OSR terminal consumption identity mismatch"
        )

    forbidden = (
        consumption.scientific_reasoning_runtime_mutation_allowed,
        consumption.implementation_import_allowed,
        consumption.implementation_symbol_load_allowed,
        consumption.callable_binding_allowed,
        consumption.callable_invocation_allowed,
        consumption.reasoning_execution_allowed,
        consumption.probability_estimation_allowed,
        consumption.final_intelligence_conclusion_allowed,
        consumption.publication_allowed,
        consumption.alerting_allowed,
        consumption.qseries_handoff_allowed,
        consumption.qseries_execution_allowed,
        consumption.order_creation_allowed,
        consumption.funds_movement_allowed,
        consumption.portfolio_mutation_allowed,
    )
    if (
        consumption.engine_id != ENGINE_ID
        or consumption.schema_version != SCHEMA_VERSION
        or consumption.algorithm_version != ALGORITHM_VERSION
        or consumption.consumption_status != CONSUMPTION_STATUS
        or consumption.terminal_certification_verified is not True
        or consumption.subsystem_frozen_verified is not True
        or consumption.no_further_osr_layers_verified is not True
        or consumption.exact_terminal_hash_scope_preserved is not True
        or consumption.read_only_integration_only is not True
        or consumption.downstream_contract_materialization_allowed is not True
        or consumption.downstream_read_only_consumption_allowed is not True
        or consumption.read_only is not True
        or consumption.callable_count <= 0
        or any(forbidden)
    ):
        raise OracleScientificReasoningRuntimeTerminalConsumptionInvariantError(
            "INT-OSR-001 permanent safety boundary violated"
        )
    return True


def serialize_oracle_scientific_reasoning_runtime_terminal_consumption(
    consumption: OracleScientificReasoningRuntimeTerminalConsumption,
) -> str:
    verify_oracle_scientific_reasoning_runtime_terminal_consumption(consumption)
    return canonical_json(consumption)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "CONSUMPTION_STATUS",
    "OracleScientificReasoningRuntimeTerminalConsumptionInvariantError",
    "OracleScientificReasoningRuntimeTerminalConsumption",
    "consume_oracle_scientific_reasoning_runtime_terminal_certification",
    "verify_oracle_scientific_reasoning_runtime_terminal_consumption",
    "serialize_oracle_scientific_reasoning_runtime_terminal_consumption",
]
