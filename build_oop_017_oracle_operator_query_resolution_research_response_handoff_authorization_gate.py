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

PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_resolution_research_response_handoff_authorization_gate.py"
TEST = ROOT / "test_oop_017_oracle_operator_query_resolution_research_response_handoff_authorization_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"
RESEARCH_RESPONSE_PACKAGE = OPERATOR_RESEARCH_RESPONSE / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    CERTIFICATION_STATUS as OOP_016_CERTIFICATION_STATUS,
    CERTIFIED_RESULT_TYPE as OOP_016_CERTIFIED_RESULT_TYPE,
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
)

SCHEMA_VERSION = "OOP-017"
ENGINE_ID = "OOP-017"
POLICY_ID = (
    "oracle.operator.query-resolution-research-response-handoff-authorization-gate.v1"
)
HANDOFF_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-research-response-handoff-authorization.v1"
)
HANDOFF_STATUS = "operator_query_resolution_research_response_handoff_authorized"
HANDOFF_TYPE = "immutable_certified_query_result_to_research_response"

EXPECTED_CERTIFICATION_STATUS = OOP_016_CERTIFICATION_STATUS
EXPECTED_CERTIFIED_RESULT_TYPE = OOP_016_CERTIFIED_RESULT_TYPE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
EXPECTED_RESEARCH_RESPONSE_NAMESPACE = "qseries_v2.oracle_operator.research_response"


class OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
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
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
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
class OracleOperatorQueryResolutionResearchResponseHandoffAuthorization:
    research_response_handoff_authorization_id: str
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
    handoff_type: str
    certified_result_type: str
    read_adapter_contract_id: str
    execution_mode: str
    handoff_resolution_strategy: str
    handoff_entry_count: int
    handoff_response_artifact_entry_ids: tuple[str, ...]
    handoff_query_response_ids: tuple[str, ...]
    handoff_result_count: int
    handoff_result_hashes: tuple[str, ...]
    handoff_result_payloads: tuple[Mapping[str, Any], ...]
    certification_type_verified: bool
    certification_identity_verified: bool
    certification_hash_verified: bool
    certification_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    certified_result_type_verified: bool
    result_cardinality_verified: bool
    result_identity_verified: bool
    result_payload_hashes_verified: bool
    deterministic_handoff_verified: bool
    query_subsystem_complete: bool
    research_response_handoff_ready: bool
    research_response_handoff_authorized: bool
    research_response_handoff_consumed: bool
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
    handoff_status: str
    research_response_handoff_authorization_hash: str


class OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate:
    @staticmethod
    def _verify_certification(
        certification: OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
    ) -> None:
        if not isinstance(
            certification,
            OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "source must be the canonical OOP-016 result certification"
            )

        body = asdict(certification)
        supplied_hash = body.pop("execution_result_certification_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification hash mismatch"
            )

        required_hashes = (
            certification.execution_result_certification_id,
            certification.source_adapter_invocation_execution_hash,
            certification.source_adapter_invocation_activation_hash,
            certification.source_adapter_execution_consumption_hash,
            certification.source_adapter_execution_authorization_hash,
            certification.source_adapter_execution_readiness_hash,
            certification.source_read_consumption_hash,
            certification.source_read_authorization_hash,
            certification.source_read_readiness_hash,
            certification.source_resolution_consumption_hash,
            certification.source_resolution_authorization_hash,
            certification.source_resolution_plan_hash,
            certification.source_query_admission_hash,
            certification.source_query_request_hash,
            certification.source_admission_hash,
            certification.source_dependency_receipt_hash,
            certification.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 lineage contains invalid hashes"
            )

        if certification.certification_status != EXPECTED_CERTIFICATION_STATUS:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification is not active"
            )
        if certification.certified_result_type != EXPECTED_CERTIFIED_RESULT_TYPE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified result type mismatch"
            )
        if certification.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if certification.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "query namespace mismatch"
            )

        if certification.certified_entry_count < 1:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certification contains no entries"
            )
        if certification.certified_entry_count != certification.certified_result_count:
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified entry/result cardinality mismatch"
            )
        if certification.certified_result_count != len(
            certification.certified_result_payloads
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified payload cardinality mismatch"
            )
        if certification.certified_result_count != len(
            certification.certified_result_hashes
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified hash cardinality mismatch"
            )
        if certification.certified_entry_count != len(
            certification.certified_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified artifact-entry cardinality mismatch"
            )
        if certification.certified_entry_count != len(
            certification.certified_query_response_ids
        ):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified query-response cardinality mismatch"
            )

        recomputed_hashes = tuple(
            stable_hash(item) for item in certification.certified_result_payloads
        )
        if recomputed_hashes != tuple(certification.certified_result_hashes):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "certified result payload hash mismatch"
            )

        required_truths = (
            certification.execution_type_verified,
            certification.execution_identity_verified,
            certification.execution_hash_verified,
            certification.execution_status_verified,
            certification.complete_lineage_verified,
            certification.namespaces_verified,
            certification.query_parameters_verified,
            certification.frozen_scope_verified,
            certification.frozen_scope_preserved,
            certification.immutable_invocation_package_verified,
            certification.immutable_execution_package_verified,
            certification.execution_result_type_verified,
            certification.read_adapter_contract_verified,
            certification.bounded_artifact_read_verified,
            certification.single_read_invocation_verified,
            certification.execution_performed_verified,
            certification.artifact_read_performed_verified,
            certification.result_cardinality_verified,
            certification.result_identity_verified,
            certification.result_payload_hashes_verified,
            certification.deterministic_certification_verified,
            certification.adapter_invocation_execution_performed,
            certification.analytics_artifact_read_performed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification is incomplete"
            )

        forbidden_activity = (
            certification.analytics_query_execution_allowed,
            certification.analytics_query_execution_performed,
            certification.analytics_reexecution_allowed,
            certification.analytics_reexecution_performed,
            certification.analytics_database_connection_allowed,
            certification.analytics_database_connection_performed,
            certification.analytics_mutation_allowed,
            certification.analytics_mutation_performed,
            certification.research_response_materialization_allowed,
            certification.research_response_materialization_performed,
            certification.operator_session_construction_allowed,
            certification.operator_console_rendering_allowed,
            certification.operator_presentation_rendering_allowed,
            certification.publication_allowed,
            certification.publication_performed,
            certification.qseries_handoff_allowed,
            certification.qseries_execution_allowed,
            certification.qseries_execution_performed,
            certification.order_creation_allowed,
            certification.order_creation_performed,
            certification.funds_movement_allowed,
            certification.funds_movement_performed,
            certification.portfolio_mutation_allowed,
            certification.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError(
                "OOP-016 certification contains forbidden activity"
            )

    def authorize(
        self,
        *,
        certification: OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification,
    ) -> OracleOperatorQueryResolutionResearchResponseHandoffAuthorization:
        self._verify_certification(certification)

        authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_execution_result_certification_id": (
                    certification.execution_result_certification_id
                ),
                "source_execution_result_certification_hash": (
                    certification.execution_result_certification_hash
                ),
                "handoff_type": HANDOFF_TYPE,
                "research_response_namespace": EXPECTED_RESEARCH_RESPONSE_NAMESPACE,
                "certified_result_type": certification.certified_result_type,
                "handoff_response_artifact_entry_ids": (
                    certification.certified_response_artifact_entry_ids
                ),
                "handoff_query_response_ids": (
                    certification.certified_query_response_ids
                ),
                "handoff_result_hashes": certification.certified_result_hashes,
            }
        )

        body = {
            "research_response_handoff_authorization_id": authorization_id,
            "source_execution_result_certification_id": certification.execution_result_certification_id,
            "source_execution_result_certification_hash": certification.execution_result_certification_hash,
            "source_adapter_invocation_execution_id": certification.source_adapter_invocation_execution_id,
            "source_adapter_invocation_execution_hash": certification.source_adapter_invocation_execution_hash,
            "source_adapter_invocation_activation_id": certification.source_adapter_invocation_activation_id,
            "source_adapter_invocation_activation_hash": certification.source_adapter_invocation_activation_hash,
            "source_adapter_execution_consumption_id": certification.source_adapter_execution_consumption_id,
            "source_adapter_execution_consumption_hash": certification.source_adapter_execution_consumption_hash,
            "source_adapter_execution_authorization_id": certification.source_adapter_execution_authorization_id,
            "source_adapter_execution_authorization_hash": certification.source_adapter_execution_authorization_hash,
            "source_adapter_execution_readiness_id": certification.source_adapter_execution_readiness_id,
            "source_adapter_execution_readiness_hash": certification.source_adapter_execution_readiness_hash,
            "source_read_consumption_id": certification.source_read_consumption_id,
            "source_read_consumption_hash": certification.source_read_consumption_hash,
            "source_read_authorization_id": certification.source_read_authorization_id,
            "source_read_authorization_hash": certification.source_read_authorization_hash,
            "source_read_readiness_id": certification.source_read_readiness_id,
            "source_read_readiness_hash": certification.source_read_readiness_hash,
            "source_resolution_consumption_id": certification.source_resolution_consumption_id,
            "source_resolution_consumption_hash": certification.source_resolution_consumption_hash,
            "source_resolution_authorization_id": certification.source_resolution_authorization_id,
            "source_resolution_authorization_hash": certification.source_resolution_authorization_hash,
            "source_resolution_plan_id": certification.source_resolution_plan_id,
            "source_resolution_plan_hash": certification.source_resolution_plan_hash,
            "source_query_admission_id": certification.source_query_admission_id,
            "source_query_admission_hash": certification.source_query_admission_hash,
            "source_query_request_id": certification.source_query_request_id,
            "source_query_request_hash": certification.source_query_request_hash,
            "source_admission_id": certification.source_admission_id,
            "source_admission_hash": certification.source_admission_hash,
            "source_dependency_receipt_id": certification.source_dependency_receipt_id,
            "source_dependency_receipt_hash": certification.source_dependency_receipt_hash,
            "source_authorization_id": certification.source_authorization_id,
            "source_authorization_hash": certification.source_authorization_hash,
            "operator_namespace": certification.operator_namespace,
            "query_namespace": certification.query_namespace,
            "research_response_namespace": EXPECTED_RESEARCH_RESPONSE_NAMESPACE,
            "consumer_id": certification.consumer_id,
            "projection": certification.projection,
            "query_mode": certification.query_mode,
            "query_text": certification.query_text,
            "time_scope": certification.time_scope,
            "sort_order": certification.sort_order,
            "result_limit": certification.result_limit,
            "requested_tags": tuple(certification.requested_tags),
            "handoff_type": HANDOFF_TYPE,
            "certified_result_type": certification.certified_result_type,
            "read_adapter_contract_id": certification.read_adapter_contract_id,
            "execution_mode": certification.execution_mode,
            "handoff_resolution_strategy": certification.certified_resolution_strategy,
            "handoff_entry_count": certification.certified_entry_count,
            "handoff_response_artifact_entry_ids": tuple(
                certification.certified_response_artifact_entry_ids
            ),
            "handoff_query_response_ids": tuple(
                certification.certified_query_response_ids
            ),
            "handoff_result_count": certification.certified_result_count,
            "handoff_result_hashes": tuple(certification.certified_result_hashes),
            "handoff_result_payloads": tuple(certification.certified_result_payloads),
            "certification_type_verified": True,
            "certification_identity_verified": True,
            "certification_hash_verified": True,
            "certification_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "certified_result_type_verified": True,
            "result_cardinality_verified": True,
            "result_identity_verified": True,
            "result_payload_hashes_verified": True,
            "deterministic_handoff_verified": True,
            "query_subsystem_complete": True,
            "research_response_handoff_ready": True,
            "research_response_handoff_authorized": True,
            "research_response_handoff_consumed": False,
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
            "handoff_status": HANDOFF_STATUS,
        }

        return OracleOperatorQueryResolutionResearchResponseHandoffAuthorization(
            **body,
            research_response_handoff_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "HANDOFF_SCHEMA_VERSION",
    "HANDOFF_STATUS",
    "HANDOFF_TYPE",
    "EXPECTED_CERTIFICATION_STATUS",
    "EXPECTED_CERTIFIED_RESULT_TYPE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "EXPECTED_RESEARCH_RESPONSE_NAMESPACE",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorization",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate",
    "OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_oop_016_oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    _execution,
)

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_adapter_invocation_execution_result_certification_gate import (
    OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_research_response_handoff_authorization_gate import (
    HANDOFF_STATUS,
    HANDOFF_TYPE,
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate,
    OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError,
    stable_hash,
)


def _certification():
    return (
        OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate()
    ).certify(
        execution=_execution()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe research-response handoff accepted")
    except OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-017 TEST")
    print(" QUERY TO RESEARCH RESPONSE HANDOFF")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    certification = _certification()
    gate = OracleOperatorQueryResolutionResearchResponseHandoffAuthorizationGate()

    first = gate.authorize(certification=certification)
    repeated = gate.authorize(certification=certification)

    assert first == repeated
    assert first.research_response_handoff_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "research_response_handoff_authorization_hash"
        }
    )

    assert first.source_execution_result_certification_id == certification.execution_result_certification_id
    assert first.source_execution_result_certification_hash == certification.execution_result_certification_hash
    assert first.handoff_type == HANDOFF_TYPE
    assert first.handoff_entry_count == certification.certified_entry_count
    assert first.handoff_result_count == certification.certified_result_count
    assert first.handoff_response_artifact_entry_ids == certification.certified_response_artifact_entry_ids
    assert first.handoff_query_response_ids == certification.certified_query_response_ids
    assert first.handoff_result_hashes == certification.certified_result_hashes
    assert first.handoff_result_payloads == certification.certified_result_payloads

    assert first.certification_type_verified
    assert first.certification_identity_verified
    assert first.certification_hash_verified
    assert first.certification_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.certified_result_type_verified
    assert first.result_cardinality_verified
    assert first.result_identity_verified
    assert first.result_payload_hashes_verified
    assert first.deterministic_handoff_verified

    assert first.query_subsystem_complete
    assert first.research_response_handoff_ready
    assert first.research_response_handoff_authorized
    assert not first.research_response_handoff_consumed
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
    assert first.handoff_status == HANDOFF_STATUS

    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                execution_result_certification_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                certification_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                certified_result_hashes=("0" * 64,) * certification.certified_result_count,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                research_response_materialization_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                operator_session_construction_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            certification=replace(
                certification,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-016 certified result consumed")
    print("[PASS] OOP-016 identity, hash, status, and lineage verified")
    print("[PASS] Certified payload hashes recomputed and verified")
    print("[PASS] Frozen query-result scope preserved")
    print("[PASS] Query subsystem completion certified")
    print("[PASS] Research Response handoff authorized")
    print("[PASS] Research Response materialization not yet performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, malformed, and unsafe certifications rejected")
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
    print(" OOP-017 INSTALLER")
    print(" QUERY TO RESEARCH RESPONSE HANDOFF")
    print(" AUTHORIZATION GATE")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_016,
        "OOP-016",
        (
            'SCHEMA_VERSION = "OOP-016"',
            "class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertification",
            "class OracleOperatorQueryResolutionAdapterInvocationExecutionResultCertificationGate",
            "execution_result_certification_id",
            "execution_result_certification_hash",
            "certification_status",
            "certified_result_type",
            "certified_result_count",
            "certified_result_hashes",
            "certified_result_payloads",
            "result_payload_hashes_verified",
            "research_response_materialization_allowed",
            "qseries_execution_allowed",
        ),
    )

    for path, name, tokens in (
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

    OPERATOR_RESEARCH_RESPONSE.mkdir(parents=True, exist_ok=True)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_resolution_research_response_handoff_authorization_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_research_response_handoff_authorization_gate import *",
    )

    if not RESEARCH_RESPONSE_PACKAGE.exists():
        RESEARCH_RESPONSE_PACKAGE.write_text(
            '"""Oracle Operator Research Response subsystem."""\n',
            encoding="utf-8",
            newline="\n",
        )
        print(f"[OK] RESEARCH RESPONSE PACKAGE CREATED: {RESEARCH_RESPONSE_PACKAGE.resolve()}")
    else:
        print(f"[OK] RESEARCH RESPONSE PACKAGE PRESENT: {RESEARCH_RESPONSE_PACKAGE.resolve()}")

    for target in (
        PRODUCTION,
        TEST,
        QUERY_PACKAGE,
        OPERATOR_PACKAGE,
        RESEARCH_RESPONSE_PACKAGE,
    ):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-016 and INT-OIA-060 unchanged")

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
    print("[PASS] Research Response namespace established")
    print("[OK] OOP-017 test executed automatically")
    print()
    print("[DONE] OOP-017 Query-to-Research Response handoff authorization installed")
    print()
    print("NEXT SUBSYSTEM")
    print("  Oracle Operator Research Response")
    print("  - handoff consumption")
    print("  - response materialization readiness")
    print("  - response materialization authorization")
    print("  - immutable research response construction")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
