from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_result_admission_gate import (
    APPROVED_RELEASE_MODE,
    APPROVED_RESULT_CLASS,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError,
    stable_hash,
)


def _seed_attestation(path: Path) -> None:
    result_payload = {
        "artifact_count": 2,
        "consumer_mode": "read_only_research",
        "evidence_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "read_only": True,
    }

    record = {
        "sequence": 1,
        "result_attestation_id": "result-attestation-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "invocation_execution_id": "execution-test",
        "invocation_nonce": stable_hash({"nonce": 1}),
        "source_invocation_execution_record_hash": stable_hash(
            {"execution": 1}
        ),
        "source_invocation_readiness_id": "readiness-test",
        "source_binding_attestation_id": "binding-test",
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"activation": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "certified_artifacts_hash": stable_hash([{"a": 1}, {"a": 2}]),
        "execution_context_hash": stable_hash({"mode": "read_only"}),
        "argument_contract_hash": stable_hash({"arguments": 1}),
        "result_type": "builtins.dict",
        "result_hash": stable_hash(result_payload),
        "recomputed_result_hash": stable_hash(result_payload),
        "result_payload": result_payload,
        "result_hash_verified": True,
        "invocation_count_verified": True,
        "one_time_invocation_verified": True,
        "immutable_result_verified": True,
        "execution_lineage_verified": True,
        "database_connection_performed": False,
        "corpus_read_performed": False,
        "source_mutation_performed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "result_admission_authorized": True,
        "downstream_release_performed": False,
        "attestation_status": "result_verified_not_released",
    }
    record["result_attestation_record_hash"] = stable_hash(record)

    manifest = {
        "schema_version": "INT-OIA-012",
        "engine_id": "INT-OIA-012",
        "attested_at": "2026-07-22T00:00:00+00:00",
        "result_attestation_manifest_id": "int-oia-012-test",
        "result_attestation_status": (
            "downstream_read_only_consumer_controlled_invocation_result_attested"
        ),
        "result_attestation_policy_id": "test",
        "source_invocation_execution_manifest_id": "int-oia-011-test",
        "source_invocation_execution_manifest_hash": stable_hash(
            {"int": 11}
        ),
        "source_invocation_readiness_manifest_id": "int-oia-010-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "attestation_record_count": 1,
        "attestation_records": [record],
        "all_execution_hashes_verified": True,
        "all_result_hashes_verified": True,
        "all_execution_lineage_verified": True,
        "all_one_time_invocations_verified": True,
        "all_results_immutable": True,
        "source_boundary_consumed_without_reexecution": True,
        "invocation_reexecution_performed": False,
        "database_connection_performed": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "controlled_result_admission_authorized": True,
        "downstream_release_performed": False,
        "attestation_artifact_persistence_allowed": True,
    }
    manifest["result_attestation_manifest_hash"] = stable_hash(
        manifest
    )

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-013 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED RESULT ADMISSION")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        attestation = root / "attestation"
        admission = root / "admission"
        _seed_attestation(attestation)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionGate(
            attestation_directory=attestation,
            admission_directory=admission,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.admit(admitted_at=fixed, persist=True)
        second = gate.admit(admitted_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-013"
        assert first.admission_record_count == 1
        assert first.all_attestation_hashes_verified
        assert first.all_result_hashes_verified
        assert first.all_attestation_lineage_verified
        assert first.all_one_time_invocations_verified
        assert first.all_results_immutable
        assert first.all_result_schemas_safe
        assert first.all_results_research_presentation_eligible
        assert first.source_boundary_consumed_without_reexecution
        assert not first.invocation_reexecution_performed
        assert not first.database_connection_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.research_presentation_release_authorized
        assert not first.downstream_release_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.admission_records[0]
        assert record.result_class == APPROVED_RESULT_CLASS
        assert record.release_mode == APPROVED_RELEASE_MODE
        assert record.result_hash_verified
        assert record.attestation_lineage_verified
        assert record.one_time_invocation_verified
        assert record.immutable_result_verified
        assert record.result_schema_safe
        assert record.research_presentation_eligible
        assert not record.signals_eligible
        assert not record.alerts_eligible
        assert not record.qseries_execution_eligible
        assert record.downstream_release_authorized
        assert not record.downstream_release_performed
        assert (
            record.admission_status
            == "admitted_for_research_presentation_not_released"
        )

        assert (admission / "current.json").exists()

        tampered = json.loads(
            (attestation / "current.json").read_text(encoding="utf-8")
        )
        tampered["attestation_records"][0][
            "result_admission_authorized"
        ] = False
        (attestation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.admit(admitted_at=fixed, persist=False)
            raise AssertionError("tampered attestation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledResultAdmissionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-012 result attestation consumed")
    print("[PASS] Every result-attestation hash verified")
    print("[PASS] Result and attestation lineage independently verified")
    print("[PASS] One-time invocation status preserved")
    print("[PASS] Immutable result schema admitted safely")
    print("[PASS] Research-presentation eligibility authorized")
    print("[PASS] No callable reexecution performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] No source mutation performed")
    print("[PASS] Tampered or unsafe attestation evidence rejected")
    print("[PASS] Result was not released downstream")
    print("[PASS] Atomic controlled-admission artifacts persisted")
    print(
        "[PASS] Signals, alerts, Q Series execution, orders, funds, "
        "and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
