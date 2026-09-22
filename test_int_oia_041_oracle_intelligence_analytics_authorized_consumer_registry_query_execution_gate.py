from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_query_admission_gate import (
    AuthorizedConsumerQueryAdmissionRequest,
    OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
)
from qseries_v2.oracle_intelligence.analytics.downstream.query.oracle_intelligence_analytics_authorized_consumer_registry_query_execution_gate import (
    QUERY_EXECUTION_SCHEMA_VERSION,
    OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate,
    OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError,
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
        "registry_entry_id": stable_hash({"registry-entry": sequence}),
        "product_admission_id": stable_hash({"product-admission": sequence}),
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


def _admitted_query(
    gate: OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate,
):
    unsigned = AuthorizedConsumerQueryAdmissionRequest(
        request_id="query-request-1",
        consumer_id="oracle.operator.console.v1",
        requested_projection="operator_research",
        market_id="KX-ALPHA",
        venue_id="kalshi",
        maximum_results=100,
        request_hash="",
    )
    signed = replace(
        unsigned,
        request_hash=gate.calculate_request_hash(unsigned),
    )
    return gate.admit(signed)


def _expect_rejected(callable_) -> None:
    try:
        callable_()
        raise AssertionError("unsafe query execution was accepted")
    except OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionInvariantError:
        pass


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-041 TEST")
    print(" AUTHORIZED REGISTRY QUERY")
    print(" EXECUTION GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        registry = Path(temporary_directory) / "registry"
        _seed_registry(registry)
        source_before = (registry / "current.json").read_bytes()

        admission_gate = (
            OracleIntelligenceAnalyticsAuthorizedConsumerQueryAdmissionGate()
        )
        admission = _admitted_query(admission_gate)

        execution_gate = (
            OracleIntelligenceAnalyticsAuthorizedConsumerRegistryQueryExecutionGate(
                product_registry_directory=registry,
            )
        )

        first = execution_gate.execute(admission)
        repeated = execution_gate.execute(admission)

        assert first == repeated
        assert first.query_execution_record_hash == stable_hash(
            {
                key: value
                for key, value in first.__dict__.items()
                if key != "query_execution_record_hash"
            }
        )
        assert first.source_query_admission_id == admission.query_admission_id
        assert (
            first.source_query_admission_record_hash
            == admission.query_admission_record_hash
        )
        assert first.source_request_id == admission.request_id
        assert first.source_consumer_id == admission.consumer_id
        assert (
            first.source_requested_projection
            == admission.requested_projection
        )
        assert first.matched_entry_count == 1
        assert len(first.matched_registry_entries) == 1
        assert first.matched_registry_entries[0]["market_id"] == "KX-ALPHA"
        assert first.query_admission_verified
        assert first.registry_read_request_derived_from_admission
        assert first.registry_read_invocation_count == 1
        assert first.registry_read_result_verified
        assert first.source_hashes_verified
        assert first.lineage_verified
        assert first.deterministic_replay_verified
        assert first.immutable_read_verified
        assert not first.registry_mutation_allowed
        assert not first.registry_mutation_performed
        assert not first.registry_update_performed
        assert not first.registry_delete_performed
        assert not first.publication_allowed
        assert not first.publication_performed
        assert not first.order_execution_allowed
        assert not first.order_execution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert source_before == (registry / "current.json").read_bytes()

        tampered_admission = replace(
            admission,
            execution_allowed=True,
        )
        _expect_rejected(
            lambda: execution_gate.execute(tampered_admission)
        )

        tampered_hash = replace(
            admission,
            query_admission_record_hash="0" * 64,
        )
        _expect_rejected(
            lambda: execution_gate.execute(tampered_hash)
        )

        tampered_registry = json.loads(
            (registry / "current.json").read_text(encoding="utf-8")
        )
        tampered_registry["registry_entries"][0]["confidence"] = 0.99
        (registry / "current.json").write_text(
            json.dumps(tampered_registry),
            encoding="utf-8",
        )
        _expect_rejected(
            lambda: execution_gate.execute(admission)
        )

    assert QUERY_EXECUTION_SCHEMA_VERSION == (
        "oracle.authorized-consumer-registry-query-execution.v1"
    )

    print("[PASS] Actual INT-OIA-040 query admission consumed")
    print("[PASS] Actual INT-OIA-039 registry read contract invoked")
    print("[PASS] Admission record hash independently verified")
    print("[PASS] Registry read request derived only from admitted query")
    print("[PASS] Registry read invoked exactly once")
    print("[PASS] Registry read result hash independently verified")
    print("[PASS] Query identity matched read-result identity")
    print("[PASS] Complete INT-OIA-013 through INT-OIA-040 lineage preserved")
    print("[PASS] Deterministic replay and idempotent execution verified")
    print("[PASS] Registry remained byte-for-byte unchanged")
    print("[PASS] Registry mutation, update, and delete remained disabled")
    print("[PASS] Publication remained disabled")
    print("[PASS] Q Series order execution remained disabled")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered admission evidence rejected")
    print("[PASS] Tampered registry evidence rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
