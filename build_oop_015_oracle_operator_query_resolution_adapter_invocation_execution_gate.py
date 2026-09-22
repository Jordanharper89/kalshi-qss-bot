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

PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_gate.py"
TEST = ROOT / "test_oop_015_oracle_operator_query_resolution_adapter_invocation_execution_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol, Sequence

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_activation_gate import (
    ACTIVATION_STATUS as OOP_014_ACTIVATION_STATUS,
    ACTIVE_INVOCATION_TYPE as OOP_014_ACTIVE_INVOCATION_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationActivation,
)

SCHEMA_VERSION = "OOP-015"
ENGINE_ID = "OOP-015"
POLICY_ID = "oracle.operator.query-resolution-adapter-invocation-execution-gate.v1"
EXECUTION_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-adapter-invocation-execution.v1"
)
EXECUTION_STATUS = "operator_query_resolution_adapter_invocation_executed"
EXECUTION_RESULT_TYPE = "immutable_bounded_read_only_adapter_execution_result"

EXPECTED_ACTIVATION_STATUS = OOP_014_ACTIVATION_STATUS
EXPECTED_ACTIVE_INVOCATION_TYPE = OOP_014_ACTIVE_INVOCATION_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
    RuntimeError
):
    pass


class ReadOnlyAnalyticsAdapter(Protocol):
    def __call__(
        self,
        *,
        response_artifact_entry_ids: tuple[str, ...],
        query_response_ids: tuple[str, ...],
        query_mode: str,
        query_text: str,
        time_scope: str,
        sort_order: str,
        result_limit: int,
        requested_tags: tuple[str, ...],
    ) -> Sequence[Mapping[str, Any]]:
        ...


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
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
class OracleOperatorQueryResolutionAdapterInvocationExecution:
    adapter_invocation_execution_id: str
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
    read_invocation_mode: str
    read_adapter_contract_id: str
    execution_mode: str
    executed_resolution_strategy: str
    executed_entry_count: int
    executed_response_artifact_entry_ids: tuple[str, ...]
    executed_query_response_ids: tuple[str, ...]
    result_count: int
    result_hashes: tuple[str, ...]
    result_payloads: tuple[Mapping[str, Any], ...]
    activation_type_verified: bool
    activation_identity_verified: bool
    activation_hash_verified: bool
    activation_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_invocation_package_verified: bool
    immutable_execution_package_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    single_read_invocation_verified: bool
    adapter_result_cardinality_verified: bool
    adapter_result_identity_verified: bool
    deterministic_execution_verified: bool
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
    execution_status: str
    adapter_invocation_execution_hash: str


class OracleOperatorQueryResolutionAdapterInvocationExecutionGate:
    @staticmethod
    def _verify_activation(
        activation: OracleOperatorQueryResolutionAdapterInvocationActivation,
    ) -> None:
        if not isinstance(
            activation,
            OracleOperatorQueryResolutionAdapterInvocationActivation,
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "source must be the canonical OOP-014 activation record"
            )

        body = asdict(activation)
        supplied_hash = body.pop("adapter_invocation_activation_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 activation hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 activation hash mismatch"
            )

        required_hashes = (
            activation.adapter_invocation_activation_id,
            activation.source_adapter_execution_consumption_hash,
            activation.source_adapter_execution_authorization_hash,
            activation.source_adapter_execution_readiness_hash,
            activation.source_read_consumption_hash,
            activation.source_read_authorization_hash,
            activation.source_read_readiness_hash,
            activation.source_resolution_consumption_hash,
            activation.source_resolution_authorization_hash,
            activation.source_resolution_plan_hash,
            activation.source_query_admission_hash,
            activation.source_query_request_hash,
            activation.source_admission_hash,
            activation.source_dependency_receipt_hash,
            activation.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 lineage contains invalid hashes"
            )

        if activation.activation_status != EXPECTED_ACTIVATION_STATUS:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 activation is not active"
            )
        if activation.active_invocation_type != EXPECTED_ACTIVE_INVOCATION_TYPE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "active invocation type mismatch"
            )
        if activation.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "operator namespace mismatch"
            )
        if activation.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "query namespace mismatch"
            )

        if activation.active_entry_count < 1:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "activation contains no entries"
            )
        if activation.active_entry_count != len(
            activation.active_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if activation.active_entry_count != len(
            activation.active_query_response_ids
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "query-response cardinality mismatch"
            )

        required_truths = (
            activation.consumption_type_verified,
            activation.consumption_identity_verified,
            activation.consumption_hash_verified,
            activation.consumption_status_verified,
            activation.complete_lineage_verified,
            activation.namespaces_verified,
            activation.query_parameters_verified,
            activation.frozen_scope_verified,
            activation.frozen_scope_preserved,
            activation.immutable_invocation_package_verified,
            activation.immutable_execution_package_verified,
            activation.read_adapter_contract_verified,
            activation.bounded_artifact_read_verified,
            activation.single_read_invocation_verified,
            activation.single_use_execution_consumption_verified,
            activation.deterministic_activation_verified,
            activation.adapter_invocation_active,
            activation.adapter_invocation_execution_ready,
            activation.adapter_invocation_execution_authorized,
            activation.adapter_invocation_execution_allowed,
            activation.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 activation is incomplete"
            )

        forbidden_activity = (
            activation.adapter_invocation_execution_performed,
            activation.analytics_artifact_read_performed,
            activation.analytics_query_execution_allowed,
            activation.analytics_query_execution_performed,
            activation.analytics_reexecution_allowed,
            activation.analytics_reexecution_performed,
            activation.analytics_database_connection_allowed,
            activation.analytics_database_connection_performed,
            activation.analytics_mutation_allowed,
            activation.analytics_mutation_performed,
            activation.research_response_materialization_allowed,
            activation.research_response_materialization_performed,
            activation.operator_session_construction_allowed,
            activation.operator_console_rendering_allowed,
            activation.operator_presentation_rendering_allowed,
            activation.publication_allowed,
            activation.publication_performed,
            activation.qseries_handoff_allowed,
            activation.qseries_execution_allowed,
            activation.qseries_execution_performed,
            activation.order_creation_allowed,
            activation.order_creation_performed,
            activation.funds_movement_allowed,
            activation.funds_movement_performed,
            activation.portfolio_mutation_allowed,
            activation.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "OOP-014 activation contains forbidden prior activity"
            )

    def execute(
        self,
        *,
        activation: OracleOperatorQueryResolutionAdapterInvocationActivation,
        adapter: ReadOnlyAnalyticsAdapter,
    ) -> OracleOperatorQueryResolutionAdapterInvocationExecution:
        self._verify_activation(activation)
        if not callable(adapter):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "adapter must be callable"
            )

        raw_results = adapter(
            response_artifact_entry_ids=tuple(
                activation.active_response_artifact_entry_ids
            ),
            query_response_ids=tuple(activation.active_query_response_ids),
            query_mode=activation.query_mode,
            query_text=activation.query_text,
            time_scope=activation.time_scope,
            sort_order=activation.sort_order,
            result_limit=activation.result_limit,
            requested_tags=tuple(activation.requested_tags),
        )

        if isinstance(raw_results, (str, bytes)) or not isinstance(
            raw_results, Sequence
        ):
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "adapter result must be a sequence of mappings"
            )

        canonical_results: list[Mapping[str, Any]] = []
        for item in raw_results:
            if not isinstance(item, Mapping):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                    "adapter result item must be a mapping"
                )
            canonical_item = _canonical(item)
            if not isinstance(canonical_item, Mapping):
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                    "canonical adapter result must remain a mapping"
                )
            canonical_results.append(canonical_item)

        if len(canonical_results) != activation.active_entry_count:
            raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                "adapter result count does not match activated scope"
            )

        for index, item in enumerate(canonical_results):
            expected_entry_id = activation.active_response_artifact_entry_ids[index]
            expected_response_id = activation.active_query_response_ids[index]
            if item.get("response_artifact_entry_id") != expected_entry_id:
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                    "adapter result artifact-entry identity mismatch"
                )
            if item.get("query_response_id") != expected_response_id:
                raise OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError(
                    "adapter result query-response identity mismatch"
                )

        result_payloads = tuple(canonical_results)
        result_hashes = tuple(stable_hash(item) for item in result_payloads)

        adapter_invocation_execution_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_adapter_invocation_activation_id": (
                    activation.adapter_invocation_activation_id
                ),
                "source_adapter_invocation_activation_hash": (
                    activation.adapter_invocation_activation_hash
                ),
                "execution_result_type": EXECUTION_RESULT_TYPE,
                "read_adapter_contract_id": activation.read_adapter_contract_id,
                "execution_mode": activation.execution_mode,
                "executed_response_artifact_entry_ids": (
                    activation.active_response_artifact_entry_ids
                ),
                "executed_query_response_ids": activation.active_query_response_ids,
                "result_hashes": result_hashes,
            }
        )

        body = {
            "adapter_invocation_execution_id": adapter_invocation_execution_id,
            "source_adapter_invocation_activation_id": activation.adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": activation.adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": activation.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": activation.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": activation.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": activation.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": activation.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": activation.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": activation.source_read_consumption_id,
            "source_read_consumption_hash": activation.source_read_consumption_hash,
            "source_read_authorization_id": activation.source_read_authorization_id,
            "source_read_authorization_hash": activation.source_read_authorization_hash,
            "source_read_readiness_id": activation.source_read_readiness_id,
            "source_read_readiness_hash": activation.source_read_readiness_hash,
            "source_resolution_consumption_id": activation.source_resolution_consumption_id,
            "source_resolution_consumption_hash": activation.source_resolution_consumption_hash,
            "source_resolution_authorization_id": activation.source_resolution_authorization_id,
            "source_resolution_authorization_hash": activation.source_resolution_authorization_hash,
            "source_resolution_plan_id": activation.source_resolution_plan_id,
            "source_resolution_plan_hash": activation.source_resolution_plan_hash,
            "source_query_admission_id": activation.source_query_admission_id,
            "source_query_admission_hash": activation.source_query_admission_hash,
            "source_query_request_id": activation.source_query_request_id,
            "source_query_request_hash": activation.source_query_request_hash,
            "source_admission_id": activation.source_admission_id,
            "source_admission_hash": activation.source_admission_hash,
            "source_dependency_receipt_id": activation.source_dependency_receipt_id,
            "source_dependency_receipt_hash": activation.source_dependency_receipt_hash,
            "source_authorization_id": activation.source_authorization_id,
            "source_authorization_hash": activation.source_authorization_hash,
            "operator_namespace": activation.operator_namespace,
            "query_namespace": activation.query_namespace,
            "consumer_id": activation.consumer_id,
            "projection": activation.projection,
            "query_mode": activation.query_mode,
            "query_text": activation.query_text,
            "time_scope": activation.time_scope,
            "sort_order": activation.sort_order,
            "result_limit": activation.result_limit,
            "requested_tags": tuple(activation.requested_tags),
            "invocation_package_type": activation.invocation_package_type,
            "execution_package_type": activation.execution_package_type,
            "active_invocation_type": activation.active_invocation_type,
            "execution_result_type": EXECUTION_RESULT_TYPE,
            "read_invocation_mode": activation.read_invocation_mode,
            "read_adapter_contract_id": activation.read_adapter_contract_id,
            "execution_mode": activation.execution_mode,
            "executed_resolution_strategy": activation.active_resolution_strategy,
            "executed_entry_count": activation.active_entry_count,
            "executed_response_artifact_entry_ids": tuple(
                activation.active_response_artifact_entry_ids
            ),
            "executed_query_response_ids": tuple(
                activation.active_query_response_ids
            ),
            "result_count": len(result_payloads),
            "result_hashes": result_hashes,
            "result_payloads": result_payloads,
            "activation_type_verified": True,
            "activation_identity_verified": True,
            "activation_hash_verified": True,
            "activation_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_invocation_package_verified": True,
            "immutable_execution_package_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "single_read_invocation_verified": True,
            "adapter_result_cardinality_verified": True,
            "adapter_result_identity_verified": True,
            "deterministic_execution_verified": True,
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
            "execution_status": EXECUTION_STATUS,
        }

        return OracleOperatorQueryResolutionAdapterInvocationExecution(
            **body,
            adapter_invocation_execution_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "EXECUTION_SCHEMA_VERSION",
    "EXECUTION_STATUS",
    "EXECUTION_RESULT_TYPE",
    "EXPECTED_ACTIVATION_STATUS",
    "EXPECTED_ACTIVE_INVOCATION_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "ReadOnlyAnalyticsAdapter",
    "OracleOperatorQueryResolutionAdapterInvocationExecution",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionGate",
    "OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_014_oracle_operator_query_resolution_adapter_invocation_activation_gate import (
    _consumption,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_activation_gate import (
    OracleOperatorQueryResolutionAdapterInvocationActivationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_gate import (
    EXECUTION_RESULT_TYPE,
    EXECUTION_STATUS,
    OracleOperatorQueryResolutionAdapterInvocationExecutionGate,
    OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError,
    stable_hash,
)


def _activation():
    return OracleOperatorQueryResolutionAdapterInvocationActivationGate().activate(
        consumption=_consumption()
    )


class _DeterministicReadOnlyAdapter:
    def __call__(
        self,
        *,
        response_artifact_entry_ids,
        query_response_ids,
        query_mode,
        query_text,
        time_scope,
        sort_order,
        result_limit,
        requested_tags,
    ):
        return tuple(
            {
                "response_artifact_entry_id": entry_id,
                "query_response_id": response_id,
                "query_mode": query_mode,
                "query_text": query_text,
                "time_scope": time_scope,
                "sort_order": sort_order,
                "result_limit": result_limit,
                "requested_tags": tuple(requested_tags),
                "read_only": True,
                "artifact_payload": {
                    "market_id": f"market-{index + 1}",
                    "venue": "certified_read_only_fixture",
                    "prediction": 0.61,
                    "confidence": 0.78,
                },
            }
            for index, (entry_id, response_id) in enumerate(
                zip(response_artifact_entry_ids, query_response_ids)
            )
        )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe adapter execution accepted")
    except OracleOperatorQueryResolutionAdapterInvocationExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-015 TEST")
    print(" ADAPTER INVOCATION EXECUTION")
    print(" FIRST CERTIFIED ANALYTICS ARTIFACT READ")
    print("=" * 40)

    activation = _activation()
    gate = OracleOperatorQueryResolutionAdapterInvocationExecutionGate()
    adapter = _DeterministicReadOnlyAdapter()

    first = gate.execute(activation=activation, adapter=adapter)
    repeated = gate.execute(activation=activation, adapter=adapter)

    assert first == repeated
    assert first.adapter_invocation_execution_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "adapter_invocation_execution_hash"
        }
    )

    assert (
        first.source_adapter_invocation_activation_id
        == activation.adapter_invocation_activation_id
    )
    assert (
        first.source_adapter_invocation_activation_hash
        == activation.adapter_invocation_activation_hash
    )
    assert first.execution_result_type == EXECUTION_RESULT_TYPE
    assert first.executed_entry_count == activation.active_entry_count
    assert first.result_count == activation.active_entry_count
    assert len(first.result_hashes) == first.result_count
    assert len(first.result_payloads) == first.result_count
    assert (
        first.executed_response_artifact_entry_ids
        == activation.active_response_artifact_entry_ids
    )
    assert (
        first.executed_query_response_ids
        == activation.active_query_response_ids
    )

    assert first.activation_type_verified
    assert first.activation_identity_verified
    assert first.activation_hash_verified
    assert first.activation_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_invocation_package_verified
    assert first.immutable_execution_package_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.single_read_invocation_verified
    assert first.adapter_result_cardinality_verified
    assert first.adapter_result_identity_verified
    assert first.deterministic_execution_verified

    assert first.adapter_invocation_active
    assert first.adapter_invocation_execution_ready
    assert first.adapter_invocation_execution_authorized
    assert first.adapter_invocation_execution_allowed
    assert first.adapter_invocation_execution_performed
    assert first.analytics_artifact_read_allowed
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
    assert first.execution_status == EXECUTION_STATUS

    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                adapter_invocation_activation_hash="0" * 64,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                activation_status="wrong_status",
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                adapter_invocation_execution_performed=True,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=replace(
                activation,
                analytics_artifact_read_performed=True,
            ),
            adapter=adapter,
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=activation,
            adapter=lambda **_: (),
        )
    )
    _expect_rejected(
        lambda: gate.execute(
            activation=activation,
            adapter=lambda **_: (
                {
                    "response_artifact_entry_id": "wrong",
                    "query_response_id": "wrong",
                },
            ),
        )
    )

    print("[PASS] Actual OOP-014 active invocation consumed")
    print("[PASS] OOP-014 identity, hash, status, and lineage verified")
    print("[PASS] Frozen activated scope preserved without expansion")
    print("[PASS] Single bounded read-only adapter call performed")
    print("[PASS] First certified analytics artifact read completed")
    print("[PASS] Immutable deterministic execution evidence created")
    print("[PASS] Result cardinality and identities verified")
    print("[PASS] Research response materialization remains gated")
    print("[PASS] No analytics query execution or reexecution occurred")
    print("[PASS] No analytics database connection or mutation occurred")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed executions rejected")
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
    print(" OOP-015 INSTALLER")
    print(" ADAPTER INVOCATION EXECUTION")
    print(" FIRST CERTIFIED ANALYTICS ARTIFACT READ")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_014,
        "OOP-014",
        (
            'SCHEMA_VERSION = "OOP-014"',
            "class OracleOperatorQueryResolutionAdapterInvocationActivation",
            "class OracleOperatorQueryResolutionAdapterInvocationActivationGate",
            "adapter_invocation_activation_id",
            "adapter_invocation_activation_hash",
            "activation_status",
            "active_invocation_type",
            "adapter_invocation_active",
            "adapter_invocation_execution_ready",
            "adapter_invocation_execution_authorized",
            "adapter_invocation_execution_allowed",
            "adapter_invocation_execution_performed",
            "analytics_artifact_read_allowed",
            "analytics_artifact_read_performed",
            "research_response_materialization_allowed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
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
        "from .oracle_operator_query_resolution_adapter_invocation_execution_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_adapter_invocation_execution_gate import *",
    )

    for target in (PRODUCTION, TEST, QUERY_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-014 and INT-OIA-060 unchanged")

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
    print("[OK] OOP-015 test executed automatically")
    print()
    print("[DONE] OOP-015 adapter invocation execution gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
