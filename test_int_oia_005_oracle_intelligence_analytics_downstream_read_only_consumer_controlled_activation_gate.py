from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_controlled_activation_gate import (
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError,
    stable_hash,
)


CAPABILITIES = [
    "perform_read_only_research_analysis",
    "persist_research_analysis_artifacts",
    "read_certified_invocation_results",
    "read_certified_oia_boundary",
    "read_certified_result_summaries",
]


def _seed_readiness(path: Path) -> None:
    record_body = {
        "sequence": 1,
        "readiness_id": "readiness-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": CAPABILITIES,
        "certified_artifact_input_ready": True,
        "immutable_output_ready": True,
        "deterministic_execution_ready": True,
        "replayable_execution_ready": True,
        "read_only_execution_ready": True,
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
        "controlled_activation_allowed": True,
        "readiness_status": "ready_read_only",
    }
    record_body["readiness_record_hash"] = stable_hash(record_body)

    manifest = {
        "schema_version": "INT-OIA-004",
        "engine_id": "INT-OIA-004",
        "evaluated_at": "2026-07-22T00:00:00+00:00",
        "execution_readiness_manifest_id": "int-oia-004-test",
        "execution_readiness_status": (
            "downstream_read_only_consumer_execution_ready"
        ),
        "execution_readiness_policy_id": "test",
        "source_execution_contract_manifest_id": "int-oia-003-test",
        "source_execution_contract_manifest_hash": stable_hash({"int": 3}),
        "source_admission_manifest_id": "int-oia-002-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "readiness_record_count": 1,
        "readiness_records": [record_body],
        "all_contract_hashes_verified": True,
        "all_consumers_ready": True,
        "all_inputs_certified_artifact_only": True,
        "all_outputs_immutable_research_artifact_only": True,
        "deterministic_execution_required": True,
        "replayable_execution_required": True,
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
        "controlled_read_only_activation_allowed": True,
        "readiness_artifact_persistence_allowed": True,
    }
    manifest["execution_readiness_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-005 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CONTROLLED ACTIVATION GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        readiness = root / "readiness"
        activation = root / "activation"
        _seed_readiness(readiness)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationGate(
            readiness_directory=readiness,
            activation_directory=activation,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.activate(
            activated_at=fixed,
            persist=True,
        )
        second = gate.activate(
            activated_at=fixed,
            persist=False,
        )

        assert first == second
        assert first.schema_version == "INT-OIA-005"
        assert first.activation_record_count == 1
        assert first.all_readiness_hashes_verified
        assert first.all_consumers_activated_once
        assert first.all_activation_nonces_unique
        assert first.certified_artifact_input_mode_preserved
        assert first.immutable_output_mode_preserved
        assert first.deterministic_execution_required
        assert first.replayable_execution_required
        assert first.source_boundary_consumed_without_reexecution
        assert first.downstream_consumer_execution_allowed
        assert not first.downstream_consumer_execution_performed
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

        record = first.activation_records[0]
        assert record.one_time_activation
        assert record.readiness_consumed
        assert record.activation_mode == "controlled_one_time_read_only"
        assert record.activation_status == "activated_not_executed"
        assert not record.execution_performed
        assert not record.callable_binding_performed
        assert not record.callable_invocation_performed
        assert not record.corpus_read_performed
        assert not record.signals_allowed
        assert not record.qseries_execution_allowed

        assert (activation / "current.json").exists()
        assert (
            activation
            / "manifests"
            / f"{first.activation_manifest_id}.json"
        ).exists()
        assert (
            activation
            / "consumers"
            / record.consumer_id
            / f"{record.activation_id}.json"
        ).exists()

        tampered = json.loads(
            (readiness / "current.json").read_text(encoding="utf-8")
        )
        tampered["readiness_records"][0][
            "controlled_activation_allowed"
        ] = False
        (readiness / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.activate(
                activated_at=fixed,
                persist=False,
            )
            raise AssertionError(
                "tampered INT-OIA-004 readiness was accepted"
            )
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerControlledActivationInvariantError:
            pass

    print("[PASS] Actual INT-OIA-004 readiness contract consumed")
    print("[PASS] Every readiness-record hash independently verified")
    print("[PASS] One-time activation IDs and nonces deterministic")
    print("[PASS] Activation nonces unique across consumers")
    print("[PASS] Certified-artifact input mode preserved")
    print("[PASS] Immutable research-artifact output mode preserved")
    print("[PASS] Controlled read-only execution authorized")
    print("[PASS] Consumer execution not yet performed")
    print("[PASS] No callable binding or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe readiness evidence rejected")
    print("[PASS] Atomic activation artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
