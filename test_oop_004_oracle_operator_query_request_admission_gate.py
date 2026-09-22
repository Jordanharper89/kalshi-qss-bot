from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import _attestation
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import OracleOperatorAnalyticsReadOnlyDependencyGate
from qseries_v2.oracle_operator.oracle_operator_analytics_dependency_admission_gate import OracleOperatorAnalyticsDependencyAdmissionGate
from qseries_v2.oracle_operator.query.oracle_operator_query_request_contract import OracleOperatorQueryRequestContract
from qseries_v2.oracle_operator.query.oracle_operator_query_request_admission_gate import (
    ADMISSION_STATUS,
    OracleOperatorQueryRequestAdmissionGate,
    OracleOperatorQueryRequestAdmissionInvariantError,
    stable_hash,
)


def _request():
    authorization = OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate().authorize(
        attestation=_attestation(),
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    receipt = OracleOperatorAnalyticsReadOnlyDependencyGate().consume(authorization=authorization)
    admission = OracleOperatorAnalyticsDependencyAdmissionGate().admit(receipt=receipt)
    return OracleOperatorQueryRequestContract().materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("kalshi", "major"),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query request admitted")
    except OracleOperatorQueryRequestAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-004 TEST")
    print(" QUERY REQUEST ADMISSION")
    print(" AUTHORIZED SCOPE FREEZE")
    print("=" * 40)

    request = _request()
    gate = OracleOperatorQueryRequestAdmissionGate()
    first = gate.admit(request=request)
    repeated = gate.admit(request=request)

    assert first == repeated
    assert first.query_admission_hash == stable_hash({
        key: value for key, value in first.__dict__.items() if key != "query_admission_hash"
    })
    assert first.source_query_request_id == request.query_request_id
    assert first.source_query_request_hash == request.query_request_hash
    assert first.consumer_id == "oracle.operator.console.v1"
    assert first.projection == "operator_research"
    assert first.operator_namespace == "qseries_v2.oracle_operator"
    assert first.query_namespace == "qseries_v2.oracle_operator.query"
    assert first.query_mode == "opportunity_lookup"
    assert first.query_text == "Show major opportunities closing today"
    assert first.time_scope == "same_day"
    assert first.sort_order == "priority"
    assert first.result_limit == 20
    assert first.requested_tags == ("kalshi", "major")
    assert first.admitted_entry_count == request.authorized_entry_count
    assert first.admitted_response_artifact_entry_ids == request.authorized_response_artifact_entry_ids
    assert first.admitted_query_response_ids == request.authorized_query_response_ids

    required_true = (
        first.query_request_type_verified,
        first.query_request_identity_verified,
        first.query_request_hash_verified,
        first.query_request_status_verified,
        first.source_admission_lineage_verified,
        first.source_dependency_lineage_verified,
        first.source_authorization_lineage_verified,
        first.operator_namespace_verified,
        first.consumer_identity_verified,
        first.projection_identity_verified,
        first.query_parameters_verified,
        first.authorized_scope_verified,
        first.authorized_scope_frozen,
        first.deterministic_admission_verified,
        first.analytics_read_only_dependency_preserved,
        first.query_resolution_allowed,
    )
    assert all(required_true)

    forbidden = (
        first.query_resolution_performed,
        first.analytics_query_execution_allowed,
        first.analytics_query_execution_performed,
        first.analytics_reexecution_allowed,
        first.analytics_reexecution_performed,
        first.analytics_database_connection_allowed,
        first.analytics_database_connection_performed,
        first.analytics_mutation_allowed,
        first.analytics_mutation_performed,
        first.operator_session_construction_allowed,
        first.operator_console_rendering_allowed,
        first.operator_presentation_rendering_allowed,
        first.publication_allowed,
        first.publication_performed,
        first.qseries_handoff_allowed,
        first.qseries_execution_allowed,
        first.qseries_execution_performed,
        first.order_creation_allowed,
        first.order_creation_performed,
        first.funds_movement_allowed,
        first.funds_movement_performed,
        first.portfolio_mutation_allowed,
        first.portfolio_mutation_performed,
    )
    assert not any(forbidden)
    assert first.admission_status == ADMISSION_STATUS

    _expect_rejected(lambda: gate.admit(request=replace(request, query_request_hash="0" * 64)))
    _expect_rejected(lambda: gate.admit(request=replace(request, query_request_status="wrong_status")))
    _expect_rejected(lambda: gate.admit(request=replace(request, operator_namespace="wrong.namespace")))
    _expect_rejected(lambda: gate.admit(request=replace(request, authorized_entry_count=0)))
    _expect_rejected(lambda: gate.admit(request=replace(request, authorized_scope_preserved=False)))
    _expect_rejected(lambda: gate.admit(request=replace(request, analytics_query_execution_allowed=True)))
    _expect_rejected(lambda: gate.admit(request=replace(request, qseries_execution_allowed=True)))
    _expect_rejected(lambda: gate.admit(request=replace(request, portfolio_mutation_performed=True)))

    print("[PASS] Actual OOP-003 query request consumed")
    print("[PASS] OOP-003 identity, hash, status, and lineage verified")
    print("[PASS] Operator and query namespaces enforced")
    print("[PASS] Consumer, projection, and query parameters verified")
    print("[PASS] Authorized analytics scope verified and frozen")
    print("[PASS] Deterministic query admission created and replay verified")
    print("[PASS] Query resolution admitted but not performed")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed requests rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
