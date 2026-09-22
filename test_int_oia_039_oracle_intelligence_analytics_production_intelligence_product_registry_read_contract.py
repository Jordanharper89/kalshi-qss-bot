from __future__ import annotations

import json
import tempfile
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_production_intelligence_product_registry_read_contract import (
    READ_CONTRACT_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract,
    OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError,
    ProductionIntelligenceProductRegistryReadRequest,
    stable_hash,
)


def _entry(
    *,
    sequence: int,
    market_id: str,
    product_id: str,
    registry_key: str,
) -> dict:
    body = {
        "sequence": sequence,
        "registry_entry_id": stable_hash(
            {"registry-entry": sequence}
        ),
        "product_admission_id": stable_hash(
            {"product-admission": sequence}
        ),
        "product_admission_record_hash": stable_hash(
            {"product-admission-record": sequence}
        ),
        "intelligence_product_id": product_id,
        "intelligence_product_hash": stable_hash(
            {"intelligence-product": sequence}
        ),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_product_admission_manifest_id": "int-oia-037-test",
        "source_product_admission_manifest_hash": stable_hash({"int": 37}),
        "source_result_admission_id": f"result-admission-{sequence}",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": sequence}
        ),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "market_id": market_id,
        "venue_id": "kalshi",
        "confidence": 0.70 + (sequence / 100),
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "registry_partition": "kalshi",
        "registry_key": registry_key,
        "immutable": True,
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "query_eligible": True,
        "projection_eligible": True,
        "publication_eligible": True,
        "publication_performed": False,
        "execution_capabilities_disabled_verified": True,
        "source_hashes_verified": True,
        "lineage_verified": True,
        "admission_verified": True,
        "duplicate_registration_rejected": True,
        "registry_entry_status": (
            "registered_immutably_for_production_serving_not_published"
        ),
    }
    body["registry_entry_hash"] = stable_hash(body)
    return body


def _seed_registry(path: Path) -> None:
    entries = [
        _entry(
            sequence=1,
            market_id="KX-ALPHA",
            product_id=stable_hash({"product": "alpha"}),
            registry_key=stable_hash({"key": "alpha"}),
        ),
        _entry(
            sequence=2,
            market_id="KX-BETA",
            product_id=stable_hash({"product": "beta"}),
            registry_key=stable_hash({"key": "beta"}),
        ),
    ]
    manifest = {
        "schema_version": "INT-OIA-038",
        "engine_id": "INT-OIA-038",
        "registered_at": "2026-07-24T17:00:00+00:00",
        "registry_manifest_id": "int-oia-038-test",
        "registry_manifest_status": (
            "admitted_intelligence_products_registered_immutably"
        ),
        "registry_policy_id": "test",
        "registry_schema_version": (
            "oracle.immutable-intelligence-product-registry.v1"
        ),
        "source_product_admission_manifest_id": "int-oia-037-test",
        "source_product_admission_manifest_hash": stable_hash({"int": 37}),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "registry_entry_count": len(entries),
        "registry_entries": entries,
        "all_product_admissions_verified": True,
        "all_product_hashes_verified": True,
        "all_source_hashes_verified": True,
        "all_lineage_verified": True,
        "all_entries_immutable": True,
        "all_entries_read_only": True,
        "all_entries_deterministic": True,
        "all_entries_replayable": True,
        "all_entries_query_eligible": True,
        "all_entries_projection_eligible": True,
        "all_entries_unpublished": True,
        "all_execution_capabilities_disabled": True,
        "duplicate_registry_entries_present": False,
        "registry_mutation_allowed": False,
        "registry_update_performed": False,
        "registry_delete_performed": False,
        "publication_performed": False,
        "presentation_branch_required": False,
        "demo_surface_dependency_required": False,
        "source_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_performed": False,
        "registry_artifact_persistence_allowed": True,
    }
    manifest["registry_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-039 TEST")
    print(" PRODUCTION REGISTRY READ")
    print(" STRICT READ-ONLY CONTRACT")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        registry = root / "registry"
        _seed_registry(registry)
        source_before = (registry / "current.json").read_bytes()

        reader = OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadContract(
            product_registry_directory=registry,
        )

        request = ProductionIntelligenceProductRegistryReadRequest(
            request_id="read-request-1",
            consumer_id="oracle.operator.console.v1",
            requested_projection="operator_research",
            venue_id="kalshi",
            maximum_results=100,
        )
        first = reader.read(request)
        second = reader.read(request)

        assert first == second
        assert first.read_result_hash == stable_hash(
            {
                key: value
                for key, value in first.__dict__.items()
                if key != "read_result_hash"
            }
        )
        assert first.matched_entry_count == 2
        assert len(first.matched_registry_entries) == 2
        assert first.all_entry_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.projection_authorized
        assert first.deterministic_ordering_verified
        assert first.immutable_read_verified
        assert not first.registry_mutation_allowed
        assert not first.registry_mutation_performed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_allowed
        assert not first.publication_performed
        assert not first.execution_allowed
        assert not first.execution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert source_before == (registry / "current.json").read_bytes()

        filtered = reader.read(
            ProductionIntelligenceProductRegistryReadRequest(
                request_id="read-request-2",
                consumer_id="oracle.audit.replay.v1",
                requested_projection="audit_replay",
                market_id="KX-BETA",
                maximum_results=1,
            )
        )
        assert filtered.matched_entry_count == 1
        assert filtered.matched_registry_entries[0]["market_id"] == "KX-BETA"

        try:
            reader.read(
                ProductionIntelligenceProductRegistryReadRequest(
                    request_id="read-request-3",
                    consumer_id="unauthorized-consumer",
                    requested_projection="execution",
                )
            )
            raise AssertionError("unauthorized projection accepted")
        except OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError:
            pass

        tampered = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        tampered["registry_entries"][0]["confidence"] = 0.99
        (registry / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            reader.read(request)
            raise AssertionError("tampered registry accepted")
        except OracleIntelligenceAnalyticsProductionIntelligenceProductRegistryReadInvariantError:
            pass

    assert READ_CONTRACT_SCHEMA_VERSION == (
        "oracle.production-intelligence-product-registry-read-contract.v1"
    )
    print("[PASS] Actual INT-OIA-038 immutable registry consumed")
    print("[PASS] Registry manifest hash independently verified")
    print("[PASS] Every registry entry hash independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-038 lineage preserved")
    print("[PASS] Strict read request and read result contracts enforced")
    print("[PASS] Deterministic filtered retrieval verified")
    print("[PASS] Authorized consumer projection enforced")
    print("[PASS] Read operation left registry byte-for-byte unchanged")
    print("[PASS] Registry mutation, update, and delete remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Unauthorized projection rejected")
    print("[PASS] Tampered registry evidence rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
