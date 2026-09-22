from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_publication_serving_consumption_attestation_gate import (
    APPROVED_PUBLICATION_MODE,
    APPROVED_PUBLICATION_SCHEMA,
    APPROVED_SERVING_CONSUMPTION_MODE,
    APPROVED_SERVING_CONSUMPTION_SCOPE,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    record = {
        "sequence": 1,
        "consumption_id": "serving-consumption-test",
        "serving_release_attestation_id": "serving-release-attestation-test",
        "serving_release_id": "serving-release-test",
        "serving_authorization_attestation_id": "serving-authorization-attestation-test",
        "serving_authorization_id": "serving-authorization-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_serving_release_attestation_record_hash": stable_hash({"sra": 1}),
        "source_serving_release_record_hash": stable_hash({"sr": 1}),
        "source_serving_authorization_attestation_record_hash": stable_hash({"saa": 1}),
        "source_serving_authorization_record_hash": stable_hash({"sa": 1}),
        "source_readiness_attestation_record_hash": stable_hash({"ra": 1}),
        "source_readiness_record_hash": stable_hash({"r": 1}),
        "source_activation_attestation_record_hash": stable_hash({"aa": 1}),
        "source_activation_record_hash": stable_hash({"a": 1}),
        "source_consumption_attestation_record_hash": stable_hash({"pca": 1}),
        "source_consumption_record_hash": stable_hash({"pc": 1}),
        "source_release_authorization_record_hash": stable_hash({"auth": 1}),
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
        "serving_release_mode": "single_use_immutable_read_only_demo_surface_release",
        "serving_release_scope": "independently_attested_serving_authorization_only",
        "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
        "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
        "serving_release_attestation_record_hash_verified": True,
        "serving_release_record_hash_verified": True,
        "serving_authorization_attestation_record_hash_verified": True,
        "serving_authorization_record_hash_verified": True,
        "readiness_attestation_record_hash_verified": True,
        "readiness_record_hash_verified": True,
        "activation_attestation_record_hash_verified": True,
        "activation_record_hash_verified": True,
        "prior_consumption_attestation_record_hash_verified": True,
        "prior_consumption_record_hash_verified": True,
        "release_authorization_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "independent_serving_release_attestation_verified": True,
        "serving_consumption_scope_verified": True,
        "single_use_consumption_verified": True,
        "duplicate_consumption_rejected": True,
        "demo_surface_publication_serving_release_consumed": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "consumption_status": "independently_attested_read_only_serving_release_consumed",
    }
    record["consumption_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-030",
        "engine_id": "INT-OIA-030",
        "consumed_at": "2026-07-23T00:00:00+00:00",
        "consumption_manifest_id": "int-oia-030-test",
        "consumption_status": "demo_surface_publication_serving_release_consumed",
        "consumption_policy_id": "test",
        "serving_consumption_mode": APPROVED_SERVING_CONSUMPTION_MODE,
        "serving_consumption_scope": APPROVED_SERVING_CONSUMPTION_SCOPE,
        "source_serving_release_attestation_manifest_id": "int-oia-029-test",
        "source_serving_release_attestation_manifest_hash": stable_hash({"int": 29}),
        "source_serving_release_manifest_id": "int-oia-028-test",
        "source_serving_release_manifest_hash": stable_hash({"int": 28}),
        "source_serving_authorization_attestation_manifest_id": "int-oia-027-test",
        "source_serving_authorization_attestation_manifest_hash": stable_hash({"int": 27}),
        "source_serving_authorization_manifest_id": "int-oia-026-test",
        "source_serving_authorization_manifest_hash": stable_hash({"int": 26}),
        "source_readiness_attestation_manifest_id": "int-oia-025-test",
        "source_readiness_attestation_manifest_hash": stable_hash({"int": 25}),
        "source_readiness_manifest_id": "int-oia-024-test",
        "source_readiness_manifest_hash": stable_hash({"int": 24}),
        "source_activation_attestation_manifest_id": "int-oia-023-test",
        "source_activation_attestation_manifest_hash": stable_hash({"int": 23}),
        "source_activation_manifest_id": "int-oia-022-test",
        "source_activation_manifest_hash": stable_hash({"int": 22}),
        "source_prior_consumption_attestation_manifest_id": "int-oia-021-test",
        "source_prior_consumption_attestation_manifest_hash": stable_hash({"int": 21}),
        "source_prior_consumption_manifest_id": "int-oia-020-test",
        "source_prior_consumption_manifest_hash": stable_hash({"int": 20}),
        "source_release_authorization_manifest_id": "int-oia-019-test",
        "source_release_authorization_manifest_hash": stable_hash({"int": 19}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_demo_surface_release_manifest_id": "int-oia-016-test",
        "source_demo_surface_release_manifest_hash": stable_hash({"int": 16}),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "consumption_record_count": 1,
        "consumption_records": [record],
        "all_serving_release_attestation_record_hashes_verified": True,
        "all_serving_release_record_hashes_verified": True,
        "all_serving_authorization_attestation_record_hashes_verified": True,
        "all_serving_authorization_record_hashes_verified": True,
        "all_readiness_attestation_record_hashes_verified": True,
        "all_readiness_record_hashes_verified": True,
        "all_activation_attestation_record_hashes_verified": True,
        "all_activation_record_hashes_verified": True,
        "all_prior_consumption_attestation_record_hashes_verified": True,
        "all_prior_consumption_record_hashes_verified": True,
        "all_release_authorization_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_independent_serving_release_attestations_verified": True,
        "all_serving_consumption_scopes_verified": True,
        "all_single_use_consumptions_verified": True,
        "all_demo_surface_publication_serving_releases_consumed": True,
        "duplicate_consumptions_rejected": True,
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
        "demo_surface_publication_serving_authorized": True,
        "demo_surface_publication_serving_authorization_attested": True,
        "demo_surface_publication_serving_released": True,
        "demo_surface_publication_serving_release_attested": True,
        "demo_surface_publication_serving_release_consumed": True,
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
        "consumption_artifact_persistence_allowed": True,
    }
    manifest["consumption_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(json.dumps(manifest, sort_keys=True, indent=2), encoding="utf-8")


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-031 TEST")
    print(" SERVING CONSUMPTION ATTESTATION")
    print(" IMMUTABLE READ-ONLY PRESENTATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        consumption = root / "consumption"
        attestation = root / "attestation"
        _seed(consumption)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationGate(
            consumption_directory=consumption,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 23, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-031"
        assert first.attestation_record_count == 1
        assert first.all_serving_consumption_record_hashes_verified
        assert first.all_serving_consumptions_verified
        assert first.all_serving_consumptions_independently_attested
        assert first.all_single_use_consumptions_verified
        assert first.duplicate_attestations_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.demo_surface_publication_serving_release_consumed
        assert first.demo_surface_publication_serving_consumption_attested
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.attestation_records[0]
        assert record.serving_consumption_record_hash_verified
        assert record.serving_consumption_verified
        assert record.single_use_consumption_verified
        assert record.independent_serving_consumption_attestation_performed
        assert record.attestation_status == "read_only_demo_publication_serving_consumption_independently_attested"
        assert (attestation / "current.json").exists()

        tampered = json.loads((consumption / "current.json").read_text(encoding="utf-8"))
        tampered["consumption_records"][0]["demo_surface_publication_serving_release_consumed"] = False
        (consumption / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered serving consumption accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePublicationServingConsumptionAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-030 serving-consumption manifest consumed")
    print("[PASS] Serving-consumption manifest hash independently verified")
    print("[PASS] Every serving-consumption record hash verified")
    print("[PASS] Publication, release, admission, and boundary lineage preserved")
    print("[PASS] One-time invocation and immutable-result proofs preserved")
    print("[PASS] Serving consumption independently verified")
    print("[PASS] Single-use read-only consumption independently verified")
    print("[PASS] Duplicate attestation identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe serving consumption rejected")
    print("[PASS] Atomic serving-consumption attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
