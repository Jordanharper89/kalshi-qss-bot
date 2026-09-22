from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_production_live_shadow_controlled_launch_package_assembly.py"
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
    / "test_ola_060_production_live_shadow_"
    "controlled_launch_package_assembly.py"
)

MODULE_TEXT = '"""\nOLA-060 Production Live Shadow Controlled Launch Package Assembly.\n\nAssembles the already-validated production launch components into one\nimmutable, auditable package:\n\nOLA-056 single-use launch token\n    -> OLA-057 exact runner launch binding\n    -> OLA-059 exact runner bound-method binding\n    -> OLA-058 controlled synchronous invoker\n\nOLA-060 performs no invocation. It only verifies cross-component identity\nconsistency and produces a package that a later launch boundary may consume.\n\nOracle remains permanently read-only.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any\n\n\nSCHEMA_VERSION = "OLA-060"\nENGINE_ID = "OLA-060"\nPACKAGE_TYPE = "oracle_production_live_shadow_controlled_launch_package"\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageError(ValueError):\n    pass\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageBlocked(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowControlledLaunchPackageRecord:\n    schema_version: str\n    engine_id: str\n    package_type: str\n\n    launch_token_identity: int\n    launch_binding_identity: int\n    callable_binding_identity: int\n    controlled_invoker_identity: int\n    runner_identity: int\n\n    launch_token_valid: bool\n    launch_binding_valid: bool\n    callable_binding_valid: bool\n    controlled_invoker_valid: bool\n\n    token_to_launch_binding_identity_preserved: bool\n    launch_binding_to_callable_binding_identity_preserved: bool\n    callable_binding_to_runner_identity_preserved: bool\n\n    controlled_launch_package_ready: bool\n\n    launch_invoked: bool = False\n    callable_invoked: bool = False\n\n    process_created: bool = False\n    thread_created: bool = False\n    background_loop_started: bool = False\n\n    read_only: bool = True\n    execution_allowed: bool = False\n\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n    def __post_init__(self) -> None:\n        if self.schema_version != SCHEMA_VERSION:\n            raise OracleProductionLiveShadowControlledLaunchPackageError(\n                "OLA-060 schema_version mismatch"\n            )\n\n        if self.engine_id != ENGINE_ID:\n            raise OracleProductionLiveShadowControlledLaunchPackageError(\n                "OLA-060 engine_id mismatch"\n            )\n\n        if self.package_type != PACKAGE_TYPE:\n            raise OracleProductionLiveShadowControlledLaunchPackageError(\n                "OLA-060 package_type mismatch"\n            )\n\n        required = (\n            self.launch_token_valid,\n            self.launch_binding_valid,\n            self.callable_binding_valid,\n            self.controlled_invoker_valid,\n            self.token_to_launch_binding_identity_preserved,\n            self.launch_binding_to_callable_binding_identity_preserved,\n            self.callable_binding_to_runner_identity_preserved,\n            self.controlled_launch_package_ready,\n            self.read_only,\n        )\n\n        if not all(value is True for value in required):\n            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(\n                "OLA-060 launch package failed closed"\n            )\n\n        forbidden = (\n            self.launch_invoked,\n            self.callable_invoked,\n            self.process_created,\n            self.thread_created,\n            self.background_loop_started,\n            self.execution_allowed,\n            self.alerts_allowed,\n            self.qseries_handoff_allowed,\n            self.execution_adapter_resolved,\n            self.execution_adapter_invoked,\n            self.trade_authorization_allowed,\n            self.order_placement_allowed,\n            self.funds_moved,\n            self.portfolio_mutated,\n        )\n\n        if any(value is True for value in forbidden):\n            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(\n                "OLA-060 observed forbidden activity"\n            )\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowControlledLaunchPackage:\n    record: OracleProductionLiveShadowControlledLaunchPackageRecord\n    launch_token: Any\n    launch_binding: Any\n    callable_binding: Any\n    controlled_invoker: Any\n    runner: Any\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageAssembler:\n    read_only = True\n    execution_allowed = False\n\n    def assemble(\n        self,\n        *,\n        launch_token: Any,\n        launch_binding: Any,\n        callable_binding: Any,\n        controlled_invoker: Any,\n        runner: Any,\n    ) -> OracleProductionLiveShadowControlledLaunchPackage:\n        callable_record = getattr(\n            callable_binding,\n            "record",\n            None,\n        )\n\n        checks = {\n            "launch_token_valid": (\n                getattr(launch_token, "schema_version", None) == "OLA-056"\n                and getattr(launch_token, "engine_id", None) == "OLA-056"\n                and getattr(\n                    launch_token,\n                    "authorization_consumed",\n                    None,\n                )\n                is True\n                and getattr(\n                    launch_token,\n                    "launch_token_issued",\n                    None,\n                )\n                is True\n                and getattr(\n                    launch_token,\n                    "launch_invoked",\n                    None,\n                )\n                is False\n                and getattr(\n                    launch_token,\n                    "read_only",\n                    None,\n                )\n                is True\n                and getattr(\n                    launch_token,\n                    "execution_allowed",\n                    None,\n                )\n                is False\n            ),\n\n            "launch_binding_valid": (\n                getattr(\n                    launch_binding,\n                    "schema_version",\n                    None,\n                )\n                == "OLA-057"\n                and getattr(\n                    launch_binding,\n                    "engine_id",\n                    None,\n                )\n                == "OLA-057"\n                and getattr(\n                    launch_binding,\n                    "launch_binding_ready",\n                    None,\n                )\n                is True\n                and getattr(\n                    launch_binding,\n                    "launch_invoked",\n                    None,\n                )\n                is False\n            ),\n\n            "callable_binding_valid": (\n                getattr(\n                    callable_record,\n                    "schema_version",\n                    None,\n                )\n                == "OLA-059"\n                and getattr(\n                    callable_record,\n                    "engine_id",\n                    None,\n                )\n                == "OLA-059"\n                and getattr(\n                    callable_record,\n                    "callable_binding_ready",\n                    None,\n                )\n                is True\n                and getattr(\n                    callable_record,\n                    "callable_invoked",\n                    None,\n                )\n                is False\n            ),\n\n            "controlled_invoker_valid": (\n                getattr(\n                    controlled_invoker,\n                    "read_only",\n                    None,\n                )\n                is True\n                and getattr(\n                    controlled_invoker,\n                    "execution_allowed",\n                    None,\n                )\n                is False\n            ),\n\n            "token_to_launch_binding_identity_preserved": (\n                getattr(\n                    launch_binding,\n                    "launch_token_identity",\n                    None,\n                )\n                == id(launch_token)\n            ),\n\n            "launch_binding_to_callable_binding_identity_preserved": (\n                getattr(\n                    callable_record,\n                    "source_launch_binding_identity",\n                    None,\n                )\n                == id(launch_binding)\n            ),\n\n            "callable_binding_to_runner_identity_preserved": (\n                getattr(\n                    callable_record,\n                    "runner_identity",\n                    None,\n                )\n                == id(runner)\n                and getattr(\n                    launch_binding,\n                    "runner_identity",\n                    None,\n                )\n                == id(runner)\n            ),\n        }\n\n        if not all(checks.values()):\n            failed = ", ".join(\n                name\n                for name, passed in checks.items()\n                if not passed\n            )\n\n            raise OracleProductionLiveShadowControlledLaunchPackageBlocked(\n                "OLA-060 launch package identity mismatch: "\n                f"{failed}"\n            )\n\n        record = (\n            OracleProductionLiveShadowControlledLaunchPackageRecord(\n                schema_version=SCHEMA_VERSION,\n                engine_id=ENGINE_ID,\n                package_type=PACKAGE_TYPE,\n\n                launch_token_identity=id(\n                    launch_token\n                ),\n\n                launch_binding_identity=id(\n                    launch_binding\n                ),\n\n                callable_binding_identity=id(\n                    callable_binding\n                ),\n\n                controlled_invoker_identity=id(\n                    controlled_invoker\n                ),\n\n                runner_identity=id(\n                    runner\n                ),\n\n                controlled_launch_package_ready=True,\n\n                **checks,\n            )\n        )\n\n        return (\n            OracleProductionLiveShadowControlledLaunchPackage(\n                record=record,\n                launch_token=launch_token,\n                launch_binding=launch_binding,\n                callable_binding=callable_binding,\n                controlled_invoker=controlled_invoker,\n                runner=runner,\n            )\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "PACKAGE_TYPE",\n    "OracleProductionLiveShadowControlledLaunchPackageError",\n    "OracleProductionLiveShadowControlledLaunchPackageBlocked",\n    "OracleProductionLiveShadowControlledLaunchPackageRecord",\n    "OracleProductionLiveShadowControlledLaunchPackage",\n    "OracleProductionLiveShadowControlledLaunchPackageAssembler",\n]\n'

TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_assembly import (\n    OracleProductionLiveShadowControlledLaunchPackageAssembler,\n    OracleProductionLiveShadowControlledLaunchPackageBlocked,\n)\n\n\nROOT = Path(__file__).resolve().parent\n\nOLA030 = (\n    ROOT\n    / "qseries_v2"\n    / "oracle_intelligence"\n    / "live_acquisition_model"\n    / "oracle_first_real_shadow_corpus_launch_command.py"\n)\n\n\nclass Runner:\n    read_only = True\n    execution_allowed = False\n\n    def launch_once(self):\n        return None\n\n\nclass ControlledInvoker:\n    read_only = True\n    execution_allowed = False\n\n\ndef make_components():\n    runner = Runner()\n\n    token = SimpleNamespace(\n        schema_version="OLA-056",\n        engine_id="OLA-056",\n        authorization_consumed=True,\n        launch_token_issued=True,\n        launch_invoked=False,\n        read_only=True,\n        execution_allowed=False,\n    )\n\n    launch_binding = SimpleNamespace(\n        schema_version="OLA-057",\n        engine_id="OLA-057",\n        launch_token_identity=id(token),\n        runner_identity=id(runner),\n        launch_binding_ready=True,\n        launch_invoked=False,\n        read_only=True,\n        execution_allowed=False,\n    )\n\n    callable_record = SimpleNamespace(\n        schema_version="OLA-059",\n        engine_id="OLA-059",\n        source_launch_binding_identity=id(\n            launch_binding\n        ),\n        runner_identity=id(\n            runner\n        ),\n        callable_binding_ready=True,\n        callable_invoked=False,\n    )\n\n    callable_binding = SimpleNamespace(\n        record=callable_record,\n        launch_callable=runner.launch_once,\n    )\n\n    controlled_invoker = ControlledInvoker()\n\n    return (\n        runner,\n        token,\n        launch_binding,\n        callable_binding,\n        controlled_invoker,\n    )\n\n\ndef main() -> None:\n    (\n        runner,\n        token,\n        launch_binding,\n        callable_binding,\n        controlled_invoker,\n    ) = make_components()\n\n    package = (\n        OracleProductionLiveShadowControlledLaunchPackageAssembler()\n        .assemble(\n            launch_token=token,\n            launch_binding=launch_binding,\n            callable_binding=callable_binding,\n            controlled_invoker=controlled_invoker,\n            runner=runner,\n        )\n    )\n\n    record = package.record\n\n    assert record.schema_version == "OLA-060"\n    assert record.engine_id == "OLA-060"\n\n    assert record.launch_token_identity == id(\n        token\n    )\n\n    assert record.launch_binding_identity == id(\n        launch_binding\n    )\n\n    assert record.callable_binding_identity == id(\n        callable_binding\n    )\n\n    assert record.runner_identity == id(\n        runner\n    )\n\n    assert record.launch_token_valid is True\n    assert record.launch_binding_valid is True\n    assert record.callable_binding_valid is True\n    assert record.controlled_invoker_valid is True\n\n    assert (\n        record.token_to_launch_binding_identity_preserved\n        is True\n    )\n\n    assert (\n        record.launch_binding_to_callable_binding_identity_preserved\n        is True\n    )\n\n    assert (\n        record.callable_binding_to_runner_identity_preserved\n        is True\n    )\n\n    assert (\n        record.controlled_launch_package_ready\n        is True\n    )\n\n    assert record.launch_invoked is False\n    assert record.callable_invoked is False\n\n    assert record.read_only is True\n    assert record.execution_allowed is False\n\n    wrong_runner = Runner()\n\n    try:\n        (\n            OracleProductionLiveShadowControlledLaunchPackageAssembler()\n            .assemble(\n                launch_token=token,\n                launch_binding=launch_binding,\n                callable_binding=callable_binding,\n                controlled_invoker=controlled_invoker,\n                runner=wrong_runner,\n            )\n        )\n\n    except OracleProductionLiveShadowControlledLaunchPackageBlocked:\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-060 must reject a runner identity mismatch"\n        )\n\n    bad_binding = SimpleNamespace(\n        **vars(launch_binding)\n    )\n\n    bad_binding.launch_token_identity = -1\n\n    try:\n        (\n            OracleProductionLiveShadowControlledLaunchPackageAssembler()\n            .assemble(\n                launch_token=token,\n                launch_binding=bad_binding,\n                callable_binding=callable_binding,\n                controlled_invoker=controlled_invoker,\n                runner=runner,\n            )\n        )\n\n    except OracleProductionLiveShadowControlledLaunchPackageBlocked:\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-060 must reject a token-to-binding identity mismatch"\n        )\n\n    source = OLA030.read_text(\n        encoding="utf-8"\n    )\n\n    ast.parse(\n        source\n    )\n\n    required = (\n        "OracleProductionLiveShadowControlledLaunchPackageAssembler",\n        "production_controlled_launch_package_assembler = (",\n        \'"production_controlled_launch_package_assembler": (\',\n    )\n\n    for marker in required:\n        assert marker in source, marker\n\n    callable_binder_pos = source.index(\n        "production_exact_runner_launch_callable_binder = ("\n    )\n\n    package_assembler_pos = source.index(\n        "production_controlled_launch_package_assembler = ("\n    )\n\n    return_pos = source.index(\n        "    return {",\n        package_assembler_pos,\n    )\n\n    assert (\n        callable_binder_pos\n        < package_assembler_pos\n        < return_pos\n    )\n\n    graph_source = source[\n        source.index(\n            "def build_real_oracle_shadow_graph("\n        ):\n    ]\n\n    forbidden = (\n        "production_start_authorization_consumer.consume(",\n        "production_launch_binder.bind(",\n        "production_exact_runner_launch_callable_binder.bind(",\n        "production_controlled_launch_package_assembler.assemble(",\n        "production_controlled_launch_invoker.invoke(",\n        "runner.run(",\n        "runner.start(",\n        "runner.launch(",\n    )\n\n    for marker in forbidden:\n        assert marker not in graph_source, marker\n\n    print(\n        "[PASS] OLA-060 "\n        "Production Live Shadow Controlled Launch Package Assembly"\n    )\n\n    print({\n        "schema_version": "OLA-060",\n        "engine_id": "OLA-060",\n        "status": "passed",\n\n        "actual_ola030_launch_package_assembler_integrated": True,\n\n        "ola056_launch_token_required": True,\n\n        "ola057_launch_binding_required": True,\n\n        "ola059_exact_callable_binding_required": True,\n\n        "ola058_controlled_invoker_required": True,\n\n        "token_to_launch_binding_identity_preserved": True,\n\n        "launch_binding_to_callable_binding_identity_preserved": True,\n\n        "callable_binding_to_runner_identity_preserved": True,\n\n        "controlled_launch_package_ready": True,\n\n        "launch_not_invoked": True,\n\n        "callable_not_invoked": True,\n\n        "runner_identity_mismatch_rejected": True,\n\n        "token_binding_identity_mismatch_rejected": True,\n\n        "no_process_created": True,\n\n        "no_thread_created": True,\n\n        "no_background_loop_started": True,\n\n        "read_only": True,\n\n        "execution_allowed": False,\n\n        "alerts_allowed": False,\n\n        "qseries_handoff_allowed": False,\n\n        "execution_adapter_resolved": False,\n\n        "execution_adapter_invoked": False,\n\n        "trade_authorization_allowed": False,\n\n        "order_placement_allowed": False,\n\n        "funds_moved": False,\n\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(
    source: str,
) -> str:

    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_exact_runner_launch_callable_binding import (\n"
        "    OracleExactRunnerLaunchCallableBinder,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_assembly "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPackageAssembler,\n"
        ")\n"
    )

    if (
        "OracleProductionLiveShadowControlledLaunchPackageAssembler"
        not in source
    ):

        if import_anchor not in source:
            raise RuntimeError(
                "OLA-059 import anchor not found. "
                "Install and pass OLA-059 first."
            )

        source = source.replace(
            import_anchor,
            new_import,
            1,
        )

    callable_binder_marker = (
        "    production_exact_runner_launch_callable_binder = (\n"
    )

    if callable_binder_marker not in source:
        raise RuntimeError(
            "OLA-059 callable binder block not found"
        )

    if (
        "production_controlled_launch_package_assembler = ("
        not in source
    ):

        callable_binder_pos = source.index(
            callable_binder_marker
        )

        return_pos = source.index(
            "    return {",
            callable_binder_pos,
        )

        assembler_block = (
            "    production_controlled_launch_package_assembler = (\n"
            "        OracleProductionLiveShadowControlledLaunchPackageAssembler()\n"
            "    )\n\n"
        )

        source = (
            source[:return_pos]
            + assembler_block
            + source[return_pos:]
        )

    return_anchor = (
        '        "production_exact_runner_launch_callable_binder": (\n'
        "            production_exact_runner_launch_callable_binder\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_controlled_launch_package_assembler": (\n'
        "            production_controlled_launch_package_assembler\n"
        "        ),\n"
    )

    if (
        '"production_controlled_launch_package_assembler": ('
        not in source
    ):

        if return_anchor not in source:
            raise RuntimeError(
                "OLA-059 return-map anchor not found"
            )

        source = source.replace(
            return_anchor,
            return_block,
            1,
        )

    return source


def main() -> None:
    print("========================================")
    print(" OLA-060 INSTALLER")
    print(" PRODUCTION LIVE SHADOW CONTROLLED LAUNCH PACKAGE ASSEMBLY")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(
            f"[ERROR] Missing OLA-030 production graph: {OLA030}"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleExactRunnerLaunchCallableBinder",

        "production_exact_runner_launch_callable_binder = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-059 production integration is incomplete. "
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
        "[OK] Wrote OLA-060 controlled launch package module: "
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
        "[OK] Integrated OLA-060 into actual OLA-030 graph: "
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
        "\n[DONE] OLA-060 production live shadow "
        "controlled launch package assembly installed"
    )

    print("\nRun:")

    print(
        "py test_ola_060_production_live_shadow_"
        "controlled_launch_package_assembly.py"
    )


if __name__ == "__main__":
    main()
