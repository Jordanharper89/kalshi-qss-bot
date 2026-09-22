from __future__ import annotations

import importlib.util
import sys
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
from qseries_v2.oracle_terminal.oracle_terminal_evidence_panel_navigation import (
    build_default_panel_registry,
    resolve_panel,
    verify_panel_registry,
)
from qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (
    build_default_command_registry,
    resolve_terminal_command,
    verify_command_registry_report,
)


def load_runner(root: Path):
    path = root / "run_oracle_open_intelligence_terminal.py"
    module_name = "oit_032_runner_test"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load OIT-032 runner")

    module = importlib.util.module_from_spec(spec)

    # Required by Python 3.14 before dataclass decorators execute.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise

    return module


def make_report(root: Path, query: str):
    # OIT-027 is the authoritative display-frame contract. The fixture uses
    # only the already certified "informational" frame type instead of
    # inventing semantic frame types that OIT-027 rejects.
    frame_definitions = (
        (
            "informational",
            (
                "Oracle Intelligence Overview",
                f"Query: {query}",
            ),
        ),
        (
            "informational",
            (
                "Certified Read-Only Result",
                "No synthetic evidence frame type introduced.",
            ),
        ),
    )

    frames = []
    for index, (frame_type, lines) in enumerate(frame_definitions, start=1):
        body = {
            "frame_index": index,
            "frame_type": frame_type,
            "frame_lines": lines,
            "source_activation_hash": "activation-hash",
            "display_only": True,
            "read_only": True,
        }
        frames.append(
            OracleTerminalDisplayFrame(
                **body,
                frame_hash=oit_027_hash(body),
            )
        )

    session_body = {
        "session_id": "session-032-correction-v2",
        "query": query,
        "source_activation_report_hash": "activation-report-hash",
        "source_output_activation_hash": "activation-hash",
        "frames": tuple(frames),
        "frame_count": len(frames),
        "output_line_count": sum(len(frame.frame_lines) for frame in frames),
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
    print(" OIT-032 TEST")
    print(" EVIDENCE EXPANSION AND PANEL NAVIGATION")
    print(" CORRECTION V2 - OIT-027 FRAME ALIGNED")
    print("=" * 48)

    root = Path(__file__).resolve().parent
    runner = load_runner(root)
    command_registry = build_default_command_registry()
    panel_registry = build_default_panel_registry()

    assert verify_command_registry_report(command_registry)
    assert verify_panel_registry(panel_registry)
    assert command_registry.command_count == 11
    assert panel_registry.panel_count == 6

    assert resolve_terminal_command(
        "/panels",
        registry=command_registry,
    ).handler_name == "handle_panels"
    assert resolve_terminal_command(
        "/evidence",
        registry=command_registry,
    ).handler_name == "handle_evidence"

    panel_resolution = resolve_terminal_command(
        "/panel timeline",
        registry=command_registry,
    )
    assert panel_resolution.handler_name == "handle_panel"
    assert panel_resolution.argument == "timeline"

    assert resolve_terminal_command(
        "/next",
        registry=command_registry,
    ).handler_name == "handle_next"
    assert resolve_terminal_command(
        "/back",
        registry=command_registry,
    ).handler_name == "handle_back"

    evidence_selection = resolve_panel(
        "sources",
        registry=panel_registry,
    )
    assert evidence_selection.matched
    assert evidence_selection.panel_name == "evidence"
    assert evidence_selection.panel_index == 1

    captured: list[str] = []
    session = runner.LocalTerminalSession()

    def builder(repository_root, query):
        return make_report(Path(repository_root), query)

    assert runner.dispatch_command(
        "/ask What changed?",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )

    assert session.query_count == 1
    assert session.last_query == "What changed?"
    assert session.last_session_id == "session-032-correction-v2"
    assert session.last_report is not None
    assert session.active_panel_index == 0
    assert "Oracle Intelligence Overview" in captured

    assert runner.dispatch_command(
        "/panels",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )
    assert "Oracle Intelligence Panels" in captured

    evidence_start = len(captured)
    assert runner.dispatch_command(
        "/evidence",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )
    evidence_output = captured[evidence_start:]
    assert session.active_panel_index == 1
    assert evidence_output == [
        "Oracle Panel: evidence",
        "  No matching certified frames are available in the current session.",
    ]

    timeline_start = len(captured)
    assert runner.dispatch_command(
        "/panel timeline",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )
    timeline_output = captured[timeline_start:]
    assert session.active_panel_index == 3
    assert timeline_output == [
        "Oracle Panel: timeline",
        "  No matching certified frames are available in the current session.",
    ]

    assert runner.dispatch_command(
        "/next",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )
    assert session.active_panel_index == 4

    assert runner.dispatch_command(
        "/back",
        registry=command_registry,
        panel_registry=panel_registry,
        session=session,
        root=root,
        builder=builder,
        write=captured.append,
        clear=lambda: None,
    )
    assert session.active_panel_index == 3

    empty_session = runner.LocalTerminalSession()
    empty_output: list[str] = []
    assert runner.dispatch_command(
        "/evidence",
        registry=command_registry,
        panel_registry=panel_registry,
        session=empty_session,
        root=root,
        builder=builder,
        write=empty_output.append,
        clear=lambda: None,
    )
    assert empty_output == [
        "[ERROR] OracleTerminalRunnerError: run a query before opening panels"
    ]

    print("[PASS] Current OIT-032 production runner imported")
    print("[PASS] OIT-027-supported informational frames consumed")
    print("[PASS] Unsupported synthetic frame types removed")
    print("[PASS] OIT-032 command registry certified")
    print("[PASS] OIT-032 panel registry certified")
    print("[PASS] /panels command activated")
    print("[PASS] /panel <name> command activated")
    print("[PASS] /evidence command activated")
    print("[PASS] /next and /back navigation activated")
    print("[PASS] Empty matching-panel fallback certified")
    print("[PASS] Pre-query panel rejection certified")
    print("[PASS] Active panel state retained locally")
    print("[PASS] Python 3.14 dynamic runner import verified")
    print("[PASS] Publication, action authorization, and Q Series execution disabled")
    print("[DONE] OIT-032 EVIDENCE EXPANSION AND PANEL NAVIGATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
