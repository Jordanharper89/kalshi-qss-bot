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
    RESOLUTION_PLAN_STATUS,
    OracleOperatorQueryResolutionPlanInvariantError,
    OracleOperatorQueryResolutionPlanner,
    stable_hash,
)


def _query_admission():
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
    return OracleOperatorQueryRequestAdmissionGate().admit(
        request=request
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe resolution plan accepted")
    except OracleOperatorQueryResolutionPlanInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-005 TEST")
    print(" QUERY RESOLUTION PLAN")
    print(" BOUNDED READ-ONLY MANIFEST")
    print("=" * 40)

    admission = _query_admission()
    planner = OracleOperatorQueryResolutionPlanner()

    first = planner.plan(admission=admission)
    repeated = planner.plan(admission=admission)

    assert first == repeated
    assert first.resolution_plan_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "resolution_plan_hash"
        }
    )

    assert first.source_query_admission_id == admission.query_admission_id
    assert first.source_query_admission_hash == admission.query_admission_hash
    assert first.query_mode == admission.query_mode
    assert first.query_text == admission.query_text
    assert first.time_scope == admission.time_scope
    assert first.sort_order == admission.sort_order
    assert first.result_limit == admission.result_limit
    assert first.requested_tags == admission.requested_tags
    assert (
        first.planned_entry_count
        == admission.admitted_entry_count
    )
    assert (
        first.planned_response_artifact_entry_ids
        == admission.admitted_response_artifact_entry_ids
    )
    assert (
        first.planned_query_response_ids
        == admission.admitted_query_response_ids
    )

    assert first.query_admission_type_verified
    assert first.query_admission_identity_verified
    assert first.query_admission_hash_verified
    assert first.query_admission_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.resolution_strategy_verified
    assert first.deterministic_plan_verified
    assert first.read_only_resolution_required

    assert first.query_resolution_allowed
    assert not first.query_resolution_performed
    assert not first.analytics_artifact_read_allowed
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
    assert first.resolution_plan_status == RESOLUTION_PLAN_STATUS

    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                query_admission_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                admission_status="wrong_status",
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                authorized_scope_frozen=False,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                query_resolution_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                analytics_query_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=replace(
                admission,
                qseries_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: planner.plan(
            admission=admission,
            resolution_strategy="unsupported",
        )
    )

    print("[PASS] Actual OOP-004 query admission consumed")
    print("[PASS] OOP-004 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic query resolution plan created")
    print("[PASS] Resolution strategy constrained to authorized filters")
    print("[PASS] Query resolution allowed but not performed")
    print("[PASS] No analytics artifact read performed")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed plans rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
