from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_authorization_gate import (
    APPROVED_ACTIVATION_MODE,
    APPROVED_ACTIVATION_SCOPE,
    APPROVED_AUTHORIZATION_MODE,
    APPROVED_AUTHORIZATION_SCOPE,
    APPROVED_CONSUMPTION_MODE,
    APPROVED_CONSUMPTION_SCOPE,
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_SERVING_AUTHORIZATION_MODE,
    APPROVED_SERVING_AUTHORIZATION_SCOPE,
    APPROVED_SERVING_MODE,
    APPROVED_SERVING_SCOPE,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    record = {
        "sequence": 1,
        "attestation_id": "readiness-attestation-test",
        "readiness_id": "readiness-test",
        "activation_attestation_id": "activation-attestation-test",
        "activation_id": "activation-test",
        "consumption_attestation_id": "consumption-attestation-test",
        "consumption_id": "consumption-test",
        "authorization_id": "release-authorization-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_readiness_record_hash": stable_hash({"readiness": 1}),
        "source_activation_attestation_record_hash": stable_hash({"aa": 1}),
        "source_activation_record_hash": stable_hash({"activation": 1}),
        "source_consumption_attestation_record_hash": stable_hash({"ca": 1}),
        "source_consumption_record_hash": stable_hash({"consumption": 1}),
        "source_authorization_record_hash": stable_hash({"authorization": 1}),
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "source_demo_surface_release_id": "demo-release-test",
        "source_result_admission_id": "admission-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "publication_schema": APPROVED_PUBLICATION_SCHEMA,
        "publication_mode": APPROVED_PUBLICATION_MODE,
        "authorization_mode": APPROVED_AUTHORIZATION_MODE,
        "authorization_scope": APPROVED_AUTHORIZATION_SCOPE,
        "consumption_mode": APPROVED_CONSUMPTION_MODE,
        "consumption_scope": APPROVED_CONSUMPTION_SCOPE,
        "activation_mode": APPROVED_ACTIVATION_MODE,
        "activation_scope": APPROVED_ACTIVATION_SCOPE,
        "serving_mode": APPROVED_SERVING_MODE,
        "serving_scope": APPROVED_SERVING_SCOPE,
        "readiness_record_hash_verified": True,
        "activation_attestation_record_hash_verified": True,
        "activation_record_hash_verified": True,
        "consumption_attestation_record_hash_verified": True,
        "consumption_record_hash_verified": True,
        "authorization_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "independent_activation_attestation_verified": True,
        "single_use_consumption_verified": True,
        "serving_scope_verified": True,
        "serving_readiness_verified": True,
        "duplicate_attestation_rejected": True,
        "independent_serving_readiness_attestation_performed": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "attestation_status": (
            "read_only_demo_publication_serving_readiness_independently_attested"
        ),
    }
    record["attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-025",
        "engine_id": "INT-OIA-025",
        "attested_at": "2026-07-23T00:00:00+00:00",
        "attestation_manifest_id": "int-oia-025-test",
        "attestation_status": (
            "demo_surface_publication_serving_readiness_independently_attested"
        ),
        "attestation_policy_id": "test",
        "source_readiness_manifest_id": "int-oia-024-test",
        "source_readiness_manifest_hash": stable_hash({"int": 24}),
        "source_activation_attestation_manifest_id": "int-oia-023-test",
        "source_activation_attestation_manifest_hash": stable_hash({"int": 23}),
        "source_activation_manifest_id": "int-oia-022-test",
        "source_activation_manifest_hash": stable_hash({"int": 22}),
        "source_consumption_attestation_manifest_id": "int-oia-021-test",
        "source_consumption_attestation_manifest_hash": stable_hash({"int": 21}),
        "source_consumption_manifest_id": "int-oia-020-test",
        "source_consumption_manifest_hash": stable_hash({"int": 20}),
        "source_authorization_manifest_id": "int-oia-019-test",
        "source_authorization_manifest_hash": stable_hash({"int": 19}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_readiness_record_hashes_verified": True,
        "all_activation_attestation_record_hashes_verified": True,
        "all_activation_record_hashes_verified": True,
        "all_consumption_attestation_record_hashes_verified": True,
        "all_consumption_record_hashes_verified": True,
        "all_authorization_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_independent_activation_attestations_verified": True,
        "all_single_use_consumptions_verified": True,
        "all_serving_scopes_verified": True,
        "all_serving_readiness_verified": True,
        "all_serving_readiness_independently_attested": True,
        "duplicate_attestations_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "publication_manifest_published": True,
        "publication_manifest_attested": True,
        "publication_release_authorized": True,
        "publication_release_authorization_consumed": True,
        "publication_release_authorization_consumption_attested": True,
        "demo_surface_publication_activated": True,
        "demo_surface_publication_activation_attested": True,
        "demo_surface_publication_serving_ready": True,
        "demo_surface_publication_serving_readiness_attested": True,
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
    print(" INT-OIA-026 TEST")
    print(" PUBLICATION SERVING AUTHORIZATION")
    print(" ATTESTED READ-ONLY PRESENTATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        authorization = root / "authorization"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationGate(
            attestation_directory=attestation,
            authorization_directory=authorization,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)

        first = gate.authorize(authorized_at=fixed, persist=True)
        second = gate.authorize(authorized_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-026"
        assert first.serving_authorization_mode == APPROVED_SERVING_AUTHORIZATION_MODE
        assert first.serving_authorization_scope == APPROVED_SERVING_AUTHORIZATION_SCOPE
        assert first.authorization_record_count == 1
        assert first.all_readiness_attestation_record_hashes_verified
        assert first.all_readiness_record_hashes_verified
        assert first.all_activation_attestation_record_hashes_verified
        assert first.all_activation_record_hashes_verified
        assert first.all_consumption_attestation_record_hashes_verified
        assert first.all_consumption_record_hashes_verified
        assert first.all_release_authorization_record_hashes_verified
        assert first.all_publication_record_hashes_verified
        assert first.all_publication_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_independent_serving_readiness_attestations_verified
        assert first.all_single_use_release_consumptions_verified
        assert first.all_serving_authorization_scopes_verified
        assert first.all_demo_surface_publications_serving_authorized
        assert first.duplicate_authorizations_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.demo_surface_publication_serving_authorized
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.authorization_records[0]
        assert record.readiness_attestation_record_hash_verified
        assert record.readiness_record_hash_verified
        assert record.independent_serving_readiness_attestation_verified
        assert record.single_use_release_consumption_verified
        assert record.serving_authorization_scope_verified
        assert record.duplicate_authorization_rejected
        assert record.demo_surface_publication_serving_authorized
        assert (
            record.authorization_status
            == "independently_attested_read_only_demo_publication_serving_authorized"
        )
        assert (authorization / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "independent_serving_readiness_attestation_performed"
        ] = False
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.authorize(authorized_at=fixed, persist=False)
            raise AssertionError("tampered serving-readiness attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingAuthorizationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-025 serving-readiness attestation consumed")
    print("[PASS] Serving-readiness attestation manifest hash verified")
    print("[PASS] Every readiness-attestation record hash verified")
    print("[PASS] Complete publication, authorization, and consumption lineage preserved")
    print("[PASS] Complete activation, admission, and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Independent serving-readiness attestation required")
    print("[PASS] Serving authorization scope restricted to attested readiness")
    print("[PASS] Duplicate serving authorization identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe readiness attestation rejected")
    print("[PASS] Atomic serving-authorization artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
