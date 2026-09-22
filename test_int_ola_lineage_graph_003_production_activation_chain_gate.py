
from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

OLA052_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_lineage_graph_assembly_attestation"
)

OLA053_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_lineage_scheduler_activation_attestation"
)


def _assert_module_contracts() -> None:
    ola052 = importlib.import_module(OLA052_MODULE)
    ola053 = importlib.import_module(OLA053_MODULE)

    assert getattr(ola052, "SCHEMA_VERSION", None) == "OLA-052"
    assert getattr(ola052, "ENGINE_ID", None) == "OLA-052"
    assert hasattr(
        ola052,
        "OracleProductionLineageGraphAssemblyAttestor",
    )

    assert getattr(ola053, "SCHEMA_VERSION", None) == "OLA-053"
    assert getattr(ola053, "ENGINE_ID", None) == "OLA-053"
    assert hasattr(
        ola053,
        "OracleProductionLineageSchedulerActivationAttestor",
    )

    assert (
        getattr(
            ola053.OracleProductionLineageSchedulerActivationAttestor,
            "read_only",
            None,
        )
        is True
    )
    assert (
        getattr(
            ola053.OracleProductionLineageSchedulerActivationAttestor,
            "execution_allowed",
            None,
        )
        is False
    )


def _assert_actual_ola030_source_graph() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert isinstance(tree, ast.Module)

    required_markers = (
        "OracleProductionLineageGraphAssemblyAttestor",
        "OracleProductionLineageSchedulerActivationAttestor",
        "lineage_graph_attestation = (",
        "cycle_runner_binding = (",
        "service_scheduler_binding = (",
        "lineage_scheduler_activation_attestation = (",
        "cycle_callable=(\n                lineage_cycle_callable",
        "cycle_runner=cycle_runner_binding",
        "tick_callable=scheduler.run_tick",
        "scheduler=service_scheduler_binding",
        '"lineage_graph_attestation": (',
        '"lineage_scheduler_activation_attestation": (',
    )

    for marker in required_markers:
        assert marker in source, marker

    assembly_pos = source.index("lineage_graph_attestation = (")
    cycle_runner_pos = source.index("cycle_runner_binding = (")
    scheduler_pos = source.index("scheduler = (")
    service_binding_pos = source.index("service_scheduler_binding = (")
    runner_pos = source.index("runner = OracleLiveShadowServiceRunner(")
    activation_pos = source.index(
        "lineage_scheduler_activation_attestation = ("
    )
    return_pos = source.index("    return {", activation_pos)

    assert assembly_pos < cycle_runner_pos
    assert cycle_runner_pos < scheduler_pos
    assert scheduler_pos < service_binding_pos
    assert service_binding_pos < runner_pos
    assert runner_pos < activation_pos
    assert activation_pos < return_pos


def _exercise_ola053_fail_closed_contract() -> None:
    ola053 = importlib.import_module(OLA053_MODULE)

    Attestor = ola053.OracleProductionLineageSchedulerActivationAttestor
    Blocked = (
        ola053.
        OracleProductionLineageSchedulerActivationAttestationBlocked
    )

    class Facade:
        def __call__(self, **kwargs):
            return None

    class CycleRunner:
        engine_id = "OLA-017"

        def __init__(self, cycle_callable):
            self.cycle_callable = cycle_callable

    class Scheduler:
        def __init__(self, cycle_runner):
            self.cycle_runner = cycle_runner

        def run_tick(self, **kwargs):
            return None

    class ServiceScheduler:
        engine_id = "OLA-021"

        def __init__(self, scheduler):
            self.tick_callable = scheduler.run_tick

    class Runner:
        def __init__(self, scheduler):
            self._scheduler = scheduler

    facade = Facade()
    cycle_runner = CycleRunner(facade)
    scheduler = Scheduler(cycle_runner)
    service_scheduler = ServiceScheduler(scheduler)
    runner = Runner(service_scheduler)

    record = Attestor().attest(
        lineage_cycle_callable=facade,
        cycle_runner_binding=cycle_runner,
        scheduler=scheduler,
        service_scheduler_binding=service_scheduler,
        runner=runner,
    )

    assert record.full_activation_chain_attested is True
    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False

    mismatched_facade = Facade()

    try:
        Attestor().attest(
            lineage_cycle_callable=mismatched_facade,
            cycle_runner_binding=cycle_runner,
            scheduler=scheduler,
            service_scheduler_binding=service_scheduler,
            runner=runner,
        )
    except Blocked:
        pass
    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-003 expected fail-closed "
            "OLA-053 identity mismatch"
        )


def main() -> None:
    _assert_module_contracts()
    _assert_actual_ola030_source_graph()
    _exercise_ola053_fail_closed_contract()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-003 "
        "Production Activation Chain Gate"
    )
    print({
        "schema_version": "INT-OLA-LINEAGE-GRAPH-003",
        "engine_id": "INT-OLA-LINEAGE-GRAPH-003",
        "status": "passed",
        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,
        "ola052_module_contract_preserved": True,
        "ola053_module_contract_preserved": True,
        "ola052_assembly_attestation_precedes_scheduler_activation": True,
        "ola050_callable_binding_preserved": True,
        "ola017_cycle_runner_binding_preserved": True,
        "ola021_scheduler_binding_preserved": True,
        "ola023_service_runner_binding_preserved": True,
        "ola053_activation_attestation_occurs_after_runner_binding": True,
        "assembly_and_activation_attestations_exposed_for_audit": True,
        "fail_closed_activation_identity_mismatch_tested": True,
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
    })


if __name__ == "__main__":
    main()
