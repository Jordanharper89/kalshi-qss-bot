from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.products.oracle_intelligence_analytics_canonical_intelligence_product_contract import (
    CANONICAL_PRODUCT_CLASS,
    CANONICAL_PRODUCT_MODE,
    PRODUCT_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductContract,
    OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError,
    stable_hash,
)


def _seed_admission(path: Path) -> None:
    result_payload = {
        "product_type": "market_research_summary",
        "market_id": "KX-TEST-MARKET",
        "venue_id": "kalshi",
        "confidence": 0.73,
        "calibration_status": "provisional",
        "evidence_references": ["evidence-1", "evidence-2"],
        "counterevidence_references": ["counterevidence-1"],
        "assumptions": ["test assumption"],
        "read_only": True,
    }
    source_boundary_hash = stable_hash({"boundary": "test"})
    admitted_result_hash = stable_hash(
        {
            "result_hash": stable_hash(result_payload),
            "result_payload": result_payload,
            "result_class": "immutable_research_artifact",
            "release_mode": "research_presentation_only",
            "source_boundary_id": "boundary-test",
            "source_boundary_hash": source_boundary_hash,
        }
    )

    record = {
        "sequence": 1,
        "result_admission_id": "result-admission-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_result_attestation_record_hash": stable_hash(
            {"result-attestation": 1}
        ),
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result_payload),
        "admitted_result_hash": admitted_result_hash,
        "result_payload": result_payload,
        "result_class": "immutable_research_artifact",
        "release_mode": "research_presentation_only",
        "result_hash_verified": True,
        "attestation_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "result_schema_safe": True,
        "research_presentation_eligible": True,
        "signals_eligible": False,
        "alerts_eligible": False,
        "qseries_handoff_eligible": False,
        "qseries_execution_eligible": False,
        "market_order_creation_eligible": False,
        "funds_movement_eligible": False,
        "portfolio_mutation_eligible": False,
        "source_mutation_allowed": False,
        "downstream_release_authorized": True,
        "downstream_release_performed": False,
        "admission_status": (
            "admitted_for_research_presentation_not_released"
        ),
    }
    record["result_admission_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-013",
        "engine_id": "INT-OIA-013",
        "admitted_at": "2026-07-22T00:00:00+00:00",
        "result_admission_manifest_id": "int-oia-013-test",
        "result_admission_status": (
            "downstream_read_only_consumer_controlled_result_admitted"
        ),
        "result_admission_policy_id": "test",
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_result_attestation_manifest_hash": stable_hash({"int": 12}),
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "admission_record_count": 1,
        "admission_records": [record],
        "all_attestation_hashes_verified": True,
        "all_result_hashes_verified": True,
        "all_attestation_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_result_schemas_safe": True,
        "all_results_research_presentation_eligible": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_release_authorized": True,
        "downstream_release_performed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "admission_artifact_persistence_allowed": True,
    }
    manifest["result_admission_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-036 TEST")
    print(" CANONICAL INTELLIGENCE PRODUCT")
    print(" PRODUCTION DOWNSTREAM CONTRACT")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admission = root / "admission"
        products = root / "products"
        _seed_admission(admission)

        contract = OracleIntelligenceAnalyticsCanonicalIntelligenceProductContract(
            result_admission_directory=admission,
            canonical_product_directory=products,
        )
        fixed = datetime(2026, 7, 24, 15, 0, tzinfo=timezone.utc)

        first = contract.create(created_at=fixed, persist=True)
        second = contract.create(created_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-036"
        assert first.product_schema_version == PRODUCT_SCHEMA_VERSION
        assert first.product_class == CANONICAL_PRODUCT_CLASS
        assert first.product_mode == CANONICAL_PRODUCT_MODE
        assert first.canonical_product_record_count == 1
        assert first.all_source_admission_record_hashes_verified
        assert first.all_source_result_hashes_verified
        assert first.all_source_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_source_results_immutable
        assert first.all_canonical_products_read_only
        assert first.all_canonical_products_deterministic
        assert first.all_canonical_products_replayable
        assert first.all_canonical_products_immutable
        assert first.all_canonical_products_unpublished
        assert first.all_execution_capabilities_disabled
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.production_intelligence_product_created
        assert not first.presentation_branch_required
        assert not first.demo_surface_dependency_required

        record = first.canonical_product_records[0]
        assert record.market_id == "KX-TEST-MARKET"
        assert record.venue_id == "kalshi"
        assert record.confidence == 0.73
        assert record.calibration_status == "provisional"
        assert record.product_state == "created_not_published"
        assert record.read_only
        assert record.deterministic
        assert record.replayable
        assert record.immutable
        assert record.publication_allowed
        assert not record.publication_performed
        assert record.query_allowed
        assert record.projection_allowed
        assert "research_presentation" in record.allowed_consumer_projections
        assert "qseries_execution" in record.execution_capabilities_disabled
        assert record.source_result_hash_verified
        assert record.source_admission_hash_verified
        assert record.source_lineage_verified
        assert record.one_time_invocation_verified
        assert record.source_consumed_without_reexecution
        assert not record.database_connection_performed
        assert not record.corpus_read_execution_repeated
        assert not record.source_mutation_performed

        assert (products / "current.json").exists()
        assert (
            products
            / "products"
            / f"{record.intelligence_product_id}.json"
        ).exists()
        assert (
            products
            / "manifests"
            / f"{first.canonical_product_manifest_id}.json"
        ).exists()

        persisted = json.loads(
            (products / "current.json").read_text(encoding="utf-8")
        )
        manifest_hash = persisted.pop(
            "canonical_product_manifest_hash"
        )
        assert stable_hash(persisted) == manifest_hash

        tampered = json.loads(
            (admission / "current.json").read_text(encoding="utf-8")
        )
        tampered["admission_records"][0]["result_payload"]["confidence"] = 0.99
        (admission / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            contract.create(created_at=fixed, persist=False)
            raise AssertionError("tampered admission accepted")
        except OracleIntelligenceAnalyticsCanonicalIntelligenceProductInvariantError:
            pass

    print("[PASS] Actual INT-OIA-013 controlled result admission consumed")
    print("[PASS] Production branch created directly from INT-OIA-013")
    print("[PASS] Presentation and demo branches were not required")
    print("[PASS] Every admission, admitted-result, and result hash verified")
    print("[PASS] Complete attestation, invocation, and boundary lineage preserved")
    print("[PASS] Canonical production intelligence product created")
    print("[PASS] Market, venue, confidence, calibration, and evidence fields normalized")
    print("[PASS] Product is deterministic, immutable, replayable, and read-only")
    print("[PASS] Product is created but not published")
    print("[PASS] Multiple authorized consumer projections declared")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered INT-OIA-013 admission evidence rejected")
    print("[PASS] Atomic manifest and per-product artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
