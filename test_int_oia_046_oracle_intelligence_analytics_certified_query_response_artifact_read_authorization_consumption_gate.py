from __future__ import annotations

from dataclasses import replace

from test_int_oia_044_oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    _manifest,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_consumption_gate import (
    CONSUMPTION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe authorization consumption accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionInvariantError:
        pass


def _authorization():
    manifest = _manifest()
    read_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate()
    )
    authorization_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate()
    )
    request = read_gate.create_request(
        registry_manifest=manifest,
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        maximum_result_count=100,
    )
    result = read_gate.read(
        registry_manifest=manifest,
        read_request=request,
    )
    return authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-046 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION CONSUMPTION")
    print("=" * 40)

    authorization = _authorization()
    gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
    )

    first = gate.consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )

    assert first.authorization_consumed
    assert first.consumed_entry_count == 2
    assert first.consumed_response_artifact_entry_ids == (
        authorization.authorized_response_artifact_entry_ids
    )
    assert first.consumed_query_response_ids == (
        authorization.authorized_query_response_ids
    )
    assert gate.consumed_authorization_ids == (
        authorization.authorization_id,
    )
    assert first.consumption_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "consumption_hash"
        }
    )

    replay_gate = (
        OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
    )
    replay = replay_gate.consume(
        authorization=authorization,
        consuming_consumer_id="oracle.operator.console.v1",
        consuming_projection="operator_research",
    )
    assert replay == first

    _expect_rejected(
        lambda: gate.consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="wrong.consumer",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(
                authorization,
                authorization_hash="0" * 64,
            ),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=replace(
                authorization,
                publication_allowed=True,
            ),
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )

    duplicate_ids = (
        authorization.authorized_response_artifact_entry_ids[0],
        authorization.authorized_response_artifact_entry_ids[0],
    )
    tampered_body = {
        key: value
        for key, value in authorization.__dict__.items()
        if key != "authorization_hash"
    }
    tampered_body["authorized_response_artifact_entry_ids"] = duplicate_ids
    tampered_authorization = replace(
        authorization,
        authorized_response_artifact_entry_ids=duplicate_ids,
        authorization_hash=stable_hash(tampered_body),
    )
    _expect_rejected(
        lambda: (
            OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationConsumptionGate()
        ).consume(
            authorization=tampered_authorization,
            consuming_consumer_id="oracle.operator.console.v1",
            consuming_projection="operator_research",
        )
    )

    assert first.authorization_verified
    assert first.authorization_identity_verified
    assert first.authorization_hash_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.non_empty_authorization_verified
    assert first.entry_identity_cardinality_verified
    assert first.query_response_identity_cardinality_verified
    assert first.single_use_verified
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
        "oracle.certified-query-response-artifact-read-authorization-consumption.v1"
    )

    print("[PASS] Actual INT-OIA-045 authorization contract consumed")
    print("[PASS] Authorization identity and hash independently verified")
    print("[PASS] Consumer and projection identities matched exactly")
    print("[PASS] Artifact-entry and query-response cardinality verified")
    print("[PASS] Duplicate authorized identities rejected")
    print("[PASS] Deterministic consumption record created")
    print("[PASS] Fresh-gate deterministic replay verified")
    print("[PASS] Same-gate duplicate consumption rejected")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-045 lineage preserved")
    print("[PASS] Tampered authorization evidence rejected")
    print("[PASS] Mismatched consumer and projection rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
