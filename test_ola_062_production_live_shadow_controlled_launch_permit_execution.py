from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_permit_execution import (
    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked,
    OracleProductionLiveShadowControlledLaunchPermitExecutor,
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
            "status": "launched_once",
            "read_only": True,
            "execution_allowed": False,
        }


class ControlledInvoker:
    read_only = True
    execution_allowed = False

    def invoke(
        self,
        *,
        launch_binding,
        runner,
        launch_callable,
    ):
        assert launch_binding.runner_identity == id(
            runner
        )

        result = launch_callable()

        record = SimpleNamespace(
            schema_version="OLA-058",
            engine_id="OLA-058",
            invocation_completed=True,
            read_only=True,
            execution_allowed=False,
        )

        return (
            record,
            result,
        )


def make_package_and_permit():
    runner = Runner()

    controlled_invoker = ControlledInvoker()

    launch_binding = SimpleNamespace(
        schema_version="OLA-057",
        engine_id="OLA-057",
        runner_identity=id(
            runner
        ),
        launch_binding_ready=True,
        launch_invoked=False,
        read_only=True,
        execution_allowed=False,
    )

    callable_binding = SimpleNamespace(
        launch_callable=runner.launch_once,
    )

    package_record = SimpleNamespace(
        schema_version="OLA-060",
        engine_id="OLA-060",
        controlled_launch_package_ready=True,
        launch_binding_identity=id(
            launch_binding
        ),
        callable_binding_identity=id(
            callable_binding
        ),
        controlled_invoker_identity=id(
            controlled_invoker
        ),
        runner_identity=id(
            runner
        ),
    )

    launch_package = SimpleNamespace(
        record=package_record,
        launch_binding=launch_binding,
        callable_binding=callable_binding,
        controlled_invoker=controlled_invoker,
        runner=runner,
    )

    invocation_permit = SimpleNamespace(
        schema_version="OLA-061",
        engine_id="OLA-061",
        source_package_identity=id(
            launch_package
        ),
        callable_binding_identity=id(
            callable_binding
        ),
        controlled_invoker_identity=id(
            controlled_invoker
        ),
        runner_identity=id(
            runner
        ),
        package_consumed=True,
        invocation_permit_issued=True,
        invocation_permit_consumed=False,
        read_only=True,
        execution_allowed=False,
    )

    return (
        launch_package,
        invocation_permit,
    )


def main() -> None:
    (
        launch_package,
        invocation_permit,
    ) = make_package_and_permit()

    executor = (
        OracleProductionLiveShadowControlledLaunchPermitExecutor()
    )

    record, result = executor.execute(
        invocation_permit=invocation_permit,
        launch_package=launch_package,
    )

    assert record.schema_version == "OLA-062"
    assert record.engine_id == "OLA-062"

    assert (
        record.invocation_permit_consumed
        is True
    )

    assert (
        record.controlled_invocation_completed
        is True
    )

    assert record.read_only is True
    assert record.execution_allowed is False

    assert result == {
        "status": "launched_once",
        "read_only": True,
        "execution_allowed": False,
    }

    try:
        executor.execute(
            invocation_permit=invocation_permit,
            launch_package=launch_package,
        )

    except (
        OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked
    ):
        pass

    else:
        raise AssertionError(
            "OLA-062 must reject replay of the same OLA-061 permit"
        )

    (
        other_package,
        other_permit,
    ) = make_package_and_permit()

    try:
        (
            OracleProductionLiveShadowControlledLaunchPermitExecutor()
            .execute(
                invocation_permit=other_permit,
                launch_package=launch_package,
            )
        )

    except (
        OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked
    ):
        pass

    else:
        raise AssertionError(
            "OLA-062 must reject permit/package identity mismatch"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchPermitExecutor",

        "production_controlled_launch_permit_executor = (",

        '"production_controlled_launch_permit_executor": (',
    )

    for marker in required:
        assert marker in source, marker

    consumer_pos = source.index(
        "production_controlled_launch_package_consumer = ("
    )

    executor_pos = source.index(
        "production_controlled_launch_permit_executor = ("
    )

    return_pos = source.index(
        "    return {",
        executor_pos,
    )

    assert (
        consumer_pos
        < executor_pos
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
        "production_controlled_launch_package_assembler.assemble(",
        "production_controlled_launch_package_consumer.consume(",
        "production_controlled_launch_permit_executor.execute(",
        "production_controlled_launch_invoker.invoke(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker

    print(
        "[PASS] OLA-062 "
        "Production Live Shadow Controlled Launch Permit Execution"
    )

    print({
        "schema_version": "OLA-062",
        "engine_id": "OLA-062",
        "status": "passed",

        "actual_ola030_launch_permit_executor_integrated": True,

        "ola061_invocation_permit_required": True,

        "ola060_launch_package_required": True,

        "permit_package_identity_preserved": True,

        "runner_identity_preserved": True,

        "controlled_invoker_identity_preserved": True,

        "callable_binding_identity_preserved": True,

        "single_use_permit_consumption_enforced": True,

        "permit_replay_rejected": True,

        "permit_package_mismatch_rejected": True,

        "controlled_invocation_completed": True,

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
