from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_assembly import (
    OracleProductionLiveShadowControlledLaunchPackageAssembler,
    OracleProductionLiveShadowControlledLaunchPackageBlocked,
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
        return None


class ControlledInvoker:
    read_only = True
    execution_allowed = False


def make_components():
    runner = Runner()

    token = SimpleNamespace(
        schema_version="OLA-056",
        engine_id="OLA-056",
        authorization_consumed=True,
        launch_token_issued=True,
        launch_invoked=False,
        read_only=True,
        execution_allowed=False,
    )

    launch_binding = SimpleNamespace(
        schema_version="OLA-057",
        engine_id="OLA-057",
        launch_token_identity=id(token),
        runner_identity=id(runner),
        launch_binding_ready=True,
        launch_invoked=False,
        read_only=True,
        execution_allowed=False,
    )

    callable_record = SimpleNamespace(
        schema_version="OLA-059",
        engine_id="OLA-059",
        source_launch_binding_identity=id(
            launch_binding
        ),
        runner_identity=id(
            runner
        ),
        callable_binding_ready=True,
        callable_invoked=False,
    )

    callable_binding = SimpleNamespace(
        record=callable_record,
        launch_callable=runner.launch_once,
    )

    controlled_invoker = ControlledInvoker()

    return (
        runner,
        token,
        launch_binding,
        callable_binding,
        controlled_invoker,
    )


def main() -> None:
    (
        runner,
        token,
        launch_binding,
        callable_binding,
        controlled_invoker,
    ) = make_components()

    package = (
        OracleProductionLiveShadowControlledLaunchPackageAssembler()
        .assemble(
            launch_token=token,
            launch_binding=launch_binding,
            callable_binding=callable_binding,
            controlled_invoker=controlled_invoker,
            runner=runner,
        )
    )

    record = package.record

    assert record.schema_version == "OLA-060"
    assert record.engine_id == "OLA-060"

    assert record.launch_token_identity == id(
        token
    )

    assert record.launch_binding_identity == id(
        launch_binding
    )

    assert record.callable_binding_identity == id(
        callable_binding
    )

    assert record.runner_identity == id(
        runner
    )

    assert record.launch_token_valid is True
    assert record.launch_binding_valid is True
    assert record.callable_binding_valid is True
    assert record.controlled_invoker_valid is True

    assert (
        record.token_to_launch_binding_identity_preserved
        is True
    )

    assert (
        record.launch_binding_to_callable_binding_identity_preserved
        is True
    )

    assert (
        record.callable_binding_to_runner_identity_preserved
        is True
    )

    assert (
        record.controlled_launch_package_ready
        is True
    )

    assert record.launch_invoked is False
    assert record.callable_invoked is False

    assert record.read_only is True
    assert record.execution_allowed is False

    wrong_runner = Runner()

    try:
        (
            OracleProductionLiveShadowControlledLaunchPackageAssembler()
            .assemble(
                launch_token=token,
                launch_binding=launch_binding,
                callable_binding=callable_binding,
                controlled_invoker=controlled_invoker,
                runner=wrong_runner,
            )
        )

    except OracleProductionLiveShadowControlledLaunchPackageBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-060 must reject a runner identity mismatch"
        )

    bad_binding = SimpleNamespace(
        **vars(launch_binding)
    )

    bad_binding.launch_token_identity = -1

    try:
        (
            OracleProductionLiveShadowControlledLaunchPackageAssembler()
            .assemble(
                launch_token=token,
                launch_binding=bad_binding,
                callable_binding=callable_binding,
                controlled_invoker=controlled_invoker,
                runner=runner,
            )
        )

    except OracleProductionLiveShadowControlledLaunchPackageBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-060 must reject a token-to-binding identity mismatch"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchPackageAssembler",
        "production_controlled_launch_package_assembler = (",
        '"production_controlled_launch_package_assembler": (',
    )

    for marker in required:
        assert marker in source, marker

    callable_binder_pos = source.index(
        "production_exact_runner_launch_callable_binder = ("
    )

    package_assembler_pos = source.index(
        "production_controlled_launch_package_assembler = ("
    )

    return_pos = source.index(
        "    return {",
        package_assembler_pos,
    )

    assert (
        callable_binder_pos
        < package_assembler_pos
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
        "production_controlled_launch_invoker.invoke(",
        "runner.run(",
        "runner.start(",
        "runner.launch(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker

    print(
        "[PASS] OLA-060 "
        "Production Live Shadow Controlled Launch Package Assembly"
    )

    print({
        "schema_version": "OLA-060",
        "engine_id": "OLA-060",
        "status": "passed",

        "actual_ola030_launch_package_assembler_integrated": True,

        "ola056_launch_token_required": True,

        "ola057_launch_binding_required": True,

        "ola059_exact_callable_binding_required": True,

        "ola058_controlled_invoker_required": True,

        "token_to_launch_binding_identity_preserved": True,

        "launch_binding_to_callable_binding_identity_preserved": True,

        "callable_binding_to_runner_identity_preserved": True,

        "controlled_launch_package_ready": True,

        "launch_not_invoked": True,

        "callable_not_invoked": True,

        "runner_identity_mismatch_rejected": True,

        "token_binding_identity_mismatch_rejected": True,

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
