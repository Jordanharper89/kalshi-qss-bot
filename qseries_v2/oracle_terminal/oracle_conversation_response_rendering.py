from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_final_intelligence_answer_assembly import (
    OracleFinalIntelligenceAnswerAssemblyInvariantError,
    OracleFinalIntelligenceAnswerAssemblyReport,
    OracleFinalIntelligenceAnswerPackage,
    verify_final_answer_package,
    verify_final_intelligence_answer_assembly_report,
)

SCHEMA_VERSION = "OIT-047"
ENGINE_ID = "OIT-047"
POLICY_ID = "oracle.conversation-response-rendering.v1"

MAX_RENDERED_LINES = 256


class OracleConversationResponseRenderingInvariantError(
    OracleFinalIntelligenceAnswerAssemblyInvariantError
):
    pass


@dataclass(frozen=True)
class OracleConversationRenderLine:
    render_index: int
    render_type: str
    text: str
    source_answer_line_hashes: tuple[str, ...]
    source_field_paths: tuple[str, ...]
    evidence_linked: bool
    render_line_hash: str


@dataclass(frozen=True)
class OracleConversationResponseFrame:
    frame_id: str
    frame_type: str
    title: str
    subtitle: str
    lines: tuple[OracleConversationRenderLine, ...]
    line_count: int
    source_package_hash: str
    source_answer_hash: str
    source_lineage_hash: str
    deterministic_ordering_applied: bool
    bounded_frame: bool
    terminal_display_ready: bool
    read_only: bool
    frame_hash: str


@dataclass(frozen=True)
class OracleConversationResponseRenderingReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    final_answer_assembly_report_hash: str
    response_frame: OracleConversationResponseFrame
    rendering_completed: bool
    interactive_pipeline_ready: bool
    exact_answer_text_preserved: bool
    unsupported_content_generated: bool
    persistent_memory_enabled: bool
    learning_update_performed: bool
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
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleConversationResponseRenderingInvariantError(
        "unsupported OIT-047 value type: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _render_type(answer_line_type: str) -> str:
    mapping = {
        "summary": "summary",
        "fact": "fact",
        "evidence": "evidence",
        "uncertainty": "uncertainty",
    }
    if answer_line_type not in mapping:
        raise OracleConversationResponseRenderingInvariantError(
            "unsupported answer line type"
        )
    return mapping[answer_line_type]


def _render_line(
    *,
    index: int,
    answer_line,
) -> OracleConversationRenderLine:
    body = {
        "render_index": index,
        "render_type": _render_type(answer_line.line_type),
        "text": answer_line.text,
        "source_answer_line_hashes": (
            answer_line.line_hash,
        ),
        "source_field_paths": (
            answer_line.source_field_paths
        ),
        "evidence_linked": answer_line.evidence_linked,
    }
    line = OracleConversationRenderLine(
        **body,
        render_line_hash=_stable_hash(body),
    )
    verify_conversation_render_line(line)
    return line


def verify_conversation_render_line(
    line: OracleConversationRenderLine,
) -> bool:
    body = asdict(line)
    supplied = body.pop("render_line_hash")

    if _stable_hash(body) != supplied:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 render line hash mismatch"
        )

    if line.render_index < 0:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 render line index invalid"
        )

    if line.render_type not in {
        "summary",
        "fact",
        "evidence",
        "uncertainty",
    }:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 render line type invalid"
        )

    if not line.text:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 render line text missing"
        )

    if not line.source_answer_line_hashes:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 answer-line lineage missing"
        )

    if not line.source_field_paths:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 field lineage missing"
        )

    if not line.evidence_linked:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 render line is not evidence-linked"
        )

    return True


def verify_conversation_response_frame(
    frame: OracleConversationResponseFrame,
) -> bool:
    body = asdict(frame)
    supplied = body.pop("frame_hash")

    if _stable_hash(body) != supplied:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 response frame hash mismatch"
        )

    if not frame.frame_id:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 frame ID missing"
        )

    if frame.frame_type != "oracle_conversation_response":
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 frame type invalid"
        )

    if not frame.title or not frame.subtitle:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 frame heading missing"
        )

    if frame.line_count != len(frame.lines):
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 frame line count mismatch"
        )

    for index, line in enumerate(frame.lines):
        verify_conversation_render_line(line)
        if line.render_index != index:
            raise OracleConversationResponseRenderingInvariantError(
                "OIT-047 render ordering mismatch"
            )

    if not frame.source_package_hash:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 package lineage missing"
        )

    if not frame.source_answer_hash:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 answer lineage missing"
        )

    if not frame.source_lineage_hash:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 final lineage missing"
        )

    if frame.bounded_frame != (
        frame.line_count <= MAX_RENDERED_LINES
    ):
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 bounded-frame state mismatch"
        )

    expected_ready = bool(
        frame.lines
        and frame.deterministic_ordering_applied
        and frame.bounded_frame
        and frame.read_only
        and all(line.evidence_linked for line in frame.lines)
    )

    if frame.terminal_display_ready != expected_ready:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 terminal display readiness mismatch"
        )

    return True


def build_conversation_response_rendering_report(
    repository_root: str | Path,
    *,
    final_answer_assembly_report: OracleFinalIntelligenceAnswerAssemblyReport,
) -> OracleConversationResponseRenderingReport:
    root = Path(repository_root).resolve()

    verify_final_intelligence_answer_assembly_report(
        final_answer_assembly_report
    )

    if not final_answer_assembly_report.conversation_rendering_ready:
        raise OracleConversationResponseRenderingInvariantError(
            final_answer_assembly_report.failure_reason
            or "OIT-046 report is not conversation-rendering ready"
        )

    package: OracleFinalIntelligenceAnswerPackage = (
        final_answer_assembly_report.final_answer_package
    )
    verify_final_answer_package(package)

    lines = tuple(
        _render_line(
            index=index,
            answer_line=answer_line,
        )
        for index, answer_line in enumerate(
            package.answer.answer_lines
        )
    )

    if len(lines) > MAX_RENDERED_LINES:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 rendered line limit exceeded"
        )

    preserved = tuple(
        line.text for line in lines
    ) == tuple(
        line.text for line in package.answer.answer_lines
    )

    frame_body = {
        "frame_id": _stable_hash(
            {
                "package_hash": package.package_hash,
                "answer_hash": package.answer.answer_hash,
                "render_lines": lines,
            }
        )[:24],
        "frame_type": "oracle_conversation_response",
        "title": "Oracle Intelligence Response",
        "subtitle": (
            "Read-only evidence-linked answer"
            + (
                " | follow-up context resolved"
                if package.follow_up_detected
                else ""
            )
        ),
        "lines": lines,
        "line_count": len(lines),
        "source_package_hash": package.package_hash,
        "source_answer_hash": package.answer.answer_hash,
        "source_lineage_hash": package.lineage.lineage_hash,
        "deterministic_ordering_applied": True,
        "bounded_frame": len(lines) <= MAX_RENDERED_LINES,
        "terminal_display_ready": bool(
            lines
            and preserved
            and all(line.evidence_linked for line in lines)
            and len(lines) <= MAX_RENDERED_LINES
        ),
        "read_only": True,
    }
    frame = OracleConversationResponseFrame(
        **frame_body,
        frame_hash=_stable_hash(frame_body),
    )
    verify_conversation_response_frame(frame)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "final_answer_assembly_report_hash": (
            final_answer_assembly_report.report_hash
        ),
        "response_frame": frame,
        "rendering_completed": frame.terminal_display_ready,
        "interactive_pipeline_ready": frame.terminal_display_ready,
        "exact_answer_text_preserved": preserved,
        "unsupported_content_generated": False,
        "persistent_memory_enabled": False,
        "learning_update_performed": False,
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
            if frame.terminal_display_ready and preserved
            else "OIT-047 conversation rendering failed"
        ),
    }
    report = OracleConversationResponseRenderingReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_conversation_response_rendering_report(report)
    return report


def verify_conversation_response_rendering_report(
    report: OracleConversationResponseRenderingReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 rendering report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 policy mismatch"
        )

    verify_conversation_response_frame(
        report.response_frame
    )

    if not report.read_only:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 report is not read-only"
        )

    if (
        report.unsupported_content_generated
        or report.persistent_memory_enabled
        or report.learning_update_performed
        or report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleConversationResponseRenderingInvariantError(
            "forbidden OIT-047 capability enabled"
        )

    expected = bool(
        report.response_frame.terminal_display_ready
        and report.exact_answer_text_preserved
        and report.response_frame.read_only
    )

    if report.rendering_completed != expected:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 rendering-completed state mismatch"
        )

    if report.interactive_pipeline_ready != expected:
        raise OracleConversationResponseRenderingInvariantError(
            "OIT-047 pipeline readiness mismatch"
        )

    return True
