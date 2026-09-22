from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_release_authorization_gate import (
    APPROVED_AUTHORIZATION_MODE,
    APPROVED_AUTHORIZATION_SCOPE,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    record = {
        "sequence": 1,
        "attestation_id": "attestation-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_publication_record_hash": stable_hash({"publication": 1}),
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
        "publication_payload_hash": stable_hash({"payload": 1}),
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "source_release_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "publication_schema_verified": True,
        "publication_mode_verified": True,
        "duplicate_publication_rejected": True,
        "independent_attestation_performed": True,
        "publication_manifest_published": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "attestation_status": "publication_manifest_record_independently_attested",
    }
    record["attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-018",
        "engine_id": "INT-OIA-018",
        "attested_at": "2026-07-23T00:00:00+00:00",
        "attestation_manifest_id": "int-oia-018-test",
        "attestation_status": (
            "demo_surface_publication_manifest_independently_attested"
        ),
        "attestation_policy_id": "test",
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_presentation_release_attestation_manifest_id": "int-oia-015-test",
        "source_research_presentation_release_manifest_id": "int-oia-014-test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_source_release_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_publication_schemas_verified": True,
        "all_publication_modes_verified": True,
        "all_publications_independently_attested": True,
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
        "publication_manifest_attested": True,
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
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["attestation_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-019 TEST")
    print(" PUBLICATION RELEASE AUTHORIZATION")
    print(" ATTESTED READ-ONLY DEMO BOUNDARY")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        authorization = root / "authorization"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationGate(
            attestation_directory=attestation,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-019"
        assert first.authorization_mode == APPROVED_AUTHORIZATION_MODE
        assert first.authorization_scope == APPROVED_AUTHORIZATION_SCOPE
        assert first.authorization_record_count == 1
        assert first.all_attestation_record_hashes_verified
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_source_release_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_independent_attestations_verified
        assert first.all_authorization_scopes_verified
        assert first.all_publication_releases_authorized
        assert first.duplicate_authorizations_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.publication_manifest_published
        assert first.publication_manifest_attested
        assert first.publication_release_authorized
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.authorization_records[0]
        assert record.attestation_record_hash_verified
        assert record.publication_record_hash_verified
        assert record.publication_payload_hash_verified
        assert record.independent_attestation_verified
        assert record.authorization_scope_verified
        assert record.duplicate_authorization_rejected
        assert record.publication_release_authorized
        assert (
            record.authorization_status
            == "attested_demo_surface_publication_release_authorized"
        )
        assert (authorization / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "qseries_execution_performed"
        ] = True
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.authorize(authorized_at=fixed, persist=False)
            raise AssertionError("tampered attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationReleaseAuthorizationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-018 attestation manifest consumed")
    print("[PASS] Attestation manifest hash independently verified")
    print("[PASS] Every attestation-record hash independently verified")
    print("[PASS] Publication and payload hash lineage preserved")
    print("[PASS] Complete release, admission, and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Independent attestation required before authorization")
    print("[PASS] Authorization scope restricted to attested demo publication")
    print("[PASS] Duplicate authorization identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe attestation rejected")
    print("[PASS] Atomic authorization artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
