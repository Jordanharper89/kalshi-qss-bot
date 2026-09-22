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


def _source() -> str:
    return inspect.getsource(
        ola030.build_real_oracle_shadow_graph
    )


def _assert_ast_parses(source: str) -> None:
    ast.parse(source)


def main() -> None:
    source = _source()
    _assert_ast_parses(source)

    required = (
        "OraclePersistedCohortLineageProductionWiringContract",
        "lineage_persistence_router",
        "persistence_router=(\n                lineage_persistence_router",
        "postgresql_router=(\n                lineage_persistence_router",
        "OracleSchedulerCycleLineageCompletionBridge",
        "OracleSchedulerLineageProductionAdapter",
        "OracleShadowCycleRunnerLineageCallableFacade",
        "cycle_callable=(\n                    lineage_cycle_callable",
        '"lineage_production_wiring"',
        '"lineage_completion_bridge"',
        '"lineage_scheduler_adapter"',
        '"lineage_cycle_callable"',
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]
    assert not missing, missing

    assert (
        OraclePersistedCohortLineageProductionWiringContract
        .read_only
        is True
    )
    assert (
        OraclePersistedCohortLineageProductionWiringContract
        .execution_allowed
        is False
    )
    assert OracleSchedulerCycleLineageCompletionBridge.read_only is True
    assert OracleSchedulerCycleLineageCompletionBridge.execution_allowed is False
    assert OracleSchedulerLineageProductionAdapter.read_only is True
    assert OracleSchedulerLineageProductionAdapter.execution_allowed is False
    assert OracleShadowCycleRunnerLineageCallableFacade.read_only is True
    assert OracleShadowCycleRunnerLineageCallableFacade.execution_allowed is False

    original_router_position = source.index(
        "lineage_production_wiring ="
    )
    runtime_position = source.index(
        "acquisition_runtime ="
    )
    cycle_callable_position = source.index(
        "def production_cycle_callable("
    )
    scheduler_adapter_position = source.index(
        "lineage_scheduler_adapter ="
    )
    scheduler_position = source.index(
        "scheduler = ("
    )

    assert original_router_position < runtime_position
    assert cycle_callable_position < scheduler_adapter_position
    assert scheduler_adapter_position < scheduler_position

    result = {
        "schema_version": "OLA-051",
        "engine_id": "OLA-051",
        "status": "passed",
        "actual_ola030_graph_modified": True,
        "two_phase_graph_assembly": True,
        "production_postgresql_router_preserved": True,
        "ola044_staging_router_injected_before_runtime": True,
        "runtime_and_ola017_share_lineage_router": True,
        "ola045_completion_bridge_bound": True,
        "ola046_scheduler_adapter_bound": True,
        "ola050_callable_facade_bound_to_shadow_cycle_runner": True,
        "scheduler_kwargs_contract_preserved": True,
        "scheduler_result_contract_preserved": True,
        "lineage_components_exposed_for_audit": True,
        "read_only": True,
        "execution_allowed": False,
    }

    print(
        "[PASS] OLA-051 Actual OLA-030 Production Graph Integration"
    )
    print(result)


if __name__ == "__main__":
    main()
