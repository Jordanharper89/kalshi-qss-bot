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

PRODUCTION = OPERATOR_RESEARCH_RESPONSE / "oracle_operator_research_response_materialization_readiness_gate.py"
TEST = ROOT / "test_oop_019_oracle_operator_research_response_materialization_readiness_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
RESEARCH_RESPONSE_PACKAGE = OPERATOR_RESEARCH_RESPONSE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_handoff_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_018_CONSUMPTION_STATUS,
    RESPONSE_INPUT_PACKAGE_TYPE as OOP_018_RESPONSE_INPUT_PACKAGE_TYPE,
    OracleOperatorResearchResponseHandoffAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-019"
ENGINE_ID = "OOP-019"
POLICY_ID = "oracle.operator.research-response-materialization-readiness-gate.v1"
READINESS_SCHEMA_VERSION = (
    "oracle.operator.research-response.materialization-readiness.v1"
)
READINESS_STATUS = "operator_research_response_materialization_ready"
READINESS_TYPE = "immutable_research_response_materialization_readiness"

EXPECTED_CONSUMPTION_STATUS = OOP_018_CONSUMPTION_STATUS
EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE = OOP_018_RESPONSE_INPUT_PACKAGE_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorResearchResponseMaterializationReadinessInvariantError(
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
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
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
class OracleOperatorResearchResponseMaterializationReadiness:
    research_response_materialization_readiness_id: str
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
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    response_resolution_strategy: str
    response_entry_count: int
    response_artifact_entry_ids: tuple[str, ...]
    response_query_response_ids: tuple[str, ...]
    response_result_count: int
    response_result_hashes: tuple[str, ...]
    response_result_payloads: tuple[Mapping[str, Any], ...]
    consumption_type_verified: bool
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    response_input_package_verified: bool
    response_schema_inputs_verified: bool
    response_content_inputs_verified: bool
    deterministic_readiness_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
    research_response_materialization_ready: bool
    research_response_materialization_authorized: bool
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
    readiness_status: str
    research_response_materialization_readiness_hash: str


class OracleOperatorResearchResponseMaterializationReadinessGate:
    @staticmethod
    def _verify_consumption(
        consumption: OracleOperatorResearchResponseHandoffAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorResearchResponseHandoffAuthorizationConsumption,
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "source must be the canonical OOP-018 handoff consumption"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("research_response_handoff_consumption_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption hash mismatch"
            )

        required_hashes = (
            consumption.research_response_handoff_consumption_id,
            consumption.source_research_response_handoff_authorization_hash,
            consumption.source_execution_result_certification_hash,
            consumption.source_adapter_invocation_execution_hash,
            consumption.source_adapter_invocation_activation_hash,
            consumption.source_adapter_execution_consumption_hash,
            consumption.source_adapter_execution_authorization_hash,
            consumption.source_adapter_execution_readiness_hash,
            consumption.source_read_consumption_hash,
            consumption.source_read_authorization_hash,
            consumption.source_read_readiness_hash,
            consumption.source_resolution_consumption_hash,
            consumption.source_resolution_authorization_hash,
            consumption.source_resolution_plan_hash,
            consumption.source_query_admission_hash,
            consumption.source_query_request_hash,
            consumption.source_admission_hash,
            consumption.source_dependency_receipt_hash,
            consumption.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 lineage contains invalid hashes"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 handoff consumption is not complete"
            )
        if (
            consumption.response_input_package_type
            != EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "response input package type mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "query namespace mismatch"
            )
        if (
            consumption.research_response_namespace
            != EXPECTED_RESEARCH_RESPONSE_NAMESPACE
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "research response namespace mismatch"
            )

        if consumption.consumed_entry_count < 1:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumption contains no entries"
            )
        if consumption.consumed_entry_count != consumption.consumed_result_count:
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed entry/result cardinality mismatch"
            )
        if consumption.consumed_result_count != len(
            consumption.consumed_result_payloads
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed payload cardinality mismatch"
            )
        if consumption.consumed_result_count != len(
            consumption.consumed_result_hashes
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed hash cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed query-response cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in consumption.consumed_result_payloads
        )
        if recomputed_hashes != tuple(consumption.consumed_result_hashes):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "consumed payload hash mismatch"
            )

        for index, payload in enumerate(consumption.consumed_result_payloads):
            if not isinstance(payload, Mapping):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed result payload must be a mapping"
                )
            if (
                payload.get("response_artifact_entry_id")
                != consumption.consumed_response_artifact_entry_ids[index]
            ):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed artifact-entry identity mismatch"
                )
            if (
                payload.get("query_response_id")
                != consumption.consumed_query_response_ids[index]
            ):
                raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                    "consumed query-response identity mismatch"
                )

        required_truths = (
            consumption.handoff_type_verified,
            consumption.handoff_identity_verified,
            consumption.handoff_hash_verified,
            consumption.handoff_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.result_cardinality_verified,
            consumption.result_identity_verified,
            consumption.result_payload_hashes_verified,
            consumption.single_use_consumption_verified,
            consumption.deterministic_consumption_verified,
            consumption.query_subsystem_complete,
            consumption.research_response_handoff_ready,
            consumption.research_response_handoff_authorized,
            consumption.research_response_handoff_consumed,
        )
        if not all(required_truths):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption is incomplete"
            )

        forbidden_activity = (
            consumption.research_response_materialization_ready,
            consumption.research_response_materialization_allowed,
            consumption.research_response_materialization_performed,
            consumption.operator_session_construction_allowed,
            consumption.operator_console_rendering_allowed,
            consumption.operator_presentation_rendering_allowed,
            consumption.publication_allowed,
            consumption.publication_performed,
            consumption.qseries_handoff_allowed,
            consumption.qseries_execution_allowed,
            consumption.qseries_execution_performed,
            consumption.order_creation_allowed,
            consumption.order_creation_performed,
            consumption.funds_movement_allowed,
            consumption.funds_movement_performed,
            consumption.portfolio_mutation_allowed,
            consumption.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorResearchResponseMaterializationReadinessInvariantError(
                "OOP-018 consumption contains forbidden downstream activity"
            )

    def evaluate(
        self,
        *,
        consumption: OracleOperatorResearchResponseHandoffAuthorizationConsumption,
    ) -> OracleOperatorResearchResponseMaterializationReadiness:
        self._verify_consumption(consumption)

        readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_research_response_handoff_consumption_id": (
                    consumption.research_response_handoff_consumption_id
                ),
                "source_research_response_handoff_consumption_hash": (
                    consumption.research_response_handoff_consumption_hash
                ),
                "readiness_type": READINESS_TYPE,
                "response_input_package_type": consumption.response_input_package_type,
                "response_artifact_entry_ids": (
                    consumption.consumed_response_artifact_entry_ids
                ),
                "response_query_response_ids": (
                    consumption.consumed_query_response_ids
                ),
                "response_result_hashes": consumption.consumed_result_hashes,
            }
        )

        body = {
            "research_response_materialization_readiness_id": readiness_id,
            "source_research_response_handoff_consumption_id": consumption.research_response_handoff_consumption_id,
            "source_research_response_handoff_consumption_hash": consumption.research_response_handoff_consumption_hash,
            "source_research_response_handoff_authorization_id": consumption.source_research_response_handoff_authorization_id,
            "source_research_response_handoff_authorization_hash": consumption.source_research_response_handoff_authorization_hash,
            "source_execution_result_certification_id": consumption.source_execution_result_certification_id,
            "source_execution_result_certification_hash": consumption.source_execution_result_certification_hash,
            "source_adapter_invocation_execution_id": consumption.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": consumption.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": consumption.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": consumption.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": consumption.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": consumption.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": consumption.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": consumption.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": consumption.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": consumption.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": consumption.source_read_consumption_id,
            "source_read_consumption_hash": consumption.source_read_consumption_hash,
            "source_read_authorization_id": consumption.source_read_authorization_id,
            "source_read_authorization_hash": consumption.source_read_authorization_hash,
            "source_read_readiness_id": consumption.source_read_readiness_id,
            "source_read_readiness_hash": consumption.source_read_readiness_hash,
            "source_resolution_consumption_id": consumption.source_resolution_consumption_id,
            "source_resolution_consumption_hash": consumption.source_resolution_consumption_hash,
            "source_resolution_authorization_id": consumption.source_resolution_authorization_id,
            "source_resolution_authorization_hash": consumption.source_resolution_authorization_hash,
            "source_resolution_plan_id": consumption.source_resolution_plan_id,
            "source_resolution_plan_hash": consumption.source_resolution_plan_hash,
            "source_query_admission_id": consumption.source_query_admission_id,
            "source_query_admission_hash": consumption.source_query_admission_hash,
            "source_query_request_id": consumption.source_query_request_id,
            "source_query_request_hash": consumption.source_query_request_hash,
            "source_admission_id": consumption.source_admission_id,
            "source_admission_hash": consumption.source_admission_hash,
            "source_dependency_receipt_id": consumption.source_dependency_receipt_id,
            "source_dependency_receipt_hash": consumption.source_dependency_receipt_hash,
            "source_authorization_id": consumption.source_authorization_id,
            "source_authorization_hash": consumption.source_authorization_hash,
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "research_response_namespace": consumption.research_response_namespace,
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "response_input_package_type": consumption.response_input_package_type,
            "readiness_type": READINESS_TYPE,
            "certified_result_type": consumption.certified_result_type,
            "read_adapter_contract_id": consumption.read_adapter_contract_id,
            "execution_mode": consumption.execution_mode,
            "response_resolution_strategy": consumption.consumed_resolution_strategy,
            "response_entry_count": consumption.consumed_entry_count,
            "response_artifact_entry_ids": tuple(
                consumption.consumed_response_artifact_entry_ids
            ),
            "response_query_response_ids": tuple(
                consumption.consumed_query_response_ids
            ),
            "response_result_count": consumption.consumed_result_count,
            "response_result_hashes": tuple(consumption.consumed_result_hashes),
            "response_result_payloads": tuple(consumption.consumed_result_payloads),
            "consumption_type_verified": True,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "response_input_package_verified": True,
            "response_schema_inputs_verified": True,
            "response_content_inputs_verified": True,
            "deterministic_readiness_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": True,
            "research_response_materialization_ready": True,
            "research_response_materialization_authorized": False,
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
            "readiness_status": READINESS_STATUS,
        }

        return OracleOperatorResearchResponseMaterializationReadiness(
            **body,
            research_response_materialization_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_SCHEMA_VERSION",
    "READINESS_STATUS",
    "READINESS_TYPE",
    "EXPECTED_CONSUMPTION_STATUS",
    "EXPECTED_RESPONSE_INPUT_PACKAGE_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorResearchResponseMaterializationReadiness",
    "OracleOperatorResearchResponseMaterializationReadinessGate",
    "OracleOperatorResearchResponseMaterializationReadinessInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_018_oracle_operator_research_response_handoff_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_handoff_authorization_consumption_gate import (
    OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.research_response.oracle_operator_research_response_materialization_readiness_gate import (
    READINESS_STATUS,
    READINESS_TYPE,
    OracleOperatorResearchResponseMaterializationReadinessGate,
    OracleOperatorResearchResponseMaterializationReadinessInvariantError,
    stable_hash,
)


def _consumption():
    return OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate().consume(
        authorization=_authorization()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe materialization readiness accepted")
    except OracleOperatorResearchResponseMaterializationReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-019 TEST")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" READINESS GATE")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorResearchResponseMaterializationReadinessGate()

    first = gate.evaluate(consumption=consumption)
    repeated = gate.evaluate(consumption=consumption)

    assert first == repeated
    assert first.research_response_materialization_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_materialization_readiness_hash"
        }
    )

    assert first.source_research_response_handoff_consumption_id == consumption.research_response_handoff_consumption_id
    assert first.source_research_response_handoff_consumption_hash == consumption.research_response_handoff_consumption_hash
    assert first.readiness_type == READINESS_TYPE
    assert first.response_entry_count == consumption.consumed_entry_count
    assert first.response_result_count == consumption.consumed_result_count
    assert first.response_artifact_entry_ids == consumption.consumed_response_artifact_entry_ids
    assert first.response_query_response_ids == consumption.consumed_query_response_ids
    assert first.response_result_hashes == consumption.consumed_result_hashes
    assert first.response_result_payloads == consumption.consumed_result_payloads

    assert first.consumption_type_verified
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.response_input_package_verified
    assert first.response_schema_inputs_verified
    assert first.response_content_inputs_verified
    assert first.deterministic_readiness_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert first.research_response_handoff_consumed
    assert first.research_response_materialization_ready
    assert not first.research_response_materialization_authorized
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
    assert first.readiness_status == READINESS_STATUS

    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                research_response_handoff_consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumption_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumed_result_hashes=("0" * 64,) * consumption.consumed_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                consumed_result_count=consumption.consumed_result_count + 1,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                research_response_materialization_ready=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.evaluate(
            consumption=replace(
                consumption,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-018 response input package consumed")
    print("[PASS] OOP-018 identity, hash, status, and lineage verified")
    print("[PASS] Response input payload hashes recomputed and verified")
    print("[PASS] Exact response identities and cardinality verified")
    print("[PASS] Frozen Research Response scope preserved")
    print("[PASS] Response schema and content inputs certified ready")
    print("[PASS] Research Response materialization marked ready")
    print("[PASS] Materialization remains unauthorized and unperformed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe readiness inputs rejected")
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
    print(" OOP-019 INSTALLER")
    print(" RESEARCH RESPONSE MATERIALIZATION")
    print(" READINESS GATE")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_018,
        "OOP-018",
        (
            'SCHEMA_VERSION = "OOP-018"',
            "class OracleOperatorResearchResponseHandoffAuthorizationConsumption",
            "class OracleOperatorResearchResponseHandoffAuthorizationConsumptionGate",
            "research_response_handoff_consumption_id",
            "research_response_handoff_consumption_hash",
            "consumption_status",
            "response_input_package_type",
            "consumed_result_count",
            "consumed_result_hashes",
            "consumed_result_payloads",
            "research_response_handoff_consumed",
            "research_response_materialization_ready",
            "research_response_materialization_allowed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
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
        "from .oracle_operator_research_response_materialization_readiness_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .research_response.oracle_operator_research_response_materialization_readiness_gate import *",
    )

    for target in (PRODUCTION, TEST, RESEARCH_RESPONSE_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-018 and INT-OIA-060 unchanged")

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
    print("[OK] OOP-019 test executed automatically")
    print()
    print("[DONE] OOP-019 Research Response materialization readiness installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
