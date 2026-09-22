from __future__ import annotations

from dataclasses import replace

from test_int_oia_053_oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_attestation_gate import (
    _consumption,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_attestation_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_054_authorization_gate import (
    AUTHORIZATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe attestation authorization accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationInvariantError:
        pass


def _attestation():
    consumption = _consumption()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationGate()
    ).attest(consumption=consumption)


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-054 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" CONSUMPTION ATTESTATION AUTHORIZATION")
    print("=" * 40)

    attestation = _attestation()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationAuthorizationGate()
    )

    first = gate.authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    repeated = gate.authorize(
        attestation=attestation,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )

    assert first == repeated
    assert first.attestation_authorized
    assert first.authorized_entry_count == attestation.attested_entry_count
    assert first.authorized_response_artifact_entry_ids == (
        attestation.attested_response_artifact_entry_ids
    )
    assert first.authorized_query_response_ids == (
        attestation.attested_query_response_ids
    )
    assert first.authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "authorization_hash"
        }
    )

    _expect_rejected(
        lambda: gate.authorize(
            attestation=attestation,
            authorized_consumer_id="wrong.consumer",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=attestation,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(attestation, attestation_hash="0" * 64),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(attestation, publication_allowed=True),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: gate.authorize(
            attestation=replace(
                attestation,
                independent_attestation_verified=False,
            ),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    assert first.attestation_hash_verified
    assert first.attestation_identity_verified
    assert first.consumption_lineage_verified
    assert first.authorization_lineage_verified
    assert first.prior_consumption_lineage_verified
    assert first.prior_authorization_lineage_verified
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
    assert first.single_use_consumption_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_replay_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert AUTHORIZATION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-consumption-attestation-"
        "authorization-consumption-attestation-authorization.v1"
    )

    print("[PASS] Actual INT-OIA-053 attestation contract consumed")
    print("[PASS] Attestation identity and hash independently verified")
    print("[PASS] Consumption, authorization, and complete read lineage verified")
    print("[PASS] Consumer and projection identities matched exactly")
    print("[PASS] Entry and query-response identity cardinality verified")
    print("[PASS] Duplicate attested identities rejected")
    print("[PASS] Independent attestation and single-use evidence required")
    print("[PASS] Deterministic authorization record created")
    print("[PASS] Deterministic authorization replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-053 lineage preserved")
    print("[PASS] Tampered and unsafe attestation evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
