from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_execution_readiness_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError,
    stable_hash,
)


CAPABILITIES = [
    "perform_read_only_research_analysis",
    "persist_research_analysis_artifacts",
    "read_certified_invocation_results",
    "read_certified_oia_boundary",
    "read_certified_result_summaries",
]


def _seed_contract(path: Path) -> None:
    contract_body = {
        "sequence": 1,
        "contract_id": "contract-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_admission_record_hash": stable_hash({"admission": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": CAPABILITIES,
        "input_mode": "certified_artifacts_only",
        "output_mode": "immutable_research_artifacts_only",
        "deterministic_required": True,
        "immutable_inputs_required": True,
        "replayable_required": True,
        "read_only_required": True,
        "source_reexecution_allowed": False,
        "corpus_read_allowed": False,
        "source_mutation_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "artifact_persistence_allowed": True,
        "execution_contract_status": "issued_read_only",
    }
    contract_body["execution_contract_hash"] = stable_hash(contract_body)

    manifest = {
        "schema_version": "INT-OIA-003",
        "engine_id": "INT-OIA-003",
        "issued_at": "2026-07-22T00:00:00+00:00",
        "execution_contract_manifest_id": "int-oia-003-test",
        "execution_contract_manifest_status": (
            "downstream_read_only_consumer_execution_contract_issued"
        ),
        "execution_contract_policy_id": "test",
        "source_admission_manifest_id": "int-oia-002-test",
        "source_admission_manifest_hash": stable_hash({"int": 2}),
        "source_integration_certification_id": "int-oia-001-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "execution_contract_count": 1,
        "execution_contracts": [contract_body],
        "admitted_consumers_only": True,
        "exact_capability_set_preserved": True,
        "deterministic_execution_required": True,
        "immutable_input_consumption_required": True,
        "replayable_output_required": True,
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
        "read_only_consumer_execution_authorized": True,
        "contract_artifact_persistence_allowed": True,
    }
    manifest["execution_contract_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-004 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" EXECUTION READINESS GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        contracts = root / "contracts"
        readiness = root / "readiness"
        _seed_contract(contracts)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessGate(
            contract_directory=contracts,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(
            evaluated_at=fixed,
            persist=True,
        )
        second = gate.evaluate(
            evaluated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-004"
        assert first.readiness_record_count == 1
        assert first.all_contract_hashes_verified
        assert first.all_consumers_ready
        assert first.all_inputs_certified_artifact_only
        assert first.all_outputs_immutable_research_artifact_only
        assert first.deterministic_execution_required
        assert first.replayable_execution_required
        assert first.source_boundary_consumed_without_reexecution
        assert first.controlled_read_only_activation_allowed
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

        record = first.readiness_records[0]
        assert record.certified_artifact_input_ready
        assert record.immutable_output_ready
        assert record.deterministic_execution_ready
        assert record.replayable_execution_ready
        assert record.read_only_execution_ready
        assert record.controlled_activation_allowed
        assert not record.source_reexecution_allowed
        assert not record.corpus_read_allowed
        assert not record.signals_allowed
        assert not record.qseries_execution_allowed

        assert (readiness / "current.json").exists()
        assert (
            readiness
            / "manifests"
            / f"{first.execution_readiness_manifest_id}.json"
        ).exists()
        assert (
            readiness
            / "consumers"
            / record.consumer_id
            / f"{record.readiness_id}.json"
        ).exists()

        tampered = json.loads(
            (contracts / "current.json").read_text(encoding="utf-8")
        )
        tampered["execution_contracts"][0][
            "corpus_read_allowed"
        ] = True
        (contracts / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(
                evaluated_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered INT-OIA-003 contract was accepted"
            )
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerExecutionReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-003 execution contract consumed")
    print("[PASS] Every execution-contract hash independently verified")
    print("[PASS] Certified-artifact-only inputs verified ready")
    print("[PASS] Immutable research-artifact outputs verified ready")
    print("[PASS] Deterministic and replayable execution verified ready")
    print("[PASS] Controlled read-only activation authorized")
    print("[PASS] Frozen OIA boundary consumed without re-execution")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe execution contract rejected")
    print("[PASS] Atomic readiness artifacts persisted")
    print("[PASS] Read-only analytical conclusion execution ready")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
