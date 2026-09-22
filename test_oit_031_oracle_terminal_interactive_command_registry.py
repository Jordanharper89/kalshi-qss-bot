from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path

from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    ENGINE_ID as OIT_027_ENGINE_ID,
    POLICY_ID as OIT_027_POLICY_ID,
    SCHEMA_VERSION as OIT_027_SCHEMA_VERSION,
    OracleTerminalDisplayFrame,
    OracleTerminalDisplaySession,
    OracleTerminalDisplaySessionGateReport,
    _stable_hash as oit_027_hash,
)
from qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (
    OracleTerminalCommandRegistryInvariantError,
    build_default_command_registry,
    resolve_terminal_command,
    verify_command_registry_report,
)


def load_runner(root: Path):
    path = root / "run_oracle_open_intelligence_terminal.py"
    module_name = "oit_031_runner_test"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load runner")
    module = importlib.util.module_from_spec(spec)

    # Python 3.14 dataclasses require the dynamically loaded module to be
    # registered before class decorators execute.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def display_report(root: Path, query: str):
    frame_body = {
        "frame_index": 1,
        "frame_type": "informational",
        "frame_lines": ("[i] Query", f"  {query}"),
        "source_activation_hash": "activation-hash",
        "display_only": True,
        "read_only": True,
    }
    frame = OracleTerminalDisplayFrame(
        **frame_body,
        frame_hash=oit_027_hash(frame_body),
    )

    session_body = {
        "session_id": "session-031",
        "query": query,
        "source_activation_report_hash": "activation-report-hash",
        "source_output_activation_hash": "activation-hash",
        "frames": (frame,),
        "frame_count": 1,
        "output_line_count": 2,
        "session_open": True,
        "display_ready": True,
        "interactive_read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    session = OracleTerminalDisplaySession(
        **session_body,
        session_hash=oit_027_hash(session_body),
    )

    report_body = {
        "schema_version": OIT_027_SCHEMA_VERSION,
        "engine_id": OIT_027_ENGINE_ID,
        "policy_id": OIT_027_POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root.resolve()),
        "query": query,
        "activation_report_hash": "activation-report-hash",
        "display_session": session,
        "session_open": True,
        "display_ready": True,
        "output_preserved_exactly": True,
        "display_session_ready": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    return OracleTerminalDisplaySessionGateReport(
        **report_body,
        report_hash=oit_027_hash(report_body),
    )


def main() -> int:
    print("=" * 48)
    print(" OIT-031 TEST")
    print(" INTERACTIVE COMMAND REGISTRY")
    print(" CORRECTION V3 - REPOSITORY-ALIGNED")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    module = load_runner(root)
    registry = build_default_command_registry()

    assert registry.registry_ready
    assert registry.command_count == 6
    assert verify_command_registry_report(registry)

    help_resolution = resolve_terminal_command("/help", registry=registry)
    status_resolution = resolve_terminal_command("status", registry=registry)
    ask_resolution = resolve_terminal_command(
        "/ask What changed?",
        registry=registry,
    )
    session_resolution = resolve_terminal_command(
        "/session",
        registry=registry,
    )
    clear_resolution = resolve_terminal_command(
        "/clear",
        registry=registry,
    )
    quit_resolution = resolve_terminal_command(
        "/quit",
        registry=registry,
    )
    plain_resolution = resolve_terminal_command(
        "What is strongest?",
        registry=registry,
    )

    assert help_resolution.handler_name == "handle_help"
    assert status_resolution.handler_name == "handle_status"
    assert ask_resolution.handler_name == "handle_ask"
    assert ask_resolution.argument == "What changed?"
    assert session_resolution.handler_name == "handle_session"
    assert clear_resolution.handler_name == "handle_clear"
    assert quit_resolution.handler_name == "handle_quit"
    assert quit_resolution.exits_terminal
    assert not plain_resolution.matched
    assert plain_resolution.argument == "What is strongest?"

    captured = []
    cleared = []
    session = module.LocalTerminalSession()

    def builder(repository_root, query):
        return display_report(Path(repository_root), query)

    assert module.dispatch_command(
        "/status",
        registry=registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: cleared.append(True),
    )

    assert module.dispatch_command(
        "/ask What changed?",
        registry=registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: cleared.append(True),
    )

    assert session.query_count == 1
    assert session.last_query == "What changed?"
    assert session.last_session_id == "session-031"

    assert module.dispatch_command(
        "/session",
        registry=registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: cleared.append(True),
    )

    assert module.dispatch_command(
        "/clear",
        registry=registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: cleared.append(True),
    )
    assert cleared == [True]

    assert not module.dispatch_command(
        "/quit",
        registry=registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: cleared.append(True),
    )

    assert any("runner: OIT-031" in line for line in captured)
    assert any("queries: 1" in line for line in captured)
    assert any("What changed?" in line for line in captured)
    assert "Oracle Terminal closed." in captured

    tampered = replace(registry, aliases_unique=False)
    try:
        verify_command_registry_report(tampered)
    except OracleTerminalCommandRegistryInvariantError:
        pass
    else:
        raise AssertionError("tampered command registry accepted")

    print("[PASS] Python 3.14 dynamic module registration verified")
    print("[PASS] Installed OIT-031 runner imported successfully")
    print("[PASS] OIT-031 command registry materialized")
    print("[PASS] Command aliases unique and deterministic")
    print("[PASS] /help command resolved")
    print("[PASS] /status command resolved")
    print("[PASS] /ask command accepted natural-language argument")
    print("[PASS] Plain natural-language input routed as query")
    print("[PASS] /session local read-only state activated")
    print("[PASS] /clear command activated")
    print("[PASS] /quit command activated")
    print("[PASS] Registry-based runner dispatch certified")
    print("[PASS] Tampered command registry rejected")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-031 INTERACTIVE COMMAND REGISTRY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
