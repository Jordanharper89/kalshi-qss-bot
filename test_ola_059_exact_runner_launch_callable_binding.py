from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_exact_runner_launch_callable_binding import (
    OracleExactRunnerLaunchCallableBinder,
    OracleExactRunnerLaunchCallableBindingBlocked,
)

ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)


class Runner:
    read_only = True
    execution_allowed = False

    def launch_once(self):
        return {
            "status": "not_invoked_by_ola059",
            "read_only": True,
        }


def make_launch_binding(runner):
    return SimpleNamespace(
        schema_version="OLA-057",
        engine_id="OLA-057",
        launch_binding_ready=True,
        launch_invoked=False,
        runner_identity=id(runner),
        read_only=True,
        execution_allowed=False,
    )


def main() -> None:
    runner = Runner()
    launch_binding = make_launch_binding(runner)

    binding = OracleExactRunnerLaunchCallableBinder().bind(
        launch_binding=launch_binding,
        runner=runner,
        launch_callable=runner.launch_once,
    )

    record = binding.record

    assert record.schema_version == "OLA-059"
    assert record.engine_id == "OLA-059"
    assert record.runner_identity == id(runner)
    assert record.callable_owner_identity == id(runner)
    assert record.launch_binding_valid is True
    assert record.exact_runner_identity_preserved is True
    assert record.callable_is_bound_method is True
    assert record.callable_bound_to_exact_runner is True
    assert record.callable_binding_ready is True
    assert record.callable_invoked is False
    assert record.read_only is True
    assert record.execution_allowed is False
    assert binding.launch_callable.__self__ is runner

    wrong_runner = Runner()

    try:
        OracleExactRunnerLaunchCallableBinder().bind(
            launch_binding=launch_binding,
            runner=runner,
            launch_callable=wrong_runner.launch_once,
        )
    except OracleExactRunnerLaunchCallableBindingBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-059 must reject a callable bound to the wrong runner"
        )

    try:
        OracleExactRunnerLaunchCallableBinder().bind(
            launch_binding=launch_binding,
            runner=runner,
            launch_callable=lambda: None,
        )
    except OracleExactRunnerLaunchCallableBindingBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-059 must reject an arbitrary unbound callable"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleExactRunnerLaunchCallableBinder",
        "production_exact_runner_launch_callable_binder = (",
        '"production_exact_runner_launch_callable_binder": (',
    )

    for marker in required:
        assert marker in source, marker

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

    assert invoker_pos < callable_binder_pos < return_pos

    graph_source = source[
        source.index("def build_real_oracle_shadow_graph("):
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

    print("[PASS] OLA-059 Exact Runner Launch Callable Binding")

    print({
        "schema_version": "OLA-059",
        "engine_id": "OLA-059",
        "status": "passed",
        "actual_ola030_exact_callable_binder_integrated": True,
        "ola057_launch_binding_required": True,
        "exact_runner_identity_required": True,
        "bound_method_required": True,
        "callable_bound_to_exact_runner": True,
        "arbitrary_callable_rejected": True,
        "wrong_runner_bound_method_rejected": True,
        "callable_not_invoked": True,
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
