from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_intelligence_session_context_assembly import (
    OracleIntelligenceContextField,
    OracleIntelligenceSessionContext,
    OracleIntelligenceSessionContextAssemblyReport,
    OracleIntelligenceSessionContextInvariantError,
    verify_context_field,
    verify_intelligence_session_context_assembly_report,
    verify_session_context,
)

SCHEMA_VERSION = "OIT-041"
ENGINE_ID = "OIT-041"
POLICY_ID = "oracle.natural-language-intelligence-response-projection.v1"

MAX_QUERY_LENGTH = 2000
MAX_SELECTED_FIELDS = 64

GENERIC_TERMS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "do",
        "does",
        "for",
        "from",
        "give",
        "how",
        "i",
        "in",
        "intelligence",
        "is",
        "it",
        "market",
        "me",
        "of",
        "on",
        "or",
        "show",
        "tell",
        "that",
        "the",
        "this",
        "to",
        "what",
        "which",
        "with",
    }
)


class OracleIntelligenceResponseProjectionInvariantError(
    OracleIntelligenceSessionContextInvariantError
):
    pass


@dataclass(frozen=True)
class OracleIntelligenceQueryIntent:
    raw_query: str
    normalized_query: str
    query_terms: tuple[str, ...]
    distinctive_terms: tuple[str, ...]
    requested_field_names: tuple[str, ...]
    broad_context_requested: bool
    evidence_requested: bool
    query_valid: bool
    intent_hash: str


@dataclass(frozen=True)
class OracleProjectedIntelligenceField:
    context_key: str
    source_field_path: str
    source_context_field_hash: str
    field_type: str
    canonical_value: Any
    searchable_text: str
    match_terms: tuple[str, ...]
    match_score: int
    selection_reason: str
    projection_ordinal: int
    projected_field_hash: str


@dataclass(frozen=True)
class OracleNaturalLanguageIntelligenceProjection:
    projection_id: str
    source_context_hash: str
    source_context_report_hash: str
    query_intent: OracleIntelligenceQueryIntent
    projected_fields: tuple[OracleProjectedIntelligenceField, ...]
    projected_field_count: int
    evidence_field_count: int
    exact_field_match_count: int
    term_match_count: int
    bounded_projection: bool
    source_lineage_preserved: bool
    deterministic_ordering_applied: bool
    projection_ready: bool
    read_only: bool
    projection_hash: str


@dataclass(frozen=True)
class OracleNaturalLanguageIntelligenceProjectionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    context_assembly_report_hash: str
    projection: OracleNaturalLanguageIntelligenceProjection
    query_accepted: bool
    relevant_context_found: bool
    answer_generation_ready: bool
    free_form_answer_generated: bool
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
    raise OracleIntelligenceResponseProjectionInvariantError(
        f"unsupported projection value type: "
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


def _terms(value: str) -> tuple[str, ...]:
    return tuple(
        re.findall(r"[a-z0-9]+", str(value).lower())
    )


def _normalize_query(query: str) -> str:
    return " ".join(str(query).strip().split())


def _build_query_intent(
    query: str,
    context: OracleIntelligenceSessionContext,
) -> OracleIntelligenceQueryIntent:
    normalized = _normalize_query(query)
    query_terms = _terms(normalized)
    distinctive = tuple(
        term
        for term in query_terms
        if term not in GENERIC_TERMS and len(term) > 1
    )

    context_names = {
        field.context_key.lower()
        for field in context.context_fields
    }
    requested = tuple(
        sorted(
            name
            for name in context_names
            if any(
                part in query_terms
                for part in _terms(name)
            )
        )
    )

    broad = bool(
        not distinctive
        or any(
            phrase in normalized.lower()
            for phrase in (
                "show everything",
                "full context",
                "all fields",
                "complete intelligence",
                "overview",
                "summary",
            )
        )
    )
    evidence_requested = any(
        term in query_terms
        for term in (
            "evidence",
            "source",
            "sources",
            "support",
            "proof",
            "confidence",
        )
    )
    valid = bool(
        normalized
        and len(normalized) <= MAX_QUERY_LENGTH
        and query_terms
    )

    body = {
        "raw_query": str(query),
        "normalized_query": normalized,
        "query_terms": query_terms,
        "distinctive_terms": distinctive,
        "requested_field_names": requested,
        "broad_context_requested": broad,
        "evidence_requested": evidence_requested,
        "query_valid": valid,
    }
    intent = OracleIntelligenceQueryIntent(
        **body,
        intent_hash=_stable_hash(body),
    )
    verify_query_intent(intent)
    return intent


def verify_query_intent(
    intent: OracleIntelligenceQueryIntent,
) -> bool:
    body = asdict(intent)
    supplied = body.pop("intent_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "query intent hash mismatch"
        )
    expected_valid = bool(
        intent.normalized_query
        and len(intent.normalized_query) <= MAX_QUERY_LENGTH
        and intent.query_terms
    )
    if intent.query_valid != expected_valid:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "query validity mismatch"
        )
    if tuple(_terms(intent.normalized_query)) != intent.query_terms:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "query term normalization mismatch"
        )
    return True


def _score_context_field(
    field: OracleIntelligenceContextField,
    intent: OracleIntelligenceQueryIntent,
) -> tuple[int, tuple[str, ...], str]:
    key_terms = set(_terms(field.context_key))
    path_terms = set(_terms(field.source_field_path))
    text_terms = set(_terms(field.searchable_text))
    distinctive = set(intent.distinctive_terms)

    exact_key = field.context_key.lower() in {
        name.lower()
        for name in intent.requested_field_names
    }
    matched = tuple(
        sorted(
            distinctive.intersection(
                key_terms | path_terms | text_terms
            )
        )
    )

    score = 0
    reason = "no_match"

    if exact_key:
        score += 100
        reason = "exact_field_request"

    if matched:
        score += len(matched) * 10
        if reason == "no_match":
            reason = "distinctive_term_match"

    if intent.evidence_requested and any(
        token in field.context_key.lower()
        or token in field.source_field_path.lower()
        for token in ("evidence", "source", "confidence")
    ):
        score += 25
        reason = (
            "evidence_request"
            if reason == "no_match"
            else reason + "+evidence_request"
        )

    if intent.broad_context_requested:
        score += 1
        if reason == "no_match":
            reason = "broad_context"

    if field.source_field_path == "$":
        score += 1
        if reason == "no_match":
            reason = "root_context"

    return score, matched, reason


def _project_field(
    field: OracleIntelligenceContextField,
    *,
    match_terms: tuple[str, ...],
    score: int,
    reason: str,
    ordinal: int,
) -> OracleProjectedIntelligenceField:
    verify_context_field(field)
    body = {
        "context_key": field.context_key,
        "source_field_path": field.source_field_path,
        "source_context_field_hash": (
            field.context_field_hash
        ),
        "field_type": field.field_type,
        "canonical_value": field.canonical_value,
        "searchable_text": field.searchable_text,
        "match_terms": match_terms,
        "match_score": score,
        "selection_reason": reason,
        "projection_ordinal": ordinal,
    }
    projected = OracleProjectedIntelligenceField(
        **body,
        projected_field_hash=_stable_hash(body),
    )
    verify_projected_field(projected)
    return projected


def verify_projected_field(
    field: OracleProjectedIntelligenceField,
) -> bool:
    body = asdict(field)
    supplied = body.pop("projected_field_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected field hash mismatch"
        )
    if not field.context_key:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected context key missing"
        )
    if not field.source_field_path:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected source path missing"
        )
    if not field.source_context_field_hash:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected field lineage missing"
        )
    if field.match_score < 0:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected field score invalid"
        )
    if field.projection_ordinal < 0:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected field ordinal invalid"
        )
    return True


def verify_projection(
    projection: OracleNaturalLanguageIntelligenceProjection,
) -> bool:
    body = asdict(projection)
    supplied = body.pop("projection_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection hash mismatch"
        )

    verify_query_intent(projection.query_intent)
    for index, field in enumerate(projection.projected_fields):
        verify_projected_field(field)
        if field.projection_ordinal != index:
            raise OracleIntelligenceResponseProjectionInvariantError(
                "projection field ordering mismatch"
            )

    if projection.projected_field_count != len(
        projection.projected_fields
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projected field count mismatch"
        )

    if projection.evidence_field_count != sum(
        any(
            token in field.context_key.lower()
            or token in field.source_field_path.lower()
            for token in ("evidence", "source", "confidence")
        )
        for field in projection.projected_fields
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "evidence field count mismatch"
        )

    if projection.exact_field_match_count != sum(
        "exact_field_request" in field.selection_reason
        for field in projection.projected_fields
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "exact field match count mismatch"
        )

    if projection.term_match_count != sum(
        bool(field.match_terms)
        for field in projection.projected_fields
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "term match count mismatch"
        )

    if projection.bounded_projection != (
        projection.projected_field_count <= MAX_SELECTED_FIELDS
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "bounded projection state mismatch"
        )

    if not projection.source_lineage_preserved:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection source lineage incomplete"
        )

    if not projection.deterministic_ordering_applied:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection ordering not deterministic"
        )

    expected_ready = bool(
        projection.query_intent.query_valid
        and projection.projected_fields
        and projection.bounded_projection
        and projection.source_lineage_preserved
        and projection.deterministic_ordering_applied
        and projection.read_only
    )
    if projection.projection_ready != expected_ready:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection readiness mismatch"
        )
    return True


def build_natural_language_intelligence_projection_report(
    repository_root: str | Path,
    *,
    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,
    query: str,
) -> OracleNaturalLanguageIntelligenceProjectionReport:
    root = Path(repository_root).resolve()
    verify_intelligence_session_context_assembly_report(
        context_assembly_report
    )

    if not context_assembly_report.query_planning_ready:
        raise OracleIntelligenceResponseProjectionInvariantError(
            context_assembly_report.failure_reason
            or "session context is not query-planning ready"
        )

    context = context_assembly_report.session_context
    verify_session_context(context)
    intent = _build_query_intent(query, context)

    if not intent.query_valid:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "natural-language query is invalid"
        )

    scored = []
    for field in context.context_fields:
        score, matched, reason = _score_context_field(
            field,
            intent,
        )
        if score > 0:
            scored.append(
                (score, field.source_field_path, field, matched, reason)
            )

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1],
            item[2].context_field_hash,
        )
    )
    selected = scored[:MAX_SELECTED_FIELDS]

    projected_fields = tuple(
        _project_field(
            field,
            match_terms=matched,
            score=score,
            reason=reason,
            ordinal=index,
        )
        for index, (
            score,
            _,
            field,
            matched,
            reason,
        ) in enumerate(selected)
    )

    lineage_preserved = all(
        any(
            projected.source_context_field_hash
            == source.context_field_hash
            and projected.source_field_path
            == source.source_field_path
            for source in context.context_fields
        )
        for projected in projected_fields
    )

    projection_body = {
        "projection_id": _stable_hash(
            {
                "context_hash": context.context_hash,
                "query_intent_hash": intent.intent_hash,
                "projected_fields": projected_fields,
            }
        )[:24],
        "source_context_hash": context.context_hash,
        "source_context_report_hash": (
            context_assembly_report.report_hash
        ),
        "query_intent": intent,
        "projected_fields": projected_fields,
        "projected_field_count": len(projected_fields),
        "evidence_field_count": sum(
            any(
                token in field.context_key.lower()
                or token in field.source_field_path.lower()
                for token in (
                    "evidence",
                    "source",
                    "confidence",
                )
            )
            for field in projected_fields
        ),
        "exact_field_match_count": sum(
            "exact_field_request" in field.selection_reason
            for field in projected_fields
        ),
        "term_match_count": sum(
            bool(field.match_terms)
            for field in projected_fields
        ),
        "bounded_projection": (
            len(projected_fields) <= MAX_SELECTED_FIELDS
        ),
        "source_lineage_preserved": lineage_preserved,
        "deterministic_ordering_applied": True,
        "projection_ready": bool(
            intent.query_valid
            and projected_fields
            and lineage_preserved
            and len(projected_fields) <= MAX_SELECTED_FIELDS
        ),
        "read_only": True,
    }
    projection = OracleNaturalLanguageIntelligenceProjection(
        **projection_body,
        projection_hash=_stable_hash(projection_body),
    )
    verify_projection(projection)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "context_assembly_report_hash": (
            context_assembly_report.report_hash
        ),
        "projection": projection,
        "query_accepted": intent.query_valid,
        "relevant_context_found": bool(projected_fields),
        "answer_generation_ready": projection.projection_ready,
        "free_form_answer_generated": False,
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
            None
            if projection.projection_ready
            else "relevant_context_not_found"
        ),
    }
    report = OracleNaturalLanguageIntelligenceProjectionReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_natural_language_intelligence_projection_report(
        report
    )
    return report


def verify_natural_language_intelligence_projection_report(
    report: OracleNaturalLanguageIntelligenceProjectionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection policy mismatch"
        )

    verify_projection(report.projection)

    if not report.read_only:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "projection report is not read-only"
        )

    if (
        report.free_form_answer_generated
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
        raise OracleIntelligenceResponseProjectionInvariantError(
            "forbidden projection capability enabled"
        )

    if report.query_accepted != (
        report.projection.query_intent.query_valid
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "query acceptance mismatch"
        )

    if report.relevant_context_found != bool(
        report.projection.projected_fields
    ):
        raise OracleIntelligenceResponseProjectionInvariantError(
            "relevant context state mismatch"
        )

    expected = bool(
        report.query_accepted
        and report.relevant_context_found
        and report.projection.projection_ready
    )
    if report.answer_generation_ready != expected:
        raise OracleIntelligenceResponseProjectionInvariantError(
            "answer generation readiness mismatch"
        )
    return True
