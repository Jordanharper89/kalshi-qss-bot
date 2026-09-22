from __future__ import annotations

from dataclasses import replace

from test_int_oia_052_oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_gate import (
    _authorization,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_secondary_consumption_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_consumption_attestation_authorization_consumption_attestation_gate import (
    ATTESTATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe consumption attestation accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationInvariantError:
        pass


def _consumption():
    authorization = _authorization()
    return (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionGate()
    ).consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-053 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" AUTHORIZATION CONSUMPTION ATTESTATION")
    print("=" * 40)

    consumption = _consumption()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactConsumptionAttestationAuthorizationConsumptionAttestationGate()
    )

    first = gate.attest(consumption=consumption)
    repeated = gate.attest(consumption=consumption)

    assert first == repeated
    assert first.consumption_attested
    assert first.attested_entry_count == consumption.consumed_entry_count
    assert first.attested_response_artifact_entry_ids == (
        consumption.consumed_response_artifact_entry_ids
    )
    assert first.attested_query_response_ids == (
        consumption.consumed_query_response_ids
    )
    assert first.attestation_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "attestation_hash"
        }
    )

    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(
                consumption,
                consumption_hash="0" * 64,
            )
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(
                consumption,
                publication_allowed=True,
            )
        )
    )
    _expect_rejected(
        lambda: gate.attest(
            consumption=replace(
                consumption,
                single_use_verified=False,
            )
        )
    )

    duplicate_ids = (
        consumption.consumed_response_artifact_entry_ids[0],
        consumption.consumed_response_artifact_entry_ids[0],
    )
    tampered_body = {
        key: value
        for key, value in consumption.__dict__.items()
        if key != "consumption_hash"
    }
    tampered_body["consumed_response_artifact_entry_ids"] = duplicate_ids
    tampered_consumption = replace(
        consumption,
        consumed_response_artifact_entry_ids=duplicate_ids,
        consumption_hash=stable_hash(tampered_body),
    )
    _expect_rejected(lambda: gate.attest(consumption=tampered_consumption))

    assert first.consumption_hash_verified
    assert first.consumption_identity_verified
    assert first.authorization_lineage_verified
    assert first.attestation_lineage_verified
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
    assert first.single_use_consumption_verified
    assert first.read_only_consumption_verified
    assert first.source_hashes_verified
    assert first.lineage_verified
    assert first.deterministic_ordering_verified
    assert first.deterministic_consumption_verified
    assert first.independent_attestation_verified
    assert not first.registry_mutation_allowed
    assert not first.registry_mutation_performed
    assert not first.publication_allowed
    assert not first.publication_performed
    assert not first.order_execution_allowed
    assert not first.order_execution_performed
    assert not first.database_connection_performed
    assert not first.corpus_read_execution_repeated

    assert ATTESTATION_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-consumption-attestation-"
        "authorization-consumption-attestation.v1"
    )

    print("[PASS] Actual corrected INT-OIA-052 consumption contract consumed")
    print("[PASS] Consumption identity and hash independently verified")
    print("[PASS] Authorization, attestation, and complete read lineage verified")
    print("[PASS] Consumer and projection identities independently attested")
    print("[PASS] Entry and query-response cardinality independently verified")
    print("[PASS] Duplicate consumed identities rejected")
    print("[PASS] Single-use consumption evidence verified")
    print("[PASS] Deterministic independent attestation created")
    print("[PASS] Deterministic attestation replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-052 lineage preserved")
    print("[PASS] Tampered and unsafe consumption evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
