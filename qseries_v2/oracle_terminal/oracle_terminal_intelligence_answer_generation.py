from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_natural_language_intelligence_response_projection import (
    OracleNaturalLanguageIntelligenceProjectionReport,
    OracleProjectedIntelligenceField,
    OracleIntelligenceResponseProjectionInvariantError,
    verify_natural_language_intelligence_projection_report,
)

SCHEMA_VERSION = "OIT-042"
ENGINE_ID = "OIT-042"
POLICY_ID = "oracle.terminal-intelligence-answer-generation.v1"

MAX_ANSWER_LINES = 128


class OracleTerminalIntelligenceAnswerInvariantError(
    OracleIntelligenceResponseProjectionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTerminalIntelligenceAnswerLine:
    line_index: int
    line_type: str
    text: str
    source_field_paths: tuple[str, ...]
    source_field_hashes: tuple[str, ...]
    evidence_linked: bool
    line_hash: str


@dataclass(frozen=True)
class OracleTerminalIntelligenceAnswer:
    answer_id: str
    source_projection_hash: str
    source_projection_report_hash: str
    query: str
    answer_lines: tuple[OracleTerminalIntelligenceAnswerLine, ...]
    answer_line_count: int
    evidence_line_count: int
    summary_line_count: int
    uncertainty_line_count: int
    all_claims_evidence_linked: bool
    deterministic_ordering_applied: bool
    bounded_answer: bool
    answer_ready: bool
    read_only: bool
    answer_hash: str


@dataclass(frozen=True)
class OracleTerminalIntelligenceAnswerGenerationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    projection_report_hash: str
    answer: OracleTerminalIntelligenceAnswer
    answer_generated: bool
    answer_render_ready: bool
    unsupported_claims_generated: bool
    free_form_generation_used: bool
    multi_turn_memory_enabled: bool
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
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleTerminalIntelligenceAnswerInvariantError(
        f"unsupported answer value type: "
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


def _format_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, (str, int)):
        return str(value)
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _answer_line(
    *,
    index: int,
    line_type: str,
    text: str,
    fields: tuple[OracleProjectedIntelligenceField, ...],
) -> OracleTerminalIntelligenceAnswerLine:
    body = {
        "line_index": index,
        "line_type": line_type,
        "text": text,
        "source_field_paths": tuple(
            field.source_field_path for field in fields
        ),
        "source_field_hashes": tuple(
            field.projected_field_hash for field in fields
        ),
        "evidence_linked": bool(fields),
    }
    line = OracleTerminalIntelligenceAnswerLine(
        **body,
        line_hash=_stable_hash(body),
    )
    verify_answer_line(line)
    return line


def _classify_field(field: OracleProjectedIntelligenceField) -> str:
    lowered = (
        field.context_key.lower()
        + " "
        + field.source_field_path.lower()
    )
    if any(token in lowered for token in ("evidence", "source", "confidence")):
        return "evidence"
    if any(token in lowered for token in ("uncertainty", "risk", "contradiction")):
        return "uncertainty"
    return "fact"


def _build_lines(
    report: OracleNaturalLanguageIntelligenceProjectionReport,
) -> tuple[OracleTerminalIntelligenceAnswerLine, ...]:
    projection = report.projection
    fields = projection.projected_fields
    lines: list[OracleTerminalIntelligenceAnswerLine] = []

    summary_text = (
        f"Oracle found {len(fields)} certified context field"
        f"{'' if len(fields) == 1 else 's'} relevant to the query."
    )
    lines.append(
        _answer_line(
            index=0,
            line_type="summary",
            text=summary_text,
            fields=tuple(fields),
        )
    )

    ordered = sorted(
        fields,
        key=lambda field: (
            -field.match_score,
            field.source_field_path,
            field.projected_field_hash,
        ),
    )

    for field in ordered:
        line_type = _classify_field(field)
        text = (
            f"{field.context_key}: "
            f"{_format_value(field.canonical_value)}"
        )
        lines.append(
            _answer_line(
                index=len(lines),
                line_type=line_type,
                text=text,
                fields=(field,),
            )
        )

    if not any(line.line_type == "uncertainty" for line in lines):
        uncertainty_fields = tuple(
            field
            for field in ordered
            if any(
                token in (
                    field.context_key.lower()
                    + " "
                    + field.source_field_path.lower()
                )
                for token in (
                    "confidence",
                    "probability",
                    "risk",
                    "uncertainty",
                )
            )
        )
        if uncertainty_fields:
            lines.append(
                _answer_line(
                    index=len(lines),
                    line_type="uncertainty",
                    text=(
                        "Uncertainty remains bounded by the certified "
                        "probability and confidence fields shown above."
                    ),
                    fields=uncertainty_fields,
                )
            )

    if len(lines) > MAX_ANSWER_LINES:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line limit exceeded"
        )

    return tuple(lines)


def verify_answer_line(
    line: OracleTerminalIntelligenceAnswerLine,
) -> bool:
    body = asdict(line)
    supplied = body.pop("line_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line hash mismatch"
        )
    if line.line_index < 0:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line index invalid"
        )
    if line.line_type not in {
        "summary",
        "fact",
        "evidence",
        "uncertainty",
    }:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line type invalid"
        )
    if not line.text:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line text missing"
        )
    if len(line.source_field_paths) != len(line.source_field_hashes):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line lineage count mismatch"
        )
    if line.evidence_linked != bool(line.source_field_paths):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line evidence state mismatch"
        )
    return True


def verify_terminal_intelligence_answer(
    answer: OracleTerminalIntelligenceAnswer,
) -> bool:
    body = asdict(answer)
    supplied = body.pop("answer_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer hash mismatch"
        )
    if answer.answer_line_count != len(answer.answer_lines):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer line count mismatch"
        )
    for index, line in enumerate(answer.answer_lines):
        verify_answer_line(line)
        if line.line_index != index:
            raise OracleTerminalIntelligenceAnswerInvariantError(
                "answer line ordering mismatch"
            )
    if answer.evidence_line_count != sum(
        line.line_type == "evidence"
        for line in answer.answer_lines
    ):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "evidence line count mismatch"
        )
    if answer.summary_line_count != sum(
        line.line_type == "summary"
        for line in answer.answer_lines
    ):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "summary line count mismatch"
        )
    if answer.uncertainty_line_count != sum(
        line.line_type == "uncertainty"
        for line in answer.answer_lines
    ):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "uncertainty line count mismatch"
        )
    if answer.all_claims_evidence_linked != all(
        line.evidence_linked
        for line in answer.answer_lines
    ):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer evidence-link state mismatch"
        )
    if answer.bounded_answer != (
        answer.answer_line_count <= MAX_ANSWER_LINES
    ):
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "bounded answer state mismatch"
        )
    expected_ready = bool(
        answer.answer_lines
        and answer.all_claims_evidence_linked
        and answer.deterministic_ordering_applied
        and answer.bounded_answer
        and answer.read_only
    )
    if answer.answer_ready != expected_ready:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer readiness mismatch"
        )
    return True


def build_terminal_intelligence_answer_generation_report(
    repository_root: str | Path,
    *,
    projection_report: OracleNaturalLanguageIntelligenceProjectionReport,
) -> OracleTerminalIntelligenceAnswerGenerationReport:
    root = Path(repository_root).resolve()
    verify_natural_language_intelligence_projection_report(
        projection_report
    )

    if not projection_report.answer_generation_ready:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            projection_report.failure_reason
            or "projection is not answer-generation ready"
        )

    projection = projection_report.projection
    lines = _build_lines(projection_report)

    answer_body = {
        "answer_id": _stable_hash(
            {
                "projection_hash": projection.projection_hash,
                "answer_lines": lines,
            }
        )[:24],
        "source_projection_hash": projection.projection_hash,
        "source_projection_report_hash": projection_report.report_hash,
        "query": projection.query_intent.normalized_query,
        "answer_lines": lines,
        "answer_line_count": len(lines),
        "evidence_line_count": sum(
            line.line_type == "evidence"
            for line in lines
        ),
        "summary_line_count": sum(
            line.line_type == "summary"
            for line in lines
        ),
        "uncertainty_line_count": sum(
            line.line_type == "uncertainty"
            for line in lines
        ),
        "all_claims_evidence_linked": all(
            line.evidence_linked for line in lines
        ),
        "deterministic_ordering_applied": True,
        "bounded_answer": len(lines) <= MAX_ANSWER_LINES,
        "answer_ready": bool(
            lines
            and all(line.evidence_linked for line in lines)
            and len(lines) <= MAX_ANSWER_LINES
        ),
        "read_only": True,
    }
    answer = OracleTerminalIntelligenceAnswer(
        **answer_body,
        answer_hash=_stable_hash(answer_body),
    )
    verify_terminal_intelligence_answer(answer)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "projection_report_hash": projection_report.report_hash,
        "answer": answer,
        "answer_generated": answer.answer_ready,
        "answer_render_ready": answer.answer_ready,
        "unsupported_claims_generated": False,
        "free_form_generation_used": False,
        "multi_turn_memory_enabled": False,
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
            None if answer.answer_ready
            else "answer_generation_failed"
        ),
    }
    report = OracleTerminalIntelligenceAnswerGenerationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_terminal_intelligence_answer_generation_report(
        report
    )
    return report


def verify_terminal_intelligence_answer_generation_report(
    report: OracleTerminalIntelligenceAnswerGenerationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer generation report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer policy mismatch"
        )

    verify_terminal_intelligence_answer(report.answer)

    if not report.read_only:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer generation report is not read-only"
        )

    if (
        report.unsupported_claims_generated
        or report.free_form_generation_used
        or report.multi_turn_memory_enabled
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
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "forbidden answer capability enabled"
        )

    expected = bool(
        report.answer.answer_ready
        and report.answer.all_claims_evidence_linked
        and report.answer.bounded_answer
    )
    if report.answer_generated != expected:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer generated state mismatch"
        )
    if report.answer_render_ready != expected:
        raise OracleTerminalIntelligenceAnswerInvariantError(
            "answer render readiness mismatch"
        )
    return True
