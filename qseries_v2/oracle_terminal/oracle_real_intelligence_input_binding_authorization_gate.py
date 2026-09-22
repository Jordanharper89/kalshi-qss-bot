from __future__ import annotations
import hashlib, json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping
from .oracle_real_intelligence_input_binding_readiness_gate import (
    OracleRealIntelligenceBindingReadinessReport,
    build_real_intelligence_binding_readiness_report,
    verify_real_intelligence_binding_readiness_report,
)

SCHEMA_VERSION = "OIT-034"
ENGINE_ID = "OIT-034"
POLICY_ID = "oracle.real-intelligence-input-binding-authorization.v1"

class OracleRealIntelligenceAuthorizationInvariantError(RuntimeError):
    pass

@dataclass(frozen=True)
class OracleAuthorizedArtifact:
    relative_path: str
    byte_count: int
    sha256: str
    source_candidate_hash: str
    authorization_granted: bool
    authorization_hash: str

@dataclass(frozen=True)
class OracleAuthorizedCallable:
    module_name: str
    callable_name: str
    signature: tuple[str, ...]
    source_candidate_hash: str
    authorization_granted: bool
    authorization_hash: str

@dataclass(frozen=True)
class OracleRealIntelligenceAuthorizationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    readiness_report_hash: str
    authorized_artifact: OracleAuthorizedArtifact | None
    authorized_callable: OracleAuthorizedCallable | None
    exact_artifact_hash_required: bool
    exact_artifact_byte_count_required: bool
    read_only_invocation_required: bool
    lower_level_bypass_allowed: bool
    persistence_allowed: bool
    analytics_execution_allowed: bool
    database_access_allowed: bool
    networking_allowed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    real_input_binding_authorized: bool
    read_only: bool
    failure_reason: str | None
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

def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()

def _select_artifact(source):
    items = sorted(
        (x for x in source.artifact_candidates if x.candidate_eligible),
        key=lambda x: (x.relative_path, x.sha256, x.byte_count, x.candidate_hash),
    )
    return items[0] if items else None

def _select_callable(source):
    items = sorted(
        (x for x in source.callable_candidates if x.candidate_eligible),
        key=lambda x: (x.module_name, x.callable_name, x.candidate_hash),
    )
    return items[0] if items else None

def build_real_intelligence_binding_authorization_report(
    repository_root: str | Path,
    *,
    readiness_report: OracleRealIntelligenceBindingReadinessReport | None = None,
) -> OracleRealIntelligenceAuthorizationReport:
    root = Path(repository_root).resolve()
    source = readiness_report or build_real_intelligence_binding_readiness_report(root)
    verify_real_intelligence_binding_readiness_report(source)

    artifact_source = _select_artifact(source)
    callable_source = _select_callable(source)

    artifact = None
    if artifact_source is not None:
        body = {
            "relative_path": artifact_source.relative_path,
            "byte_count": artifact_source.byte_count,
            "sha256": artifact_source.sha256,
            "source_candidate_hash": artifact_source.candidate_hash,
            "authorization_granted": bool(
                artifact_source.candidate_eligible
                and artifact_source.byte_count > 0
                and len(artifact_source.sha256) == 64
            ),
        }
        artifact = OracleAuthorizedArtifact(**body, authorization_hash=_hash(body))

    callable_item = None
    if callable_source is not None:
        body = {
            "module_name": callable_source.module_name,
            "callable_name": callable_source.callable_name,
            "signature": tuple(callable_source.signature),
            "source_candidate_hash": callable_source.candidate_hash,
            "authorization_granted": bool(
                callable_source.candidate_eligible
                and callable_source.read_only_name_signal
                and not callable_source.persistence_name_signal
            ),
        }
        callable_item = OracleAuthorizedCallable(**body, authorization_hash=_hash(body))

    authorized = bool(
        source.real_input_binding_ready
        and artifact is not None and artifact.authorization_granted
        and callable_item is not None and callable_item.authorization_granted
    )
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "readiness_report_hash": source.report_hash,
        "authorized_artifact": artifact,
        "authorized_callable": callable_item,
        "exact_artifact_hash_required": True,
        "exact_artifact_byte_count_required": True,
        "read_only_invocation_required": True,
        "lower_level_bypass_allowed": False,
        "persistence_allowed": False,
        "analytics_execution_allowed": False,
        "database_access_allowed": False,
        "networking_allowed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "real_input_binding_authorized": authorized,
        "read_only": True,
        "failure_reason": None if authorized else "real_input_binding_not_authorized",
    }
    report = OracleRealIntelligenceAuthorizationReport(**body, report_hash=_hash(body))
    verify_real_intelligence_binding_authorization_report(report)
    return report

def verify_real_intelligence_binding_authorization_report(report) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _hash(body) != supplied:
        raise OracleRealIntelligenceAuthorizationInvariantError("authorization report hash mismatch")
    if report.schema_version != SCHEMA_VERSION or report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceAuthorizationInvariantError("authorization identity mismatch")
    if not report.read_only:
        raise OracleRealIntelligenceAuthorizationInvariantError("authorization report is not read-only")
    if (
        report.lower_level_bypass_allowed
        or report.persistence_allowed
        or report.analytics_execution_allowed
        or report.database_access_allowed
        or report.networking_allowed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceAuthorizationInvariantError("forbidden capability enabled")
    if not (
        report.exact_artifact_hash_required
        and report.exact_artifact_byte_count_required
        and report.read_only_invocation_required
    ):
        raise OracleRealIntelligenceAuthorizationInvariantError("required authorization control missing")
    if report.authorized_artifact is not None:
        body = asdict(report.authorized_artifact)
        supplied = body.pop("authorization_hash")
        if _hash(body) != supplied:
            raise OracleRealIntelligenceAuthorizationInvariantError("artifact authorization hash mismatch")
    if report.authorized_callable is not None:
        body = asdict(report.authorized_callable)
        supplied = body.pop("authorization_hash")
        if _hash(body) != supplied:
            raise OracleRealIntelligenceAuthorizationInvariantError("callable authorization hash mismatch")
    expected = bool(
        report.authorized_artifact
        and report.authorized_artifact.authorization_granted
        and report.authorized_callable
        and report.authorized_callable.authorization_granted
    )
    if report.real_input_binding_authorized != expected:
        raise OracleRealIntelligenceAuthorizationInvariantError("authorization state mismatch")
    return True
