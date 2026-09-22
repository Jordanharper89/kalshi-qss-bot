from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_final_completion_and_freeze_gate import (
    COMPLETION_STATUS as OOR_013_COMPLETION_STATUS,
    OracleOperatorRuntimeFinalCompletionAndFreeze,
    verify_oracle_operator_runtime_final_completion_and_freeze,
)

SCHEMA_VERSION = "ORR-001"
ENGINE_ID = "ORR-001"
POLICY_ID = "oracle.research-response.runtime-read-only-dependency-gate.v1"
SUBSYSTEM_NAMESPACE = "oracle_research_response"
DEPENDENCY_TYPE = "oracle_operator_runtime_final_completion_read_only_dependency"
DEPENDENCY_STATUS = "oracle_operator_runtime_dependency_admitted"


class OracleResearchResponseRuntimeDependencyInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResearchResponseRuntimeDependencyInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleResearchResponseRuntimeDependencyReceipt:
    dependency_receipt_id: str
    source_runtime_completion_id: str
    source_runtime_completion_hash: str
    source_runtime_namespace: str
    source_runtime_completion_status: str
    subsystem_namespace: str
    admitted_at: datetime
    complete_runtime_lineage_verified: bool
    source_runtime_complete_verified: bool
    source_runtime_immutable_freeze_verified: bool
    source_runtime_read_only_verified: bool
    downstream_read_only_operation_verified: bool
    deterministic_boundary_verified: bool
    immutable_result_boundary_verified: bool
    dependency_single_use_verified: bool
    duplicate_dependency_allowed: bool
    dependency_reversible: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    dependency_type: str
    dependency_status: str
    dependency_receipt_hash: str


class OracleResearchResponseRuntimeDependencyGate:
    def admit(
        self,
        *,
        completion: OracleOperatorRuntimeFinalCompletionAndFreeze,
        admitted_at: datetime,
    ) -> OracleResearchResponseRuntimeDependencyReceipt:
        if not isinstance(completion, OracleOperatorRuntimeFinalCompletionAndFreeze):
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "completion must be canonical OOR-013 final completion"
            )

        try:
            verified = verify_oracle_operator_runtime_final_completion_and_freeze(completion)
        except Exception as exc:
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "OOR-013 completion verification failed"
            ) from exc
        if not verified:
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "OOR-013 completion verification failed"
            )

        required = (
            completion.complete_lineage_verified,
            completion.deterministic_completion,
            completion.immutable_freeze,
            completion.runtime_complete,
            completion.read_only,
            completion.downstream_read_only_operation_allowed,
            not completion.further_oor_certification_required,
            completion.completion_status == OOR_013_COMPLETION_STATUS,
        )
        forbidden = (
            completion.runtime_serving_allowed,
            completion.network_listener_allowed,
            completion.database_connection_allowed,
            completion.publication_allowed,
            completion.qseries_handoff_allowed,
            completion.qseries_execution_allowed,
            completion.order_creation_allowed,
            completion.funds_movement_allowed,
            completion.portfolio_mutation_allowed,
        )
        if not all(required) or any(forbidden):
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "OOR-013 permanent read-only boundary violated"
            )

        if (
            not isinstance(admitted_at, datetime)
            or admitted_at.tzinfo is None
            or admitted_at.utcoffset() is None
        ):
            raise OracleResearchResponseRuntimeDependencyInvariantError(
                "admitted_at must be timezone-aware"
            )
        at = admitted_at.astimezone(timezone.utc)

        body = {
            "source_runtime_completion_id": completion.completion_id,
            "source_runtime_completion_hash": completion.completion_hash,
            "source_runtime_namespace": completion.runtime_namespace,
            "source_runtime_completion_status": completion.completion_status,
            "subsystem_namespace": SUBSYSTEM_NAMESPACE,
            "admitted_at": at,
            "complete_runtime_lineage_verified": True,
            "source_runtime_complete_verified": True,
            "source_runtime_immutable_freeze_verified": True,
            "source_runtime_read_only_verified": True,
            "downstream_read_only_operation_verified": True,
            "deterministic_boundary_verified": True,
            "immutable_result_boundary_verified": True,
            "dependency_single_use_verified": True,
            "duplicate_dependency_allowed": False,
            "dependency_reversible": False,
            "runtime_serving_allowed": False,
            "network_listener_allowed": False,
            "database_connection_allowed": False,
            "publication_allowed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "order_creation_allowed": False,
            "funds_movement_allowed": False,
            "portfolio_mutation_allowed": False,
            "dependency_type": DEPENDENCY_TYPE,
            "dependency_status": DEPENDENCY_STATUS,
        }
        body["dependency_receipt_id"] = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_runtime_completion_id": completion.completion_id,
                "source_runtime_completion_hash": completion.completion_hash,
                "subsystem_namespace": SUBSYSTEM_NAMESPACE,
                "admitted_at": at,
                "dependency_type": DEPENDENCY_TYPE,
            }
        )
        return OracleResearchResponseRuntimeDependencyReceipt(
            **body,
            dependency_receipt_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "SUBSYSTEM_NAMESPACE",
    "DEPENDENCY_TYPE",
    "DEPENDENCY_STATUS",
    "OracleResearchResponseRuntimeDependencyInvariantError",
    "OracleResearchResponseRuntimeDependencyReceipt",
    "OracleResearchResponseRuntimeDependencyGate",
    "stable_hash",
]
