from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "OIT-032"
ENGINE_ID = "OIT-032"
POLICY_ID = "oracle.interactive-command-registry.v2"


class OracleTerminalCommandRegistryInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleTerminalCommandDefinition:
    command: str
    aliases: tuple[str, ...]
    handler_name: str
    summary: str
    accepts_argument: bool
    exits_terminal: bool
    clears_terminal: bool
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    definition_hash: str


@dataclass(frozen=True)
class OracleTerminalCommandResolution:
    raw_input: str
    normalized_input: str
    matched: bool
    command: str | None
    handler_name: str | None
    argument: str
    exits_terminal: bool
    clears_terminal: bool
    read_only: bool
    resolution_hash: str


@dataclass(frozen=True)
class OracleTerminalCommandRegistryReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    commands: tuple[OracleTerminalCommandDefinition, ...]
    command_count: int
    aliases_unique: bool
    registry_ready: bool
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _definition(command, aliases, handler_name, summary, *, accepts_argument=False, exits_terminal=False, clears_terminal=False):
    body = {
        "command": command.strip().lower(),
        "aliases": tuple(sorted({a.strip().lower() for a in aliases if a.strip()})),
        "handler_name": handler_name,
        "summary": summary,
        "accepts_argument": accepts_argument,
        "exits_terminal": exits_terminal,
        "clears_terminal": clears_terminal,
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    item = OracleTerminalCommandDefinition(**body, definition_hash=_stable_hash(body))
    verify_command_definition(item)
    return item


def build_default_command_registry():
    commands = (
        _definition("/help", ("help", "?"), "handle_help", "Show available terminal commands."),
        _definition("/status", ("status",), "handle_status", "Show certified read-only terminal status."),
        _definition("/ask", ("ask",), "handle_ask", "Submit a natural-language intelligence question.", accepts_argument=True),
        _definition("/session", ("session",), "handle_session", "Show current local read-only session state."),
        _definition("/panels", ("panels",), "handle_panels", "List available intelligence panels."),
        _definition("/panel", ("panel",), "handle_panel", "Open a named intelligence panel.", accepts_argument=True),
        _definition("/evidence", ("evidence",), "handle_evidence", "Open the evidence panel."),
        _definition("/next", ("next",), "handle_next", "Move to the next intelligence panel."),
        _definition("/back", ("back", "previous", "prev"), "handle_back", "Move to the previous intelligence panel."),
        _definition("/clear", ("clear",), "handle_clear", "Clear the visible terminal screen.", clears_terminal=True),
        _definition("/quit", ("/exit", "quit", "exit"), "handle_quit", "Close the Oracle terminal.", exits_terminal=True),
    )
    tokens = []
    for item in commands:
        tokens.append(item.command)
        tokens.extend(item.aliases)
    unique = len(tokens) == len(set(tokens))
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "commands": commands,
        "command_count": len(commands),
        "aliases_unique": unique,
        "registry_ready": bool(commands and unique),
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    report = OracleTerminalCommandRegistryReport(**body, report_hash=_stable_hash(body))
    verify_command_registry_report(report)
    return report


def verify_command_definition(item):
    body = asdict(item)
    supplied = body.pop("definition_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalCommandRegistryInvariantError("command definition hash mismatch")
    if not item.command.startswith("/") or not item.handler_name.startswith("handle_"):
        raise OracleTerminalCommandRegistryInvariantError("command identity invalid")
    if not item.read_only or item.publication_allowed or item.action_authorization_allowed or item.qseries_execution_allowed:
        raise OracleTerminalCommandRegistryInvariantError("forbidden command capability enabled")
    return True


def verify_command_registry_report(report):
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalCommandRegistryInvariantError("command registry report hash mismatch")
    if report.schema_version != SCHEMA_VERSION or report.policy_id != POLICY_ID:
        raise OracleTerminalCommandRegistryInvariantError("registry identity mismatch")
    if report.command_count != len(report.commands):
        raise OracleTerminalCommandRegistryInvariantError("command count mismatch")
    for item in report.commands:
        verify_command_definition(item)
    if not report.aliases_unique or not report.registry_ready or not report.read_only:
        raise OracleTerminalCommandRegistryInvariantError("command registry not ready")
    if report.publication_allowed or report.action_authorization_allowed or report.qseries_execution_allowed:
        raise OracleTerminalCommandRegistryInvariantError("forbidden registry capability enabled")
    return True


def resolve_terminal_command(raw_input, *, registry=None):
    active = registry or build_default_command_registry()
    verify_command_registry_report(active)
    normalized = " ".join(str(raw_input).strip().split())
    token, argument = (normalized.split(" ", 1) + [""])[:2] if " " in normalized else (normalized, "")
    lowered = token.lower()
    match = None
    for item in active.commands:
        if lowered == item.command or lowered in item.aliases:
            match = item
            break
    body = {
        "raw_input": str(raw_input),
        "normalized_input": normalized,
        "matched": match is not None,
        "command": match.command if match else None,
        "handler_name": match.handler_name if match else None,
        "argument": argument if match else normalized,
        "exits_terminal": bool(match and match.exits_terminal),
        "clears_terminal": bool(match and match.clears_terminal),
        "read_only": True,
    }
    resolution = OracleTerminalCommandResolution(**body, resolution_hash=_stable_hash(body))
    verify_command_resolution(resolution)
    return resolution


def verify_command_resolution(resolution):
    body = asdict(resolution)
    supplied = body.pop("resolution_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalCommandRegistryInvariantError("command resolution hash mismatch")
    if not resolution.read_only:
        raise OracleTerminalCommandRegistryInvariantError("resolution not read-only")
    return True
