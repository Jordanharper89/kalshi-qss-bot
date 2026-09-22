from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_adversarial_perspective_debate_and_challenge import (
    OracleAdversarialDebateInvariantError,
    build_adversarial_debate_report,
    verify_adversarial_debate_report,
)
from .oracle_evidence_inspection_and_answer_explainability import (
    OracleAnswerExplainabilityReport,
    OracleEvidenceInspection,
    build_answer_explainability_report,
    verify_answer_explainability_report,
    verify_evidence_inspection,
)

SCHEMA_VERSION = "OIT-013"
ENGINE_ID = "OIT-013"
POLICY_ID = "oracle.temporal-intelligence-timeline-reconstruction.v3"

TIMESTAMP_FIELDS = frozenset({
    "executed_at", "executed_at_utc",
    "created_at", "created_at_utc",
    "updated_at", "updated_at_utc",
    "observed_at", "observed_at_utc",
    "timestamp", "timestamp_utc",
    "date",
    "published_at", "published_at_utc",
    "expires_at", "expires_at_utc",
    "expiration", "expiration_at",
    "valid_until", "valid_through",
})
IDENTITY_FIELDS = (
    "record_id", "market_id", "id", "prediction_id",
    "event_id", "contract_id", "ticker", "symbol",
)
STALE_AFTER_SECONDS = 86400
MAX_DEPTH = 12
MAX_VALUES = 512


class OracleTemporalTimelineInvariantError(
    OracleAdversarialDebateInvariantError
):
    pass


@dataclass(frozen=True)
class OracleTemporalEvidenceEvent:
    event_index: int
    evidence_index: int
    record_id: str
    timestamp_field: str
    timestamp_text: str
    timestamp_utc: str
    epoch_seconds: int
    temporal_role: str
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    evidence_hash: str
    query_plan_hash: str
    inspection_hash: str
    source_record_locator: str
    read_only: bool
    event_hash: str


@dataclass(frozen=True)
class OracleTemporalTransition:
    transition_index: int
    from_event_index: int
    to_event_index: int
    from_record_id: str
    to_record_id: str
    elapsed_seconds: int
    elapsed_label: str
    transition_type: str
    transition_reason: str
    read_only: bool
    transition_hash: str


@dataclass(frozen=True)
class OracleTemporalIntelligenceReport:
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
    explainability_report_hash: str
    contradiction_report_hash: str
    debate_report_hash: str
    events: tuple[OracleTemporalEvidenceEvent, ...]
    transitions: tuple[OracleTemporalTransition, ...]
    event_count: int
    transition_count: int
    earliest_timestamp_utc: str | None
    latest_timestamp_utc: str | None
    span_seconds: int
    temporal_order_complete: bool
    stale_evidence_detected: bool
    missing_record_count: int
    missing_timestamp_count: int
    invalid_timestamp_count: int
    duplicate_timestamp_count: int
    chronology_state: str
    timeline_summary: str
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
    return hashlib.sha256(json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")).hexdigest()


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            number = float(value)
            if number > 10_000_000_000:
                number /= 1000.0
            return datetime.fromtimestamp(number, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    candidates = [normalized]
    if "T" not in normalized and " " not in normalized:
        candidates.append(normalized + "T00:00:00+00:00")
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None


def _temporal_role(path: str) -> str:
    leaf = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
    if "expire" in leaf or "expiration" in leaf or leaf.startswith("valid_"):
        return "expiration"
    if "update" in leaf:
        return "update"
    if "publish" in leaf:
        return "publication"
    if "create" in leaf:
        return "creation"
    if "observe" in leaf:
        return "observation"
    if "execute" in leaf:
        return "execution"
    return "timestamp"


def _flatten_timestamp_values(
    value: Any,
    *,
    prefix: str = "",
    depth: int = 0,
) -> tuple[tuple[str, Any], ...]:
    if depth >= MAX_DEPTH:
        return ()
    output: list[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            path = f"{prefix}.{key}" if prefix else str(key)
            leaf = str(key).lower()
            if leaf in TIMESTAMP_FIELDS:
                output.append((path, child))
            if isinstance(child, (Mapping, list, tuple)):
                output.extend(_flatten_timestamp_values(
                    child, prefix=path, depth=depth + 1
                ))
            if len(output) >= MAX_VALUES:
                break
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value[:MAX_VALUES]):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            if isinstance(child, (Mapping, list, tuple)):
                output.extend(_flatten_timestamp_values(
                    child, prefix=path, depth=depth + 1
                ))
            if len(output) >= MAX_VALUES:
                break
    return tuple(output[:MAX_VALUES])


def _identity_matches(record: Mapping[str, Any], record_id: str) -> bool:
    wanted = str(record_id).strip()
    for field in IDENTITY_FIELDS:
        if field in record and str(record[field]).strip() == wanted:
            return True
    return False


def _find_record(
    value: Any,
    record_id: str,
    *,
    path: str = "$",
    depth: int = 0,
) -> tuple[Mapping[str, Any], str] | None:
    if depth >= MAX_DEPTH:
        return None
    if isinstance(value, Mapping):
        if _identity_matches(value, record_id):
            return value, path
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            if isinstance(child, (Mapping, list, tuple)):
                found = _find_record(
                    child,
                    record_id,
                    path=f"{path}.{key}",
                    depth=depth + 1,
                )
                if found is not None:
                    return found
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for index, child in enumerate(value[:MAX_VALUES]):
            if isinstance(child, (Mapping, list, tuple)):
                found = _find_record(
                    child,
                    record_id,
                    path=f"{path}[{index}]",
                    depth=depth + 1,
                )
                if found is not None:
                    return found
    return None


def _load_verified_artifact(
    root: Path,
    inspection: OracleEvidenceInspection,
) -> Any:
    verify_evidence_inspection(inspection)
    relative = Path(inspection.artifact_relative_path)
    if relative.is_absolute():
        raise OracleTemporalTimelineInvariantError(
            "absolute artifact path is not allowed"
        )
    artifact = (root / relative).resolve()
    try:
        artifact.relative_to(root)
    except ValueError as exc:
        raise OracleTemporalTimelineInvariantError(
            "artifact path escapes repository root"
        ) from exc
    if not artifact.is_file():
        raise OracleTemporalTimelineInvariantError(
            f"certified artifact missing: {inspection.artifact_relative_path}"
        )
    raw = artifact.read_bytes()
    if hashlib.sha256(raw).hexdigest() != inspection.artifact_sha256:
        raise OracleTemporalTimelineInvariantError(
            "certified artifact hash mismatch"
        )
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OracleTemporalTimelineInvariantError(
            "certified artifact is not valid UTF-8 JSON"
        ) from exc


def _validate_alignment(debate, explainability) -> None:
    verify_adversarial_debate_report(debate)
    verify_answer_explainability_report(explainability)
    checks = (
        ("query", debate.query, explainability.query),
        ("answer_hash", debate.answer_hash, explainability.answer_hash),
        ("query_plan_hash", debate.query_plan_hash, explainability.query_plan_hash),
        ("query_result_hash", debate.query_result_hash, explainability.query_result_hash),
        ("explainability_report_hash", debate.explainability_report_hash, explainability.report_hash),
    )
    for label, left, right in checks:
        if left != right:
            raise OracleTemporalTimelineInvariantError(
                f"OIT-013 upstream {label} lineage mismatch"
            )


def _build_events(
    root: Path,
    explainability: OracleAnswerExplainabilityReport,
) -> tuple[tuple[OracleTemporalEvidenceEvent, ...], int, int, int]:
    raw_events = []
    missing_record_count = 0
    missing_timestamp_count = 0
    invalid_timestamp_count = 0

    for inspection in explainability.inspections:
        payload = _load_verified_artifact(root, inspection)
        located = _find_record(payload, inspection.record_id)
        if located is None:
            missing_record_count += 1
            continue
        record, locator = located
        candidates = _flatten_timestamp_values(record)
        if not candidates:
            missing_timestamp_count += 1
            continue
        valid_for_record = 0
        for field, value in candidates:
            parsed = _parse_timestamp(value)
            if parsed is None:
                invalid_timestamp_count += 1
                continue
            valid_for_record += 1
            raw_events.append((
                parsed,
                inspection,
                field,
                str(value),
                locator,
            ))
        if valid_for_record == 0:
            missing_timestamp_count += 1

    raw_events.sort(key=lambda item: (
        item[0],
        item[1].evidence_index,
        item[1].record_id,
        item[2],
    ))

    events = []
    for event_index, (parsed, inspection, field, original, locator) in enumerate(
        raw_events, start=1
    ):
        body = {
            "event_index": event_index,
            "evidence_index": inspection.evidence_index,
            "record_id": inspection.record_id,
            "timestamp_field": field,
            "timestamp_text": original,
            "timestamp_utc": parsed.isoformat(),
            "epoch_seconds": int(parsed.timestamp()),
            "temporal_role": _temporal_role(field),
            "artifact_relative_path": inspection.artifact_relative_path,
            "artifact_sha256": inspection.artifact_sha256,
            "record_hash": inspection.record_hash,
            "evidence_hash": inspection.evidence_hash,
            "query_plan_hash": inspection.query_plan_hash,
            "inspection_hash": inspection.inspection_hash,
            "source_record_locator": locator,
            "read_only": True,
        }
        event = OracleTemporalEvidenceEvent(
            **body,
            event_hash=_stable_hash(body),
        )
        verify_temporal_evidence_event(event)
        events.append(event)

    return (
        tuple(events),
        missing_record_count,
        missing_timestamp_count,
        invalid_timestamp_count,
    )


def verify_temporal_evidence_event(event: OracleTemporalEvidenceEvent) -> bool:
    body = asdict(event)
    supplied = body.pop("event_hash")
    if _stable_hash(body) != supplied:
        raise OracleTemporalTimelineInvariantError(
            "OIT-013 temporal event hash mismatch"
        )
    if not event.read_only or event.event_index < 1 or event.evidence_index < 1:
        raise OracleTemporalTimelineInvariantError("invalid temporal event")
    if (
        len(event.artifact_sha256) != 64
        or not event.record_hash
        or not event.evidence_hash
        or not event.query_plan_hash
        or not event.inspection_hash
        or not event.source_record_locator
    ):
        raise OracleTemporalTimelineInvariantError(
            "temporal event lineage is incomplete"
        )
    parsed = _parse_timestamp(event.timestamp_utc)
    if parsed is None or int(parsed.timestamp()) != event.epoch_seconds:
        raise OracleTemporalTimelineInvariantError(
            "temporal event timestamp mismatch"
        )
    return True


def _elapsed_label(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def _build_transitions(events):
    transitions = []
    for index in range(1, len(events)):
        left, right = events[index - 1], events[index]
        elapsed = right.epoch_seconds - left.epoch_seconds
        if elapsed < 0:
            raise OracleTemporalTimelineInvariantError(
                "negative temporal transition"
            )
        if elapsed == 0:
            kind = "simultaneous"
            reason = "events share the same normalized UTC timestamp"
        elif elapsed > STALE_AFTER_SECONDS:
            kind = "stale_gap"
            reason = (
                f"elapsed time exceeds the {STALE_AFTER_SECONDS}-second "
                "staleness threshold"
            )
        else:
            kind = "chronological_progression"
            reason = "events advance in deterministic chronological order"
        body = {
            "transition_index": index,
            "from_event_index": left.event_index,
            "to_event_index": right.event_index,
            "from_record_id": left.record_id,
            "to_record_id": right.record_id,
            "elapsed_seconds": elapsed,
            "elapsed_label": _elapsed_label(elapsed),
            "transition_type": kind,
            "transition_reason": reason,
            "read_only": True,
        }
        transition = OracleTemporalTransition(
            **body,
            transition_hash=_stable_hash(body),
        )
        verify_temporal_transition(transition)
        transitions.append(transition)
    return tuple(transitions)


def verify_temporal_transition(transition: OracleTemporalTransition) -> bool:
    body = asdict(transition)
    supplied = body.pop("transition_hash")
    if _stable_hash(body) != supplied:
        raise OracleTemporalTimelineInvariantError(
            "OIT-013 transition hash mismatch"
        )
    if not transition.read_only or transition.elapsed_seconds < 0:
        raise OracleTemporalTimelineInvariantError(
            "invalid temporal transition"
        )
    return True


def build_temporal_intelligence_report(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleTemporalIntelligenceReport:
    root = repository_root.resolve()
    debate = build_adversarial_debate_report(
        repository_root=root,
        query=query,
        result_limit=result_limit,
    )
    explainability = build_answer_explainability_report(
        repository_root=root,
        query=query,
        result_limit=result_limit,
    )
    _validate_alignment(debate, explainability)

    (
        events,
        missing_record_count,
        missing_timestamp_count,
        invalid_timestamp_count,
    ) = _build_events(root, explainability)
    transitions = _build_transitions(events)

    counts = {}
    for event in events:
        counts[event.epoch_seconds] = counts.get(event.epoch_seconds, 0) + 1
    duplicate_timestamp_count = sum(
        count - 1 for count in counts.values() if count > 1
    )

    earliest = events[0].timestamp_utc if events else None
    latest = events[-1].timestamp_utc if events else None
    span = (
        events[-1].epoch_seconds - events[0].epoch_seconds
        if len(events) > 1 else 0
    )
    stale = any(x.transition_type == "stale_gap" for x in transitions)
    complete = bool(
        events
        and missing_record_count == 0
        and missing_timestamp_count == 0
        and invalid_timestamp_count == 0
    )

    if not events:
        state = "no_timestamped_evidence"
        summary = (
            "Oracle found no verified timestamped record in the certified "
            "source artifacts."
        )
    elif missing_record_count or missing_timestamp_count or invalid_timestamp_count:
        state = "partial_chronology"
        summary = (
            f"Oracle reconstructed {len(events)} event(s), with "
            f"{missing_record_count} missing record(s), "
            f"{missing_timestamp_count} record(s) without a valid timestamp, "
            f"and {invalid_timestamp_count} invalid timestamp value(s)."
        )
    elif stale:
        state = "chronology_with_stale_gaps"
        summary = (
            f"Oracle reconstructed {len(events)} event(s) across "
            f"{_elapsed_label(span)} and detected a stale gap."
        )
    elif duplicate_timestamp_count:
        state = "chronology_with_simultaneous_events"
        summary = (
            f"Oracle reconstructed {len(events)} event(s) with "
            f"{duplicate_timestamp_count} duplicate timestamp(s)."
        )
    else:
        state = "complete_chronology"
        summary = (
            f"Oracle reconstructed {len(events)} event(s) in deterministic "
            f"UTC order across {_elapsed_label(span)}."
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "temporal_intelligence_reconstructed"
            if events else "temporal_intelligence_limited"
        ),
        "repository_root": root.as_posix(),
        "query": debate.query,
        "answer_text": debate.answer_text,
        "answer_hash": debate.answer_hash,
        "query_plan_hash": debate.query_plan_hash,
        "query_result_hash": debate.query_result_hash,
        "explainability_report_hash": explainability.report_hash,
        "contradiction_report_hash": debate.contradiction_report_hash,
        "debate_report_hash": debate.report_hash,
        "events": events,
        "transitions": transitions,
        "event_count": len(events),
        "transition_count": len(transitions),
        "earliest_timestamp_utc": earliest,
        "latest_timestamp_utc": latest,
        "span_seconds": span,
        "temporal_order_complete": complete,
        "stale_evidence_detected": stale,
        "missing_record_count": missing_record_count,
        "missing_timestamp_count": missing_timestamp_count,
        "invalid_timestamp_count": invalid_timestamp_count,
        "duplicate_timestamp_count": duplicate_timestamp_count,
        "chronology_state": state,
        "timeline_summary": summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": debate.failure_reason,
    }
    report = OracleTemporalIntelligenceReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_temporal_intelligence_report(report)
    return report


def verify_temporal_intelligence_report(
    report: OracleTemporalIntelligenceReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleTemporalTimelineInvariantError(
            "OIT-013 report hash mismatch"
        )
    for event in report.events:
        verify_temporal_evidence_event(event)
        if event.query_plan_hash != report.query_plan_hash:
            raise OracleTemporalTimelineInvariantError(
                "event query-plan lineage mismatch"
            )
    for transition in report.transitions:
        verify_temporal_transition(transition)
    if report.event_count != len(report.events):
        raise OracleTemporalTimelineInvariantError("event count mismatch")
    if report.transition_count != len(report.transitions):
        raise OracleTemporalTimelineInvariantError("transition count mismatch")
    if report.transition_count != max(0, report.event_count - 1):
        raise OracleTemporalTimelineInvariantError(
            "transition topology mismatch"
        )
    epochs = [event.epoch_seconds for event in report.events]
    if epochs != sorted(epochs):
        raise OracleTemporalTimelineInvariantError(
            "events are not chronologically sorted"
        )
    if not report.read_only or (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleTemporalTimelineInvariantError(
            "unsafe temporal intelligence boundary"
        )
    return True


def temporal_intelligence_lines(
    report: OracleTemporalIntelligenceReport,
) -> tuple[str, ...]:
    verify_temporal_intelligence_report(report)
    lines = [
        "ORACLE TEMPORAL INTELLIGENCE TIMELINE",
        f"query: {report.query}",
        f"chronology_state: {report.chronology_state}",
        f"event_count: {report.event_count}",
        f"transition_count: {report.transition_count}",
        f"earliest_timestamp_utc: {report.earliest_timestamp_utc or 'none'}",
        f"latest_timestamp_utc: {report.latest_timestamp_utc or 'none'}",
        f"span_seconds: {report.span_seconds}",
        f"temporal_order_complete: {str(report.temporal_order_complete).lower()}",
        f"stale_evidence_detected: {str(report.stale_evidence_detected).lower()}",
        f"missing_record_count: {report.missing_record_count}",
        f"missing_timestamp_count: {report.missing_timestamp_count}",
        f"invalid_timestamp_count: {report.invalid_timestamp_count}",
        f"duplicate_timestamp_count: {report.duplicate_timestamp_count}",
        f"summary: {report.timeline_summary}",
        f"failure_reason: {report.failure_reason or 'none'}",
    ]
    if not report.events:
        lines.append("events: none")
    for event in report.events:
        lines.extend((
            f"[T{event.event_index}] {event.timestamp_utc}",
            f"    record_id: {event.record_id}",
            f"    evidence: E{event.evidence_index}",
            f"    field: {event.timestamp_field}",
            f"    original_value: {event.timestamp_text}",
            f"    temporal_role: {event.temporal_role}",
            f"    source_record_locator: {event.source_record_locator}",
            f"    artifact: {event.artifact_relative_path}",
            f"    inspection_hash: {event.inspection_hash}",
            f"    event_hash: {event.event_hash}",
        ))
    if report.transitions:
        lines.append("transitions:")
        for transition in report.transitions:
            lines.extend((
                f"  [X{transition.transition_index}] "
                f"T{transition.from_event_index}->T{transition.to_event_index}",
                f"      elapsed: {transition.elapsed_label}",
                f"      type: {transition.transition_type}",
                f"      reason: {transition.transition_reason}",
            ))
    else:
        lines.append("transitions: none")
    lines.extend((
        f"query_plan_hash: {report.query_plan_hash}",
        f"query_result_hash: {report.query_result_hash}",
        f"answer_hash: {report.answer_hash}",
        f"explainability_report_hash: {report.explainability_report_hash}",
        f"contradiction_report_hash: {report.contradiction_report_hash}",
        f"debate_report_hash: {report.debate_report_hash}",
        f"report_hash: {report.report_hash}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)
