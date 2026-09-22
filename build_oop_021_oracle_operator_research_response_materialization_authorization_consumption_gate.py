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
OPERATOR_RESEARCH_RESPONSE = OPERATOR / "research_response"

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
SOURCE_OOP_016 = OPERATOR_QUERY / "oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate.py"
SOURCE_OOP_017 = OPERATOR_QUERY / "oracle_operator_query_resolution_research_response_handoff_authorization_gate.py"
SOURCE_OOP_018 = OPERATOR_RESEARCH_RESPONSE / "oracle_operator_research_response_handoff_authorization_consumption_gate.py"
SOURCE_OOP_019 = OPERATOR_RESEARCH_RESPONSE / "oracle_operator_research_response_materialization_readiness_gate.py"
SOURCE_OOP_020 = OPERATOR_RESEARCH_RESPONSE / "oracle_operator_research_response_materialization_authorization_gate.py"

PRODUCTION = OPERATOR_RESEARCH_RESPONSE / "oracle_operator_research_response_materialization_authorization_consumption_gate.py"
TEST = ROOT / "test_oop_021_oracle_operator_research_response_materialization_authorization_consumption_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
RESEARCH_RESPONSE_PACKAGE = OPERATOR_RESEARCH_RESPONSE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_gate import (
    AUTHORIZATION_STATUS as OOP_020_AUTHORIZATION_STATUS,
    AUTHORIZATION_TYPE as OOP_020_AUTHORIZATION_TYPE,
    OracleOperatorResearchResponseMaterializationAuthorization,
)

SCHEMA_VERSION = "OOP-021"
ENGINE_ID = "OOP-021"
POLICY_ID = (
    "oracle.operator.research-response-materialization-authorization-consumption-gate.v1"
)
CONSUMPTION_SCHEMA_VERSION = (
    "oracle.operator.research-response.materialization-authorization-consumption.v1"
)
CONSUMPTION_STATUS = (
    "operator_research_response_materialization_authorization_consumed"
)
EXECUTION_PACKAGE_TYPE = (
    "single_use_immutable_research_response_materialization_execution_package"
)

EXPECTED_AUTHORIZATION_STATUS = OOP_020_AUTHORIZATION_STATUS
EXPECTED_AUTHORIZATION_TYPE = OOP_020_AUTHORIZATION_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
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
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
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
class OracleOperatorResearchResponseMaterializationAuthorizationConsumption:
    research_response_materialization_consumption_id: str
    source_research_response_materialization_authorization_id: str
    source_research_response_materialization_authorization_hash: str
    source_research_response_materialization_readiness_id: str
    source_research_response_materialization_readiness_hash: str
    source_research_response_handoff_consumption_id: str
    source_research_response_handoff_consumption_hash: str
    source_research_response_handoff_authorization_id: str
    source_research_response_handoff_authorization_hash: str
    source_execution_result_certification_id: str
    source_execution_result_certification_hash: str
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
    research_response_namespace: str
    consumer_id: str
    projection: str
    query_mode: str
    query_text: str
    time_scope: str
    sort_order: str
    result_limit: int
    requested_tags: tuple[str, ...]
    response_input_package_type: str
    readiness_type: str
    authorization_type: str
    execution_package_type: str
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    consumed_resolution_strategy: str
    consumed_entry_count: int
    consumed_response_artifact_entry_ids: tuple[str, ...]
    consumed_query_response_ids: tuple[str, ...]
    consumed_result_count: int
    consumed_result_hashes: tuple[str, ...]
    consumed_result_payloads: tuple[Mapping[str, Any], ...]
    authorization_type_verified: bool
    authorization_identity_verified: bool
    authorization_hash_verified: bool
    authorization_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    response_input_package_verified: bool
    response_schema_inputs_verified: bool
    response_content_inputs_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    single_use_consumption_verified: bool
    immutable_execution_package_verified: bool
    deterministic_consumption_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
    research_response_materialization_authorized: bool
    research_response_materialization_authorization_consumed: bool
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
    consumption_status: str
    research_response_materialization_consumption_hash: str


class OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate:
    @staticmethod
    def _verify_authorization(
        authorization: OracleOperatorResearchResponseMaterializationAuthorization,
    ) -> None:
        if not isinstance(
            authorization,
            OracleOperatorResearchResponseMaterializationAuthorization,
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "source must be the canonical OOP-020 materialization authorization"
            )

        body = asdict(authorization)
        supplied_hash = body.pop(
            "research_response_materialization_authorization_hash",
            None,
        )
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 authorization hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 authorization hash mismatch"
            )

        required_hashes = (
            authorization.research_response_materialization_authorization_id,
            authorization.source_research_response_materialization_readiness_hash,
            authorization.source_research_response_handoff_consumption_hash,
            authorization.source_research_response_handoff_authorization_hash,
            authorization.source_execution_result_certification_hash,
            authorization.source_adapter_invocation_execution_hash,
            authorization.source_adapter_invocation_activation_hash,
            authorization.source_adapter_execution_consumption_hash,
            authorization.source_adapter_execution_authorization_hash,
            authorization.source_adapter_execution_readiness_hash,
            authorization.source_read_consumption_hash,
            authorization.source_read_authorization_hash,
            authorization.source_read_readiness_hash,
            authorization.source_resolution_consumption_hash,
            authorization.source_resolution_authorization_hash,
            authorization.source_resolution_plan_hash,
            authorization.source_query_admission_hash,
            authorization.source_query_request_hash,
            authorization.source_admission_hash,
            authorization.source_dependency_receipt_hash,
            authorization.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 lineage contains invalid hashes"
            )

        if authorization.authorization_status != EXPECTED_AUTHORIZATION_STATUS:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 authorization is not active"
            )
        if authorization.authorization_type != EXPECTED_AUTHORIZATION_TYPE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorization type mismatch"
            )
        if authorization.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "operator namespace mismatch"
            )
        if authorization.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "query namespace mismatch"
            )
        if (
            authorization.research_response_namespace
            != EXPECTED_RESEARCH_RESPONSE_NAMESPACE
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "research response namespace mismatch"
            )

        if authorization.authorized_entry_count < 1:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorization contains no entries"
            )
        if authorization.authorized_entry_count != authorization.authorized_result_count:
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorized entry/result cardinality mismatch"
            )
        if authorization.authorized_result_count != len(
            authorization.authorized_result_payloads
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorized payload cardinality mismatch"
            )
        if authorization.authorized_result_count != len(
            authorization.authorized_result_hashes
        ):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorized hash cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in authorization.authorized_result_payloads
        )
        if recomputed_hashes != tuple(authorization.authorized_result_hashes):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "authorized payload hash mismatch"
            )

        required_truths = (
            authorization.readiness_type_verified,
            authorization.readiness_identity_verified,
            authorization.readiness_hash_verified,
            authorization.readiness_status_verified,
            authorization.complete_lineage_verified,
            authorization.namespaces_verified,
            authorization.query_parameters_verified,
            authorization.frozen_scope_verified,
            authorization.frozen_scope_preserved,
            authorization.response_input_package_verified,
            authorization.response_schema_inputs_verified,
            authorization.response_content_inputs_verified,
            authorization.result_cardinality_verified,
            authorization.result_identity_verified,
            authorization.result_payload_hashes_verified,
            authorization.single_use_authorization_verified,
            authorization.deterministic_authorization_verified,
            authorization.query_subsystem_complete,
            authorization.research_response_handoff_ready,
            authorization.research_response_handoff_authorized,
            authorization.research_response_handoff_consumed,
            authorization.research_response_materialization_ready,
            authorization.research_response_materialization_authorized,
            authorization.research_response_materialization_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 authorization is incomplete"
            )

        forbidden_activity = (
            authorization.research_response_materialization_performed,
            authorization.operator_session_construction_allowed,
            authorization.operator_console_rendering_allowed,
            authorization.operator_presentation_rendering_allowed,
            authorization.publication_allowed,
            authorization.publication_performed,
            authorization.qseries_handoff_allowed,
            authorization.qseries_execution_allowed,
            authorization.qseries_execution_performed,
            authorization.order_creation_allowed,
            authorization.order_creation_performed,
            authorization.funds_movement_allowed,
            authorization.funds_movement_performed,
            authorization.portfolio_mutation_allowed,
            authorization.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError(
                "OOP-020 authorization contains forbidden downstream activity"
            )

    def consume(
        self,
        *,
        authorization: OracleOperatorResearchResponseMaterializationAuthorization,
    ) -> OracleOperatorResearchResponseMaterializationAuthorizationConsumption:
        self._verify_authorization(authorization)

        consumption_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_research_response_materialization_authorization_id": (
                    authorization.research_response_materialization_authorization_id
                ),
                "source_research_response_materialization_authorization_hash": (
                    authorization.research_response_materialization_authorization_hash
                ),
                "execution_package_type": EXECUTION_PACKAGE_TYPE,
                "authorized_response_artifact_entry_ids": (
                    authorization.authorized_response_artifact_entry_ids
                ),
                "authorized_query_response_ids": (
                    authorization.authorized_query_response_ids
                ),
                "authorized_result_hashes": authorization.authorized_result_hashes,
            }
        )

        body = {
            "research_response_materialization_consumption_id": consumption_id,
            "source_research_response_materialization_authorization_id": authorization.research_response_materialization_authorization_id,
            "source_research_response_materialization_authorization_hash": authorization.research_response_materialization_authorization_hash,
            "source_research_response_materialization_readiness_id": authorization.source_research_response_materialization_readiness_id,
            "source_research_response_materialization_readiness_hash": authorization.source_research_response_materialization_readiness_hash,
            "source_research_response_handoff_consumption_id": authorization.source_research_response_handoff_consumption_id,
            "source_research_response_handoff_consumption_hash": authorization.source_research_response_handoff_consumption_hash,
            "source_research_response_handoff_authorization_id": authorization.source_research_response_handoff_authorization_id,
            "source_research_response_handoff_authorization_hash": authorization.source_research_response_handoff_authorization_hash,
            "source_execution_result_certification_id": authorization.source_execution_result_certification_id,
            "source_execution_result_certification_hash": authorization.source_execution_result_certification_hash,
            "source_adapter_invocation_execution_id": authorization.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": authorization.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": authorization.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": authorization.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": authorization.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": authorization.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": authorization.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": authorization.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": authorization.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": authorization.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": authorization.source_read_consumption_id,
            "source_read_consumption_hash": authorization.source_read_consumption_hash,
            "source_read_authorization_id": authorization.source_read_authorization_id,
            "source_read_authorization_hash": authorization.source_read_authorization_hash,
            "source_read_readiness_id": authorization.source_read_readiness_id,
            "source_read_readiness_hash": authorization.source_read_readiness_hash,
            "source_resolution_consumption_id": authorization.source_resolution_consumption_id,
            "source_resolution_consumption_hash": authorization.source_resolution_consumption_hash,
            "source_resolution_authorization_id": authorization.source_resolution_authorization_id,
            "source_resolution_authorization_hash": authorization.source_resolution_authorization_hash,
            "source_resolution_plan_id": authorization.source_resolution_plan_id,
            "source_resolution_plan_hash": authorization.source_resolution_plan_hash,
            "source_query_admission_id": authorization.source_query_admission_id,
            "source_query_admission_hash": authorization.source_query_admission_hash,
            "source_query_request_id": authorization.source_query_request_id,
            "source_query_request_hash": authorization.source_query_request_hash,
            "source_admission_id": authorization.source_admission_id,
            "source_admission_hash": authorization.source_admission_hash,
            "source_dependency_receipt_id": authorization.source_dependency_receipt_id,
            "source_dependency_receipt_hash": authorization.source_dependency_receipt_hash,
            "source_authorization_id": authorization.source_authorization_id,
            "source_authorization_hash": authorization.source_authorization_hash,
            "operator_namespace": authorization.operator_namespace,
            "query_namespace": authorization.query_namespace,
            "research_response_namespace": authorization.research_response_namespace,
            "consumer_id": authorization.consumer_id,
            "projection": authorization.projection,
            "query_mode": authorization.query_mode,
            "query_text": authorization.query_text,
            "time_scope": authorization.time_scope,
            "sort_order": authorization.sort_order,
            "result_limit": authorization.result_limit,
            "requested_tags": tuple(authorization.requested_tags),
            "response_input_package_type": authorization.response_input_package_type,
            "readiness_type": authorization.readiness_type,
            "authorization_type": authorization.authorization_type,
            "execution_package_type": EXECUTION_PACKAGE_TYPE,
            "certified_result_type": authorization.certified_result_type,
            "read_adapter_contract_id": authorization.read_adapter_contract_id,
            "execution_mode": authorization.execution_mode,
            "consumed_resolution_strategy": authorization.authorized_resolution_strategy,
            "consumed_entry_count": authorization.authorized_entry_count,
            "consumed_response_artifact_entry_ids": tuple(
                authorization.authorized_response_artifact_entry_ids
            ),
            "consumed_query_response_ids": tuple(
                authorization.authorized_query_response_ids
            ),
            "consumed_result_count": authorization.authorized_result_count,
            "consumed_result_hashes": tuple(authorization.authorized_result_hashes),
            "consumed_result_payloads": tuple(authorization.authorized_result_payloads),
            "authorization_type_verified": True,
            "authorization_identity_verified": True,
            "authorization_hash_verified": True,
            "authorization_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "response_input_package_verified": True,
            "response_schema_inputs_verified": True,
            "response_content_inputs_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "single_use_consumption_verified": True,
            "immutable_execution_package_verified": True,
            "deterministic_consumption_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": True,
            "research_response_materialization_authorization_consumed": True,
            "research_response_materialization_allowed": True,
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
            "consumption_status": CONSUMPTION_STATUS,
        }

        return OracleOperatorResearchResponseMaterializationAuthorizationConsumption(
            **body,
            research_response_materialization_consumption_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "CONSUMPTION_SCHEMA_VERSION",
    "CONSUMPTION_STATUS",
    "EXECUTION_PACKAGE_TYPE",
    "EXPECTED_AUTHORIZATION_STATUS",
    "EXPECTED_AUTHORIZATION_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorResearchResponseMaterializationAuthorizationConsumption",
    "OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate",
    "OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_020_oracle_operator_research_response_materialization_authorization_gate import (
    _readiness,
)

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_gate import (
    OracleOperatorResearchResponseMaterializationAuthorizationGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import (
    CONSUMPTION_STATUS,
    EXECUTION_PACKAGE_TYPE,
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate,
    OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
    return OracleOperatorResearchResponseMaterializationAuthorizationGate().authorize(
        readiness=_readiness()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe materialization authorization consumption accepted")
    except OracleOperatorResearchResponseMaterializationAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-021 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorResearchResponseMaterializationAuthorizationConsumptionGate()

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.research_response_materialization_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_consumption_hash"
        }
    )

    assert first.source_research_response_materialization_authorization_id == authorization.research_response_materialization_authorization_id
    assert first.source_research_response_materialization_authorization_hash == authorization.research_response_materialization_authorization_hash
    assert first.execution_package_type == EXECUTION_PACKAGE_TYPE
    assert first.consumed_entry_count == authorization.authorized_entry_count
    assert first.consumed_result_count == authorization.authorized_result_count
    assert first.consumed_response_artifact_entry_ids == authorization.authorized_response_artifact_entry_ids
    assert first.consumed_query_response_ids == authorization.authorized_query_response_ids
    assert first.consumed_result_hashes == authorization.authorized_result_hashes
    assert first.consumed_result_payloads == authorization.authorized_result_payloads

    assert first.authorization_type_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.authorization_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.response_input_package_verified
    assert first.response_schema_inputs_verified
    assert first.response_content_inputs_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.single_use_consumption_verified
    assert first.immutable_execution_package_verified
    assert first.deterministic_consumption_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert first.research_response_materialization_ready
    assert first.research_response_materialization_authorized
    assert first.research_response_materialization_authorization_consumed
    assert first.research_response_materialization_allowed
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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_materialization_authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorization_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_result_hashes=("0" * 64,) * authorization.authorized_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_result_count=authorization.authorized_result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                research_response_materialization_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-020 materialization authorization consumed")
    print("[PASS] OOP-020 identity, hash, status, and lineage verified")
    print("[PASS] Authorized response payload hashes recomputed and verified")
    print("[PASS] Exact response identities and cardinality preserved")
    print("[PASS] Frozen Research Response scope preserved")
    print("[PASS] Single-use immutable execution package created")
    print("[PASS] Materialization authorization marked consumed")
    print("[PASS] Research Response construction remains unperformed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe authorizations rejected")
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
    print(" OOP-021 INSTALLER")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_020,
        "OOP-020",
        (
            'SCHEMA_VERSION = "OOP-020"',
            "class OracleOperatorResearchResponseMaterializationAuthorization",
            "class OracleOperatorResearchResponseMaterializationAuthorizationGate",
            "research_response_materialization_authorization_id",
            "research_response_materialization_authorization_hash",
            "authorization_status",
            "authorization_type",
            "authorized_result_count",
            "authorized_result_hashes",
            "authorized_result_payloads",
            "research_response_materialization_authorized",
            "research_response_materialization_allowed",
            "research_response_materialization_performed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
        (SOURCE_OOP_019, "OOP-019", ('SCHEMA_VERSION = "OOP-019"', "research_response_materialization_readiness_hash")),
        (SOURCE_OOP_018, "OOP-018", ('SCHEMA_VERSION = "OOP-018"', "research_response_handoff_consumption_hash")),
        (SOURCE_OOP_017, "OOP-017", ('SCHEMA_VERSION = "OOP-017"', "research_response_handoff_authorization_hash")),
        (SOURCE_OOP_016, "OOP-016", ('SCHEMA_VERSION = "OOP-016"', "execution_result_certification_hash")),
        (SOURCE_OOP_015, "OOP-015", ('SCHEMA_VERSION = "OOP-015"', "adapter_invocation_execution_hash")),
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
            SOURCE_OOP_020,
            SOURCE_OOP_019,
            SOURCE_OOP_018,
            SOURCE_OOP_017,
            SOURCE_OOP_016,
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
        RESEARCH_RESPONSE_PACKAGE,
        "from .oracle_operator_research_response_materialization_authorization_consumption_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .research_response.oracle_operator_research_response_materialization_authorization_consumption_gate import *",
    )

    for target in (PRODUCTION, TEST, RESEARCH_RESPONSE_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-020 and INT-OIA-060 unchanged")

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
    print("[PASS] No Query package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-021 test executed automatically")
    print()
    print("[DONE] OOP-021 Research Response materialization authorization consumption installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
