from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_exact_runner_launch_callable_binding.py"
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
    / "test_ola_059_exact_runner_launch_callable_binding.py"
)

MODULE_TEXT = '"""\nOLA-059 Exact Runner Launch Callable Binding.\n\nFail-closed binding between the exact OLA-023 production runner instance and\nthe exact bound method that a later controlled launch invocation may call.\n\nThis closes the remaining OLA-058 gap where an arbitrary callable could be\nsupplied even when the runner identity itself was correct.\n\nOLA-059 does not invoke the callable.\n"""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Any, Callable\n\nSCHEMA_VERSION = "OLA-059"\nENGINE_ID = "OLA-059"\nBINDING_TYPE = "oracle_exact_runner_launch_callable_binding"\n\n\nclass OracleExactRunnerLaunchCallableBindingError(ValueError):\n    pass\n\n\nclass OracleExactRunnerLaunchCallableBindingBlocked(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleExactRunnerLaunchCallableBindingRecord:\n    schema_version: str\n    engine_id: str\n    binding_type: str\n    source_launch_binding_schema_version: str\n    source_launch_binding_engine_id: str\n    source_launch_binding_identity: int\n    runner_identity: int\n    callable_owner_identity: int\n    callable_function_identity: int\n    launch_binding_valid: bool\n    exact_runner_identity_preserved: bool\n    callable_is_bound_method: bool\n    callable_bound_to_exact_runner: bool\n    callable_binding_ready: bool\n    callable_invoked: bool = False\n    process_created: bool = False\n    thread_created: bool = False\n    background_loop_started: bool = False\n    read_only: bool = True\n    execution_allowed: bool = False\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n    def __post_init__(self) -> None:\n        if self.schema_version != SCHEMA_VERSION:\n            raise OracleExactRunnerLaunchCallableBindingError(\n                "OLA-059 schema_version mismatch"\n            )\n        if self.engine_id != ENGINE_ID:\n            raise OracleExactRunnerLaunchCallableBindingError(\n                "OLA-059 engine_id mismatch"\n            )\n        if self.binding_type != BINDING_TYPE:\n            raise OracleExactRunnerLaunchCallableBindingError(\n                "OLA-059 binding_type mismatch"\n            )\n\n        required = (\n            self.launch_binding_valid,\n            self.exact_runner_identity_preserved,\n            self.callable_is_bound_method,\n            self.callable_bound_to_exact_runner,\n            self.callable_binding_ready,\n            self.read_only,\n        )\n\n        if not all(value is True for value in required):\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 callable binding failed closed"\n            )\n\n        forbidden = (\n            self.callable_invoked,\n            self.process_created,\n            self.thread_created,\n            self.background_loop_started,\n            self.execution_allowed,\n            self.alerts_allowed,\n            self.qseries_handoff_allowed,\n            self.execution_adapter_resolved,\n            self.execution_adapter_invoked,\n            self.trade_authorization_allowed,\n            self.order_placement_allowed,\n            self.funds_moved,\n            self.portfolio_mutated,\n        )\n\n        if any(value is True for value in forbidden):\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 observed forbidden activity"\n            )\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleExactRunnerLaunchCallableBinding:\n    record: OracleExactRunnerLaunchCallableBindingRecord\n    launch_callable: Callable[[], Any]\n\n\nclass OracleExactRunnerLaunchCallableBinder:\n    read_only = True\n    execution_allowed = False\n\n    def bind(\n        self,\n        *,\n        launch_binding: Any,\n        runner: Any,\n        launch_callable: Callable[[], Any],\n    ) -> OracleExactRunnerLaunchCallableBinding:\n        if (\n            getattr(launch_binding, "schema_version", None) != "OLA-057"\n            or getattr(launch_binding, "engine_id", None) != "OLA-057"\n            or getattr(launch_binding, "launch_binding_ready", None) is not True\n            or getattr(launch_binding, "launch_invoked", None) is not False\n            or getattr(launch_binding, "runner_identity", None) != id(runner)\n            or getattr(launch_binding, "read_only", None) is not True\n            or getattr(launch_binding, "execution_allowed", None) is not False\n        ):\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-057 launch binding is not eligible for OLA-059"\n            )\n\n        if (\n            getattr(runner, "read_only", None) is not True\n            or getattr(runner, "execution_allowed", None) is not False\n        ):\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 runner invariants failed closed"\n            )\n\n        if not callable(launch_callable):\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 launch_callable is not callable"\n            )\n\n        callable_owner = getattr(launch_callable, "__self__", None)\n        callable_function = getattr(launch_callable, "__func__", None)\n\n        if callable_owner is None or callable_function is None:\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 requires a bound runner method"\n            )\n\n        if callable_owner is not runner:\n            raise OracleExactRunnerLaunchCallableBindingBlocked(\n                "OLA-059 callable is not bound to the exact runner"\n            )\n\n        record = OracleExactRunnerLaunchCallableBindingRecord(\n            schema_version=SCHEMA_VERSION,\n            engine_id=ENGINE_ID,\n            binding_type=BINDING_TYPE,\n            source_launch_binding_schema_version=launch_binding.schema_version,\n            source_launch_binding_engine_id=launch_binding.engine_id,\n            source_launch_binding_identity=id(launch_binding),\n            runner_identity=id(runner),\n            callable_owner_identity=id(callable_owner),\n            callable_function_identity=id(callable_function),\n            launch_binding_valid=True,\n            exact_runner_identity_preserved=True,\n            callable_is_bound_method=True,\n            callable_bound_to_exact_runner=True,\n            callable_binding_ready=True,\n        )\n\n        return OracleExactRunnerLaunchCallableBinding(\n            record=record,\n            launch_callable=launch_callable,\n        )\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "BINDING_TYPE",\n    "OracleExactRunnerLaunchCallableBindingError",\n    "OracleExactRunnerLaunchCallableBindingBlocked",\n    "OracleExactRunnerLaunchCallableBindingRecord",\n    "OracleExactRunnerLaunchCallableBinding",\n    "OracleExactRunnerLaunchCallableBinder",\n]\n'
TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_exact_runner_launch_callable_binding import (\n    OracleExactRunnerLaunchCallableBinder,\n    OracleExactRunnerLaunchCallableBindingBlocked,\n)\n\nROOT = Path(__file__).resolve().parent\n\nOLA030 = (\n    ROOT\n    / "qseries_v2"\n    / "oracle_intelligence"\n    / "live_acquisition_model"\n    / "oracle_first_real_shadow_corpus_launch_command.py"\n)\n\n\nclass Runner:\n    read_only = True\n    execution_allowed = False\n\n    def launch_once(self):\n        return {\n            "status": "not_invoked_by_ola059",\n            "read_only": True,\n        }\n\n\ndef make_launch_binding(runner):\n    return SimpleNamespace(\n        schema_version="OLA-057",\n        engine_id="OLA-057",\n        launch_binding_ready=True,\n        launch_invoked=False,\n        runner_identity=id(runner),\n        read_only=True,\n        execution_allowed=False,\n    )\n\n\ndef main() -> None:\n    runner = Runner()\n    launch_binding = make_launch_binding(runner)\n\n    binding = OracleExactRunnerLaunchCallableBinder().bind(\n        launch_binding=launch_binding,\n        runner=runner,\n        launch_callable=runner.launch_once,\n    )\n\n    record = binding.record\n\n    assert record.schema_version == "OLA-059"\n    assert record.engine_id == "OLA-059"\n    assert record.runner_identity == id(runner)\n    assert record.callable_owner_identity == id(runner)\n    assert record.launch_binding_valid is True\n    assert record.exact_runner_identity_preserved is True\n    assert record.callable_is_bound_method is True\n    assert record.callable_bound_to_exact_runner is True\n    assert record.callable_binding_ready is True\n    assert record.callable_invoked is False\n    assert record.read_only is True\n    assert record.execution_allowed is False\n    assert binding.launch_callable.__self__ is runner\n\n    wrong_runner = Runner()\n\n    try:\n        OracleExactRunnerLaunchCallableBinder().bind(\n            launch_binding=launch_binding,\n            runner=runner,\n            launch_callable=wrong_runner.launch_once,\n        )\n    except OracleExactRunnerLaunchCallableBindingBlocked:\n        pass\n    else:\n        raise AssertionError(\n            "OLA-059 must reject a callable bound to the wrong runner"\n        )\n\n    try:\n        OracleExactRunnerLaunchCallableBinder().bind(\n            launch_binding=launch_binding,\n            runner=runner,\n            launch_callable=lambda: None,\n        )\n    except OracleExactRunnerLaunchCallableBindingBlocked:\n        pass\n    else:\n        raise AssertionError(\n            "OLA-059 must reject an arbitrary unbound callable"\n        )\n\n    source = OLA030.read_text(encoding="utf-8")\n    ast.parse(source)\n\n    required = (\n        "OracleExactRunnerLaunchCallableBinder",\n        "production_exact_runner_launch_callable_binder = (",\n        \'"production_exact_runner_launch_callable_binder": (\',\n    )\n\n    for marker in required:\n        assert marker in source, marker\n\n    invoker_pos = source.index(\n        "production_controlled_launch_invoker = ("\n    )\n\n    callable_binder_pos = source.index(\n        "production_exact_runner_launch_callable_binder = ("\n    )\n\n    return_pos = source.index(\n        "    return {",\n        callable_binder_pos,\n    )\n\n    assert invoker_pos < callable_binder_pos < return_pos\n\n    graph_source = source[\n        source.index("def build_real_oracle_shadow_graph("):\n    ]\n\n    forbidden = (\n        "production_start_authorization_consumer.consume(",\n        "production_launch_binder.bind(",\n        "production_exact_runner_launch_callable_binder.bind(",\n        "production_controlled_launch_invoker.invoke(",\n        "runner.run(",\n        "runner.start(",\n        "runner.launch(",\n    )\n\n    for marker in forbidden:\n        assert marker not in graph_source, marker\n\n    print("[PASS] OLA-059 Exact Runner Launch Callable Binding")\n\n    print({\n        "schema_version": "OLA-059",\n        "engine_id": "OLA-059",\n        "status": "passed",\n        "actual_ola030_exact_callable_binder_integrated": True,\n        "ola057_launch_binding_required": True,\n        "exact_runner_identity_required": True,\n        "bound_method_required": True,\n        "callable_bound_to_exact_runner": True,\n        "arbitrary_callable_rejected": True,\n        "wrong_runner_bound_method_rejected": True,\n        "callable_not_invoked": True,\n        "no_process_created": True,\n        "no_thread_created": True,\n        "no_background_loop_started": True,\n        "read_only": True,\n        "execution_allowed": False,\n        "alerts_allowed": False,\n        "qseries_handoff_allowed": False,\n        "execution_adapter_resolved": False,\n        "execution_adapter_invoked": False,\n        "trade_authorization_allowed": False,\n        "order_placement_allowed": False,\n        "funds_moved": False,\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_invocation import (\n"
        "    OracleProductionLiveShadowControlledLaunchInvoker,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_exact_runner_launch_callable_binding import (\n"
        "    OracleExactRunnerLaunchCallableBinder,\n"
        ")\n"
    )

    if "OracleExactRunnerLaunchCallableBinder" not in source:
        if import_anchor not in source:
            raise RuntimeError(
                "OLA-058 import anchor not found. "
                "Install and pass OLA-058 first."
            )

        source = source.replace(
            import_anchor,
            new_import,
            1,
        )

    invoker_marker = (
        "    production_controlled_launch_invoker = (\n"
    )

    if invoker_marker not in source:
        raise RuntimeError(
            "OLA-058 controlled launch invoker block not found"
        )

    if "production_exact_runner_launch_callable_binder = (" not in source:
        invoker_pos = source.index(invoker_marker)

        return_pos = source.index(
            "    return {",
            invoker_pos,
        )

        binder_block = (
            "    production_exact_runner_launch_callable_binder = (\n"
            "        OracleExactRunnerLaunchCallableBinder()\n"
            "    )\n\n"
        )

        source = (
            source[:return_pos]
            + binder_block
            + source[return_pos:]
        )

    return_anchor = (
        '        "production_controlled_launch_invoker": (\n'
        "            production_controlled_launch_invoker\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_exact_runner_launch_callable_binder": (\n'
        "            production_exact_runner_launch_callable_binder\n"
        "        ),\n"
    )

    if '"production_exact_runner_launch_callable_binder": (' not in source:
        if return_anchor not in source:
            raise RuntimeError(
                "OLA-058 return-map anchor not found"
            )

        source = source.replace(
            return_anchor,
            return_block,
            1,
        )

    return source


def main() -> None:
    print("========================================")
    print(" OLA-059 INSTALLER")
    print(" EXACT RUNNER LAUNCH CALLABLE BINDING")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(
            f"[ERROR] Missing OLA-030 production graph: {OLA030}"
        )

    source = OLA030.read_text(
        encoding="utf-8"
    )

    required = (
        "OracleProductionLiveShadowControlledLaunchInvoker",
        "production_controlled_launch_invoker = (",
    )

    missing = [
        marker
        for marker in required
        if marker not in source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-058 production integration is incomplete. "
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
        "[OK] Wrote OLA-059 exact runner callable binding module: "
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
        "[OK] Integrated OLA-059 into actual OLA-030 graph: "
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
        MODULE.read_text(encoding="utf-8"),
        str(MODULE),
        "exec",
    )

    compile(
        OLA030.read_text(encoding="utf-8"),
        str(OLA030),
        "exec",
    )

    compile(
        TEST.read_text(encoding="utf-8"),
        str(TEST),
        "exec",
    )

    print(
        "\n[DONE] OLA-059 exact runner "
        "launch callable binding installed"
    )

    print("\nRun:")

    print(
        "py test_ola_059_exact_runner_launch_callable_binding.py"
    )


if __name__ == "__main__":
    main()
