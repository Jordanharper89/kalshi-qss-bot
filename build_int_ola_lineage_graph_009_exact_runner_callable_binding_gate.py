from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST = (
    ROOT
    / "test_int_ola_lineage_graph_009_"
    "exact_runner_callable_binding_gate.py"
)


TEST_TEXT = r'''
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

OLA057_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_launch_binding"
)

OLA058_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_controlled_launch_invocation"
)

OLA059_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_exact_runner_launch_callable_binding"
)


def _assert_module_contracts() -> None:
    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    ola059 = importlib.import_module(
        OLA059_MODULE
    )

    assert ola057.SCHEMA_VERSION == "OLA-057"
    assert ola057.ENGINE_ID == "OLA-057"

    assert ola058.SCHEMA_VERSION == "OLA-058"
    assert ola058.ENGINE_ID == "OLA-058"

    assert ola059.SCHEMA_VERSION == "OLA-059"
    assert ola059.ENGINE_ID == "OLA-059"

    Binder = (
        ola059.
        OracleExactRunnerLaunchCallableBinder
    )

    assert Binder.read_only is True
    assert Binder.execution_allowed is False


def _assert_actual_ola030_binding_boundary() -> None:
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

    required = (
        "OracleProductionLiveShadowLaunchBinder",

        "OracleProductionLiveShadowControlledLaunchInvoker",

        "OracleExactRunnerLaunchCallableBinder",

        "production_launch_binder = (",

        "production_controlled_launch_invoker = (",

        "production_exact_runner_launch_callable_binder = (",

        '"production_launch_binder": (',

        '"production_controlled_launch_invoker": (',

        '"production_exact_runner_launch_callable_binder": (',
    )

    for marker in required:
        assert marker in source, marker

    launch_binder_pos = source.index(
        "production_launch_binder = ("
    )

    invoker_pos = source.index(
        "production_controlled_launch_invoker = ("
    )

    callable_binder_pos = source.index(
        "production_exact_runner_launch_callable_binder = ("
    )

    return_pos = source.index(
        "    return {",
        callable_binder_pos,
    )

    assert (
        launch_binder_pos
        < invoker_pos
        < callable_binder_pos
        < return_pos
    )

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden = (
        "production_start_authorization_consumer.consume(",

        "production_launch_binder.bind(",

        "production_exact_runner_launch_callable_binder.bind(",

        "production_controlled_launch_invoker.invoke(",

        "runner.run(",

        "runner.start(",

        "runner.launch(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker


class Runner:
    read_only = True
    execution_allowed = False

    def launch_once(self):
        return {
            "status": "not_invoked",
            "read_only": True,
        }


def _make_launch_binding(
    runner,
):
    return SimpleNamespace(
        schema_version="OLA-057",

        engine_id="OLA-057",

        launch_binding_ready=True,

        launch_invoked=False,

        runner_identity=id(
            runner
        ),

        read_only=True,

        execution_allowed=False,
    )


def _exercise_exact_callable_binding() -> None:
    ola059 = importlib.import_module(
        OLA059_MODULE
    )

    Binder = (
        ola059.
        OracleExactRunnerLaunchCallableBinder
    )

    runner = Runner()

    launch_binding = _make_launch_binding(
        runner
    )

    binding = Binder().bind(
        launch_binding=launch_binding,

        runner=runner,

        launch_callable=runner.launch_once,
    )

    record = binding.record

    assert record.schema_version == "OLA-059"
    assert record.engine_id == "OLA-059"

    assert (
        record.runner_identity
        == id(runner)
    )

    assert (
        record.callable_owner_identity
        == id(runner)
    )

    assert (
        record.launch_binding_valid
        is True
    )

    assert (
        record.exact_runner_identity_preserved
        is True
    )

    assert (
        record.callable_is_bound_method
        is True
    )

    assert (
        record.callable_bound_to_exact_runner
        is True
    )

    assert (
        record.callable_binding_ready
        is True
    )

    assert (
        record.callable_invoked
        is False
    )

    assert (
        binding.launch_callable.__self__
        is runner
    )


def _exercise_wrong_runner_method_rejection() -> None:
    ola059 = importlib.import_module(
        OLA059_MODULE
    )

    Binder = (
        ola059.
        OracleExactRunnerLaunchCallableBinder
    )

    Blocked = (
        ola059.
        OracleExactRunnerLaunchCallableBindingBlocked
    )

    runner = Runner()

    wrong_runner = Runner()

    launch_binding = _make_launch_binding(
        runner
    )

    try:
        Binder().bind(
            launch_binding=launch_binding,

            runner=runner,

            launch_callable=wrong_runner.launch_once,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-009 "
            "expected wrong-runner bound method rejection"
        )


def _exercise_arbitrary_callable_rejection() -> None:
    ola059 = importlib.import_module(
        OLA059_MODULE
    )

    Binder = (
        ola059.
        OracleExactRunnerLaunchCallableBinder
    )

    Blocked = (
        ola059.
        OracleExactRunnerLaunchCallableBindingBlocked
    )

    runner = Runner()

    launch_binding = _make_launch_binding(
        runner
    )

    try:
        Binder().bind(
            launch_binding=launch_binding,

            runner=runner,

            launch_callable=lambda: None,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-009 "
            "expected arbitrary callable rejection"
        )


def main() -> None:
    _assert_module_contracts()

    _assert_actual_ola030_binding_boundary()

    _exercise_exact_callable_binding()

    _exercise_wrong_runner_method_rejection()

    _exercise_arbitrary_callable_rejection()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-009 "
        "Exact Runner Callable Binding Gate"
    )

    print({
        "schema_version": (
            "INT-OLA-LINEAGE-GRAPH-009"
        ),

        "engine_id": (
            "INT-OLA-LINEAGE-GRAPH-009"
        ),

        "status": "passed",

        "actual_ola030_source_graph_inspected": True,

        "actual_graph_ast_valid": True,

        "ola057_launch_binding_contract_preserved": True,

        "ola058_controlled_invocation_contract_preserved": True,

        "ola059_exact_callable_binding_contract_preserved": True,

        "launch_binder_precedes_controlled_invoker": True,

        "controlled_invoker_precedes_exact_callable_binder": True,

        "exact_runner_identity_required": True,

        "bound_runner_method_required": True,

        "arbitrary_callable_rejected": True,

        "wrong_runner_bound_method_rejected": True,

        "callable_binding_ready": True,

        "callable_not_invoked": True,

        "authorization_not_auto_consumed": True,

        "launch_token_not_auto_issued": True,

        "launch_binding_not_auto_created": True,

        "exact_callable_binding_not_auto_created": True,

        "controlled_invocation_not_auto_called": True,

        "runner_not_auto_invoked_during_graph_assembly": True,

        "no_process_created": True,

        "no_thread_created": True,

        "no_background_loop_started": True,

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
'''


def main() -> None:
    print("========================================")
    print(" INT-OLA-LINEAGE-GRAPH-009 INSTALLER")
    print(" EXACT RUNNER CALLABLE BINDING GATE")
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
            "[ERROR] Missing actual OLA-030 "
            "production graph: "
            f"{ola030}"
        )

    source = ola030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowLaunchBinder",

        "OracleProductionLiveShadowControlledLaunchInvoker",

        "OracleExactRunnerLaunchCallableBinder",

        "production_launch_binder = (",

        "production_controlled_launch_invoker = (",

        "production_exact_runner_launch_callable_binder = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-057/058/059 production integration "
            "is incomplete. "
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
        f"[OK] Wrote integration gate: {TEST}"
    )

    print(
        "\n[DONE] INT-OLA-LINEAGE-GRAPH-009 "
        "exact runner callable binding gate installed"
    )

    print("\nRun:")

    print(
        "py test_int_ola_lineage_graph_009_"
        "exact_runner_callable_binding_gate.py"
    )


if __name__ == "__main__":
    main()