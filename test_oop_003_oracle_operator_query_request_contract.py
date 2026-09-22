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
    QUERY_REQUEST_STATUS,
    OracleOperatorQueryRequestContract,
    OracleOperatorQueryRequestInvariantError,
    stable_hash,
)


def _admission():
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
    return OracleOperatorAnalyticsDependencyAdmissionGate().admit(
        receipt=receipt
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query request accepted")
    except OracleOperatorQueryRequestInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-003 TEST")
    print(" OPERATOR QUERY REQUEST")
    print(" DETERMINISTIC READ-ONLY CONTRACT")
    print("=" * 40)

    admission = _admission()
    contract = OracleOperatorQueryRequestContract()

    first = contract.materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="  Show   major opportunities closing today  ",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=(" Kalshi ", "Major", "kalshi"),
    )
    repeated = contract.materialize(
        admission=admission,
        query_mode="opportunity_lookup",
        query_text="Show major opportunities closing today",
        time_scope="same_day",
        sort_order="priority",
        result_limit=20,
        requested_tags=("major", "kalshi"),
    )

    assert first == repeated
    assert first.query_request_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "query_request_hash"
        }
    )

    assert first.source_admission_id == admission.admission_id
    assert first.source_admission_hash == admission.admission_hash
    assert first.consumer_id == "oracle.operator.console.v1"
    assert first.projection == "operator_research"
    assert first.operator_namespace == "qseries_v2.oracle_operator"
    assert first.query_mode == "opportunity_lookup"
    assert first.query_text == "Show major opportunities closing today"
    assert first.time_scope == "same_day"
    assert first.sort_order == "priority"
    assert first.result_limit == 20
    assert first.requested_tags == ("kalshi", "major")
    assert first.authorized_entry_count == admission.admitted_entry_count
    assert (
        first.authorized_response_artifact_entry_ids
        == admission.admitted_response_artifact_entry_ids
    )
    assert (
        first.authorized_query_response_ids
        == admission.admitted_query_response_ids
    )

    assert first.admission_type_verified
    assert first.admission_hash_verified
    assert first.admission_status_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.query_mode_verified
    assert first.time_scope_verified
    assert first.sort_order_verified
    assert first.result_limit_verified
    assert first.authorized_scope_preserved
    assert first.deterministic_request_verified
    assert first.analytics_read_only_dependency_preserved

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
    assert first.query_request_status == QUERY_REQUEST_STATUS

    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                admission_hash="0" * 64,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                operator_query_construction_allowed=False,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=replace(
                admission,
                qseries_execution_allowed=True,
            ),
            query_mode="market_lookup",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="unsupported",
            query_text="test",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="   ",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            time_scope="unsupported",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            sort_order="unsupported",
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            result_limit=0,
        )
    )
    _expect_rejected(
        lambda: contract.materialize(
            admission=admission,
            query_mode="market_lookup",
            query_text="test",
            result_limit=101,
        )
    )

    print("[PASS] Actual OOP-002 admission consumed")
    print("[PASS] OOP-002 identity, hash, status, and lineage verified")
    print("[PASS] Deterministic operator query request materialized")
    print("[PASS] Query text and tags normalized deterministically")
    print("[PASS] Query mode, time scope, sort order, and limit enforced")
    print("[PASS] Authorized analytics scope preserved without expansion")
    print("[PASS] No analytics query execution or reexecution performed")
    print("[PASS] No analytics database connection or mutation performed")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Publication and Q Series execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, unsafe, and malformed requests rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
