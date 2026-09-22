from __future__ import annotations

from dataclasses import replace

from test_int_oia_058_oracle_intelligence_analytics_certified_query_response_artifact_authorization_consumption_attestation_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_058_consumption_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_int_oia_059_attestation_gate import (
    ATTESTATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe authorization consumption attestation accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationInvariantError:
        pass


def _consumption():
    authorization = _authorization()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionGate()
    ).consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-059 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION")
    print("=" * 40)

    consumption = _consumption()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactAuthorizationConsumptionAttestationAuthorizationConsumptionAttestationGate()
    )

    first = gate.attest(consumption=consumption)
    repeated = gate.attest(consumption=consumption)

    assert first == repeated
    assert first.consumption_attested
    assert first.attested_entry_count == consumption.consumed_entry_count
    assert first.attested_response_artifact_entry_ids == consumption.consumed_response_artifact_entry_ids
    assert first.attested_query_response_ids == consumption.consumed_query_response_ids
    assert first.attestation_hash == stable_hash(
        {key: value for key, value in first.__dict__.items() if key != "attestation_hash"}
    )

    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, consumption_hash="0" * 64)
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, publication_allowed=True)
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, single_use_authorization_verified=False)
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(consumption, independent_attestation_verified=False)
        )
    )

    assert first.consumption_hash_verified
    assert first.consumption_identity_verified
    assert first.authorization_lineage_verified
    assert first.prior_attestation_lineage_verified
    assert first.prior_consumption_lineage_verified
    assert first.prior_authorization_lineage_verified
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

    assert ATTESTATION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-authorization-consumption-"
        "attestation-authorization-consumption-attestation.v1"
    )

    print("[PASS] Actual INT-OIA-058 consumption contract consumed")
    print("[PASS] Consumption identity and hash independently verified")
    print("[PASS] Authorization and complete read lineage independently verified")
    print("[PASS] Consumer and projection identities independently attested")
    print("[PASS] Entry and query-response cardinality independently verified")
    print("[PASS] Single-use authorization evidence verified")
    print("[PASS] Deterministic independent attestation created")
    print("[PASS] Deterministic attestation replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-058 lineage preserved")
    print("[PASS] Tampered and unsafe consumption evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
