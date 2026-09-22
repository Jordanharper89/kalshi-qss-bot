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
