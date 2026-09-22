from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_natural_language_query_planning_and_execution import (
    OracleNaturalLanguageQueryInvariantError,
    OracleNaturalLanguageQueryMatch,
    OracleNaturalLanguageQueryResult,
    execute_natural_language_query,
    verify_natural_language_query_match,
    verify_natural_language_query_result,
)

SCHEMA_VERSION = "OIT-009"
ENGINE_ID = "OIT-009"
POLICY_ID = "oracle.grounded-intelligence-answer-composition.v2"

MAX_EVIDENCE_ITEMS = 10
SUMMARY_FIELD_PRIORITY = (
    "title",
    "question",
    "market",
    "market_id",
    "prediction_id",
    "record_id",
    "ticker",
    "symbol",
    "stance",
    "direction",
    "signal",
    "probability",
    "confidence",
    "score",
    "price",
    "venue",
    "exchange",
    "expires_at",
    "date",
    "status",
)


class OracleGroundedAnswerInvariantError(
    OracleNaturalLanguageQueryInvariantError
):
    pass


@dataclass(frozen=True)
class OracleGroundedEvidenceItem:
    evidence_index: int
    record_id: str
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    query_plan_hash: str
    matched_terms: tuple[str, ...]
    matched_required_terms: tuple[str, ...]
    matched_field_hints: tuple[str, ...]
    score: int
    selected_fields: tuple[tuple[str, Any], ...]
    evidence_label: str
    read_only: bool
    evidence_hash: str


@dataclass(frozen=True)
class OracleGroundedIntelligenceAnswer:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    answer_text: str
    evidence: tuple[OracleGroundedEvidenceItem, ...]
    evidence_count: int
    answer_grounded: bool
    uncertainty_statement: str
    limitation_statement: str
    query_plan_hash: str
    query_result_hash: str
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    answer_hash: str


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


def _selected_fields(payload: Any) -> tuple[tuple[str, Any], ...]:
    if not isinstance(payload, Mapping):
        return (("value", _canonical(payload)),)

    selected: list[tuple[str, Any]] = []
    seen: set[str] = set()

    for key in SUMMARY_FIELD_PRIORITY:
        if key in payload and key not in seen:
            selected.append((key, _canonical(payload[key])))
            seen.add(key)

    if not selected:
        for key, value in sorted(payload.items(), key=lambda item: str(item[0])):
            selected.append((str(key), _canonical(value)))
            if len(selected) >= 8:
                break

    return tuple(selected)


def _display_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(
            _canonical(value),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return str(value)


def _build_evidence_item(
    *,
    index: int,
    match: OracleNaturalLanguageQueryMatch,
    query_plan_hash: str,
) -> OracleGroundedEvidenceItem:
    verify_natural_language_query_match(match)
    selected = _selected_fields(match.payload)
    label_parts = [
        f"{key}={_display_value(value)}"
        for key, value in selected[:6]
    ]
    label = "; ".join(label_parts) or f"record_id={match.record_id}"

    body = {
        "evidence_index": index,
        "record_id": match.record_id,
        "artifact_relative_path": match.artifact_relative_path,
        "artifact_sha256": match.artifact_sha256,
        "record_hash": match.record_hash,
        "query_plan_hash": query_plan_hash,
        "matched_terms": match.matched_terms,
        "matched_required_terms": match.matched_required_terms,
        "matched_field_hints": match.matched_field_hints,
        "score": match.score,
        "selected_fields": selected,
        "evidence_label": label,
        "read_only": True,
    }
    item = OracleGroundedEvidenceItem(
        **body,
        evidence_hash=_stable_hash(body),
    )
    verify_grounded_evidence_item(item)
    return item


def verify_grounded_evidence_item(
    item: OracleGroundedEvidenceItem,
) -> bool:
    body = asdict(item)
    supplied = body.pop("evidence_hash")
    if _stable_hash(body) != supplied:
        raise OracleGroundedAnswerInvariantError(
            "OIT-009 evidence hash mismatch"
        )
    if not item.read_only:
        raise OracleGroundedAnswerInvariantError(
            "grounded evidence item is not read-only"
        )
    if item.evidence_index < 1:
        raise OracleGroundedAnswerInvariantError(
            "invalid evidence index"
        )
    if (
        len(item.artifact_sha256) != 64
        or not item.record_hash
        or not item.query_plan_hash
    ):
        raise OracleGroundedAnswerInvariantError(
            "evidence lineage is incomplete"
        )
    if item.matched_required_terms and not set(
        item.matched_required_terms
    ).issubset(set(item.matched_terms)):
        raise OracleGroundedAnswerInvariantError(
            "required evidence terms are not present in matched terms"
        )
    return True


def _compose_answer_text(
    *,
    query: str,
    evidence: tuple[OracleGroundedEvidenceItem, ...],
) -> str:
    if not evidence:
        return (
            f'No admitted Oracle intelligence record matched the question '
            f'"{query}".'
        )
    if len(evidence) == 1:
        item = evidence[0]
        return (
            f'Oracle found one grounded match for "{query}": '
            f'{item.evidence_label}. Evidence [E1].'
        )
    return (
        f'Oracle found {len(evidence)} grounded matches for "{query}". '
        + " ".join(
            f"[E{item.evidence_index}] {item.evidence_label}"
            for item in evidence
        )
    )


def _uncertainty_statement(
    result: OracleNaturalLanguageQueryResult,
) -> str:
    if not result.query_ready:
        return (
            "The answer is unavailable because the admitted intelligence "
            "read model is not query-ready."
        )
    if result.match_count == 0:
        return (
            "No matching admitted record was found; this does not prove that "
            "the requested fact or opportunity does not exist."
        )
    if result.match_count == 1:
        return (
            "The answer is supported by one admitted record and should not be "
            "treated as independently corroborated."
        )
    return (
        f"The answer reflects {result.match_count} admitted matching records; "
        "agreement, independence, and freshness are not inferred beyond the "
        "fields shown."
    )


def compose_grounded_intelligence_answer(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleGroundedIntelligenceAnswer:
    root = repository_root.resolve()
    result = execute_natural_language_query(
        repository_root=root,
        query=query,
        result_limit=min(result_limit, MAX_EVIDENCE_ITEMS),
    )
    verify_natural_language_query_result(result)

    evidence = tuple(
        _build_evidence_item(
            index=index,
            match=match,
            query_plan_hash=result.plan.plan_hash,
        )
        for index, match in enumerate(result.matches, start=1)
    )
    grounded = bool(result.query_ready and evidence)
    failure = result.failure_reason
    limitation = (
        "This answer only summarizes immutable OIT-005-admitted artifacts "
        "available through the certified OIT-006 to OIT-008 V3 read-only "
        "chain. It does not execute analytics, access databases, publish, "
        "trade, or create facts absent from matched records."
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "grounded_intelligence_answer_composed"
            if result.query_ready
            else "grounded_intelligence_answer_blocked"
        ),
        "repository_root": root.as_posix(),
        "query": result.plan.normalized_query,
        "answer_text": _compose_answer_text(
            query=result.plan.normalized_query,
            evidence=evidence,
        ),
        "evidence": evidence,
        "evidence_count": len(evidence),
        "answer_grounded": grounded,
        "uncertainty_statement": _uncertainty_statement(result),
        "limitation_statement": limitation,
        "query_plan_hash": result.plan.plan_hash,
        "query_result_hash": result.result_hash,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    answer = OracleGroundedIntelligenceAnswer(
        **body,
        answer_hash=_stable_hash(body),
    )
    verify_grounded_intelligence_answer(answer)
    return answer


def verify_grounded_intelligence_answer(
    answer: OracleGroundedIntelligenceAnswer,
) -> bool:
    body = asdict(answer)
    supplied = body.pop("answer_hash")
    if _stable_hash(body) != supplied:
        raise OracleGroundedAnswerInvariantError(
            "OIT-009 answer hash mismatch"
        )
    for item in answer.evidence:
        verify_grounded_evidence_item(item)
        if item.query_plan_hash != answer.query_plan_hash:
            raise OracleGroundedAnswerInvariantError(
                "evidence query-plan lineage mismatch"
            )
    if not answer.read_only:
        raise OracleGroundedAnswerInvariantError(
            "OIT-009 is not read-only"
        )
    if (
        answer.analytics_execution_performed
        or answer.database_access_performed
        or answer.publication_allowed
        or answer.qseries_execution_allowed
    ):
        raise OracleGroundedAnswerInvariantError(
            "unsafe grounded answer boundary"
        )
    if answer.evidence_count != len(answer.evidence):
        raise OracleGroundedAnswerInvariantError(
            "evidence count mismatch"
        )
    if answer.answer_grounded and not answer.evidence:
        raise OracleGroundedAnswerInvariantError(
            "grounded answer has no evidence"
        )
    if not answer.query_plan_hash or not answer.query_result_hash:
        raise OracleGroundedAnswerInvariantError(
            "grounded answer lacks query lineage"
        )
    return True


def grounded_answer_lines(
    answer: OracleGroundedIntelligenceAnswer,
) -> tuple[str, ...]:
    verify_grounded_intelligence_answer(answer)
    lines = [
        "ORACLE GROUNDED INTELLIGENCE ANSWER",
        f"query: {answer.query}",
        f"answer: {answer.answer_text}",
        f"answer_grounded: {str(answer.answer_grounded).lower()}",
        f"evidence_count: {answer.evidence_count}",
        f"failure_reason: {answer.failure_reason or 'none'}",
        f"uncertainty: {answer.uncertainty_statement}",
        f"limitations: {answer.limitation_statement}",
    ]
    if not answer.evidence:
        lines.append("evidence: none")
    else:
        lines.append("evidence:")
        for item in answer.evidence:
            lines.extend((
                f"  [E{item.evidence_index}] {item.record_id}",
                f"      summary: {item.evidence_label}",
                f"      score: {item.score}",
                f"      matched_terms: {', '.join(item.matched_terms) or 'none'}",
                f"      matched_required_terms: {', '.join(item.matched_required_terms) or 'none'}",
                f"      matched_field_hints: {', '.join(item.matched_field_hints) or 'none'}",
                f"      artifact: {item.artifact_relative_path}",
                f"      artifact_sha256: {item.artifact_sha256}",
                f"      record_hash: {item.record_hash}",
                f"      query_plan_hash: {item.query_plan_hash}",
            ))
    lines.extend((
        f"query_plan_hash: {answer.query_plan_hash}",
        f"query_result_hash: {answer.query_result_hash}",
        f"answer_hash: {answer.answer_hash}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)
