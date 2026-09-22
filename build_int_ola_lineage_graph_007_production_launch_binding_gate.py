from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

TEST = (
    ROOT
    / "test_int_ola_lineage_graph_007_"
    "production_launch_binding_gate.py"
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

OLA056_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_start_authorization_consumption"
)

OLA057_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_launch_binding"
)


def _assert_module_contracts() -> None:
    ola056 = importlib.import_module(
        OLA056_MODULE
    )

    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    assert (
        getattr(
            ola056,
            "SCHEMA_VERSION",
            None,
        )
        == "OLA-056"
    )

    assert (
        getattr(
            ola056,
            "ENGINE_ID",
            None,
        )
        == "OLA-056"
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

    Binder = (
        ola057.
        OracleProductionLiveShadowLaunchBinder
    )

    assert (
        getattr(
            Binder,
            "read_only",
            None,
        )
        is True
    )

    assert (
        getattr(
            Binder,
            "execution_allowed",
            None,
        )
        is False
    )


def _assert_actual_ola030_launch_boundary() -> None:
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
        "OracleProductionLiveShadowStartAuthorizationConsumer",
        "OracleProductionLiveShadowLaunchBinder",

        "production_start_authorization_consumer = (",
        "production_launch_binder = (",

        '"production_start_authorization_consumer": (',
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

    graph_start = source.index(
        "def build_real_oracle_shadow_graph("
    )

    graph_source = source[
        graph_start:
    ]

    forbidden_auto_activation = (
        "production_start_authorization_consumer.consume(",
        "production_launch_binder.bind(",

        "launch_token =",
        "production_launch_binding =",

        "runner.run(",
        "runner.start(",
        "runner.launch(",
    )

    for marker in forbidden_auto_activation:
        assert marker not in graph_source, marker


def _make_launch_token():
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


class Runner:
    read_only = True
    execution_allowed = False


def _exercise_binding_contract() -> None:
    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    Binder = (
        ola057.
        OracleProductionLiveShadowLaunchBinder
    )

    token = _make_launch_token()
    runner = Runner()

    record = Binder().bind(
        launch_token=token,
        runner=runner,
    )

    assert (
        record.schema_version
        == "OLA-057"
    )

    assert (
        record.engine_id
        == "OLA-057"
    )

    assert (
        record.launch_token_identity
        == id(token)
    )

    assert (
        record.runner_identity
        == id(runner)
    )

    assert record.token_valid is True

    assert (
        record.token_not_invoked
        is True
    )

    assert (
        record.runner_identity_bound
        is True
    )

    assert (
        record.launch_binding_ready
        is True
    )

    assert (
        record.launch_invoked
        is False
    )

    assert (
        record.service_started
        is False
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
        record.loop_started
        is False
    )

    assert (
        record.acquisition_invoked
        is False
    )

    assert (
        record.scheduler_tick_invoked
        is False
    )

    assert (
        record.shadow_cycle_invoked
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


def _exercise_fail_closed_token_rejection() -> None:
    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    Binder = (
        ola057.
        OracleProductionLiveShadowLaunchBinder
    )

    Blocked = (
        ola057.
        OracleProductionLiveShadowLaunchBindingBlocked
    )

    token = _make_launch_token()

    token.scheduler_tick_invoked = True

    try:
        Binder().bind(
            launch_token=token,
            runner=Runner(),
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-007 "
            "expected fail-closed rejection "
            "of a token with prior runtime activity"
        )


def _exercise_fail_closed_runner_rejection() -> None:
    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    Binder = (
        ola057.
        OracleProductionLiveShadowLaunchBinder
    )

    Blocked = (
        ola057.
        OracleProductionLiveShadowLaunchBindingBlocked
    )

    class BadRunner:
        read_only = True
        execution_allowed = True

    try:
        Binder().bind(
            launch_token=_make_launch_token(),
            runner=BadRunner(),
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-007 "
            "expected fail-closed rejection "
            "of an execution-enabled runner"
        )


def main() -> None:
    _assert_module_contracts()

    _assert_actual_ola030_launch_boundary()

    _exercise_binding_contract()

    _exercise_fail_closed_token_rejection()

    _exercise_fail_closed_runner_rejection()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-007 "
        "Production Launch Binding Gate"
    )

    print({
        "schema_version": (
            "INT-OLA-LINEAGE-GRAPH-007"
        ),

        "engine_id": (
            "INT-OLA-LINEAGE-GRAPH-007"
        ),

        "status": "passed",

        "actual_ola030_source_graph_inspected": True,

        "actual_graph_ast_valid": True,

        "ola056_launch_token_contract_preserved": True,

        "ola057_launch_binding_contract_preserved": True,

        "authorization_consumer_precedes_launch_binder": True,

        "consumer_exposed_for_controlled_launch": True,

        "launch_binder_exposed_for_controlled_launch": True,

        "authorization_not_auto_consumed_during_graph_assembly": True,

        "launch_token_not_auto_issued_during_graph_assembly": True,

        "launch_token_not_auto_bound_during_graph_assembly": True,

        "runner_not_auto_invoked_during_graph_assembly": True,

        "exact_launch_token_identity_bound": True,

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

        "fail_closed_prior_runtime_activity_tested": True,

        "fail_closed_execution_enabled_runner_tested": True,

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
    print(" INT-OLA-LINEAGE-GRAPH-007 INSTALLER")
    print(" PRODUCTION LAUNCH BINDING GATE")
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
        "OracleProductionLiveShadowStartAuthorizationConsumer",

        "OracleProductionLiveShadowLaunchBinder",

        "production_start_authorization_consumer = (",

        "production_launch_binder = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-056/057 production integration "
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
        "\n[DONE] INT-OLA-LINEAGE-GRAPH-007 "
        "production launch binding gate installed"
    )

    print("\nRun:")

    print(
        "py test_int_ola_lineage_graph_007_"
        "production_launch_binding_gate.py"
    )


if __name__ == "__main__":
    main()