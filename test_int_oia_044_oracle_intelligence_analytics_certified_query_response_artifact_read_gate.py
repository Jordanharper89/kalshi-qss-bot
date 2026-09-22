from __future__ import annotations

from dataclasses import replace

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import (
    ImmutableCertifiedQueryResponseArtifactEntry,
    ImmutableCertifiedQueryResponseArtifactRegistryManifest,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_certified_query_response_artifact_read_gate import (
    READ_RESULT_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate,
    OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError,
    stable_hash,
)


def _entry(
    sequence: int,
    *,
    consumer_id: str,
    projection: str,
) -> ImmutableCertifiedQueryResponseArtifactEntry:
    response_item = {
        "sequence": 1,
        "projected_entry": {
            "intelligence_product_id": stable_hash(
                {"product": sequence}
            ),
            "market_id": f"KX-{sequence:03d}",
            "venue_id": "kalshi",
        },
        "projected_entry_hash": stable_hash(
            {
                "intelligence_product_id": stable_hash(
                    {"product": sequence}
                ),
                "market_id": f"KX-{sequence:03d}",
                "venue_id": "kalshi",
            }
        ),
    }
    body = {
        "sequence": sequence,
        "response_artifact_entry_id": stable_hash(
            {"response-artifact-entry": sequence}
        ),
        "query_response_id": stable_hash(
            {"query-response": sequence}
        ),
        "query_response_record_hash": stable_hash(
            {"query-response-record": sequence}
        ),
        "source_query_execution_id": stable_hash(
            {"query-execution": sequence}
        ),
        "source_query_execution_record_hash": stable_hash(
            {"query-execution-record": sequence}
        ),
        "source_query_admission_id": stable_hash(
            {"query-admission": sequence}
        ),
        "source_request_id": f"request-{sequence}",
        "consumer_id": consumer_id,
        "requested_projection": projection,
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash(
            {"source-registry": 38}
        ),
        "source_read_result_hash": stable_hash(
            {"source-read-result": sequence}
        ),
        "matched_entry_count": 1,
        "certified_response_item_count": 1,
        "certified_response_items": (response_item,),
        "source_response_verified": True,
        "response_item_hashes_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "deterministic_ordering_verified": True,
        "deterministic_replay_verified": True,
        "immutable": True,
        "read_only": True,
        "response_artifact_persisted": True,
        "product_registry_mutation_allowed": False,
        "product_registry_mutation_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "response_artifact_entry_status": (
            "certified_query_response_registered_immutably"
        ),
    }
    return ImmutableCertifiedQueryResponseArtifactEntry(
        **body,
        response_artifact_entry_hash=stable_hash(body),
    )


def _manifest() -> ImmutableCertifiedQueryResponseArtifactRegistryManifest:
    entries = (
        _entry(
            1,
            consumer_id="oracle.operator.console.v1",
            projection="operator_research",
        ),
        _entry(
            2,
            consumer_id="oracle.research.presentation.v1",
            projection="research_presentation",
        ),
        _entry(
            3,
            consumer_id="oracle.operator.console.v1",
            projection="operator_research",
        ),
    )
    body = {
        "schema_version": "INT-OIA-043",
        "engine_id": "INT-OIA-043",
        "policy_id": (
            "oracle.intelligence.analytics.immutable-certified-query-response."
            "artifact-registry.v1"
        ),
        "response_artifact_registry_schema_version": (
            "oracle.immutable-certified-query-response-artifact-registry.v1"
        ),
        "response_artifact_registry_status": (
            "certified_query_responses_registered_immutably"
        ),
        "source_query_response_schema_version": (
            "oracle.authorized-consumer-query-response-certification.v1"
        ),
        "registry_manifest_id": stable_hash(
            {"registry-manifest": 43}
        ),
        "registry_entry_count": len(entries),
        "registry_entries": entries,
        "all_source_responses_verified": True,
        "all_response_item_hashes_verified": True,
        "all_source_hashes_verified": True,
        "all_lineage_verified": True,
        "all_entries_deterministic": True,
        "all_entries_replayable": True,
        "all_entries_immutable": True,
        "all_entries_read_only": True,
        "all_response_artifacts_persisted": True,
        "duplicate_registry_entries_present": False,
        "product_registry_mutation_allowed": False,
        "product_registry_mutation_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
    }
    return ImmutableCertifiedQueryResponseArtifactRegistryManifest(
        **body,
        response_artifact_registry_manifest_hash=stable_hash(body),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe certified response artifact read accepted")
    except OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-044 TEST")
    print(" CERTIFIED QUERY RESPONSE ARTIFACT")
    print(" READ GATE")
    print("=" * 40)

    gate = OracleIntelligenceAnalyticsCertifiedQueryResponseArtifactReadGate()
    manifest = _manifest()

    all_request = gate.create_request(
        registry_manifest=manifest,
        maximum_result_count=100,
    )
    first_all = gate.read(
        registry_manifest=manifest,
        read_request=all_request,
    )
    repeated_all = gate.read(
        registry_manifest=manifest,
        read_request=all_request,
    )

    assert first_all == repeated_all
    assert first_all.matched_entry_count == 3
    assert tuple(item.sequence for item in first_all.matched_entries) == (
        1,
        2,
        3,
    )

    operator_request = gate.create_request(
        registry_manifest=manifest,
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        maximum_result_count=1,
    )
    operator_result = gate.read(
        registry_manifest=manifest,
        read_request=operator_request,
    )
    assert operator_result.matched_entry_count == 1
    assert operator_result.matched_entries[0].sequence == 1

    exact_entry = manifest.registry_entries[1]
    exact_request = gate.create_request(
        registry_manifest=manifest,
        response_artifact_entry_id=(
            exact_entry.response_artifact_entry_id
        ),
        query_response_id=exact_entry.query_response_id,
    )
    exact_result = gate.read(
        registry_manifest=manifest,
        read_request=exact_request,
    )
    assert exact_result.matched_entries == (exact_entry,)

    assert first_all.read_result_hash == stable_hash(
        {
            key: value
            for key, value in first_all.__dict__.items()
            if key != "read_result_hash"
        }
    )
    assert first_all.registry_manifest_verified
    assert first_all.registry_entry_hashes_verified
    assert first_all.request_verified
    assert first_all.filters_applied_deterministically
    assert first_all.maximum_result_count_enforced
    assert first_all.immutable_read_verified
    assert first_all.source_hashes_verified
    assert first_all.lineage_verified
    assert first_all.deterministic_ordering_verified
    assert first_all.deterministic_replay_verified
    assert not first_all.registry_mutation_allowed
    assert not first_all.registry_mutation_performed
    assert not first_all.publication_allowed
    assert not first_all.publication_performed
    assert not first_all.order_execution_allowed
    assert not first_all.order_execution_performed
    assert not first_all.database_connection_performed
    assert not first_all.corpus_read_execution_repeated

    _expect_rejected(
        lambda: gate.read(
            registry_manifest=manifest,
            read_request=replace(
                all_request,
                mutation_allowed=True,
            ),
        )
    )
    _expect_rejected(
        lambda: gate.read(
            registry_manifest=manifest,
            read_request=replace(
                all_request,
                read_request_hash="0" * 64,
            ),
        )
    )
    _expect_rejected(
        lambda: gate.read(
            registry_manifest=replace(
                manifest,
                response_artifact_registry_manifest_hash="0" * 64,
            ),
            read_request=all_request,
        )
    )

    tampered_entry = replace(
        manifest.registry_entries[0],
        consumer_id="tampered.consumer",
    )
    tampered_entries = (
        tampered_entry,
        *manifest.registry_entries[1:],
    )
    tampered_body = {
        key: value
        for key, value in manifest.__dict__.items()
        if key != "response_artifact_registry_manifest_hash"
    }
    tampered_body["registry_entries"] = tampered_entries
    tampered_manifest = (
        ImmutableCertifiedQueryResponseArtifactRegistryManifest(
            **tampered_body,
            response_artifact_registry_manifest_hash=stable_hash(
                tampered_body
            ),
        )
    )
    _expect_rejected(
        lambda: gate.create_request(
            registry_manifest=tampered_manifest,
        )
    )

    assert READ_RESULT_SCHEMA_VERSION == (
        "oracle.certified-query-response-artifact-read-result.v1"
    )

    print("[PASS] Actual INT-OIA-043 registry contract consumed")
    print("[PASS] Registry manifest hash independently verified")
    print("[PASS] Every response artifact entry hash verified")
    print("[PASS] Deterministic read request created")
    print("[PASS] Full registry read completed immutably")
    print("[PASS] Consumer and projection filters applied")
    print("[PASS] Exact artifact and query-response filters applied")
    print("[PASS] Maximum result count enforced deterministically")
    print("[PASS] Deterministic replay and ordering verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-043 lineage preserved")
    print("[PASS] Tampered request evidence rejected")
    print("[PASS] Tampered manifest evidence rejected")
    print("[PASS] Tampered registry entry evidence rejected")
    print("[PASS] Registry and product mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
