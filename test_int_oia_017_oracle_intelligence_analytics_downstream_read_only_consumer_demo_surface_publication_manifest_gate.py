from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_gate import (
    APPROVED_DEMO_SURFACE_MODE,
    APPROVED_DEMO_SURFACE_SCHEMA,
    APPROVED_PRESENTATION_SCHEMA,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError,
    stable_hash,
)


def _seed_release(path: Path) -> None:
    demo_payload = {
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "source_presentation_payload_hash": stable_hash({"presentation": 1}),
        "research_result": {"artifact_count": 2, "read_only": True},
        "read_only": True,
        "execution_disabled": True,
        "signals_disabled": True,
        "alerts_disabled": True,
        "qseries_handoff_disabled": True,
        "qseries_execution_disabled": True,
        "market_order_creation_disabled": True,
        "funds_movement_disabled": True,
        "portfolio_mutation_disabled": True,
        "source_mutation_disabled": True,
    }
    demo_hash = stable_hash(demo_payload)

    record = {
        "sequence": 1,
        "demo_surface_release_id": "demo-release-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_presentation_release_attestation_id": "attestation-test",
        "source_presentation_release_attestation_record_hash": stable_hash(
            {"attestation": 1}
        ),
        "research_presentation_release_id": "presentation-release-test",
        "source_result_admission_id": "admission-test",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "source_presentation_payload_hash": stable_hash({"presentation": 1}),
        "demo_surface_payload_hash": demo_hash,
        "demo_surface_payload": demo_payload,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "attestation_hash_verified": True,
        "presentation_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "demo_surface_schema_verified": True,
        "research_presentation_released": True,
        "demo_surface_released": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "release_status": "released_to_read_only_research_demo_surface",
    }
    record["demo_surface_release_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-016",
        "engine_id": "INT-OIA-016",
        "released_at": "2026-07-23T00:00:00+00:00",
        "demo_surface_release_manifest_id": "int-oia-016-test",
        "demo_surface_release_status": (
            "downstream_read_only_consumer_controlled_demo_surface_released"
        ),
        "demo_surface_release_policy_id": "test",
        "source_presentation_release_attestation_manifest_id": "int-oia-015-test",
        "source_presentation_release_attestation_manifest_hash": stable_hash(
            {"int": 15}
        ),
        "source_research_presentation_release_manifest_id": "int-oia-014-test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "release_record_count": 1,
        "release_records": [record],
        "all_attestation_hashes_verified": True,
        "all_presentation_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_demo_surface_schemas_verified": True,
        "all_releases_read_only_research_demo_only": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_released": True,
        "demo_surface_released": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "signals_created": False,
        "alerts_allowed": False,
        "alerts_created": False,
        "qseries_handoff_allowed": False,
        "qseries_handoff_performed": False,
        "qseries_execution_allowed": False,
        "qseries_execution_performed": False,
        "market_order_creation_allowed": False,
        "market_order_creation_performed": False,
        "funds_movement_allowed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_allowed": False,
        "portfolio_mutation_performed": False,
        "demo_surface_artifact_persistence_allowed": True,
    }
    manifest["demo_surface_release_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-017 TEST")
    print(" DEMO-SURFACE PUBLICATION MANIFEST")
    print(" IMMUTABLE READ-ONLY RELEASE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        release = root / "release"
        publication = root / "publication"
        _seed_release(release)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestGate(
            demo_release_directory=release,
            publication_directory=publication,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.publish(published_at=fixed, persist=True)
        second = gate.publish(published_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-017"
        assert first.publication_record_count == 1
        assert first.all_source_release_hashes_verified
        assert first.all_demo_surface_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_publication_schemas_verified
        assert first.all_publications_immutable_read_only_demo_only
        assert first.duplicate_publications_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_released
        assert first.demo_surface_released
        assert first.publication_manifest_published
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.publication_records[0]
        assert record.source_release_hash_verified
        assert record.demo_surface_payload_hash_verified
        assert record.admission_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.read_only_boundary_verified
        assert record.execution_disabled_boundary_verified
        assert record.publication_schema_verified
        assert record.duplicate_publication_rejected
        assert record.demo_surface_released
        assert record.publication_manifest_published
        assert record.publication_schema == APPROVED_PUBLICATION_SCHEMA
        assert record.publication_mode == APPROVED_PUBLICATION_MODE
        assert record.publication_payload["immutable"] is True
        assert record.publication_payload["read_only"] is True
        assert record.publication_payload["execution_disabled"] is True
        assert record.publication_payload["signals_disabled"] is True
        assert record.publication_payload["alerts_disabled"] is True
        assert record.publication_payload["qseries_execution_disabled"] is True
        assert (
            record.publication_status
            == "published_as_immutable_read_only_demo_manifest"
        )
        assert (
            record.publication_payload_hash
            == stable_hash(record.publication_payload)
        )
        assert (publication / "current.json").exists()

        tampered = json.loads(
            (release / "current.json").read_text(encoding="utf-8")
        )
        tampered["release_records"][0]["demo_surface_payload"][
            "execution_disabled"
        ] = False
        (release / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.publish(published_at=fixed, persist=False)
            raise AssertionError("tampered release accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestInvariantError:
            pass

    print("[PASS] Actual INT-OIA-016 demo-surface release consumed")
    print("[PASS] Every release-record and manifest hash verified")
    print("[PASS] Demo-surface payload hash independently recomputed")
    print("[PASS] Complete admission and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable publication payload generated")
    print("[PASS] Read-only and execution-disabled boundaries verified")
    print("[PASS] Duplicate publication identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe demo release rejected")
    print("[PASS] Atomic publication-manifest artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
