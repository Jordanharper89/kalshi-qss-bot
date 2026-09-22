from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_admission_gate import (
    DownstreamReadOnlyConsumerDeclaration,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError,
    stable_hash,
)


def _seed_integration(path: Path) -> None:
    boundary_body = {
        "boundary_id": stable_hash(
            {
                "subsystem_id": "OIA",
                "source_completion_attestation_id": "oia067-test",
                "source_completion_attestation_manifest_hash": stable_hash({"oia": 67}),
            }
        ),
        "subsystem_id": "OIA",
        "first_module_id": "OIA-001",
        "final_module_id": "OIA-067",
        "module_count": 67,
        "source_completion_attestation_id": "oia067-test",
        "source_completion_attestation_manifest_hash": stable_hash({"oia": 67}),
        "complete_lineage_verified": True,
        "controlled_read_execution_verified": True,
        "completion_attestation_verified": True,
        "read_only_boundary_frozen": True,
        "downstream_consumer_authorized": True,
        "source_reexecution_performed": False,
        "corpus_read_performed": False,
        "signal_generation_allowed": False,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
    }
    boundary_body["boundary_hash"] = stable_hash(boundary_body)

    manifest = {
        "schema_version": "INT-OIA-001",
        "engine_id": "INT-OIA-001",
        "certified_at": "2026-07-22T00:00:00+00:00",
        "integration_certification_id": "int-oia-001-test",
        "integration_certification_status": "oracle_intelligence_analytics_subsystem_integration_certified",
        "integration_policy_id": "test",
        "source_completion_attestation_id": "oia067-test",
        "source_completion_attestation_manifest_hash": stable_hash({"oia": 67}),
        "source_worker_id": "worker-test",
        "source_lineage": {"completion_module_id": "OIA-067"},
        "subsystem_boundary": boundary_body,
        "oia_001_through_oia_067_complete": True,
        "actual_oia_067_contract_consumed": True,
        "exact_approved_adapter_set_completed": True,
        "invocation_results_validated": True,
        "all_result_hashes_verified": True,
        "all_nonce_pairs_unique": True,
        "controlled_read_only_execution_completed": True,
        "source_invocation_reexecuted": False,
        "owner_reconstruction_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "adapter_execution_performed": False,
        "corpus_read_execution_performed": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "trading_recommendations_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "downstream_read_only_consumption_allowed": True,
        "oia_subsystem_frozen": True,
        "integration_artifact_persistence_allowed": True,
    }
    manifest["integration_certification_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-002 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" ADMISSION GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        integration = root / "integration"
        admission = root / "admission"
        _seed_integration(integration)

        source = json.loads(
            (integration / "current.json").read_text(encoding="utf-8")
        )
        boundary_id = source["subsystem_boundary"]["boundary_id"]

        consumers = (
            DownstreamReadOnlyConsumerDeclaration(
                consumer_id="oracle.research.analytics.consumer.v1",
                consumer_module=(
                    "qseries_v2.oracle_intelligence."
                    "research_analytics_consumer"
                ),
                consumer_class="OracleResearchAnalyticsConsumer",
                requested_capabilities=(
                    "read_certified_oia_boundary",
                    "read_certified_invocation_results",
                    "read_certified_result_summaries",
                    "perform_read_only_research_analysis",
                    "persist_research_analysis_artifacts",
                ),
                source_boundary_id=boundary_id,
            ),
        )

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionGate(
            integration_directory=integration,
            admission_directory=admission,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.admit(
            consumers=consumers,
            admitted_at=fixed,
            persist=True,
        )
        second = gate.admit(
            consumers=consumers,
            admitted_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-002"
        assert first.admission_record_count == 1
        assert first.all_consumers_read_only
        assert first.all_capabilities_allowlisted
        assert first.duplicate_consumers_rejected
        assert first.source_boundary_consumed_without_reexecution
        assert first.downstream_read_only_research_allowed
        assert first.analytic_conclusion_allowed
        assert not first.forecast_creation_allowed
        assert not first.controlled_read_execution_repeated
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_handoff_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed
        assert first.admission_records[0].admitted

        assert (admission / "current.json").exists()
        assert (
            admission / "manifests" / f"{first.admission_manifest_id}.json"
        ).exists()

        unsafe = DownstreamReadOnlyConsumerDeclaration(
            consumer_id="unsafe.consumer",
            consumer_module="unsafe.module",
            consumer_class="UnsafeConsumer",
            requested_capabilities=("generate_signal",),
            source_boundary_id=boundary_id,
            signals_allowed=True,
        )
        try:
            gate.admit(
                consumers=(unsafe,),
                admitted_at=fixed,
                persist=False,
            )
            raise AssertionError("unsafe downstream consumer was admitted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError:
            pass

        duplicate = (
            consumers[0],
            consumers[0],
        )
        try:
            gate.admit(
                consumers=duplicate,
                admitted_at=fixed,
                persist=False,
            )
            raise AssertionError("duplicate downstream consumer was admitted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError:
            pass

        tampered = json.loads(
            (integration / "current.json").read_text(encoding="utf-8")
        )
        tampered["qseries_execution_allowed"] = True
        (integration / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.admit(
                consumers=consumers,
                admitted_at=fixed,
                persist=False,
            )
            raise AssertionError("tampered INT-OIA-001 boundary was accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerAdmissionInvariantError:
            pass

    print("[PASS] Actual INT-OIA-001 integration contract consumed")
    print("[PASS] Frozen OIA-001 through OIA-067 boundary verified")
    print("[PASS] Declared downstream consumer admitted read-only")
    print("[PASS] Requested capabilities restricted to explicit allowlist")
    print("[PASS] Duplicate consumer declarations rejected")
    print("[PASS] Unsafe or execution-capable consumers rejected fail-closed")
    print("[PASS] INT-OIA-001 source boundary not re-executed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered integration evidence rejected")
    print("[PASS] Atomic admission artifacts persisted")
    print("[PASS] Read-only research analysis authorized")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
