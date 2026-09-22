from __future__ import annotations

from dataclasses import replace

from test_int_oia_060_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_attestation_authorization_gate import (
    _attestation,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_060_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
)
from qseries_v2.oracle_operator.oracle_operator_analytics_read_only_dependency_gate import (
    DEPENDENCY_SCHEMA_VERSION,
    EXPECTED_ANALYTICS_SCHEMA_VERSION,
    OPERATOR_PACKAGE_NAMESPACE,
    OracleOperatorAnalyticsReadOnlyDependencyGate,
    OracleOperatorAnalyticsReadOnlyDependencyInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe analytics dependency accepted")
    except OracleOperatorAnalyticsReadOnlyDependencyInvariantError:
        pass


def _authorization():
    attestation = _attestation()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" OOP-001 TEST")
    print(" ORACLE OPERATOR SUBSYSTEM ROOT")
    print(" ANALYTICS READ-ONLY DEPENDENCY")
    print("=" * 40)

    authorization = _authorization()
    gate = OracleOperatorAnalyticsReadOnlyDependencyGate()

    boundary = gate.subsystem_boundary()
    first = gate.consume(authorization=authorization)
    repeated = gate.consume(authorization=authorization)

    assert first == repeated
    assert first.dependency_receipt_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "dependency_receipt_hash"
        }
    )

    assert boundary.subsystem_id == "oracle.operator"
    assert boundary.package_namespace == "qseries_v2.oracle_operator"
    assert boundary.query_namespace == "qseries_v2.oracle_operator.query"
    assert boundary.session_namespace == "qseries_v2.oracle_operator.session"
    assert boundary.console_namespace == "qseries_v2.oracle_operator.console"
    assert (
        boundary.presentation_namespace
        == "qseries_v2.oracle_operator.presentation"
    )
    assert boundary.separate_from_analytics
    assert boundary.separate_from_qseries_execution
    assert not boundary.analytics_mutation_allowed
    assert not boundary.qseries_execution_import_allowed
    assert not boundary.qseries_execution_allowed
    assert not boundary.order_creation_allowed
    assert not boundary.funds_movement_allowed
    assert not boundary.portfolio_mutation_allowed

    assert first.source_schema_version == "INT-OIA-060"
    assert first.source_authorization_id == authorization.authorization_id
    assert first.source_authorization_hash == authorization.authorization_hash
    assert first.authorized_consumer_id == "oracle.operator.console.v1"
    assert first.authorized_projection == "operator_research"
    assert first.authorized_entry_count == authorization.authorized_entry_count
    assert first.source_type_verified
    assert first.source_hash_verified
    assert first.source_lineage_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.deterministic_replay_verified
    assert first.read_only_dependency_verified

    assert not first.analytics_reexecution_performed
    assert not first.analytics_database_connection_performed
    assert not first.analytics_corpus_read_repeated
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

    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorization_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_consumer_id="wrong.consumer",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                authorized_projection="wrong_projection",
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                order_execution_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.consume(
            authorization=replace(
                authorization,
                database_connection_performed=True,
            )
        )
    )

    assert EXPECTED_ANALYTICS_SCHEMA_VERSION == "INT-OIA-060"
    assert OPERATOR_PACKAGE_NAMESPACE == "qseries_v2.oracle_operator"
    assert (
        DEPENDENCY_SCHEMA_VERSION
        == "oracle.operator.analytics-read-only-dependency-receipt.v1"
    )

    print("[PASS] Separate qseries_v2.oracle_operator subsystem established")
    print("[PASS] query, session, console, and presentation namespaces established")
    print("[PASS] Actual canonical INT-OIA-060 authorization consumed")
    print("[PASS] INT-OIA-060 source type and hash independently verified")
    print("[PASS] Complete certified analytics lineage preserved read-only")
    print("[PASS] Deterministic dependency receipt created and replay verified")
    print("[PASS] Analytics was not reexecuted, queried, connected, or modified")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series handoff and execution remained disabled")
    print("[PASS] Orders, funds, and portfolio mutation remained disabled")
    print("[PASS] Tampered and unsafe dependency evidence rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
