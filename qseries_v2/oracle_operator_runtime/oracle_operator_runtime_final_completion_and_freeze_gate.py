from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator_runtime.oracle_operator_runtime_session_activation_continuation_attestation_gate import (
    ATTESTATION_STATUS as OOR_012_ATTESTATION_STATUS,
    ATTESTATION_TYPE as OOR_012_ATTESTATION_TYPE,
    OracleOperatorRuntimeSessionActivationContinuationAttestation,
)

SCHEMA_VERSION = "OOR-013"
ENGINE_ID = "OOR-013"
POLICY_ID = "oracle.operator-runtime-final-completion-and-freeze-gate.v1"
COMPLETION_STATUS = "oracle_operator_runtime_complete_and_frozen"


class OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(ValueError):
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
            raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
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


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleOperatorRuntimeFinalCompletionAndFreeze:
    completion_id: str
    source_attestation_id: str
    source_attestation_hash: str
    source_continuation_id: str
    source_continuation_hash: str
    source_session_id: str
    source_session_hash: str
    source_request_id: str
    source_request_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_operator_completion_certification_id: str
    runtime_namespace: str
    complete_lineage_verified: bool
    deterministic_completion: bool
    immutable_freeze: bool
    runtime_complete: bool
    read_only: bool
    downstream_read_only_operation_allowed: bool
    further_oor_certification_required: bool
    runtime_serving_allowed: bool
    network_listener_allowed: bool
    database_connection_allowed: bool
    publication_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    completion_status: str
    completion_hash: str


def _verify_source_attestation(
    attestation: OracleOperatorRuntimeSessionActivationContinuationAttestation,
) -> None:
    if not isinstance(attestation, OracleOperatorRuntimeSessionActivationContinuationAttestation):
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "attestation must be canonical OOR-012 continuation attestation"
        )

    body = asdict(attestation)
    supplied_hash = body.pop("attestation_hash", None)
    if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "OOR-012 attestation hash mismatch"
        )

    lineage = (
        attestation.attestation_id,
        attestation.continuation_id,
        attestation.continuation_hash,
        attestation.session_id,
        attestation.session_hash,
        attestation.request_id,
        attestation.request_hash,
        attestation.dependency_receipt_id,
        attestation.dependency_receipt_hash,
        attestation.source_operator_completion_certification_id,
    )
    if not all(_valid_sha256(value) for value in lineage):
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "OOR-012 lineage identity invalid"
        )

    required = (
        attestation.continuation_identity_verified,
        attestation.continuation_hash_verified,
        attestation.continuation_contract_verified,
        attestation.complete_runtime_lineage_verified,
        attestation.single_continuation_scope_verified,
        attestation.single_attestation_scope_verified,
        attestation.attestation_single_use_verified,
        attestation.read_only_boundary_verified,
        attestation.deterministic_boundary_verified,
        attestation.immutable_result_boundary_verified,
        attestation.attestation_type == OOR_012_ATTESTATION_TYPE,
        attestation.attestation_status == OOR_012_ATTESTATION_STATUS,
        not attestation.duplicate_attestation_allowed,
        not attestation.attestation_reversible,
    )
    forbidden = (
        attestation.runtime_serving_allowed,
        attestation.network_listener_allowed,
        attestation.database_connection_allowed,
        attestation.publication_allowed,
        attestation.qseries_handoff_allowed,
        attestation.qseries_execution_allowed,
        attestation.order_creation_allowed,
        attestation.funds_movement_allowed,
        attestation.portfolio_mutation_allowed,
    )
    if not all(required) or any(forbidden):
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "OOR-012 permanent read-only boundary violated"
        )


def complete_and_freeze_oracle_operator_runtime(
    *,
    attestation: OracleOperatorRuntimeSessionActivationContinuationAttestation,
) -> OracleOperatorRuntimeFinalCompletionAndFreeze:
    _verify_source_attestation(attestation)

    body = {
        "source_attestation_id": attestation.attestation_id,
        "source_attestation_hash": attestation.attestation_hash,
        "source_continuation_id": attestation.continuation_id,
        "source_continuation_hash": attestation.continuation_hash,
        "source_session_id": attestation.session_id,
        "source_session_hash": attestation.session_hash,
        "source_request_id": attestation.request_id,
        "source_request_hash": attestation.request_hash,
        "source_dependency_receipt_id": attestation.dependency_receipt_id,
        "source_dependency_receipt_hash": attestation.dependency_receipt_hash,
        "source_operator_completion_certification_id": attestation.source_operator_completion_certification_id,
        "runtime_namespace": attestation.runtime_namespace,
        "complete_lineage_verified": True,
        "deterministic_completion": True,
        "immutable_freeze": True,
        "runtime_complete": True,
        "read_only": True,
        "downstream_read_only_operation_allowed": True,
        "further_oor_certification_required": False,
        "runtime_serving_allowed": False,
        "network_listener_allowed": False,
        "database_connection_allowed": False,
        "publication_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "completion_status": COMPLETION_STATUS,
    }
    body["completion_id"] = stable_hash(
        {
            "engine_id": ENGINE_ID,
            "source_attestation_id": attestation.attestation_id,
            "source_attestation_hash": attestation.attestation_hash,
            "completion_status": COMPLETION_STATUS,
        }
    )
    return OracleOperatorRuntimeFinalCompletionAndFreeze(
        **body,
        completion_hash=stable_hash(body),
    )


def verify_oracle_operator_runtime_final_completion_and_freeze(
    value: OracleOperatorRuntimeFinalCompletionAndFreeze,
) -> bool:
    if not isinstance(value, OracleOperatorRuntimeFinalCompletionAndFreeze):
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "value must be canonical OOR-013 completion"
        )
    body = asdict(value)
    supplied_hash = body.pop("completion_hash", None)
    if not _valid_sha256(supplied_hash) or stable_hash(body) != supplied_hash:
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "OOR-013 completion hash mismatch"
        )
    required = (
        value.complete_lineage_verified,
        value.deterministic_completion,
        value.immutable_freeze,
        value.runtime_complete,
        value.read_only,
        value.downstream_read_only_operation_allowed,
        not value.further_oor_certification_required,
    )
    forbidden = (
        value.runtime_serving_allowed,
        value.network_listener_allowed,
        value.database_connection_allowed,
        value.publication_allowed,
        value.qseries_handoff_allowed,
        value.qseries_execution_allowed,
        value.order_creation_allowed,
        value.funds_movement_allowed,
        value.portfolio_mutation_allowed,
    )
    if not all(required) or any(forbidden) or value.completion_status != COMPLETION_STATUS:
        raise OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError(
            "OOR-013 permanent completion boundary violated"
        )
    return True


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "COMPLETION_STATUS",
    "OracleOperatorRuntimeFinalCompletionAndFreezeInvariantError",
    "OracleOperatorRuntimeFinalCompletionAndFreeze",
    "complete_and_freeze_oracle_operator_runtime",
    "verify_oracle_operator_runtime_final_completion_and_freeze",
    "stable_hash",
]
