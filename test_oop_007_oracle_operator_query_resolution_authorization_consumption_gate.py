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
    CONSUMPTION_STATUS,
    READ_INVOCATION_MODE,
    OracleOperatorQueryResolutionAuthorizationConsumptionGate,
    OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _authorization():
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
    return OracleOperatorQueryResolutionAuthorizationGate().authorize(
        plan=plan
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError(
            "unsafe authorization consumption accepted"
        )
    except OracleOperatorQueryResolutionAuthorizationConsumptionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-007 TEST")
    print(" AUTHORIZATION CONSUMPTION")
    print(" IMMUTABLE READ MANIFEST")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleOperatorQueryResolutionAuthorizationConsumptionGate()
    )

    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.resolution_consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "resolution_consumption_hash"
        }
    )

    assert (
        first.source_resolution_authorization_id
        == authorization.resolution_authorization_id
    )
    assert (
        first.source_resolution_authorization_hash
        == authorization.resolution_authorization_hash
    )
    assert first.query_mode == authorization.query_mode
    assert first.query_text == authorization.query_text
    assert first.time_scope == authorization.time_scope
    assert first.sort_order == authorization.sort_order
    assert first.result_limit == authorization.result_limit
    assert first.requested_tags == authorization.requested_tags
    assert first.read_invocation_mode == READ_INVOCATION_MODE
    assert (
        first.consumed_resolution_strategy
        == authorization.authorized_resolution_strategy
    )
    assert (
        first.consumed_entry_count
        == authorization.authorized_entry_count
    )
    assert (
        first.consumed_response_artifact_entry_ids
        == authorization.authorized_response_artifact_entry_ids
    )
    assert (
        first.consumed_query_response_ids
        == authorization.authorized_query_response_ids
    )

    assert first.resolution_authorization_type_verified
    assert first.resolution_authorization_identity_verified
    assert first.resolution_authorization_hash_verified
    assert first.resolution_authorization_status_verified
    assert first.complete_lineage_verified
    assert first.namespaces_verified
    assert first.query_parameters_verified
    assert first.frozen_scope_verified
    assert first.frozen_scope_preserved
    assert first.single_bounded_resolution_path_verified
    assert first.single_use_consumption_verified
    assert first.immutable_read_manifest_verified
    assert first.deterministic_consumption_verified
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
    assert first.consumption_status == CONSUMPTION_STATUS

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                resolution_authorization_hash="0" * 64,
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
                frozen_scope_preserved=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_artifact_read_allowed=False,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_artifact_read_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                analytics_query_execution_allowed=True,
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
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                portfolio_mutation_performed=True,
            )
        )
    )

    print("[PASS] Actual OOP-006 authorization consumed")
    print("[PASS] OOP-006 identity, hash, status, and lineage verified")
    print("[PASS] Frozen authorized scope preserved without expansion")
    print("[PASS] Deterministic single-use consumption record created")
    print("[PASS] Immutable read invocation manifest materialized")
    print("[PASS] Analytics artifact read allowed but not performed")
    print("[PASS] No analytics query execution or reexecution allowed")
    print("[PASS] No analytics database connection or mutation allowed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed authorizations rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
