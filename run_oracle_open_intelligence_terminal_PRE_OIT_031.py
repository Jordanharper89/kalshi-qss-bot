from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Iterable, Sequence

from qseries_v2.oracle_terminal.oracle_terminal_activated_output_display_session_gate import (
    OracleTerminalDisplayFrame,
    OracleTerminalDisplaySessionGateReport,
    build_terminal_display_session_gate_report,
    verify_terminal_display_session_gate_report,
)

RUNNER_VERSION = "OIT-030"
PROMPT = "oracle> "
EXIT_COMMANDS = frozenset({"/quit", "/exit", "quit", "exit"})
HELP_COMMANDS = frozenset({"/help", "help", "?"})
STATUS_COMMANDS = frozenset({"/status", "status"})


class OracleTerminalRunnerError(RuntimeError):
    pass


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
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
    write: Callable[[str], None] = print,
) -> OracleTerminalDisplaySessionGateReport:
    report = execute_query(query, root=root, builder=builder)
    print_lines(flatten_display_session(report), write=write)
    return report


def help_lines() -> tuple[str, ...]:
    return (
        "Oracle Open Intelligence Terminal",
        f"Runner certification: {RUNNER_VERSION}",
        "",
        "Enter a natural-language intelligence question.",
        "",
        "Commands:",
        "  /help    Show this help",
        "  /status  Show terminal safety status",
        "  /quit    Close the terminal",
    )


def status_lines() -> tuple[str, ...]:
    return (
        "Oracle Terminal Status",
        f"  runner: {RUNNER_VERSION}",
        "  mode: interactive read-only",
        "  display boundary: OIT-027 certified session",
        "  publication: disabled",
        "  action authorization: disabled",
        "  Q Series execution: disabled",
    )


def run_interactive(
    *,
    root: Path | None = None,
    builder: Callable[..., OracleTerminalDisplaySessionGateReport] = (
        build_terminal_display_session_gate_report
    ),
    read: Callable[[str], str] = input,
    write: Callable[[str], None] = print,
) -> int:
    print_lines(help_lines(), write=write)
    while True:
        try:
            raw = read(PROMPT)
        except (EOFError, KeyboardInterrupt):
            write("")
            write("Oracle Terminal closed.")
            return 0

        command = raw.strip()
        lowered = command.lower()
        if not command:
            continue
        if lowered in EXIT_COMMANDS:
            write("Oracle Terminal closed.")
            return 0
        if lowered in HELP_COMMANDS:
            print_lines(help_lines(), write=write)
            continue
        if lowered in STATUS_COMMANDS:
            print_lines(status_lines(), write=write)
            continue

        try:
            display_query(
                command,
                root=root,
                builder=builder,
                write=write,
            )
        except Exception as exc:
            write(f"[ERROR] {type(exc).__name__}: {exc}")


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
