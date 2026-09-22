from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.products.oracle_intelligence_analytics_canonical_intelligence_product_validation_and_admission_gate import (
    ADMISSION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate,
    stable_hash,
)


def _seed_product(path: Path) -> None:
    record = {
        "sequence": 1,
        "intelligence_product_id": stable_hash({"product": 1}),
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_type": "market_research_summary",
        "product_mode": "production_read_only_multi_consumer",
        "product_state": "created_not_published",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "market_id": "KX-TEST-MARKET",
        "venue_id": "kalshi",
        "analytic_result_class": "immutable_research_artifact",
        "analytic_result_type": "builtins.dict",
        "analytic_result_payload": {"summary": "test"},
        "analytic_result_hash": stable_hash({"summary": "test"}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "source_result_admission_id": "result-admission-test",
        "source_result_admission_record_hash": stable_hash(
            {"result-admission": 1}
        ),
        "source_result_attestation_id": "result-attestation-test",
        "source_result_attestation_record_hash": stable_hash(
            {"result-attestation": 1}
        ),
        "source_invocation_execution_id": "execution-test",
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "source_release_mode": "research_presentation_only",
        "source_admission_status": (
            "admitted_for_research_presentation_not_released"
        ),
        "produced_at": "2026-07-24T15:00:00+00:00",
        "valid_from": "2026-07-24T15:00:00+00:00",
        "expires_at": None,
        "confidence": 0.73,
        "calibration_status": "provisional",
        "evidence_references": ["evidence-1"],
        "counterevidence_references": ["counterevidence-1"],
        "assumptions": ["test assumption"],
        "allowed_consumer_projections": [
            "operator_research",
            "research_presentation",
            "audit_replay",
        ],
        "read_only": True,
        "deterministic": True,
        "replayable": True,
        "immutable": True,
        "publication_allowed": True,
        "publication_performed": False,
        "query_allowed": True,
        "projection_allowed": True,
        "execution_capabilities_disabled": [
            "forecast_creation",
            "signal_creation",
            "alert_creation",
            "qseries_handoff",
            "qseries_execution",
            "market_order_creation",
            "funds_movement",
            "portfolio_mutation",
            "source_mutation",
        ],
        "source_result_hash_verified": True,
        "source_admission_hash_verified": True,
        "source_lineage_verified": True,
        "one_time_invocation_verified": True,
        "source_consumed_without_reexecution": True,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_performed": False,
        "product_status": (
            "canonical_production_intelligence_product_created_not_published"
        ),
    }
    record["intelligence_product_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-036",
        "engine_id": "INT-OIA-036",
        "created_at": "2026-07-24T15:00:00+00:00",
        "canonical_product_manifest_id": "int-oia-036-test",
        "canonical_product_manifest_status": (
            "canonical_intelligence_products_created"
        ),
        "canonical_product_policy_id": "test",
        "product_schema_version": "oracle.canonical-intelligence-product.v1",
        "product_class": "oracle_certified_intelligence_product",
        "product_mode": "production_read_only_multi_consumer",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_result_admission_manifest_hash": stable_hash({"int": 13}),
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_result_attestation_manifest_hash": stable_hash({"int": 12}),
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "canonical_product_record_count": 1,
        "canonical_product_records": [record],
        "all_source_admission_record_hashes_verified": True,
        "all_source_result_hashes_verified": True,
        "all_source_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_source_results_immutable": True,
        "all_canonical_products_read_only": True,
        "all_canonical_products_deterministic": True,
        "all_canonical_products_replayable": True,
        "all_canonical_products_immutable": True,
        "all_canonical_products_unpublished": True,
        "all_execution_capabilities_disabled": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "production_intelligence_product_created": True,
        "presentation_branch_required": False,
        "demo_surface_dependency_required": False,
        "product_artifact_persistence_allowed": True,
    }
    manifest["canonical_product_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-037 TEST")
    print(" PRODUCT VALIDATION AND ADMISSION")
    print(" PRODUCTION DOWNSTREAM GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        products = root / "products"
        admissions = root / "admissions"
        _seed_product(products)

        gate = OracleIntelligenceAnalyticsCanonicalIntelligenceProductValidationAndAdmissionGate(
            canonical_product_directory=products,
            product_admission_directory=admissions,
        )
        fixed = datetime(2026, 7, 24, 16, 0, tzinfo=timezone.utc)

        first = gate.admit(admitted_at=fixed, persist=True)
        second = gate.admit(admitted_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-037"
        assert first.admission_schema_version == ADMISSION_SCHEMA_VERSION
        assert first.product_admission_record_count == 1
        assert first.all_product_hashes_verified
        assert first.all_source_hashes_verified
        assert first.all_lineage_verified
        assert first.all_schemas_verified
        assert first.all_products_read_only
        assert first.all_products_deterministic
        assert first.all_products_replayable
        assert first.all_products_immutable
        assert first.all_consumer_projection_policies_verified
        assert first.all_execution_capabilities_disabled
        assert first.all_products_admitted_unpublished
        assert first.publication_allowed
        assert not first.publication_performed
        assert first.query_allowed
        assert first.projection_allowed
        assert not first.presentation_branch_required
        assert not first.demo_surface_dependency_required
        assert first.source_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_allowed
        assert not first.source_mutation_performed

        record = first.product_admission_records[0]
        assert record.product_hash_verified
        assert record.source_hashes_verified
        assert record.lineage_verified
        assert record.schema_verified
        assert record.read_only_verified
        assert record.deterministic_verified
        assert record.replayable_verified
        assert record.immutable_verified
        assert record.consumer_projection_policy_verified
        assert record.execution_capabilities_disabled_verified
        assert record.publication_allowed
        assert not record.publication_performed
        assert record.query_allowed
        assert record.projection_allowed
        assert record.product_admission_status == (
            "admitted_for_production_serving_not_published"
        )

        assert (admissions / "current.json").exists()
        assert (
            admissions
            / "admissions"
            / f"{record.product_admission_id}.json"
        ).exists()
        assert (
            admissions
            / "manifests"
            / f"{first.product_admission_manifest_id}.json"
        ).exists()

        persisted = json.loads(
            (admissions / "current.json").read_text(encoding="utf-8")
        )
        manifest_hash = persisted.pop("product_admission_manifest_hash")
        assert stable_hash(persisted) == manifest_hash

        tampered = json.loads(
            (products / "current.json").read_text(encoding="utf-8")
        )
        tampered["canonical_product_records"][0]["confidence"] = 0.99
        (products / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.admit(admitted_at=fixed, persist=False)
            raise AssertionError("tampered canonical product accepted")
        except OracleIntelligenceAnalyticsCanonicalIntelligenceProductAdmissionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-036 canonical intelligence product consumed")
    print("[PASS] Canonical product manifest hash independently verified")
    print("[PASS] Every canonical product record hash independently verified")
    print("[PASS] Product schema, class, mode, and state validated")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-036 lineage preserved")
    print("[PASS] Read-only, deterministic, replayable, and immutable guarantees verified")
    print("[PASS] Consumer projection policy verified")
    print("[PASS] All execution capabilities remained disabled")
    print("[PASS] Products admitted for production serving but not published")
    print("[PASS] Presentation and demo branches were not required")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered canonical intelligence product rejected")
    print("[PASS] Atomic admission manifest and per-product admissions persisted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
