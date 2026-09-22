from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
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

RUNNER_VERSION = "OIT-031"
PROMPT = "oracle> "


class OracleTerminalRunnerError(RuntimeError):
    pass


@dataclass
class LocalTerminalSession:
    query_count: int = 0
    last_query: str = ""
    last_session_id: str = ""


def repository_root() -> Path:
    return Path(__file__).resolve().parent


def normalize_query(value: str) -> str:
    query = " ".join(str(value).strip().split())
    if not query:
        raise OracleTerminalRunnerError("query cannot be empty")
    return query


def render_frame_lines(frame: OracleTerminalDisplayFrame) -> tuple[str, ...]:
    if not frame.read_only or not frame.display_only:
        raise OracleTerminalRunnerError(
            "refusing to render a non-read-only display frame"
        )
    if not frame.frame_lines:
        raise OracleTerminalRunnerError(
            "refusing to render an empty display frame"
        )
    return tuple(frame.frame_lines)


def flatten_display_session(
    report: OracleTerminalDisplaySessionGateReport,
) -> tuple[str, ...]:
    verify_terminal_display_session_gate_report(report)
    if not report.display_session_ready:
        raise OracleTerminalRunnerError(
            report.failure_reason or "display session is not ready"
        )
    if not report.read_only:
        raise OracleTerminalRunnerError(
            "display-session report is not read-only"
        )
    if (
        report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalRunnerError(
            "forbidden capability exposed by display session"
        )

    lines: list[str] = []
    for index, frame in enumerate(report.display_session.frames):
        if index:
            lines.append("")
        lines.extend(render_frame_lines(frame))
    return tuple(lines)


def print_lines(
    lines: Iterable[str],
    *,
    write: Callable[[str], None] = print,
) -> None:
    for line in lines:
        write(str(line))


def execute_query(
    query: str,
    *,
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
) -> OracleTerminalDisplaySessionGateReport:
    canonical_query = normalize_query(query)
    active_root = (root or repository_root()).resolve()
    report = builder(active_root, canonical_query)
    verify_terminal_display_session_gate_report(report)
    if report.query != canonical_query:
        raise OracleTerminalRunnerError(
            "display-session query lineage mismatch"
        )
    return report


def display_query(
    query: str,
    *,
    session: LocalTerminalSession | None = None,
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
    write: Callable[[str], None] = print,
) -> OracleTerminalDisplaySessionGateReport:
    report = execute_query(query, root=root, builder=builder)
    print_lines(flatten_display_session(report), write=write)
    if session is not None:
        session.query_count += 1
        session.last_query = report.query
        session.last_session_id = report.display_session.session_id
    return report


def help_lines(
    registry: OracleTerminalCommandRegistryReport,
) -> tuple[str, ...]:
    verify_command_registry_report(registry)
    lines = [
        "Oracle Open Intelligence Terminal",
        f"Runner certification: {RUNNER_VERSION}",
        "",
        "Enter a natural-language intelligence question.",
        "",
        "Commands:",
    ]
    for definition in registry.commands:
        suffix = " <question>" if definition.accepts_argument else ""
        lines.append(
            f"  {definition.command}{suffix:<12} {definition.summary}"
        )
    return tuple(lines)


def status_lines() -> tuple[str, ...]:
    return (
        "Oracle Terminal Status",
        f"  runner: {RUNNER_VERSION}",
        "  mode: interactive read-only",
        "  command registry: OIT-031 certified",
        "  display boundary: OIT-027 certified session",
        "  publication: disabled",
        "  action authorization: disabled",
        "  Q Series execution: disabled",
    )


def session_lines(session: LocalTerminalSession) -> tuple[str, ...]:
    return (
        "Oracle Terminal Session",
        f"  queries: {session.query_count}",
        f"  last query: {session.last_query or '(none)'}",
        f"  last display session: {session.last_session_id or '(none)'}",
        "  persistence: local process only",
        "  mode: read-only",
    )


def clear_terminal() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def dispatch_command(
    raw_input: str,
    *,
    registry: OracleTerminalCommandRegistryReport,
    session: LocalTerminalSession,
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
    write: Callable[[str], None] = print,
    clear: Callable[[], None] = clear_terminal,
) -> bool:
    resolution = resolve_terminal_command(raw_input, registry=registry)

    if not resolution.matched:
        display_query(
            resolution.argument,
            session=session,
            root=root,
            builder=builder,
            write=write,
        )
        return True

    if resolution.handler_name == "handle_help":
        print_lines(help_lines(registry), write=write)
        return True
    if resolution.handler_name == "handle_status":
        print_lines(status_lines(), write=write)
        return True
    if resolution.handler_name == "handle_session":
        print_lines(session_lines(session), write=write)
        return True
    if resolution.handler_name == "handle_clear":
        clear()
        return True
    if resolution.handler_name == "handle_quit":
        write("Oracle Terminal closed.")
        return False
    if resolution.handler_name == "handle_ask":
        if not resolution.argument:
            write("[ERROR] OracleTerminalRunnerError: /ask requires a question")
            return True
        display_query(
            resolution.argument,
            session=session,
            root=root,
            builder=builder,
            write=write,
        )
        return True

    raise OracleTerminalRunnerError(
        f"unsupported command handler: {resolution.handler_name}"
    )


def run_interactive(
    *,
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
    clear: Callable[[], None] = clear_terminal,
) -> int:
    registry = build_default_command_registry()
    verify_command_registry_report(registry)
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


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Oracle Open Intelligence Terminal",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="optional one-shot natural-language query",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="show read-only terminal status and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

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
