from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_decision_explanation_evidence_trace_intelligence import (
    OracleDecisionExplanationFinding,
    OracleDecisionExplanationInvariantError,
    OracleDecisionExplanationReport,
    build_decision_explanation_report,
    verify_decision_explanation_report,
)

SCHEMA_VERSION = "OIT-022"
ENGINE_ID = "OIT-022"
POLICY_ID = "oracle.operator-decision-brief-assembly.v1"


class OracleOperatorDecisionBriefInvariantError(
    OracleDecisionExplanationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleOperatorDecisionBriefItem:
    item_index: int
    cause_record_id: str
    effect_record_id: str
    source_explanation_hash: str
    readiness_state: str
    directional_interpretation: str
    headline: str
    explanation: str
    evidence_points: tuple[str, ...]
    confirmation_actions: tuple[str, ...]
    blocking_conditions: tuple[str, ...]
    operator_attention_required: bool
    presentation_priority: int
    read_only: bool
    item_hash: str


@dataclass(frozen=True)
class OracleOperatorDecisionBrief:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    explanation_report_hash: str
    brief_items: tuple[OracleOperatorDecisionBriefItem, ...]
    item_count: int
    ready_item_count: int
    observe_item_count: int
    abstain_item_count: int
    operator_attention_count: int
    primary_state: str
    primary_direction: str
    brief_title: str
    executive_summary: str
    operator_next_steps: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    terminal_consumption_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    action_authorization_allowed: bool
    failure_reason: str | None
    brief_hash: str


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


def _headline(source: OracleDecisionExplanationFinding) -> str:
    direction = source.directional_interpretation.replace("_", " ").title()
    if source.readiness_state == "ready":
        return f"READY — {direction}"
    if source.readiness_state == "observe":
        return f"OBSERVE — {direction}"
    return f"ABSTAIN — {direction}"


def _priority(source: OracleDecisionExplanationFinding) -> int:
    if source.readiness_state == "abstain":
        return 1
    if source.operator_attention_required:
        return 2
    if source.readiness_state == "observe":
        return 3
    return 4


def _build_item(
    source: OracleDecisionExplanationFinding,
    index: int,
) -> OracleOperatorDecisionBriefItem:
    evidence = tuple(
        trace.evidence_statement for trace in source.evidence_trace
    )
    body = {
        "item_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_explanation_hash": source.finding_hash,
        "readiness_state": source.readiness_state,
        "directional_interpretation": source.directional_interpretation,
        "headline": _headline(source),
        "explanation": source.concise_explanation,
        "evidence_points": evidence,
        "confirmation_actions": tuple(source.confirmation_plan),
        "blocking_conditions": tuple(source.blocking_conditions),
        "operator_attention_required": source.operator_attention_required,
        "presentation_priority": _priority(source),
        "read_only": True,
    }
    return OracleOperatorDecisionBriefItem(
        **body,
        item_hash=_stable_hash(body),
    )


def verify_operator_decision_brief_item(
    item: OracleOperatorDecisionBriefItem,
) -> bool:
    body = asdict(item)
    supplied = body.pop("item_hash")
    if _stable_hash(body) != supplied:
        raise OracleOperatorDecisionBriefInvariantError(
            "operator decision brief item hash mismatch"
        )
    if not item.read_only:
        raise OracleOperatorDecisionBriefInvariantError(
            "operator decision brief item is not read-only"
        )
    if item.readiness_state not in {"ready", "observe", "abstain"}:
        raise OracleOperatorDecisionBriefInvariantError(
            "unsupported brief readiness state"
        )
    if not item.source_explanation_hash:
        raise OracleOperatorDecisionBriefInvariantError(
            "explanation lineage missing"
        )
    if not item.headline or not item.explanation:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief presentation content missing"
        )
    if not item.evidence_points:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief evidence points missing"
        )
    if not item.confirmation_actions:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief confirmation actions missing"
        )
    if not item.blocking_conditions:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief blocking conditions missing"
        )
    if item.presentation_priority < 1:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief presentation priority invalid"
        )
    return True


def _aggregate_next_steps(
    items: tuple[OracleOperatorDecisionBriefItem, ...],
) -> tuple[str, ...]:
    collected: list[str] = []
    seen: set[str] = set()
    for item in items:
        for action in item.confirmation_actions:
            if action not in seen:
                seen.add(action)
                collected.append(action)
    return tuple(collected)


def _aggregate_blockers(
    items: tuple[OracleOperatorDecisionBriefItem, ...],
) -> tuple[str, ...]:
    collected: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item.readiness_state == "ready":
            continue
        for blocker in item.blocking_conditions:
            if blocker not in seen:
                seen.add(blocker)
                collected.append(blocker)
    return tuple(collected)


def build_operator_decision_brief(
    repository_root: str | Path,
    query: str,
    *,
    explanation_report: OracleDecisionExplanationReport | None = None,
) -> OracleOperatorDecisionBrief:
    root = Path(repository_root).resolve()
    source = explanation_report
    if source is None:
        source = build_decision_explanation_report(root, query)
    verify_decision_explanation_report(source)

    unsorted_items = tuple(
        _build_item(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    items = tuple(
        sorted(
            unsorted_items,
            key=lambda item: (
                item.presentation_priority,
                item.item_index,
                item.item_hash,
            ),
        )
    )
    for item in items:
        verify_operator_decision_brief_item(item)

    ready_count = sum(item.readiness_state == "ready" for item in items)
    observe_count = sum(item.readiness_state == "observe" for item in items)
    abstain_count = sum(item.readiness_state == "abstain" for item in items)
    attention_count = sum(
        item.operator_attention_required for item in items
    )
    next_steps = _aggregate_next_steps(items)
    blockers = _aggregate_blockers(items)
    terminal_ready = bool(
        items
        and all(item.evidence_points for item in items)
        and all(item.source_explanation_hash for item in items)
    )
    title = (
        f"Oracle Operator Decision Brief — "
        f"{source.aggregate_state.upper()} / "
        f"{source.aggregate_direction.upper()}"
    )
    summary = (
        f"{len(items)} items assembled: {ready_count} ready, "
        f"{observe_count} observe, {abstain_count} abstain; "
        f"{attention_count} require operator attention. "
        "This brief is explanatory only and cannot authorize action."
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "explanation_report_hash": source.report_hash,
        "brief_items": items,
        "item_count": len(items),
        "ready_item_count": ready_count,
        "observe_item_count": observe_count,
        "abstain_item_count": abstain_count,
        "operator_attention_count": attention_count,
        "primary_state": source.aggregate_state,
        "primary_direction": source.aggregate_direction,
        "brief_title": title,
        "executive_summary": summary,
        "operator_next_steps": next_steps,
        "unresolved_blockers": blockers,
        "terminal_consumption_ready": terminal_ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    brief = OracleOperatorDecisionBrief(
        **body,
        brief_hash=_stable_hash(body),
    )
    verify_operator_decision_brief(brief)
    return brief


def verify_operator_decision_brief(
    brief: OracleOperatorDecisionBrief,
) -> bool:
    body = asdict(brief)
    supplied = body.pop("brief_hash")
    if _stable_hash(body) != supplied:
        raise OracleOperatorDecisionBriefInvariantError(
            "operator decision brief hash mismatch"
        )
    if brief.schema_version != SCHEMA_VERSION:
        raise OracleOperatorDecisionBriefInvariantError("schema mismatch")
    if brief.policy_id != POLICY_ID:
        raise OracleOperatorDecisionBriefInvariantError("policy mismatch")
    if not brief.read_only:
        raise OracleOperatorDecisionBriefInvariantError(
            "operator decision brief is not read-only"
        )
    if (
        brief.analytics_execution_performed
        or brief.database_access_performed
        or brief.publication_allowed
        or brief.qseries_execution_allowed
        or brief.action_authorization_allowed
    ):
        raise OracleOperatorDecisionBriefInvariantError(
            "forbidden capability enabled"
        )
    if brief.item_count != len(brief.brief_items):
        raise OracleOperatorDecisionBriefInvariantError(
            "brief item count mismatch"
        )
    counts = {
        "ready": brief.ready_item_count,
        "observe": brief.observe_item_count,
        "abstain": brief.abstain_item_count,
    }
    for state, expected in counts.items():
        actual = sum(
            item.readiness_state == state for item in brief.brief_items
        )
        if actual != expected:
            raise OracleOperatorDecisionBriefInvariantError(
                f"{state} brief count mismatch"
            )
    if sum(counts.values()) != brief.item_count:
        raise OracleOperatorDecisionBriefInvariantError(
            "classified brief count mismatch"
        )
    if brief.operator_attention_count != sum(
        item.operator_attention_required for item in brief.brief_items
    ):
        raise OracleOperatorDecisionBriefInvariantError(
            "operator attention count mismatch"
        )
    if brief.primary_state not in {"ready", "observe", "abstain"}:
        raise OracleOperatorDecisionBriefInvariantError(
            "invalid primary state"
        )
    if brief.primary_direction not in {"bull", "bear", "neutral"}:
        raise OracleOperatorDecisionBriefInvariantError(
            "invalid primary direction"
        )
    for item in brief.brief_items:
        verify_operator_decision_brief_item(item)
    expected_order = tuple(
        sorted(
            brief.brief_items,
            key=lambda item: (
                item.presentation_priority,
                item.item_index,
                item.item_hash,
            ),
        )
    )
    if brief.brief_items != expected_order:
        raise OracleOperatorDecisionBriefInvariantError(
            "brief item presentation order mismatch"
        )
    if brief.terminal_consumption_ready and not brief.brief_items:
        raise OracleOperatorDecisionBriefInvariantError(
            "empty brief marked terminal-ready"
        )
    return True
