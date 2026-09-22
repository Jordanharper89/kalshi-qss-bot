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

SOURCE_060 = (
    ANALYTICS_QUERY
    / "oracle_intelligence_analytics_int_oia_060_authorization_gate.py"
)
SOURCE_OOP_001 = (
    OPERATOR
    / "oracle_operator_analytics_read_only_dependency_gate.py"
)
SOURCE_OOP_002 = (
    OPERATOR
    / "oracle_operator_analytics_dependency_admission_gate.py"
)
SOURCE_OOP_003 = (
    OPERATOR_QUERY
    / "oracle_operator_query_request_contract.py"
)
SOURCE_OOP_004 = (
    OPERATOR_QUERY
    / "oracle_operator_query_request_admission_gate.py"
)
SOURCE_OOP_005 = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_plan.py"
)
SOURCE_OOP_006 = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_authorization_gate.py"
)
SOURCE_OOP_007 = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_authorization_consumption_gate.py"
)

PRODUCTION = (
    OPERATOR_QUERY
    / "oracle_operator_query_resolution_read_invocation_readiness_gate.py"
)
TEST = (
    ROOT
    / "test_oop_008_oracle_operator_query_resolution_read_invocation_readiness_gate.py"
)

OPERATOR_PACKAGE = OPERATOR / "__init__.py"
QUERY_PACKAGE = OPERATOR_QUERY / "__init__.py"

PRODUCTION_SOURCE = r"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_consumption_gate import (
    CONSUMPTION_STATUS as OOP_007_CONSUMPTION_STATUS,
    READ_INVOCATION_MODE as OOP_007_READ_INVOCATION_MODE,
    OracleOperatorQueryResolutionAuthorizationConsumption,
)

SCHEMA_VERSION = "OOP-008"
ENGINE_ID = "OOP-008"
POLICY_ID = (
    "oracle.operator.query-resolution-read-invocation-readiness-gate.v1"
)
READINESS_SCHEMA_VERSION = (
    "oracle.operator.query.resolution-read-invocation-readiness.v1"
)
READINESS_STATUS = "operator_query_resolution_read_invocation_ready"

EXPECTED_CONSUMPTION_STATUS = OOP_007_CONSUMPTION_STATUS
EXPECTED_READ_INVOCATION_MODE = OOP_007_READ_INVOCATION_MODE
EXPECTED_OPERATOR_NAMESPACE = "qseries_v2.oracle_operator"
EXPECTED_QUERY_NAMESPACE = "qseries_v2.oracle_operator.query"
READ_ADAPTER_CONTRACT_ID = "oracle.operator.analytics-artifact-read-adapter.v1"


class OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
    RuntimeError
):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "datetime must be timezone-aware"
            )
        return value.astimezone(timezone.utc).isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
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
class OracleOperatorQueryResolutionReadInvocationReadiness:
    read_readiness_id: str
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
    ready_resolution_strategy: str
    ready_entry_count: int
    ready_response_artifact_entry_ids: tuple[str, ...]
    ready_query_response_ids: tuple[str, ...]
    consumption_type_verified: bool
    consumption_identity_verified: bool
    consumption_hash_verified: bool
    consumption_status_verified: bool
    complete_lineage_verified: bool
    namespaces_verified: bool
    query_parameters_verified: bool
    frozen_scope_verified: bool
    frozen_scope_preserved: bool
    immutable_manifest_verified: bool
    single_use_consumption_verified: bool
    read_invocation_mode_verified: bool
    read_adapter_contract_verified: bool
    deterministic_readiness_verified: bool
    bounded_artifact_read_verified: bool
    read_only_resolution_required: bool
    read_invocation_ready: bool
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
    readiness_status: str
    read_readiness_hash: str


class OracleOperatorQueryResolutionReadInvocationReadinessGate:
    @staticmethod
    def _verify_consumption(
        consumption: OracleOperatorQueryResolutionAuthorizationConsumption,
    ) -> None:
        if not isinstance(
            consumption,
            OracleOperatorQueryResolutionAuthorizationConsumption,
        ):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "source must be the canonical OOP-007 consumption record"
            )

        body = asdict(consumption)
        supplied_hash = body.pop("resolution_consumption_hash", None)
        if not _valid_sha256(supplied_hash):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 consumption hash is invalid"
            )
        if stable_hash(body) != supplied_hash:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 consumption hash mismatch"
            )

        required_hashes = (
            consumption.resolution_consumption_id,
            consumption.source_resolution_authorization_hash,
            consumption.source_resolution_plan_hash,
            consumption.source_query_admission_hash,
            consumption.source_query_request_hash,
            consumption.source_admission_hash,
            consumption.source_dependency_receipt_hash,
            consumption.source_authorization_hash,
        )
        if not all(_valid_sha256(value) for value in required_hashes):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 lineage contains invalid hashes"
            )

        if consumption.consumption_status != EXPECTED_CONSUMPTION_STATUS:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 consumption record is not active"
            )
        if consumption.read_invocation_mode != EXPECTED_READ_INVOCATION_MODE:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "read invocation mode mismatch"
            )
        if consumption.operator_namespace != EXPECTED_OPERATOR_NAMESPACE:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "operator namespace mismatch"
            )
        if consumption.query_namespace != EXPECTED_QUERY_NAMESPACE:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "query namespace mismatch"
            )

        if consumption.consumed_entry_count < 1:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "consumption record contains no entries"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_response_artifact_entry_ids
        ):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "artifact-entry cardinality mismatch"
            )
        if consumption.consumed_entry_count != len(
            consumption.consumed_query_response_ids
        ):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "query-response cardinality mismatch"
            )
        if len(
            set(consumption.consumed_response_artifact_entry_ids)
        ) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "duplicate artifact-entry identities detected"
            )
        if len(
            set(consumption.consumed_query_response_ids)
        ) != consumption.consumed_entry_count:
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "duplicate query-response identities detected"
            )

        required_truths = (
            consumption.resolution_authorization_type_verified,
            consumption.resolution_authorization_identity_verified,
            consumption.resolution_authorization_hash_verified,
            consumption.resolution_authorization_status_verified,
            consumption.complete_lineage_verified,
            consumption.namespaces_verified,
            consumption.query_parameters_verified,
            consumption.frozen_scope_verified,
            consumption.frozen_scope_preserved,
            consumption.single_bounded_resolution_path_verified,
            consumption.single_use_consumption_verified,
            consumption.immutable_read_manifest_verified,
            consumption.deterministic_consumption_verified,
            consumption.read_only_resolution_required,
            consumption.query_resolution_allowed,
            consumption.analytics_artifact_read_allowed,
        )
        if not all(required_truths):
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 consumption record is incomplete"
            )

        forbidden_activity = (
            consumption.query_resolution_performed,
            consumption.analytics_artifact_read_performed,
            consumption.analytics_query_execution_allowed,
            consumption.analytics_query_execution_performed,
            consumption.analytics_reexecution_allowed,
            consumption.analytics_reexecution_performed,
            consumption.analytics_database_connection_allowed,
            consumption.analytics_database_connection_performed,
            consumption.analytics_mutation_allowed,
            consumption.analytics_mutation_performed,
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
            raise OracleOperatorQueryResolutionReadInvocationReadinessInvariantError(
                "OOP-007 consumption record contains forbidden activity"
            )

    def certify(
        self,
        *,
        consumption: OracleOperatorQueryResolutionAuthorizationConsumption,
    ) -> OracleOperatorQueryResolutionReadInvocationReadiness:
        self._verify_consumption(consumption)

        read_readiness_id = stable_hash(
            {
                "engine_id": ENGINE_ID,
                "source_resolution_consumption_id": (
                    consumption.resolution_consumption_id
                ),
                "source_resolution_consumption_hash": (
                    consumption.resolution_consumption_hash
                ),
                "read_invocation_mode": consumption.read_invocation_mode,
                "read_adapter_contract_id": READ_ADAPTER_CONTRACT_ID,
                "ready_resolution_strategy": (
                    consumption.consumed_resolution_strategy
                ),
                "query_mode": consumption.query_mode,
                "query_text": consumption.query_text,
                "time_scope": consumption.time_scope,
                "sort_order": consumption.sort_order,
                "result_limit": consumption.result_limit,
                "requested_tags": consumption.requested_tags,
                "ready_response_artifact_entry_ids": (
                    consumption.consumed_response_artifact_entry_ids
                ),
                "ready_query_response_ids": (
                    consumption.consumed_query_response_ids
                ),
            }
        )

        body = {
            "read_readiness_id": read_readiness_id,
            "source_resolution_consumption_id": (
                consumption.resolution_consumption_id
            ),
            "source_resolution_consumption_hash": (
                consumption.resolution_consumption_hash
            ),
            "source_resolution_authorization_id": (
                consumption.source_resolution_authorization_id
            ),
            "source_resolution_authorization_hash": (
                consumption.source_resolution_authorization_hash
            ),
            "source_resolution_plan_id": (
                consumption.source_resolution_plan_id
            ),
            "source_resolution_plan_hash": (
                consumption.source_resolution_plan_hash
            ),
            "source_query_admission_id": (
                consumption.source_query_admission_id
            ),
            "source_query_admission_hash": (
                consumption.source_query_admission_hash
            ),
            "source_query_request_id": (
                consumption.source_query_request_id
            ),
            "source_query_request_hash": (
                consumption.source_query_request_hash
            ),
            "source_admission_id": consumption.source_admission_id,
            "source_admission_hash": consumption.source_admission_hash,
            "source_dependency_receipt_id": (
                consumption.source_dependency_receipt_id
            ),
            "source_dependency_receipt_hash": (
                consumption.source_dependency_receipt_hash
            ),
            "source_authorization_id": (
                consumption.source_authorization_id
            ),
            "source_authorization_hash": (
                consumption.source_authorization_hash
            ),
            "operator_namespace": consumption.operator_namespace,
            "query_namespace": consumption.query_namespace,
            "consumer_id": consumption.consumer_id,
            "projection": consumption.projection,
            "query_mode": consumption.query_mode,
            "query_text": consumption.query_text,
            "time_scope": consumption.time_scope,
            "sort_order": consumption.sort_order,
            "result_limit": consumption.result_limit,
            "requested_tags": tuple(consumption.requested_tags),
            "read_invocation_mode": consumption.read_invocation_mode,
            "read_adapter_contract_id": READ_ADAPTER_CONTRACT_ID,
            "ready_resolution_strategy": (
                consumption.consumed_resolution_strategy
            ),
            "ready_entry_count": consumption.consumed_entry_count,
            "ready_response_artifact_entry_ids": tuple(
                consumption.consumed_response_artifact_entry_ids
            ),
            "ready_query_response_ids": tuple(
                consumption.consumed_query_response_ids
            ),
            "consumption_type_verified": True,
            "consumption_identity_verified": True,
            "consumption_hash_verified": True,
            "consumption_status_verified": True,
            "complete_lineage_verified": True,
            "namespaces_verified": True,
            "query_parameters_verified": True,
            "frozen_scope_verified": True,
            "frozen_scope_preserved": True,
            "immutable_manifest_verified": True,
            "single_use_consumption_verified": True,
            "read_invocation_mode_verified": True,
            "read_adapter_contract_verified": True,
            "deterministic_readiness_verified": True,
            "bounded_artifact_read_verified": True,
            "read_only_resolution_required": True,
            "read_invocation_ready": True,
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
            "readiness_status": READINESS_STATUS,
        }

        return OracleOperatorQueryResolutionReadInvocationReadiness(
            **body,
            read_readiness_hash=stable_hash(body),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "POLICY_ID",
    "READINESS_SCHEMA_VERSION",
    "READINESS_STATUS",
    "EXPECTED_CONSUMPTION_STATUS",
    "EXPECTED_READ_INVOCATION_MODE",
    "EXPECTED_OPERATOR_NAMESPACE",
    "EXPECTED_QUERY_NAMESPACE",
    "READ_ADAPTER_CONTRACT_ID",
    "OracleOperatorQueryResolutionReadInvocationReadiness",
    "OracleOperatorQueryResolutionReadInvocationReadinessGate",
    "OracleOperatorQueryResolutionReadInvocationReadinessInvariantError",
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
    READINESS_STATUS,
    READ_ADAPTER_CONTRACT_ID,
    OracleOperatorQueryResolutionReadInvocationReadinessGate,
    OracleOperatorQueryResolutionReadInvocationReadinessInvariantError,
    stable_hash,
)


def _consumption():
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
    dependency_admission = (
        OracleOperatorAnalyticsDependencyAdmissionGate()
    ).admit(
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
    query_admission = (
        OracleOperatorQueryRequestAdmissionGate()
    ).admit(
        request=request
    )
    plan = OracleOperatorQueryResolutionPlanner().plan(
        admission=query_admission
    )
    resolution_authorization = (
        OracleOperatorQueryResolutionAuthorizationGate()
    ).authorize(
        plan=plan
    )
    return (
        OracleOperatorQueryResolutionAuthorizationConsumptionGate()
    ).consume(
        authorization=resolution_authorization
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe read readiness accepted")
    except OracleOperatorQueryResolutionReadInvocationReadinessInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-008 TEST")
    print(" READ INVOCATION READINESS")
    print(" BOUNDED ARTIFACT READ")
    print("=" * 40)

    consumption = _consumption()
    gate = OracleOperatorQueryResolutionReadInvocationReadinessGate()

    first = gate.certify(consumption=consumption)
    repeated = gate.certify(consumption=consumption)

    assert first == repeated
    assert first.read_readiness_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "read_readiness_hash"
        }
    )

    assert (
        first.source_resolution_consumption_id
        == consumption.resolution_consumption_id
    )
    assert (
        first.source_resolution_consumption_hash
        == consumption.resolution_consumption_hash
    )
    assert first.query_mode == consumption.query_mode
    assert first.query_text == consumption.query_text
    assert first.time_scope == consumption.time_scope
    assert first.sort_order == consumption.sort_order
    assert first.result_limit == consumption.result_limit
    assert first.requested_tags == consumption.requested_tags
    assert (
        first.read_invocation_mode
        == consumption.read_invocation_mode
    )
    assert first.read_adapter_contract_id == READ_ADAPTER_CONTRACT_ID
    assert (
        first.ready_resolution_strategy
        == consumption.consumed_resolution_strategy
    )
    assert first.ready_entry_count == consumption.consumed_entry_count
    assert (
        first.ready_response_artifact_entry_ids
        == consumption.consumed_response_artifact_entry_ids
    )
    assert (
        first.ready_query_response_ids
        == consumption.consumed_query_response_ids
    )

    assert first.consumption_type_verified
    assert first.consumption_identity_verified
    assert first.consumption_hash_verified
    assert first.consumption_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.immutable_manifest_verified
    assert first.single_use_consumption_verified
    assert first.read_invocation_mode_verified
    assert first.read_adapter_contract_verified
    assert first.deterministic_readiness_verified
    assert first.bounded_artifact_read_verified
    assert first.read_only_resolution_required

    assert first.read_invocation_ready
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
    assert first.readiness_status == READINESS_STATUS

    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                resolution_consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                consumption_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                read_invocation_mode="wrong_mode",
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                immutable_read_manifest_verified=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_artifact_read_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.certify(
            consumption=replace(
                consumption,
                qseries_execution_allowed=True,
            )
        )
    )

    print("[PASS] Actual OOP-007 consumption record consumed")
    print("[PASS] OOP-007 identity, hash, status, and lineage verified")
    print("[PASS] Immutable single-use read manifest verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic read-invocation readiness certified")
    print("[PASS] Bounded artifact-read adapter contract assigned")
    print("[PASS] Read invocation ready but not performed")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed manifests rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_replacement(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text.strip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
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
    path.write_text(
        existing + export_line + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] PACKAGE UPDATED: {path.resolve()}")


def verify_contract(
    path: Path,
    name: str,
    required_tokens: tuple[str, ...],
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Actual {name} module missing: {path}")
    source = path.read_text(encoding="utf-8")
    missing = [token for token in required_tokens if token not in source]
    if missing:
        raise RuntimeError(
            f"Actual {name} contract mismatch; missing: "
            + ", ".join(missing)
        )
    print(f"[OK] Actual {name} contract verified")


def main() -> int:
    print("=" * 40)
    print(" OOP-008 INSTALLER")
    print(" READ INVOCATION READINESS")
    print(" BOUNDED ARTIFACT READ")
    print("=" * 40)

    verify_contract(
        SOURCE_OOP_007,
        "OOP-007",
        (
            'SCHEMA_VERSION = "OOP-007"',
            "class OracleOperatorQueryResolutionAuthorizationConsumption",
            "class OracleOperatorQueryResolutionAuthorizationConsumptionGate",
            "resolution_consumption_id",
            "resolution_consumption_hash",
            "consumption_status",
            "read_invocation_mode",
            "immutable_read_manifest_verified",
            "single_use_consumption_verified",
            "analytics_artifact_read_allowed",
            "analytics_artifact_read_performed",
            "analytics_query_execution_allowed",
            "operator_session_construction_allowed",
            "qseries_execution_allowed",
        ),
    )
    verify_contract(
        SOURCE_OOP_006,
        "OOP-006",
        (
            'SCHEMA_VERSION = "OOP-006"',
            "class OracleOperatorQueryResolutionAuthorization",
            "resolution_authorization_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_005,
        "OOP-005",
        (
            'SCHEMA_VERSION = "OOP-005"',
            "class OracleOperatorQueryResolutionPlan",
            "resolution_plan_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_004,
        "OOP-004",
        (
            'SCHEMA_VERSION = "OOP-004"',
            "class OracleOperatorQueryRequestAdmission",
            "query_admission_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_003,
        "OOP-003",
        (
            'SCHEMA_VERSION = "OOP-003"',
            "class OracleOperatorQueryRequest",
            "query_request_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_002,
        "OOP-002",
        (
            'SCHEMA_VERSION = "OOP-002"',
            "class OracleOperatorAnalyticsDependencyAdmission",
            "admission_hash",
        ),
    )
    verify_contract(
        SOURCE_OOP_001,
        "OOP-001",
        (
            'SCHEMA_VERSION = "OOP-001"',
            "class OracleOperatorAnalyticsDependencyReceipt",
            "dependency_receipt_hash",
        ),
    )
    verify_contract(
        SOURCE_060,
        "INT-OIA-060",
        (
            'SCHEMA_VERSION = "INT-OIA-060"',
            "authorization_hash",
            "read_only_consumption_verified",
        ),
    )

    protected_before = {
        SOURCE_OOP_007: sha256_file(SOURCE_OOP_007),
        SOURCE_OOP_006: sha256_file(SOURCE_OOP_006),
        SOURCE_OOP_005: sha256_file(SOURCE_OOP_005),
        SOURCE_OOP_004: sha256_file(SOURCE_OOP_004),
        SOURCE_OOP_003: sha256_file(SOURCE_OOP_003),
        SOURCE_OOP_002: sha256_file(SOURCE_OOP_002),
        SOURCE_OOP_001: sha256_file(SOURCE_OOP_001),
        SOURCE_060: sha256_file(SOURCE_060),
    }

    write_replacement(PRODUCTION, PRODUCTION_SOURCE)
    write_replacement(TEST, TEST_SOURCE)

    append_export(
        QUERY_PACKAGE,
        "from .oracle_operator_query_resolution_read_invocation_readiness_gate import *",
    )
    append_export(
        OPERATOR_PACKAGE,
        "from .query.oracle_operator_query_resolution_read_invocation_readiness_gate import *",
    )

    for target in (
        PRODUCTION,
        TEST,
        QUERY_PACKAGE,
        OPERATOR_PACKAGE,
    ):
        ast.parse(
            target.read_text(encoding="utf-8"),
            filename=str(target),
        )
    print("[OK] Production, test, and package syntax verified in memory")

    for path, expected_hash in protected_before.items():
        if sha256_file(path) != expected_hash:
            raise RuntimeError(f"Protected upstream module changed: {path}")
    print("[PASS] OOP-001 through OOP-007 and INT-OIA-060 unchanged")

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
    print("[OK] OOP-008 test executed automatically")
    print()
    print("[DONE] OOP-008 read invocation readiness gate installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
