from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_bounded_multi_turn_intelligence_session_context import (
    OracleBoundedMultiTurnSessionContext,
    OracleBoundedMultiTurnSessionInvariantError,
    OracleIntelligenceConversationTurn,
    verify_conversation_turn,
    verify_multi_turn_session_context,
)

SCHEMA_VERSION = "OIT-044"
ENGINE_ID = "OIT-044"
POLICY_ID = "oracle.multi-turn-follow-up-query-context-resolution.v1"

MAX_FOLLOW_UP_LENGTH = 2000

FOLLOW_UP_TERMS = frozenset(
    {
        "it",
        "that",
        "this",
        "they",
        "them",
        "those",
        "these",
        "same",
        "still",
        "changed",
        "change",
        "now",
        "before",
        "again",
        "more",
        "less",
        "why",
        "how",
        "what",
        "which",
        "and",
        "but",
    }
)


class OracleFollowUpQueryResolutionInvariantError(
    OracleBoundedMultiTurnSessionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleFollowUpQueryReference:
    reference_type: str
    source_turn_index: int
    source_turn_hash: str
    source_query: str
    source_answer_id: str
    source_answer_hash: str
    reference_text: str
    reference_score: int
    reference_hash: str


@dataclass(frozen=True)
class OracleResolvedFollowUpQuery:
    raw_query: str
    normalized_query: str
    query_terms: tuple[str, ...]
    follow_up_detected: bool
    standalone_query: bool
    referenced_turns: tuple[OracleFollowUpQueryReference, ...]
    referenced_turn_count: int
    primary_reference_turn_index: int | None
    resolved_query: str
    resolution_confidence: float
    session_lineage_preserved: bool
    resolution_ready: bool
    read_only: bool
    resolution_hash: str


@dataclass(frozen=True)
class OracleFollowUpQueryResolutionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    source_session_context_hash: str
    resolved_follow_up_query: OracleResolvedFollowUpQuery
    context_resolution_performed: bool
    downstream_projection_ready: bool
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
    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value
    raise OracleFollowUpQueryResolutionInvariantError(
        "unsupported follow-up resolution value type: "
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


def _normalize_query(query: str) -> str:
    return " ".join(str(query).strip().split())


def _terms(query: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", query.lower()))


def _detect_follow_up(
    normalized_query: str,
    query_terms: tuple[str, ...],
) -> bool:
    if not normalized_query or not query_terms:
        return False

    if any(term in FOLLOW_UP_TERMS for term in query_terms):
        return True

    return len(query_terms) <= 4


def _reference_for_turn(
    turn: OracleIntelligenceConversationTurn,
    *,
    current_terms: tuple[str, ...],
    latest_turn_index: int,
) -> OracleFollowUpQueryReference:
    verify_conversation_turn(turn)

    source_terms = set(_terms(turn.query))
    overlap = len(source_terms.intersection(current_terms))

    distance = latest_turn_index - turn.turn_index
    recency_score = max(1, 20 - max(0, distance))
    reference_score = (overlap * 10) + recency_score

    body = {
        "reference_type": (
            "latest_turn"
            if turn.turn_index == latest_turn_index
            else "prior_turn"
        ),
        "source_turn_index": turn.turn_index,
        "source_turn_hash": turn.turn_hash,
        "source_query": turn.query,
        "source_answer_id": turn.answer_id,
        "source_answer_hash": turn.answer_hash,
        "reference_text": (
            f"turn {turn.turn_index}: {turn.query}"
        ),
        "reference_score": reference_score,
    }
    reference = OracleFollowUpQueryReference(
        **body,
        reference_hash=_stable_hash(body),
    )
    verify_follow_up_reference(reference)
    return reference


def verify_follow_up_reference(
    reference: OracleFollowUpQueryReference,
) -> bool:
    body = asdict(reference)
    supplied = body.pop("reference_hash")

    if _stable_hash(body) != supplied:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up reference hash mismatch"
        )

    if reference.reference_type not in {
        "latest_turn",
        "prior_turn",
    }:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up reference type invalid"
        )

    if reference.source_turn_index < 0:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up source turn index invalid"
        )

    if not reference.source_turn_hash:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up source turn lineage missing"
        )

    if not reference.source_query:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up source query missing"
        )

    if (
        not reference.source_answer_id
        or not reference.source_answer_hash
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up source answer identity missing"
        )

    if reference.reference_score < 0:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up reference score invalid"
        )

    return True


def verify_resolved_follow_up_query(
    resolved: OracleResolvedFollowUpQuery,
) -> bool:
    body = asdict(resolved)
    supplied = body.pop("resolution_hash")

    if _stable_hash(body) != supplied:
        raise OracleFollowUpQueryResolutionInvariantError(
            "resolved follow-up query hash mismatch"
        )

    if not resolved.normalized_query:
        raise OracleFollowUpQueryResolutionInvariantError(
            "normalized follow-up query missing"
        )

    if len(resolved.normalized_query) > MAX_FOLLOW_UP_LENGTH:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up query exceeds length limit"
        )

    if resolved.query_terms != _terms(
        resolved.normalized_query
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up query term normalization mismatch"
        )

    if resolved.follow_up_detected == resolved.standalone_query:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up and standalone states conflict"
        )

    for reference in resolved.referenced_turns:
        verify_follow_up_reference(reference)

    if resolved.referenced_turn_count != len(
        resolved.referenced_turns
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up reference count mismatch"
        )

    if resolved.primary_reference_turn_index is None:
        if resolved.referenced_turns:
            raise OracleFollowUpQueryResolutionInvariantError(
                "follow-up primary reference missing"
            )
    elif not any(
        reference.source_turn_index
        == resolved.primary_reference_turn_index
        for reference in resolved.referenced_turns
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up primary reference not present"
        )

    if not 0.0 <= resolved.resolution_confidence <= 1.0:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up resolution confidence outside bounds"
        )

    expected_ready = bool(
        resolved.normalized_query
        and resolved.session_lineage_preserved
        and resolved.read_only
        and (
            resolved.standalone_query
            or (
                resolved.follow_up_detected
                and resolved.referenced_turns
                and resolved.primary_reference_turn_index
                is not None
            )
        )
    )

    if resolved.resolution_ready != expected_ready:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up resolution readiness mismatch"
        )

    return True


def resolve_multi_turn_follow_up_query(
    repository_root: str | Path,
    *,
    session_context: OracleBoundedMultiTurnSessionContext,
    query: str,
) -> OracleFollowUpQueryResolutionReport:
    root = Path(repository_root).resolve()
    verify_multi_turn_session_context(session_context)

    normalized = _normalize_query(query)
    query_terms = _terms(normalized)

    if not normalized:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up query is empty"
        )

    if len(normalized) > MAX_FOLLOW_UP_LENGTH:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up query exceeds maximum length"
        )

    follow_up_detected = _detect_follow_up(
        normalized,
        query_terms,
    )
    standalone_query = not follow_up_detected

    references: tuple[OracleFollowUpQueryReference, ...] = ()
    primary_reference_turn_index: int | None = None
    resolved_query = normalized
    resolution_confidence = 1.0 if standalone_query else 0.0

    if follow_up_detected:
        latest_turn_index = session_context.latest_turn_index

        candidates = tuple(
            _reference_for_turn(
                turn,
                current_terms=query_terms,
                latest_turn_index=latest_turn_index,
            )
            for turn in session_context.turns
        )

        references = tuple(
            sorted(
                candidates,
                key=lambda reference: (
                    -reference.reference_score,
                    -reference.source_turn_index,
                    reference.reference_hash,
                ),
            )[:3]
        )

        if references:
            primary = references[0]
            primary_reference_turn_index = (
                primary.source_turn_index
            )
            resolved_query = (
                normalized
                + " [context from prior query: "
                + primary.source_query
                + "]"
            )
            resolution_confidence = min(
                1.0,
                0.5 + (primary.reference_score / 100.0),
            )

    lineage_preserved = all(
        any(
            turn.turn_hash == reference.source_turn_hash
            and turn.answer_hash
            == reference.source_answer_hash
            and turn.answer_id
            == reference.source_answer_id
            for turn in session_context.turns
        )
        for reference in references
    )

    resolved_body = {
        "raw_query": str(query),
        "normalized_query": normalized,
        "query_terms": query_terms,
        "follow_up_detected": follow_up_detected,
        "standalone_query": standalone_query,
        "referenced_turns": references,
        "referenced_turn_count": len(references),
        "primary_reference_turn_index": (
            primary_reference_turn_index
        ),
        "resolved_query": resolved_query,
        "resolution_confidence": resolution_confidence,
        "session_lineage_preserved": lineage_preserved,
        "resolution_ready": bool(
            normalized
            and lineage_preserved
            and (
                standalone_query
                or (
                    follow_up_detected
                    and references
                    and primary_reference_turn_index
                    is not None
                )
            )
        ),
        "read_only": True,
    }
    resolved = OracleResolvedFollowUpQuery(
        **resolved_body,
        resolution_hash=_stable_hash(resolved_body),
    )
    verify_resolved_follow_up_query(resolved)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "source_session_context_hash": (
            session_context.context_hash
        ),
        "resolved_follow_up_query": resolved,
        "context_resolution_performed": follow_up_detected,
        "downstream_projection_ready": (
            resolved.resolution_ready
        ),
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
            if resolved.resolution_ready
            else "follow_up_resolution_not_ready"
        ),
    }
    report = OracleFollowUpQueryResolutionReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_follow_up_query_resolution_report(report)
    return report


def verify_follow_up_query_resolution_report(
    report: OracleFollowUpQueryResolutionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up query resolution report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up resolution schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up resolution policy mismatch"
        )

    verify_resolved_follow_up_query(
        report.resolved_follow_up_query
    )

    if not report.read_only:
        raise OracleFollowUpQueryResolutionInvariantError(
            "follow-up resolution report is not read-only"
        )

    if (
        report.persistent_memory_enabled
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
        raise OracleFollowUpQueryResolutionInvariantError(
            "forbidden follow-up capability enabled"
        )

    if report.context_resolution_performed != (
        report.resolved_follow_up_query.follow_up_detected
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "context resolution state mismatch"
        )

    if report.downstream_projection_ready != (
        report.resolved_follow_up_query.resolution_ready
    ):
        raise OracleFollowUpQueryResolutionInvariantError(
            "downstream projection readiness mismatch"
        )

    return True
