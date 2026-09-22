from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_temporal_intelligence_timeline_reconstruction import (
    OracleTemporalEvidenceEvent,
    OracleTemporalTimelineInvariantError,
    build_temporal_intelligence_report,
    verify_temporal_intelligence_report,
)

SCHEMA_VERSION = "OIT-014"
ENGINE_ID = "OIT-014"
POLICY_ID = "oracle.cross-market-intelligence-relationship-analysis.v2"
IDENTITY_FIELDS = ("record_id", "market_id", "id", "prediction_id", "event_id", "contract_id")
ENTITY_FIELDS = ("entity", "entities", "subject", "subjects", "company", "companies", "asset", "assets", "team", "teams", "candidate", "candidates", "person", "people", "organization", "organizations", "ticker", "symbol", "league")
PROBABILITY_FIELDS = ("probability", "probability_yes", "yes_probability", "forecast_probability", "confidence", "score")
DIRECTION_FIELDS = ("stance", "direction", "signal", "side", "outlook", "bias")
TITLE_FIELDS = ("title", "name", "question", "market", "description")
LEAD_LAG_WINDOW_SECONDS = 604800
MAX_DEPTH = 12
MAX_ITEMS = 512


class OracleCrossMarketRelationshipInvariantError(OracleTemporalTimelineInvariantError):
    pass


@dataclass(frozen=True)
class OracleCrossMarketRecordProfile:
    profile_index: int
    evidence_index: int
    record_id: str
    title: str
    entities: tuple[str, ...]
    venue: str | None
    category: str | None
    probability: float | None
    direction: str | None
    timestamp_utc: str
    epoch_seconds: int
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    evidence_hash: str
    inspection_hash: str
    temporal_event_hash: str
    source_record_locator: str
    read_only: bool
    profile_hash: str


@dataclass(frozen=True)
class OracleCrossMarketRelationship:
    relationship_index: int
    left_profile_index: int
    right_profile_index: int
    left_record_id: str
    right_record_id: str
    shared_entities: tuple[str, ...]
    shared_entity_count: int
    elapsed_seconds: int
    temporal_relationship: str
    directional_relationship: str
    probability_distance: float | None
    evidence_dependence: str
    relationship_score: float
    relationship_strength: str
    rationale: tuple[str, ...]
    read_only: bool
    relationship_hash: str


@dataclass(frozen=True)
class OracleCrossMarketIntelligenceReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    answer_hash: str
    query_plan_hash: str
    query_result_hash: str
    temporal_report_hash: str
    profiles: tuple[OracleCrossMarketRecordProfile, ...]
    relationships: tuple[OracleCrossMarketRelationship, ...]
    profile_count: int
    relationship_count: int
    connected_profile_count: int
    independent_profile_count: int
    strong_relationship_count: int
    moderate_relationship_count: int
    weak_relationship_count: int
    lead_lag_relationship_count: int
    contradictory_direction_count: int
    relationship_state: str
    relationship_summary: str
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
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, Path):
        return value.as_posix()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _norm(value: Any) -> str:
    return " ".join(str(value).strip().lower().split())


def _display(value: Any) -> str:
    return " ".join(str(value).strip().split())


def _matches(record: Mapping[str, Any], record_id: str) -> bool:
    return any(field in record and str(record[field]).strip() == str(record_id).strip() for field in IDENTITY_FIELDS)


def _find_record(value: Any, record_id: str, path: str = "$", depth: int = 0):
    if depth >= MAX_DEPTH:
        return None
    if isinstance(value, Mapping):
        if _matches(value, record_id):
            return value, path
        for key, child in sorted(value.items(), key=lambda x: str(x[0])):
            if isinstance(child, (Mapping, list, tuple)):
                found = _find_record(child, record_id, f"{path}.{key}", depth + 1)
                if found is not None:
                    return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value[:MAX_ITEMS]):
            if isinstance(child, (Mapping, list, tuple)):
                found = _find_record(child, record_id, f"{path}[{index}]", depth + 1)
                if found is not None:
                    return found
    return None


def _load_record(root: Path, event: OracleTemporalEvidenceEvent):
    relative = Path(event.artifact_relative_path)
    if relative.is_absolute():
        raise OracleCrossMarketRelationshipInvariantError("absolute artifact path forbidden")
    artifact = (root / relative).resolve()
    try:
        artifact.relative_to(root)
    except ValueError as exc:
        raise OracleCrossMarketRelationshipInvariantError("artifact path escapes repository") from exc
    raw = artifact.read_bytes()
    if hashlib.sha256(raw).hexdigest() != event.artifact_sha256:
        raise OracleCrossMarketRelationshipInvariantError("certified artifact hash mismatch")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OracleCrossMarketRelationshipInvariantError("certified artifact is not JSON") from exc
    located = _find_record(payload, event.record_id)
    if located is None:
        raise OracleCrossMarketRelationshipInvariantError(f"certified record missing: {event.record_id}")
    return located


def _scalars(value: Any) -> tuple[str, ...]:
    output = []
    def visit(item: Any, depth: int = 0):
        if depth >= 4 or len(output) >= 64:
            return
        if isinstance(item, Mapping):
            for child in item.values():
                visit(child, depth + 1)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for child in item:
                visit(child, depth + 1)
        elif item is not None and not isinstance(item, bool):
            text = _display(item)
            if text:
                output.append(text)
    visit(value)
    return tuple(output)


def _entities(record: Mapping[str, Any]) -> tuple[str, ...]:
    found = {}
    for field in ENTITY_FIELDS + ("tags", "keywords", "labels"):
        if field in record:
            for value in _scalars(record[field]):
                found.setdefault(_norm(value), value)
    return tuple(found[key] for key in sorted(found))


def _first(record: Mapping[str, Any], fields: tuple[str, ...]) -> str | None:
    for field in fields:
        if field in record and record[field] is not None:
            text = _display(record[field])
            if text:
                return text
    return None


def _probability(record: Mapping[str, Any]) -> float | None:
    for field in PROBABILITY_FIELDS:
        if field not in record or isinstance(record[field], bool):
            continue
        try:
            value = float(record[field])
        except (TypeError, ValueError):
            continue
        if value > 1.0 and value <= 100.0:
            value /= 100.0
        if 0.0 <= value <= 1.0:
            return round(value, 12)
    return None


def _direction(value: str | None) -> str | None:
    if value is None:
        return None
    text = _norm(value)
    if text in {"bull", "bullish", "yes", "long", "up", "positive", "buy"}:
        return "positive"
    if text in {"bear", "bearish", "no", "short", "down", "negative", "sell"}:
        return "negative"
    if text in {"neutral", "mixed", "hold", "uncertain", "none"}:
        return "neutral"
    return text or None


def _profile(root: Path, event: OracleTemporalEvidenceEvent, index: int):
    record, locator = _load_record(root, event)
    body = {
        "profile_index": index,
        "evidence_index": event.evidence_index,
        "record_id": event.record_id,
        "title": _first(record, TITLE_FIELDS) or event.record_id,
        "entities": _entities(record),
        "venue": _first(record, ("venue", "exchange", "platform")),
        "category": _first(record, ("category", "topic", "sector")),
        "probability": _probability(record),
        "direction": _direction(_first(record, DIRECTION_FIELDS)),
        "timestamp_utc": event.timestamp_utc,
        "epoch_seconds": event.epoch_seconds,
        "artifact_relative_path": event.artifact_relative_path,
        "artifact_sha256": event.artifact_sha256,
        "record_hash": event.record_hash,
        "evidence_hash": event.evidence_hash,
        "inspection_hash": event.inspection_hash,
        "temporal_event_hash": event.event_hash,
        "source_record_locator": locator,
        "read_only": True,
    }
    profile = OracleCrossMarketRecordProfile(**body, profile_hash=_stable_hash(body))
    verify_cross_market_record_profile(profile)
    return profile


def verify_cross_market_record_profile(profile: OracleCrossMarketRecordProfile) -> bool:
    body = asdict(profile)
    supplied = body.pop("profile_hash")
    if _stable_hash(body) != supplied:
        raise OracleCrossMarketRelationshipInvariantError("profile hash mismatch")
    if not profile.read_only or profile.profile_index < 1:
        raise OracleCrossMarketRelationshipInvariantError("invalid profile")
    if len(profile.artifact_sha256) != 64:
        raise OracleCrossMarketRelationshipInvariantError(
            "profile artifact hash is incomplete"
        )
    if not (
        profile.record_hash
        and profile.evidence_hash
        and profile.inspection_hash
        and profile.temporal_event_hash
        and profile.source_record_locator
    ):
        raise OracleCrossMarketRelationshipInvariantError(
            "profile lineage is incomplete"
        )
    normalized_entities = tuple(_norm(value) for value in profile.entities)
    if len(normalized_entities) != len(set(normalized_entities)):
        raise OracleCrossMarketRelationshipInvariantError(
            "profile contains duplicate normalized entities"
        )
    return True


def _relationship(left, right, index):
    left_map = {_norm(v): v for v in left.entities}
    right_map = {_norm(v): v for v in right.entities}
    keys = sorted(set(left_map) & set(right_map))
    same_category = bool(
        left.category
        and right.category
        and _norm(left.category) == _norm(right.category)
    )
    same_venue = bool(
        left.venue
        and right.venue
        and _norm(left.venue) == _norm(right.venue)
    )

    # A venue match alone is operational context, not evidence that two
    # markets concern the same underlying subject. Category may support an
    # existing semantic link but cannot create one by itself.
    if not keys:
        return None
    shared = tuple(left_map[key] for key in keys)
    elapsed = right.epoch_seconds - left.epoch_seconds
    if elapsed == 0:
        temporal = "simultaneous"
    elif abs(elapsed) <= LEAD_LAG_WINDOW_SECONDS:
        temporal = "left_leads_right" if elapsed > 0 else "right_leads_left"
    else:
        temporal = "temporally_distant"
    if left.direction is None or right.direction is None:
        directional = "unknown"
    elif left.direction == right.direction:
        directional = "aligned"
    elif {left.direction, right.direction} == {"positive", "negative"}:
        directional = "contradictory"
    elif "neutral" in {left.direction, right.direction}:
        directional = "neutral_or_mixed"
    else:
        directional = "different"
    distance = round(abs(left.probability - right.probability), 12) if left.probability is not None and right.probability is not None else None
    score = min(
        1.0,
        len(shared) * 0.25
        + (0.15 if directional in {"aligned", "contradictory"} else 0.05)
        + (0.15 if temporal != "temporally_distant" else 0.0)
        + (
            0.15 * (1.0 - distance)
            if distance is not None
            else 0.0
        )
        + (0.08 if same_category else 0.0)
        + (0.02 if same_venue else 0.0),
    )
    score = round(score, 6)
    strength = "strong" if score >= 0.72 else "moderate" if score >= 0.45 else "weak"
    rationale = []
    if shared:
        rationale.append("shared entities: " + ", ".join(shared))
    if same_category:
        rationale.append("same category")
    if same_venue:
        rationale.append("same venue context")
    rationale.append(f"temporal relationship: {temporal}")
    rationale.append(f"directional relationship: {directional}")
    if distance is not None:
        rationale.append(f"probability distance: {distance:.6f}")
    body = {
        "relationship_index": index,
        "left_profile_index": left.profile_index,
        "right_profile_index": right.profile_index,
        "left_record_id": left.record_id,
        "right_record_id": right.record_id,
        "shared_entities": shared,
        "shared_entity_count": len(shared),
        "elapsed_seconds": elapsed,
        "temporal_relationship": temporal,
        "directional_relationship": directional,
        "probability_distance": distance,
        "evidence_dependence": "potentially_dependent",
        "relationship_score": score,
        "relationship_strength": strength,
        "rationale": tuple(rationale),
        "read_only": True,
    }
    relationship = OracleCrossMarketRelationship(**body, relationship_hash=_stable_hash(body))
    verify_cross_market_relationship(relationship)
    return relationship


def verify_cross_market_relationship(relationship: OracleCrossMarketRelationship) -> bool:
    body = asdict(relationship)
    supplied = body.pop("relationship_hash")
    if _stable_hash(body) != supplied:
        raise OracleCrossMarketRelationshipInvariantError("relationship hash mismatch")
    if not relationship.read_only or relationship.left_profile_index >= relationship.right_profile_index:
        raise OracleCrossMarketRelationshipInvariantError("invalid relationship")
    if relationship.shared_entity_count != len(relationship.shared_entities):
        raise OracleCrossMarketRelationshipInvariantError("shared entity count mismatch")
    return True


def build_cross_market_intelligence_report(*, repository_root: Path, query: str, result_limit: int = 10):
    root = repository_root.resolve()
    temporal = build_temporal_intelligence_report(repository_root=root, query=query, result_limit=result_limit)
    verify_temporal_intelligence_report(temporal)
    profiles = tuple(_profile(root, event, index) for index, event in enumerate(temporal.events, start=1))
    relationships_list = []
    for left_index in range(len(profiles)):
        for right_index in range(left_index + 1, len(profiles)):
            item = _relationship(profiles[left_index], profiles[right_index], len(relationships_list) + 1)
            if item is not None:
                relationships_list.append(item)
    relationships = tuple(relationships_list)
    connected = {index for item in relationships for index in (item.left_profile_index, item.right_profile_index)}
    strong = sum(item.relationship_strength == "strong" for item in relationships)
    moderate = sum(item.relationship_strength == "moderate" for item in relationships)
    weak = sum(item.relationship_strength == "weak" for item in relationships)
    lead_lag = sum(item.temporal_relationship in {"left_leads_right", "right_leads_left"} for item in relationships)
    contradictions = sum(item.directional_relationship == "contradictory" for item in relationships)
    if not profiles:
        state = "no_cross_market_evidence"
        summary = "Oracle found no timestamped records to compare."
    elif not relationships:
        state = "independent_market_evidence"
        summary = f"Oracle profiled {len(profiles)} record(s) without a shared relationship."
    elif strong:
        state = "strong_cross_market_relationships"
        summary = f"Oracle found {len(relationships)} relationship(s), including {strong} strong relationship(s)."
    else:
        state = "cross_market_relationships_detected"
        summary = f"Oracle found {len(relationships)} relationship(s) across {len(connected)} profile(s)."
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "cross_market_relationships_analyzed" if profiles else "cross_market_analysis_limited",
        "repository_root": root.as_posix(),
        "query": temporal.query,
        "answer_hash": temporal.answer_hash,
        "query_plan_hash": temporal.query_plan_hash,
        "query_result_hash": temporal.query_result_hash,
        "temporal_report_hash": temporal.report_hash,
        "profiles": profiles,
        "relationships": relationships,
        "profile_count": len(profiles),
        "relationship_count": len(relationships),
        "connected_profile_count": len(connected),
        "independent_profile_count": len(profiles) - len(connected),
        "strong_relationship_count": strong,
        "moderate_relationship_count": moderate,
        "weak_relationship_count": weak,
        "lead_lag_relationship_count": lead_lag,
        "contradictory_direction_count": contradictions,
        "relationship_state": state,
        "relationship_summary": summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": temporal.failure_reason,
    }
    report = OracleCrossMarketIntelligenceReport(**body, report_hash=_stable_hash(body))
    verify_cross_market_intelligence_report(report)
    return report


def verify_cross_market_intelligence_report(report: OracleCrossMarketIntelligenceReport) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleCrossMarketRelationshipInvariantError("OIT-014 report hash mismatch")
    for profile in report.profiles:
        verify_cross_market_record_profile(profile)
    for relationship in report.relationships:
        verify_cross_market_relationship(relationship)
    if report.profile_count != len(report.profiles) or report.relationship_count != len(report.relationships):
        raise OracleCrossMarketRelationshipInvariantError("report count mismatch")
    if report.connected_profile_count + report.independent_profile_count != report.profile_count:
        raise OracleCrossMarketRelationshipInvariantError("connectivity accounting mismatch")
    if not report.read_only or report.analytics_execution_performed or report.database_access_performed or report.publication_allowed or report.qseries_execution_allowed:
        raise OracleCrossMarketRelationshipInvariantError("unsafe OIT-014 boundary")
    return True


def cross_market_intelligence_lines(report: OracleCrossMarketIntelligenceReport) -> tuple[str, ...]:
    verify_cross_market_intelligence_report(report)
    lines = [
        "ORACLE CROSS-MARKET INTELLIGENCE",
        f"query: {report.query}",
        f"relationship_state: {report.relationship_state}",
        f"profile_count: {report.profile_count}",
        f"relationship_count: {report.relationship_count}",
        f"connected_profile_count: {report.connected_profile_count}",
        f"independent_profile_count: {report.independent_profile_count}",
        f"strong_relationship_count: {report.strong_relationship_count}",
        f"lead_lag_relationship_count: {report.lead_lag_relationship_count}",
        f"contradictory_direction_count: {report.contradictory_direction_count}",
        f"summary: {report.relationship_summary}",
    ]
    for profile in report.profiles:
        lines.extend((f"[P{profile.profile_index}] {profile.record_id}", f"    title: {profile.title}", f"    entities: {', '.join(profile.entities) or 'none'}", f"    timestamp_utc: {profile.timestamp_utc}", f"    direction: {profile.direction or 'unknown'}", f"    probability: {profile.probability if profile.probability is not None else 'unknown'}"))
    if not report.relationships:
        lines.append("relationships: none")
    for item in report.relationships:
        lines.extend((f"[R{item.relationship_index}] {item.left_record_id} <-> {item.right_record_id}", f"    shared_entities: {', '.join(item.shared_entities) or 'none'}", f"    temporal_relationship: {item.temporal_relationship}", f"    directional_relationship: {item.directional_relationship}", f"    relationship_score: {item.relationship_score:.6f}", f"    relationship_strength: {item.relationship_strength}", f"    relationship_hash: {item.relationship_hash}"))
    lines.extend((f"temporal_report_hash: {report.temporal_report_hash}", f"report_hash: {report.report_hash}", "analytics_execution_performed: false", "database_access_performed: false", "publication_allowed: false", "qseries_execution_allowed: false", "read_only: true"))
    return tuple(lines)
