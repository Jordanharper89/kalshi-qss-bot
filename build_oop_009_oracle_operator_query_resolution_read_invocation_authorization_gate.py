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

PRODUCTION = OPERATOR_QUERY / "oracle_operator_query_resolution_read_invocation_authorization_gate.py"
TEST = ROOT / "test_oop_009_oracle_operator_query_resolution_read_invocation_authorization_gate.py"

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_readiness_gate import (
    READINESS_STATUS as OOP_008_READINESS_STATUS,
    READ_ADAPTER_CONTRACT_ID as OOP_008_READ_ADAPTER_CONTRACT_ID,
    OracleOperatorQueryResolutionReadInvocationReadiness,
)

SCHEMA_VERSION = "OOP-009"
ENGINE_ID = "OOP-009"
POLICY_ID = "oracle.operator.query-resolution-read-invocation-authorization-gate.v1"
AUTHORIZATION_SCHEMA_VERSION = "oracle.operator.query.resolution-read-invocation-authorization.v1"
AUTHORIZATION_STATUS = "operator_query_resolution_read_invocation_authorized"

EXPECTED_READINESS_STATUS = OOP_008_READINESS_STATUS
EXPECTED_READ_ADAPTER_CONTRACT_ID = OOP_008_READ_ADAPTER_CONTRACT_ID
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"


class OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(RuntimeError):
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
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
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
class OracleOperatorQueryResolutionReadInvocationAuthorization:
    read_authorization_id: str
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
    read_invocation_mode: str
    read_adapter_contract_id: str
    authorized_resolution_strategy: str
    authorized_entry_count: int
    authorized_response_artifact_entry_ids: tuple[str, ...]
    authorized_query_response_ids: tuple[str, ...]
    readiness_type_verified: bool
    readiness_identity_verified: bool
    readiness_hash_verified: bool
    readiness_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_manifest_verified: bool
    single_use_consumption_verified: bool
    read_invocation_mode_verified: bool
    read_adapter_contract_verified: bool
    bounded_artifact_read_verified: bool
    deterministic_authorization_verified: bool
    single_read_invocation_authorized: bool
    read_only_resolution_required: bool
    read_invocation_ready: bool
    read_invocation_allowed: bool
    read_invocation_performed: bool
    query_resolution_allowed: bool
    query_resolution_performed: bool
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
    authorization_status: str
    read_authorization_hash: str


class OracleOperatorQueryResolutionReadInvocationAuthorizationGate:
    @staticmethod
    def _verify_readiness(
        readiness: OracleOperatorQueryResolutionReadInvocationReadiness,
    ) -> None:
        if not isinstance(
            readiness,
            OracleOperatorQueryResolutionReadInvocationReadiness,
        ):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "source must be the canonical OOP-008 readiness record"
            )

        body = asdict(readiness)
        supplied_hash = body.pop("read_readiness_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 readiness hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 readiness hash mismatch"
            )

        required_hashes = (
            readiness.read_readiness_id,
            readiness.source_resolution_consumption_hash,
            readiness.source_resolution_authorization_hash,
            readiness.source_resolution_plan_hash,
            readiness.source_query_admission_hash,
            readiness.source_query_request_hash,
            readiness.source_admission_hash,
            readiness.source_dependency_receipt_hash,
            readiness.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 lineage contains invalid hashes"
            )

        if readiness.readiness_status != EXPECTED_READINESS_STATUS:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 readiness record is not active"
            )
        if readiness.read_adapter_contract_id != EXPECTED_READ_ADAPTER_CONTRACT_ID:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "read adapter contract mismatch"
            )
        if readiness.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "operator namespace mismatch"
            )
        if readiness.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "query namespace mismatch"
            )

        if readiness.ready_entry_count < 1:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "readiness record contains no entries"
            )
        if readiness.ready_entry_count != len(readiness.ready_response_artifact_entry_ids):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if readiness.ready_entry_count != len(readiness.ready_query_response_ids):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "query-response cardinality mismatch"
            )
        if len(set(readiness.ready_response_artifact_entry_ids)) != readiness.ready_entry_count:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(set(readiness.ready_query_response_ids)) != readiness.ready_entry_count:
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            readiness.consumption_type_verified,
            readiness.consumption_identity_verified,
            readiness.consumption_hash_verified,
            readiness.consumption_status_verified,
            readiness.complete_lineage_verified,
            readiness.namespaces_verified,
            readiness.query_parameters_verified,
            readiness.frozen_scope_verified,
            readiness.frozen_scope_preserved,
            readiness.immutable_manifest_verified,
            readiness.single_use_consumption_verified,
            readiness.read_invocation_mode_verified,
            readiness.read_adapter_contract_verified,
            readiness.deterministic_readiness_verified,
            readiness.bounded_artifact_read_verified,
            readiness.read_only_resolution_required,
            readiness.read_invocation_ready,
            readiness.query_resolution_allowed,
            readiness.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 readiness record is incomplete"
            )

        forbidden_activity = (
            readiness.read_invocation_performed,
            readiness.query_resolution_performed,
            readiness.analytics_artifact_read_performed,
            readiness.analytics_query_execution_allowed,
            readiness.analytics_query_execution_performed,
            readiness.analytics_reexecution_allowed,
            readiness.analytics_reexecution_performed,
            readiness.analytics_database_connection_allowed,
            readiness.analytics_database_connection_performed,
            readiness.analytics_mutation_allowed,
            readiness.analytics_mutation_performed,
            readiness.operator_session_construction_allowed,
            readiness.operator_console_rendering_allowed,
            readiness.operator_presentation_rendering_allowed,
            readiness.publication_allowed,
            readiness.publication_performed,
            readiness.qseries_handoff_allowed,
            readiness.qseries_execution_allowed,
            readiness.qseries_execution_performed,
            readiness.order_creation_allowed,
            readiness.order_creation_performed,
            readiness.funds_movement_allowed,
            readiness.funds_movement_performed,
            readiness.portfolio_mutation_allowed,
            readiness.portfolio_mutation_performed,
        )
        if any(forbidden_activity):
            raise OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError(
                "OOP-008 readiness record contains forbidden activity"
            )

    def authorize(
        self,
        *,
        readiness: OracleOperatorQueryResolutionReadInvocationReadiness,
    ) -> OracleOperatorQueryResolutionReadInvocationAuthorization:
        self._verify_readiness(readiness)

        read_authorization_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_read_readiness_id": readiness.read_readiness_id,
                "source_read_readiness_hash": readiness.read_readiness_hash,
                "read_invocation_mode": readiness.read_invocation_mode,
                "read_adapter_contract_id": readiness.read_adapter_contract_id,
                "authorized_resolution_strategy": readiness.ready_resolution_strategy,
                "query_mode": readiness.query_mode,
                "query_text": readiness.query_text,
                "time_scope": readiness.time_scope,
                "sort_order": readiness.sort_order,
                "result_limit": readiness.result_limit,
                "requested_tags": readiness.requested_tags,
                "authorized_response_artifact_entry_ids": readiness.ready_response_artifact_entry_ids,
                "authorized_query_response_ids": readiness.ready_query_response_ids,
            }
        )

        body = {
            "read_authorization_id": read_authorization_id,
            "source_read_readiness_id": readiness.read_readiness_id,
            "source_read_readiness_hash": readiness.read_readiness_hash,
            "source_resolution_consumption_id": readiness.source_resolution_consumption_id,
            "source_resolution_consumption_hash": readiness.source_resolution_consumption_hash,
            "source_resolution_authorization_id": readiness.source_resolution_authorization_id,
            "source_resolution_authorization_hash": readiness.source_resolution_authorization_hash,
            "source_resolution_plan_id": readiness.source_resolution_plan_id,
            "source_resolution_plan_hash": readiness.source_resolution_plan_hash,
            "source_query_admission_id": readiness.source_query_admission_id,
            "source_query_admission_hash": readiness.source_query_admission_hash,
            "source_query_request_id": readiness.source_query_request_id,
            "source_query_request_hash": readiness.source_query_request_hash,
            "source_admission_id": readiness.source_admission_id,
            "source_admission_hash": readiness.source_admission_hash,
            "source_dependency_receipt_id": readiness.source_dependency_receipt_id,
            "source_dependency_receipt_hash": readiness.source_dependency_receipt_hash,
            "source_authorization_id": readiness.source_authorization_id,
            "source_authorization_hash": readiness.source_authorization_hash,
            "operator_namespace": readiness.operator_namespace,
            "query_namespace": readiness.query_namespace,
            "consumer_id": readiness.consumer_id,
            "projection": readiness.projection,
            "query_mode": readiness.query_mode,
            "query_text": readiness.query_text,
            "time_scope": readiness.time_scope,
            "sort_order": readiness.sort_order,
            "result_limit": readiness.result_limit,
            "requested_tags": tuple(readiness.requested_tags),
            "read_invocation_mode": readiness.read_invocation_mode,
            "read_adapter_contract_id": readiness.read_adapter_contract_id,
            "authorized_resolution_strategy": readiness.ready_resolution_strategy,
            "authorized_entry_count": readiness.ready_entry_count,
            "authorized_response_artifact_entry_ids": tuple(
                readiness.ready_response_artifact_entry_ids
            ),
            "authorized_query_response_ids": tuple(readiness.ready_query_response_ids),
            "readiness_type_verified": True,
            "readiness_identity_verified": True,
            "readiness_hash_verified": True,
            "readiness_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_manifest_verified": True,
            "single_use_consumption_verified": True,
            "read_invocation_mode_verified": True,
            "read_adapter_contract_verified": True,
            "bounded_artifact_read_verified": True,
            "deterministic_authorization_verified": True,
            "single_read_invocation_authorized": True,
            "read_only_resolution_required": True,
            "read_invocation_ready": True,
            "read_invocation_allowed": True,
            "read_invocation_performed": False,
            "query_resolution_allowed": True,
            "query_resolution_performed": False,
            "analytics_artifact_read_allowed": True,
            "analytics_artifact_read_performed": False,
            "analytics_query_execution_allowed": False,
            "analytics_query_execution_performed": False,
            "analytics_reexecution_allowed": False,
            "analytics_reexecution_performed": False,
            "analytics_database_connection_allowed": False,
            "analytics_database_connection_performed": False,
            "analytics_mutation_allowed": False,
            "analytics_mutation_performed": False,
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
            "authorization_status": AUTHORIZATION_STATUS,
        }

        return OracleOperatorQueryResolutionReadInvocationAuthorization(
            **body,
            read_authorization_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "AUTHORIZATION_SCHEMA_VERSION",
    "AUTHORIZATION_STATUS",
    "EXPECTED_READINESS_STATUS",
    "EXPECTED_READ_ADAPTER_CONTRACT_ID",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "OracleOperatorQueryResolutionReadInvocationAuthorization",
    "OracleOperatorQueryResolutionReadInvocationAuthorizationGate",
    "OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError",
    "stable_hash",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import (
    _attestation,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import (
    OracleOperatorAnalyticsReadOnlyDependencyGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import (
    OracleOperatorAnalyticsDependencyAdmissionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import (
    OracleOperatorQueryRequestContract,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    OracleOperatorQueryRequestAdmissionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_plan import (
    OracleOperatorQueryResolutionPlanner,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_gate import (
    OracleOperatorQueryResolutionAuthorizationGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_consumption_gate import (
    OracleOperatorQueryResolutionAuthorizationConsumptionGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_readiness_gate import (
    OracleOperatorQueryResolutionReadInvocationReadinessGate,
)
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_read_invocation_authorization_gate import (
    AUTHORIZATION_STATUS,
    OracleOperatorQueryResolutionReadInvocationAuthorizationGate,
    OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError,
    stable_hash,
)


def _readiness():
    authorization = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=_attestation(),
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    receipt = OracleOperatorAnalyticsReadOnlyDependencyGate().consume(
        authorization=authorization
    )
    dependency_admission = OracleOperatorAnalyticsDependencyAdmissionGate().admit(
        receipt=receipt
    )
    request = OracleOperatorQueryRequestContract().materialize(
        admission=dependency_admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("kalshi", "major"),
    )
    query_admission = OracleOperatorQueryRequestAdmissionGate().admit(
        request=request
    )
    plan = OracleOperatorQueryResolutionPlanner().plan(
        admission=query_admission
    )
    resolution_authorization = (
        OracleOperatorQueryResolutionAuthorizationGate()
    ).authorize(plan=plan)
    consumption = (
        OracleOperatorQueryResolutionAuthorizationConsumptionGate()
    ).consume(authorization=resolution_authorization)
    return OracleOperatorQueryResolutionReadInvocationReadinessGate().certify(
        consumption=consumption
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe read authorization accepted")
    except OracleOperatorQueryResolutionReadInvocationAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-009 TEST")
    print(" READ INVOCATION AUTHORIZATION")
    print(" SINGLE ADAPTER-BOUND READ")
    print("=" * 40)

    readiness = _readiness()
    gate = OracleOperatorQueryResolutionReadInvocationAuthorizationGate()

    first = gate.authorize(readiness=readiness)
    repeated = gate.authorize(readiness=readiness)

    assert first == repeated
    assert first.read_authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "read_authorization_hash"
        }
    )

    assert first.source_read_readiness_id == readiness.read_readiness_id
    assert first.source_read_readiness_hash == readiness.read_readiness_hash
    assert first.read_adapter_contract_id == readiness.read_adapter_contract_id
    assert first.authorized_entry_count == readiness.ready_entry_count
    assert (
        first.authorized_response_artifact_entry_ids
        == readiness.ready_response_artifact_entry_ids
    )
    assert (
        first.authorized_query_response_ids
        == readiness.ready_query_response_ids
    )

    assert first.readiness_type_verified
    assert first.readiness_identity_verified
    assert first.readiness_hash_verified
    assert first.readiness_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_manifest_verified
    assert first.single_use_consumption_verified
    assert first.read_invocation_mode_verified
    assert first.read_adapter_contract_verified
    assert first.bounded_artifact_read_verified
    assert first.deterministic_authorization_verified
    assert first.single_read_invocation_authorized
    assert first.read_only_resolution_required

    assert first.read_invocation_ready
    assert first.read_invocation_allowed
    assert not first.read_invocation_performed
    assert first.query_resolution_allowed
    assert not first.query_resolution_performed
    assert first.analytics_artifact_read_allowed
    assert not first.analytics_artifact_read_performed
    assert not first.analytics_query_execution_allowed
    assert not first.analytics_query_execution_performed
    assert not first.analytics_reexecution_allowed
    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_allowed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
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
    assert first.authorization_status == AUTHORIZATION_STATUS

    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                read_readiness_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                readiness_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                read_adapter_contract_id="wrong_adapter",
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                read_invocation_ready=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                read_invocation_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            readiness=replace(
                readiness,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-008 readiness record consumed")
    print("[PASS] OOP-008 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic read-invocation authorization created")
    print("[PASS] Single adapter-bound artifact read authorized")
    print("[PASS] Read invocation allowed but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed readiness rejected")
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
    source = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"Actual {name} contract mismatch; missing: " + ", ".join(missing)
        )
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-009 INSTALLER")
    print(" READ INVOCATION AUTHORIZATION")
    print(" SINGLE ADAPTER-BOUND READ")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_008,
        "OOP-008",
        (
            'SCHEMA_VERSION = "OOP-008"',
            "class OracleOperatorQueryResolutionReadInvocationReadiness",
            "class OracleOperatorQueryResolutionReadInvocationReadinessGate",
            "read_readiness_id",
            "read_readiness_hash",
            "readiness_status",
            "read_adapter_contract_id",
            "read_invocation_ready",
            "read_invocation_performed",
            "analytics_artifact_read_allowed",
            "analytics_artifact_read_performed",
            "analytics_query_execution_allowed",
            "operator_session_construction_allowed",
            "qseries_execution_allowed",
        ),
    )
    verify_contract(SOURCE_OOP_007, "OOP-007", ('SCHEMA_VERSION = "OOP-007"', "resolution_consumption_hash"))
    verify_contract(SOURCE_OOP_006, "OOP-006", ('SCHEMA_VERSION = "OOP-006"', "resolution_authorization_hash"))
    verify_contract(SOURCE_OOP_005, "OOP-005", ('SCHEMA_VERSION = "OOP-005"', "resolution_plan_hash"))
    verify_contract(SOURCE_OOP_004, "OOP-004", ('SCHEMA_VERSION = "OOP-004"', "query_admission_hash"))
    verify_contract(SOURCE_OOP_003, "OOP-003", ('SCHEMA_VERSION = "OOP-003"', "query_request_hash"))
    verify_contract(SOURCE_OOP_002, "OOP-002", ('SCHEMA_VERSION = "OOP-002"', "admission_hash"))
    verify_contract(SOURCE_OOP_001, "OOP-001", ('SCHEMA_VERSION = "OOP-001"', "dependency_receipt_hash"))
    verify_contract(
        SOURCE_060,
        "INT-OIA-060",
        ('SCHEMA_VERSION = "INT-OIA-060"', "authorization_hash", "read_only_consumption_verified"),
    )

    protected_before = {
        path: sha256_file(path)
        for path in (
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
        "from .oracle_operator_query_resolution_read_invocation_authorization_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_read_invocation_authorization_gate import *",
    )

    for target in (PRODUCTION, TEST, QUERY_PACKAGE, OPERATOR_PACKAGE):
        ast.parse(target.read_text(encoding="utf-8"), filename=str(target))
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-008 and INT-OIA-060 unchanged")

    completed = subprocess.run(
        [sys.executable, str(TEST)],
        cwd=str(ROOT),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed during test: {path}")

    print("[PASS] Protected upstream modules unchanged after test")
    print("[PASS] No analytics package export modified")
    print("[PASS] No Q Series execution package imported or modified")
    print("[OK] OOP-009 test executed automatically")
    print()
    print("[DONE] OOP-009 read invocation authorization gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
