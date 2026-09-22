from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_execution_contract_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError,
    stable_hash,
)


CAPABILITIES = [
    "perform_read_only_research_analysis",
    "persist_research_analysis_artifacts",
    "read_certified_invocation_results",
    "read_certified_oia_boundary",
    "read_certified_result_summaries",
]


def _seed_admission(path: Path) -> None:
    record_body = {
        "sequence": 1,
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "requested_capabilities": CAPABILITIES,
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "read_only": True,
        "execution_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "source_mutation_allowed": False,
        "admitted": True,
        "admission_status": "admitted_read_only",
    }
    record_body["admission_record_hash"] = stable_hash(record_body)

    manifest = {
        "schema_version": "INT-OIA-002",
        "engine_id": "INT-OIA-002",
        "admitted_at": "2026-07-22T00:00:00+00:00",
        "admission_manifest_id": "int-oia-002-test",
        "admission_status": "downstream_read_only_consumers_admitted",
        "admission_policy_id": "test",
        "source_integration_certification_id": "int-oia-001-test",
        "source_integration_certification_manifest_hash": stable_hash({"int": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "admission_record_count": 1,
        "admission_records": [record_body],
        "all_consumers_read_only": True,
        "all_capabilities_allowlisted": True,
        "duplicate_consumers_rejected": True,
        "source_boundary_consumed_without_reexecution": True,
        "controlled_read_execution_repeated": False,
        "corpus_read_execution_repeated": False,
        "source_mutation_allowed": False,
        "source_mutation_performed": False,
        "analytic_conclusion_allowed": True,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "trading_recommendations_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "downstream_read_only_research_allowed": True,
        "admission_artifact_persistence_allowed": True,
    }
    manifest["admission_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-003 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" EXECUTION CONTRACT GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        admission = root / "admission"
        contracts = root / "contracts"
        _seed_admission(admission)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractGate(
            admission_directory=admission,
            contract_directory=contracts,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.issue(issued_at=fixed, persist=True)
        second = gate.issue(issued_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-003"
        assert first.execution_contract_count == 1
        assert first.admitted_consumers_only
        assert first.exact_capability_set_preserved
        assert first.deterministic_execution_required
        assert first.immutable_input_consumption_required
        assert first.replayable_output_required
        assert first.source_boundary_consumed_without_reexecution
        assert first.read_only_consumer_execution_authorized
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

        contract = first.execution_contracts[0]
        assert contract.read_only_required
        assert contract.deterministic_required
        assert contract.immutable_inputs_required
        assert contract.replayable_required
        assert contract.input_mode == "certified_artifacts_only"
        assert contract.output_mode == "immutable_research_artifacts_only"
        assert not contract.source_reexecution_allowed
        assert not contract.corpus_read_allowed
        assert not contract.signals_allowed
        assert not contract.qseries_execution_allowed

        assert (contracts / "current.json").exists()
        assert (
            contracts
            / "manifests"
            / f"{first.execution_contract_manifest_id}.json"
        ).exists()
        assert (
            contracts
            / "consumers"
            / contract.consumer_id
            / f"{contract.contract_id}.json"
        ).exists()

        tampered = json.loads(
            (admission / "current.json").read_text(encoding="utf-8")
        )
        tampered["admission_records"][0]["signals_allowed"] = True
        (admission / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.issue(issued_at=fixed, persist=False)
            raise AssertionError("tampered INT-OIA-002 admission was accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionContractInvariantError:
            pass

    print("[PASS] Actual INT-OIA-002 admission contract consumed")
    print("[PASS] Admitted consumer converted to exact execution contract")
    print("[PASS] Exact capability allowlist preserved")
    print("[PASS] Certified-artifact-only input mode enforced")
    print("[PASS] Immutable research-artifact output mode enforced")
    print("[PASS] Deterministic and replayable execution required")
    print("[PASS] Frozen OIA boundary consumed without re-execution")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe admission evidence rejected")
    print("[PASS] Atomic execution-contract artifacts persisted")
    print("[PASS] Read-only analytical conclusion production authorized")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
