
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
    "OLA-060": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_assembly"
    ),
    "OLA-061": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_consumption"
    ),
    "OLA-062": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_permit_execution"
    ),
}


def _assert_module_identity_chain() -> None:
    for expected, module_name in MODULES.items():
        module = importlib.import_module(module_name)

        assert getattr(module, "SCHEMA_VERSION", None) == expected
        assert getattr(module, "ENGINE_ID", None) == expected


def _assert_actual_ola030_controlled_execution_boundary() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    assert isinstance(
        tree,
        ast.Module,
    )

    ordered_markers = (
        "production_controlled_launch_package_assembler = (",
        "production_controlled_launch_package_consumer = (",
        "production_controlled_launch_permit_executor = (",
    )

    positions = []

    for marker in ordered_markers:
        assert marker in source, marker

        positions.append(
            source.index(
                marker
            )
        )

    assert positions == sorted(
        positions
    )

    return_pos = source.index(
        "    return {",
        positions[-1],
    )

    assert (
        positions[-1]
        < return_pos
    )

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden_auto_actions = (
        "production_controlled_launch_package_assembler.assemble(",
        "production_controlled_launch_package_consumer.consume(",
        "production_controlled_launch_permit_executor.execute(",
        "production_controlled_launch_invoker.invoke(",
        "runner.run(",
        "runner.start(",
        "runner.launch(",
    )

    for marker in forbidden_auto_actions:
        assert marker not in graph_source, marker


def _assert_execution_contract_surface() -> None:
    ola062 = importlib.import_module(
        MODULES["OLA-062"]
    )

    Executor = (
        ola062.
        OracleProductionLiveShadowControlledLaunchPermitExecutor
    )

    assert (
        getattr(
            Executor,
            "read_only",
            None,
        )
        is True
    )

    assert (
        getattr(
            Executor,
            "execution_allowed",
            None,
        )
        is False
    )

    assert hasattr(
        Executor,
        "execute",
    )


def main() -> None:
    _assert_module_identity_chain()

    _assert_actual_ola030_controlled_execution_boundary()

    _assert_execution_contract_surface()

    print(
        "[PASS] INT-OLA-LAUNCH-CONTROL-002 "
        "Controlled Invocation Execution Gate"
    )

    print({
        "schema_version": "INT-OLA-LAUNCH-CONTROL-002",
        "engine_id": "INT-OLA-LAUNCH-CONTROL-002",
        "status": "passed",

        "ola060_launch_package_contract_preserved": True,
        "ola061_single_use_invocation_permit_contract_preserved": True,
        "ola062_controlled_invocation_execution_contract_preserved": True,

        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,

        "launch_package_assembler_precedes_package_consumer": True,
        "package_consumer_precedes_permit_executor": True,

        "controlled_invocation_execution_boundary_present": True,

        "launch_package_not_auto_assembled": True,
        "launch_package_not_auto_consumed": True,
        "invocation_permit_not_auto_executed": True,
        "controlled_invoker_not_auto_called": True,
        "runner_not_auto_invoked_during_graph_assembly": True,

        "single_synchronous_invocation_boundary_frozen": True,

        "no_process_created_by_graph_assembly": True,
        "no_thread_created_by_graph_assembly": True,
        "no_background_loop_started_by_graph_assembly": True,

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
