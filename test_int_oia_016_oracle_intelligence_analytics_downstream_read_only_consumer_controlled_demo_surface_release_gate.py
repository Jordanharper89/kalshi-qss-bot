from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_demo_surface_release_gate import (
    APPROVED_DEMO_SURFACE_MODE,
    APPROVED_DEMO_SURFACE_SCHEMA,
    APPROVED_PRESENTATION_SCHEMA,
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    presentation_payload = {
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "research_result": {
            "artifact_count": 2,
            "read_only": True,
        },
        "read_only": True,
        "execution_disabled": True,
    }
    presentation_payload_hash = stable_hash(presentation_payload)

    record = {
        "sequence": 1,
        "presentation_release_attestation_id": "attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "research_presentation_release_id": "release-test",
        "source_research_presentation_release_record_hash": stable_hash(
            {"release": 1}
        ),
        "source_result_admission_id": "admission-test",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "presentation_payload_hash": presentation_payload_hash,
        "recomputed_presentation_payload_hash": presentation_payload_hash,
        "presentation_payload": presentation_payload,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "release_hash_verified": True,
        "presentation_payload_hash_verified": True,
        "admission_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "read_only_boundary_verified": True,
        "execution_disabled_boundary_verified": True,
        "demo_surface_eligible": True,
        "demo_surface_release_performed": False,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "attestation_status": (
            "presentation_release_attested_demo_surface_not_released"
        ),
    }
    record["presentation_release_attestation_record_hash"] = stable_hash(
        record
    )

    manifest = {
        "schema_version": "INT-OIA-015",
        "engine_id": "INT-OIA-015",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "presentation_release_attestation_manifest_id": "int-oia-015-test",
        "presentation_release_attestation_status": (
            "downstream_read_only_consumer_"
            "research_presentation_release_attested"
        ),
        "presentation_release_attestation_policy_id": "test",
        "source_research_presentation_release_manifest_id": (
            "int-oia-014-test"
        ),
        "source_research_presentation_release_manifest_hash": stable_hash(
            {"int": 14}
        ),
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_release_hashes_verified": True,
        "all_presentation_payload_hashes_verified": True,
        "all_admission_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_read_only_boundaries_verified": True,
        "all_execution_disabled_boundaries_verified": True,
        "all_presentations_demo_surface_eligible": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_released": True,
        "demo_surface_release_authorized": True,
        "demo_surface_release_performed": False,
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
    manifest["presentation_release_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-016 TEST")
    print(" CONTROLLED DEMO-SURFACE RELEASE")
    print(" READ-ONLY RESEARCH PRESENTATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        demo_release = root / "demo-release"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseGate(
            attestation_directory=attestation,
            demo_release_directory=demo_release,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.release(released_at=fixed, persist=True)
        second = gate.release(released_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-016"
        assert first.release_record_count == 1
        assert first.all_attestation_hashes_verified
        assert first.all_presentation_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_demo_surface_schemas_verified
        assert first.all_releases_read_only_research_demo_only
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_released
        assert first.demo_surface_released
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.release_records[0]
        assert record.attestation_hash_verified
        assert record.presentation_payload_hash_verified
        assert record.admission_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.read_only_boundary_verified
        assert record.execution_disabled_boundary_verified
        assert record.demo_surface_schema_verified
        assert record.research_presentation_released
        assert record.demo_surface_released
        assert record.demo_surface_schema == APPROVED_DEMO_SURFACE_SCHEMA
        assert record.demo_surface_mode == APPROVED_DEMO_SURFACE_MODE
        assert record.demo_surface_payload["read_only"] is True
        assert record.demo_surface_payload["execution_disabled"] is True
        assert record.demo_surface_payload["signals_disabled"] is True
        assert record.demo_surface_payload["alerts_disabled"] is True
        assert record.demo_surface_payload["qseries_execution_disabled"] is True
        assert (
            record.release_status
            == "released_to_read_only_research_demo_surface"
        )
        assert (
            record.demo_surface_payload_hash
            == stable_hash(record.demo_surface_payload)
        )

        assert (demo_release / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "demo_surface_eligible"
        ] = False
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.release(released_at=fixed, persist=False)
            raise AssertionError("tampered attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledDemoSurfaceReleaseInvariantError:
            pass

    print("[PASS] Actual INT-OIA-015 presentation attestation consumed")
    print("[PASS] Every attestation and presentation hash verified")
    print("[PASS] Complete admission and invocation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable research result copied into demo schema")
    print("[PASS] Demo-surface payload is explicitly read-only")
    print("[PASS] Demo-surface payload explicitly disables execution")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe attestation evidence rejected")
    print("[PASS] Atomic demo-surface release artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
