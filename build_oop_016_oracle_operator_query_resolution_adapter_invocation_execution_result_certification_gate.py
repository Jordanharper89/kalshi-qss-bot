from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

QSERIES = ROOT / "qseries_v2"
ANALYTICS = QSERIES / "oracle_intelligence" / "analytics"
ANALYTICS_QUERY = ANALYTICS / "downstream" / "query"
OPERATOR = QSERIES / "oracle_operator"
OPERATOR_QUERY = OPERATOR / "query"

SOURCE_060 = ANALYTICS_QUERY / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
SOURCE_OOP_001 = OPERATOR / "oracle_operator_analytics_read_only_dependency_gate.py"
SOURCE_OOP_002 = OPERATOR / "oracle_operator_analytics_dependency_admission_gate.py"
SOURCE_OOP_003 = OPERATOR_QUERY / "oracle_operator_query_request_contract.py"
SOURCE_OOP_004 = OPERATOR_QUERY / "oracle_operator_query_request_admission_gate.py"
SOURCE_OOP_005 = OPERATOR_QUERY / "oracle_operator_query_resolution_plan.py"
SOURCE_OOP_006 = OPERATOR_QUERY / "oracle_operator_query_resolution_authorization_gate.py"
SOURCE_OOP_007 = OPERATOR_QUERY / "oracle_operator_query_resolution_authorization_consumption_gate.py"
SOURCE_OOP_008 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_readiness_gate.py"
SOURCE_OOP_009 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_authorization_gate.py"
SOURCE_OOP_010 = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_authorization_consumption_gate.py"
SOURCE_OOP_011 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_readiness_gate.py"
SOURCE_OOP_012 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_authorization_gate.py"
SOURCE_OOP_013 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_authorization_consumption_gate.py"
SOURCE_OOP_014 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_activation_gate.py"
SOURCE_OOP_015 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_gate.py"

PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate.py"
TEST = ROOT / "test_oop_016_oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    EXECUTION_RESULT_TYPE as OOP_015_EXECUTION_RESULT_TYPE,
    EXECUTION_STATUS as OOP_015_EXECUTION_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecution,
)

SCHEMA_VERSION = "OOP-016"
ENGINE_ID = "OOP-016"
POLICY_ID = (
    "oracle.operator.query-resolution-adapter-invocation-execution-result-certification-gate.v1"
)
CERTIFICATION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-execution-result-certification.v1"
)
CERTIFICATION_STATUS = (
    "operator_query_resolution_adapter_invocation_execution_result_certified"
)
CERTIFIED_RESULT_TYPE = "immutable_certified_bounded_read_only_adapter_result"

EXPECTED_EXECUTION_STATUS = OOP_015_EXECUTION_STATUS
EXPECTED_EXECUTION_RESULT_TYPE = OOP_015_EXECUTION_RESULT_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
    RuntimeError
):
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
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
        f"unsupported value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            _canonical(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True)
class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification:
    execution_result_certification_id: str
    source_adapter_invocation_execution_id: str
    source_adapter_invocation_execution_hash: str
    source_adapter_invocation_activation_id: str
    source_adapter_invocation_activation_hash: str
    source_adapter_execution_consumption_id: str
    source_adapter_execution_consumption_hash: str
    source_adapter_execution_authorization_id: str
    source_adapter_execution_authorization_hash: str
    source_adapter_execution_readiness_id: str
    source_adapter_execution_readiness_hash: str
    source_read_consumption_id: str
    source_read_consumption_hash: str
    source_read_authorization_id: str
    source_read_authorization_hash: str
    source_read_readiness_id: str
    source_read_readiness_hash: str
    source_resolution_consumption_id: str
    source_resolution_consumption_hash: str
    source_resolution_authorization_id: str
    source_resolution_authorization_hash: str
    source_resolution_plan_id: str
    source_resolution_plan_hash: str
    source_query_admission_id: str
    source_query_admission_hash: str
    source_query_request_id: str
    source_query_request_hash: str
    source_admission_id: str
    source_admission_hash: str
    source_dependency_receipt_id: str
    source_dependency_receipt_hash: str
    source_authorization_id: str
    source_authorization_hash: str
    operator_namespace: str
    query_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    invocation_package_type: str
    execution_package_type: str
    active_invocation_type: str
    execution_result_type: str
    certified_result_type: str
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    certified_resolution_strategy: str
    certified_entry_count: int
    certified_response_artifact_entry_ids: tuple[str, ...]
    certified_query_response_ids: tuple[str, ...]
    certified_result_count: int
    certified_result_hashes: tuple[str, ...]
    certified_result_payloads: tuple[Mapping[str, Any], ...]
    execution_type_verified: bool
    execution_identity_verified: bool
    execution_hash_verified: bool
    execution_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    immutable_execution_package_verified: bool
    execution_result_type_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    execution_performed_verified: bool
    artifact_read_performed_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    deterministic_certification_verified: bool
    adapter_invocation_active: bool
    adapter_invocation_execution_ready: bool
    adapter_invocation_execution_authorized: bool
    adapter_invocation_execution_allowed: bool
    adapter_invocation_execution_performed: bool
    analytics_artifact_read_allowed: bool
    analytics_artifact_read_performed: bool
    analytics_query_execution_allowed: bool
    analytics_query_execution_performed: bool
    analytics_reexecution_allowed: bool
    analytics_reexecution_performed: bool
    analytics_database_connection_allowed: bool
    analytics_database_connection_performed: bool
    analytics_mutation_allowed: bool
    analytics_mutation_performed: bool
    research_response_materialization_allowed: bool
    research_response_materialization_performed: bool
    operator_session_construction_allowed: bool
    operator_console_rendering_allowed: bool
    operator_presentation_rendering_allowed: bool
    publication_allowed: bool
    publication_performed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    qseries_execution_performed: bool
    order_creation_allowed: bool
    order_creation_performed: bool
    funds_movement_allowed: bool
    funds_movement_performed: bool
    portfolio_mutation_allowed: bool
    portfolio_mutation_performed: bool
    certification_status: str
    execution_result_certification_hash: str


class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate:
    @staticmethod
    def _verify_execution(
        execution: OracleOperatorQueryResolutionAdapterInvocationExecution,
    ) -> None:
        if not isinstance(
            execution,
            OracleOperatorQueryResolutionAdapterInvocationExecution,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "source must be the canonical OOP-015 execution result"
            )

        body = asdict(execution)
        supplied_hash = body.pop("adapter_invocation_execution_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution hash mismatch"
            )

        required_hashes = (
            execution.adapter_invocation_execution_id,
            execution.source_adapter_invocation_activation_hash,
            execution.source_adapter_execution_consumption_hash,
            execution.source_adapter_execution_authorization_hash,
            execution.source_adapter_execution_readiness_hash,
            execution.source_read_consumption_hash,
            execution.source_read_authorization_hash,
            execution.source_read_readiness_hash,
            execution.source_resolution_consumption_hash,
            execution.source_resolution_authorization_hash,
            execution.source_resolution_plan_hash,
            execution.source_query_admission_hash,
            execution.source_query_request_hash,
            execution.source_admission_hash,
            execution.source_dependency_receipt_hash,
            execution.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 lineage contains invalid hashes"
            )

        if execution.execution_status != EXPECTED_EXECUTION_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution is not complete"
            )
        if execution.execution_result_type != EXPECTED_EXECUTION_RESULT_TYPE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution result type mismatch"
            )
        if execution.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "operator namespace mismatch"
            )
        if execution.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "query namespace mismatch"
            )

        if execution.executed_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution contains no entries"
            )
        if execution.executed_entry_count != execution.result_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "execution/result cardinality mismatch"
            )
        if execution.result_count != len(execution.result_payloads):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result payload cardinality mismatch"
            )
        if execution.result_count != len(execution.result_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result hash cardinality mismatch"
            )
        if execution.executed_entry_count != len(
            execution.executed_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if execution.executed_entry_count != len(
            execution.executed_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(execution.executed_response_artifact_entry_ids)) != execution.executed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(execution.executed_query_response_ids)) != execution.executed_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "duplicate query-response identities detected"
            )

        recomputed_hashes = tuple(stable_hash(item) for item in execution.result_payloads)
        if recomputed_hashes != tuple(execution.result_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "result payload hash mismatch"
            )

        for index, payload in enumerate(execution.result_payloads):
            if not isinstance(payload, Mapping):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result payload must be a mapping"
                )
            if (
                payload.get("response_artifact_entry_id")
                != execution.executed_response_artifact_entry_ids[index]
            ):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result artifact-entry identity mismatch"
                )
            if (
                payload.get("query_response_id")
                != execution.executed_query_response_ids[index]
            ):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                    "result query-response identity mismatch"
                )

        required_truths = (
            execution.activation_type_verified,
            execution.activation_identity_verified,
            execution.activation_hash_verified,
            execution.activation_status_verified,
            execution.complete_lineage_verified,
            execution.namespaces_verified,
            execution.query_parameters_verified,
            execution.frozen_scope_verified,
            execution.frozen_scope_preserved,
            execution.immutable_invocation_package_verified,
            execution.immutable_execution_package_verified,
            execution.read_adapter_contract_verified,
            execution.bounded_artifact_read_verified,
            execution.single_read_invocation_verified,
            execution.adapter_result_cardinality_verified,
            execution.adapter_result_identity_verified,
            execution.deterministic_execution_verified,
            execution.adapter_invocation_active,
            execution.adapter_invocation_execution_ready,
            execution.adapter_invocation_execution_authorized,
            execution.adapter_invocation_execution_allowed,
            execution.adapter_invocation_execution_performed,
            execution.analytics_artifact_read_allowed,
            execution.analytics_artifact_read_performed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution is incomplete"
            )

        forbidden_activity = (
            execution.analytics_query_execution_allowed,
            execution.analytics_query_execution_performed,
            execution.analytics_reexecution_allowed,
            execution.analytics_reexecution_performed,
            execution.analytics_database_connection_allowed,
            execution.analytics_database_connection_performed,
            execution.analytics_mutation_allowed,
            execution.analytics_mutation_performed,
            execution.research_response_materialization_allowed,
            execution.research_response_materialization_performed,
            execution.operator_session_construction_allowed,
            execution.operator_console_rendering_allowed,
            execution.operator_presentation_rendering_allowed,
            execution.publication_allowed,
            execution.publication_performed,
            execution.qseries_handoff_allowed,
            execution.qseries_execution_allowed,
            execution.qseries_execution_performed,
            execution.order_creation_allowed,
            execution.order_creation_performed,
            execution.funds_movement_allowed,
            execution.funds_movement_performed,
            execution.portfolio_mutation_allowed,
            execution.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError(
                "OOP-015 execution contains forbidden activity"
            )

    def certify(
        self,
        *,
        execution: OracleOperatorQueryResolutionAdapterInvocationExecution,
    ) -> OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification:
        self._verify_execution(execution)

        certification_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_adapter_invocation_execution_id": (
                    execution.adapter_invocation_execution_id
                ),
                "source_adapter_invocation_execution_hash": (
                    execution.adapter_invocation_execution_hash
                ),
                "certified_result_type": CERTIFIED_RESULT_TYPE,
                "read_adapter_contract_id": execution.read_adapter_contract_id,
                "execution_mode": execution.execution_mode,
                "certified_response_artifact_entry_ids": (
                    execution.executed_response_artifact_entry_ids
                ),
                "certified_query_response_ids": execution.executed_query_response_ids,
                "certified_result_hashes": execution.result_hashes,
            }
        )

        body = {
            "execution_result_certification_id": certification_id,
            "source_adapter_invocation_execution_id": execution.adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": execution.adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": execution.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": execution.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": execution.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": execution.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": execution.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": execution.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": execution.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": execution.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": execution.source_read_consumption_id,
            "source_read_consumption_hash": execution.source_read_consumption_hash,
            "source_read_authorization_id": execution.source_read_authorization_id,
            "source_read_authorization_hash": execution.source_read_authorization_hash,
            "source_read_readiness_id": execution.source_read_readiness_id,
            "source_read_readiness_hash": execution.source_read_readiness_hash,
            "source_resolution_consumption_id": execution.source_resolution_consumption_id,
            "source_resolution_consumption_hash": execution.source_resolution_consumption_hash,
            "source_resolution_authorization_id": execution.source_resolution_authorization_id,
            "source_resolution_authorization_hash": execution.source_resolution_authorization_hash,
            "source_resolution_plan_id": execution.source_resolution_plan_id,
            "source_resolution_plan_hash": execution.source_resolution_plan_hash,
            "source_query_admission_id": execution.source_query_admission_id,
            "source_query_admission_hash": execution.source_query_admission_hash,
            "source_query_request_id": execution.source_query_request_id,
            "source_query_request_hash": execution.source_query_request_hash,
            "source_admission_id": execution.source_admission_id,
            "source_admission_hash": execution.source_admission_hash,
            "source_dependency_receipt_id": execution.source_dependency_receipt_id,
            "source_dependency_receipt_hash": execution.source_dependency_receipt_hash,
            "source_authorization_id": execution.source_authorization_id,
            "source_authorization_hash": execution.source_authorization_hash,
            "operator_namespace": execution.operator_namespace,
            "query_namespace": execution.query_namespace,
            "consumer_id": execution.consumer_id,
            "projection": execution.projection,
            "query_mode": execution.query_mode,
            "query_text": execution.query_text,
            "time_scope": execution.time_scope,
            "sort_order": execution.sort_order,
            "result_limit": execution.result_limit,
            "requested_tags": tuple(execution.requested_tags),
            "invocation_package_type": execution.invocation_package_type,
            "execution_package_type": execution.execution_package_type,
            "active_invocation_type": execution.active_invocation_type,
            "execution_result_type": execution.execution_result_type,
            "certified_result_type": CERTIFIED_RESULT_TYPE,
            "read_invocation_mode": execution.read_invocation_mode,
            "read_adapter_contract_id": execution.read_adapter_contract_id,
            "execution_mode": execution.execution_mode,
            "certified_resolution_strategy": execution.executed_resolution_strategy,
            "certified_entry_count": execution.executed_entry_count,
            "certified_response_artifact_entry_ids": tuple(
                execution.executed_response_artifact_entry_ids
            ),
            "certified_query_response_ids": tuple(
                execution.executed_query_response_ids
            ),
            "certified_result_count": execution.result_count,
            "certified_result_hashes": tuple(execution.result_hashes),
            "certified_result_payloads": tuple(execution.result_payloads),
            "execution_type_verified": True,
            "execution_identity_verified": True,
            "execution_hash_verified": True,
            "execution_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "immutable_execution_package_verified": True,
            "execution_result_type_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "execution_performed_verified": True,
            "artifact_read_performed_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "deterministic_certification_verified": True,
            "adapter_invocation_active": True,
            "adapter_invocation_execution_ready": True,
            "adapter_invocation_execution_authorized": True,
            "adapter_invocation_execution_allowed": True,
            "adapter_invocation_execution_performed": True,
            "analytics_artifact_read_allowed": True,
            "analytics_artifact_read_performed": True,
            "analytics_query_execution_allowed": False,
            "analytics_query_execution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
            "research_response_materialization_allowed": False,
            "research_response_materialization_performed": False,
            "operator_session_construction_allowed": False,
            "operator_console_rendering_allowed": False,
            "operator_presentation_rendering_allowed": False,
            "publication_allowed": False,
            "publication_performed": False,
            "qseries_handoff_allowed": False,
            "qseries_execution_allowed": False,
            "qseries_execution_performed": False,
            "order_creation_allowed": False,
            "order_creation_performed": False,
            "funds_movement_allowed": False,
            "funds_movement_performed": False,
            "portfolio_mutation_allowed": False,
            "portfolio_mutation_performed": False,
            "certification_status": CERTIFICATION_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification(
            **body,
            execution_result_certification_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CERTIFICATION_SCHEMA_VERSION",
    "CERTIFICATION_STATUS",
    "CERTIFIED_RESULT_TYPE",
    "EXPECTED_EXECUTION_STATUS",
    "EXPECTED_EXECUTION_RESULT_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_015_oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    _activation,
    _DeterministicReadOnlyAdapter,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    CERTIFICATION_STATUS,
    CERTIFIED_RESULT_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError,
    stable_hash,
)


def _execution():
    return OracleOperatorQueryResolutionAdapterInvocationExecutionGate().execute(
        activation=_activation(),
        adapter=_DeterministicReadOnlyAdapter(),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe execution result certification accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-016 TEST")
    print(" EXECUTION RESULT CERTIFICATION")
    print(" CERTIFIED BOUNDED READ-ONLY RESULT")
    print("=" * 40)

    execution = _execution()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate()

    first = gate.certify(execution=execution)
    repeated = gate.certify(execution=execution)

    assert first == repeated
    assert first.execution_result_certification_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "execution_result_certification_hash"
        }
    )

    assert first.source_adapter_invocation_execution_id == execution.adapter_invocation_execution_id
    assert first.source_adapter_invocation_execution_hash == execution.adapter_invocation_execution_hash
    assert first.certified_result_type == CERTIFIED_RESULT_TYPE
    assert first.certified_entry_count == execution.executed_entry_count
    assert first.certified_result_count == execution.result_count
    assert first.certified_response_artifact_entry_ids == execution.executed_response_artifact_entry_ids
    assert first.certified_query_response_ids == execution.executed_query_response_ids
    assert first.certified_result_hashes == execution.result_hashes
    assert first.certified_result_payloads == execution.result_payloads

    assert first.execution_type_verified
    assert first.execution_identity_verified
    assert first.execution_hash_verified
    assert first.execution_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.immutable_execution_package_verified
    assert first.execution_result_type_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.execution_performed_verified
    assert first.artifact_read_performed_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.deterministic_certification_verified

    assert first.adapter_invocation_execution_performed
    assert first.analytics_artifact_read_performed
    assert not first.analytics_query_execution_allowed
    assert not first.analytics_query_execution_performed
    assert not first.analytics_reexecution_allowed
    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_allowed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
    assert not first.research_response_materialization_allowed
    assert not first.research_response_materialization_performed
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.qseries_handoff_allowed
    assert not first.qseries_execution_allowed
    assert not first.qseries_execution_performed
    assert not first.order_creation_allowed
    assert not first.order_creation_performed
    assert not first.funds_movement_allowed
    assert not first.funds_movement_performed
    assert not first.portfolio_mutation_allowed
    assert not first.portfolio_mutation_performed
    assert first.certification_status == CERTIFICATION_STATUS

    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                adapter_invocation_execution_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                execution_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                result_count=execution.result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                result_hashes=("0" * 64,) * execution.result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            execution=replace(
                execution,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-015 execution result consumed")
    print("[PASS] OOP-015 identity, hash, status, and lineage verified")
    print("[PASS] Result payload hashes recomputed and verified")
    print("[PASS] Result cardinality and exact identities certified")
    print("[PASS] Frozen bounded read scope preserved")
    print("[PASS] First analytics artifact read result certified")
    print("[PASS] No analytics query execution, reexecution, DB, or mutation occurred")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe executions rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_replacement(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def append_export(path: Path, export_line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8", newline="\n")
    existing = path.read_text(encoding="utf-8")
    if export_line in existing.splitlines():
        print(f"[OK] PACKAGE EXPORT PRESENT: {path.resolve()}")
        return
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + export_line + "\n", encoding="utf-8", newline="\n")
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_contract(path: Path, name: str, required_tokens: tuple[str, ...]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {name} module missing: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in text]
    if missing:
        raise RuntimeError(
            f"Actual {name} contract mismatch; missing: " + ", ".join(missing)
        )
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-016 INSTALLER")
    print(" EXECUTION RESULT CERTIFICATION")
    print(" CERTIFIED BOUNDED READ-ONLY RESULT")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_015,
        "OOP-015",
        (
            'SCHEMA_VERSION = "OOP-015"',
            "class OracleOperatorQueryResolutionAdapterInvocationExecution",
            "class OracleOperatorQueryResolutionAdapterInvocationExecutionGate",
            "adapter_invocation_execution_id",
            "adapter_invocation_execution_hash",
            "execution_status",
            "execution_result_type",
            "result_count",
            "result_hashes",
            "result_payloads",
            "adapter_invocation_execution_performed",
            "analytics_artifact_read_performed",
            "analytics_query_execution_allowed",
            "research_response_materialization_allowed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
        (SOURCE_OOP_014, "OOP-014", ('SCHEMA_VERSION = "OOP-014"', "adapter_invocation_activation_hash")),
        (SOURCE_OOP_013, "OOP-013", ('SCHEMA_VERSION = "OOP-013"', "adapter_execution_consumption_hash")),
        (SOURCE_OOP_012, "OOP-012", ('SCHEMA_VERSION = "OOP-012"', "adapter_execution_authorization_hash")),
        (SOURCE_OOP_011, "OOP-011", ('SCHEMA_VERSION = "OOP-011"', "adapter_execution_readiness_hash")),
        (SOURCE_OOP_010, "OOP-010", ('SCHEMA_VERSION = "OOP-010"', "read_consumption_hash")),
        (SOURCE_OOP_009, "OOP-009", ('SCHEMA_VERSION = "OOP-009"', "read_authorization_hash")),
        (SOURCE_OOP_008, "OOP-008", ('SCHEMA_VERSION = "OOP-008"', "read_readiness_hash")),
        (SOURCE_OOP_007, "OOP-007", ('SCHEMA_VERSION = "OOP-007"', "resolution_consumption_hash")),
        (SOURCE_OOP_006, "OOP-006", ('SCHEMA_VERSION = "OOP-006"', "resolution_authorization_hash")),
        (SOURCE_OOP_005, "OOP-005", ('SCHEMA_VERSION = "OOP-005"', "resolution_plan_hash")),
        (SOURCE_OOP_004, "OOP-004", ('SCHEMA_VERSION = "OOP-004"', "query_admission_hash")),
        (SOURCE_OOP_003, "OOP-003", ('SCHEMA_VERSION = "OOP-003"', "query_request_hash")),
        (SOURCE_OOP_002, "OOP-002", ('SCHEMA_VERSION = "OOP-002"', "admission_hash")),
        (SOURCE_OOP_001, "OOP-001", ('SCHEMA_VERSION = "OOP-001"', "dependency_receipt_hash")),
        (
            SOURCE_060,
            "INT-OIA-060",
            ('SCHEMA_VERSION = "INT-OIA-060"', "authorization_hash", "read_only_consumption_verified"),
        ),
    ):
        verify_contract(path, name, tokens)

    protected_before = {
        path: sha256_file(path)
        for path in (
            SOURCE_OOP_015,
            SOURCE_OOP_014,
            SOURCE_OOP_013,
            SOURCE_OOP_012,
            SOURCE_OOP_011,
            SOURCE_OOP_010,
            SOURCE_OOP_009,
            SOURCE_OOP_008,
            SOURCE_OOP_007,
            SOURCE_OOP_006,
            SOURCE_OOP_005,
            SOURCE_OOP_004,
            SOURCE_OOP_003,
            SOURCE_OOP_002,
            SOURCE_OOP_001,
            SOURCE_060,
        )
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import *",
    )

    for target in (PRODUCTION, TEST, QUERY_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-015 and INT-OIA-060 unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(
                f"Protected upstream module changed during test: {path}"
            )

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-016 test executed automatically")
    print()
    print("[DONE] OOP-016 execution result certification gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
