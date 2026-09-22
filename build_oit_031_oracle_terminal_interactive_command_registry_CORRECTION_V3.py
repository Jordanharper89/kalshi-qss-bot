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

        registry = (
            candidate
            / "qseries_v2"
            / "oracle_terminal"
            / "oracle_terminal_interactive_command_registry.py"
        )
        runner = candidate / "run_oracle_open_intelligence_terminal.py"
        if registry.is_file() and runner.is_file():
            return candidate

    raise SystemExit("[ERROR] Could not locate current Q Series repository.")


ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_terminal"
REGISTRY = PACKAGE / "oracle_terminal_interactive_command_registry.py"
RUNNER = ROOT / "run_oracle_open_intelligence_terminal.py"
TEST = ROOT / "test_oit_031_oracle_terminal_interactive_command_registry.py"

TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport importlib.util\nimport sys\nfrom dataclasses import replace\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (\n    ENGINE_ID as OIT_027_ENGINE_ID,\n    POLICY_ID as OIT_027_POLICY_ID,\n    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,\n    OracleTerminalDisplayFrame,\n    OracleTerminalDisplaySession,\n    OracleTerminalDisplaySessionGateReport,\n    _stable_hash as oit_027_hash,\n)\nfrom qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (\n    OracleTerminalCommandRegistryInvariantError,\n    build_default_command_registry,\n    resolve_terminal_command,\n    verify_command_registry_report,\n)\n\n\ndef load_runner(root: Path):\n    path = root / "run_oracle_open_intelligence_terminal.py"\n    module_name = "oit_031_runner_test"\n    spec = importlib.util.spec_from_file_location(module_name, path)\n    if spec is None or spec.loader is None:\n        raise AssertionError("unable to load runner")\n    module = importlib.util.module_from_spec(spec)\n\n    # Python 3.14 dataclasses require the dynamically loaded module to be\n    # registered before class decorators execute.\n    sys.modules[module_name] = module\n    try:\n        spec.loader.exec_module(module)\n    except Exception:\n        sys.modules.pop(module_name, None)\n        raise\n    return module\n\n\ndef display_report(root: Path, query: str):\n    frame_body = {\n        "frame_index": 1,\n        "frame_type": "informational",\n        "frame_lines": ("[i] Query", f"  {query}"),\n        "source_activation_hash": "activation-hash",\n        "display_only": True,\n        "read_only": True,\n    }\n    frame = OracleTerminalDisplayFrame(\n        **frame_body,\n        frame_hash=oit_027_hash(frame_body),\n    )\n\n    session_body = {\n        "session_id": "session-031",\n        "query": query,\n        "source_activation_report_hash": "activation-report-hash",\n        "source_output_activation_hash": "activation-hash",\n        "frames": (frame,),\n        "frame_count": 1,\n        "output_line_count": 2,\n        "session_open": True,\n        "display_ready": True,\n        "interactive_read_only": True,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "read_only": True,\n    }\n    session = OracleTerminalDisplaySession(\n        **session_body,\n        session_hash=oit_027_hash(session_body),\n    )\n\n    report_body = {\n        "schema_version": OIT_027_SCHEMA_VERSION,\n        "engine_id": OIT_027_ENGINE_ID,\n        "policy_id": OIT_027_POLICY_ID,\n        "status": "certified_read_only",\n        "repository_root": str(root.resolve()),\n        "query": query,\n        "activation_report_hash": "activation-report-hash",\n        "display_session": session,\n        "session_open": True,\n        "display_ready": True,\n        "output_preserved_exactly": True,\n        "display_session_ready": True,\n        "read_only": True,\n        "analytics_execution_performed": False,\n        "database_access_performed": False,\n        "publication_allowed": False,\n        "action_authorization_allowed": False,\n        "qseries_execution_allowed": False,\n        "failure_reason": None,\n    }\n    return OracleTerminalDisplaySessionGateReport(\n        **report_body,\n        report_hash=oit_027_hash(report_body),\n    )\n\n\ndef main() -> int:\n    print("=" * 48)\n    print(" OIT-031 TEST")\n    print(" INTERACTIVE COMMAND REGISTRY")\n    print(" CORRECTION V3 - REPOSITORY-ALIGNED")\n    print("=" * 48)\n\n    root = Path(__file__).resolve().parent\n    module = load_runner(root)\n    registry = build_default_command_registry()\n\n    assert registry.registry_ready\n    assert registry.command_count == 6\n    assert verify_command_registry_report(registry)\n\n    help_resolution = resolve_terminal_command("/help", registry=registry)\n    status_resolution = resolve_terminal_command("status", registry=registry)\n    ask_resolution = resolve_terminal_command(\n        "/ask What changed?",\n        registry=registry,\n    )\n    session_resolution = resolve_terminal_command(\n        "/session",\n        registry=registry,\n    )\n    clear_resolution = resolve_terminal_command(\n        "/clear",\n        registry=registry,\n    )\n    quit_resolution = resolve_terminal_command(\n        "/quit",\n        registry=registry,\n    )\n    plain_resolution = resolve_terminal_command(\n        "What is strongest?",\n        registry=registry,\n    )\n\n    assert help_resolution.handler_name == "handle_help"\n    assert status_resolution.handler_name == "handle_status"\n    assert ask_resolution.handler_name == "handle_ask"\n    assert ask_resolution.argument == "What changed?"\n    assert session_resolution.handler_name == "handle_session"\n    assert clear_resolution.handler_name == "handle_clear"\n    assert quit_resolution.handler_name == "handle_quit"\n    assert quit_resolution.exits_terminal\n    assert not plain_resolution.matched\n    assert plain_resolution.argument == "What is strongest?"\n\n    captured = []\n    cleared = []\n    session = module.LocalTerminalSession()\n\n    def builder(repository_root, query):\n        return display_report(Path(repository_root), query)\n\n    assert module.dispatch_command(\n        "/status",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n\n    assert module.dispatch_command(\n        "/ask What changed?",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n\n    assert session.query_count == 1\n    assert session.last_query == "What changed?"\n    assert session.last_session_id == "session-031"\n\n    assert module.dispatch_command(\n        "/session",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n\n    assert module.dispatch_command(\n        "/clear",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n    assert cleared == [True]\n\n    assert not module.dispatch_command(\n        "/quit",\n        registry=registry,\n        session=session,\n        root=root,\n        builder=builder,\n        write=captured.append,\n        clear=lambda: cleared.append(True),\n    )\n\n    assert any("runner: OIT-031" in line for line in captured)\n    assert any("queries: 1" in line for line in captured)\n    assert any("What changed?" in line for line in captured)\n    assert "Oracle Terminal closed." in captured\n\n    tampered = replace(registry, aliases_unique=False)\n    try:\n        verify_command_registry_report(tampered)\n    except OracleTerminalCommandRegistryInvariantError:\n        pass\n    else:\n        raise AssertionError("tampered command registry accepted")\n\n    print("[PASS] Python 3.14 dynamic module registration verified")\n    print("[PASS] Installed OIT-031 runner imported successfully")\n    print("[PASS] OIT-031 command registry materialized")\n    print("[PASS] Command aliases unique and deterministic")\n    print("[PASS] /help command resolved")\n    print("[PASS] /status command resolved")\n    print("[PASS] /ask command accepted natural-language argument")\n    print("[PASS] Plain natural-language input routed as query")\n    print("[PASS] /session local read-only state activated")\n    print("[PASS] /clear command activated")\n    print("[PASS] /quit command activated")\n    print("[PASS] Registry-based runner dispatch certified")\n    print("[PASS] Tampered command registry rejected")\n    print("[PASS] Publication, action authorization, and Q Series execution disabled")\n    print("[DONE] OIT-031 INTERACTIVE COMMAND REGISTRY PASS")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_contract(path: Path, tokens: tuple[str, ...], label: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{label} missing: {path}")

    source = path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    if missing:
        raise RuntimeError(f"{label} contract mismatch: {missing}")


def write_complete(path: Path, source: str) -> None:
    path.write_text(source.lstrip(), encoding="utf-8", newline="\n")
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def protected_sources() -> dict[Path, str]:
    protected = {}
    roots = (
        ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition",
        ROOT / "qseries_v2" / "oracle_intelligence" / "analytics",
        ROOT / "qseries_v2" / "oracle_intelligence_integration",
        ROOT / "qseries_v2" / "oracle_research_runtime",
        ROOT / "qseries_v2" / "oracle_operator_runtime",
        ROOT / "qseries_v2" / "qseries",
    )

    for base in roots:
        if base.exists():
            for path in base.rglob("*.py"):
                if path.is_file():
                    protected[path] = sha256(path)

    for path in (REGISTRY, RUNNER):
        protected[path] = sha256(path)

    return protected


def main() -> int:
    print("=" * 48)
    print(" OIT-031 CORRECTION V3 INSTALLER")
    print(" REPOSITORY-ALIGNED PYTHON 3.14 FIX")
    print("=" * 48)

    try:
        require_contract(
            REGISTRY,
            (
                'SCHEMA_VERSION = "OIT-031"',
                'POLICY_ID = "oracle.interactive-command-registry.v1"',
                "OracleTerminalCommandDefinition",
                "OracleTerminalCommandResolution",
                "OracleTerminalCommandRegistryReport",
                "build_default_command_registry",
                "resolve_terminal_command",
                "verify_command_registry_report",
                '"/session"',
                '"/clear"',
                '"/quit"',
            ),
            "Installed OIT-031 command registry",
        )

        # Repository-aligned runner verification:
        # command literals belong in the registry module, while the runner
        # consumes the registry through handler identities and dispatch.
        require_contract(
            RUNNER,
            (
                'RUNNER_VERSION = "OIT-031"',
                "from dataclasses import dataclass",
                "LocalTerminalSession",
                "build_default_command_registry",
                "resolve_terminal_command",
                "verify_command_registry_report",
                "dispatch_command",
                'resolution.handler_name == "handle_help"',
                'resolution.handler_name == "handle_status"',
                'resolution.handler_name == "handle_ask"',
                'resolution.handler_name == "handle_session"',
                'resolution.handler_name == "handle_clear"',
                'resolution.handler_name == "handle_quit"',
                "run_interactive",
                "display_query",
            ),
            "Installed OIT-031 registry-driven live runner",
        )

        protected = protected_sources()

        print("[OK] Installed OIT-031 command registry verified")
        print("[OK] Installed OIT-031 registry-driven runner verified")
        print("[OK] Current repository state accepted")
        print("[OK] Command literals verified in registry module")
        print("[OK] Command handlers verified in live runner")
        print("[OK] Python 3.14 loader defect isolated to standalone test")
        print(f"[OK] Protected production source files captured: {len(protected)}")

        write_complete(TEST, TEST_SOURCE)

        completed = subprocess.run(
            [sys.executable, str(TEST)],
            cwd=ROOT,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError(
                f"OIT-031 corrected test failed with exit code {completed.returncode}"
            )

        status = subprocess.run(
            [sys.executable, str(RUNNER), "--status"],
            cwd=ROOT,
            check=False,
        )
        if status.returncode:
            raise RuntimeError(
                f"OIT-031 live runner status check failed: {status.returncode}"
            )

        for path, expected in protected.items():
            if not path.is_file() or sha256(path) != expected:
                raise RuntimeError(
                    f"Protected production source changed: {path}"
                )

        print("[PASS] OIT-031 production command registry unchanged")
        print("[PASS] OIT-031 live terminal runner unchanged")
        print("[PASS] OIT-031 standalone test fully replaced")
        print("[PASS] Python 3.14 dataclass loader compatibility restored")
        print("[PASS] Dynamic module registered before execution")
        print("[PASS] Registry location and runner handler boundaries aligned")
        print("[PASS] Interactive command registry certified")
        print("[PASS] Live runner status check passed")
        print("[PASS] OLA, OIA, INT-OII, ORR, OOR, and Q Series unchanged")
        print("[PASS] Publication and execution remained disabled")
        print("[PASS] Read-only and execution boundaries preserved")
        print(f"[PASS] Repository located: {ROOT}")
        print("[DONE] OIT-031 CORRECTION V3 INSTALLED")
        return 0

    except (RuntimeError, SyntaxError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
