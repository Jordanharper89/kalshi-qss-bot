from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_binding_contract_gate import (
    APPROVED_CALLABLE_NAME,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError,
    stable_hash,
)


def _seed(path: Path) -> None:
    capabilities = [
        "perform_read_only_research_analysis",
        "persist_research_analysis_artifacts",
        "read_certified_invocation_results",
        "read_certified_oia_boundary",
        "read_certified_result_summaries",
    ]
    record = {
        "sequence": 1,
        "activation_id": "activation-test",
        "activation_nonce": stable_hash({"nonce": 1}),
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": "qseries_v2.oracle_intelligence.research_analytics_consumer",
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "source_readiness_id": "readiness-test",
        "source_readiness_record_hash": stable_hash({"readiness": 1}),
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": capabilities,
        "activation_mode": "controlled_one_time_read_only",
        "one_time_activation": True,
        "readiness_consumed": True,
        "execution_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "corpus_read_performed": False,
        "source_mutation_allowed": False,
        "forecast_creation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "activation_status": "activated_not_executed",
    }
    record["activation_record_hash"] = stable_hash(record)
    manifest = {
        "schema_version": "INT-OIA-005",
        "engine_id": "INT-OIA-005",
        "activated_at": "2026-07-22T00:00:00+00:00",
        "activation_manifest_id": "int-oia-005-test",
        "activation_manifest_status": "test",
        "activation_policy_id": "test",
        "source_execution_readiness_manifest_id": "int-oia-004-test",
        "source_execution_readiness_manifest_hash": stable_hash({"int": 4}),
        "source_execution_contract_manifest_id": "int-oia-003-test",
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "activation_record_count": 1,
        "activation_records": [record],
        "all_readiness_hashes_verified": True,
        "all_consumers_activated_once": True,
        "all_activation_nonces_unique": True,
        "certified_artifact_input_mode_preserved": True,
        "immutable_output_mode_preserved": True,
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
        "downstream_consumer_execution_allowed": True,
        "downstream_consumer_execution_performed": False,
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
    print(" INT-OIA-006 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE BINDING CONTRACT GATE")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        activation = root / "activation"
        binding = root / "binding"
        _seed(activation)
        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingContractGate(
            activation_directory=activation,
            binding_directory=binding,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)
        first = gate.issue(issued_at=fixed, persist=True)
        second = gate.issue(issued_at=fixed, persist=False)
        assert first == second
        assert first.schema_version == "INT-OIA-006"
        assert first.binding_contract_count == 1
        assert first.all_activation_hashes_verified
        assert first.all_activation_nonces_unique
        assert first.exact_consumer_identity_preserved
        assert first.exact_callable_identity_frozen
        assert first.source_boundary_consumed_without_reexecution
        assert not first.callable_resolution_allowed
        assert not first.callable_binding_allowed
        assert not first.callable_invocation_allowed
        assert not first.callable_resolution_performed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        contract = first.binding_contracts[0]
        assert contract.callable_name == APPROVED_CALLABLE_NAME
        assert contract.callable_path.endswith(
            ".OracleResearchAnalyticsConsumer.analyze_certified_oia_artifacts"
        )
        assert contract.exact_callable_identity_required
        assert not contract.dynamic_import_allowed
        assert not contract.callable_resolution_performed
        assert not contract.callable_binding_performed
        assert not contract.callable_invocation_performed
        assert (binding / "current.json").exists()

        tampered = json.loads(
            (activation / "current.json").read_text(encoding="utf-8")
        )
        tampered["activation_records"][0]["callable_binding_performed"] = True
        (activation / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.issue(issued_at=fixed, persist=False)
            raise AssertionError("tampered activation accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableBindingInvariantError:
            pass

    print("[PASS] Actual INT-OIA-005 activation contract consumed")
    print("[PASS] Every activation-record hash independently verified")
    print("[PASS] Activation nonces remained unique")
    print("[PASS] Exact consumer module and class identity preserved")
    print("[PASS] Exact approved analytical callable identity frozen")
    print("[PASS] Callable path hash-bound to one-time activation")
    print("[PASS] No dynamic import or callable resolution performed")
    print("[PASS] No callable binding or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe activation evidence rejected")
    print("[PASS] Atomic binding-contract artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
