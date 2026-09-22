from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_production_live_shadow_controlled_launch_package_consumption.py"
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
    / "test_ola_061_production_live_shadow_"
    "controlled_launch_package_consumption.py"
)

MODULE_TEXT = '"""\nOLA-061 Production Live Shadow Controlled Launch Package Consumption.\n\nConsumes an OLA-060 controlled launch package exactly once and issues a\nsingle-use invocation permit.\n\nThis module does not invoke the OLA-058 controlled invoker, does not invoke the\nbound runner method, and does not start any process, thread, or background\nloop.\n\nOracle remains permanently read-only.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom threading import Lock\nfrom typing import Any\n\n\nSCHEMA_VERSION = "OLA-061"\nENGINE_ID = "OLA-061"\nPERMIT_TYPE = "oracle_production_live_shadow_single_use_invocation_permit"\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageConsumptionError(\n    ValueError\n):\n    pass\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(\n    RuntimeError\n):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowSingleUseInvocationPermit:\n    schema_version: str\n    engine_id: str\n    permit_type: str\n\n    source_package_schema_version: str\n    source_package_engine_id: str\n    source_package_identity: int\n\n    launch_token_identity: int\n    launch_binding_identity: int\n    callable_binding_identity: int\n    controlled_invoker_identity: int\n    runner_identity: int\n\n    package_consumed: bool\n    invocation_permit_issued: bool\n\n    invocation_permit_consumed: bool = False\n    launch_invoked: bool = False\n    callable_invoked: bool = False\n\n    process_created: bool = False\n    thread_created: bool = False\n    background_loop_started: bool = False\n\n    read_only: bool = True\n    execution_allowed: bool = False\n\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n    def __post_init__(self) -> None:\n        if self.schema_version != SCHEMA_VERSION:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(\n                    "OLA-061 schema_version mismatch"\n                )\n            )\n\n        if self.engine_id != ENGINE_ID:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(\n                    "OLA-061 engine_id mismatch"\n                )\n            )\n\n        if self.permit_type != PERMIT_TYPE:\n            raise (\n                OracleProductionLiveShadowControlledLaunchPackageConsumptionError(\n                    "OLA-061 permit_type mismatch"\n                )\n            )\n\n        required = (\n            self.package_consumed,\n            self.invocation_permit_issued,\n            self.read_only,\n        )\n\n        if not all(value is True for value in required):\n            raise (\n                OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(\n                    "OLA-061 permit issuance failed closed"\n                )\n            )\n\n        forbidden = (\n            self.invocation_permit_consumed,\n            self.launch_invoked,\n            self.callable_invoked,\n            self.process_created,\n            self.thread_created,\n            self.background_loop_started,\n            self.execution_allowed,\n            self.alerts_allowed,\n            self.qseries_handoff_allowed,\n            self.execution_adapter_resolved,\n            self.execution_adapter_invoked,\n            self.trade_authorization_allowed,\n            self.order_placement_allowed,\n            self.funds_moved,\n            self.portfolio_mutated,\n        )\n\n        if any(value is True for value in forbidden):\n            raise (\n                OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(\n                    "OLA-061 observed forbidden activity"\n                )\n            )\n\n\nclass OracleProductionLiveShadowControlledLaunchPackageConsumer:\n    read_only = True\n    execution_allowed = False\n\n    def __init__(self) -> None:\n        self._lock = Lock()\n        self._consumed_package_identities: set[int] = set()\n\n    def consume(\n        self,\n        *,\n        launch_package: Any,\n    ) -> OracleProductionLiveShadowSingleUseInvocationPermit:\n        with self._lock:\n            package_identity = id(\n                launch_package\n            )\n\n            if (\n                package_identity\n                in self._consumed_package_identities\n            ):\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(\n                        "OLA-060 launch package already consumed"\n                    )\n                )\n\n            record = getattr(\n                launch_package,\n                "record",\n                None,\n            )\n\n            checks = (\n                getattr(\n                    record,\n                    "schema_version",\n                    None,\n                )\n                == "OLA-060",\n\n                getattr(\n                    record,\n                    "engine_id",\n                    None,\n                )\n                == "OLA-060",\n\n                getattr(\n                    record,\n                    "controlled_launch_package_ready",\n                    None,\n                )\n                is True,\n\n                getattr(\n                    record,\n                    "launch_invoked",\n                    None,\n                )\n                is False,\n\n                getattr(\n                    record,\n                    "callable_invoked",\n                    None,\n                )\n                is False,\n\n                getattr(\n                    record,\n                    "read_only",\n                    None,\n                )\n                is True,\n\n                getattr(\n                    record,\n                    "execution_allowed",\n                    None,\n                )\n                is False,\n            )\n\n            if not all(checks):\n                raise (\n                    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked(\n                        "OLA-060 launch package is not eligible "\n                        "for OLA-061 consumption"\n                    )\n                )\n\n            self._consumed_package_identities.add(\n                package_identity\n            )\n\n            return (\n                OracleProductionLiveShadowSingleUseInvocationPermit(\n                    schema_version=SCHEMA_VERSION,\n                    engine_id=ENGINE_ID,\n                    permit_type=PERMIT_TYPE,\n\n                    source_package_schema_version=(\n                        record.schema_version\n                    ),\n\n                    source_package_engine_id=(\n                        record.engine_id\n                    ),\n\n                    source_package_identity=(\n                        package_identity\n                    ),\n\n                    launch_token_identity=(\n                        record.launch_token_identity\n                    ),\n\n                    launch_binding_identity=(\n                        record.launch_binding_identity\n                    ),\n\n                    callable_binding_identity=(\n                        record.callable_binding_identity\n                    ),\n\n                    controlled_invoker_identity=(\n                        record.controlled_invoker_identity\n                    ),\n\n                    runner_identity=(\n                        record.runner_identity\n                    ),\n\n                    package_consumed=True,\n\n                    invocation_permit_issued=True,\n                )\n            )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "PERMIT_TYPE",\n    "OracleProductionLiveShadowControlledLaunchPackageConsumptionError",\n    "OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked",\n    "OracleProductionLiveShadowSingleUseInvocationPermit",\n    "OracleProductionLiveShadowControlledLaunchPackageConsumer",\n]\n'

TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_package_consumption import (\n    OracleProductionLiveShadowControlledLaunchPackageConsumer,\n    OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked,\n)\n\n\nROOT = Path(__file__).resolve().parent\n\nOLA030 = (\n    ROOT\n    / "qseries_v2"\n    / "oracle_intelligence"\n    / "live_acquisition_model"\n    / "oracle_first_real_shadow_corpus_launch_command.py"\n)\n\n\ndef make_package():\n    record = SimpleNamespace(\n        schema_version="OLA-060",\n        engine_id="OLA-060",\n\n        launch_token_identity=101,\n        launch_binding_identity=202,\n        callable_binding_identity=303,\n        controlled_invoker_identity=404,\n        runner_identity=505,\n\n        controlled_launch_package_ready=True,\n\n        launch_invoked=False,\n        callable_invoked=False,\n\n        read_only=True,\n        execution_allowed=False,\n    )\n\n    return SimpleNamespace(\n        record=record,\n    )\n\n\ndef main() -> None:\n    package = make_package()\n\n    consumer = (\n        OracleProductionLiveShadowControlledLaunchPackageConsumer()\n    )\n\n    permit = consumer.consume(\n        launch_package=package,\n    )\n\n    assert permit.schema_version == "OLA-061"\n    assert permit.engine_id == "OLA-061"\n\n    assert (\n        permit.source_package_identity\n        == id(package)\n    )\n\n    assert permit.package_consumed is True\n\n    assert (\n        permit.invocation_permit_issued\n        is True\n    )\n\n    assert (\n        permit.invocation_permit_consumed\n        is False\n    )\n\n    assert permit.launch_invoked is False\n\n    assert permit.callable_invoked is False\n\n    assert permit.read_only is True\n\n    assert permit.execution_allowed is False\n\n    try:\n        consumer.consume(\n            launch_package=package,\n        )\n\n    except (\n        OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked\n    ):\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-061 must reject replay of the same OLA-060 package"\n        )\n\n    invalid_package = make_package()\n\n    invalid_package.record.launch_invoked = True\n\n    try:\n        (\n            OracleProductionLiveShadowControlledLaunchPackageConsumer()\n            .consume(\n                launch_package=invalid_package,\n            )\n        )\n\n    except (\n        OracleProductionLiveShadowControlledLaunchPackageConsumptionBlocked\n    ):\n        pass\n\n    else:\n        raise AssertionError(\n            "OLA-061 must reject an already-invoked OLA-060 package"\n        )\n\n    source = OLA030.read_text(\n        encoding="utf-8"\n    )\n\n    ast.parse(\n        source\n    )\n\n    required = (\n        "OracleProductionLiveShadowControlledLaunchPackageConsumer",\n\n        "production_controlled_launch_package_consumer = (",\n\n        \'"production_controlled_launch_package_consumer": (\',\n    )\n\n    for marker in required:\n        assert marker in source, marker\n\n    assembler_pos = source.index(\n        "production_controlled_launch_package_assembler = ("\n    )\n\n    consumer_pos = source.index(\n        "production_controlled_launch_package_consumer = ("\n    )\n\n    return_pos = source.index(\n        "    return {",\n        consumer_pos,\n    )\n\n    assert (\n        assembler_pos\n        < consumer_pos\n        < return_pos\n    )\n\n    graph_source = source[\n        source.index(\n            "def build_real_oracle_shadow_graph("\n        ):\n    ]\n\n    forbidden = (\n        "production_start_authorization_consumer.consume(",\n\n        "production_launch_binder.bind(",\n\n        "production_exact_runner_launch_callable_binder.bind(",\n\n        "production_controlled_launch_package_assembler.assemble(",\n\n        "production_controlled_launch_package_consumer.consume(",\n\n        "production_controlled_launch_invoker.invoke(",\n\n        "runner.run(",\n\n        "runner.start(",\n\n        "runner.launch(",\n    )\n\n    for marker in forbidden:\n        assert marker not in graph_source, marker\n\n    print(\n        "[PASS] OLA-061 "\n        "Production Live Shadow Controlled Launch Package Consumption"\n    )\n\n    print({\n        "schema_version": "OLA-061",\n\n        "engine_id": "OLA-061",\n\n        "status": "passed",\n\n        "actual_ola030_launch_package_consumer_integrated": True,\n\n        "ola060_launch_package_required": True,\n\n        "single_use_package_consumption_enforced": True,\n\n        "package_replay_rejected": True,\n\n        "already_invoked_package_rejected": True,\n\n        "invocation_permit_issued": True,\n\n        "invocation_permit_not_consumed": True,\n\n        "launch_not_invoked": True,\n\n        "callable_not_invoked": True,\n\n        "no_process_created": True,\n\n        "no_thread_created": True,\n\n        "no_background_loop_started": True,\n\n        "read_only": True,\n\n        "execution_allowed": False,\n\n        "alerts_allowed": False,\n\n        "qseries_handoff_allowed": False,\n\n        "execution_adapter_resolved": False,\n\n        "execution_adapter_invoked": False,\n\n        "trade_authorization_allowed": False,\n\n        "order_placement_allowed": False,\n\n        "funds_moved": False,\n\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(
    source: str,
) -> str:

    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_assembly "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPackageAssembler,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_package_consumption "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPackageConsumer,\n"
        ")\n"
    )

    if (
        "OracleProductionLiveShadowControlledLaunchPackageConsumer"
        not in source
    ):

        if import_anchor not in source:
            raise RuntimeError(
                "OLA-060 import anchor not found. "
                "Install and pass OLA-060 first."
            )

        source = source.replace(
            import_anchor,
            new_import,
            1,
        )

    assembler_marker = (
        "    production_controlled_launch_package_assembler = (\n"
    )

    if assembler_marker not in source:
        raise RuntimeError(
            "OLA-060 package assembler block not found"
        )

    if (
        "production_controlled_launch_package_consumer = ("
        not in source
    ):

        assembler_pos = source.index(
            assembler_marker
        )

        return_pos = source.index(
            "    return {",
            assembler_pos,
        )

        consumer_block = (
            "    production_controlled_launch_package_consumer = (\n"
            "        OracleProductionLiveShadowControlledLaunchPackageConsumer()\n"
            "    )\n\n"
        )

        source = (
            source[:return_pos]
            + consumer_block
            + source[return_pos:]
        )

    return_anchor = (
        '        "production_controlled_launch_package_assembler": (\n'
        "            production_controlled_launch_package_assembler\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_controlled_launch_package_consumer": (\n'
        "            production_controlled_launch_package_consumer\n"
        "        ),\n"
    )

    if (
        '"production_controlled_launch_package_consumer": ('
        not in source
    ):

        if return_anchor not in source:
            raise RuntimeError(
                "OLA-060 return-map anchor not found"
            )

        source = source.replace(
            return_anchor,
            return_block,
            1,
        )

    return source


def main() -> None:
    print("========================================")
    print(" OLA-061 INSTALLER")
    print(" PRODUCTION LIVE SHADOW CONTROLLED LAUNCH PACKAGE CONSUMPTION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(
            f"[ERROR] Missing OLA-030 production graph: {OLA030}"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchPackageAssembler",

        "production_controlled_launch_package_assembler = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-060 production integration is incomplete. "
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
        "[OK] Wrote OLA-061 launch package consumption module: "
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
        "[OK] Integrated OLA-061 into actual OLA-030 graph: "
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
        "\n[DONE] OLA-061 production live shadow "
        "controlled launch package consumption installed"
    )

    print("\nRun:")

    print(
        "py test_ola_061_production_live_shadow_"
        "controlled_launch_package_consumption.py"
    )


if __name__ == "__main__":
    main()
