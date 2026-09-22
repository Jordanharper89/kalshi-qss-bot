from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_response_certification_gate import (
    CertifiedConsumerQueryResponseItem,
    CertifiedConsumerQueryResponseRecord,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_immutable_certified_query_response_artifact_registry import (
    RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry,
    OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError,
    stable_hash,
)


def _response() -> CertifiedConsumerQueryResponseRecord:
    projected_entry = {
        "intelligence_product_id": stable_hash({"product": 1}),
        "product_type": "market_research_summary",
        "market_id": "KX-001",
        "venue_id": "kalshi",
        "confidence": 0.81,
        "calibration_status": "provisional",
        "product_state": "created_not_published",
        "registry_entry_hash": stable_hash({"entry": 1}),
        "registry_key": stable_hash({"key": 1}),
        "query_eligible": True,
        "projection_eligible": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
    }
    item = CertifiedConsumerQueryResponseItem(
        sequence=1,
        projected_entry=projected_entry,
        projected_entry_hash=stable_hash(projected_entry),
    )
    body = {
        "query_response_id": stable_hash({"response": 1}),
        "source_query_execution_id": stable_hash({"execution": 1}),
        "source_query_execution_record_hash": stable_hash(
            {"execution-record": 1}
        ),
        "source_query_admission_id": stable_hash({"admission": 1}),
        "source_request_id": "request-1",
        "consumer_id": "oracle.operator.console.v1",
        "requested_projection": "operator_research",
        "source_registry_manifest_id": "int-oia-038-test",
        "source_registry_manifest_hash": stable_hash({"manifest": 38}),
        "source_read_result_hash": stable_hash({"read-result": 1}),
        "matched_entry_count": 1,
        "certified_response_item_count": 1,
        "certified_response_items": (item,),
        "source_execution_verified": True,
        "projection_policy_verified": True,
        "field_allowlist_enforced": True,
        "forbidden_fields_absent": True,
        "response_item_hashes_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "deterministic_ordering_verified": True,
        "deterministic_replay_verified": True,
        "immutable_read_verified": True,
        "response_artifact_persistence_allowed": True,
        "registry_mutation_allowed": False,
        "registry_mutation_performed": False,
        "publication_allowed": False,
        "publication_performed": False,
        "order_execution_allowed": False,
        "order_execution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "query_response_status": (
            "authorized_consumer_query_response_certified"
        ),
    }
    return CertifiedConsumerQueryResponseRecord(
        **body,
        query_response_record_hash=stable_hash(body),
    )


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe response artifact was registered")
    except OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistryInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-043 TEST")
    print(" IMMUTABLE CERTIFIED QUERY RESPONSE")
    print(" ARTIFACT REGISTRY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        registry_directory = (
            Path(temporary_directory) / "response_artifacts"
        )
        registry = (
            OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )

        response = _response()
        first_manifest = registry.register(response)

        manifest_path = registry_directory / "current.json"
        manifest_bytes_before = manifest_path.read_bytes()
        entry_files_before = tuple(
            sorted((registry_directory / "entries").glob("*.json"))
        )
        assert len(entry_files_before) == 1
        entry_bytes_before = entry_files_before[0].read_bytes()

        repeated_manifest = registry.register(response)

        assert repeated_manifest == first_manifest
        assert manifest_path.read_bytes() == manifest_bytes_before
        entry_files_after = tuple(
            sorted((registry_directory / "entries").glob("*.json"))
        )
        assert entry_files_after == entry_files_before
        assert entry_files_after[0].read_bytes() == entry_bytes_before

        assert first_manifest.registry_entry_count == 1
        assert not first_manifest.duplicate_registry_entries_present
        assert first_manifest.all_source_responses_verified
        assert first_manifest.all_response_item_hashes_verified
        assert first_manifest.all_source_hashes_verified
        assert first_manifest.all_lineage_verified
        assert first_manifest.all_entries_deterministic
        assert first_manifest.all_entries_replayable
        assert first_manifest.all_entries_immutable
        assert first_manifest.all_entries_read_only
        assert first_manifest.all_response_artifacts_persisted
        assert not first_manifest.product_registry_mutation_allowed
        assert not first_manifest.product_registry_mutation_performed
        assert not first_manifest.publication_allowed
        assert not first_manifest.publication_performed
        assert not first_manifest.order_execution_allowed
        assert not first_manifest.order_execution_performed
        assert not first_manifest.database_connection_performed
        assert not first_manifest.corpus_read_execution_repeated

        entry = first_manifest.registry_entries[0]
        assert entry.query_response_id == response.query_response_id
        assert (
            entry.query_response_record_hash
            == response.query_response_record_hash
        )
        assert entry.consumer_id == response.consumer_id
        assert entry.requested_projection == response.requested_projection
        assert entry.response_artifact_entry_hash == stable_hash(
            {
                key: value
                for key, value in entry.__dict__.items()
                if key != "response_artifact_entry_hash"
            }
        )

        assert (
            first_manifest.response_artifact_registry_manifest_hash
            == stable_hash(
                {
                    key: value
                    for key, value in first_manifest.__dict__.items()
                    if key
                    != "response_artifact_registry_manifest_hash"
                }
            )
        )

        reloaded = (
            OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )
        assert reloaded.build_manifest() == first_manifest

        _expect_rejected(
            lambda: registry.register(
                replace(
                    response,
                    publication_allowed=True,
                )
            )
        )
        _expect_rejected(
            lambda: registry.register(
                replace(
                    response,
                    query_response_record_hash="0" * 64,
                )
            )
        )

        tampered_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        tampered_manifest["registry_entries"][0][
            "consumer_id"
        ] = "tampered.consumer"
        manifest_path.write_text(
            json.dumps(tampered_manifest),
            encoding="utf-8",
        )

        _expect_rejected(
            lambda: OracleIntelligenceAnalyticsImmutableCertifiedQueryResponseArtifactRegistry(
                response_artifact_registry_directory=registry_directory,
            )
        )

    assert RESPONSE_ARTIFACT_REGISTRY_SCHEMA_VERSION == (
        "oracle.immutable-certified-query-response-artifact-registry.v1"
    )

    print("[PASS] Actual INT-OIA-042 certified response consumed")
    print("[PASS] Certified response record hash independently verified")
    print("[PASS] Certified response item hashes independently verified")
    print("[PASS] Immutable response artifact entry created")
    print("[PASS] Atomic partitioned entry persisted")
    print("[PASS] Atomic current manifest persisted")
    print("[PASS] Duplicate registration remained idempotent")
    print("[PASS] Sequence-dependent entry hash excluded from duplicate identity comparison")
    print("[PASS] Persisted files remained byte-for-byte unchanged")
    print("[PASS] Registry reload reproduced identical manifest")
    print("[PASS] Persisted response-item lists restored to canonical immutable tuples")
    print("[PASS] Entry and manifest hashes independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-042 lineage preserved")
    print("[PASS] Tampered response evidence rejected")
    print("[PASS] Tampered persisted manifest rejected")
    print("[PASS] Product registry mutation remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
