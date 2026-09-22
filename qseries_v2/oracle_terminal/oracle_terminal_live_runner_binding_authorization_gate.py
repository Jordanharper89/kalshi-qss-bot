from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_terminal_live_runner_binding_readiness_gate import (
    OracleTerminalRunnerBindingReadinessGateReport,
    OracleTerminalRunnerBindingReadinessInvariantError,
    build_terminal_runner_binding_readiness_gate_report,
    verify_terminal_runner_binding_readiness_gate_report,
)

SCHEMA_VERSION = "OIT-029"
ENGINE_ID = "OIT-029"
POLICY_ID = "oracle.live-runner-binding-authorization-gate.v1"

AUTHORIZED_MODULE = (
    "qseries_v2.oracle_terminal."
    "oracle_terminal_activated_output_display_session_gate"
)
AUTHORIZED_CALLABLE = "build_terminal_display_session_gate_report"


class OracleTerminalRunnerBindingAuthorizationInvariantError(
    OracleTerminalRunnerBindingReadinessInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalRunnerCallableAuthorization:
    authorization_id: str
    runner_sha256: str
    readiness_report_hash: str
    authorized_module: str
    authorized_callable: str
    authorized_signature: tuple[str, ...]
    invocation_mode: str
    display_only: bool
    read_only: bool
    analytics_access_allowed: bool
    database_access_allowed: bool
    networking_allowed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    authorization_granted: bool
    authorization_hash: str


@dataclass(frozen=True)
class OracleTerminalRunnerDeniedCapability:
    capability_name: str
    denial_reason: str
    denial_enforced: bool
    denial_hash: str


@dataclass(frozen=True)
class OracleTerminalRunnerBindingAuthorizationGateReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    readiness_report_hash: str
    runner_sha256: str
    callable_authorization: OracleTerminalRunnerCallableAuthorization
    denied_capabilities: tuple[OracleTerminalRunnerDeniedCapability, ...]
    denied_capability_count: int
    runner_identity_authorized: bool
    callable_identity_authorized: bool
    signature_authorized: bool
    display_only_authorized: bool
    read_only_boundary_authorized: bool
    live_runner_binding_authorized: bool
    runner_modified: bool
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


def _build_denial(
    capability_name: str,
    denial_reason: str,
) -> OracleTerminalRunnerDeniedCapability:
    body = {
        "capability_name": capability_name,
        "denial_reason": denial_reason,
        "denial_enforced": True,
    }
    return OracleTerminalRunnerDeniedCapability(
        **body,
        denial_hash=_stable_hash(body),
    )


def verify_terminal_runner_denied_capability(
    denial: OracleTerminalRunnerDeniedCapability,
) -> bool:
    body = asdict(denial)
    supplied = body.pop("denial_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner denied capability hash mismatch"
        )
    if not denial.capability_name or not denial.denial_reason:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner denied capability metadata missing"
        )
    if not denial.denial_enforced:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner denied capability not enforced"
        )
    return True


def _build_authorization(
    readiness: OracleTerminalRunnerBindingReadinessGateReport,
) -> OracleTerminalRunnerCallableAuthorization:
    binding = readiness.binding_contract
    granted = bool(
        readiness.live_runner_binding_ready
        and readiness.runner_identity_verified
        and readiness.syntax_verified
        and readiness.import_safety_verified
        and readiness.callable_resolution_verified
        and readiness.signature_compatibility_verified
        and readiness.read_only_dependency_verified
        and not readiness.runner_modified
        and binding.required_callable_module == AUTHORIZED_MODULE
        and binding.required_callable_name == AUTHORIZED_CALLABLE
        and binding.required_callable_signature == ("repository_root", "query")
        and not binding.publication_exposure_detected
        and not binding.execution_exposure_detected
        and not binding.database_write_exposure_detected
        and not binding.networking_side_effect_exposure_detected
    )
    body = {
        "authorization_id": _stable_hash(
            {
                "runner_sha256": readiness.runner_inspection.runner_sha256,
                "readiness_report_hash": readiness.report_hash,
                "module": AUTHORIZED_MODULE,
                "callable": AUTHORIZED_CALLABLE,
            }
        )[:24],
        "runner_sha256": readiness.runner_inspection.runner_sha256,
        "readiness_report_hash": readiness.report_hash,
        "authorized_module": AUTHORIZED_MODULE,
        "authorized_callable": AUTHORIZED_CALLABLE,
        "authorized_signature": ("repository_root", "query"),
        "invocation_mode": "display_session_only",
        "display_only": True,
        "read_only": True,
        "analytics_access_allowed": False,
        "database_access_allowed": False,
        "networking_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "authorization_granted": granted,
    }
    authorization = OracleTerminalRunnerCallableAuthorization(
        **body,
        authorization_hash=_stable_hash(body),
    )
    verify_terminal_runner_callable_authorization(authorization)
    return authorization


def verify_terminal_runner_callable_authorization(
    authorization: OracleTerminalRunnerCallableAuthorization,
) -> bool:
    body = asdict(authorization)
    supplied = body.pop("authorization_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner callable authorization hash mismatch"
        )
    if authorization.authorized_module != AUTHORIZED_MODULE:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "unauthorized runner module"
        )
    if authorization.authorized_callable != AUTHORIZED_CALLABLE:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "unauthorized runner callable"
        )
    if authorization.authorized_signature != ("repository_root", "query"):
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "unauthorized runner callable signature"
        )
    if authorization.invocation_mode != "display_session_only":
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner invocation mode is not display-session-only"
        )
    if not authorization.display_only or not authorization.read_only:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner authorization is not read-only display-only"
        )
    if (
        authorization.analytics_access_allowed
        or authorization.database_access_allowed
        or authorization.networking_allowed
        or authorization.publication_allowed
        or authorization.action_authorization_allowed
        or authorization.qseries_execution_allowed
    ):
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "forbidden runner capability authorized"
        )
    return True


def build_terminal_runner_binding_authorization_gate_report(
    repository_root: str | Path,
    query: str,
    *,
    readiness_report: OracleTerminalRunnerBindingReadinessGateReport | None = None,
) -> OracleTerminalRunnerBindingAuthorizationGateReport:
    root = Path(repository_root).resolve()
    source = readiness_report
    if source is None:
        source = build_terminal_runner_binding_readiness_gate_report(root, query)
    verify_terminal_runner_binding_readiness_gate_report(source)

    authorization = _build_authorization(source)
    denials = (
        _build_denial(
            "direct_analytics_execution",
            "runner may consume only the certified display-session gate",
        ),
        _build_denial(
            "database_access",
            "terminal presentation runner has no database-access authority",
        ),
        _build_denial(
            "networking",
            "terminal presentation runner has no direct networking authority",
        ),
        _build_denial(
            "publication",
            "display output is local and not publication-authorized",
        ),
        _build_denial(
            "action_authorization",
            "terminal output cannot authorize operator or market actions",
        ),
        _build_denial(
            "qseries_execution",
            "Oracle remains isolated from Q Series execution",
        ),
        _build_denial(
            "lower_level_terminal_bypass",
            "runner must invoke the certified OIT-027 display-session boundary",
        ),
    )
    for denial in denials:
        verify_terminal_runner_denied_capability(denial)

    authorized = bool(
        authorization.authorization_granted
        and all(item.denial_enforced for item in denials)
    )
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "readiness_report_hash": source.report_hash,
        "runner_sha256": source.runner_inspection.runner_sha256,
        "callable_authorization": authorization,
        "denied_capabilities": denials,
        "denied_capability_count": len(denials),
        "runner_identity_authorized": bool(
            source.runner_identity_verified
            and authorization.runner_sha256
            == source.runner_inspection.runner_sha256
        ),
        "callable_identity_authorized": bool(
            authorization.authorized_module == AUTHORIZED_MODULE
            and authorization.authorized_callable == AUTHORIZED_CALLABLE
        ),
        "signature_authorized": bool(
            authorization.authorized_signature
            == ("repository_root", "query")
        ),
        "display_only_authorized": bool(
            authorization.display_only
            and authorization.invocation_mode == "display_session_only"
        ),
        "read_only_boundary_authorized": bool(
            authorization.read_only
            and not authorization.analytics_access_allowed
            and not authorization.database_access_allowed
            and not authorization.networking_allowed
            and not authorization.publication_allowed
            and not authorization.action_authorization_allowed
            and not authorization.qseries_execution_allowed
        ),
        "live_runner_binding_authorized": authorized,
        "runner_modified": False,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None if authorized else "runner_binding_not_authorized",
    }
    report = OracleTerminalRunnerBindingAuthorizationGateReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_terminal_runner_binding_authorization_gate_report(report)
    return report


def verify_terminal_runner_binding_authorization_gate_report(
    report: OracleTerminalRunnerBindingAuthorizationGateReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner binding authorization report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "policy mismatch"
        )
    if report.runner_modified:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner modification detected during authorization"
        )
    if not report.read_only:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner binding authorization report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "forbidden capability enabled"
        )
    verify_terminal_runner_callable_authorization(
        report.callable_authorization
    )
    if report.denied_capability_count != len(report.denied_capabilities):
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "denied capability count mismatch"
        )
    for denial in report.denied_capabilities:
        verify_terminal_runner_denied_capability(denial)
    if report.readiness_report_hash != (
        report.callable_authorization.readiness_report_hash
    ):
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "authorization readiness lineage mismatch"
        )
    if report.runner_sha256 != report.callable_authorization.runner_sha256:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "authorization runner identity mismatch"
        )
    expected = bool(
        report.callable_authorization.authorization_granted
        and report.runner_identity_authorized
        and report.callable_identity_authorized
        and report.signature_authorized
        and report.display_only_authorized
        and report.read_only_boundary_authorized
        and all(
            denial.denial_enforced
            for denial in report.denied_capabilities
        )
    )
    if report.live_runner_binding_authorized != expected:
        raise OracleTerminalRunnerBindingAuthorizationInvariantError(
            "runner binding authorization state mismatch"
        )
    return True
