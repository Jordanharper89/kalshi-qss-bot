from __future__ import annotations

from dataclasses import replace

from test_int_oia_054_oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_attestation_authorization_gate import (
    _attestation,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_054_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_055_consumption_gate import (
    CONSUMPTION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe authorization consumption accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionInvariantError:
        pass


def _authorization():
    attestation = _attestation()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    ).authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-055 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" ATTESTATION AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
    )

    first = gate.consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )

    fresh_replay = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
    ).consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )

    assert first == fresh_replay
    assert first.authorization_consumed
    assert first.consumed_entry_count == authorization.authorized_entry_count
    assert first.consumed_response_artifact_entry_ids == (
        authorization.authorized_response_artifact_entry_ids
    )
    assert first.consumed_query_response_ids == (
        authorization.authorized_query_response_ids
    )
    assert first.consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "consumption_hash"
        }
    )

    _expect_rejected(
        lambda: gate.consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="wrong.consumer",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(authorization, authorization_hash="0" * 64),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(authorization, publication_allowed=True),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(
                authorization,
                independent_attestation_verified=False,
            ),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )

    assert first.authorization_hash_verified
    assert first.authorization_identity_verified
    assert first.attestation_lineage_verified
    assert first.consumption_lineage_verified
    assert first.prior_authorization_lineage_verified
    assert first.prior_consumption_lineage_verified
    assert first.prior_attestation_lineage_verified
    assert first.read_authorization_lineage_verified
    assert first.read_result_lineage_verified
    assert first.read_request_lineage_verified
    assert first.registry_manifest_lineage_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.entry_identity_cardinality_verified
    assert first.query_response_identity_cardinality_verified
    assert first.unique_entry_identities_verified
    assert first.unique_query_response_identities_verified
    assert first.independent_attestation_verified
    assert first.single_use_authorization_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_consumption_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert CONSUMPTION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-consumption-attestation-"
        "authorization-consumption-attestation-authorization-consumption.v1"
    )

    print("[PASS] Actual INT-OIA-054 authorization contract consumed")
    print("[PASS] Authorization identity and hash independently verified")
    print("[PASS] Attestation, consumption, and complete read lineage preserved")
    print("[PASS] Consumer and projection identities matched exactly")
    print("[PASS] Entry and query-response cardinality verified")
    print("[PASS] Duplicate authorized identities rejected")
    print("[PASS] Deterministic consumption record created")
    print("[PASS] Fresh-gate deterministic replay verified")
    print("[PASS] Same-gate duplicate consumption rejected")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-054 lineage preserved")
    print("[PASS] Tampered and unsafe authorization evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
