from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_real_intelligence_input_binding_authorization_gate import (
    OracleAuthorizedArtifact,
    OracleAuthorizedCallable,
    OracleRealIntelligenceAuthorizationInvariantError,
    OracleRealIntelligenceAuthorizationReport,
    build_real_intelligence_binding_authorization_report,
    verify_real_intelligence_binding_authorization_report,
)

SCHEMA_VERSION = "OIT-035"
ENGINE_ID = "OIT-035"
POLICY_ID = "oracle.authorized-real-intelligence-read-session-activation.v1"


class OracleRealIntelligenceReadSessionInvariantError(
    OracleRealIntelligenceAuthorizationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceArtifactReadReceipt:
    relative_path: str
    resolved_path: str
    expected_byte_count: int
    observed_byte_count: int
    expected_sha256: str
    observed_sha256: str
    opened_read_only: bool
    content_loaded: bool
    content_mutated: bool
    identity_verified: bool
    receipt_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceCallableResolution:
    module_name: str
    callable_name: str
    expected_signature: tuple[str, ...]
    observed_signature: tuple[str, ...]
    module_imported: bool
    callable_resolved: bool
    signature_verified: bool
    callable_invoked: bool
    resolution_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceReadSession:
    session_id: str
    authorization_report_hash: str
    artifact_authorization_hash: str
    callable_authorization_hash: str
    artifact_read_receipt: OracleRealIntelligenceArtifactReadReceipt
    callable_resolution: OracleRealIntelligenceCallableResolution
    artifact_content_sha256: str
    artifact_content_byte_count: int
    session_active: bool
    bounded_single_artifact: bool
    read_only: bool
    analytics_execution_performed: bool
    callable_invocation_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    session_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceReadSessionActivationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    authorization_report_hash: str
    read_session: OracleRealIntelligenceReadSession
    artifact_identity_verified: bool
    callable_identity_verified: bool
    callable_signature_verified: bool
    read_session_active: bool
    consumption_invocation_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    callable_invocation_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_authorized_path(
    repository_root: Path,
    artifact: OracleAuthorizedArtifact,
) -> Path:
    candidate = (repository_root / artifact.relative_path).resolve()
    runtime_root = (repository_root / "runtime" / "oracle_intelligence").resolve()
    try:
        candidate.relative_to(runtime_root)
    except ValueError as exc:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "authorized artifact escapes canonical runtime root"
        ) from exc
    return candidate


def _read_authorized_artifact(
    repository_root: Path,
    artifact: OracleAuthorizedArtifact,
) -> tuple[OracleRealIntelligenceArtifactReadReceipt, bytes]:
    path = _resolve_authorized_path(repository_root, artifact)
    if not path.is_file():
        raise OracleRealIntelligenceReadSessionInvariantError(
            f"authorized artifact missing: {path}"
        )

    before_stat = path.stat()
    with path.open("rb") as handle:
        content = handle.read()
    after_stat = path.stat()

    observed_sha = _sha256_bytes(content)
    observed_count = len(content)
    unchanged = bool(
        before_stat.st_size == after_stat.st_size
        and before_stat.st_mtime_ns == after_stat.st_mtime_ns
    )
    identity_verified = bool(
        observed_count == artifact.byte_count
        and observed_sha == artifact.sha256
        and unchanged
    )

    body = {
        "relative_path": artifact.relative_path,
        "resolved_path": str(path),
        "expected_byte_count": artifact.byte_count,
        "observed_byte_count": observed_count,
        "expected_sha256": artifact.sha256,
        "observed_sha256": observed_sha,
        "opened_read_only": True,
        "content_loaded": True,
        "content_mutated": not unchanged,
        "identity_verified": identity_verified,
    }
    receipt = OracleRealIntelligenceArtifactReadReceipt(
        **body,
        receipt_hash=_stable_hash(body),
    )
    verify_artifact_read_receipt(receipt)
    return receipt, content


def _resolve_authorized_callable(
    authorization: OracleAuthorizedCallable,
) -> OracleRealIntelligenceCallableResolution:
    module_imported = False
    callable_resolved = False
    observed_signature: tuple[str, ...] = ()
    resolved = None

    try:
        module = importlib.import_module(authorization.module_name)
        module_imported = True
        resolved = getattr(module, authorization.callable_name)
        callable_resolved = callable(resolved)
        if callable_resolved:
            observed_signature = tuple(
                inspect.signature(resolved).parameters
            )
    except Exception:
        module_imported = False
        callable_resolved = False
        observed_signature = ()

    signature_verified = bool(
        callable_resolved
        and observed_signature == tuple(authorization.signature)
    )
    body = {
        "module_name": authorization.module_name,
        "callable_name": authorization.callable_name,
        "expected_signature": tuple(authorization.signature),
        "observed_signature": observed_signature,
        "module_imported": module_imported,
        "callable_resolved": callable_resolved,
        "signature_verified": signature_verified,
        "callable_invoked": False,
    }
    resolution = OracleRealIntelligenceCallableResolution(
        **body,
        resolution_hash=_stable_hash(body),
    )
    verify_callable_resolution(resolution)
    return resolution


def verify_artifact_read_receipt(
    receipt: OracleRealIntelligenceArtifactReadReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "artifact read receipt hash mismatch"
        )
    if not receipt.opened_read_only or not receipt.content_loaded:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "artifact was not loaded through read-only boundary"
        )
    if receipt.content_mutated:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "artifact mutation detected during read"
        )
    expected = bool(
        receipt.expected_byte_count == receipt.observed_byte_count
        and receipt.expected_sha256 == receipt.observed_sha256
    )
    if receipt.identity_verified != expected:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "artifact identity verification mismatch"
        )
    return True


def verify_callable_resolution(
    resolution: OracleRealIntelligenceCallableResolution,
) -> bool:
    body = asdict(resolution)
    supplied = body.pop("resolution_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "callable resolution hash mismatch"
        )
    if resolution.callable_invoked:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "callable invocation performed during resolution"
        )
    expected = bool(
        resolution.module_imported
        and resolution.callable_resolved
        and resolution.expected_signature == resolution.observed_signature
    )
    if resolution.signature_verified != expected:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "callable signature verification mismatch"
        )
    return True


def activate_authorized_real_intelligence_read_session(
    repository_root: str | Path,
    *,
    authorization_report: OracleRealIntelligenceAuthorizationReport | None = None,
) -> OracleRealIntelligenceReadSessionActivationReport:
    root = Path(repository_root).resolve()
    source = authorization_report
    if source is None:
        source = build_real_intelligence_binding_authorization_report(root)
    verify_real_intelligence_binding_authorization_report(source)

    if not source.real_input_binding_authorized:
        raise OracleRealIntelligenceReadSessionInvariantError(
            source.failure_reason or "real input binding not authorized"
        )
    if source.authorized_artifact is None:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "authorized artifact missing"
        )
    if source.authorized_callable is None:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "authorized callable missing"
        )

    receipt, content = _read_authorized_artifact(
        root,
        source.authorized_artifact,
    )
    resolution = _resolve_authorized_callable(
        source.authorized_callable,
    )

    active = bool(
        receipt.identity_verified
        and resolution.signature_verified
        and not receipt.content_mutated
        and not resolution.callable_invoked
    )
    session_body = {
        "session_id": _stable_hash(
            {
                "authorization_report_hash": source.report_hash,
                "artifact_receipt_hash": receipt.receipt_hash,
                "callable_resolution_hash": resolution.resolution_hash,
            }
        )[:24],
        "authorization_report_hash": source.report_hash,
        "artifact_authorization_hash": (
            source.authorized_artifact.authorization_hash
        ),
        "callable_authorization_hash": (
            source.authorized_callable.authorization_hash
        ),
        "artifact_read_receipt": receipt,
        "callable_resolution": resolution,
        "artifact_content_sha256": _sha256_bytes(content),
        "artifact_content_byte_count": len(content),
        "session_active": active,
        "bounded_single_artifact": True,
        "read_only": True,
        "analytics_execution_performed": False,
        "callable_invocation_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
    }
    session = OracleRealIntelligenceReadSession(
        **session_body,
        session_hash=_stable_hash(session_body),
    )
    verify_read_session(session)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "authorization_report_hash": source.report_hash,
        "read_session": session,
        "artifact_identity_verified": receipt.identity_verified,
        "callable_identity_verified": bool(
            resolution.module_imported and resolution.callable_resolved
        ),
        "callable_signature_verified": resolution.signature_verified,
        "read_session_active": session.session_active,
        "consumption_invocation_ready": active,
        "read_only": True,
        "analytics_execution_performed": False,
        "callable_invocation_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None if active else "read_session_not_active",
    }
    report = OracleRealIntelligenceReadSessionActivationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_read_session_activation_report(report)
    return report


def verify_read_session(
    session: OracleRealIntelligenceReadSession,
) -> bool:
    body = asdict(session)
    supplied = body.pop("session_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "read session hash mismatch"
        )
    verify_artifact_read_receipt(session.artifact_read_receipt)
    verify_callable_resolution(session.callable_resolution)
    if not session.bounded_single_artifact or not session.read_only:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "read session boundary invalid"
        )
    if (
        session.analytics_execution_performed
        or session.callable_invocation_performed
        or session.database_access_performed
        or session.runtime_artifact_created
        or session.runtime_artifact_modified
        or session.networking_performed
        or session.publication_allowed
        or session.action_authorization_allowed
        or session.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceReadSessionInvariantError(
            "forbidden session capability enabled"
        )
    expected = bool(
        session.artifact_read_receipt.identity_verified
        and session.callable_resolution.signature_verified
    )
    if session.session_active != expected:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "read session activation mismatch"
        )
    return True


def verify_read_session_activation_report(
    report: OracleRealIntelligenceReadSessionActivationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "read session activation report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "policy mismatch"
        )
    verify_read_session(report.read_session)
    if not report.read_only:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "activation report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.callable_invocation_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceReadSessionInvariantError(
            "forbidden activation capability enabled"
        )
    expected = bool(
        report.artifact_identity_verified
        and report.callable_identity_verified
        and report.callable_signature_verified
        and report.read_session_active
    )
    if report.consumption_invocation_ready != expected:
        raise OracleRealIntelligenceReadSessionInvariantError(
            "consumption invocation readiness mismatch"
        )
    return True
