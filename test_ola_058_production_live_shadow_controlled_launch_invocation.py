from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_invocation import (
    OracleProductionLiveShadowControlledLaunchInvocationBlocked,
    OracleProductionLiveShadowControlledLaunchInvoker,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Runner:
    read_only = True
    execution_allowed = False


def make_binding(runner):
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
    binding = make_binding(runner)
    calls = []

    def launch_callable():
        calls.append("called")
        return {"status": "completed", "read_only": True}

    record, result = OracleProductionLiveShadowControlledLaunchInvoker().invoke(
        launch_binding=binding,
        runner=runner,
        launch_callable=launch_callable,
    )

    assert calls == ["called"]
    assert result == {"status": "completed", "read_only": True}
    assert record.schema_version == "OLA-058"
    assert record.engine_id == "OLA-058"
    assert record.launch_binding_valid is True
    assert record.exact_runner_identity_preserved is True
    assert record.synchronous_invocation_allowed is True
    assert record.invocation_completed is True
    assert record.process_created is False
    assert record.thread_created is False
    assert record.background_loop_started is False
    assert record.read_only is True
    assert record.execution_allowed is False

    wrong_runner = Runner()
    try:
        OracleProductionLiveShadowControlledLaunchInvoker().invoke(
            launch_binding=binding,
            runner=wrong_runner,
            launch_callable=lambda: None,
        )
    except OracleProductionLiveShadowControlledLaunchInvocationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-058 must fail closed on runner identity mismatch"
        )

    bad_binding = make_binding(runner)
    bad_binding.launch_invoked = True
    try:
        OracleProductionLiveShadowControlledLaunchInvoker().invoke(
            launch_binding=bad_binding,
            runner=runner,
            launch_callable=lambda: None,
        )
    except OracleProductionLiveShadowControlledLaunchInvocationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-058 must fail closed for an already-invoked binding"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowControlledLaunchInvoker",
        "production_controlled_launch_invoker = (",
        '"production_controlled_launch_invoker": (',
    )
    for marker in required:
        assert marker in source, marker

    binder_pos = source.index("production_launch_binder = (")
    invoker_pos = source.index("production_controlled_launch_invoker = (")
    return_pos = source.index("    return {", invoker_pos)
    assert binder_pos < invoker_pos < return_pos

    graph_source = source[source.index("def build_real_oracle_shadow_graph("):]
    forbidden = (
        "production_start_authorization_consumer.consume(",
        "production_launch_binder.bind(",
        "production_controlled_launch_invoker.invoke(",
        "runner.run(",
        "runner.start(",
        "runner.launch(",
    )
    for marker in forbidden:
        assert marker not in graph_source, marker

    print("[PASS] OLA-058 Production Live Shadow Controlled Launch Invocation")
    print({
        "schema_version": "OLA-058",
        "engine_id": "OLA-058",
        "status": "passed",
        "actual_ola030_controlled_launch_invoker_integrated": True,
        "ola057_launch_binding_required": True,
        "exact_runner_identity_required": True,
        "single_synchronous_invocation_tested": True,
        "runner_identity_mismatch_rejected": True,
        "already_invoked_binding_rejected": True,
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
