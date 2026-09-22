from __future__ import annotations

import hashlib
import json
import shlex
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "OIT-001"
ENGINE_ID = "OIT-001"
POLICY_ID = "oracle.open-intelligence-terminal-foundation.v1"
TERMINAL_NAME = "Oracle Open Intelligence Terminal"
TERMINAL_PROMPT = "oracle> "
TERMINAL_STATUS = "open_intelligence_terminal_foundation_ready"

READ_ONLY_COMMANDS = (
    "help",
    "status",
    "health",
    "runtime",
    "certification",
    "freshness",
    "coverage",
    "capabilities",
    "analyze",
    "explain",
    "confidence",
    "evidence",
    "sources",
    "timeline",
    "challenge",
    "contradictions",
    "assumptions",
    "hypotheses",
    "invalidation",
    "uncertainty",
    "opportunities",
    "changes",
    "compare",
    "divergence",
    "rank",
    "watch",
    "predictions",
    "outcomes",
    "wins",
    "losses",
    "calibration",
    "history",
)
SESSION_COMMANDS = ("clear", "exit", "quit")
FORBIDDEN_EXECUTION_COMMANDS = (
    "buy",
    "sell",
    "trade",
    "execute",
    "order",
    "cancel-order",
    "deposit",
    "withdraw",
    "transfer",
    "publish",
)
SUBJECT_OPTIONAL_COMMANDS = {
    "help", "status", "health", "runtime", "certification", "freshness",
    "coverage", "capabilities", "opportunities", "changes", "predictions",
    "outcomes", "wins", "losses", "calibration", "history",
}


class OracleOpenIntelligenceTerminalInvariantError(ValueError):
    pass


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleOpenIntelligenceTerminalInvariantError(
        f"unsupported canonical value type: {type(value)!r}"
    )


def stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class OracleTerminalDependencyReceipt:
    source_schema_version: str
    source_engine_id: str
    source_module_sha256: str
    runtime_complete: bool
    immutable_freeze: bool
    read_only: bool
    downstream_read_only_operation_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool
    receipt_hash: str


@dataclass(frozen=True)
class OracleTerminalCommand:
    command: str
    subject: str
    arguments: tuple[str, ...]
    raw_text: str
    read_only: bool
    command_hash: str


@dataclass(frozen=True)
class OracleTerminalResponse:
    command_hash: str
    response_type: str
    status: str
    subject: str
    lines: tuple[str, ...]
    read_only: bool
    execution_allowed: bool
    publication_allowed: bool
    data_available: bool
    response_hash: str


def build_dependency_receipt(*, source_module_sha256: str) -> OracleTerminalDependencyReceipt:
    if len(source_module_sha256) != 64 or any(c not in "0123456789abcdef" for c in source_module_sha256):
        raise OracleOpenIntelligenceTerminalInvariantError("invalid OOR-013 module sha256")
    body = {
        "source_schema_version": "OOR-013",
        "source_engine_id": "OOR-013",
        "source_module_sha256": source_module_sha256,
        "runtime_complete": True,
        "immutable_freeze": True,
        "read_only": True,
        "downstream_read_only_operation_allowed": True,
        "qseries_execution_allowed": False,
        "order_creation_allowed": False,
        "funds_movement_allowed": False,
        "portfolio_mutation_allowed": False,
    }
    return OracleTerminalDependencyReceipt(**body, receipt_hash=stable_hash(body))


def verify_dependency_receipt(receipt: OracleTerminalDependencyReceipt) -> bool:
    if not isinstance(receipt, OracleTerminalDependencyReceipt):
        raise OracleOpenIntelligenceTerminalInvariantError("invalid dependency receipt type")
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if stable_hash(body) != supplied:
        raise OracleOpenIntelligenceTerminalInvariantError("dependency receipt hash mismatch")
    required = (
        receipt.source_schema_version == "OOR-013",
        receipt.source_engine_id == "OOR-013",
        receipt.runtime_complete,
        receipt.immutable_freeze,
        receipt.read_only,
        receipt.downstream_read_only_operation_allowed,
        not receipt.qseries_execution_allowed,
        not receipt.order_creation_allowed,
        not receipt.funds_movement_allowed,
        not receipt.portfolio_mutation_allowed,
    )
    if not all(required):
        raise OracleOpenIntelligenceTerminalInvariantError("OOR-013 read-only boundary violated")
    return True


def parse_terminal_input(text: str) -> OracleTerminalCommand:
    if not isinstance(text, str):
        raise OracleOpenIntelligenceTerminalInvariantError("terminal input must be text")
    raw = text.strip()
    if not raw:
        raise OracleOpenIntelligenceTerminalInvariantError("terminal input cannot be empty")
    try:
        tokens = shlex.split(raw, posix=False)
    except ValueError as exc:
        raise OracleOpenIntelligenceTerminalInvariantError(str(exc)) from exc
    if not tokens:
        raise OracleOpenIntelligenceTerminalInvariantError("terminal input cannot be empty")
    command = tokens[0].lower().strip()
    arguments = tuple(token.strip('"') for token in tokens[1:])
    subject = " ".join(arguments).strip()
    body = {
        "command": command,
        "subject": subject,
        "arguments": arguments,
        "raw_text": raw,
        "read_only": True,
    }
    return OracleTerminalCommand(**body, command_hash=stable_hash(body))


def _response(
    command: OracleTerminalCommand,
    *,
    response_type: str,
    status: str,
    lines: Sequence[str],
    data_available: bool,
) -> OracleTerminalResponse:
    body = {
        "command_hash": command.command_hash,
        "response_type": response_type,
        "status": status,
        "subject": command.subject,
        "lines": tuple(str(line) for line in lines),
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "data_available": bool(data_available),
    }
    return OracleTerminalResponse(**body, response_hash=stable_hash(body))


def discover_local_intelligence(repository_root: Path) -> Mapping[str, Any]:
    root = Path(repository_root).resolve()
    targets = {
        "live_shadow_runtime": root / "runtime" / "oracle_live_shadow",
        "intelligence_runtime": root / "runtime" / "oracle_intelligence",
        "research_response_runtime": root / "runtime" / "oracle_research_response",
        "analytics_package": root / "qseries_v2" / "oracle_intelligence" / "analytics",
        "operator_runtime_package": root / "qseries_v2" / "oracle_operator_runtime",
    }
    result: dict[str, Any] = {}
    for name, path in targets.items():
        exists = path.exists()
        file_count = 0
        if exists and path.is_dir():
            try:
                file_count = sum(1 for item in path.rglob("*") if item.is_file())
            except OSError:
                file_count = 0
        result[name] = {
            "exists": exists,
            "file_count": file_count,
            "path": str(path),
        }
    return result


def execute_terminal_command(
    command: OracleTerminalCommand,
    *,
    repository_root: Path,
    dependency_receipt: OracleTerminalDependencyReceipt,
) -> OracleTerminalResponse:
    verify_dependency_receipt(dependency_receipt)
    if command.command_hash != stable_hash({
        "command": command.command,
        "subject": command.subject,
        "arguments": command.arguments,
        "raw_text": command.raw_text,
        "read_only": command.read_only,
    }):
        raise OracleOpenIntelligenceTerminalInvariantError("terminal command hash mismatch")
    if not command.read_only:
        raise OracleOpenIntelligenceTerminalInvariantError("terminal command must remain read-only")

    if command.command in FORBIDDEN_EXECUTION_COMMANDS:
        return _response(
            command,
            response_type="execution_rejection",
            status="rejected_read_only_boundary",
            lines=(
                "Execution is disabled in Oracle.",
                "Oracle can inspect, analyze, explain, and challenge intelligence only.",
                "Q Series remains the sole execution layer.",
            ),
            data_available=False,
        )

    if command.command in SESSION_COMMANDS:
        return _response(
            command,
            response_type="session_control",
            status=command.command,
            lines=(command.command,),
            data_available=True,
        )

    if command.command not in READ_ONLY_COMMANDS:
        return _response(
            command,
            response_type="unknown_command",
            status="unsupported_command",
            lines=(
                f"Unknown command: {command.command}",
                "Type 'help' to list the current open-intelligence commands.",
            ),
            data_available=False,
        )

    discovery = discover_local_intelligence(repository_root)

    if command.command == "help":
        return _response(
            command,
            response_type="help",
            status="ok",
            lines=(
                "SYSTEM: status health runtime certification freshness coverage capabilities",
                "INTELLIGENCE: analyze explain confidence evidence sources timeline",
                "REASONING: challenge contradictions assumptions hypotheses invalidation uncertainty",
                "DISCOVERY: opportunities changes compare divergence rank watch",
                "ACCOUNTABILITY: predictions outcomes wins losses calibration history",
                "SESSION: clear exit quit",
                "USAGE: <command> <any subject>",
            ),
            data_available=True,
        )

    if command.command in {"status", "health", "runtime", "certification", "freshness", "coverage", "capabilities"}:
        lines = [
            f"{TERMINAL_NAME}: READY",
            "Mode: local read-only intelligence inspection",
            "Execution: disabled",
            "Publication: disabled",
            f"OOR dependency: {dependency_receipt.source_schema_version} complete and frozen",
        ]
        for name, item in discovery.items():
            state = "available" if item["exists"] else "not found"
            lines.append(f"{name}: {state} ({item['file_count']} files)")
        return _response(
            command,
            response_type="system_status",
            status=TERMINAL_STATUS,
            lines=lines,
            data_available=True,
        )

    if command.command not in SUBJECT_OPTIONAL_COMMANDS and not command.subject:
        return _response(
            command,
            response_type="missing_subject",
            status="subject_required",
            lines=(f"Command '{command.command}' requires a subject.",),
            data_available=False,
        )

    intelligence_runtime = discovery["intelligence_runtime"]
    research_runtime = discovery["research_response_runtime"]
    available = bool(intelligence_runtime["exists"] or research_runtime["exists"])
    lines = [
        f"Command: {command.command}",
        f"Subject: {command.subject or 'all available intelligence'}",
        "Read-only request: accepted",
    ]
    if available:
        lines.extend((
            "Local intelligence artifacts were discovered.",
            "OIT-001 does not yet bind command-specific artifact resolution.",
            "Next terminal layers will connect this request to certified Oracle outputs.",
        ))
        status = "accepted_binding_pending"
    else:
        lines.extend((
            "No active Oracle intelligence or research-response runtime artifacts were found.",
            "Installed analytics capability is preserved; live output binding is not yet active.",
            "No analysis was fabricated.",
        ))
        status = "accepted_no_live_artifact"
    return _response(
        command,
        response_type="open_intelligence_request",
        status=status,
        lines=lines,
        data_available=available,
    )


def format_terminal_response(response: OracleTerminalResponse) -> str:
    body = asdict(response)
    supplied = body.pop("response_hash")
    if stable_hash(body) != supplied:
        raise OracleOpenIntelligenceTerminalInvariantError("terminal response hash mismatch")
    if not response.read_only or response.execution_allowed or response.publication_allowed:
        raise OracleOpenIntelligenceTerminalInvariantError("unsafe terminal response boundary")
    return "\n".join(response.lines)


def terminal_banner() -> str:
    return "\n".join((
        "=" * 56,
        f" {TERMINAL_NAME.upper()}",
        " READ-ONLY FOUNDATION",
        "=" * 56,
        "Type 'help' for commands. Type 'exit' to close.",
    ))


__all__ = [
    "SCHEMA_VERSION", "ENGINE_ID", "POLICY_ID", "TERMINAL_NAME",
    "TERMINAL_PROMPT", "TERMINAL_STATUS", "READ_ONLY_COMMANDS",
    "SESSION_COMMANDS", "FORBIDDEN_EXECUTION_COMMANDS",
    "OracleOpenIntelligenceTerminalInvariantError",
    "OracleTerminalDependencyReceipt", "OracleTerminalCommand",
    "OracleTerminalResponse", "stable_hash", "build_dependency_receipt",
    "verify_dependency_receipt", "parse_terminal_input",
    "discover_local_intelligence", "execute_terminal_command",
    "format_terminal_response", "terminal_banner",
]
