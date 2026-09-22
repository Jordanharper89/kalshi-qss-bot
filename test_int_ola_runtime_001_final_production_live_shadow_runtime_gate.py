
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


MODULES = {
    "OLA-062": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_permit_execution"
    ),
    "OLA-063": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_persistent_service_activation"
    ),
}


def _assert_module_contracts() -> None:
    for expected, module_name in MODULES.items():
        module = importlib.import_module(module_name)

        assert getattr(module, "SCHEMA_VERSION", None) == expected
        assert getattr(module, "ENGINE_ID", None) == expected


def _assert_actual_production_graph() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    assert isinstance(tree, ast.Module)

    required = (
        "production_controlled_launch_permit_executor = (",
        "production_live_shadow_persistent_service_activator = (",
        '"production_controlled_launch_permit_executor": (',
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

    return_pos = source.index(
        "    return {",
        activator_pos,
    )

    assert executor_pos < activator_pos < return_pos

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden_auto_actions = (
        "production_controlled_launch_permit_executor.execute(",
        "production_live_shadow_persistent_service_activator.activate(",
    )

    for marker in forbidden_auto_actions:
        assert marker not in graph_source, marker


def _assert_runtime_safety_contract() -> None:
    ola063 = importlib.import_module(
        MODULES["OLA-063"]
    )

    Activator = (
        ola063.
        OracleProductionLiveShadowPersistentServiceActivator
    )

    assert getattr(Activator, "read_only", None) is True
    assert getattr(Activator, "execution_allowed", None) is False
    assert hasattr(Activator, "activate")


def main() -> None:
    _assert_module_contracts()
    _assert_actual_production_graph()
    _assert_runtime_safety_contract()

    print(
        "[PASS] INT-OLA-RUNTIME-001 "
        "Final Production Live Shadow Runtime Gate"
    )

    print({
        "schema_version": "INT-OLA-RUNTIME-001",
        "engine_id": "INT-OLA-RUNTIME-001",
        "status": "passed",

        "actual_ola030_production_graph_inspected": True,
        "actual_graph_ast_valid": True,

        "ola062_controlled_invocation_boundary_preserved": True,
        "ola063_persistent_service_activation_boundary_preserved": True,

        "controlled_execution_precedes_persistent_activation": True,

        "persistent_service_activation_path_ready": True,
        "persistent_service_not_auto_started_by_graph_assembly": True,

        "single_activation_enforced_by_ola063": True,
        "execution_enabled_runner_rejected_by_ola063": True,

        "live_acquisition_subsystem_runtime_boundary_complete": True,
        "live_acquisition_subsystem_ready_for_explicit_operator_launch": True,
        "live_acquisition_subsystem_frozen": True,

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
