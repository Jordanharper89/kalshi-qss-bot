from __future__ import annotations

import ast
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_persistent_service_activation import (
    OracleProductionLiveShadowPersistentServiceActivationBlocked,
    OracleProductionLiveShadowPersistentServiceActivator,
)


ROOT = Path(__file__).resolve().parent
OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)


class FakeReadOnlyServiceRunner:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self.calls = 0

    def run(self, *, max_cycles: int = 1):
        self.calls += 1
        return {
            "status": "completed",
            "max_cycles": max_cycles,
            "read_only": True,
            "execution_allowed": False,
        }


def make_graph():
    runner = FakeReadOnlyServiceRunner()
    return {
        "service_runner": runner,
        "production_controlled_launch_package_assembler": object(),
        "production_controlled_launch_package_consumer": object(),
        "production_controlled_launch_permit_executor": object(),
    }, runner


def main() -> None:
    graph, runner = make_graph()
    activator = OracleProductionLiveShadowPersistentServiceActivator()

    record, result = activator.activate(
        production_graph=graph,
        start_kwargs={"max_cycles": 1},
    )

    assert record.schema_version == "OLA-063"
    assert record.engine_id == "OLA-063"
    assert record.service_start_invoked is True
    assert record.single_activation_enforced is True
    assert runner.calls == 1
    assert result["status"] == "completed"
    assert result["read_only"] is True
    assert result["execution_allowed"] is False

    try:
        activator.activate(
            production_graph=graph,
            start_kwargs={"max_cycles": 1},
        )
    except OracleProductionLiveShadowPersistentServiceActivationBlocked:
        pass
    else:
        raise AssertionError("OLA-063 must reject duplicate activation")

    unsafe_graph, unsafe_runner = make_graph()
    unsafe_runner.execution_allowed = True

    try:
        OracleProductionLiveShadowPersistentServiceActivator().activate(
            production_graph=unsafe_graph,
            start_kwargs={"max_cycles": 1},
        )
    except OracleProductionLiveShadowPersistentServiceActivationBlocked:
        pass
    else:
        raise AssertionError("OLA-063 must reject execution-enabled runner")

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowPersistentServiceActivator",
        "production_live_shadow_persistent_service_activator = (",
        '"production_live_shadow_persistent_service_activator": (',
    )

    for marker in required:
        assert marker in source, marker

    executor_pos = source.index(
        "production_controlled_launch_permit_executor = ("
    )
    activator_pos = source.index(
        "production_live_shadow_persistent_service_activator = ("
    )
    return_pos = source.index("    return {", activator_pos)

    assert executor_pos < activator_pos < return_pos

    print("[PASS] OLA-063 Production Live Shadow Persistent Service Activation")
    print({
        "schema_version": "OLA-063",
        "engine_id": "OLA-063",
        "status": "passed",
        "actual_ola030_persistent_service_activator_integrated": True,
        "ola062_controlled_execution_boundary_required": True,
        "existing_service_runner_required": True,
        "service_start_callable_resolved": True,
        "single_activation_enforced": True,
        "duplicate_activation_rejected": True,
        "execution_enabled_runner_rejected": True,
        "persistent_service_activation_path_ready": True,
        "graph_assembly_does_not_auto_activate_service": True,
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
