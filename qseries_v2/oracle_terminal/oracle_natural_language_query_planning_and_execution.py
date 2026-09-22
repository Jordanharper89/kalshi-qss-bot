from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_queryable_intelligence_read_model import (
    OracleQueryableIntelligenceInvariantError,
    QueryableIntelligenceRecord,
    build_queryable_intelligence_read_model,
    verify_queryable_intelligence_read_model,
    verify_queryable_record,
)

SCHEMA_VERSION = "OIT-008"
ENGINE_ID = "OIT-008"
POLICY_ID = "oracle.natural-language-query-planning-and-execution.v2"

MAX_QUERY_LENGTH = 1000
MAX_TERMS = 24
MAX_RESULTS = 50

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "give", "how", "i", "in", "is", "it", "me", "of", "on",
    "or", "show", "tell", "that", "the", "this", "to", "what", "when",
    "where", "which", "who", "why", "with", "would",
}

FIELD_ALIASES = {
    "market": ("market_id", "market", "title", "slug"),
    "probability": ("probability", "confidence", "score"),
    "confidence": ("confidence", "probability", "score"),
    "bull": ("stance", "direction", "signal"),
    "bear": ("stance", "direction", "signal"),
    "neutral": ("stance", "direction", "signal"),
    "ticker": ("ticker", "symbol"),
    "price": ("price", "market_price", "venue_price"),
    "venue": ("venue", "exchange", "platform"),
    "date": ("date", "executed_at", "created_at", "expires_at"),
}

# These describe schema/field intent and may match through field hints.
# Directional values, IDs, names, venues, tickers, and other content terms
# remain mandatory record-content matches.
GENERIC_SCHEMA_TERMS = frozenset({
    "market",
    "probability",
    "confidence",
    "ticker",
    "price",
    "venue",
    "date",
})


class OracleNaturalLanguageQueryInvariantError(
    OracleQueryableIntelligenceInvariantError
):
    pass


@dataclass(frozen=True)
class OracleNaturalLanguageQueryPlan:
    schema_version: str
    engine_id: str
    policy_id: str
    original_query: str
    normalized_query: str
    search_terms: tuple[str, ...]
    required_content_terms: tuple[str, ...]
    generic_schema_terms: tuple[str, ...]
    field_hints: tuple[str, ...]
    result_limit: int
    query_mode: str
    read_only: bool
    analytics_execution_allowed: bool
    database_access_allowed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    plan_hash: str


@dataclass(frozen=True)
class OracleNaturalLanguageQueryMatch:
    rank: int
    global_record_index: int
    record_id: str
    artifact_relative_path: str
    artifact_sha256: str
    matched_terms: tuple[str, ...]
    matched_required_terms: tuple[str, ...]
    matched_field_hints: tuple[str, ...]
    score: int
    payload: Any
    record_hash: str
    read_only: bool
    match_hash: str


@dataclass(frozen=True)
class OracleNaturalLanguageQueryResult:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    plan: OracleNaturalLanguageQueryPlan
    matches: tuple[OracleNaturalLanguageQueryMatch, ...]
    match_count: int
    query_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    result_hash: str


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


def _normalize_query(query: str) -> str:
    normalized = " ".join(query.strip().split())
    if not normalized:
        raise OracleNaturalLanguageQueryInvariantError(
            "natural-language query is required"
        )
    if len(normalized) > MAX_QUERY_LENGTH:
        raise OracleNaturalLanguageQueryInvariantError(
            f"query exceeds maximum length of {MAX_QUERY_LENGTH}"
        )
    return normalized


def _tokenize(query: str) -> tuple[str, ...]:
    tokens = re.findall(r"[A-Za-z0-9_.:/%-]+", query.lower())
    filtered: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in STOP_WORDS:
            continue
        if token not in seen:
            filtered.append(token)
            seen.add(token)
        if len(filtered) >= MAX_TERMS:
            break
    return tuple(filtered)


def _required_content_terms(
    terms: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        term for term in terms
        if term not in GENERIC_SCHEMA_TERMS
    )


def _generic_schema_terms(
    terms: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        term for term in terms
        if term in GENERIC_SCHEMA_TERMS
    )


def _field_hints(terms: tuple[str, ...]) -> tuple[str, ...]:
    hints: set[str] = set()
    for term in terms:
        for field in FIELD_ALIASES.get(term, ()):
            hints.add(field)
    return tuple(sorted(hints))


def build_natural_language_query_plan(
    *,
    query: str,
    result_limit: int = 10,
) -> OracleNaturalLanguageQueryPlan:
    normalized = _normalize_query(query)
    if result_limit < 1 or result_limit > MAX_RESULTS:
        raise OracleNaturalLanguageQueryInvariantError(
            f"result_limit must be between 1 and {MAX_RESULTS}"
        )

    terms = _tokenize(normalized)
    if not terms:
        raise OracleNaturalLanguageQueryInvariantError(
            "query contains no searchable terms"
        )

    required = _required_content_terms(terms)
    generic = _generic_schema_terms(terms)
    hints = _field_hints(terms)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "original_query": query,
        "normalized_query": normalized,
        "search_terms": terms,
        "required_content_terms": required,
        "generic_schema_terms": generic,
        "field_hints": hints,
        "result_limit": result_limit,
        "query_mode": "deterministic_read_only_grounded_search",
        "read_only": True,
        "analytics_execution_allowed": False,
        "database_access_allowed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
    }
    plan = OracleNaturalLanguageQueryPlan(
        **body,
        plan_hash=_stable_hash(body),
    )
    verify_natural_language_query_plan(plan)
    return plan


def verify_natural_language_query_plan(
    plan: OracleNaturalLanguageQueryPlan,
) -> bool:
    body = asdict(plan)
    supplied = body.pop("plan_hash")
    if _stable_hash(body) != supplied:
        raise OracleNaturalLanguageQueryInvariantError(
            "OIT-008 query plan hash mismatch"
        )
    if not plan.read_only:
        raise OracleNaturalLanguageQueryInvariantError(
            "query plan is not read-only"
        )
    if (
        plan.analytics_execution_allowed
        or plan.database_access_allowed
        or plan.publication_allowed
        or plan.qseries_execution_allowed
    ):
        raise OracleNaturalLanguageQueryInvariantError(
            "unsafe query plan boundary"
        )
    if not plan.search_terms:
        raise OracleNaturalLanguageQueryInvariantError(
            "query plan has no search terms"
        )
    if set(plan.required_content_terms) & set(plan.generic_schema_terms):
        raise OracleNaturalLanguageQueryInvariantError(
            "required and generic term sets overlap"
        )
    if set(plan.required_content_terms) | set(plan.generic_schema_terms) != set(
        plan.search_terms
    ):
        raise OracleNaturalLanguageQueryInvariantError(
            "query term partition is incomplete"
        )
    return True


def _field_hint_matches(
    record: QueryableIntelligenceRecord,
    hints: tuple[str, ...],
) -> tuple[str, ...]:
    fields = set(record.field_paths)
    matched: list[str] = []
    for hint in hints:
        if any(
            field == hint
            or field.startswith(hint + ".")
            or field.endswith("." + hint)
            or field.endswith("]." + hint)
            for field in fields
        ):
            matched.append(hint)
    return tuple(sorted(set(matched)))


def _matched_terms(
    record: QueryableIntelligenceRecord,
    terms: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        term for term in terms
        if term in record.searchable_text
    )


def _score_record(
    record: QueryableIntelligenceRecord,
    *,
    matched_terms: tuple[str, ...],
    matched_required_terms: tuple[str, ...],
    matched_hints: tuple[str, ...],
) -> int:
    score = (
        len(matched_terms) * 10
        + len(matched_required_terms) * 20
        + len(matched_hints) * 4
    )
    lowered_id = record.record_id.lower()
    for term in matched_required_terms:
        if term == lowered_id:
            score += 25
        elif term in lowered_id:
            score += 8
    return score


def _build_match(
    *,
    rank: int,
    record: QueryableIntelligenceRecord,
    matched_terms: tuple[str, ...],
    matched_required_terms: tuple[str, ...],
    matched_hints: tuple[str, ...],
    score: int,
) -> OracleNaturalLanguageQueryMatch:
    verify_queryable_record(record)
    body = {
        "rank": rank,
        "global_record_index": record.global_record_index,
        "record_id": record.record_id,
        "artifact_relative_path": record.artifact_relative_path,
        "artifact_sha256": record.artifact_sha256,
        "matched_terms": matched_terms,
        "matched_required_terms": matched_required_terms,
        "matched_field_hints": matched_hints,
        "score": score,
        "payload": _canonical(record.payload),
        "record_hash": record.record_hash,
        "read_only": True,
    }
    match = OracleNaturalLanguageQueryMatch(
        **body,
        match_hash=_stable_hash(body),
    )
    verify_natural_language_query_match(match)
    return match


def verify_natural_language_query_match(
    match: OracleNaturalLanguageQueryMatch,
) -> bool:
    body = asdict(match)
    supplied = body.pop("match_hash")
    if _stable_hash(body) != supplied:
        raise OracleNaturalLanguageQueryInvariantError(
            "OIT-008 query match hash mismatch"
        )
    if not match.read_only:
        raise OracleNaturalLanguageQueryInvariantError(
            "query match is not read-only"
        )
    if match.rank < 1 or match.score < 0:
        raise OracleNaturalLanguageQueryInvariantError(
            "invalid query match ranking"
        )
    return True


def execute_natural_language_query(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleNaturalLanguageQueryResult:
    root = repository_root.resolve()
    plan = build_natural_language_query_plan(
        query=query,
        result_limit=result_limit,
    )
    model = build_queryable_intelligence_read_model(
        repository_root=root
    )
    verify_queryable_intelligence_read_model(model)

    ranked: list[
        tuple[
            QueryableIntelligenceRecord,
            tuple[str, ...],
            tuple[str, ...],
            tuple[str, ...],
            int,
        ]
    ] = []

    if model.query_ready:
        for record in model.records:
            matched_terms = _matched_terms(record, plan.search_terms)
            matched_required = tuple(
                term for term in plan.required_content_terms
                if term in record.searchable_text
            )
            matched_hints = _field_hint_matches(
                record,
                plan.field_hints,
            )

            # Every content-bearing term must exist in the record.
            if plan.required_content_terms and matched_required != (
                plan.required_content_terms
            ):
                continue

            # A schema-only query must have at least one matching field hint.
            if not plan.required_content_terms and not matched_hints:
                continue

            # Mixed queries must also have at least one schema hint when
            # generic schema terms were explicitly requested.
            if plan.generic_schema_terms and not matched_hints:
                continue

            score = _score_record(
                record,
                matched_terms=matched_terms,
                matched_required_terms=matched_required,
                matched_hints=matched_hints,
            )
            ranked.append(
                (
                    record,
                    matched_terms,
                    matched_required,
                    matched_hints,
                    score,
                )
            )

    ranked.sort(
        key=lambda item: (
            -item[4],
            item[0].global_record_index,
            item[0].record_id,
        )
    )

    matches = tuple(
        _build_match(
            rank=index,
            record=record,
            matched_terms=matched_terms,
            matched_required_terms=matched_required,
            matched_hints=matched_hints,
            score=score,
        )
        for index, (
            record,
            matched_terms,
            matched_required,
            matched_hints,
            score,
        ) in enumerate(ranked[:plan.result_limit], start=1)
    )

    ready = model.query_ready
    failure = model.failure_reason
    if ready and not matches:
        failure = "query completed with no matching intelligence records"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "natural_language_query_completed"
            if ready
            else "natural_language_query_blocked"
        ),
        "repository_root": root.as_posix(),
        "plan": plan,
        "matches": matches,
        "match_count": len(matches),
        "query_ready": ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    result = OracleNaturalLanguageQueryResult(
        **body,
        result_hash=_stable_hash(body),
    )
    verify_natural_language_query_result(result)
    return result


def verify_natural_language_query_result(
    result: OracleNaturalLanguageQueryResult,
) -> bool:
    body = asdict(result)
    supplied = body.pop("result_hash")
    if _stable_hash(body) != supplied:
        raise OracleNaturalLanguageQueryInvariantError(
            "OIT-008 query result hash mismatch"
        )
    verify_natural_language_query_plan(result.plan)
    for match in result.matches:
        verify_natural_language_query_match(match)
        if result.plan.required_content_terms and match.matched_required_terms != (
            result.plan.required_content_terms
        ):
            raise OracleNaturalLanguageQueryInvariantError(
                "query result admitted a partial required-term match"
            )
    if not result.read_only:
        raise OracleNaturalLanguageQueryInvariantError(
            "OIT-008 is not read-only"
        )
    if (
        result.analytics_execution_performed
        or result.database_access_performed
        or result.publication_allowed
        or result.qseries_execution_allowed
    ):
        raise OracleNaturalLanguageQueryInvariantError(
            "unsafe natural-language query boundary"
        )
    if result.match_count != len(result.matches):
        raise OracleNaturalLanguageQueryInvariantError(
            "query match count mismatch"
        )
    return True


def natural_language_query_plan_lines(
    plan: OracleNaturalLanguageQueryPlan,
) -> tuple[str, ...]:
    verify_natural_language_query_plan(plan)
    return (
        "ORACLE NATURAL-LANGUAGE QUERY PLAN",
        f"original_query: {plan.original_query}",
        f"normalized_query: {plan.normalized_query}",
        f"search_terms: {', '.join(plan.search_terms)}",
        f"required_content_terms: {', '.join(plan.required_content_terms) or 'none'}",
        f"generic_schema_terms: {', '.join(plan.generic_schema_terms) or 'none'}",
        f"field_hints: {', '.join(plan.field_hints) or 'none'}",
        f"result_limit: {plan.result_limit}",
        f"query_mode: {plan.query_mode}",
        "analytics_execution_allowed: false",
        "database_access_allowed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    )


def natural_language_query_result_lines(
    result: OracleNaturalLanguageQueryResult,
) -> tuple[str, ...]:
    verify_natural_language_query_result(result)
    lines = [
        "ORACLE NATURAL-LANGUAGE INTELLIGENCE QUERY",
        f"query: {result.plan.normalized_query}",
        f"required_content_terms: {', '.join(result.plan.required_content_terms) or 'none'}",
        f"generic_schema_terms: {', '.join(result.plan.generic_schema_terms) or 'none'}",
        f"field_hints: {', '.join(result.plan.field_hints) or 'none'}",
        f"query_ready: {str(result.query_ready).lower()}",
        f"match_count: {result.match_count}",
        f"failure_reason: {result.failure_reason or 'none'}",
    ]
    if not result.matches:
        lines.append("matches: none")
    for match in result.matches:
        payload = json.dumps(
            _canonical(match.payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        lines.extend((
            f"[{match.rank}] {match.record_id}",
            f"    score: {match.score}",
            f"    matched_terms: {', '.join(match.matched_terms) or 'none'}",
            f"    matched_required_terms: {', '.join(match.matched_required_terms) or 'none'}",
            f"    matched_field_hints: {', '.join(match.matched_field_hints) or 'none'}",
            f"    artifact: {match.artifact_relative_path}",
            f"    record_index: {match.global_record_index}",
            "    payload:",
            *tuple(f"      {line}" for line in payload.splitlines()),
        ))
    lines.extend((
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)
