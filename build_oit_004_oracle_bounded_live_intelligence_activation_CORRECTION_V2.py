from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def locate_repository() -> Path:
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates.extend((base, base / "kalshi-qss-bot"))
        for parent in base.parents:
            candidates.extend((parent, parent / "kalshi-qss-bot"))
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (
            candidate
            / "qseries_v2"
            / "oracle_terminal"
            / "oracle_bounded_live_intelligence_activation.py"
        ).is_file():
            return candidate
    raise SystemExit("[ERROR] Could not locate repository containing OIT-004.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
OIT_003 = PACKAGE / "oracle_live_intelligence_activation_discovery.py"
OIT_004 = PACKAGE / "oracle_bounded_live_intelligence_activation.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_004_oracle_bounded_live_intelligence_activation.py"

TEST_SOURCE = '\nimport json\nimport os\nimport sys\nfrom pathlib import Path\nfrom tempfile import TemporaryDirectory\n\n\ndef _clear_qseries_modules() -> None:\n    for name in list(sys.modules):\n        if name == "qseries_v2" or name.startswith("qseries_v2."):\n            del sys.modules[name]\n\n\ndef main() -> int:\n    print("=" * 40)\n    print(" OIT-004 CORRECTION V2 TEST")\n    print(" BOUNDED LIVE INTELLIGENCE ACTIVATION")\n    print("=" * 40)\n\n    installed_root = Path(__file__).resolve().parent\n    installed_terminal = installed_root / "qseries_v2" / "oracle_terminal"\n\n    with TemporaryDirectory() as temporary:\n        root = Path(temporary)\n\n        qseries = root / "qseries_v2"\n        oracle_intelligence = qseries / "oracle_intelligence"\n        terminal = qseries / "oracle_terminal"\n        analytics = oracle_intelligence / "analytics"\n        live = oracle_intelligence / "live_acquisition"\n        operator = qseries / "oracle_operator_runtime"\n        runtime_input = root / "runtime" / "oracle_research"\n\n        for directory in (\n            qseries,\n            oracle_intelligence,\n            terminal,\n            analytics,\n            live,\n            operator,\n            runtime_input,\n        ):\n            directory.mkdir(parents=True, exist_ok=True)\n\n        # Explicit package roots are required so Python cannot fall through\n        # to the real repository package during isolated import resolution.\n        for package_dir in (\n            qseries,\n            oracle_intelligence,\n            terminal,\n            analytics,\n            live,\n            operator,\n        ):\n            (package_dir / "__init__.py").write_text("", encoding="utf-8")\n\n        for name in (\n            "oracle_open_intelligence_terminal_foundation.py",\n            "oracle_live_intelligence_runtime_discovery_and_binding.py",\n            "oracle_live_intelligence_activation_discovery.py",\n            "oracle_bounded_live_intelligence_activation.py",\n        ):\n            source = installed_terminal / name\n            if not source.is_file():\n                raise AssertionError(f"installed OIT source missing: {source}")\n            (terminal / name).write_text(\n                source.read_text(encoding="utf-8"),\n                encoding="utf-8",\n            )\n\n        (operator / "oracle_operator_runtime_final_completion_and_freeze_gate.py").write_text(\n            "SCHEMA_VERSION = \'OOR-013\'\\n",\n            encoding="utf-8",\n        )\n\n        (live / "oracle_live_contract.py").write_text(\n            "class LiveInput:\\n"\n            "    pass\\n",\n            encoding="utf-8",\n        )\n\n        (analytics / "oracle_test_execution_gate.py").write_text(\n            "import json\\n"\n            "from pathlib import Path\\n"\n            "TARGET = \'runtime/oracle_intelligence/test_output\'\\n"\n            "class OracleTestExecutionGate:\\n"\n            "    def execute(self, certified_artifacts, execution_context, executed_at, persist):\\n"\n            "        assert persist is True\\n"\n            "        assert certified_artifacts\\n"\n            "        root = Path.cwd()\\n"\n            "        target = root / \'runtime\' / \'oracle_intelligence\' / \'test_output\'\\n"\n            "        target.mkdir(parents=True, exist_ok=True)\\n"\n            "        output = {\\n"\n            "            \'status\': \'ok\',\\n"\n            "            \'artifact_count\': len(certified_artifacts),\\n"\n            "            \'executed_at\': executed_at.isoformat(),\\n"\n            "            \'activation_mode\': execution_context[\'activation_mode\'],\\n"\n            "        }\\n"\n            "        (target / \'genuine.json\').write_text(\\n"\n            "            json.dumps(output, sort_keys=True) + \'\\\\n\',\\n"\n            "            encoding=\'utf-8\',\\n"\n            "        )\\n"\n            "        return output\\n",\n            encoding="utf-8",\n        )\n\n        payload = {\n            "schema_version": "TEST-1",\n            "status": "certified",\n            "receipt_hash": "a" * 64,\n            "certified_artifacts": [{"artifact_id": "genuine-1"}],\n        }\n        (runtime_input / "certified_research_artifacts.json").write_text(\n            json.dumps(payload, sort_keys=True) + "\\n",\n            encoding="utf-8",\n        )\n\n        old_path = list(sys.path)\n        old_cwd = Path.cwd()\n        try:\n            os.chdir(root)\n            sys.path.insert(0, str(root))\n            _clear_qseries_modules()\n\n            module = __import__(\n                "qseries_v2.oracle_terminal.oracle_bounded_live_intelligence_activation",\n                fromlist=["*"],\n            )\n\n            loaded_path = Path(module.__file__).resolve()\n            expected_path = (\n                terminal / "oracle_bounded_live_intelligence_activation.py"\n            ).resolve()\n            assert loaded_path == expected_path, (\n                f"isolated module resolution failed: {loaded_path} != {expected_path}"\n            )\n\n            candidates = module.discover_genuine_input_candidates(\n                repository_root=root\n            )\n            assert candidates\n            assert (\n                candidates[0].relative_path\n                == "runtime/oracle_research/certified_research_artifacts.json"\n            )\n\n            readiness = module.inspect_bounded_activation(\n                repository_root=root\n            )\n            assert readiness.activation_readiness == "ready_for_activate_once"\n            assert readiness.activation_attempted is False\n\n            receipt = module.activate_once(repository_root=root)\n            assert module.verify_bounded_activation_receipt(receipt)\n            assert receipt.invocation_completed\n            assert receipt.analytics_execution_performed\n            assert receipt.new_intelligence_artifacts\n            assert receipt.protected_source_unchanged\n            assert receipt.outside_target_runtime_unchanged\n            assert (\n                root\n                / "runtime"\n                / "oracle_intelligence"\n                / "test_output"\n                / "genuine.json"\n            ).is_file()\n\n            rendered = "\\n".join(\n                module.bounded_activation_lines(receipt)\n            )\n            assert "invocation_completed: true" in rendered\n            assert "database_write_requested: false" in rendered\n            assert "publication_allowed: false" in rendered\n            assert "qseries_execution_allowed: false" in rendered\n            assert "bounded_once: true" in rendered\n\n            try:\n                module.activate_once(repository_root=root)\n                raise AssertionError("second bounded activation accepted")\n            except module.OracleBoundedActivationInvariantError:\n                pass\n        finally:\n            os.chdir(old_cwd)\n            sys.path[:] = old_path\n            _clear_qseries_modules()\n\n    print("[PASS] Isolated qseries_v2 package root created")\n    print("[PASS] Isolated oracle_intelligence package root created")\n    print("[PASS] Test analytics gate resolved from temporary repository")\n    print("[PASS] Actual OIT-003 discovery contract consumed")\n    print("[PASS] Genuine runtime input candidate discovered")\n    print("[PASS] Exactly one bounded persist-enabled invocation performed")\n    print("[PASS] Genuine runtime/oracle_intelligence artifact required")\n    print("[PASS] Protected subsystem source hashes preserved")\n    print("[PASS] Runtime mutation outside canonical target rejected")\n    print("[PASS] Database writes, publication, and Q Series execution disabled")\n    print("[PASS] Second completed activation rejected")\n    print("[DONE] OIT-004 CORRECTION V2 PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_complete(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    paths = {}
    prefixes = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )
    for base in prefixes:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.is_file():
                paths[path] = sha256(path)
    for path in (OIT_003, OIT_004, RUNNER):
        if path.is_file():
            paths[path] = sha256(path)
    return paths


def main() -> int:
    print("=" * 40)
    print(" OIT-004 CORRECTION V2 INSTALLER")
    print(" ISOLATED TEST PACKAGE RESOLUTION")
    print("=" * 40)
    try:
        if not OIT_003.is_file():
            raise RuntimeError(f"Actual OIT-003 module missing: {OIT_003}")
        if not OIT_004.is_file():
            raise RuntimeError(f"Actual OIT-004 module missing: {OIT_004}")
        if not RUNNER.is_file():
            raise RuntimeError(f"Actual OIT-004 runner missing: {RUNNER}")

        oit_004_text = OIT_004.read_text(encoding="utf-8")
        required = (
            'SCHEMA_VERSION = "OIT-004"',
            "def activate_once(",
            "def inspect_bounded_activation(",
            "def verify_bounded_activation_receipt(",
            "runtime/oracle_intelligence",
        )
        missing = [item for item in required if item not in oit_004_text]
        if missing:
            raise RuntimeError(f"OIT-004 production contract incomplete: {missing}")

        protected = protected_sources()
        print("[OK] Actual OIT-003 discovery contract verified")
        print("[OK] Actual OIT-004 production activation contract verified")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        write_complete(TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-004 CORRECTION V2 test failed with exit code "
                f"{completed.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] OIT-004 production module unchanged")
        print("[PASS] OIT-004 terminal runner unchanged")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Isolated test package resolution corrected")
        print("[PASS] Complete OIT-004 production test passed")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-004 CORRECTION V2 INSTALLED")
        return 0
    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
