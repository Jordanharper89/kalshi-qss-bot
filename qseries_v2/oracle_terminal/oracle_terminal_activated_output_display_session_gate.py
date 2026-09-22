from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_renderer_invocation_output_activation_gate import (
    OracleTerminalRendererActivationGateReport,
    OracleTerminalRendererActivationInvariantError,
    build_terminal_renderer_activation_gate_report,
    verify_terminal_renderer_activation_gate_report,
)

SCHEMA_VERSION = "OIT-027"
ENGINE_ID = "OIT-027"
POLICY_ID = "oracle.terminal-activated-output-display-session-gate.v1"


class OracleTerminalDisplaySessionInvariantError(
    OracleTerminalRendererActivationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalDisplayFrame:
    frame_index: int
    frame_type: str
    frame_lines: tuple[str, ...]
    source_activation_hash: str
    display_only: bool
    read_only: bool
    frame_hash: str


@dataclass(frozen=True)
class OracleTerminalDisplaySession:
    session_id: str
    query: str
    source_activation_report_hash: str
    source_output_activation_hash: str
    frames: tuple[OracleTerminalDisplayFrame, ...]
    frame_count: int
    output_line_count: int
    session_open: bool
    display_ready: bool
    interactive_read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
    session_hash: str


@dataclass(frozen=True)
class OracleTerminalDisplaySessionGateReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    activation_report_hash: str
    display_session: OracleTerminalDisplaySession
    session_open: bool
    display_ready: bool
    output_preserved_exactly: bool
    display_session_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _frame_type(lines: tuple[str, ...]) -> str:
    if not lines:
        return "empty"
    first = lines[0]
    if first.startswith("="):
        return "banner"
    if first.startswith("[!]"):
        return "critical"
    if first.startswith("[~]"):
        return "warning"
    if first.startswith("[i]"):
        return "informational"
    return "content"


def _split_frames(
    output_lines: tuple[str, ...],
    activation_hash: str,
) -> tuple[OracleTerminalDisplayFrame, ...]:
    groups: list[tuple[str, ...]] = []
    current: list[str] = []
    for line in output_lines:
        if line == "":
            if current:
                groups.append(tuple(current))
                current = []
            continue
        current.append(line)
    if current:
        groups.append(tuple(current))

    frames = []
    for index, lines in enumerate(groups, start=1):
        body = {
            "frame_index": index,
            "frame_type": _frame_type(lines),
            "frame_lines": lines,
            "source_activation_hash": activation_hash,
            "display_only": True,
            "read_only": True,
        }
        frames.append(
            OracleTerminalDisplayFrame(
                **body,
                frame_hash=_stable_hash(body),
            )
        )
    return tuple(frames)


def verify_terminal_display_frame(
    frame: OracleTerminalDisplayFrame,
) -> bool:
    body = asdict(frame)
    supplied = body.pop("frame_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display frame hash mismatch"
        )
    if frame.frame_type not in {
        "banner",
        "critical",
        "warning",
        "informational",
        "content",
    }:
        raise OracleTerminalDisplaySessionInvariantError(
            "unsupported terminal display frame type"
        )
    if not frame.frame_lines:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display frame is empty"
        )
    if not frame.source_activation_hash:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display frame activation lineage missing"
        )
    if not frame.display_only or not frame.read_only:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display frame is not read-only display-only"
        )
    return True


def _flatten_frames(
    frames: tuple[OracleTerminalDisplayFrame, ...],
) -> tuple[str, ...]:
    lines: list[str] = []
    for index, frame in enumerate(frames):
        if index:
            lines.append("")
        lines.extend(frame.frame_lines)
    return tuple(lines)


def _build_display_session(
    query: str,
    activation_report: OracleTerminalRendererActivationGateReport,
) -> OracleTerminalDisplaySession:
    activation = activation_report.activation
    frames = _split_frames(
        tuple(activation.terminal_output_lines),
        activation.activation_hash,
    )
    for frame in frames:
        verify_terminal_display_frame(frame)

    session_id = _stable_hash(
        {
            "query": query,
            "activation_report_hash": activation_report.report_hash,
            "activation_hash": activation.activation_hash,
            "frames": frames,
        }
    )[:24]

    body = {
        "session_id": session_id,
        "query": str(query),
        "source_activation_report_hash": activation_report.report_hash,
        "source_output_activation_hash": activation.activation_hash,
        "frames": frames,
        "frame_count": len(frames),
        "output_line_count": len(activation.terminal_output_lines),
        "session_open": bool(
            activation_report.renderer_activation_ready and frames
        ),
        "display_ready": bool(
            activation.display_ready and activation.output_activated
        ),
        "interactive_read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    session = OracleTerminalDisplaySession(
        **body,
        session_hash=_stable_hash(body),
    )
    verify_terminal_display_session(session)
    return session


def verify_terminal_display_session(
    session: OracleTerminalDisplaySession,
) -> bool:
    body = asdict(session)
    supplied = body.pop("session_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display session hash mismatch"
        )
    if not session.read_only or not session.interactive_read_only:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display session is not read-only"
        )
    if (
        session.publication_allowed
        or session.action_authorization_allowed
        or session.qseries_execution_allowed
    ):
        raise OracleTerminalDisplaySessionInvariantError(
            "forbidden display session capability enabled"
        )
    if session.frame_count != len(session.frames):
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display frame count mismatch"
        )
    for frame in session.frames:
        verify_terminal_display_frame(frame)
        if frame.source_activation_hash != session.source_output_activation_hash:
            raise OracleTerminalDisplaySessionInvariantError(
                "terminal display frame lineage mismatch"
            )
    if session.session_open and not session.frames:
        raise OracleTerminalDisplaySessionInvariantError(
            "empty terminal display session opened"
        )
    if session.session_open and not session.display_ready:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display session opened without display readiness"
        )
    return True


def build_terminal_display_session_gate_report(
    repository_root: str | Path,
    query: str,
    *,
    activation_report: OracleTerminalRendererActivationGateReport | None = None,
) -> OracleTerminalDisplaySessionGateReport:
    root = Path(repository_root).resolve()
    source = activation_report
    if source is None:
        source = build_terminal_renderer_activation_gate_report(root, query)
    verify_terminal_renderer_activation_gate_report(source)

    session = _build_display_session(query, source)
    source_output = tuple(source.activation.terminal_output_lines)
    reconstructed = _flatten_frames(session.frames)
    preserved = reconstructed == source_output
    ready = bool(
        source.renderer_activation_ready
        and session.session_open
        and session.display_ready
        and preserved
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "activation_report_hash": source.report_hash,
        "display_session": session,
        "session_open": session.session_open,
        "display_ready": session.display_ready,
        "output_preserved_exactly": preserved,
        "display_session_ready": ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleTerminalDisplaySessionGateReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_terminal_display_session_gate_report(report)
    return report


def verify_terminal_display_session_gate_report(
    report: OracleTerminalDisplaySessionGateReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display session gate report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalDisplaySessionInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleTerminalDisplaySessionInvariantError(
            "policy mismatch"
        )
    if not report.read_only:
        raise OracleTerminalDisplaySessionInvariantError(
            "terminal display session gate report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalDisplaySessionInvariantError(
            "forbidden capability enabled"
        )
    verify_terminal_display_session(report.display_session)
    if report.activation_report_hash != (
        report.display_session.source_activation_report_hash
    ):
        raise OracleTerminalDisplaySessionInvariantError(
            "display session activation-report lineage mismatch"
        )
    if report.session_open != report.display_session.session_open:
        raise OracleTerminalDisplaySessionInvariantError(
            "display session open state mismatch"
        )
    if report.display_ready != report.display_session.display_ready:
        raise OracleTerminalDisplaySessionInvariantError(
            "display session readiness state mismatch"
        )
    expected_ready = bool(
        report.session_open
        and report.display_ready
        and report.output_preserved_exactly
    )
    if report.display_session_ready != expected_ready:
        raise OracleTerminalDisplaySessionInvariantError(
            "display session gate readiness mismatch"
        )
    return True
