from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_live_runner_binding_authorization_gate import (
    OracleTerminalRunnerBindingAuthorizationGateReport,
    OracleTerminalRunnerBindingAuthorizationInvariantError,
    verify_terminal_runner_binding_authorization_gate_report,
)

SCHEMA_VERSION = "OIT-030"
ENGINE_ID = "OIT-030"
POLICY_ID = "oracle.live-runner-display-integration-certification.v1"
EXPECTED_RUNNER_NAME = "run_oracle_open_intelligence_terminal.py"


class OracleTerminalLiveRunnerIntegrationInvariantError(
    OracleTerminalRunnerBindingAuthorizationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalLiveRunnerIntegrationCertification:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    runner_path: str
    runner_sha256: str
    authorization_report_hash: str
    runner_version: str
    natural_language_query_supported: bool
    one_shot_query_supported: bool
    interactive_prompt_supported: bool
    certified_display_session_invocation_present: bool
    certified_frame_rendering_present: bool
    exact_frame_order_preserved: bool
    safe_prompt_return_present: bool
    help_command_present: bool
    status_command_present: bool
    quit_command_present: bool
    runner_integration_ready: bool
    read_only: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    certification_hash: str


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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def certify_live_runner_integration(
    repository_root: str | Path,
    authorization_report: OracleTerminalRunnerBindingAuthorizationGateReport,
) -> OracleTerminalLiveRunnerIntegrationCertification:
    root = Path(repository_root).resolve()
    verify_terminal_runner_binding_authorization_gate_report(
        authorization_report
    )
    if not authorization_report.live_runner_binding_authorized:
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "live runner binding is not authorized"
        )

    runner = root / EXPECTED_RUNNER_NAME
    if not runner.is_file():
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            f"live terminal runner missing: {runner}"
        )

    source = runner.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(runner))
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    required_names = {
        "normalize_query",
        "flatten_display_session",
        "execute_query",
        "display_query",
        "run_interactive",
        "build_argument_parser",
        "main",
    }
    required_tokens = {
        "build_terminal_display_session_gate_report",
        "verify_terminal_display_session_gate_report",
        "display_session_ready",
        "frame.frame_lines",
        "publication_allowed",
        "action_authorization_allowed",
        "qseries_execution_allowed",
        '"/help"',
        '"/status"',
        '"/quit"',
        'RUNNER_VERSION = "OIT-030"',
    }

    callable_present = (
        "execute_query" in names
        and "build_terminal_display_session_gate_report" in source
    )
    rendering_present = (
        "flatten_display_session" in names
        and "render_frame_lines" in names
        and "frame.frame_lines" in source
    )
    exact_order = (
        "for index, frame in enumerate(report.display_session.frames)"
        in source
    )
    ready = bool(
        required_names.issubset(names)
        and all(token in source for token in required_tokens)
        and callable_present
        and rendering_present
        and exact_order
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "runner_path": str(runner),
        "runner_sha256": _sha256(runner),
        "authorization_report_hash": authorization_report.report_hash,
        "runner_version": "OIT-030",
        "natural_language_query_supported": "normalize_query" in names,
        "one_shot_query_supported": "build_argument_parser" in names,
        "interactive_prompt_supported": "run_interactive" in names,
        "certified_display_session_invocation_present": callable_present,
        "certified_frame_rendering_present": rendering_present,
        "exact_frame_order_preserved": exact_order,
        "safe_prompt_return_present": "while True" in source,
        "help_command_present": '"/help"' in source,
        "status_command_present": '"/status"' in source,
        "quit_command_present": '"/quit"' in source,
        "runner_integration_ready": ready,
        "read_only": True,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    certification = OracleTerminalLiveRunnerIntegrationCertification(
        **body,
        certification_hash=_stable_hash(body),
    )
    verify_live_runner_integration_certification(certification)
    return certification


def verify_live_runner_integration_certification(
    certification: OracleTerminalLiveRunnerIntegrationCertification,
) -> bool:
    body = asdict(certification)
    supplied = body.pop("certification_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "live runner integration certification hash mismatch"
        )
    if certification.schema_version != SCHEMA_VERSION:
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "schema mismatch"
        )
    if certification.policy_id != POLICY_ID:
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "policy mismatch"
        )
    if not certification.read_only:
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "live runner integration is not read-only"
        )
    if (
        certification.publication_allowed
        or certification.action_authorization_allowed
        or certification.qseries_execution_allowed
    ):
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "forbidden live runner capability enabled"
        )
    required = (
        certification.natural_language_query_supported,
        certification.one_shot_query_supported,
        certification.interactive_prompt_supported,
        certification.certified_display_session_invocation_present,
        certification.certified_frame_rendering_present,
        certification.exact_frame_order_preserved,
        certification.safe_prompt_return_present,
        certification.help_command_present,
        certification.status_command_present,
        certification.quit_command_present,
    )
    if certification.runner_integration_ready != all(required):
        raise OracleTerminalLiveRunnerIntegrationInvariantError(
            "live runner integration readiness mismatch"
        )
    return True
