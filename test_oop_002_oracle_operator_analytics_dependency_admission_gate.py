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
    ADMISSION_STATUS,
    EXPECTED_OPERATOR_NAMESPACE,
    OracleOperatorAnalyticsDependencyAdmissionGate,
    OracleOperatorAnalyticsDependencyAdmissionInvariantError,
    stable_hash,
)


def _authorization():
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=_attestation(),
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def _receipt():
    return OracleOperatorAnalyticsReadOnlyDependencyGate().consume(
        authorization=_authorization()
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe dependency receipt admitted")
    except OracleOperatorAnalyticsDependencyAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" OOP-002 TEST")
    print(" ANALYTICS DEPENDENCY ADMISSION")
    print(" READ-ONLY OPERATOR BOUNDARY")
    print("=" * 40)

    receipt = _receipt()
    gate = OracleOperatorAnalyticsDependencyAdmissionGate()

    first = gate.admit(receipt=receipt)
    repeated = gate.admit(receipt=receipt)

    assert first == repeated
    assert first.admission_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "admission_hash"
        }
    )

    assert first.source_dependency_receipt_id == receipt.dependency_receipt_id
    assert (
        first.source_dependency_receipt_hash
        == receipt.dependency_receipt_hash
    )
    assert first.source_subsystem_boundary_hash == receipt.subsystem_boundary_hash
    assert first.source_schema_version == "INT-OIA-060"
    assert first.source_authorization_id == receipt.source_authorization_id
    assert first.source_authorization_hash == receipt.source_authorization_hash
    assert first.admitted_consumer_id == "oracle.operator.console.v1"
    assert first.admitted_projection == "operator_research"
    assert first.admitted_entry_count == receipt.authorized_entry_count
    assert (
        first.admitted_response_artifact_entry_ids
        == receipt.authorized_response_artifact_entry_ids
    )
    assert (
        first.admitted_query_response_ids
        == receipt.authorized_query_response_ids
    )

    assert first.dependency_receipt_type_verified
    assert first.dependency_receipt_hash_verified
    assert first.subsystem_boundary_verified
    assert first.source_schema_verified
    assert first.source_authorization_schema_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.entry_cardinality_verified
    assert first.unique_entry_identities_verified
    assert first.source_lineage_verified
    assert first.deterministic_replay_verified
    assert first.read_only_dependency_verified

    assert first.operator_query_construction_allowed
    assert not first.operator_session_construction_allowed
    assert not first.operator_console_rendering_allowed
    assert not first.operator_presentation_rendering_allowed

    assert not first.analytics_reexecution_allowed
    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_allowed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_mutation_allowed
    assert not first.analytics_mutation_performed
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
    assert first.admission_status == ADMISSION_STATUS

    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                dependency_receipt_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                source_schema_version="INT-OIA-059",
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                authorized_consumer_id="wrong.consumer",
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                authorized_projection="wrong_projection",
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                authorized_entry_count=0,
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                qseries_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                analytics_database_connection_performed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.admit(
            receipt=replace(
                receipt,
                portfolio_mutation_performed=True,
            )
        )
    )

    assert EXPECTED_OPERATOR_NAMESPACE == "qseries_v2.oracle_operator"

    print("[PASS] Actual OOP-001 dependency receipt consumed")
    print("[PASS] OOP-001 receipt type, identity, and hash verified")
    print("[PASS] INT-OIA-060 source schema and lineage preserved")
    print("[PASS] Consumer and projection identities enforced")
    print("[PASS] Entry cardinality and uniqueness verified")
    print("[PASS] Deterministic operator admission record created")
    print("[PASS] Operator query construction admitted")
    print("[PASS] Session, console, and presentation remain gated")
    print("[PASS] Analytics reexecution and reconnection remain disabled")
    print("[PASS] Analytics mutation and publication remain disabled")
    print("[PASS] Q Series handoff and execution remain disabled")
    print("[PASS] Orders, funds, and portfolio mutation remain disabled")
    print("[PASS] Tampered, stale, and unsafe receipts rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
