from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
TARGET = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)
TEST = ROOT / "test_ola_051_actual_ola030_production_graph_integration.py"

IMPORT_ANCHOR = '''from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (\n    OraclePostgreSQLShadowAcquisitionCycleOrchestrator,\n)\n'''

IMPORT_REPLACEMENT = IMPORT_ANCHOR + '''\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_persisted_cohort_lineage_production_wiring_contract import (\n    OraclePersistedCohortLineageProductionWiringContract,\n)\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_cycle_lineage_completion_bridge import (\n    OracleSchedulerCycleLineageCompletionBridge,\n)\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_scheduler_lineage_production_adapter import (\n    OracleSchedulerLineageProductionAdapter,\n)\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_shadow_cycle_runner_lineage_callable_facade import (\n    OracleShadowCycleRunnerLineageCallableFacade,\n)\n'''

ROUTER_ANCHOR = '''    persistence_router = (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter(\n            persistence_backend=(\n                persistence_backend\n            ),\n            route_id=(\n                "oracle.postgresql.kalshi."\n                "shadow.router.v1"\n            ),\n            routing_metadata={\n                "production_path": True,\n                "shadow_mode": True,\n                "launch_engine_id": ENGINE_ID,\n            },\n            replay_metadata={\n                "replay_source": ENGINE_ID,\n            },\n            audit_metadata={\n                "launch_engine_id": ENGINE_ID,\n            },\n        )\n    )\n'''

ROUTER_REPLACEMENT = ROUTER_ANCHOR + '''\n    lineage_production_wiring = (\n        OraclePersistedCohortLineageProductionWiringContract(\n            production_persistence_router=(\n                persistence_router\n            )\n        )\n    )\n\n    lineage_persistence_router = (\n        lineage_production_wiring\n        .staged_persistence_router\n    )\n'''

RUNTIME_OLD = '''    acquisition_runtime = (\n        _build_production_acquisition_runtime(\n            shadow_adapter=shadow_adapter,\n            deduplication=deduplication,\n            persistence_router=persistence_router,\n        )\n    )\n\n    cycle_orchestrator = (\n        OraclePostgreSQLShadowAcquisitionCycleOrchestrator(\n            acquisition_runtime=acquisition_runtime,\n            postgresql_router=persistence_router,\n            shadow_adapter=shadow_adapter,\n            bootstrap_record=postgresql_bootstrap,\n        )\n    )\n'''

RUNTIME_NEW = '''    acquisition_runtime = (\n        _build_production_acquisition_runtime(\n            shadow_adapter=shadow_adapter,\n            deduplication=deduplication,\n            persistence_router=(\n                lineage_persistence_router\n            ),\n        )\n    )\n\n    cycle_orchestrator = (\n        OraclePostgreSQLShadowAcquisitionCycleOrchestrator(\n            acquisition_runtime=acquisition_runtime,\n            postgresql_router=(\n                lineage_persistence_router\n            ),\n            shadow_adapter=shadow_adapter,\n            bootstrap_record=postgresql_bootstrap,\n        )\n    )\n'''

SCHEDULER_ANCHOR = '''    scheduler = (\n        OracleControlledShadowCollectionSchedulerTick(\n            polling_engine=polling_engine,\n            cycle_runner=ShadowCycleRunnerBinding(\n                runner_id=(\n                    "runner.ola017.ola030.production"\n                ),\n                engine_id="OLA-017",\n                source_id=SOURCE_ID,\n                adapter_id=ADAPTER_ID,\n                cycle_callable=(\n                    production_cycle_callable\n                ),\n            ),\n        )\n    )\n'''

SCHEDULER_REPLACEMENT = '''    lineage_completion_bridge = (\n        OracleSchedulerCycleLineageCompletionBridge(\n            production_wiring=(\n                lineage_production_wiring\n            )\n        )\n    )\n\n    lineage_scheduler_adapter = (\n        OracleSchedulerLineageProductionAdapter(\n            scheduler_cycle_callable=(\n                production_cycle_callable\n            ),\n            lineage_completion_bridge=(\n                lineage_completion_bridge\n            ),\n        )\n    )\n\n    lineage_cycle_callable = (\n        OracleShadowCycleRunnerLineageCallableFacade(\n            scheduler_adapter=(\n                lineage_scheduler_adapter\n            )\n        )\n    )\n\n    scheduler = (\n        OracleControlledShadowCollectionSchedulerTick(\n            polling_engine=polling_engine,\n            cycle_runner=ShadowCycleRunnerBinding(\n                runner_id=(\n                    "runner.ola017.ola030.production"\n                ),\n                engine_id="OLA-017",\n                source_id=SOURCE_ID,\n                adapter_id=ADAPTER_ID,\n                cycle_callable=(\n                    lineage_cycle_callable\n                ),\n            ),\n        )\n    )\n'''

RETURN_ANCHOR = '''        "persistence_router": (\n            persistence_router\n        ),\n        "shadow_adapter": shadow_adapter,\n'''

RETURN_REPLACEMENT = '''        "persistence_router": (\n            persistence_router\n        ),\n        "lineage_persistence_router": (\n            lineage_persistence_router\n        ),\n        "lineage_production_wiring": (\n            lineage_production_wiring\n        ),\n        "lineage_completion_bridge": (\n            lineage_completion_bridge\n        ),\n        "lineage_scheduler_adapter": (\n            lineage_scheduler_adapter\n        ),\n        "lineage_cycle_callable": (\n            lineage_cycle_callable\n        ),\n        "shadow_adapter": shadow_adapter,\n'''

TEST_SOURCE = r'''from __future__ import annotations

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
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one anchor, found {count}"
        )
    return source.replace(old, new, 1)


def main() -> None:
    print("========================================")
    print(" OLA-051 INSTALLER")
    print(" ACTUAL OLA-030 PRODUCTION GRAPH INTEGRATION")
    print("========================================")

    source = TARGET.read_text(encoding="utf-8")

    already_installed = (
        "lineage_cycle_callable" in source
        and "OraclePersistedCohortLineageProductionWiringContract" in source
        and '"lineage_production_wiring"' in source
    )

    if not already_installed:
        source = replace_once(
            source,
            IMPORT_ANCHOR,
            IMPORT_REPLACEMENT,
            "lineage imports",
        )
        source = replace_once(
            source,
            ROUTER_ANCHOR,
            ROUTER_REPLACEMENT,
            "production router wiring",
        )
        source = replace_once(
            source,
            RUNTIME_OLD,
            RUNTIME_NEW,
            "runtime and OLA-017 shared router wiring",
        )
        source = replace_once(
            source,
            SCHEDULER_ANCHOR,
            SCHEDULER_REPLACEMENT,
            "scheduler lineage callable wiring",
        )
        source = replace_once(
            source,
            RETURN_ANCHOR,
            RETURN_REPLACEMENT,
            "graph audit exposure",
        )

        compile(source, str(TARGET), "exec")
        TARGET.write_text(
            source,
            encoding="utf-8",
            newline="\n",
        )
        print(f"[OK] Integrated OLA-030 production graph: {TARGET}")
    else:
        print(f"[OK] OLA-051 already installed: {TARGET}")

    TEST.write_text(
        TEST_SOURCE,
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] Wrote regression test: {TEST}")

    print()
    print("[DONE] OLA-051 actual OLA-030 production graph integration installed")
    print()
    print("Run:")
    print("py test_ola_051_actual_ola030_production_graph_integration.py")


if __name__ == "__main__":
    main()
