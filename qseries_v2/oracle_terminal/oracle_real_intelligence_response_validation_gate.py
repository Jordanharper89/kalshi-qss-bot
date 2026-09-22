from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_authorized_real_intelligence_read_invocation_execution_gate import (
    OracleRealIntelligenceInvocationResult,
    OracleRealIntelligenceReadInvocationExecutionInvariantError,
    OracleRealIntelligenceReadInvocationExecutionReport,
    execute_authorized_real_intelligence_read_invocation,
    verify_read_invocation_execution_report,
)

SCHEMA_VERSION = "OIT-038"
ENGINE_ID = "OIT-038"
POLICY_ID = "oracle.real-intelligence-response-validation.v1"

MAX_DEPTH = 12
MAX_CONTAINER_ITEMS = 10000
MAX_STRING_LENGTH = 1_000_000


class OracleRealIntelligenceResponseValidationInvariantError(
    OracleRealIntelligenceReadInvocationExecutionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleRealIntelligenceStructuralFinding:
    finding_code: str
    severity: str
    location: str
    message: str
    blocking: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceResponseShape:
    root_type: str
    root_mapping: bool
    root_sequence: bool
    root_scalar: bool
    maximum_depth: int
    mapping_count: int
    sequence_count: int
    scalar_count: int
    null_count: int
    string_count: int
    number_count: int
    boolean_count: int
    total_node_count: int
    total_key_count: int
    duplicate_key_risk_detected: bool
    unsupported_type_detected: bool
    nonfinite_number_detected: bool
    oversized_value_detected: bool
    shape_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceResponseValidationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    execution_report_hash: str
    invocation_result_hash: str
    response_shape: OracleRealIntelligenceResponseShape
    findings: tuple[OracleRealIntelligenceStructuralFinding, ...]
    finding_count: int
    blocking_finding_count: int
    structurally_valid: bool
    deterministic_replay_ready: bool
    normalization_ready: bool
    source_result_preserved: bool
    response_modified: bool
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
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _finding(
    code: str,
    severity: str,
    location: str,
    message: str,
    *,
    blocking: bool,
) -> OracleRealIntelligenceStructuralFinding:
    body = {
        "finding_code": code,
        "severity": severity,
        "location": location,
        "message": message,
        "blocking": blocking,
    }
    finding = OracleRealIntelligenceStructuralFinding(
        **body,
        finding_hash=_stable_hash(body),
    )
    verify_structural_finding(finding)
    return finding


def _inspect_structure(value: Any) -> tuple[OracleRealIntelligenceResponseShape, tuple[OracleRealIntelligenceStructuralFinding, ...]]:
    counts = {
        "maximum_depth": 0,
        "mapping_count": 0,
        "sequence_count": 0,
        "scalar_count": 0,
        "null_count": 0,
        "string_count": 0,
        "number_count": 0,
        "boolean_count": 0,
        "total_node_count": 0,
        "total_key_count": 0,
    }
    findings: list[OracleRealIntelligenceStructuralFinding] = []
    unsupported = False
    nonfinite = False
    oversized = False

    def walk(node: Any, location: str, depth: int) -> None:
        nonlocal unsupported, nonfinite, oversized

        counts["maximum_depth"] = max(counts["maximum_depth"], depth)
        counts["total_node_count"] += 1

        if depth > MAX_DEPTH:
            findings.append(
                _finding(
                    "maximum_depth_exceeded",
                    "error",
                    location,
                    f"Response depth exceeded {MAX_DEPTH}.",
                    blocking=True,
                )
            )
            oversized = True
            return

        if isinstance(node, Mapping):
            counts["mapping_count"] += 1
            counts["total_key_count"] += len(node)
            if len(node) > MAX_CONTAINER_ITEMS:
                findings.append(
                    _finding(
                        "mapping_item_limit_exceeded",
                        "error",
                        location,
                        f"Mapping contains more than {MAX_CONTAINER_ITEMS} items.",
                        blocking=True,
                    )
                )
                oversized = True

            seen_keys: set[str] = set()
            for key, item in node.items():
                key_text = str(key)
                if key_text in seen_keys:
                    findings.append(
                        _finding(
                            "duplicate_canonical_key",
                            "error",
                            location,
                            f"Duplicate canonical key detected: {key_text}",
                            blocking=True,
                        )
                    )
                seen_keys.add(key_text)
                walk(item, f"{location}.{key_text}", depth + 1)
            return

        if isinstance(node, (list, tuple)):
            counts["sequence_count"] += 1
            if len(node) > MAX_CONTAINER_ITEMS:
                findings.append(
                    _finding(
                        "sequence_item_limit_exceeded",
                        "error",
                        location,
                        f"Sequence contains more than {MAX_CONTAINER_ITEMS} items.",
                        blocking=True,
                    )
                )
                oversized = True
            for index, item in enumerate(node):
                walk(item, f"{location}[{index}]", depth + 1)
            return

        counts["scalar_count"] += 1

        if node is None:
            counts["null_count"] += 1
            return

        if isinstance(node, bool):
            counts["boolean_count"] += 1
            return

        if isinstance(node, str):
            counts["string_count"] += 1
            if len(node) > MAX_STRING_LENGTH:
                findings.append(
                    _finding(
                        "string_length_limit_exceeded",
                        "error",
                        location,
                        f"String exceeds {MAX_STRING_LENGTH} characters.",
                        blocking=True,
                    )
                )
                oversized = True
            return

        if isinstance(node, (int, float)):
            counts["number_count"] += 1
            if isinstance(node, float):
                if node != node or node in (float("inf"), float("-inf")):
                    findings.append(
                        _finding(
                            "nonfinite_number",
                            "error",
                            location,
                            "NaN and infinite numbers are not permitted.",
                            blocking=True,
                        )
                    )
                    nonfinite = True
            return

        unsupported = True
        findings.append(
            _finding(
                "unsupported_response_type",
                "error",
                location,
                f"Unsupported response type: {type(node).__module__}.{type(node).__qualname__}",
                blocking=True,
            )
        )

    walk(value, "$", 0)

    root_mapping = isinstance(value, Mapping)
    root_sequence = isinstance(value, (list, tuple))
    root_scalar = not root_mapping and not root_sequence

    duplicate_key_risk = any(
        item.finding_code == "duplicate_canonical_key"
        for item in findings
    )

    body = {
        "root_type": f"{type(value).__module__}.{type(value).__qualname__}",
        "root_mapping": root_mapping,
        "root_sequence": root_sequence,
        "root_scalar": root_scalar,
        "maximum_depth": counts["maximum_depth"],
        "mapping_count": counts["mapping_count"],
        "sequence_count": counts["sequence_count"],
        "scalar_count": counts["scalar_count"],
        "null_count": counts["null_count"],
        "string_count": counts["string_count"],
        "number_count": counts["number_count"],
        "boolean_count": counts["boolean_count"],
        "total_node_count": counts["total_node_count"],
        "total_key_count": counts["total_key_count"],
        "duplicate_key_risk_detected": duplicate_key_risk,
        "unsupported_type_detected": unsupported,
        "nonfinite_number_detected": nonfinite,
        "oversized_value_detected": oversized,
    }
    shape = OracleRealIntelligenceResponseShape(
        **body,
        shape_hash=_stable_hash(body),
    )
    verify_response_shape(shape)
    return shape, tuple(findings)


def verify_structural_finding(
    finding: OracleRealIntelligenceStructuralFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "structural finding hash mismatch"
        )
    if not finding.finding_code or not finding.location or not finding.message:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "structural finding incomplete"
        )
    if finding.severity not in {"info", "warning", "error"}:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "structural finding severity invalid"
        )
    return True


def verify_response_shape(
    shape: OracleRealIntelligenceResponseShape,
) -> bool:
    body = asdict(shape)
    supplied = body.pop("shape_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "response shape hash mismatch"
        )
    if sum((shape.root_mapping, shape.root_sequence, shape.root_scalar)) != 1:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "response root classification invalid"
        )
    if shape.total_node_count < 1:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "response node count invalid"
        )
    return True


def build_real_intelligence_response_validation_report(
    repository_root: str | Path,
    *,
    execution_report: OracleRealIntelligenceReadInvocationExecutionReport | None = None,
) -> OracleRealIntelligenceResponseValidationReport:
    root = Path(repository_root).resolve()
    source = execution_report
    if source is None:
        source = execute_authorized_real_intelligence_read_invocation(root)
    verify_read_invocation_execution_report(source)

    if not source.execution_succeeded:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            source.failure_reason or "read invocation execution did not succeed"
        )

    invocation_result: OracleRealIntelligenceInvocationResult = (
        source.execution_receipt.invocation_result
    )
    original_result_hash = invocation_result.result_hash
    original_canonical_hash = _stable_hash(
        invocation_result.canonical_result
    )

    shape, findings = _inspect_structure(
        invocation_result.canonical_result
    )

    blocking_count = sum(item.blocking for item in findings)
    structurally_valid = blocking_count == 0

    source_preserved = bool(
        invocation_result.result_hash == original_result_hash
        and _stable_hash(invocation_result.canonical_result)
        == original_canonical_hash
    )

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "execution_report_hash": source.report_hash,
        "invocation_result_hash": invocation_result.result_hash,
        "response_shape": shape,
        "findings": findings,
        "finding_count": len(findings),
        "blocking_finding_count": blocking_count,
        "structurally_valid": structurally_valid,
        "deterministic_replay_ready": structurally_valid,
        "normalization_ready": bool(
            structurally_valid and source_preserved
        ),
        "source_result_preserved": source_preserved,
        "response_modified": False,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "runtime_artifact_created": False,
        "runtime_artifact_modified": False,
        "networking_performed": False,
        "publication_allowed": False,
        "action_authorization_allowed": False,
        "qseries_execution_allowed": False,
        "read_only": True,
        "failure_reason": (
            None
            if structurally_valid and source_preserved
            else "response_structure_not_certified"
        ),
    }
    report = OracleRealIntelligenceResponseValidationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_real_intelligence_response_validation_report(report)
    return report


def verify_real_intelligence_response_validation_report(
    report: OracleRealIntelligenceResponseValidationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "response validation report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "policy mismatch"
        )

    verify_response_shape(report.response_shape)
    for finding in report.findings:
        verify_structural_finding(finding)

    if report.finding_count != len(report.findings):
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "finding count mismatch"
        )
    if report.blocking_finding_count != sum(
        item.blocking for item in report.findings
    ):
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "blocking finding count mismatch"
        )
    if report.structurally_valid != (
        report.blocking_finding_count == 0
    ):
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "structural validity mismatch"
        )
    if report.normalization_ready != bool(
        report.structurally_valid
        and report.deterministic_replay_ready
        and report.source_result_preserved
    ):
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "normalization readiness mismatch"
        )
    if not report.read_only or report.response_modified:
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "response validation mutated source data"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceResponseValidationInvariantError(
            "forbidden validation capability enabled"
        )
    return True
