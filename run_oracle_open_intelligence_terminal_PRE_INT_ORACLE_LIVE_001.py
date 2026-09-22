from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    OracleTerminalDisplayFrame,
    OracleTerminalDisplaySessionGateReport,
    build_terminal_display_session_gate_report,
    verify_terminal_display_session_gate_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_interactive_command_registry import (
    OracleTerminalCommandRegistryReport,
    build_default_command_registry,
    resolve_terminal_command,
    verify_command_registry_report,
)
from qseries_v2.oracle_terminal.oracle_terminal_evidence_panel_navigation import (
    OracleTerminalPanelRegistry,
    build_default_panel_registry,
    resolve_panel,
    verify_panel_registry,
)

RUNNER_VERSION = "OIT-048"
PROMPT = "oracle> "


class OracleTerminalRunnerError(RuntimeError):
    pass


@dataclass
class LocalTerminalSession:
    query_count: int = 0
    last_query: str = ""
    last_session_id: str = ""
    active_panel_index: int = 0
    last_report: OracleTerminalDisplaySessionGateReport | None = field(default=None, repr=False)


def repository_root() -> Path:
    return Path(__file__).resolve().parent


def normalize_query(value: str) -> str:
    query = " ".join(str(value).strip().split())
    if not query:
        raise OracleTerminalRunnerError("query cannot be empty")
    return query


def render_frame_lines(frame: OracleTerminalDisplayFrame) -> tuple[str, ...]:
    if not frame.read_only or not frame.display_only:
        raise OracleTerminalRunnerError("refusing to render a non-read-only display frame")
    if not frame.frame_lines:
        raise OracleTerminalRunnerError("refusing to render an empty display frame")
    return tuple(frame.frame_lines)


def flatten_display_session(report: OracleTerminalDisplaySessionGateReport) -> tuple[str, ...]:
    verify_terminal_display_session_gate_report(report)
    if not report.display_session_ready or not report.read_only:
        raise OracleTerminalRunnerError(report.failure_reason or "display session is not ready")
    if report.publication_allowed or report.action_authorization_allowed or report.qseries_execution_allowed:
        raise OracleTerminalRunnerError("forbidden capability exposed by display session")
    lines = []
    for index, frame in enumerate(report.display_session.frames):
        if index:
            lines.append("")
        lines.extend(render_frame_lines(frame))
    return tuple(lines)


def print_lines(lines: Iterable[str], *, write: Callable[[str], None] = print) -> None:
    for line in lines:
        write(str(line))


def execute_query(query, *, root=None, builder=build_terminal_display_session_gate_report):
    canonical_query = normalize_query(query)
    active_root = (root or repository_root()).resolve()
    report = builder(active_root, canonical_query)
    verify_terminal_display_session_gate_report(report)
    if report.query != canonical_query:
        raise OracleTerminalRunnerError("display-session query lineage mismatch")
    return report


def display_query(query, *, session=None, root=None, builder=build_terminal_display_session_gate_report, write=print):
    report = execute_query(query, root=root, builder=builder)
    print_lines(flatten_display_session(report), write=write)
    if session is not None:
        session.query_count += 1
        session.last_query = report.query
        session.last_session_id = report.display_session.session_id
        session.last_report = report
        session.active_panel_index = 0
    return report


def panel_lines(registry: OracleTerminalPanelRegistry, active_index: int) -> tuple[str, ...]:
    verify_panel_registry(registry)
    lines = ["Oracle Intelligence Panels"]
    for panel in registry.panels:
        marker = "*" if panel.panel_index == active_index else " "
        lines.append(f" {marker} {panel.panel_name:<14} {panel.summary}")
    return tuple(lines)


def filtered_panel_lines(report, panel_name, source_frame_types):
    verify_terminal_display_session_gate_report(report)
    selected = []
    allowed = {item.lower() for item in source_frame_types}
    for frame in report.display_session.frames:
        frame_type = str(frame.frame_type).lower()
        if frame_type in allowed or any(token in frame_type for token in allowed):
            if selected:
                selected.append("")
            selected.extend(render_frame_lines(frame))
    if not selected:
        return (
            f"Oracle Panel: {panel_name}",
            "  No matching certified frames are available in the current session.",
        )
    return tuple(selected)


def open_panel(session, panel_registry, panel_name, *, write=print):
    if session.last_report is None:
        write("[ERROR] OracleTerminalRunnerError: run a query before opening panels")
        return
    selection = resolve_panel(panel_name, registry=panel_registry)
    if not selection.matched:
        write(f"[ERROR] OracleTerminalRunnerError: unknown panel '{panel_name}'")
        return
    session.active_panel_index = int(selection.panel_index)
    print_lines(
        filtered_panel_lines(
            session.last_report,
            selection.panel_name,
            selection.source_frame_types,
        ),
        write=write,
    )


def help_lines(registry):
    verify_command_registry_report(registry)
    lines = ["Oracle Open Intelligence Terminal", f"Runner certification: {RUNNER_VERSION}", "", "Enter a natural-language intelligence question.", "", "Commands:"]
    for definition in registry.commands:
        suffix = " <value>" if definition.accepts_argument else ""
        lines.append(f"  {definition.command}{suffix:<12} {definition.summary}")
    return tuple(lines)


def status_lines():
    return (
        "Oracle Terminal Status",
        f"  runner: {RUNNER_VERSION}",
        "  mode: interactive read-only",
        "  command registry: OIT-032 certified",
        "  panel navigation: OIT-032 certified",
        "  display boundary: OIT-027 certified session",
        "  publication: disabled",
        "  action authorization: disabled",
        "  Q Series execution: disabled",
    )


def session_lines(session):
    return (
        "Oracle Terminal Session",
        f"  queries: {session.query_count}",
        f"  last query: {session.last_query or '(none)'}",
        f"  last display session: {session.last_session_id or '(none)'}",
        f"  active panel index: {session.active_panel_index}",
        "  persistence: local process only",
        "  mode: read-only",
    )


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def dispatch_command(raw_input, *, registry, panel_registry, session, root=None, builder=build_terminal_display_session_gate_report, write=print, clear=clear_terminal):
    resolution = resolve_terminal_command(raw_input, registry=registry)
    if not resolution.matched:
        display_query(resolution.argument, session=session, root=root, builder=builder, write=write)
        return True

    handler = resolution.handler_name
    if handler == "handle_help":
        print_lines(help_lines(registry), write=write)
    elif handler == "handle_status":
        print_lines(status_lines(), write=write)
    elif handler == "handle_session":
        print_lines(session_lines(session), write=write)
    elif handler == "handle_panels":
        print_lines(panel_lines(panel_registry, session.active_panel_index), write=write)
    elif handler == "handle_panel":
        if not resolution.argument:
            write("[ERROR] OracleTerminalRunnerError: /panel requires a panel name")
        else:
            open_panel(session, panel_registry, resolution.argument, write=write)
    elif handler == "handle_evidence":
        open_panel(session, panel_registry, "evidence", write=write)
    elif handler in ("handle_next", "handle_back"):
        delta = 1 if handler == "handle_next" else -1
        count = panel_registry.panel_count
        session.active_panel_index = (session.active_panel_index + delta) % count
        panel = panel_registry.panels[session.active_panel_index]
        open_panel(session, panel_registry, panel.panel_name, write=write)
    elif handler == "handle_clear":
        clear()
    elif handler == "handle_quit":
        write("Oracle Terminal closed.")
        return False
    elif handler == "handle_ask":
        if not resolution.argument:
            write("[ERROR] OracleTerminalRunnerError: /ask requires a question")
        else:
            display_query(resolution.argument, session=session, root=root, builder=builder, write=write)
    else:
        raise OracleTerminalRunnerError(f"unsupported command handler: {handler}")
    return True


def run_interactive(*, root=None, builder=build_terminal_display_session_gate_report, read=input, write=print, clear=clear_terminal):
    registry = build_default_command_registry()
    panel_registry = build_default_panel_registry()
    verify_command_registry_report(registry)
    verify_panel_registry(panel_registry)
    session = LocalTerminalSession()
    print_lines(help_lines(registry), write=write)
    while True:
        try:
            raw = read(PROMPT)
        except (EOFError, KeyboardInterrupt):
            write("")
            write("Oracle Terminal closed.")
            return 0
        if not raw.strip():
            continue
        try:
            keep_running = dispatch_command(
                raw,
                registry=registry,
                panel_registry=panel_registry,
                session=session,
                root=root,
                builder=builder,
                write=write,
                clear=clear,
            )
        except Exception as exc:
            write(f"[ERROR] {type(exc).__name__}: {exc}")
            continue
        if not keep_running:
            return 0


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Oracle Open Intelligence Terminal")
    parser.add_argument("query", nargs="*", help="optional one-shot natural-language query")
    parser.add_argument("--status", action="store_true", help="show read-only terminal status and exit")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    if arguments.status:
        print_lines(status_lines())
        return 0
    if arguments.query:
        try:
            display_query(" ".join(arguments.query))
            return 0
        except Exception as exc:
            print(f"[ERROR] {type(exc).__name__}: {exc}")
            return 1
    return run_interactive()


if __name__ == "__main__":
    raise SystemExit(main())

# BEGIN OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE
from qseries_v2.oracle_terminal.oracle_end_to_end_interactive_intelligence_pipeline import (
    execute_end_to_end_interactive_intelligence_pipeline as _oit_048_execute_pipeline,
    verify_interactive_intelligence_pipeline_report as _oit_048_verify_pipeline,
)

OIT_048_PIPELINE_BOUND = True
OIT_048_PIPELINE_VERSION = "OIT-048"


def execute_oit_048_interactive_pipeline(
    *,
    repository_root,
    context_assembly_report,
    prior_session_context,
    query,
):
    report = _oit_048_execute_pipeline(
        repository_root,
        context_assembly_report=context_assembly_report,
        prior_session_context=prior_session_context,
        query=query,
    )
    _oit_048_verify_pipeline(report)
    return report


def render_oit_048_interactive_pipeline(
    report,
    *,
    write=print,
):
    _oit_048_verify_pipeline(report)
    for line in report.pipeline_result.rendered_lines:
        write(line)
    return report.pipeline_result.session_update_report.updated_session_context
# END OIT-048 END-TO-END INTERACTIVE INTELLIGENCE PIPELINE
