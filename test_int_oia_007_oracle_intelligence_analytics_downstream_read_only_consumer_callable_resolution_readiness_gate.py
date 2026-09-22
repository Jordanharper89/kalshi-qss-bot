from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.analytics.oracle_intelligence_analytics_downstream_read_only_consumer_callable_resolution_readiness_gate import (
    APPROVED_CALLABLE_NAME,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessGate,
    OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError,
    stable_hash,
)


def _seed_binding(path: Path) -> None:
    contract = {
        "sequence": 1,
        "binding_contract_id": "binding-test",
        "consumer_id": "oracle.research.analytics.consumer.v1",
        "consumer_module": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer"
        ),
        "consumer_class": "OracleResearchAnalyticsConsumer",
        "callable_name": APPROVED_CALLABLE_NAME,
        "callable_path": (
            "qseries_v2.oracle_intelligence."
            "research_analytics_consumer."
            "OracleResearchAnalyticsConsumer."
            "analyze_certified_oia_artifacts"
        ),
        "source_activation_id": "activation-test",
        "source_activation_nonce": stable_hash({"nonce": 1}),
        "source_activation_record_hash": stable_hash({"activation": 1}),
        "source_contract_id": "contract-test",
        "source_contract_hash": stable_hash({"contract": 1}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "authorized_capabilities": [
            "perform_read_only_research_analysis",
            "persist_research_analysis_artifacts",
            "read_certified_invocation_results",
            "read_certified_oia_boundary",
            "read_certified_result_summaries",
        ],
        "exact_callable_identity_required": True,
        "dynamic_import_allowed": False,
        "callable_resolution_allowed": False,
        "callable_binding_allowed": False,
        "callable_invocation_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
        "corpus_read_allowed": False,
        "source_mutation_allowed": False,
        "signals_allowed": False,
        "alerts_allowed": False,
        "qseries_execution_allowed": False,
        "market_order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
        "binding_status": "contract_issued_not_resolved",
    }
    contract["binding_contract_hash"] = stable_hash(contract)

    manifest = {
        "schema_version": "INT-OIA-006",
        "engine_id": "INT-OIA-006",
        "issued_at": "2026-07-22T00:00:00+00:00",
        "binding_manifest_id": "int-oia-006-test",
        "source_activation_manifest_id": "int-oia-005-test",
        "source_activation_manifest_hash": stable_hash({"int": 5}),
        "source_boundary_id": "boundary-test",
        "source_boundary_hash": stable_hash({"boundary": 1}),
        "binding_contract_count": 1,
        "binding_contracts": [contract],
        "all_activation_hashes_verified": True,
        "all_activation_nonces_unique": True,
        "exact_consumer_identity_preserved": True,
        "exact_callable_identity_frozen": True,
        "source_boundary_consumed_without_reexecution": True,
        "corpus_read_execution_repeated": False,
        "callable_resolution_allowed": False,
        "callable_binding_allowed": False,
        "callable_invocation_allowed": False,
        "callable_resolution_performed": False,
        "callable_binding_performed": False,
        "callable_invocation_performed": False,
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
        "binding_artifact_persistence_allowed": True,
    }
    manifest["binding_manifest_hash"] = stable_hash(manifest)

    path.mkdir(parents=True, exist_ok=True)
    (path / "current.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    print("=" * 40)
    print(" INT-OIA-007 TEST")
    print(" DOWNSTREAM READ-ONLY CONSUMER")
    print(" CALLABLE RESOLUTION READINESS")
    print("=" * 40)

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        binding = root / "binding"
        readiness = root / "readiness"
        _seed_binding(binding)

        gate = OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessGate(
            binding_directory=binding,
            readiness_directory=readiness,
        )
        fixed = datetime(2026, 7, 22, tzinfo=timezone.utc)

        first = gate.evaluate(evaluated_at=fixed, persist=True)
        second = gate.evaluate(evaluated_at=fixed, persist=False)

        assert first == second
        assert first.schema_version == "INT-OIA-007"
        assert first.readiness_record_count == 1
        assert first.all_binding_hashes_verified
        assert first.all_callable_paths_consistent
        assert first.exact_callable_identity_preserved
        assert first.source_boundary_consumed_without_reexecution
        assert not first.dynamic_import_allowed
        assert not first.module_import_performed
        assert first.callable_resolution_allowed
        assert not first.callable_resolution_performed
        assert not first.callable_binding_allowed
        assert not first.callable_binding_performed
        assert not first.callable_invocation_allowed
        assert not first.callable_invocation_performed
        assert not first.corpus_read_execution_repeated
        assert not first.source_mutation_performed
        assert first.controlled_callable_resolution_authorized
        assert not first.signals_allowed
        assert not first.alerts_allowed
        assert not first.qseries_execution_allowed
        assert not first.market_order_creation_allowed
        assert not first.funds_movement_allowed
        assert not first.portfolio_mutation_allowed

        record = first.readiness_records[0]
        assert record.module_identity_valid
        assert record.class_identity_valid
        assert record.callable_identity_valid
        assert record.callable_path_consistent
        assert record.exact_identity_hash_verified
        assert record.controlled_resolution_authorized
        assert not record.module_import_performed
        assert not record.callable_resolution_performed
        assert not record.callable_binding_performed
        assert not record.callable_invocation_performed

        assert (readiness / "current.json").exists()

        tampered = json.loads(
            (binding / "current.json").read_text(encoding="utf-8")
        )
        tampered["binding_contracts"][0][
            "callable_path"
        ] = "unsafe.module.UnsafeClass.execute"
        (binding / "current.json").write_text(
            json.dumps(tampered),
            encoding="utf-8",
        )
        try:
            gate.evaluate(evaluated_at=fixed, persist=False)
            raise AssertionError("tampered binding accepted")
        except OracleIntelligenceAnalyticsDownstreamReadOnlyConsumerCallableResolutionReadinessInvariantError:
            pass

    print("[PASS] Actual INT-OIA-006 binding contract consumed")
    print("[PASS] Every binding-contract hash independently verified")
    print("[PASS] Exact module, class, callable, and path identity verified")
    print("[PASS] Callable path consistency verified")
    print("[PASS] Controlled callable resolution authorized")
    print("[PASS] No dynamic import or module import performed")
    print("[PASS] No callable resolution, binding, or invocation performed")
    print("[PASS] No PostgreSQL connection or corpus read repeated")
    print("[PASS] Tampered or unsafe binding evidence rejected")
    print("[PASS] Atomic resolution-readiness artifacts persisted")
    print(
        "[PASS] Forecasts, signals, alerts, Q Series execution, orders, "
        "funds, and portfolio mutation remained disabled"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
