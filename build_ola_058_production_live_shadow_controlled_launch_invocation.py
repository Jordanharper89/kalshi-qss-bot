from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / "qseries_v2/oracle_intelligence/live_acquisition/oracle_production_live_shadow_controlled_launch_invocation.py"
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"
TEST = ROOT / "test_ola_058_production_live_shadow_controlled_launch_invocation.py"

MODULE_TEXT = '"""\nOLA-058 Production Live Shadow Controlled Launch Invocation.\n\nFail-closed invocation adapter requiring an OLA-057 launch binding and the\nexact bound production runner identity before a synchronous launch call may be\ndelegated. This module does not create a process, thread, or background loop,\nand it never enables alerts, Q Series handoff, or execution.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any, Callable\n\nSCHEMA_VERSION = "OLA-058"\nENGINE_ID = "OLA-058"\nINVOCATION_TYPE = "oracle_production_live_shadow_controlled_launch_invocation"\n\n\nclass OracleProductionLiveShadowControlledLaunchInvocationError(ValueError):\n    pass\n\n\nclass OracleProductionLiveShadowControlledLaunchInvocationBlocked(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowControlledLaunchInvocationRecord:\n    schema_version: str\n    engine_id: str\n    invocation_type: str\n    source_binding_schema_version: str\n    source_binding_engine_id: str\n    source_binding_identity: int\n    runner_identity: int\n    launch_binding_valid: bool\n    exact_runner_identity_preserved: bool\n    synchronous_invocation_allowed: bool\n    invocation_completed: bool\n    process_created: bool = False\n    thread_created: bool = False\n    background_loop_started: bool = False\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n    read_only: bool = True\n    execution_allowed: bool = False\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n    def __post_init__(self) -> None:\n        if self.schema_version != SCHEMA_VERSION:\n            raise OracleProductionLiveShadowControlledLaunchInvocationError(\n                "OLA-058 schema_version mismatch"\n            )\n        if self.engine_id != ENGINE_ID:\n            raise OracleProductionLiveShadowControlledLaunchInvocationError(\n                "OLA-058 engine_id mismatch"\n            )\n        if self.invocation_type != INVOCATION_TYPE:\n            raise OracleProductionLiveShadowControlledLaunchInvocationError(\n                "OLA-058 invocation_type mismatch"\n            )\n\n        required = (\n            self.launch_binding_valid,\n            self.exact_runner_identity_preserved,\n            self.synchronous_invocation_allowed,\n            self.invocation_completed,\n            self.read_only,\n        )\n        if not all(value is True for value in required):\n            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(\n                "OLA-058 invocation record failed closed"\n            )\n\n        forbidden = (\n            self.process_created,\n            self.thread_created,\n            self.background_loop_started,\n            self.alerts_allowed,\n            self.qseries_handoff_allowed,\n            self.execution_allowed,\n            self.execution_adapter_resolved,\n            self.execution_adapter_invoked,\n            self.trade_authorization_allowed,\n            self.order_placement_allowed,\n            self.funds_moved,\n            self.portfolio_mutated,\n        )\n        if any(value is True for value in forbidden):\n            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(\n                "OLA-058 observed forbidden activity"\n            )\n\n\nclass OracleProductionLiveShadowControlledLaunchInvoker:\n    read_only = True\n    execution_allowed = False\n\n    def invoke(\n        self,\n        *,\n        launch_binding: Any,\n        runner: Any,\n        launch_callable: Callable[[], Any],\n    ) -> tuple[\n        OracleProductionLiveShadowControlledLaunchInvocationRecord,\n        Any,\n    ]:\n        checks = (\n            getattr(launch_binding, "schema_version", None) == "OLA-057",\n            getattr(launch_binding, "engine_id", None) == "OLA-057",\n            getattr(launch_binding, "launch_binding_ready", None) is True,\n            getattr(launch_binding, "launch_invoked", None) is False,\n            getattr(launch_binding, "runner_identity", None) == id(runner),\n            getattr(launch_binding, "read_only", None) is True,\n            getattr(launch_binding, "execution_allowed", None) is False,\n            getattr(runner, "read_only", None) is True,\n            getattr(runner, "execution_allowed", None) is False,\n            callable(launch_callable),\n        )\n\n        if not all(checks):\n            raise OracleProductionLiveShadowControlledLaunchInvocationBlocked(\n                "OLA-058 launch invocation eligibility failed closed"\n            )\n\n        result = launch_callable()\n\n        record = OracleProductionLiveShadowControlledLaunchInvocationRecord(\n            schema_version=SCHEMA_VERSION,\n            engine_id=ENGINE_ID,\n            invocation_type=INVOCATION_TYPE,\n            source_binding_schema_version=launch_binding.schema_version,\n            source_binding_engine_id=launch_binding.engine_id,\n            source_binding_identity=id(launch_binding),\n            runner_identity=id(runner),\n            launch_binding_valid=True,\n            exact_runner_identity_preserved=True,\n            synchronous_invocation_allowed=True,\n            invocation_completed=True,\n        )\n\n        return record, result\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "INVOCATION_TYPE",\n    "OracleProductionLiveShadowControlledLaunchInvocationError",\n    "OracleProductionLiveShadowControlledLaunchInvocationBlocked",\n    "OracleProductionLiveShadowControlledLaunchInvocationRecord",\n    "OracleProductionLiveShadowControlledLaunchInvoker",\n]\n'
TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_controlled_launch_invocation import (\n    OracleProductionLiveShadowControlledLaunchInvocationBlocked,\n    OracleProductionLiveShadowControlledLaunchInvoker,\n)\n\nROOT = Path(__file__).resolve().parent\nOLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"\n\n\nclass Runner:\n    read_only = True\n    execution_allowed = False\n\n\ndef make_binding(runner):\n    return SimpleNamespace(\n        schema_version="OLA-057",\n        engine_id="OLA-057",\n        launch_binding_ready=True,\n        launch_invoked=False,\n        runner_identity=id(runner),\n        read_only=True,\n        execution_allowed=False,\n    )\n\n\ndef main() -> None:\n    runner = Runner()\n    binding = make_binding(runner)\n    calls = []\n\n    def launch_callable():\n        calls.append("called")\n        return {"status": "completed", "read_only": True}\n\n    record, result = OracleProductionLiveShadowControlledLaunchInvoker().invoke(\n        launch_binding=binding,\n        runner=runner,\n        launch_callable=launch_callable,\n    )\n\n    assert calls == ["called"]\n    assert result == {"status": "completed", "read_only": True}\n    assert record.schema_version == "OLA-058"\n    assert record.engine_id == "OLA-058"\n    assert record.launch_binding_valid is True\n    assert record.exact_runner_identity_preserved is True\n    assert record.synchronous_invocation_allowed is True\n    assert record.invocation_completed is True\n    assert record.process_created is False\n    assert record.thread_created is False\n    assert record.background_loop_started is False\n    assert record.read_only is True\n    assert record.execution_allowed is False\n\n    wrong_runner = Runner()\n    try:\n        OracleProductionLiveShadowControlledLaunchInvoker().invoke(\n            launch_binding=binding,\n            runner=wrong_runner,\n            launch_callable=lambda: None,\n        )\n    except OracleProductionLiveShadowControlledLaunchInvocationBlocked:\n        pass\n    else:\n        raise AssertionError(\n            "OLA-058 must fail closed on runner identity mismatch"\n        )\n\n    bad_binding = make_binding(runner)\n    bad_binding.launch_invoked = True\n    try:\n        OracleProductionLiveShadowControlledLaunchInvoker().invoke(\n            launch_binding=bad_binding,\n            runner=runner,\n            launch_callable=lambda: None,\n        )\n    except OracleProductionLiveShadowControlledLaunchInvocationBlocked:\n        pass\n    else:\n        raise AssertionError(\n            "OLA-058 must fail closed for an already-invoked binding"\n        )\n\n    source = OLA030.read_text(encoding="utf-8")\n    ast.parse(source)\n\n    required = (\n        "OracleProductionLiveShadowControlledLaunchInvoker",\n        "production_controlled_launch_invoker = (",\n        \'"production_controlled_launch_invoker": (\',\n    )\n    for marker in required:\n        assert marker in source, marker\n\n    binder_pos = source.index("production_launch_binder = (")\n    invoker_pos = source.index("production_controlled_launch_invoker = (")\n    return_pos = source.index("    return {", invoker_pos)\n    assert binder_pos < invoker_pos < return_pos\n\n    graph_source = source[source.index("def build_real_oracle_shadow_graph("):]\n    forbidden = (\n        "production_start_authorization_consumer.consume(",\n        "production_launch_binder.bind(",\n        "production_controlled_launch_invoker.invoke(",\n        "runner.run(",\n        "runner.start(",\n        "runner.launch(",\n    )\n    for marker in forbidden:\n        assert marker not in graph_source, marker\n\n    print("[PASS] OLA-058 Production Live Shadow Controlled Launch Invocation")\n    print({\n        "schema_version": "OLA-058",\n        "engine_id": "OLA-058",\n        "status": "passed",\n        "actual_ola030_controlled_launch_invoker_integrated": True,\n        "ola057_launch_binding_required": True,\n        "exact_runner_identity_required": True,\n        "single_synchronous_invocation_tested": True,\n        "runner_identity_mismatch_rejected": True,\n        "already_invoked_binding_rejected": True,\n        "no_process_created": True,\n        "no_thread_created": True,\n        "no_background_loop_started": True,\n        "read_only": True,\n        "execution_allowed": False,\n        "alerts_allowed": False,\n        "qseries_handoff_allowed": False,\n        "execution_adapter_resolved": False,\n        "execution_adapter_invoked": False,\n        "trade_authorization_allowed": False,\n        "order_placement_allowed": False,\n        "funds_moved": False,\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_launch_binding import (\n"
        "    OracleProductionLiveShadowLaunchBinder,\n"
        ")\n"
    )
    new_import = import_anchor + (
        "\nfrom qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_invocation import (\n"
        "    OracleProductionLiveShadowControlledLaunchInvoker,\n"
        ")\n"
    )

    if "OracleProductionLiveShadowControlledLaunchInvoker" not in source:
        if import_anchor not in source:
            raise RuntimeError(
                "OLA-057 import anchor not found. Install and pass OLA-057 first."
            )
        source = source.replace(import_anchor, new_import, 1)

    binder_marker = "    production_launch_binder = (\n"
    if binder_marker not in source:
        raise RuntimeError("OLA-057 launch binder block not found")

    if "production_controlled_launch_invoker = (" not in source:
        binder_pos = source.index(binder_marker)
        return_pos = source.index("    return {", binder_pos)
        invoker_block = (
            "    production_controlled_launch_invoker = (\n"
            "        OracleProductionLiveShadowControlledLaunchInvoker()\n"
            "    )\n\n"
        )
        source = source[:return_pos] + invoker_block + source[return_pos:]

    return_anchor = (
        '        "production_launch_binder": (\n'
        "            production_launch_binder\n"
        "        ),\n"
    )
    return_block = return_anchor + (
        '        "production_controlled_launch_invoker": (\n'
        "            production_controlled_launch_invoker\n"
        "        ),\n"
    )

    if '"production_controlled_launch_invoker": (' not in source:
        if return_anchor not in source:
            raise RuntimeError("OLA-057 return-map anchor not found")
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-058 INSTALLER")
    print(" PRODUCTION LIVE SHADOW CONTROLLED LAUNCH INVOCATION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")
    required = (
        "OracleProductionLiveShadowLaunchBinder",
        "production_launch_binder = (",
    )
    missing = [marker for marker in required if marker not in source]
    if missing:
        raise SystemExit(
            "[ERROR] OLA-057 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-058 controlled launch invocation module: {MODULE}")

    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding="utf-8")
    print(f"[OK] Integrated OLA-058 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-058 production live shadow "
        "controlled launch invocation installed"
    )
    print("\nRun:")
    print("py test_ola_058_production_live_shadow_controlled_launch_invocation.py")


if __name__ == "__main__":
    main()
