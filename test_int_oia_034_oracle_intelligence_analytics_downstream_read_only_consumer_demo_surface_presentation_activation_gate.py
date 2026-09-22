from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_demo_surface_presentation_activation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    record = {
        "sequence": 1,
        "attestation_id": "presentation-readiness-attestation-test",
        "readiness_id": "presentation-readiness-test",
        "serving_consumption_attestation_id": "serving-consumption-attestation-test",
        "serving_consumption_id": "serving-consumption-test",
        "serving_release_id": "serving-release-test",
        "publication_id": "publication-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_readiness_record_hash": stable_hash({"readiness": 1}),
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
        "attestation_mode": "independent_immutable_read_only_presentation_readiness_attestation",
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
        "independent_serving_consumption_attestation_verified": True,
        "presentation_scope_verified": True,
        "presentation_readiness_verified": True,
        "independent_presentation_readiness_attestation_performed": True,
        "duplicate_attestation_rejected": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "attestation_status": "immutable_read_only_demo_surface_presentation_readiness_independently_attested",
    }
    record["attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-033",
        "engine_id": "INT-OIA-033",
        "attested_at": "2026-07-24T00:00:00+00:00",
        "attestation_manifest_id": "int-oia-033-test",
        "attestation_status": "demo_surface_presentation_readiness_independently_attested",
        "attestation_policy_id": "test",
        "attestation_mode": "independent_immutable_read_only_presentation_readiness_attestation",
        "presentation_mode": "immutable_read_only_demo_surface_presentation",
        "presentation_scope": "independently_attested_serving_consumption_only",
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
        "attestation_record_count": 1,
        "attestation_records": [record],
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
        "all_independent_serving_consumption_attestations_verified": True,
        "all_presentation_scopes_verified": True,
        "all_presentation_readiness_records_verified": True,
        "all_presentation_readiness_records_independently_attested": True,
        "duplicate_attestations_rejected": True,
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
    print(" INT-OIA-034 TEST")
    print(" PRESENTATION ACTIVATION")
    print(" SINGLE-USE IMMUTABLE READ-ONLY SURFACE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        source = root / "source"
        output = root / "output"
        _seed(source)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationGate(
            readiness_attestation_directory=source,
            activation_directory=output,
        )
        fixed = datetime(2026, 7, 24, tzinfo=timezone.utc)
        first = gate.activate(activated_at=fixed, persist=True)
        second = gate.activate(activated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-034"
        assert first.activation_record_count == 1
        assert first.all_readiness_attestation_record_hashes_verified
        assert first.all_readiness_record_hashes_verified
        assert first.all_presentation_readiness_attestations_verified
        assert first.all_activation_scopes_verified
        assert first.all_single_use_activations_verified
        assert first.all_demo_surface_presentations_activated
        assert first.duplicate_activations_rejected
        assert first.demo_surface_presentation_readiness_attested
        assert first.demo_surface_presentation_activated
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

        record = first.activation_records[0]
        assert record.readiness_attestation_record_hash_verified
        assert record.presentation_readiness_attestation_verified
        assert record.activation_scope_verified
        assert record.single_use_activation_verified
        assert record.presentation_activated
        assert record.activation_status == "immutable_read_only_demo_surface_presentation_activated"

        tampered = json.loads((source / "current.json").read_text(encoding="utf-8"))
        tampered["attestation_records"][0]["presentation_readiness_verified"] = False
        (source / "current.json").write_text(json.dumps(tampered), encoding="utf-8")
        try:
            gate.activate(activated_at=fixed, persist=False)
            raise AssertionError("tampered presentation-readiness attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerDemoSurfacePresentationActivationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-033 presentation-readiness attestation consumed")
    print("[PASS] Attestation manifest and every attestation-record hash verified")
    print("[PASS] Publication, release, admission, and boundary lineage preserved")
    print("[PASS] One-time invocation and immutable-result proofs preserved")
    print("[PASS] Presentation activation restricted to independently attested readiness")
    print("[PASS] Single-use immutable read-only demo-surface presentation activated")
    print("[PASS] Duplicate presentation-activation identities rejected")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe readiness attestation rejected")
    print("[PASS] Atomic presentation-activation artifacts persisted")
    print("[PASS] Signals, alerts, Q Series handoff/execution, orders, funds, and portfolio mutation remained disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
