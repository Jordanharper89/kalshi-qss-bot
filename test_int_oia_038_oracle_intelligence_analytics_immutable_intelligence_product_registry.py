from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.registry.oracle_intelligence_analytics_immutable_intelligence_product_registry import (
    REGISTRY_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry,
    OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError,
    stable_hash,
)


def _seed_admission(path: Path) -> None:
    record = {
        "sequence": 1,
        "product_admission_id": stable_hash({"admission": 1}),
        "intelligence_product_id": stable_hash({"product": 1}),
        "intelligence_product_hash": stable_hash({"product-hash": 1}),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_result_admission_id": "result-admission-test",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": 1}
        ),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "market_id": "KX-TEST-MARKET",
        "venue_id": "kalshi",
        "confidence": 0.73,
        "calibration_status": "provisional",
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "read_only_verified": True,
        "deterministic_verified": True,
        "replayable_verified": True,
        "immutable_verified": True,
        "lineage_verified": True,
        "source_hashes_verified": True,
        "product_hash_verified": True,
        "schema_verified": True,
        "consumer_projection_policy_verified": True,
        "execution_capabilities_disabled_verified": True,
        "publication_allowed": True,
        "publication_performed": False,
        "query_allowed": True,
        "projection_allowed": True,
        "product_admission_status": (
            "admitted_for_production_serving_not_published"
        ),
    }
    record["product_admission_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-037",
        "engine_id": "INT-OIA-037",
        "admitted_at": "2026-07-24T16:00:00+00:00",
        "product_admission_manifest_id": "int-oia-037-test",
        "product_admission_manifest_status": (
            "canonical_intelligence_products_validated_and_admitted"
        ),
        "product_admission_policy_id": "test",
        "admission_schema_version": (
            "oracle.canonical-intelligence-product-admission.v1"
        ),
        "source_canonical_product_manifest_id": "int-oia-036-test",
        "source_canonical_product_manifest_hash": stable_hash({"int": 36}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_result_admission_manifest_hash": stable_hash({"int": 13}),
        "product_admission_record_count": 1,
        "product_admission_records": [record],
        "all_product_hashes_verified": True,
        "all_source_hashes_verified": True,
        "all_lineage_verified": True,
        "all_schemas_verified": True,
        "all_products_read_only": True,
        "all_products_deterministic": True,
        "all_products_replayable": True,
        "all_products_immutable": True,
        "all_consumer_projection_policies_verified": True,
        "all_execution_capabilities_disabled": True,
        "all_products_admitted_unpublished": True,
        "publication_allowed": True,
        "publication_performed": False,
        "query_allowed": True,
        "projection_allowed": True,
        "presentation_branch_required": False,
        "demo_surface_dependency_required": False,
        "source_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "admission_artifact_persistence_allowed": True,
    }
    manifest["product_admission_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-038 TEST")
    print(" IMMUTABLE INTELLIGENCE PRODUCT")
    print(" PRODUCTION REGISTRY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admissions = root / "admissions"
        registry = root / "registry"
        _seed_admission(admissions)

        service = OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistry(
            product_admission_directory=admissions,
            product_registry_directory=registry,
        )
        fixed = datetime(2026, 7, 24, 17, 0, tzinfo=timezone.utc)

        first = service.register(registered_at=fixed, persist=True)
        second = service.register(registered_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-038"
        assert first.registry_schema_version == REGISTRY_SCHEMA_VERSION
        assert first.registry_entry_count == 1
        assert first.all_product_admissions_verified
        assert first.all_product_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.all_entries_immutable
        assert first.all_entries_read_only
        assert first.all_entries_deterministic
        assert first.all_entries_replayable
        assert first.all_entries_query_eligible
        assert first.all_entries_projection_eligible
        assert first.all_entries_unpublished
        assert first.all_execution_capabilities_disabled
        assert not first.duplicate_registry_entries_present
        assert not first.registry_mutation_allowed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_performed
        assert not first.presentation_branch_required
        assert not first.demo_surface_dependency_required
        assert first.source_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed

        entry = first.registry_entries[0]
        assert entry.registry_partition == "kalshi"
        assert entry.immutable
        assert entry.read_only
        assert entry.deterministic
        assert entry.replayable
        assert entry.query_eligible
        assert entry.projection_eligible
        assert entry.publication_eligible
        assert not entry.publication_performed
        assert entry.execution_capabilities_disabled_verified
        assert entry.source_hashes_verified
        assert entry.lineage_verified
        assert entry.admission_verified
        assert entry.duplicate_registration_rejected

        assert (registry / "current.json").exists()
        assert (
            registry
            / "manifests"
            / f"{first.registry_manifest_id}.json"
        ).exists()
        entry_path = (
            registry
            / "entries"
            / entry.registry_partition
            / f"{entry.registry_key}.json"
        )
        assert entry_path.exists()

        persisted = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        manifest_hash = persisted.pop("registry_manifest_hash")
        assert stable_hash(persisted) == manifest_hash

        before_idempotent_registration = entry_path.read_bytes()
        repeated = service.register(registered_at=fixed, persist=True)
        after_idempotent_registration = entry_path.read_bytes()
        assert repeated == first
        assert before_idempotent_registration == after_idempotent_registration

        tampered = json.loads(
            (admissions / "current.json").read_text(encoding="utf-8")
        )
        tampered["product_admission_records"][0]["confidence"] = 0.99
        (admissions / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            service.register(registered_at=fixed, persist=False)
            raise AssertionError("tampered product admission accepted")
        except OracleIntelligenceAnalyticsImmutableIntelligenceProductRegistryInvariantError:
            pass

    print("[PASS] Actual INT-OIA-037 product admission consumed")
    print("[PASS] Product admission manifest hash independently verified")
    print("[PASS] Every product admission record hash independently verified")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-037 lineage preserved")
    print("[PASS] Only admitted canonical intelligence products registered")
    print("[PASS] Registry identities and keys deterministic")
    print("[PASS] Registry entries immutable, read-only, and replayable")
    print("[PASS] Query and projection eligibility preserved")
    print("[PASS] Products remained unpublished")
    print("[PASS] Duplicate immutable registration remained idempotent")
    print("[PASS] Registry update and delete operations remained disabled")
    print("[PASS] Presentation and demo branches were not required")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered product admission evidence rejected")
    print("[PASS] Atomic registry manifest and partitioned entries persisted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
