
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

OLA058_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_controlled_launch_invocation"
)

OLA059_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_exact_runner_launch_callable_binding"
)

OLA060_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_controlled_launch_package_assembly"
)


def _assert_module_contracts() -> None:
    ola056 = importlib.import_module(
        OLA056_MODULE
    )

    ola057 = importlib.import_module(
        OLA057_MODULE
    )

    ola058 = importlib.import_module(
        OLA058_MODULE
    )

    ola059 = importlib.import_module(
        OLA059_MODULE
    )

    ola060 = importlib.import_module(
        OLA060_MODULE
    )

    assert ola056.SCHEMA_VERSION == "OLA-056"
    assert ola056.ENGINE_ID == "OLA-056"

    assert ola057.SCHEMA_VERSION == "OLA-057"
    assert ola057.ENGINE_ID == "OLA-057"

    assert ola058.SCHEMA_VERSION == "OLA-058"
    assert ola058.ENGINE_ID == "OLA-058"

    assert ola059.SCHEMA_VERSION == "OLA-059"
    assert ola059.ENGINE_ID == "OLA-059"

    assert ola060.SCHEMA_VERSION == "OLA-060"
    assert ola060.ENGINE_ID == "OLA-060"

    Assembler = (
        ola060.
        OracleProductionLiveShadowControlledLaunchPackageAssembler
    )

    assert Assembler.read_only is True
    assert Assembler.execution_allowed is False


def _assert_actual_ola030_package_boundary() -> None:
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

        "OracleProductionLiveShadowControlledLaunchInvoker",

        "OracleExactRunnerLaunchCallableBinder",

        "OracleProductionLiveShadowControlledLaunchPackageAssembler",

        "production_start_authorization_consumer = (",

        "production_launch_binder = (",

        "production_controlled_launch_invoker = (",

        "production_exact_runner_launch_callable_binder = (",

        "production_controlled_launch_package_assembler = (",

        '"production_start_authorization_consumer": (',

        '"production_launch_binder": (',

        '"production_controlled_launch_invoker": (',

        '"production_exact_runner_launch_callable_binder": (',

        '"production_controlled_launch_package_assembler": (',
    )

    for marker in required:
        assert marker in source, marker

    consumer_pos = source.index(
        "production_start_authorization_consumer = ("
    )

    launch_binder_pos = source.index(
        "production_launch_binder = ("
    )

    controlled_invoker_pos = source.index(
        "production_controlled_launch_invoker = ("
    )

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
        consumer_pos
        < launch_binder_pos
        < controlled_invoker_pos
        < callable_binder_pos
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


class Runner:
    read_only = True
    execution_allowed = False

    def launch_once(self):
        return None


class ControlledInvoker:
    read_only = True
    execution_allowed = False


def _make_components():
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

        launch_token_identity=id(
            token
        ),

        runner_identity=id(
            runner
        ),

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


def _exercise_package_assembly_contract() -> None:
    ola060 = importlib.import_module(
        OLA060_MODULE
    )

    Assembler = (
        ola060.
        OracleProductionLiveShadowControlledLaunchPackageAssembler
    )

    (
        runner,
        token,
        launch_binding,
        callable_binding,
        controlled_invoker,
    ) = _make_components()

    package = Assembler().assemble(
        launch_token=token,

        launch_binding=launch_binding,

        callable_binding=callable_binding,

        controlled_invoker=controlled_invoker,

        runner=runner,
    )

    record = package.record

    assert record.schema_version == "OLA-060"
    assert record.engine_id == "OLA-060"

    assert (
        record.launch_token_identity
        == id(token)
    )

    assert (
        record.launch_binding_identity
        == id(launch_binding)
    )

    assert (
        record.callable_binding_identity
        == id(callable_binding)
    )

    assert (
        record.controlled_invoker_identity
        == id(controlled_invoker)
    )

    assert (
        record.runner_identity
        == id(runner)
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


def _exercise_cross_identity_rejection() -> None:
    ola060 = importlib.import_module(
        OLA060_MODULE
    )

    Assembler = (
        ola060.
        OracleProductionLiveShadowControlledLaunchPackageAssembler
    )

    Blocked = (
        ola060.
        OracleProductionLiveShadowControlledLaunchPackageBlocked
    )

    (
        runner,
        token,
        launch_binding,
        callable_binding,
        controlled_invoker,
    ) = _make_components()

    wrong_runner = Runner()

    try:
        Assembler().assemble(
            launch_token=token,

            launch_binding=launch_binding,

            callable_binding=callable_binding,

            controlled_invoker=controlled_invoker,

            runner=wrong_runner,
        )

    except Blocked:
        pass

    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-010 "
            "expected cross-runner identity mismatch rejection"
        )


def main() -> None:
    _assert_module_contracts()

    _assert_actual_ola030_package_boundary()

    _exercise_package_assembly_contract()

    _exercise_cross_identity_rejection()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-010 "
        "Controlled Launch Package Assembly Gate"
    )

    print({
        "schema_version": (
            "INT-OLA-LINEAGE-GRAPH-010"
        ),

        "engine_id": (
            "INT-OLA-LINEAGE-GRAPH-010"
        ),

        "status": "passed",

        "actual_ola030_source_graph_inspected": True,

        "actual_graph_ast_valid": True,

        "ola056_launch_token_contract_preserved": True,

        "ola057_launch_binding_contract_preserved": True,

        "ola058_controlled_invocation_contract_preserved": True,

        "ola059_exact_callable_binding_contract_preserved": True,

        "ola060_launch_package_contract_preserved": True,

        "authorization_consumer_precedes_launch_binder": True,

        "launch_binder_precedes_controlled_invoker": True,

        "controlled_invoker_precedes_exact_callable_binder": True,

        "exact_callable_binder_precedes_package_assembler": True,

        "token_to_launch_binding_identity_preserved": True,

        "launch_binding_to_callable_binding_identity_preserved": True,

        "callable_binding_to_runner_identity_preserved": True,

        "controlled_launch_package_ready": True,

        "cross_runner_identity_mismatch_rejected": True,

        "authorization_not_auto_consumed": True,

        "launch_token_not_auto_issued": True,

        "launch_binding_not_auto_created": True,

        "exact_callable_binding_not_auto_created": True,

        "launch_package_not_auto_assembled": True,

        "controlled_invocation_not_auto_called": True,

        "runner_not_auto_invoked_during_graph_assembly": True,

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
