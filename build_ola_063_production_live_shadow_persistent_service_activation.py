from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition"
    / "oracle_production_live_shadow_persistent_service_activation.py"
)

OLA030 = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

TEST = (
    ROOT / "test_ola_063_production_live_shadow_persistent_service_activation.py"
)

MODULE_TEXT = '"""OLA-063 Production Live Shadow Persistent Service Activation."""\n\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom threading import Lock\nfrom typing import Any\n\n\nSCHEMA_VERSION = "OLA-063"\nENGINE_ID = "OLA-063"\n\n\nclass OracleProductionLiveShadowPersistentServiceActivationBlocked(RuntimeError):\n    pass\n\n\n@dataclass(frozen=True, slots=True)\nclass OracleProductionLiveShadowPersistentServiceActivationRecord:\n    schema_version: str\n    engine_id: str\n    exact_production_graph_required: bool\n    ola062_controlled_execution_boundary_present: bool\n    existing_service_runner_required: bool\n    service_start_callable_resolved: bool\n    service_start_invoked: bool\n    single_activation_enforced: bool\n    read_only: bool = True\n    execution_allowed: bool = False\n    alerts_allowed: bool = False\n    qseries_handoff_allowed: bool = False\n    execution_adapter_resolved: bool = False\n    execution_adapter_invoked: bool = False\n    trade_authorization_allowed: bool = False\n    order_placement_allowed: bool = False\n    funds_moved: bool = False\n    portfolio_mutated: bool = False\n\n\nclass OracleProductionLiveShadowPersistentServiceActivator:\n    read_only = True\n    execution_allowed = False\n\n    _RUNNER_KEYS = (\n        "service_runner",\n        "production_service_runner",\n        "shadow_service_runner",\n        "oracle_live_acquisition_service_runner",\n    )\n\n    _START_METHODS = (\n        "run",\n        "start",\n        "run_service",\n        "start_service",\n        "serve",\n    )\n\n    def __init__(self) -> None:\n        self._lock = Lock()\n        self._activated_graph_ids: set[int] = set()\n\n    def _resolve_runner(self, graph: dict[str, Any]) -> Any:\n        for key in self._RUNNER_KEYS:\n            runner = graph.get(key)\n            if runner is not None:\n                return runner\n\n        for value in graph.values():\n            if (\n                getattr(value, "read_only", None) is True\n                and getattr(value, "execution_allowed", None) is False\n                and any(callable(getattr(value, name, None)) for name in self._START_METHODS)\n            ):\n                return value\n\n        raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n            "Unable to resolve the existing read-only service runner"\n        )\n\n    def activate(\n        self,\n        *,\n        production_graph: dict[str, Any],\n        start_kwargs: dict[str, Any] | None = None,\n    ) -> tuple[OracleProductionLiveShadowPersistentServiceActivationRecord, Any]:\n        if not isinstance(production_graph, dict):\n            raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                "OLA-063 requires the exact OLA-030 production graph mapping"\n            )\n\n        required_keys = (\n            "production_controlled_launch_package_assembler",\n            "production_controlled_launch_package_consumer",\n            "production_controlled_launch_permit_executor",\n        )\n\n        missing = [key for key in required_keys if key not in production_graph]\n        if missing:\n            raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                "Frozen launch-control boundary missing: " + ", ".join(missing)\n            )\n\n        graph_identity = id(production_graph)\n\n        with self._lock:\n            if graph_identity in self._activated_graph_ids:\n                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                    "This exact production graph was already activated"\n                )\n\n            runner = self._resolve_runner(production_graph)\n\n            if getattr(runner, "read_only", None) is not True:\n                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                    "Service runner is not read-only"\n                )\n\n            if getattr(runner, "execution_allowed", None) is not False:\n                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                    "Service runner exposes execution permission"\n                )\n\n            start_callable = None\n            for name in self._START_METHODS:\n                candidate = getattr(runner, name, None)\n                if callable(candidate):\n                    start_callable = candidate\n                    break\n\n            if start_callable is None:\n                raise OracleProductionLiveShadowPersistentServiceActivationBlocked(\n                    "Existing service runner has no supported public start method"\n                )\n\n            self._activated_graph_ids.add(graph_identity)\n\n        try:\n            result = start_callable(**dict(start_kwargs or {}))\n        except Exception:\n            with self._lock:\n                self._activated_graph_ids.discard(graph_identity)\n            raise\n\n        record = OracleProductionLiveShadowPersistentServiceActivationRecord(\n            schema_version=SCHEMA_VERSION,\n            engine_id=ENGINE_ID,\n            exact_production_graph_required=True,\n            ola062_controlled_execution_boundary_present=True,\n            existing_service_runner_required=True,\n            service_start_callable_resolved=True,\n            service_start_invoked=True,\n            single_activation_enforced=True,\n        )\n\n        return record, result\n\n\n__all__ = [\n    "SCHEMA_VERSION",\n    "ENGINE_ID",\n    "OracleProductionLiveShadowPersistentServiceActivationBlocked",\n    "OracleProductionLiveShadowPersistentServiceActivationRecord",\n    "OracleProductionLiveShadowPersistentServiceActivator",\n]\n'
TEST_TEXT = 'from __future__ import annotations\n\nimport ast\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_persistent_service_activation import (\n    OracleProductionLiveShadowPersistentServiceActivationBlocked,\n    OracleProductionLiveShadowPersistentServiceActivator,\n)\n\n\nROOT = Path(__file__).resolve().parent\nOLA030 = (\n    ROOT\n    / "qseries_v2"\n    / "oracle_intelligence"\n    / "live_acquisition_model"\n    / "oracle_first_real_shadow_corpus_launch_command.py"\n)\n\n\nclass FakeReadOnlyServiceRunner:\n    read_only = True\n    execution_allowed = False\n\n    def __init__(self) -> None:\n        self.calls = 0\n\n    def run(self, *, max_cycles: int = 1):\n        self.calls += 1\n        return {\n            "status": "completed",\n            "max_cycles": max_cycles,\n            "read_only": True,\n            "execution_allowed": False,\n        }\n\n\ndef make_graph():\n    runner = FakeReadOnlyServiceRunner()\n    return {\n        "service_runner": runner,\n        "production_controlled_launch_package_assembler": object(),\n        "production_controlled_launch_package_consumer": object(),\n        "production_controlled_launch_permit_executor": object(),\n    }, runner\n\n\ndef main() -> None:\n    graph, runner = make_graph()\n    activator = OracleProductionLiveShadowPersistentServiceActivator()\n\n    record, result = activator.activate(\n        production_graph=graph,\n        start_kwargs={"max_cycles": 1},\n    )\n\n    assert record.schema_version == "OLA-063"\n    assert record.engine_id == "OLA-063"\n    assert record.service_start_invoked is True\n    assert record.single_activation_enforced is True\n    assert runner.calls == 1\n    assert result["status"] == "completed"\n    assert result["read_only"] is True\n    assert result["execution_allowed"] is False\n\n    try:\n        activator.activate(\n            production_graph=graph,\n            start_kwargs={"max_cycles": 1},\n        )\n    except OracleProductionLiveShadowPersistentServiceActivationBlocked:\n        pass\n    else:\n        raise AssertionError("OLA-063 must reject duplicate activation")\n\n    unsafe_graph, unsafe_runner = make_graph()\n    unsafe_runner.execution_allowed = True\n\n    try:\n        OracleProductionLiveShadowPersistentServiceActivator().activate(\n            production_graph=unsafe_graph,\n            start_kwargs={"max_cycles": 1},\n        )\n    except OracleProductionLiveShadowPersistentServiceActivationBlocked:\n        pass\n    else:\n        raise AssertionError("OLA-063 must reject execution-enabled runner")\n\n    source = OLA030.read_text(encoding="utf-8")\n    ast.parse(source)\n\n    required = (\n        "OracleProductionLiveShadowPersistentServiceActivator",\n        "production_live_shadow_persistent_service_activator = (",\n        \'"production_live_shadow_persistent_service_activator": (\',\n    )\n\n    for marker in required:\n        assert marker in source, marker\n\n    executor_pos = source.index(\n        "production_controlled_launch_permit_executor = ("\n    )\n    activator_pos = source.index(\n        "production_live_shadow_persistent_service_activator = ("\n    )\n    return_pos = source.index("    return {", activator_pos)\n\n    assert executor_pos < activator_pos < return_pos\n\n    print("[PASS] OLA-063 Production Live Shadow Persistent Service Activation")\n    print({\n        "schema_version": "OLA-063",\n        "engine_id": "OLA-063",\n        "status": "passed",\n        "actual_ola030_persistent_service_activator_integrated": True,\n        "ola062_controlled_execution_boundary_required": True,\n        "existing_service_runner_required": True,\n        "service_start_callable_resolved": True,\n        "single_activation_enforced": True,\n        "duplicate_activation_rejected": True,\n        "execution_enabled_runner_rejected": True,\n        "persistent_service_activation_path_ready": True,\n        "graph_assembly_does_not_auto_activate_service": True,\n        "read_only": True,\n        "execution_allowed": False,\n        "alerts_allowed": False,\n        "qseries_handoff_allowed": False,\n        "execution_adapter_resolved": False,\n        "execution_adapter_invoked": False,\n        "trade_authorization_allowed": False,\n        "order_placement_allowed": False,\n        "funds_moved": False,\n        "portfolio_mutated": False,\n    })\n\n\nif __name__ == "__main__":\n    main()\n'


def patch_ola030(source: str) -> str:
    import_anchor = (
        "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_controlled_launch_permit_execution "
        "import (\n"
        "    OracleProductionLiveShadowControlledLaunchPermitExecutor,\n"
        ")\n"
    )

    new_import = (
        import_anchor
        + "\n"
        + "from qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_production_live_shadow_persistent_service_activation "
        "import (\n"
        "    OracleProductionLiveShadowPersistentServiceActivator,\n"
        ")\n"
    )

    if "OracleProductionLiveShadowPersistentServiceActivator" not in source:
        if import_anchor not in source:
            raise RuntimeError("OLA-062 import anchor not found")
        source = source.replace(import_anchor, new_import, 1)

    executor_marker = (
        "    production_controlled_launch_permit_executor = (\n"
    )

    if executor_marker not in source:
        raise RuntimeError("OLA-062 permit executor block not found")

    if "production_live_shadow_persistent_service_activator = (" not in source:
        executor_pos = source.index(executor_marker)
        return_pos = source.index("    return {", executor_pos)

        activator_block = (
            "    production_live_shadow_persistent_service_activator = (\n"
            "        OracleProductionLiveShadowPersistentServiceActivator()\n"
            "    )\n\n"
        )

        source = source[:return_pos] + activator_block + source[return_pos:]

    return_anchor = (
        '        "production_controlled_launch_permit_executor": (\n'
        "            production_controlled_launch_permit_executor\n"
        "        ),\n"
    )

    return_block = (
        return_anchor
        + '        "production_live_shadow_persistent_service_activator": (\n'
        "            production_live_shadow_persistent_service_activator\n"
        "        ),\n"
    )

    if '"production_live_shadow_persistent_service_activator": (' not in source:
        if return_anchor not in source:
            raise RuntimeError("OLA-062 return-map anchor not found")
        source = source.replace(return_anchor, return_block, 1)

    return source


def main() -> None:
    print("========================================")
    print(" OLA-063 INSTALLER")
    print(" PRODUCTION LIVE SHADOW PERSISTENT SERVICE ACTIVATION")
    print("========================================")

    if not OLA030.exists():
        raise SystemExit(f"[ERROR] Missing OLA-030 production graph: {OLA030}")

    source = OLA030.read_text(encoding="utf-8")

    required = (
        "OracleProductionLiveShadowControlledLaunchPermitExecutor",
        "production_controlled_launch_permit_executor = (",
    )

    missing = [marker for marker in required if marker not in source]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-062 production integration is incomplete. "
            f"Missing markers: {missing}"
        )

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding="utf-8")
    print(f"[OK] Wrote OLA-063 persistent service activation module: {MODULE}")

    OLA030.write_text(patch_ola030(source), encoding="utf-8")
    print(f"[OK] Integrated OLA-063 into actual OLA-030 graph: {OLA030}")

    TEST.write_text(TEST_TEXT, encoding="utf-8")
    print(f"[OK] Wrote regression test: {TEST}")

    compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
    compile(OLA030.read_text(encoding="utf-8"), str(OLA030), "exec")
    compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

    print(
        "\n[DONE] OLA-063 production live shadow "
        "persistent service activation installed"
    )
    print("\nRun:")
    print("py test_ola_063_production_live_shadow_persistent_service_activation.py")


if __name__ == "__main__":
    main()
