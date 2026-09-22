import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def _clear_qseries_modules() -> None:
    for name in list(sys.modules):
        if name == "qseries_v2" or name.startswith("qseries_v2."):
            del sys.modules[name]


def main() -> int:
    print("=" * 40)
    print(" OIT-004 CORRECTION V2 TEST")
    print(" BOUNDED LIVE INTELLIGENCE ACTIVATION")
    print("=" * 40)

    installed_root = Path(__file__).resolve().parent
    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"

    with TemporaryDirectory() as temporary:
        root = Path(temporary)

        qseries = root / "qseries_v2"
        oracle_intelligence = qseries / "oracle_intelligence"
        terminal = qseries / "oracle_terminal"
        analytics = oracle_intelligence / "analytics"
        live = oracle_intelligence / "live_acquisition"
        operator = qseries / "oracle_operator_runtime"
        runtime_input = root / "runtime" / "oracle_research"

        for directory in (
            qseries,
            oracle_intelligence,
            terminal,
            analytics,
            live,
            operator,
            runtime_input,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        # Explicit package roots are required so Python cannot fall through
        # to the real repository package during isolated import resolution.
        for package_dir in (
            qseries,
            oracle_intelligence,
            terminal,
            analytics,
            live,
            operator,
        ):
            (package_dir / "__init__.py").write_text("", encoding="utf-8")

        for name in (
            "oracle_open_intelligence_terminal_foundation.py",
            "oracle_live_intelligence_runtime_discovery_and_binding.py",
            "oracle_live_intelligence_activation_discovery.py",
            "oracle_bounded_live_intelligence_activation.py",
        ):
            source = installed_terminal / name
            if not source.is_file():
                raise AssertionError(f"installed OIT source missing: {source}")
            (terminal / name).write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        (operator / "oracle_operator_runtime_final_completion_and_freeze_gate.py").write_text(
            "SCHEMA_VERSION = 'OOR-013'\n",
            encoding="utf-8",
        )

        (live / "oracle_live_contract.py").write_text(
            "class LiveInput:\n"
            "    pass\n",
            encoding="utf-8",
        )

        (analytics / "oracle_test_execution_gate.py").write_text(
            "import json\n"
            "from pathlib import Path\n"
            "TARGET = 'runtime/oracle_intelligence/test_output'\n"
            "class OracleTestExecutionGate:\n"
            "    def execute(self, certified_artifacts, execution_context, executed_at, persist):\n"
            "        assert persist is True\n"
            "        assert certified_artifacts\n"
            "        root = Path.cwd()\n"
            "        target = root / 'runtime' / 'oracle_intelligence' / 'test_output'\n"
            "        target.mkdir(parents=True, exist_ok=True)\n"
            "        output = {\n"
            "            'status': 'ok',\n"
            "            'artifact_count': len(certified_artifacts),\n"
            "            'executed_at': executed_at.isoformat(),\n"
            "            'activation_mode': execution_context['activation_mode'],\n"
            "        }\n"
            "        (target / 'genuine.json').write_text(\n"
            "            json.dumps(output, sort_keys=True) + '\\n',\n"
            "            encoding='utf-8',\n"
            "        )\n"
            "        return output\n",
            encoding="utf-8",
        )

        payload = {
            "schema_version": "TEST-1",
            "status": "certified",
            "receipt_hash": "a" * 64,
            "certified_artifacts": [{"artifact_id": "genuine-1"}],
        }
        (runtime_input / "certified_research_artifacts.json").write_text(
            json.dumps(payload, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        old_path = list(sys.path)
        old_cwd = Path.cwd()
        try:
            os.chdir(root)
            sys.path.insert(0, str(root))
            _clear_qseries_modules()

            module = __import__(
                "qseries_v2.oracle_terminal.oracle_bounded_live_intelligence_activation",
                fromlist=["*"],
            )

            loaded_path = Path(module.__file__).resolve()
            expected_path = (
                terminal / "oracle_bounded_live_intelligence_activation.py"
            ).resolve()
            assert loaded_path == expected_path, (
                f"isolated module resolution failed: {loaded_path} != {expected_path}"
            )

            candidates = module.discover_genuine_input_candidates(
                repository_root=root
            )
            assert candidates
            assert (
                candidates[0].relative_path
                == "runtime/oracle_research/certified_research_artifacts.json"
            )

            readiness = module.inspect_bounded_activation(
                repository_root=root
            )
            assert readiness.activation_readiness == "ready_for_activate_once"
            assert readiness.activation_attempted is False

            receipt = module.activate_once(repository_root=root)
            assert module.verify_bounded_activation_receipt(receipt)
            assert receipt.invocation_completed
            assert receipt.analytics_execution_performed
            assert receipt.new_intelligence_artifacts
            assert receipt.protected_source_unchanged
            assert receipt.outside_target_runtime_unchanged
            assert (
                root
                / "runtime"
                / "oracle_intelligence"
                / "test_output"
                / "genuine.json"
            ).is_file()

            rendered = "\n".join(
                module.bounded_activation_lines(receipt)
            )
            assert "invocation_completed: true" in rendered
            assert "database_write_requested: false" in rendered
            assert "publication_allowed: false" in rendered
            assert "qseries_execution_allowed: false" in rendered
            assert "bounded_once: true" in rendered

            try:
                module.activate_once(repository_root=root)
                raise AssertionError("second bounded activation accepted")
            except module.OracleBoundedActivationInvariantError:
                pass
        finally:
            os.chdir(old_cwd)
            sys.path[:] = old_path
            _clear_qseries_modules()

    print("[PASS] Isolated qseries_v2 package root created")
    print("[PASS] Isolated oracle_intelligence package root created")
    print("[PASS] Test analytics gate resolved from temporary repository")
    print("[PASS] Actual OIT-003 discovery contract consumed")
    print("[PASS] Genuine runtime input candidate discovered")
    print("[PASS] Exactly one bounded persist-enabled invocation performed")
    print("[PASS] Genuine runtime/oracle_intelligence artifact required")
    print("[PASS] Protected subsystem source hashes preserved")
    print("[PASS] Runtime mutation outside canonical target rejected")
    print("[PASS] Database writes, publication, and Q Series execution disabled")
    print("[PASS] Second completed activation rejected")
    print("[DONE] OIT-004 CORRECTION V2 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
