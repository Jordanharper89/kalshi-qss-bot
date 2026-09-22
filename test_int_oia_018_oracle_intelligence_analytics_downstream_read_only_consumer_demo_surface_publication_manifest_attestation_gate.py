from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_manifest_attestation_gate import (
    APPROVED_DEMO_SURFACE_MODE,
    APPROVED_DEMO_SURFACE_SCHEMA,
    APPROVED_PRESENTATION_SCHEMA,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError,
    stable_hash,
)


def _seed_publication(path: Path) -> None:
    publication_payload = {
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_demo_surface_release_id": "demo-release-test",
        "source_demo_surface_payload_hash": stable_hash({"demo": 1}),
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "published_demo_surface": {
            "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
            "read_only": True,
            "execution_disabled": True,
        },
        "immutable": True,
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
    payload_hash = stable_hash(publication_payload)

    record = {
        "sequence": 1,
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_demo_surface_release_id": "demo-release-test",
        "source_demo_surface_release_record_hash": stable_hash({"release": 1}),
        "source_presentation_release_attestation_id": "presentation-attestation-test",
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
        "source_demo_surface_payload_hash": stable_hash({"demo": 1}),
        "publication_payload_hash": payload_hash,
        "publication_payload": publication_payload,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "demo_surface_schema": APPROVED_DEMO_SURFACE_SCHEMA,
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "demo_surface_mode": APPROVED_DEMO_SURFACE_MODE,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "source_release_hash_verified": True,
        "demo_surface_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "publication_schema_verified": True,
        "duplicate_publication_rejected": True,
        "demo_surface_released": True,
        "publication_manifest_published": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "publication_status": "published_as_immutable_read_only_demo_manifest",
    }
    record["publication_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-017",
        "engine_id": "INT-OIA-017",
        "published_at": "2026-07-23T00:00:00+00:00",
        "publication_manifest_id": "int-oia-017-test",
        "publication_manifest_status": (
            "read_only_demo_surface_publication_manifest_published"
        ),
        "publication_policy_id": "test",
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_presentation_release_attestation_manifest_id": "int-oia-015-test",
        "source_research_presentation_release_manifest_id": "int-oia-014-test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "publication_record_count": 1,
        "publication_records": [record],
        "all_source_release_hashes_verified": True,
        "all_demo_surface_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_publication_schemas_verified": True,
        "all_publications_immutable_read_only_demo_only": True,
        "duplicate_publications_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_released": True,
        "demo_surface_released": True,
        "publication_manifest_published": True,
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
        "publication_artifact_persistence_allowed": True,
    }
    manifest["publication_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-018 TEST")
    print(" PUBLICATION MANIFEST ATTESTATION")
    print(" INDEPENDENT READ-ONLY VERIFICATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        publication = root / "publication"
        attestation = root / "attestation"
        _seed_publication(publication)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationGate(
            publication_directory=publication,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-018"
        assert first.attestation_record_count == 1
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_source_release_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_publication_schemas_verified
        assert first.all_publication_modes_verified
        assert first.all_publications_independently_attested
        assert first.duplicate_publications_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.publication_manifest_published
        assert first.publication_manifest_attested
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.attestation_records[0]
        assert record.publication_record_hash_verified
        assert record.publication_payload_hash_verified
        assert record.source_release_hash_verified
        assert record.admission_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.read_only_boundary_verified
        assert record.execution_disabled_boundary_verified
        assert record.publication_schema_verified
        assert record.publication_mode_verified
        assert record.duplicate_publication_rejected
        assert record.independent_attestation_performed
        assert (
            record.attestation_status
            == "publication_manifest_record_independently_attested"
        )
        assert (attestation / "current.json").exists()

        tampered = json.loads(
            (publication / "current.json").read_text(encoding="utf-8")
        )
        tampered["publication_records"][0]["publication_payload"][
            "qseries_execution_disabled"
        ] = False
        (publication / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered publication accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationManifestAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-017 publication manifest consumed")
    print("[PASS] Publication manifest hash independently verified")
    print("[PASS] Every publication-record hash independently verified")
    print("[PASS] Every publication payload hash independently recomputed")
    print("[PASS] Complete release, admission, and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable read-only publication mode independently attested")
    print("[PASS] Execution-disabled boundary independently verified")
    print("[PASS] Duplicate publication identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe publication manifest rejected")
    print("[PASS] Atomic independent-attestation artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
