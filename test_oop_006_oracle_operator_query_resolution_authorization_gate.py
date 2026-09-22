from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import _attestation
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import OracleOperatorAnalyticsReadOnlyDependencyGate
from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import OracleOperatorAnalyticsDependencyAdmissionGate
from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import OracleOperatorQueryRequestContract
from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import OracleOperatorQueryRequestAdmissionGate
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_plan import OracleOperatorQueryResolutionPlanner
from qseries_v2.oracle_operator.query.oracle_operator_query_resolution_authorization_gate import (
    AUTHORIZATION_STATUS,
    OracleOperatorQueryResolutionAuthorizationGate,
    OracleOperatorQueryResolutionAuthorizationInvariantError,
    stable_hash,
)


def _plan():
    authorization = OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate().authorize(
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
    return OracleOperatorQueryResolutionPlanner().plan(
        admission=query_admission
    )


def _expect_rejected(fn) -> None:
    try:
        fn()
        raise AssertionError("unsafe resolution authorization accepted")
    except OracleOperatorQueryResolutionAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-006 TEST")
    print(" RESOLUTION AUTHORIZATION")
    print(" SINGLE READ-ONLY PATH")
    print("=" * 40)

    plan = _plan()
    gate = OracleOperatorQueryResolutionAuthorizationGate()
    first = gate.authorize(plan=plan)
    repeated = gate.authorize(plan=plan)

    assert first == repeated
    assert first.resolution_authorization_hash == stable_hash(
        {k: v for k, v in first.__dict__.items() if k != "resolution_authorization_hash"}
    )
    assert first.source_resolution_plan_id == plan.resolution_plan_id
    assert first.source_resolution_plan_hash == plan.resolution_plan_hash
    assert first.authorized_resolution_strategy == plan.resolution_strategy
    assert first.authorized_entry_count == plan.planned_entry_count
    assert first.authorized_response_artifact_entry_ids == plan.planned_response_artifact_entry_ids
    assert first.authorized_query_response_ids == plan.planned_query_response_ids
    assert first.resolution_plan_type_verified
    assert first.resolution_plan_identity_verified
    assert first.resolution_plan_hash_verified
    assert first.resolution_plan_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.strategy_verified
    assert first.deterministic_authorization_verified
    assert first.single_bounded_resolution_path_verified
    assert first.read_only_resolution_required
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

    _expect_rejected(lambda: gate.authorize(plan=replace(plan, resolution_plan_hash="0" * 64)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, resolution_plan_status="wrong_status")))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, frozen_scope_preserved=False)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, query_resolution_allowed=False)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, analytics_artifact_read_allowed=True)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, analytics_query_execution_allowed=True)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, qseries_execution_allowed=True)))
    _expect_rejected(lambda: gate.authorize(plan=replace(plan, portfolio_mutation_performed=True)))

    print("[PASS] Actual OOP-005 resolution plan consumed")
    print("[PASS] OOP-005 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic resolution authorization created")
    print("[PASS] Single bounded read-only resolution path authorized")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed plans rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
