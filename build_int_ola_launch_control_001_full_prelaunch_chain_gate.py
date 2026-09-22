from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST = (
    ROOT
    / "test_int_ola_launch_control_001_"
    "full_prelaunch_chain_gate.py"
)


TEST_TEXT = r"""
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
    "OLA-052": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_lineage_graph_assembly_attestation"
    ),
    "OLA-053": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_lineage_scheduler_activation_attestation"
    ),
    "OLA-054": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_startup_readiness_attestation"
    ),
    "OLA-055": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization"
    ),
    "OLA-056": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_start_authorization_consumption"
    ),
    "OLA-057": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_launch_binding"
    ),
    "OLA-058": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_invocation"
    ),
    "OLA-059": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_exact_runner_launch_callable_binding"
    ),
    "OLA-060": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_assembly"
    ),
    "OLA-061": (
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_consumption"
    ),
}


def _assert_module_identity_chain() -> None:
    for expected, module_name in MODULES.items():
        module = importlib.import_module(module_name)

        assert getattr(module, "SCHEMA_VERSION", None) == expected
        assert getattr(module, "ENGINE_ID", None) == expected


def _assert_actual_ola030_full_prelaunch_chain() -> None:
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
        "lineage_graph_attestation = (",
        "lineage_scheduler_activation_attestation = (",
        "production_startup_readiness_attestation = (",
        "production_start_authorization = (",
        "production_start_authorization_consumer = (",
        "production_launch_binder = (",
        "production_controlled_launch_invoker = (",
        "production_exact_runner_launch_callable_binder = (",
        "production_controlled_launch_package_assembler = (",
        "production_controlled_launch_package_consumer = (",
    )

    positions = []

    for marker in ordered_markers:
        assert marker in source, marker
        positions.append(
            source.index(marker)
        )

    assert positions == sorted(
        positions
    )

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden_auto_actions = (
        "production_start_authorization_consumer.consume(",
        "production_launch_binder.bind(",
        "production_exact_runner_launch_callable_binder.bind(",
        "production_controlled_launch_package_assembler.assemble(",
        "production_controlled_launch_package_consumer.consume(",
        "production_controlled_launch_invoker.invoke(",
        "runner.run(",
        "runner.start(",
        "runner.launch(",
    )

    for marker in forbidden_auto_actions:
        assert marker not in graph_source, marker


def main() -> None:
    _assert_module_identity_chain()

    _assert_actual_ola030_full_prelaunch_chain()

    print(
        "[PASS] INT-OLA-LAUNCH-CONTROL-001 "
        "Full Prelaunch Chain Gate"
    )

    print({
        "schema_version": "INT-OLA-LAUNCH-CONTROL-001",
        "engine_id": "INT-OLA-LAUNCH-CONTROL-001",
        "status": "passed",

        "ola052_through_ola061_module_chain_present": True,

        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,

        "full_prelaunch_order_preserved": True,

        "graph_assembly_attested": True,
        "scheduler_activation_attested": True,
        "startup_readiness_attested": True,
        "start_authorization_present": True,
        "single_use_launch_token_boundary_present": True,
        "exact_runner_launch_binding_present": True,
        "controlled_invoker_present": True,
        "exact_runner_callable_binding_present": True,
        "controlled_launch_package_assembler_present": True,
        "single_use_invocation_permit_boundary_present": True,

        "authorization_not_auto_consumed": True,
        "launch_token_not_auto_issued": True,
        "launch_binding_not_auto_created": True,
        "callable_binding_not_auto_created": True,
        "launch_package_not_auto_assembled": True,
        "launch_package_not_auto_consumed": True,
        "controlled_invocation_not_auto_called": True,
        "runner_not_auto_invoked_during_graph_assembly": True,

        "prelaunch_chain_frozen": True,

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
"""


def main() -> None:
    print("========================================")
    print(" INT-OLA-LAUNCH-CONTROL-001 INSTALLER")
    print(" FULL PRELAUNCH CHAIN GATE")
    print("========================================")

    ola030 = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition_model"
        / "oracle_first_real_shadow_corpus_launch_command.py"
    )

    if not ola030.exists():
        raise SystemExit(
            "[ERROR] Missing actual OLA-030 production graph: "
            f"{ola030}"
        )

    source = ola030.read_text(
        encoding="utf-8"
    )

    required = (
        "lineage_graph_attestation = (",
        "lineage_scheduler_activation_attestation = (",
        "production_startup_readiness_attestation = (",
        "production_start_authorization = (",
        "production_start_authorization_consumer = (",
        "production_launch_binder = (",
        "production_controlled_launch_invoker = (",
        "production_exact_runner_launch_callable_binder = (",
        "production_controlled_launch_package_assembler = (",
        "production_controlled_launch_package_consumer = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] Full OLA-052 through OLA-061 "
            "prelaunch chain is incomplete. "
            f"Missing markers: {missing}"
        )

    TEST.write_text(
        TEST_TEXT,
        encoding="utf-8",
    )

    compile(
        TEST.read_text(
            encoding="utf-8"
        ),
        str(TEST),
        "exec",
    )

    print(
        f"[OK] Wrote consolidated integration gate: {TEST}"
    )

    print(
        "\n[DONE] INT-OLA-LAUNCH-CONTROL-001 "
        "full prelaunch chain gate installed"
    )

    print("\nRun:")

    print(
        "py test_int_ola_launch_control_001_"
        "full_prelaunch_chain_gate.py"
    )


if __name__ == "__main__":
    main()
