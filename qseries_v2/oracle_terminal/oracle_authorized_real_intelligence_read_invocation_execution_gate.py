from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_authorized_real_intelligence_read_invocation_readiness_gate import (
    OracleRealIntelligenceReadInvocationReadinessInvariantError,
    OracleRealIntelligenceReadInvocationReadinessReport,
    build_authorized_read_invocation_readiness_report,
    verify_read_invocation_readiness_report,
)

SCHEMA_VERSION = "OIT-037"
ENGINE_ID = "OIT-037"
POLICY_ID = "oracle.authorized-real-intelligence-read-invocation-execution.v1"


class OracleRealIntelligenceReadInvocationExecutionInvariantError(
    OracleRealIntelligenceReadInvocationReadinessInvariantError
):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceInvocationResult:
    result_type: str
    canonical_result: Any
    result_hash: str
    result_available: bool
    result_none: bool
    read_only: bool
    verification_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceInvocationExecutionReceipt:
    invocation_id: str
    readiness_report_hash: str
    manifest_hash: str
    module_name: str
    callable_name: str
    invocation_argument_names: tuple[str, ...]
    callable_invocation_count: int
    callable_invoked: bool
    invocation_completed: bool
    artifact_sha256_before: str
    artifact_sha256_after: str
    artifact_byte_count_before: int
    artifact_byte_count_after: int
    artifact_mtime_ns_before: int
    artifact_mtime_ns_after: int
    artifact_unchanged: bool
    invocation_result: OracleRealIntelligenceInvocationResult
    persistence_performed: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    runtime_artifact_created: bool
    runtime_artifact_modified: bool
    networking_performed: bool
    publication_allowed: bool
    action_authorization_allowed: bool
    qseries_execution_allowed: bool
    read_only: bool
    receipt_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceReadInvocationExecutionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    readiness_report_hash: str
    execution_receipt: OracleRealIntelligenceInvocationExecutionReceipt
    exact_callable_invoked: bool
    exact_arguments_consumed: bool
    exactly_one_invocation_performed: bool
    artifact_identity_preserved: bool
    bounded_read_result_available: bool
    execution_succeeded: bool
    persistence_performed: bool
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
    if isinstance(value, set):
        return sorted(_canonical(item) for item in value)
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, bytes):
        return {
            "__bytes_sha256__": hashlib.sha256(value).hexdigest(),
            "__bytes_count__": len(value),
        }
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "to_dict") and callable(value.to_dict):
        try:
            return _canonical(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return _canonical(vars(value))
    return {
        "__type__": f"{type(value).__module__}.{type(value).__qualname__}",
        "__repr__": repr(value),
    }


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _argument_value(argument) -> Any:
    if argument.value_kind == "repository_root":
        return Path(argument.canonical_value)
    if argument.value_kind == "authorized_artifact_path":
        return Path(argument.canonical_value)
    if argument.value_kind == "boolean":
        lowered = argument.canonical_value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "unsupported boolean invocation value"
        )
    raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
        f"unsupported invocation argument kind: {argument.value_kind}"
    )


def _build_result(value: Any) -> OracleRealIntelligenceInvocationResult:
    canonical = _canonical(value)
    body = {
        "result_type": (
            f"{type(value).__module__}.{type(value).__qualname__}"
        ),
        "canonical_result": canonical,
        "result_hash": _stable_hash(canonical),
        "result_available": True,
        "result_none": value is None,
        "read_only": True,
    }
    result = OracleRealIntelligenceInvocationResult(
        **body,
        verification_hash=_stable_hash(body),
    )
    verify_invocation_result(result)
    return result


def verify_invocation_result(
    result: OracleRealIntelligenceInvocationResult,
) -> bool:
    body = asdict(result)
    supplied = body.pop("verification_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "invocation result verification hash mismatch"
        )
    if not result.read_only:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "invocation result is not read-only"
        )
    if not result.result_available:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "invocation result unavailable"
        )
    if result.result_hash != _stable_hash(result.canonical_result):
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "invocation result hash mismatch"
        )
    return True


def execute_authorized_real_intelligence_read_invocation(
    repository_root: str | Path,
    *,
    readiness_report: OracleRealIntelligenceReadInvocationReadinessReport | None = None,
) -> OracleRealIntelligenceReadInvocationExecutionReport:
    root = Path(repository_root).resolve()
    source = readiness_report
    if source is None:
        source = build_authorized_read_invocation_readiness_report(root)
    verify_read_invocation_readiness_report(source)

    if not source.invocation_ready:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            source.failure_reason or "invocation is not ready"
        )

    manifest = source.invocation_manifest
    module = importlib.import_module(manifest.module_name)
    callable_object = getattr(module, manifest.callable_name)
    if not callable(callable_object):
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "authorized callable did not resolve"
        )

    kwargs = {
        argument.argument_name: _argument_value(argument)
        for argument in manifest.invocation_arguments
    }
    if tuple(kwargs) != tuple(manifest.callable_signature):
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "bound invocation arguments do not match callable signature"
        )

    artifact_argument = next(
        (
            argument
            for argument in manifest.invocation_arguments
            if argument.value_kind == "authorized_artifact_path"
        ),
        None,
    )
    if artifact_argument is None:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "authorized artifact-path argument missing"
        )

    artifact_path = Path(artifact_argument.canonical_value).resolve()
    before_stat = artifact_path.stat()
    before_sha = _sha256_file(artifact_path)

    result_value = callable_object(**kwargs)

    after_stat = artifact_path.stat()
    after_sha = _sha256_file(artifact_path)

    unchanged = bool(
        before_sha == after_sha
        and before_stat.st_size == after_stat.st_size
        and before_stat.st_mtime_ns == after_stat.st_mtime_ns
    )
    if not unchanged:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "authorized artifact changed during read invocation"
        )

    result = _build_result(result_value)

    receipt_body = {
        "invocation_id": manifest.invocation_id,
        "readiness_report_hash": source.report_hash,
        "manifest_hash": manifest.manifest_hash,
        "module_name": manifest.module_name,
        "callable_name": manifest.callable_name,
        "invocation_argument_names": tuple(kwargs),
        "callable_invocation_count": 1,
        "callable_invoked": True,
        "invocation_completed": True,
        "artifact_sha256_before": before_sha,
        "artifact_sha256_after": after_sha,
        "artifact_byte_count_before": before_stat.st_size,
        "artifact_byte_count_after": after_stat.st_size,
        "artifact_mtime_ns_before": before_stat.st_mtime_ns,
        "artifact_mtime_ns_after": after_stat.st_mtime_ns,
        "artifact_unchanged": unchanged,
        "invocation_result": result,
        "persistence_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
    }
    receipt = OracleRealIntelligenceInvocationExecutionReceipt(
        **receipt_body,
        receipt_hash=_stable_hash(receipt_body),
    )
    verify_execution_receipt(receipt)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "readiness_report_hash": source.report_hash,
        "execution_receipt": receipt,
        "exact_callable_invoked": bool(
            receipt.module_name == manifest.module_name
            and receipt.callable_name == manifest.callable_name
        ),
        "exact_arguments_consumed": bool(
            receipt.invocation_argument_names
            == tuple(manifest.callable_signature)
        ),
        "exactly_one_invocation_performed": (
            receipt.callable_invocation_count == 1
        ),
        "artifact_identity_preserved": receipt.artifact_unchanged,
        "bounded_read_result_available": (
            receipt.invocation_result.result_available
        ),
        "execution_succeeded": bool(
            receipt.invocation_completed
            and receipt.callable_invocation_count == 1
            and receipt.artifact_unchanged
            and receipt.invocation_result.result_available
        ),
        "persistence_performed": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": None,
    }
    report = OracleRealIntelligenceReadInvocationExecutionReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_read_invocation_execution_report(report)
    return report


def verify_execution_receipt(
    receipt: OracleRealIntelligenceInvocationExecutionReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "execution receipt hash mismatch"
        )
    verify_invocation_result(receipt.invocation_result)
    if not receipt.read_only:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "execution receipt is not read-only"
        )
    if receipt.callable_invocation_count != 1:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "read invocation count is not exactly one"
        )
    if not receipt.callable_invoked or not receipt.invocation_completed:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "read invocation did not complete"
        )
    expected_unchanged = bool(
        receipt.artifact_sha256_before == receipt.artifact_sha256_after
        and receipt.artifact_byte_count_before
        == receipt.artifact_byte_count_after
        and receipt.artifact_mtime_ns_before
        == receipt.artifact_mtime_ns_after
    )
    if receipt.artifact_unchanged != expected_unchanged:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "artifact preservation state mismatch"
        )
    if (
        receipt.persistence_performed
        or receipt.analytics_execution_performed
        or receipt.database_access_performed
        or receipt.runtime_artifact_created
        or receipt.runtime_artifact_modified
        or receipt.networking_performed
        or receipt.publication_allowed
        or receipt.action_authorization_allowed
        or receipt.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "forbidden execution capability enabled"
        )
    return True


def verify_read_invocation_execution_report(
    report: OracleRealIntelligenceReadInvocationExecutionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "read invocation execution report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "policy mismatch"
        )
    verify_execution_receipt(report.execution_receipt)
    if not report.read_only:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "execution report is not read-only"
        )
    if (
        report.persistence_performed
        or report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "forbidden report capability enabled"
        )
    expected = bool(
        report.exact_callable_invoked
        and report.exact_arguments_consumed
        and report.exactly_one_invocation_performed
        and report.artifact_identity_preserved
        and report.bounded_read_result_available
        and report.execution_receipt.invocation_completed
    )
    if report.execution_succeeded != expected:
        raise OracleRealIntelligenceReadInvocationExecutionInvariantError(
            "read invocation execution state mismatch"
        )
    return True
