from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_genuine_intelligence_artifact_admission import (
    AdmittedIntelligenceArtifact,
    OracleIntelligenceArtifactAdmissionInvariantError,
    discover_and_admit_intelligence_artifacts,
    load_admitted_artifact,
    verify_intelligence_artifact_admission,
)

SCHEMA_VERSION = "OIT-006"
ENGINE_ID = "OIT-006"
POLICY_ID = "oracle.genuine-intelligence-read-only-consumption.v1"

MAX_PREVIEW_RECORDS = 25
MAX_PREVIEW_DEPTH = 6
MAX_PREVIEW_STRING = 500


class OracleIntelligenceConsumptionInvariantError(
    OracleIntelligenceArtifactAdmissionInvariantError
):
    pass


@dataclass(frozen=True)
class IntelligenceArtifactView:
    artifact_index: int
    relative_path: str
    sha256: str
    byte_count: int
    modified_ns: int
    payload_kind: str
    record_count: int
    top_level_keys: tuple[str, ...]
    preview: Any
    preview_record_limit: int
    truncated: bool
    activation_lineage_verified: bool
    content_hash_verified: bool
    byte_count_verified: bool
    read_only: bool
    view_hash: str


@dataclass(frozen=True)
class OracleIntelligenceConsumptionReceipt:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    artifact_count: int
    artifacts: tuple[IntelligenceArtifactView, ...]
    admission_ready: bool
    terminal_consumption_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    receipt_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
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


def _safe_preview(
    value: Any,
    *,
    depth: int = 0,
) -> tuple[Any, bool]:
    if depth >= MAX_PREVIEW_DEPTH:
        return "<maximum preview depth reached>", True

    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        truncated = False
        items = sorted(value.items(), key=lambda item: str(item[0]))
        for index, (key, item) in enumerate(items):
            if index >= MAX_PREVIEW_RECORDS:
                truncated = True
                break
            preview, child_truncated = _safe_preview(
                item,
                depth=depth + 1,
            )
            output[str(key)] = preview
            truncated = truncated or child_truncated
        return output, truncated

    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        output = []
        truncated = len(value) > MAX_PREVIEW_RECORDS
        for item in list(value)[:MAX_PREVIEW_RECORDS]:
            preview, child_truncated = _safe_preview(
                item,
                depth=depth + 1,
            )
            output.append(preview)
            truncated = truncated or child_truncated
        return output, truncated

    if isinstance(value, str):
        if len(value) > MAX_PREVIEW_STRING:
            return value[:MAX_PREVIEW_STRING] + "...", True
        return value, False

    if value is None or isinstance(value, (int, float, bool)):
        return value, False

    rendered = repr(value)
    if len(rendered) > MAX_PREVIEW_STRING:
        return rendered[:MAX_PREVIEW_STRING] + "...", True
    return rendered, False


def _top_level_keys(payload: Any) -> tuple[str, ...]:
    if isinstance(payload, Mapping):
        return tuple(sorted(str(key) for key in payload))
    return ()


def _build_view(
    *,
    index: int,
    artifact: AdmittedIntelligenceArtifact,
    payload: Any,
) -> IntelligenceArtifactView:
    preview, truncated = _safe_preview(payload)
    body = {
        "artifact_index": index,
        "relative_path": artifact.relative_path,
        "sha256": artifact.sha256,
        "byte_count": artifact.byte_count,
        "modified_ns": artifact.modified_ns,
        "payload_kind": artifact.payload_kind,
        "record_count": artifact.record_count,
        "top_level_keys": _top_level_keys(payload),
        "preview": preview,
        "preview_record_limit": MAX_PREVIEW_RECORDS,
        "truncated": truncated,
        "activation_lineage_verified": artifact.activation_lineage_verified,
        "content_hash_verified": artifact.content_hash_verified,
        "byte_count_verified": artifact.byte_count_verified,
        "read_only": True,
    }
    return IntelligenceArtifactView(
        **body,
        view_hash=_stable_hash(body),
    )


def verify_intelligence_artifact_view(
    view: IntelligenceArtifactView,
) -> bool:
    body = asdict(view)
    supplied = body.pop("view_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceConsumptionInvariantError(
            "OIT-006 artifact view hash mismatch"
        )
    if not view.read_only:
        raise OracleIntelligenceConsumptionInvariantError(
            "artifact view is not read-only"
        )
    if not (
        view.activation_lineage_verified
        and view.content_hash_verified
        and view.byte_count_verified
    ):
        raise OracleIntelligenceConsumptionInvariantError(
            "artifact view lacks immutable OIT-005 admission"
        )
    if view.preview_record_limit != MAX_PREVIEW_RECORDS:
        raise OracleIntelligenceConsumptionInvariantError(
            "artifact preview limit mismatch"
        )
    return True


def consume_admitted_intelligence(
    *,
    repository_root: Path,
) -> OracleIntelligenceConsumptionReceipt:
    root = repository_root.resolve()
    admission = discover_and_admit_intelligence_artifacts(
        repository_root=root
    )
    verify_intelligence_artifact_admission(admission)

    views: list[IntelligenceArtifactView] = []
    failure = admission.failure_reason

    if admission.admission_ready:
        for index, artifact in enumerate(
            admission.admitted_artifacts,
            start=1,
        ):
            payload = load_admitted_artifact(
                repository_root=root,
                relative_path=artifact.relative_path,
            )
            view = _build_view(
                index=index,
                artifact=artifact,
                payload=payload,
            )
            verify_intelligence_artifact_view(view)
            views.append(view)

    ready = bool(
        admission.admission_ready
        and admission.terminal_consumption_ready
        and views
        and len(views) == admission.artifact_count
    )
    if not ready and failure is None:
        failure = "no OIT-005-admitted intelligence artifact is consumable"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "genuine_intelligence_consumption_ready"
            if ready
            else "genuine_intelligence_consumption_blocked"
        ),
        "repository_root": root.as_posix(),
        "artifact_count": len(views),
        "artifacts": tuple(views),
        "admission_ready": admission.admission_ready,
        "terminal_consumption_ready": ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    receipt = OracleIntelligenceConsumptionReceipt(
        **body,
        receipt_hash=_stable_hash(body),
    )
    verify_intelligence_consumption(receipt)
    return receipt


def verify_intelligence_consumption(
    receipt: OracleIntelligenceConsumptionReceipt,
) -> bool:
    body = asdict(receipt)
    supplied = body.pop("receipt_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceConsumptionInvariantError(
            "OIT-006 consumption receipt hash mismatch"
        )
    if not receipt.read_only:
        raise OracleIntelligenceConsumptionInvariantError(
            "OIT-006 is not read-only"
        )
    if receipt.analytics_execution_performed:
        raise OracleIntelligenceConsumptionInvariantError(
            "analytics execution occurred during consumption"
        )
    if receipt.database_access_performed:
        raise OracleIntelligenceConsumptionInvariantError(
            "database access occurred during consumption"
        )
    if receipt.publication_allowed or receipt.qseries_execution_allowed:
        raise OracleIntelligenceConsumptionInvariantError(
            "unsafe terminal consumption boundary"
        )
    for view in receipt.artifacts:
        verify_intelligence_artifact_view(view)
    if receipt.terminal_consumption_ready:
        if not receipt.admission_ready:
            raise OracleIntelligenceConsumptionInvariantError(
                "consumption ready without OIT-005 admission"
            )
        if not receipt.artifacts:
            raise OracleIntelligenceConsumptionInvariantError(
                "consumption ready without artifacts"
            )
        if receipt.artifact_count != len(receipt.artifacts):
            raise OracleIntelligenceConsumptionInvariantError(
                "artifact count mismatch"
            )
    return True


def select_intelligence_artifact(
    receipt: OracleIntelligenceConsumptionReceipt,
    *,
    selector: str,
) -> IntelligenceArtifactView:
    verify_intelligence_consumption(receipt)
    if not receipt.terminal_consumption_ready:
        raise OracleIntelligenceConsumptionInvariantError(
            receipt.failure_reason or "intelligence consumption is blocked"
        )

    normalized = selector.strip()
    if not normalized:
        raise OracleIntelligenceConsumptionInvariantError(
            "artifact selector is required"
        )

    if normalized.isdigit():
        index = int(normalized)
        for artifact in receipt.artifacts:
            if artifact.artifact_index == index:
                return artifact
        raise OracleIntelligenceConsumptionInvariantError(
            f"artifact index not found: {index}"
        )

    normalized_path = normalized.replace("\\", "/")
    for artifact in receipt.artifacts:
        if artifact.relative_path == normalized_path:
            return artifact
    raise OracleIntelligenceConsumptionInvariantError(
        "artifact path is not admitted for consumption"
    )


def intelligence_consumption_status_lines(
    receipt: OracleIntelligenceConsumptionReceipt,
) -> tuple[str, ...]:
    verify_intelligence_consumption(receipt)
    return (
        "ORACLE GENUINE INTELLIGENCE READ-ONLY CONSUMPTION",
        f"artifact_count: {receipt.artifact_count}",
        f"admission_ready: {str(receipt.admission_ready).lower()}",
        f"terminal_consumption_ready: {str(receipt.terminal_consumption_ready).lower()}",
        f"failure_reason: {receipt.failure_reason or 'none'}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    )


def intelligence_inventory_lines(
    receipt: OracleIntelligenceConsumptionReceipt,
) -> tuple[str, ...]:
    verify_intelligence_consumption(receipt)
    lines = [
        "ORACLE INTELLIGENCE ARTIFACT INVENTORY",
        f"artifact_count: {receipt.artifact_count}",
    ]
    if not receipt.artifacts:
        lines.append("artifacts: none")
    else:
        for artifact in receipt.artifacts:
            lines.extend((
                f"[{artifact.artifact_index}] {artifact.relative_path}",
                f"    sha256: {artifact.sha256}",
                f"    bytes: {artifact.byte_count}",
                f"    payload_kind: {artifact.payload_kind}",
                f"    record_count: {artifact.record_count}",
                f"    truncated_preview: {str(artifact.truncated).lower()}",
            ))
    lines.extend((
        f"terminal_consumption_ready: {str(receipt.terminal_consumption_ready).lower()}",
        "read_only: true",
    ))
    return tuple(lines)


def intelligence_artifact_lines(
    artifact: IntelligenceArtifactView,
) -> tuple[str, ...]:
    verify_intelligence_artifact_view(artifact)
    preview = json.dumps(
        _canonical(artifact.preview),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    return (
        "ORACLE INTELLIGENCE ARTIFACT READ",
        f"artifact_index: {artifact.artifact_index}",
        f"relative_path: {artifact.relative_path}",
        f"sha256: {artifact.sha256}",
        f"byte_count: {artifact.byte_count}",
        f"payload_kind: {artifact.payload_kind}",
        f"record_count: {artifact.record_count}",
        f"top_level_keys: {', '.join(artifact.top_level_keys) or 'none'}",
        f"preview_record_limit: {artifact.preview_record_limit}",
        f"preview_truncated: {str(artifact.truncated).lower()}",
        "preview:",
        preview,
        "activation_lineage_verified: true",
        "content_hash_verified: true",
        "byte_count_verified: true",
        "read_only: true",
    )
