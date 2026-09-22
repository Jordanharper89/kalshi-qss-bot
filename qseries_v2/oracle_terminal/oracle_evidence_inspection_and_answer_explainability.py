from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_grounded_intelligence_answer_composition import (
    OracleGroundedAnswerInvariantError,
    OracleGroundedEvidenceItem,
    OracleGroundedIntelligenceAnswer,
    compose_grounded_intelligence_answer,
    verify_grounded_evidence_item,
    verify_grounded_intelligence_answer,
)

SCHEMA_VERSION = "OIT-010"
ENGINE_ID = "OIT-010"
POLICY_ID = "oracle.evidence-inspection-and-answer-explainability.v1"

MAX_SUPPORT_VALUES = 64
MAX_VALUE_LENGTH = 500


class OracleEvidenceExplainabilityInvariantError(
    OracleGroundedAnswerInvariantError
):
    pass


@dataclass(frozen=True)
class OracleEvidenceSupport:
    support_index: int
    evidence_index: int
    record_id: str
    matched_term: str
    support_path: str
    support_value: Any
    support_kind: str
    read_only: bool
    support_hash: str


@dataclass(frozen=True)
class OracleEvidenceInspection:
    evidence_index: int
    record_id: str
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    query_plan_hash: str
    evidence_hash: str
    matched_terms: tuple[str, ...]
    matched_required_terms: tuple[str, ...]
    matched_field_hints: tuple[str, ...]
    selected_fields: tuple[tuple[str, Any], ...]
    supports: tuple[OracleEvidenceSupport, ...]
    support_count: int
    explanation_text: str
    lineage_complete: bool
    read_only: bool
    inspection_hash: str


@dataclass(frozen=True)
class OracleAnswerExplainabilityReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    answer_text: str
    answer_hash: str
    query_plan_hash: str
    query_result_hash: str
    inspections: tuple[OracleEvidenceInspection, ...]
    evidence_count: int
    explained_evidence_count: int
    answer_grounded: bool
    explainability_ready: bool
    uncertainty_statement: str
    limitation_statement: str
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    report_hash: str


def _canonical(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
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


def _truncate(value: Any) -> Any:
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return value[:MAX_VALUE_LENGTH] + "..."
    return _canonical(value)


def _flatten_values(
    value: Any,
    *,
    prefix: str = "",
    depth: int = 0,
) -> tuple[tuple[str, Any], ...]:
    if depth >= 8:
        return ((prefix or "$", "<maximum depth reached>"),)

    output: list[tuple[str, Any]] = []

    if isinstance(value, Mapping):
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            path = f"{prefix}.{key}" if prefix else str(key)
            output.extend(
                _flatten_values(child, prefix=path, depth=depth + 1)
            )
            if len(output) >= MAX_SUPPORT_VALUES:
                break
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(list(value)[:MAX_SUPPORT_VALUES]):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            output.extend(
                _flatten_values(child, prefix=path, depth=depth + 1)
            )
            if len(output) >= MAX_SUPPORT_VALUES:
                break
    else:
        output.append((prefix or "$", _truncate(value)))

    return tuple(output[:MAX_SUPPORT_VALUES])


def _contains(value: Any, term: str) -> bool:
    if isinstance(value, (dict, list, tuple)):
        rendered = json.dumps(
            _canonical(value),
            sort_keys=True,
            ensure_ascii=False,
        )
    else:
        rendered = str(value)
    return term.lower() in rendered.lower()


def _support_kind(path: str, value: Any, term: str) -> str:
    leaf = path.rsplit(".", 1)[-1].lower()
    normalized = term.lower()
    if leaf == normalized and str(value).lower() == normalized:
        return "exact-field-and-value"
    if leaf == normalized:
        return "exact-field"
    if normalized in leaf:
        return "field-name"
    if str(value).lower() == normalized:
        return "exact-value"
    return "value"


def _build_supports(
    evidence: OracleGroundedEvidenceItem,
) -> tuple[OracleEvidenceSupport, ...]:
    flattened = _flatten_values(dict(evidence.selected_fields))
    supports: list[OracleEvidenceSupport] = []
    support_index = 1

    for term in evidence.matched_terms:
        for path, value in flattened:
            leaf = path.rsplit(".", 1)[-1]
            if term.lower() in leaf.lower() or _contains(value, term):
                body = {
                    "support_index": support_index,
                    "evidence_index": evidence.evidence_index,
                    "record_id": evidence.record_id,
                    "matched_term": term,
                    "support_path": path,
                    "support_value": _truncate(value),
                    "support_kind": _support_kind(path, value, term),
                    "read_only": True,
                }
                support = OracleEvidenceSupport(
                    **body,
                    support_hash=_stable_hash(body),
                )
                verify_evidence_support(support)
                supports.append(support)
                support_index += 1

    return tuple(supports)


def verify_evidence_support(
    support: OracleEvidenceSupport,
) -> bool:
    body = asdict(support)
    supplied = body.pop("support_hash")
    if _stable_hash(body) != supplied:
        raise OracleEvidenceExplainabilityInvariantError(
            "OIT-010 support hash mismatch"
        )
    if not support.read_only:
        raise OracleEvidenceExplainabilityInvariantError(
            "evidence support is not read-only"
        )
    if support.support_index < 1 or support.evidence_index < 1:
        raise OracleEvidenceExplainabilityInvariantError(
            "invalid evidence support index"
        )
    if not support.support_path:
        raise OracleEvidenceExplainabilityInvariantError(
            "evidence support path is missing"
        )
    return True


def _explanation_text(
    evidence: OracleGroundedEvidenceItem,
    supports: tuple[OracleEvidenceSupport, ...],
) -> str:
    if not evidence.matched_terms:
        return (
            f"Evidence [E{evidence.evidence_index}] was selected by the "
            "certified deterministic ranking, but no matched term was recorded."
        )
    if not supports:
        return (
            f"Evidence [E{evidence.evidence_index}] matched "
            f"{', '.join(evidence.matched_terms)}, but the bounded summary "
            "does not expose a more specific supporting field path."
        )

    grouped: dict[str, list[str]] = {}
    for support in supports:
        grouped.setdefault(support.matched_term, []).append(
            support.support_path
        )

    parts = []
    for term in evidence.matched_terms:
        paths = grouped.get(term, [])
        if paths:
            parts.append(f'"{term}" at {", ".join(paths[:5])}')
    return (
        f"Evidence [E{evidence.evidence_index}] supports the answer because "
        + "; ".join(parts)
        + "."
    )


def inspect_grounded_evidence(
    evidence: OracleGroundedEvidenceItem,
) -> OracleEvidenceInspection:
    verify_grounded_evidence_item(evidence)
    supports = _build_supports(evidence)
    lineage_complete = bool(
        evidence.artifact_relative_path
        and len(evidence.artifact_sha256) == 64
        and evidence.record_hash
        and evidence.query_plan_hash
        and evidence.evidence_hash
    )
    body = {
        "evidence_index": evidence.evidence_index,
        "record_id": evidence.record_id,
        "artifact_relative_path": evidence.artifact_relative_path,
        "artifact_sha256": evidence.artifact_sha256,
        "record_hash": evidence.record_hash,
        "query_plan_hash": evidence.query_plan_hash,
        "evidence_hash": evidence.evidence_hash,
        "matched_terms": evidence.matched_terms,
        "matched_required_terms": evidence.matched_required_terms,
        "matched_field_hints": evidence.matched_field_hints,
        "selected_fields": evidence.selected_fields,
        "supports": supports,
        "support_count": len(supports),
        "explanation_text": _explanation_text(evidence, supports),
        "lineage_complete": lineage_complete,
        "read_only": True,
    }
    inspection = OracleEvidenceInspection(
        **body,
        inspection_hash=_stable_hash(body),
    )
    verify_evidence_inspection(inspection)
    return inspection


def verify_evidence_inspection(
    inspection: OracleEvidenceInspection,
) -> bool:
    body = asdict(inspection)
    supplied = body.pop("inspection_hash")
    if _stable_hash(body) != supplied:
        raise OracleEvidenceExplainabilityInvariantError(
            "OIT-010 inspection hash mismatch"
        )
    for support in inspection.supports:
        verify_evidence_support(support)
    if not inspection.read_only:
        raise OracleEvidenceExplainabilityInvariantError(
            "evidence inspection is not read-only"
        )
    if inspection.support_count != len(inspection.supports):
        raise OracleEvidenceExplainabilityInvariantError(
            "support count mismatch"
        )
    if not inspection.lineage_complete:
        raise OracleEvidenceExplainabilityInvariantError(
            "evidence inspection lineage is incomplete"
        )
    if inspection.matched_required_terms and not set(
        inspection.matched_required_terms
    ).issubset(set(inspection.matched_terms)):
        raise OracleEvidenceExplainabilityInvariantError(
            "required terms are not preserved in matched terms"
        )
    return True


def build_answer_explainability_report(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleAnswerExplainabilityReport:
    root = repository_root.resolve()
    answer = compose_grounded_intelligence_answer(
        repository_root=root,
        query=query,
        result_limit=result_limit,
    )
    verify_grounded_intelligence_answer(answer)

    inspections = tuple(
        inspect_grounded_evidence(item)
        for item in answer.evidence
    )
    ready = bool(
        answer.answer_grounded
        and inspections
        and len(inspections) == answer.evidence_count
    )
    failure = answer.failure_reason
    if answer.answer_grounded and not ready and failure is None:
        failure = "not all grounded evidence could be explained"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "answer_explainability_ready"
            if ready
            else "answer_explainability_blocked"
        ),
        "repository_root": root.as_posix(),
        "query": answer.query,
        "answer_text": answer.answer_text,
        "answer_hash": answer.answer_hash,
        "query_plan_hash": answer.query_plan_hash,
        "query_result_hash": answer.query_result_hash,
        "inspections": inspections,
        "evidence_count": answer.evidence_count,
        "explained_evidence_count": len(inspections),
        "answer_grounded": answer.answer_grounded,
        "explainability_ready": ready,
        "uncertainty_statement": answer.uncertainty_statement,
        "limitation_statement": answer.limitation_statement,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    report = OracleAnswerExplainabilityReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_answer_explainability_report(report)
    return report


def verify_answer_explainability_report(
    report: OracleAnswerExplainabilityReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleEvidenceExplainabilityInvariantError(
            "OIT-010 report hash mismatch"
        )
    for inspection in report.inspections:
        verify_evidence_inspection(inspection)
        if inspection.query_plan_hash != report.query_plan_hash:
            raise OracleEvidenceExplainabilityInvariantError(
                "inspection query-plan lineage mismatch"
            )
    if not report.read_only:
        raise OracleEvidenceExplainabilityInvariantError(
            "OIT-010 is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleEvidenceExplainabilityInvariantError(
            "unsafe explainability boundary"
        )
    if report.explained_evidence_count != len(report.inspections):
        raise OracleEvidenceExplainabilityInvariantError(
            "explained evidence count mismatch"
        )
    if report.explainability_ready:
        if not report.answer_grounded:
            raise OracleEvidenceExplainabilityInvariantError(
                "explainability ready without grounded answer"
            )
        if report.evidence_count != report.explained_evidence_count:
            raise OracleEvidenceExplainabilityInvariantError(
                "not all evidence was explained"
            )
    return True


def select_evidence_inspection(
    report: OracleAnswerExplainabilityReport,
    *,
    selector: str,
) -> OracleEvidenceInspection:
    verify_answer_explainability_report(report)
    normalized = selector.strip()
    if not normalized:
        raise OracleEvidenceExplainabilityInvariantError(
            "evidence selector is required"
        )
    numeric = normalized[1:] if normalized.upper().startswith("E") else normalized
    if numeric.isdigit():
        index = int(numeric)
        for inspection in report.inspections:
            if inspection.evidence_index == index:
                return inspection
    for inspection in report.inspections:
        if inspection.record_id == normalized:
            return inspection
    raise OracleEvidenceExplainabilityInvariantError(
        f"evidence inspection not found: {selector}"
    )


def answer_explainability_lines(
    report: OracleAnswerExplainabilityReport,
) -> tuple[str, ...]:
    verify_answer_explainability_report(report)
    lines = [
        "ORACLE ANSWER EXPLAINABILITY REPORT",
        f"query: {report.query}",
        f"answer: {report.answer_text}",
        f"answer_grounded: {str(report.answer_grounded).lower()}",
        f"explainability_ready: {str(report.explainability_ready).lower()}",
        f"evidence_count: {report.evidence_count}",
        f"explained_evidence_count: {report.explained_evidence_count}",
        f"failure_reason: {report.failure_reason or 'none'}",
        f"uncertainty: {report.uncertainty_statement}",
    ]
    if not report.inspections:
        lines.append("explanations: none")
    for inspection in report.inspections:
        lines.extend((
            f"[E{inspection.evidence_index}] {inspection.record_id}",
            f"    explanation: {inspection.explanation_text}",
            f"    matched_terms: {', '.join(inspection.matched_terms) or 'none'}",
            f"    matched_required_terms: {', '.join(inspection.matched_required_terms) or 'none'}",
            f"    matched_field_hints: {', '.join(inspection.matched_field_hints) or 'none'}",
            f"    support_count: {inspection.support_count}",
            f"    artifact: {inspection.artifact_relative_path}",
            f"    lineage_complete: {str(inspection.lineage_complete).lower()}",
        ))
    lines.extend((
        f"query_plan_hash: {report.query_plan_hash}",
        f"query_result_hash: {report.query_result_hash}",
        f"answer_hash: {report.answer_hash}",
        f"report_hash: {report.report_hash}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)


def evidence_inspection_lines(
    inspection: OracleEvidenceInspection,
) -> tuple[str, ...]:
    verify_evidence_inspection(inspection)
    lines = [
        "ORACLE EVIDENCE INSPECTION",
        f"evidence: E{inspection.evidence_index}",
        f"record_id: {inspection.record_id}",
        f"explanation: {inspection.explanation_text}",
        f"matched_terms: {', '.join(inspection.matched_terms) or 'none'}",
        f"matched_required_terms: {', '.join(inspection.matched_required_terms) or 'none'}",
        f"matched_field_hints: {', '.join(inspection.matched_field_hints) or 'none'}",
        f"support_count: {inspection.support_count}",
    ]
    if not inspection.supports:
        lines.append("supports: none")
    for support in inspection.supports:
        lines.extend((
            f"[S{support.support_index}] term={support.matched_term}",
            f"    path: {support.support_path}",
            f"    value: {json.dumps(_canonical(support.support_value), ensure_ascii=False)}",
            f"    kind: {support.support_kind}",
        ))
    lines.extend((
        f"artifact: {inspection.artifact_relative_path}",
        f"artifact_sha256: {inspection.artifact_sha256}",
        f"record_hash: {inspection.record_hash}",
        f"query_plan_hash: {inspection.query_plan_hash}",
        f"evidence_hash: {inspection.evidence_hash}",
        f"inspection_hash: {inspection.inspection_hash}",
        "lineage_complete: true",
        "read_only: true",
    ))
    return tuple(lines)
