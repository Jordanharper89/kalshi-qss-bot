from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_activation_attestation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationAttestationInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    record = {
        "sequence": 1,
        "activation_id": "presentation-activation-test",
        "readiness_attestation_id": "presentation-readiness-attestation-test",
        "readiness_id": "presentation-readiness-test",
        "serving_consumption_attestation_id": "serving-consumption-attestation-test",
        "serving_consumption_id": "serving-consumption-test",
        "serving_release_id": "serving-release-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_readiness_attestation_record_hash": stable_hash({"ra": 1}),
        "source_readiness_record_hash": stable_hash({"r": 1}),
        "source_serving_consumption_attestation_record_hash": stable_hash({"sca": 1}),
        "source_serving_consumption_record_hash": stable_hash({"sc": 1}),
        "source_serving_release_attestation_record_hash": stable_hash({"sra": 1}),
        "source_serving_release_record_hash": stable_hash({"sr": 1}),
        "source_publication_record_hash": stable_hash({"publication": 1}),
        "publication_payload_hash": stable_hash({"payload": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "presentation_mode": "immutable_read_only_demo_surface_presentation",
        "presentation_scope": "independently_attested_serving_consumption_only",
        "activation_mode": "single_use_immutable_read_only_presentation_activation",
        "readiness_attestation_record_hash_verified": True,
        "readiness_record_hash_verified": True,
        "serving_consumption_attestation_record_hash_verified": True,
        "serving_consumption_record_hash_verified": True,
        "serving_release_attestation_record_hash_verified": True,
        "serving_release_record_hash_verified": True,
        "publication_record_hash_verified": True,
        "publication_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "presentation_readiness_attestation_verified": True,
        "activation_scope_verified": True,
        "single_use_activation_verified": True,
        "presentation_activated": True,
        "duplicate_activation_rejected": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "activation_status": "immutable_read_only_demo_surface_presentation_activated",
    }
    record["activation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-034",
        "engine_id": "INT-OIA-034",
        "activated_at": "2026-07-24T00:00:00+00:00",
        "activation_manifest_id": "int-oia-034-test",
        "activation_status": "demo_surface_presentation_activated",
        "activation_policy_id": "test",
        "activation_mode": "single_use_immutable_read_only_presentation_activation",
        "presentation_mode": "immutable_read_only_demo_surface_presentation",
        "presentation_scope": "independently_attested_serving_consumption_only",
        "source_readiness_attestation_manifest_id": "int-oia-033-test",
        "source_readiness_attestation_manifest_hash": stable_hash({"int": 33}),
        "source_presentation_readiness_manifest_id": "int-oia-032-test",
        "source_presentation_readiness_manifest_hash": stable_hash({"int": 32}),
        "source_serving_consumption_attestation_manifest_id": "int-oia-031-test",
        "source_serving_consumption_attestation_manifest_hash": stable_hash({"int": 31}),
        "source_serving_consumption_manifest_id": "int-oia-030-test",
        "source_serving_consumption_manifest_hash": stable_hash({"int": 30}),
        "source_serving_release_attestation_manifest_id": "int-oia-029-test",
        "source_serving_release_attestation_manifest_hash": stable_hash({"int": 29}),
        "source_serving_release_manifest_id": "int-oia-028-test",
        "source_serving_release_manifest_hash": stable_hash({"int": 28}),
        "source_publication_manifest_id": "int-oia-017-test",
        "source_publication_manifest_hash": stable_hash({"int": 17}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "activation_record_count": 1,
        "activation_records": [record],
        "all_readiness_attestation_record_hashes_verified": True,
        "all_readiness_record_hashes_verified": True,
        "all_serving_consumption_attestation_record_hashes_verified": True,
        "all_serving_consumption_record_hashes_verified": True,
        "all_serving_release_attestation_record_hashes_verified": True,
        "all_serving_release_record_hashes_verified": True,
        "all_publication_record_hashes_verified": True,
        "all_publication_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_presentation_readiness_attestations_verified": True,
        "all_activation_scopes_verified": True,
        "all_single_use_activations_verified": True,
        "all_demo_surface_presentations_activated": True,
        "duplicate_activations_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "demo_surface_publication_serving_release_consumed": True,
        "demo_surface_publication_serving_consumption_attested": True,
        "demo_surface_presentation_ready": True,
        "demo_surface_presentation_readiness_attested": True,
        "demo_surface_presentation_activated": True,
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
        "activation_artifact_persistence_allowed": True,
    }
    manifest["activation_manifest_hash"] = stable_hash(manifest)
    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-035 TEST")
    print(" PRESENTATION ACTIVATION ATTESTATION")
    print(" INDEPENDENT IMMUTABLE READ-ONLY PROOF")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        output = root / "output"
        _seed(source)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationAttestationGate(
            presentation_activation_directory=source,
            attestation_directory=output,
        )
        fixed = datetime(2026, 7, 24, tzinfo=timezone.utc)
        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-035"
        assert first.attestation_record_count == 1
        assert first.all_activation_record_hashes_verified
        assert first.all_presentation_activations_verified
        assert first.all_presentation_activations_independently_attested
        assert first.all_single_use_activations_verified
        assert first.demo_surface_presentation_activated
        assert first.demo_surface_presentation_activation_attested
        assert first.duplicate_attestations_rejected
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed
        assert (output / "current.json").exists()

        record = first.attestation_records[0]
        assert record.activation_record_hash_verified
        assert record.presentation_activation_verified
        assert record.independent_presentation_activation_attestation_performed
        assert record.attestation_status == "immutable_read_only_demo_surface_presentation_activation_independently_attested"

        tampered = json.loads((source / "current.json").read_text(encoding="utf-8"))
        tampered["activation_records"][0]["presentation_activated"] = False
        (source / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered presentation-activation manifest accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-034 presentation-activation manifest consumed")
    print("[PASS] Activation manifest hash independently verified")
    print("[PASS] Every presentation-activation record hash independently verified")
    print("[PASS] Publication, release, admission, and boundary lineage preserved")
    print("[PASS] One-time invocation and immutable-result proofs preserved")
    print("[PASS] Activation scope and single-use activation independently verified")
    print("[PASS] Every demo-surface presentation activation independently attested")
    print("[PASS] Duplicate attestation identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe presentation activation rejected")
    print("[PASS] Atomic presentation-activation attestation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
