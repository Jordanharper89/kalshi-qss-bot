from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_decision_brief_renderer_contract import (
    OracleTerminalRendererContract,
    OracleTerminalRendererInvariantError,
    build_terminal_renderer_contract,
    verify_terminal_renderer_contract,
)

SCHEMA_VERSION = "OIT-026"
ENGINE_ID = "OIT-026"
POLICY_ID = "oracle.terminal-renderer-invocation-output-activation-gate.v1"


class OracleTerminalRendererActivationInvariantError(
    OracleTerminalRendererInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalRendererInvocation:
    invocation_id: str
    query: str
    source_renderer_contract_hash: str
    requested_operation: str
    output_mode: str
    invocation_authorized: bool
    display_only: bool
    read_only: bool
    invocation_hash: str


@dataclass(frozen=True)
class OracleTerminalRendererOutputActivation:
    activation_id: str
    invocation_hash: str
    source_renderer_contract_hash: str
    terminal_output_lines: tuple[str, ...]
    output_line_count: int
    display_ready: bool
    output_activated: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
    activation_hash: str


@dataclass(frozen=True)
class OracleTerminalRendererActivationGateReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    renderer_contract_hash: str
    invocation: OracleTerminalRendererInvocation
    activation: OracleTerminalRendererOutputActivation
    invocation_authorized: bool
    output_activated: bool
    display_ready: bool
    renderer_activation_ready: bool
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


def _build_invocation(
    query: str,
    renderer_contract: OracleTerminalRendererContract,
) -> OracleTerminalRendererInvocation:
    invocation_id = _stable_hash(
        {
            "query": query,
            "renderer_contract_hash": renderer_contract.contract_hash,
            "operation": "render_terminal_output",
            "output_mode": "display_only",
        }
    )[:24]
    body = {
        "invocation_id": invocation_id,
        "query": str(query),
        "source_renderer_contract_hash": renderer_contract.contract_hash,
        "requested_operation": "render_terminal_output",
        "output_mode": "display_only",
        "invocation_authorized": bool(
            renderer_contract.renderer_ready
            and renderer_contract.terminal_output_lines
        ),
        "display_only": True,
        "read_only": True,
    }
    return OracleTerminalRendererInvocation(
        **body,
        invocation_hash=_stable_hash(body),
    )


def verify_terminal_renderer_invocation(
    invocation: OracleTerminalRendererInvocation,
) -> bool:
    body = asdict(invocation)
    supplied = body.pop("invocation_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal renderer invocation hash mismatch"
        )
    if invocation.requested_operation != "render_terminal_output":
        raise OracleTerminalRendererActivationInvariantError(
            "unsupported renderer invocation operation"
        )
    if invocation.output_mode != "display_only":
        raise OracleTerminalRendererActivationInvariantError(
            "renderer invocation output mode is not display-only"
        )
    if not invocation.display_only or not invocation.read_only:
        raise OracleTerminalRendererActivationInvariantError(
            "renderer invocation is not read-only display-only"
        )
    if not invocation.source_renderer_contract_hash:
        raise OracleTerminalRendererActivationInvariantError(
            "renderer invocation lineage missing"
        )
    return True


def _build_activation(
    invocation: OracleTerminalRendererInvocation,
    renderer_contract: OracleTerminalRendererContract,
) -> OracleTerminalRendererOutputActivation:
    output = tuple(renderer_contract.terminal_output_lines)
    activation_id = _stable_hash(
        {
            "invocation_hash": invocation.invocation_hash,
            "renderer_contract_hash": renderer_contract.contract_hash,
            "output": output,
        }
    )[:24]
    activated = bool(
        invocation.invocation_authorized
        and renderer_contract.renderer_ready
        and output
    )
    body = {
        "activation_id": activation_id,
        "invocation_hash": invocation.invocation_hash,
        "source_renderer_contract_hash": renderer_contract.contract_hash,
        "terminal_output_lines": output,
        "output_line_count": len(output),
        "display_ready": activated,
        "output_activated": activated,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    return OracleTerminalRendererOutputActivation(
        **body,
        activation_hash=_stable_hash(body),
    )


def verify_terminal_renderer_output_activation(
    activation: OracleTerminalRendererOutputActivation,
) -> bool:
    body = asdict(activation)
    supplied = body.pop("activation_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal renderer activation hash mismatch"
        )
    if not activation.read_only:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal renderer activation is not read-only"
        )
    if (
        activation.publication_allowed
        or activation.action_authorization_allowed
        or activation.qseries_execution_allowed
    ):
        raise OracleTerminalRendererActivationInvariantError(
            "forbidden activation capability enabled"
        )
    if activation.output_line_count != len(activation.terminal_output_lines):
        raise OracleTerminalRendererActivationInvariantError(
            "terminal activation output-line count mismatch"
        )
    if activation.output_activated != activation.display_ready:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal activation display state mismatch"
        )
    if activation.output_activated and not activation.terminal_output_lines:
        raise OracleTerminalRendererActivationInvariantError(
            "empty output activated"
        )
    return True


def build_terminal_renderer_activation_gate_report(
    repository_root: str | Path,
    query: str,
    *,
    renderer_contract: OracleTerminalRendererContract | None = None,
) -> OracleTerminalRendererActivationGateReport:
    root = Path(repository_root).resolve()
    source = renderer_contract
    if source is None:
        source = build_terminal_renderer_contract(root, query)
    verify_terminal_renderer_contract(source)

    invocation = _build_invocation(query, source)
    verify_terminal_renderer_invocation(invocation)

    activation = _build_activation(invocation, source)
    verify_terminal_renderer_output_activation(activation)

    ready = bool(
        invocation.invocation_authorized
        and activation.output_activated
        and activation.display_ready
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "renderer_contract_hash": source.contract_hash,
        "invocation": invocation,
        "activation": activation,
        "invocation_authorized": invocation.invocation_authorized,
        "output_activated": activation.output_activated,
        "display_ready": activation.display_ready,
        "renderer_activation_ready": ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleTerminalRendererActivationGateReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_terminal_renderer_activation_gate_report(report)
    return report


def verify_terminal_renderer_activation_gate_report(
    report: OracleTerminalRendererActivationGateReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal renderer activation report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalRendererActivationInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleTerminalRendererActivationInvariantError(
            "policy mismatch"
        )
    if not report.read_only:
        raise OracleTerminalRendererActivationInvariantError(
            "terminal renderer activation report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalRendererActivationInvariantError(
            "forbidden capability enabled"
        )
    verify_terminal_renderer_invocation(report.invocation)
    verify_terminal_renderer_output_activation(report.activation)
    if report.renderer_contract_hash != (
        report.invocation.source_renderer_contract_hash
    ):
        raise OracleTerminalRendererActivationInvariantError(
            "renderer invocation lineage mismatch"
        )
    if report.renderer_contract_hash != (
        report.activation.source_renderer_contract_hash
    ):
        raise OracleTerminalRendererActivationInvariantError(
            "renderer activation lineage mismatch"
        )
    if report.activation.invocation_hash != report.invocation.invocation_hash:
        raise OracleTerminalRendererActivationInvariantError(
            "activation invocation lineage mismatch"
        )
    if report.invocation_authorized != report.invocation.invocation_authorized:
        raise OracleTerminalRendererActivationInvariantError(
            "invocation authorization state mismatch"
        )
    if report.output_activated != report.activation.output_activated:
        raise OracleTerminalRendererActivationInvariantError(
            "output activation state mismatch"
        )
    if report.display_ready != report.activation.display_ready:
        raise OracleTerminalRendererActivationInvariantError(
            "display readiness state mismatch"
        )
    expected_ready = bool(
        report.invocation_authorized
        and report.output_activated
        and report.display_ready
    )
    if report.renderer_activation_ready != expected_ready:
        raise OracleTerminalRendererActivationInvariantError(
            "renderer activation readiness mismatch"
        )
    return True
