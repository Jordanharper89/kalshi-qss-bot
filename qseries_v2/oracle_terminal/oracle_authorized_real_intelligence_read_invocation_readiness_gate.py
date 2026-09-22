from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_authorized_real_intelligence_read_session_activation_gate import (
    OracleRealIntelligenceReadSessionActivationReport,
    OracleRealIntelligenceReadSessionInvariantError,
    activate_authorized_real_intelligence_read_session,
    verify_read_session_activation_report,
)

SCHEMA_VERSION = "OIT-036"
ENGINE_ID = "OIT-036"
POLICY_ID = "oracle.authorized-real-intelligence-read-invocation-readiness.v1"


class OracleRealIntelligenceReadInvocationReadinessInvariantError(
    OracleRealIntelligenceReadSessionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceInvocationArgument:
    argument_name: str
    argument_position: int
    value_kind: str
    canonical_value: str
    source_lineage_hash: str
    read_only: bool
    argument_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceReadInvocationManifest:
    invocation_id: str
    session_hash: str
    module_name: str
    callable_name: str
    callable_signature: tuple[str, ...]
    invocation_arguments: tuple[OracleRealIntelligenceInvocationArgument, ...]
    invocation_argument_count: int
    exact_signature_bound: bool
    exact_artifact_path_bound: bool
    repository_root_bound: bool
    persist_argument_present: bool
    persist_argument_value: bool | None
    invocation_ready: bool
    callable_invoked: bool
    read_only: bool
    manifest_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceReadInvocationReadinessReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    read_session_report_hash: str
    invocation_manifest: OracleRealIntelligenceReadInvocationManifest
    exact_callable_identity_verified: bool
    exact_callable_signature_verified: bool
    exact_argument_binding_verified: bool
    persistence_disabled: bool
    bounded_single_artifact_verified: bool
    invocation_ready: bool
    invocation_performed: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
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


def _argument(
    *,
    name: str,
    position: int,
    value_kind: str,
    canonical_value: str,
    source_lineage_hash: str,
) -> OracleRealIntelligenceInvocationArgument:
    body = {
        "argument_name": name,
        "argument_position": position,
        "value_kind": value_kind,
        "canonical_value": canonical_value,
        "source_lineage_hash": source_lineage_hash,
        "read_only": True,
    }
    argument = OracleRealIntelligenceInvocationArgument(
        **body,
        argument_hash=_stable_hash(body),
    )
    verify_invocation_argument(argument)
    return argument


def _bind_arguments(
    report: OracleRealIntelligenceReadSessionActivationReport,
) -> tuple[OracleRealIntelligenceInvocationArgument, ...]:
    session = report.read_session
    signature = session.callable_resolution.observed_signature
    repository_root = report.repository_root
    artifact_path = session.artifact_read_receipt.resolved_path

    values = []
    for position, name in enumerate(signature):
        lowered = name.lower()

        if lowered in {
            "repository_root",
            "repo_root",
            "root",
        }:
            values.append(
                _argument(
                    name=name,
                    position=position,
                    value_kind="repository_root",
                    canonical_value=repository_root,
                    source_lineage_hash=report.report_hash,
                )
            )
            continue

        if lowered in {
            "artifact_path",
            "path",
            "source_path",
            "runtime_artifact_path",
        }:
            values.append(
                _argument(
                    name=name,
                    position=position,
                    value_kind="authorized_artifact_path",
                    canonical_value=artifact_path,
                    source_lineage_hash=(
                        session.artifact_read_receipt.receipt_hash
                    ),
                )
            )
            continue

        if lowered == "persist":
            values.append(
                _argument(
                    name=name,
                    position=position,
                    value_kind="boolean",
                    canonical_value="false",
                    source_lineage_hash=session.session_hash,
                )
            )
            continue

        values.append(
            _argument(
                name=name,
                position=position,
                value_kind="unsupported_unbound",
                canonical_value="",
                source_lineage_hash=session.session_hash,
            )
        )

    return tuple(values)


def verify_invocation_argument(
    argument: OracleRealIntelligenceInvocationArgument,
) -> bool:
    body = asdict(argument)
    supplied = body.pop("argument_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument hash mismatch"
        )
    if argument.argument_position < 0:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument position invalid"
        )
    if not argument.argument_name:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument name missing"
        )
    if not argument.source_lineage_hash:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument lineage missing"
        )
    if not argument.read_only:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument is not read-only"
        )
    return True


def verify_invocation_manifest(
    manifest: OracleRealIntelligenceReadInvocationManifest,
) -> bool:
    body = asdict(manifest)
    supplied = body.pop("manifest_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation manifest hash mismatch"
        )
    if not manifest.read_only:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation manifest is not read-only"
        )
    if manifest.callable_invoked:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "callable invoked during readiness certification"
        )
    if manifest.invocation_argument_count != len(
        manifest.invocation_arguments
    ):
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation argument count mismatch"
        )
    for argument in manifest.invocation_arguments:
        verify_invocation_argument(argument)

    expected_ready = bool(
        manifest.exact_signature_bound
        and manifest.exact_artifact_path_bound
        and manifest.repository_root_bound
        and all(
            argument.value_kind != "unsupported_unbound"
            for argument in manifest.invocation_arguments
        )
        and (
            not manifest.persist_argument_present
            or manifest.persist_argument_value is False
        )
    )
    if manifest.invocation_ready != expected_ready:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "invocation readiness mismatch"
        )
    return True


def build_authorized_read_invocation_readiness_report(
    repository_root: str | Path,
    *,
    read_session_report: OracleRealIntelligenceReadSessionActivationReport | None = None,
) -> OracleRealIntelligenceReadInvocationReadinessReport:
    root = Path(repository_root).resolve()
    source = read_session_report
    if source is None:
        source = activate_authorized_real_intelligence_read_session(root)
    verify_read_session_activation_report(source)

    if not source.consumption_invocation_ready:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            source.failure_reason or "read session is not invocation-ready"
        )

    session = source.read_session
    arguments = _bind_arguments(source)
    signature = tuple(
        session.callable_resolution.observed_signature
    )

    exact_signature_bound = bool(
        signature
        and signature
        == session.callable_resolution.expected_signature
        and tuple(argument.argument_name for argument in arguments)
        == signature
    )

    exact_artifact_path_bound = any(
        argument.value_kind == "authorized_artifact_path"
        and argument.canonical_value
        == session.artifact_read_receipt.resolved_path
        for argument in arguments
    )

    repository_root_bound = any(
        argument.value_kind == "repository_root"
        and Path(argument.canonical_value).resolve() == root
        for argument in arguments
    )

    persist_arguments = tuple(
        argument
        for argument in arguments
        if argument.argument_name.lower() == "persist"
    )
    persist_present = bool(persist_arguments)
    persist_value = (
        persist_arguments[0].canonical_value.lower() == "true"
        if persist_arguments
        else None
    )

    ready = bool(
        exact_signature_bound
        and exact_artifact_path_bound
        and repository_root_bound
        and all(
            argument.value_kind != "unsupported_unbound"
            for argument in arguments
        )
        and (not persist_present or persist_value is False)
    )

    manifest_body = {
        "invocation_id": _stable_hash(
            {
                "session_hash": session.session_hash,
                "module_name": (
                    session.callable_resolution.module_name
                ),
                "callable_name": (
                    session.callable_resolution.callable_name
                ),
                "arguments": arguments,
            }
        )[:24],
        "session_hash": session.session_hash,
        "module_name": session.callable_resolution.module_name,
        "callable_name": session.callable_resolution.callable_name,
        "callable_signature": signature,
        "invocation_arguments": arguments,
        "invocation_argument_count": len(arguments),
        "exact_signature_bound": exact_signature_bound,
        "exact_artifact_path_bound": exact_artifact_path_bound,
        "repository_root_bound": repository_root_bound,
        "persist_argument_present": persist_present,
        "persist_argument_value": persist_value,
        "invocation_ready": ready,
        "callable_invoked": False,
        "read_only": True,
    }
    manifest = OracleRealIntelligenceReadInvocationManifest(
        **manifest_body,
        manifest_hash=_stable_hash(manifest_body),
    )
    verify_invocation_manifest(manifest)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "read_session_report_hash": source.report_hash,
        "invocation_manifest": manifest,
        "exact_callable_identity_verified": bool(
            manifest.module_name
            == session.callable_resolution.module_name
            and manifest.callable_name
            == session.callable_resolution.callable_name
        ),
        "exact_callable_signature_verified": exact_signature_bound,
        "exact_argument_binding_verified": ready,
        "persistence_disabled": bool(
            not persist_present or persist_value is False
        ),
        "bounded_single_artifact_verified": (
            session.bounded_single_artifact
        ),
        "invocation_ready": ready,
        "invocation_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None if ready else "invocation_binding_incomplete",
    }
    report = OracleRealIntelligenceReadInvocationReadinessReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_read_invocation_readiness_report(report)
    return report


def verify_read_invocation_readiness_report(
    report: OracleRealIntelligenceReadInvocationReadinessReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "read invocation readiness report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "policy mismatch"
        )
    verify_invocation_manifest(report.invocation_manifest)
    if not report.read_only:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "read invocation readiness report is not read-only"
        )
    if (
        report.invocation_performed
        or report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "forbidden readiness capability enabled"
        )

    expected = bool(
        report.exact_callable_identity_verified
        and report.exact_callable_signature_verified
        and report.exact_argument_binding_verified
        and report.persistence_disabled
        and report.bounded_single_artifact_verified
        and report.invocation_manifest.invocation_ready
    )
    if report.invocation_ready != expected:
        raise OracleRealIntelligenceReadInvocationReadinessInvariantError(
            "read invocation readiness state mismatch"
        )
    return True
