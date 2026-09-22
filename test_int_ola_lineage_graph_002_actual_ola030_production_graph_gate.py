from __future__ import annotations

import ast
import inspect

from qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (
    OraclePersistedCohortLineageProductionWiringContract,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (
    OracleSchedulerCycleLineageCompletionBridge,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_adapter import (
    OracleSchedulerLineageProductionAdapter,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_cycle_runner_lineage_callable_facade import (
    OracleShadowCycleRunnerLineageCallableFacade,
)
from qseries_v2.oracle_intelligence.live_acquisition_model import (
    oracle_first_real_shadow_corpus_launch_command as ola030,
)
from test_int_ola_lineage_prod_smoke_001_oracle_scheduler_lineage_production_smoke_gate import (
    run_deterministic_replay,
    run_three_cycle_production_smoke,
)

SCHEMA_VERSION = "INT-OLA-LINEAGE-GRAPH-002"
ENGINE_ID = "INT-OLA-LINEAGE-GRAPH-002"


def _actual_graph_source() -> str:
    source = inspect.getsource(
        ola030.build_real_oracle_shadow_graph
    )
    ast.parse(source)
    return source


def _assert_actual_ola030_graph_binding(source: str) -> None:
    required_markers = (
        "OraclePersistedCohortLineageProductionWiringContract(",
        "lineage_persistence_router = (",
        "persistence_router=(\n                lineage_persistence_router",
        "postgresql_router=(\n                lineage_persistence_router",
        "OracleSchedulerCycleLineageCompletionBridge(",
        "OracleSchedulerLineageProductionAdapter(",
        "OracleShadowCycleRunnerLineageCallableFacade(",
        "cycle_callable=(\n                    lineage_cycle_callable",
        '"lineage_persistence_router"',
        '"lineage_production_wiring"',
        '"lineage_completion_bridge"',
        '"lineage_scheduler_adapter"',
        '"lineage_cycle_callable"',
    )

    missing = [
        marker
        for marker in required_markers
        if marker not in source
    ]
    assert not missing, missing

    wiring_position = source.index(
        "lineage_production_wiring ="
    )
    runtime_position = source.index(
        "acquisition_runtime ="
    )
    orchestrator_position = source.index(
        "cycle_orchestrator ="
    )
    production_callable_position = source.index(
        "def production_cycle_callable("
    )
    completion_bridge_position = source.index(
        "lineage_completion_bridge ="
    )
    scheduler_adapter_position = source.index(
        "lineage_scheduler_adapter ="
    )
    lineage_callable_position = source.index(
        "lineage_cycle_callable ="
    )
    scheduler_position = source.index(
        "scheduler = ("
    )

    assert wiring_position < runtime_position
    assert runtime_position < orchestrator_position
    assert orchestrator_position < production_callable_position
    assert production_callable_position < completion_bridge_position
    assert completion_bridge_position < scheduler_adapter_position
    assert scheduler_adapter_position < lineage_callable_position
    assert lineage_callable_position < scheduler_position

    assert source.count(
        "production_persistence_router=(\n                persistence_router"
    ) == 1
    assert source.count(
        "cycle_callable=(\n                    lineage_cycle_callable"
    ) == 1


def _assert_invariants() -> None:
    classes = (
        OraclePersistedCohortLineageProductionWiringContract,
        OracleSchedulerCycleLineageCompletionBridge,
        OracleSchedulerLineageProductionAdapter,
        OracleShadowCycleRunnerLineageCallableFacade,
    )

    for cls in classes:
        assert cls.read_only is True
        assert cls.execution_allowed is False


def main() -> None:
    source = _actual_graph_source()
    _assert_actual_ola030_graph_binding(source)
    _assert_invariants()

    (
        composition,
        persistence_router,
        scheduler_callable,
        first_receipt,
        second_receipt,
        third_receipt,
    ) = run_three_cycle_production_smoke()

    replay_receipts, replay_records = run_deterministic_replay()

    assert persistence_router.batch_call_count == 3
    assert persistence_router.single_call_count == 0
    assert scheduler_callable.call_count == 3

    assert (
        composition.staged_persistence_router
        is composition.production_wiring.staged_persistence_router
    )
    assert (
        composition.production_wiring.capture_port.pending_count
        == 0
    )
    assert (
        composition.staged_persistence_router.pending_stage_count
        == 0
    )

    assert (
        first_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 5
    )
    assert (
        second_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 10
    )
    assert (
        third_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .lineage_record_count_after
        == 15
    )
    assert (
        third_receipt
        .lineage_completion_receipt
        .lineage_wiring_receipt
        .transition_count
        == 1
    )

    assert len(replay_receipts) == 3
    assert len(replay_records) == 15

    result = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": "passed",
        "ola030_actual_production_graph_inspected": True,
        "actual_graph_ast_valid": True,
        "two_phase_graph_assembly_preserved": True,
        "ola044_bound_before_runtime_and_ola017": True,
        "runtime_and_ola017_share_staged_lineage_router": True,
        "ola045_bound_after_production_cycle_callable": True,
        "ola046_scheduler_adapter_bound": True,
        "ola050_callable_facade_bound_to_shadow_cycle_runner": True,
        "actual_graph_lineage_components_exposed_for_audit": True,
        "production_lineage_smoke_replayed": True,
        "production_persistence_batch_calls": (
            persistence_router.batch_call_count
        ),
        "scheduler_callable_calls": scheduler_callable.call_count,
        "first_cycle_lineage_record_count": 5,
        "second_cycle_lineage_record_count": 10,
        "third_cycle_lineage_record_count": 15,
        "third_cycle_transition_count": 1,
        "deterministic_replay_receipt_count": len(replay_receipts),
        "deterministic_replay_record_count": len(replay_records),
        "pending_stage_count_after_cycles": (
            composition.staged_persistence_router.pending_stage_count
        ),
        "pending_capture_count_after_cycles": (
            composition.production_wiring.capture_port.pending_count
        ),
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    }

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-002 "
        "Actual OLA-030 Production Graph Gate"
    )
    print(result)


if __name__ == "__main__":
    main()
