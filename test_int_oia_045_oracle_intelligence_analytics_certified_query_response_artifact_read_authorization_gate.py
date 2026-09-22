from __future__ import annotations

from dataclasses import replace

from test_int_oia_044_oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    _manifest,
)

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_authorization_gate import (
    AUTHORIZATION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError,
    stable_hash,
)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe read authorization accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadAuthorizationInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-045 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ AUTHORIZATION GATE")
    print("=" * 40)

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
    assert result.matched_entry_count == 2

    first = authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )
    repeated = authorization_gate.authorize(
        read_result=result,
        authorized_consumer_id="oracle.operator.console.v1",
        authorized_projection="operator_research",
    )

    assert first == repeated
    assert first.read_authorized
    assert first.authorized_entry_count == 2
    assert first.authorized_response_artifact_entry_ids == tuple(
        entry.response_artifact_entry_id
        for entry in result.matched_entries
    )
    assert first.authorized_query_response_ids == tuple(
        entry.query_response_id
        for entry in result.matched_entries
    )
    assert first.authorization_hash == stable_hash(
        {
            key: value
            for key, value in first.__dict__.items()
            if key != "authorization_hash"
        }
    )

    mixed_request = read_gate.create_request(
        registry_manifest=manifest,
        maximum_result_count=100,
    )
    mixed_result = read_gate.read(
        registry_manifest=manifest,
        read_request=mixed_request,
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=mixed_result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=result,
            authorized_consumer_id="wrong.consumer",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="wrong_projection",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=replace(
                result,
                read_result_hash="0" * 64,
            ),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=replace(
                result,
                publication_allowed=True,
            ),
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    tampered_entry = replace(
        result.matched_entries[0],
        consumer_id="tampered.consumer",
    )
    tampered_entries = (
        tampered_entry,
        *result.matched_entries[1:],
    )
    tampered_body = {
        key: value
        for key, value in result.__dict__.items()
        if key != "read_result_hash"
    }
    tampered_body["matched_entries"] = tampered_entries
    tampered_result = replace(
        result,
        matched_entries=tampered_entries,
        read_result_hash=stable_hash(tampered_body),
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=tampered_result,
            authorized_consumer_id="oracle.operator.console.v1",
            authorized_projection="operator_research",
        )
    )

    empty_request = read_gate.create_request(
        registry_manifest=manifest,
        consumer_id="missing.consumer",
    )
    empty_result = read_gate.read(
        registry_manifest=manifest,
        read_request=empty_request,
    )
    _expect_rejected(
        lambda: authorization_gate.authorize(
            read_result=empty_result,
            authorized_consumer_id="missing.consumer",
            authorized_projection="operator_research",
        )
    )

    assert first.read_result_verified
    assert first.registry_manifest_verified
    assert first.registry_entry_hashes_verified
    assert first.request_verified
    assert first.non_empty_result_verified
    assert first.single_consumer_verified
    assert first.single_projection_verified
    assert first.consumer_identity_verified
    assert first.projection_identity_verified
    assert first.immutable_read_verified
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
        "oracle.certified-query-response-artifact-read-authorization.v1"
    )

    print("[PASS] Actual INT-OIA-044 read-result contract consumed")
    print("[PASS] Read-result hash independently verified")
    print("[PASS] Every authorized artifact entry hash verified")
    print("[PASS] Non-empty read result required")
    print("[PASS] Single-consumer boundary enforced")
    print("[PASS] Single-projection boundary enforced")
    print("[PASS] Consumer and projection identities verified")
    print("[PASS] Deterministic authorization record created")
    print("[PASS] Deterministic authorization replay verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-044 lineage preserved")
    print("[PASS] Mixed-consumer and mixed-projection results rejected")
    print("[PASS] Tampered read-result evidence rejected")
    print("[PASS] Tampered artifact-entry evidence rejected")
    print("[PASS] Empty read result rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
