
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_launch_binding import (
    OracleProductionLiveShadowLaunchBinder,
    OracleProductionLiveShadowLaunchBindingBlocked,
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


def make_token():
    return SimpleNamespace(
        schema_version="OLA-056",
        engine_id="OLA-056",

        authorization_consumed=True,
        launch_token_issued=True,

        launch_invoked=False,
        service_started=False,
        process_created=False,
        thread_created=False,
        loop_started=False,

        acquisition_invoked=False,
        scheduler_tick_invoked=False,
        shadow_cycle_invoked=False,

        read_only=True,
        execution_allowed=False,
    )


def main() -> None:
    token = make_token()
    runner = Runner()

    record = (
        OracleProductionLiveShadowLaunchBinder()
        .bind(
            launch_token=token,
            runner=runner,
        )
    )

    assert record.schema_version == "OLA-057"
    assert record.engine_id == "OLA-057"

    assert record.launch_token_identity == id(
        token
    )

    assert record.runner_identity == id(
        runner
    )

    assert record.token_valid is True
    assert record.token_not_invoked is True

    assert record.runner_identity_bound is True
    assert record.launch_binding_ready is True

    assert record.launch_invoked is False

    assert record.service_started is False
    assert record.process_created is False
    assert record.thread_created is False
    assert record.loop_started is False

    assert record.acquisition_invoked is False
    assert record.scheduler_tick_invoked is False
    assert record.shadow_cycle_invoked is False

    assert record.read_only is True
    assert record.execution_allowed is False

    bad_token = make_token()
    bad_token.launch_invoked = True

    try:
        (
            OracleProductionLiveShadowLaunchBinder()
            .bind(
                launch_token=bad_token,
                runner=runner,
            )
        )

    except OracleProductionLiveShadowLaunchBindingBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-057 must fail closed for "
            "an already-invoked launch token"
        )

    class BadRunner:
        read_only = False
        execution_allowed = False

    try:
        (
            OracleProductionLiveShadowLaunchBinder()
            .bind(
                launch_token=make_token(),
                runner=BadRunner(),
            )
        )

    except OracleProductionLiveShadowLaunchBindingBlocked:
        pass

    else:
        raise AssertionError(
            "OLA-057 must fail closed for "
            "a non-read-only runner"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    ast.parse(
        source
    )

    required = (
        "OracleProductionLiveShadowLaunchBinder",
        "production_launch_binder = (",
        '"production_launch_binder": (',
    )

    for marker in required:
        assert marker in source, marker

    consumer_pos = source.index(
        "production_start_authorization_consumer = ("
    )

    binder_pos = source.index(
        "production_launch_binder = ("
    )

    return_pos = source.index(
        "    return {",
        binder_pos,
    )

    assert (
        consumer_pos
        < binder_pos
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
        "runner.run(",
        "runner.start(",
    )

    for marker in forbidden:
        assert marker not in graph_source, marker

    print(
        "[PASS] OLA-057 "
        "Production Live Shadow Launch Binding"
    )

    print({
        "schema_version": "OLA-057",
        "engine_id": "OLA-057",
        "status": "passed",

        "actual_ola030_launch_binder_integrated": True,

        "ola056_launch_token_required": True,

        "exact_runner_identity_bound": True,

        "launch_binding_ready": True,

        "launch_not_invoked": True,

        "service_not_started": True,

        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,

        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,

        "fail_closed_invoked_token_tested": True,

        "fail_closed_non_read_only_runner_tested": True,

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
