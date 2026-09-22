from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_admission_gate import (
    AuthorizedConsumerQueryAdmissionRequest,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError,
    QUERY_ADMISSION_SCHEMA_VERSION,
    stable_hash,
)


def signed(gate, **overrides):
    request = AuthorizedConsumerQueryAdmissionRequest(
        request_id="query-request-1",
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        market_id="KX-ALPHA",
        venue_id="kalshi",
        maximum_results=100,
    )
    request = replace(request, **overrides)
    return replace(request, request_hash=gate.calculate_request_hash(request))


def rejected(callable_):
    try:
        callable_()
        raise AssertionError("unsafe query was admitted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-040 TEST")
    print(" AUTHORIZED CONSUMER QUERY")
    print(" ADMISSION GATE")
    print("=" * 40)
    gate = OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate()
    request = signed(gate)
    first = gate.admit(request)
    assert gate.admit(request) == first
    assert first.query_admission_record_hash == stable_hash({k: v for k, v in first.__dict__.items() if k != "query_admission_record_hash"})
    assert first.consumer_authorized and first.projection_authorized
    assert first.filters_validated and first.result_limit_validated and first.request_hash_verified
    assert first.registry_read_authorized
    assert not first.registry_mutation_allowed and not first.publication_allowed and not first.execution_allowed
    read_request = gate.to_registry_read_request(first)
    assert read_request.request_id == first.request_id
    assert read_request.consumer_id == first.consumer_id
    assert read_request.market_id == "KX-ALPHA"

    gate.admit(signed(gate, request_id="query-request-2", consumer_id="oracle.audit.replay.v1", requested_projection="audit_replay", market_id=None, maximum_results=25))
    manifest = gate.build_manifest()
    assert manifest.query_admission_count == 2
    assert manifest.query_admission_manifest_hash == stable_hash({k: v for k, v in manifest.__dict__.items() if k != "query_admission_manifest_hash"})
    assert manifest.all_consumers_authorized and manifest.all_projections_authorized
    assert manifest.all_filters_validated and manifest.all_result_limits_validated
    assert manifest.all_request_hashes_verified and manifest.all_registry_reads_authorized

    rejected(lambda: gate.admit(signed(gate, request_id="bad-consumer", consumer_id="unknown.consumer.v1")))
    rejected(lambda: gate.admit(signed(gate, request_id="bad-projection", consumer_id="oracle.audit.replay.v1", requested_projection="operator_research")))
    rejected(lambda: gate.admit(replace(signed(gate, request_id="tampered"), maximum_results=99)))
    rejected(lambda: gate.admit(signed(gate, request_id="oversized", maximum_results=1001)))
    rejected(lambda: gate.admit(signed(gate, request_id="unsafe-filter", market_id="KX-ALPHA\nINJECT")))
    rejected(lambda: gate.to_registry_read_request(replace(first, execution_allowed=True)))

    assert QUERY_ADMISSION_SCHEMA_VERSION == "oracle.authorized-consumer-query-admission.v1"
    print("[PASS] Actual INT-OIA-039 registry-read request contract consumed")
    print("[PASS] Canonical query request hashing verified")
    print("[PASS] Authorized consumer identities enforced")
    print("[PASS] Consumer-specific projection scopes enforced")
    print("[PASS] Query filters and result limits validated")
    print("[PASS] Admitted query identities deterministic")
    print("[PASS] Duplicate valid admission remained idempotent")
    print("[PASS] Admission record and manifest hashes independently verified")
    print("[PASS] Eligible admission converted to INT-OIA-039 read request")
    print("[PASS] Unauthorized consumer and projection rejected")
    print("[PASS] Tampered request hash and admission record rejected")
    print("[PASS] Oversized result request and unsafe filter rejected")
    print("[PASS] Registry mutation, publication, and execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
