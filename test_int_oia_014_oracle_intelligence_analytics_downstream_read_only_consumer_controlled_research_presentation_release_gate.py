from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_research_presentation_release_gate import (
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    PRESENTATION_SCHEMA,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError,
    stable_hash,
)


def _seed_admission(path: Path) -> None:
    result_payload = {
        "artifact_count": 2,
        "consumer_mode": "read_only_research",
        "evidence_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "read_only": True,
    }
    source_boundary_hash = stable_hash({"boundary": 1})
    admitted_result_hash = stable_hash(
        {
            "result_hash": stable_hash(result_payload),
            "result_payload": result_payload,
            "result_class": APPROVED_RESULT_CLASS,
            "release_mode": APPROVED_RELEASE_MODE,
            "source_boundary_id": "boundary-test",
            "source_boundary_hash": source_boundary_hash,
        }
    )

    record = {
        "sequence": 1,
        "result_admission_id": "result-admission-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "result_attestation_id": "result-attestation-test",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_result_attestation_record_hash": stable_hash(
            {"result-attestation": 1}
        ),
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result_payload),
        "admitted_result_hash": admitted_result_hash,
        "result_payload": result_payload,
        "result_class": APPROVED_RESULT_CLASS,
        "release_mode": APPROVED_RELEASE_MODE,
        "result_hash_verified": True,
        "attestation_lineage_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "result_schema_safe": True,
        "research_presentation_eligible": True,
        "signals_eligible": False,
        "alerts_eligible": False,
        "qseries_handoff_eligible": False,
        "qseries_execution_eligible": False,
        "market_order_creation_eligible": False,
        "funds_movement_eligible": False,
        "portfolio_mutation_eligible": False,
        "source_mutation_allowed": False,
        "downstream_release_authorized": True,
        "downstream_release_performed": False,
        "admission_status": "admitted_for_research_presentation_not_released",
    }
    record["result_admission_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-013",
        "engine_id": "INT-OIA-013",
        "admitted_at": "2026-07-22T00:00:00+00:00",
        "result_admission_manifest_id": "int-oia-013-test",
        "result_admission_status": (
            "downstream_read_only_consumer_controlled_result_admitted"
        ),
        "result_admission_policy_id": "test",
        "source_result_attestation_manifest_id": "int-oia-012-test",
        "source_result_attestation_manifest_hash": stable_hash(
            {"int": 12}
        ),
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": source_boundary_hash,
        "admission_record_count": 1,
        "admission_records": [record],
        "all_attestation_hashes_verified": True,
        "all_result_hashes_verified": True,
        "all_attestation_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "all_result_schemas_safe": True,
        "all_results_research_presentation_eligible": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "research_presentation_release_authorized": True,
        "downstream_release_performed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "admission_artifact_persistence_allowed": True,
    }
    manifest["result_admission_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-014 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" RESEARCH PRESENTATION RELEASE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admission = root / "admission"
        release = root / "release"
        _seed_admission(admission)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseGate(
            admission_directory=admission,
            release_directory=release,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.release(released_at=fixed, persist=True)
        second = gate.release(released_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-014"
        assert first.release_record_count == 1
        assert first.all_admission_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_attestation_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_presentation_schemas_verified
        assert first.all_releases_research_presentation_only
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_released
        assert not first.signals_created
        assert not first.alerts_created
        assert not first.qseries_handoff_performed
        assert not first.qseries_execution_performed
        assert not first.market_order_creation_performed
        assert not first.funds_movement_performed
        assert not first.portfolio_mutation_performed

        record = first.release_records[0]
        assert record.presentation_schema == PRESENTATION_SCHEMA
        assert record.result_class == APPROVED_RESULT_CLASS
        assert record.release_mode == APPROVED_RELEASE_MODE
        assert record.admission_hash_verified
        assert record.result_hash_verified
        assert record.attestation_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.presentation_schema_verified
        assert record.research_presentation_released
        assert record.presentation_payload["read_only"] is True
        assert record.presentation_payload["execution_disabled"] is True
        assert (
            record.release_status
            == "released_for_read_only_research_presentation"
        )

        assert (release / "current.json").exists()

        tampered = json.loads(
            (admission / "current.json").read_text(encoding="utf-8")
        )
        tampered["admission_records"][0][
            "qseries_execution_eligible"
        ] = True
        (admission / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.release(released_at=fixed, persist=False)
            raise AssertionError("tampered admission accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResearchPresentationReleaseInvariantError:
            pass

    print("[PASS] Actual INT-OIA-013 controlled admission consumed")
    print("[PASS] Every admission and result hash verified")
    print("[PASS] Complete attestation lineage preserved")
    print("[PASS] One-time invocation proof preserved")
    print("[PASS] Immutable result released through presentation schema")
    print("[PASS] Research presentation payload marked read-only")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe admission evidence rejected")
    print("[PASS] Atomic research-presentation artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series handoff/execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
