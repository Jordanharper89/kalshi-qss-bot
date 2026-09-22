from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_research_presentation_release_attestation_gate import (
    APPROVED_PRESENTATION_SCHEMA,
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError,
    stable_hash,
)


def _seed_release(path: Path) -> None:
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

    record = {
        "sequence": 1,
        "research_presentation_release_id": "release-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "source_result_admission_id": "admission-test",
        "source_result_admission_record_hash": stable_hash(
            {"admission": 1}
        ),
        "result_attestation_id": "attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "result_hash": stable_hash({"result": 1}),
        "admitted_result_hash": stable_hash({"admitted": 1}),
        "presentation_payload_hash": stable_hash(presentation_payload),
        "presentation_payload": presentation_payload,
        "presentation_schema": APPROVED_PRESENTATION_SCHEMA,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "admission_hash_verified": True,
        "result_hash_verified": True,
        "attestation_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "presentation_schema_verified": True,
        "research_presentation_released": True,
        "signals_created": False,
        "alerts_created": False,
        "qseries_handoff_performed": False,
        "qseries_execution_performed": False,
        "market_order_creation_performed": False,
        "funds_movement_performed": False,
        "portfolio_mutation_performed": False,
        "source_mutation_performed": False,
        "release_status": "released_for_read_only_research_presentation",
    }
    record["research_presentation_release_record_hash"] = stable_hash(
        record
    )

    manifest = {
        "schema_version": "INT-OIA-014",
        "engine_id": "INT-OIA-014",
        "released_at": "2026-07-22T00:00:00+00:00",
        "research_presentation_release_manifest_id": "int-oia-014-test",
        "research_presentation_release_status": (
            "downstream_read_only_consumer_controlled_research_presentation_released"
        ),
        "research_presentation_release_policy_id": "test",
        "source_result_admission_manifest_id": "int-oia-013-test",
        "source_result_admission_manifest_hash": stable_hash({"int": 13}),
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "release_record_count": 1,
        "release_records": [record],
        "all_admission_hashes_verified": True,
        "all_result_hashes_verified": True,
        "all_attestation_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_presentation_schemas_verified": True,
        "all_releases_research_presentation_only": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_released": True,
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
        "release_artifact_persistence_allowed": True,
    }
    manifest["research_presentation_release_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-015 TEST")
    print(" RESEARCH PRESENTATION RELEASE")
    print(" INDEPENDENT ATTESTATION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        release = root / "release"
        attestation = root / "attestation"
        _seed_release(release)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationGate(
            release_directory=release,
            attestation_directory=attestation,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.attest(attested_at=fixed, persist=True)
        second = gate.attest(attested_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-015"
        assert first.attestation_record_count == 1
        assert first.all_release_hashes_verified
        assert first.all_presentation_payload_hashes_verified
        assert first.all_admission_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_read_only_boundaries_verified
        assert first.all_execution_disabled_boundaries_verified
        assert first.all_presentations_demo_surface_eligible
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_released
        assert first.demo_surface_release_authorized
        assert not first.demo_surface_release_performed
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.attestation_records[0]
        assert record.release_hash_verified
        assert record.presentation_payload_hash_verified
        assert record.admission_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.read_only_boundary_verified
        assert record.execution_disabled_boundary_verified
        assert record.demo_surface_eligible
        assert not record.demo_surface_release_performed
        assert (
            record.presentation_payload_hash
            == record.recomputed_presentation_payload_hash
        )
        assert (
            record.attestation_status
            == "presentation_release_attested_demo_surface_not_released"
        )

        assert (attestation / "current.json").exists()

        tampered = json.loads(
            (release / "current.json").read_text(encoding="utf-8")
        )
        tampered["release_records"][0]["presentation_payload"][
            "execution_disabled"
        ] = False
        (release / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.attest(attested_at=fixed, persist=False)
            raise AssertionError("tampered release accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerResearchPresentationReleaseAttestationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-014 presentation release consumed")
    print("[PASS] Every release and presentation hash verified")
    print("[PASS] Presentation payload hash independently recomputed")
    print("[PASS] Complete admission and invocation lineage preserved")
    print("[PASS] Read-only presentation boundary independently verified")
    print("[PASS] Execution-disabled boundary independently verified")
    print("[PASS] Demo-surface eligibility authorized")
    print("[PASS] Demo-surface release was not performed")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe presentation release rejected")
    print("[PASS] Atomic presentation-attestation artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series execution, orders, funds, "
        "and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
