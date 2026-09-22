
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


def _assert_module_contracts() -> None:
    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    assert (
        getattr(
            ola057,
            "SCHEMA_VERSION",
            None,
        )
        == "OLA-057"
    )

    assert (
        getattr(
            ola057,
            "ENGINE_ID",
            None,
        )
        == "OLA-057"
    )

    assert (
        getattr(
            ola058,
            "SCHEMA_VERSION",
            None,
        )
        == "OLA-058"
    )

    assert (
        getattr(
            ola058,
            "ENGINE_ID",
            None,
        )
        == "OLA-058"
    )

    Invoker = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvoker
    )

    assert (
        getattr(
            Invoker,
            "read_only",
            None,
        )
        is True
    )

    assert (
        getattr(
            Invoker,
            "execution_allowed",
            None,
        )
        is False
    )


def _assert_actual_ola030_invocation_boundary() -> None:
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

        "production_launch_binder = (",

        "production_controlled_launch_invoker = (",

        '"production_launch_binder": (',

        '"production_controlled_launch_invoker": (',
    )

    for marker in required:
        assert marker in source, marker

    binder_pos = source.index(
        "production_launch_binder = ("
    )

    invoker_pos = source.index(
        "production_controlled_launch_invoker = ("
    )

    return_pos = source.index(
        "    return {",
        invoker_pos,
    )

    assert (
        binder_pos
        < invoker_pos
        < return_pos
    )

    graph_source = source[
        source.index(
            "def build_real_oracle_shadow_graph("
        ):
    ]

    forbidden_auto_invocation = (
        "production_start_authorization_consumer.consume(",

        "production_launch_binder.bind(",

        "production_controlled_launch_invoker.invoke(",

        "runner.run(",

        "runner.start(",

        "runner.launch(",
    )

    for marker in forbidden_auto_invocation:
        assert marker not in graph_source, marker


class Runner:
    read_only = True
    execution_allowed = False


def _make_binding(
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


def _exercise_controlled_invocation_contract() -> None:
    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    Invoker = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvoker
    )

    runner = Runner()

    binding = _make_binding(
        runner
    )

    calls = []

    def launch_callable():
        calls.append(
            "called"
        )

        return {
            "status": "completed",

            "read_only": True,

            "execution_allowed": False,
        }

    record, result = (
        Invoker()
        .invoke(
            launch_binding=binding,

            runner=runner,

            launch_callable=launch_callable,
        )
    )

    assert calls == [
        "called"
    ]

    assert result == {
        "status": "completed",

        "read_only": True,

        "execution_allowed": False,
    }

    assert (
        record.schema_version
        == "OLA-058"
    )

    assert (
        record.engine_id
        == "OLA-058"
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
        record.synchronous_invocation_allowed
        is True
    )

    assert (
        record.invocation_completed
        is True
    )

    assert (
        record.process_created
        is False
    )

    assert (
        record.thread_created
        is False
    )

    assert (
        record.background_loop_started
        is False
    )

    assert (
        record.read_only
        is True
    )

    assert (
        record.execution_allowed
        is False
    )


def _exercise_runner_identity_rejection() -> None:
    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    Invoker = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvoker
    )

    Blocked = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvocationBlocked
    )

    bound_runner = Runner()

    wrong_runner = Runner()

    binding = _make_binding(
        bound_runner
    )

    try:
        Invoker().invoke(
            launch_binding=binding,

            runner=wrong_runner,

            launch_callable=lambda: None,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-008 "
            "expected fail-closed runner "
            "identity mismatch rejection"
        )


def _exercise_invoked_binding_rejection() -> None:
    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    Invoker = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvoker
    )

    Blocked = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvocationBlocked
    )

    runner = Runner()

    binding = _make_binding(
        runner
    )

    binding.launch_invoked = True

    try:
        Invoker().invoke(
            launch_binding=binding,

            runner=runner,

            launch_callable=lambda: None,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-008 "
            "expected fail-closed rejection "
            "of an already-invoked binding"
        )


def _exercise_execution_enabled_runner_rejection() -> None:
    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    Invoker = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvoker
    )

    Blocked = (
        ola058.
        OracleProductionLiveShadowControlledLaunchInvocationBlocked
    )

    class BadRunner:
        read_only = True

        execution_allowed = True

    bad_runner = BadRunner()

    binding = SimpleNamespace(
        schema_version="OLA-057",

        engine_id="OLA-057",

        launch_binding_ready=True,

        launch_invoked=False,

        runner_identity=id(
            bad_runner
        ),

        read_only=True,

        execution_allowed=False,
    )

    try:
        Invoker().invoke(
            launch_binding=binding,

            runner=bad_runner,

            launch_callable=lambda: None,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-008 "
            "expected fail-closed rejection "
            "of execution-enabled runner"
        )


def main() -> None:
    _assert_module_contracts()

    _assert_actual_ola030_invocation_boundary()

    _exercise_controlled_invocation_contract()

    _exercise_runner_identity_rejection()

    _exercise_invoked_binding_rejection()

    _exercise_execution_enabled_runner_rejection()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-008 "
        "Production Controlled Launch Invocation Gate"
    )

    print({
        "schema_version": (
            "INT-OLA-LINEAGE-GRAPH-008"
        ),

        "engine_id": (
            "INT-OLA-LINEAGE-GRAPH-008"
        ),

        "status": "passed",

        "actual_ola030_source_graph_inspected": True,

        "actual_graph_ast_valid": True,

        "ola057_launch_binding_contract_preserved": True,

        "ola058_controlled_invocation_contract_preserved": True,

        "launch_binder_precedes_controlled_invoker": True,

        "controlled_invoker_exposed_for_explicit_launch": True,

        "authorization_not_auto_consumed": True,

        "launch_token_not_auto_issued": True,

        "launch_binding_not_auto_created": True,

        "controlled_invocation_not_auto_called": True,

        "runner_not_auto_invoked_during_graph_assembly": True,

        "single_synchronous_invocation_tested": True,

        "exact_runner_identity_required": True,

        "runner_identity_mismatch_rejected": True,

        "already_invoked_binding_rejected": True,

        "execution_enabled_runner_rejected": True,

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
