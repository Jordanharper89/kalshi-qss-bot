from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_production_live_shadow_controlled_launch_permit_execution.py"
)

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST = (
    ROOT
    / "test_ola_062_production_live_shadow_"
    "controlled_launch_permit_execution.py"
)

MODULE_TEXT = '"""\nOLA-062 Production Live Shadow Controlled Launch Permit Execution.\n\nConsumes an OLA-061 single-use invocation permit exactly once and delegates\none synchronous launch through the already-assembled OLA-060 package:\n\nOLA-061 invocation permit\n    + OLA-060 controlled launch package\n    -> OLA-058 controlled invoker\n    -> OLA-059 exact runner-bound launch callable\n\nThis module does not create a process, thread, or background loop. It does not\nenable alerts, Q Series handoff, trade authorization, order placement, funds\nmovement, or portfolio mutation.\n\nOracle remains permanently read-only.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom threading import Lock\nfrom typing import Any\n\n\nSCHEMA_VERSION = "OLA-062"\nENGINE_ID = "OLA-062"\nEXECUTION_TYPE = "oracle_production_live_shadow_controlled_launch_permit_execution"\n\n\nclass OracleProductionLiveShadowControlledLaunchPermitExecutionError(\n    ValueError\n):\n    pass\n\n\nclass OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n    RuntimeError\n):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowControlledLaunchPermitExecutionRecord:\n    schema_version: str\n    engine_id: str\n    execution_type: str\n\n    invocation_permit_identity: int\n    source_package_identity: int\n\n    runner_identity: int\n    controlled_invoker_identity: int\n    callable_binding_identity: int\n\n    invocation_permit_valid: bool\n    package_identity_preserved: bool\n    runner_identity_preserved: bool\n    controlled_invoker_identity_preserved: bool\n    callable_binding_identity_preserved: bool\n\n    invocation_permit_consumed: bool\n    controlled_invocation_completed: bool\n\n    process_created: bool = False\n    thread_created: bool = False\n    background_loop_started: bool = False\n\n    read_only: bool = True\n    execution_allowed: bool = False\n\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n    def __post_init__(self) -> None:\n        if self.schema_version != SCHEMA_VERSION:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionError(\n                    "OLA-062 schema_version mismatch"\n                )\n            )\n\n        if self.engine_id != ENGINE_ID:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionError(\n                    "OLA-062 engine_id mismatch"\n                )\n            )\n\n        if self.execution_type != EXECUTION_TYPE:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionError(\n                    "OLA-062 execution_type mismatch"\n                )\n            )\n\n        required = (\n            self.invocation_permit_valid,\n            self.package_identity_preserved,\n            self.runner_identity_preserved,\n            self.controlled_invoker_identity_preserved,\n            self.callable_binding_identity_preserved,\n            self.invocation_permit_consumed,\n            self.controlled_invocation_completed,\n            self.read_only,\n        )\n\n        if not all(value is True for value in required):\n            raise (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                    "OLA-062 execution record failed closed"\n                )\n            )\n\n        forbidden = (\n            self.process_created,\n            self.thread_created,\n            self.background_loop_started,\n            self.execution_allowed,\n            self.alerts_allowed,\n            self.qseries_handoff_allowed,\n            self.execution_adapter_resolved,\n            self.execution_adapter_invoked,\n            self.trade_authorization_allowed,\n            self.order_placement_allowed,\n            self.funds_moved,\n            self.portfolio_mutated,\n        )\n\n        if any(value is True for value in forbidden):\n            raise (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                    "OLA-062 observed forbidden activity"\n                )\n            )\n\n\nclass OracleProductionLiveShadowControlledLaunchPermitExecutor:\n    read_only = True\n    execution_allowed = False\n\n    def __init__(self) -> None:\n        self._lock = Lock()\n        self._consumed_permit_identities: set[int] = set()\n\n    def execute(\n        self,\n        *,\n        invocation_permit: Any,\n        launch_package: Any,\n    ) -> tuple[\n        OracleProductionLiveShadowControlledLaunchPermitExecutionRecord,\n        Any,\n    ]:\n        with self._lock:\n            permit_identity = id(\n                invocation_permit\n            )\n\n            if (\n                permit_identity\n                in self._consumed_permit_identities\n            ):\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                        "OLA-061 invocation permit already consumed"\n                    )\n                )\n\n            package_record = getattr(\n                launch_package,\n                "record",\n                None,\n            )\n\n            callable_binding = getattr(\n                launch_package,\n                "callable_binding",\n                None,\n            )\n\n            controlled_invoker = getattr(\n                launch_package,\n                "controlled_invoker",\n                None,\n            )\n\n            runner = getattr(\n                launch_package,\n                "runner",\n                None,\n            )\n\n            checks = {\n                "invocation_permit_valid": (\n                    getattr(\n                        invocation_permit,\n                        "schema_version",\n                        None,\n                    )\n                    == "OLA-061"\n                    and getattr(\n                        invocation_permit,\n                        "engine_id",\n                        None,\n                    )\n                    == "OLA-061"\n                    and getattr(\n                        invocation_permit,\n                        "package_consumed",\n                        None,\n                    )\n                    is True\n                    and getattr(\n                        invocation_permit,\n                        "invocation_permit_issued",\n                        None,\n                    )\n                    is True\n                    and getattr(\n                        invocation_permit,\n                        "invocation_permit_consumed",\n                        None,\n                    )\n                    is False\n                    and getattr(\n                        invocation_permit,\n                        "read_only",\n                        None,\n                    )\n                    is True\n                    and getattr(\n                        invocation_permit,\n                        "execution_allowed",\n                        None,\n                    )\n                    is False\n                ),\n\n                "package_identity_preserved": (\n                    getattr(\n                        invocation_permit,\n                        "source_package_identity",\n                        None,\n                    )\n                    == id(\n                        launch_package\n                    )\n                    and getattr(\n                        package_record,\n                        "schema_version",\n                        None,\n                    )\n                    == "OLA-060"\n                    and getattr(\n                        package_record,\n                        "engine_id",\n                        None,\n                    )\n                    == "OLA-060"\n                    and getattr(\n                        package_record,\n                        "controlled_launch_package_ready",\n                        None,\n                    )\n                    is True\n                ),\n\n                "runner_identity_preserved": (\n                    getattr(\n                        invocation_permit,\n                        "runner_identity",\n                        None,\n                    )\n                    == id(\n                        runner\n                    )\n                    and getattr(\n                        package_record,\n                        "runner_identity",\n                        None,\n                    )\n                    == id(\n                        runner\n                    )\n                ),\n\n                "controlled_invoker_identity_preserved": (\n                    getattr(\n                        invocation_permit,\n                        "controlled_invoker_identity",\n                        None,\n                    )\n                    == id(\n                        controlled_invoker\n                    )\n                    and getattr(\n                        package_record,\n                        "controlled_invoker_identity",\n                        None,\n                    )\n                    == id(\n                        controlled_invoker\n                    )\n                ),\n\n                "callable_binding_identity_preserved": (\n                    getattr(\n                        invocation_permit,\n                        "callable_binding_identity",\n                        None,\n                    )\n                    == id(\n                        callable_binding\n                    )\n                    and getattr(\n                        package_record,\n                        "callable_binding_identity",\n                        None,\n                    )\n                    == id(\n                        callable_binding\n                    )\n                ),\n            }\n\n            if not all(\n                checks.values()\n            ):\n                failed = ", ".join(\n                    name\n                    for name, passed in checks.items()\n                    if not passed\n                )\n\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                        "OLA-062 permit/package identity mismatch: "\n                        f"{failed}"\n                    )\n                )\n\n            launch_callable = getattr(\n                callable_binding,\n                "launch_callable",\n                None,\n            )\n\n            launch_binding = getattr(\n                launch_package,\n                "launch_binding",\n                None,\n            )\n\n            if (\n                not callable(\n                    launch_callable\n                )\n                or controlled_invoker is None\n                or runner is None\n                or launch_binding is None\n            ):\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                        "OLA-062 launch package is incomplete"\n                    )\n                )\n\n            self._consumed_permit_identities.add(\n                permit_identity\n            )\n\n            invocation_record, result = (\n                controlled_invoker.invoke(\n                    launch_binding=launch_binding,\n                    runner=runner,\n                    launch_callable=launch_callable,\n                )\n            )\n\n            if (\n                getattr(\n                    invocation_record,\n                    "schema_version",\n                    None,\n                )\n                != "OLA-058"\n                or getattr(\n                    invocation_record,\n                    "engine_id",\n                    None,\n                )\n                != "OLA-058"\n                or getattr(\n                    invocation_record,\n                    "invocation_completed",\n                    None,\n                )\n                is not True\n                or getattr(\n                    invocation_record,\n                    "read_only",\n                    None,\n                )\n                is not True\n                or getattr(\n                    invocation_record,\n                    "execution_allowed",\n                    None,\n                )\n                is not False\n            ):\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked(\n                        "OLA-058 controlled invocation result failed closed"\n                    )\n                )\n\n            record = (\n                OracleProductionLiveShadowControlledLaunchPermitExecutionRecord(\n                    schema_version=SCHEMA_VERSION,\n                    engine_id=ENGINE_ID,\n                    execution_type=EXECUTION_TYPE,\n\n                    invocation_permit_identity=(\n                        permit_identity\n                    ),\n\n                    source_package_identity=id(\n                        launch_package\n                    ),\n\n                    runner_identity=id(\n                        runner\n                    ),\n\n                    controlled_invoker_identity=id(\n                        controlled_invoker\n                    ),\n\n                    callable_binding_identity=id(\n                        callable_binding\n                    ),\n\n                    invocation_permit_consumed=True,\n\n                    controlled_invocation_completed=True,\n\n                    **checks,\n                )\n            )\n\n            return (\n                record,\n                result,\n            )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "EXECUTION_TYPE",\n    "OracleProductionLiveShadowControlledLaunchPermitExecutionError",\n    "OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked",\n    "OracleProductionLiveShadowControlledLaunchPermitExecutionRecord",\n    "OracleProductionLiveShadowControlledLaunchPermitExecutor",\n]\n'
TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_permit_execution import (\n    OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked,\n    OracleProductionLiveShadowControlledLaunchPermitExecutor,\n)\n\n\nROOT = Path(__file__).resolve().parent\n\nOLA030 = (\n    ROOT\n    / "qseries_v2"\n    / "oracle_intelligence"\n    / "live_acquisition_model"\n    / "oracle_first_real_shadow_corpus_launch_command.py"\n)\n\n\nclass Runner:\n    read_only = True\n    execution_allowed = False\n\n    def launch_once(self):\n        return {\n            "status": "launched_once",\n            "read_only": True,\n            "execution_allowed": False,\n        }\n\n\nclass ControlledInvoker:\n    read_only = True\n    execution_allowed = False\n\n    def invoke(\n        self,\n        *,\n        launch_binding,\n        runner,\n        launch_callable,\n    ):\n        assert launch_binding.runner_identity == id(\n            runner\n        )\n\n        result = launch_callable()\n\n        record = SimpleNamespace(\n            schema_version="OLA-058",\n            engine_id="OLA-058",\n            invocation_completed=True,\n            read_only=True,\n            execution_allowed=False,\n        )\n\n        return (\n            record,\n            result,\n        )\n\n\ndef make_package_and_permit():\n    runner = Runner()\n\n    controlled_invoker = ControlledInvoker()\n\n    launch_binding = SimpleNamespace(\n        schema_version="OLA-057",\n        engine_id="OLA-057",\n        runner_identity=id(\n            runner\n        ),\n        launch_binding_ready=True,\n        launch_invoked=False,\n        read_only=True,\n        execution_allowed=False,\n    )\n\n    callable_binding = SimpleNamespace(\n        launch_callable=runner.launch_once,\n    )\n\n    package_record = SimpleNamespace(\n        schema_version="OLA-060",\n        engine_id="OLA-060",\n        controlled_launch_package_ready=True,\n        launch_binding_identity=id(\n            launch_binding\n        ),\n        callable_binding_identity=id(\n            callable_binding\n        ),\n        controlled_invoker_identity=id(\n            controlled_invoker\n        ),\n        runner_identity=id(\n            runner\n        ),\n    )\n\n    launch_package = SimpleNamespace(\n        record=package_record,\n        launch_binding=launch_binding,\n        callable_binding=callable_binding,\n        controlled_invoker=controlled_invoker,\n        runner=runner,\n    )\n\n    invocation_permit = SimpleNamespace(\n        schema_version="OLA-061",\n        engine_id="OLA-061",\n        source_package_identity=id(\n            launch_package\n        ),\n        callable_binding_identity=id(\n            callable_binding\n        ),\n        controlled_invoker_identity=id(\n            controlled_invoker\n        ),\n        runner_identity=id(\n            runner\n        ),\n        package_consumed=True,\n        invocation_permit_issued=True,\n        invocation_permit_consumed=False,\n        read_only=True,\n        execution_allowed=False,\n    )\n\n    return (\n        launch_package,\n        invocation_permit,\n    )\n\n\ndef main() -> None:\n    (\n        launch_package,\n        invocation_permit,\n    ) = make_package_and_permit()\n\n    executor = (\n        OracleProductionLiveShadowControlledLaunchPermitExecutor()\n    )\n\n    record, result = executor.execute(\n        invocation_permit=invocation_permit,\n        launch_package=launch_package,\n    )\n\n    assert record.schema_version == "OLA-062"\n    assert record.engine_id == "OLA-062"\n\n    assert (\n        record.invocation_permit_consumed\n        is True\n    )\n\n    assert (\n        record.controlled_invocation_completed\n        is True\n    )\n\n    assert record.read_only is True\n    assert record.execution_allowed is False\n\n    assert result == {\n        "status": "launched_once",\n        "read_only": True,\n        "execution_allowed": False,\n    }\n\n    try:\n        executor.execute(\n            invocation_permit=invocation_permit,\n            launch_package=launch_package,\n        )\n\n    except (\n        OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked\n    ):\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-062 must reject replay of the same OLA-061 permit"\n        )\n\n    (\n        other_package,\n        other_permit,\n    ) = make_package_and_permit()\n\n    try:\n        (\n            OracleProductionLiveShadowControlledLaunchPermitExecutor()\n            .execute(\n                invocation_permit=other_permit,\n                launch_package=launch_package,\n            )\n        )\n\n    except (\n        OracleProductionLiveShadowControlledLaunchPermitExecutionBlocked\n    ):\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-062 must reject permit/package identity mismatch"\n        )\n\n    source = OLA030.read_text(\n        encoding="utf-8"\n    )\n\n    ast.parse(\n        source\n    )\n\n    required = (\n        "OracleProductionLiveShadowControlledLaunchPermitExecutor",\n\n        "production_controlled_launch_permit_executor = (",\n\n        \'"production_controlled_launch_permit_executor": (\',\n    )\n\n    for marker in required:\n        assert marker in source, marker\n\n    consumer_pos = source.index(\n        "production_controlled_launch_package_consumer = ("\n    )\n\n    executor_pos = source.index(\n        "production_controlled_launch_permit_executor = ("\n    )\n\n    return_pos = source.index(\n        "    return {",\n        executor_pos,\n    )\n\n    assert (\n        consumer_pos\n        < executor_pos\n        < return_pos\n    )\n\n    graph_source = source[\n        source.index(\n            "def build_real_oracle_shadow_graph("\n        ):\n    ]\n\n    forbidden = (\n        "production_start_authorization_consumer.consume(",\n        "production_launch_binder.bind(",\n        "production_exact_runner_launch_callable_binder.bind(",\n        "production_controlled_launch_package_assembler.assemble(",\n        "production_controlled_launch_package_consumer.consume(",\n        "production_controlled_launch_permit_executor.execute(",\n        "production_controlled_launch_invoker.invoke(",\n    )\n\n    for marker in forbidden:\n        assert marker not in graph_source, marker\n\n    print(\n        "[PASS] OLA-062 "\n        "Production Live Shadow Controlled Launch Permit Execution"\n    )\n\n    print({\n        "schema_version": "OLA-062",\n        "engine_id": "OLA-062",\n        "status": "passed",\n\n        "actual_ola030_launch_permit_executor_integrated": True,\n\n        "ola061_invocation_permit_required": True,\n\n        "ola060_launch_package_required": True,\n\n        "permit_package_identity_preserved": True,\n\n        "runner_identity_preserved": True,\n\n        "controlled_invoker_identity_preserved": True,\n\n        "callable_binding_identity_preserved": True,\n\n        "single_use_permit_consumption_enforced": True,\n\n        "permit_replay_rejected": True,\n\n        "permit_package_mismatch_rejected": True,\n\n        "controlled_invocation_completed": True,\n\n        "no_process_created": True,\n\n        "no_thread_created": True,\n\n        "no_background_loop_started": True,\n\n        "read_only": True,\n\n        "execution_allowed": False,\n\n        "alerts_allowed": False,\n\n        "qseries_handoff_allowed": False,\n\n        "execution_adapter_resolved": False,\n\n        "execution_adapter_invoked": False,\n\n        "trade_authorization_allowed": False,\n\n        "order_placement_allowed": False,\n\n        "funds_moved": False,\n\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(
    source: str,
) -> str:

    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_consumption "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPackageConsumer,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_permit_execution "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPermitExecutor,\n"
        ")\n"
    )

    if (
        "OracleProductionLiveShadowControlledLaunchPermitExecutor"
        not in source
    ):

        if import_anchor not in source:
            raise RuntimeError(
                "OLA-061 import anchor not found. "
                "Install and pass OLA-061 first."
            )

        source = source.replace(
            import_anchor,
            new_import,
            1,
        )

    consumer_marker = (
        "    production_controlled_launch_package_consumer = (\n"
    )

    if consumer_marker not in source:
        raise RuntimeError(
            "OLA-061 launch package consumer block not found"
        )

    if (
        "production_controlled_launch_permit_executor = ("
        not in source
    ):

        consumer_pos = source.index(
            consumer_marker
        )

        return_pos = source.index(
            "    return {",
            consumer_pos,
        )

        executor_block = (
            "    production_controlled_launch_permit_executor = (\n"
            "        OracleProductionLiveShadowControlledLaunchPermitExecutor()\n"
            "    )\n\n"
        )

        source = (
            source[:return_pos]
            + executor_block
            + source[return_pos:]
        )

    return_anchor = (
        '        "production_controlled_launch_package_consumer": (\n'
        "            production_controlled_launch_package_consumer\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_controlled_launch_permit_executor": (\n'
        "            production_controlled_launch_permit_executor\n"
        "        ),\n"
    )

    if (
        '"production_controlled_launch_permit_executor": ('
        not in source
    ):

        if return_anchor not in source:
            raise RuntimeError(
                "OLA-061 return-map anchor not found"
            )

        source = source.replace(
            return_anchor,
            return_block,
            1,
        )

    return source


def main() -> None:
    print("========================================")
    print(" OLA-062 INSTALLER")
    print(" PRODUCTION LIVE SHADOW CONTROLLED LAUNCH PERMIT EXECUTION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(
            f"[ERROR] Missing OLA-030 production graph: {OLA030}"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchPackageConsumer",

        "production_controlled_launch_package_consumer = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-061 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    MODULE.write_text(
        MODULE_TEXT,
        encoding="utf-8",
    )

    print(
        "[OK] Wrote OLA-062 controlled launch permit execution module: "
        f"{MODULE}"
    )

    patched = patch_ola030(
        source
    )

    OLA030.write_text(
        patched,
        encoding="utf-8",
    )

    print(
        "[OK] Integrated OLA-062 into actual OLA-030 graph: "
        f"{OLA030}"
    )

    TEST.write_text(
        TEST_TEXT,
        encoding="utf-8",
    )

    print(
        f"[OK] Wrote regression test: {TEST}"
    )

    compile(
        MODULE.read_text(
            encoding="utf-8"
        ),
        str(MODULE),
        "exec",
    )

    compile(
        OLA030.read_text(
            encoding="utf-8"
        ),
        str(OLA030),
        "exec",
    )

    compile(
        TEST.read_text(
            encoding="utf-8"
        ),
        str(TEST),
        "exec",
    )

    print(
        "\n[DONE] OLA-062 production live shadow "
        "controlled launch permit execution installed"
    )

    print("\nRun:")

    print(
        "py test_ola_062_production_live_shadow_"
        "controlled_launch_permit_execution.py"
    )


if __name__ == "__main__":
    main()
