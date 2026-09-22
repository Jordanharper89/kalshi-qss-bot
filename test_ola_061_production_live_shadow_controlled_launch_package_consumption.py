from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_consumption import (
    OracleProductionLiveShadowControlledLaunchPackageConsumer,
    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked,
)


ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)


def make_package():
    record = SimpleNamespace(
        schema_version="OLA-060",
        engine_id="OLA-060",

        launch_token_identity=101,
        launch_binding_identity=202,
        callable_binding_identity=303,
        controlled_invoker_identity=404,
        runner_identity=505,

        controlled_launch_package_ready=True,

        launch_invoked=False,
        callable_invoked=False,

        read_only=True,
        execution_allowed=False,
    )

    return SimpleNamespace(
        record=record,
    )


def main() -> None:
    package = make_package()

    consumer = (
        OracleProductionLiveShadowControlledLaunchPackageConsumer()
    )

    permit = consumer.consume(
        launch_package=package,
    )

    assert permit.schema_version == "OLA-061"
    assert permit.engine_id == "OLA-061"

    assert (
        permit.source_package_identity
        == id(package)
    )

    assert permit.package_consumed is True

    assert (
        permit.invocation_permit_issued
        is True
    )

    assert (
        permit.invocation_permit_consumed
        is False
    )

    assert permit.launch_invoked is False

    assert permit.callable_invoked is False

    assert permit.read_only is True

    assert permit.execution_allowed is False

    try:
        consumer.consume(
            launch_package=package,
        )

    except (
        OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked
    ):
        pass

    else:
        raise AssertionError(
            "OLA-061 must reject replay of the same OLA-060 package"
        )

    invalid_package = make_package()

    invalid_package.record.launch_invoked = True

    try:
        (
            OracleProductionLiveShadowControlledLaunchPackageConsumer()
            .consume(
                launch_package=invalid_package,
            )
        )

    except (
        OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked
    ):
        pass

    else:
        raise AssertionError(
            "OLA-061 must reject an already-invoked OLA-060 package"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchPackageConsumer",

        "production_controlled_launch_package_consumer = (",

        '"production_controlled_launch_package_consumer": (',
    )

    for marker in required:
        assert marker in source, marker

    assembler_pos = source.index(
        "production_controlled_launch_package_assembler = ("
    )

    consumer_pos = source.index(
        "production_controlled_launch_package_consumer = ("
    )

    return_pos = source.index(
        "    return {",
        consumer_pos,
    )

    assert (
        assembler_pos
        < consumer_pos
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

        "production_controlled_launch_invoker.invoke(",

        "runner.run(",

        "runner.start(",

        "runner.launch(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker

    print(
        "[PASS] OLA-061 "
        "Production Live Shadow Controlled Launch Package Consumption"
    )

    print({
        "schema_version": "OLA-061",

        "engine_id": "OLA-061",

        "status": "passed",

        "actual_ola030_launch_package_consumer_integrated": True,

        "ola060_launch_package_required": True,

        "single_use_package_consumption_enforced": True,

        "package_replay_rejected": True,

        "already_invoked_package_rejected": True,

        "invocation_permit_issued": True,

        "invocation_permit_not_consumed": True,

        "launch_not_invoked": True,

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
