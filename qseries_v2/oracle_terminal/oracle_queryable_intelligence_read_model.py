from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .oracle_genuine_intelligence_read_only_consumption import (
    IntelligenceArtifactView,
    OracleIntelligenceConsumptionInvariantError,
    consume_admitted_intelligence,
    select_intelligence_artifact,
    verify_intelligence_artifact_view,
    verify_intelligence_consumption,
)

SCHEMA_VERSION = "OIT-007"
ENGINE_ID = "OIT-007"
POLICY_ID = "oracle.queryable-intelligence-read-model.v1"

MAX_RECORDS_PER_ARTIFACT = 5000
MAX_FIELD_DEPTH = 8
RECORD_CONTAINER_KEYS = (
    "records",
    "items",
    "results",
    "artifacts",
    "candidates",
    "markets",
    "predictions",
    "intelligence",
    "entries",
)


class OracleQueryableIntelligenceInvariantError(
    OracleIntelligenceConsumptionInvariantError
):
    pass


@dataclass(frozen=True)
class QueryableIntelligenceRecord:
    global_record_index: int
    artifact_index: int
    artifact_relative_path: str
    artifact_sha256: str
    local_record_index: int
    record_id: str
    payload: Any
    field_paths: tuple[str, ...]
    searchable_text: str
    read_only: bool
    record_hash: str


@dataclass(frozen=True)
class QueryableIntelligenceArtifact:
    artifact_index: int
    relative_path: str
    sha256: str
    source_payload_kind: str
    source_record_count: int
    normalized_record_count: int
    record_container: str
    field_paths: tuple[str, ...]
    read_only: bool
    artifact_model_hash: str


@dataclass(frozen=True)
class OracleQueryableIntelligenceReadModel:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    artifacts: tuple[QueryableIntelligenceArtifact, ...]
    records: tuple[QueryableIntelligenceRecord, ...]
    artifact_count: int
    record_count: int
    query_ready: bool
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    failure_reason: str | None
    model_hash: str


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


def _flatten_field_paths(
    value: Any,
    *,
    prefix: str = "",
    depth: int = 0,
) -> tuple[str, ...]:
    if depth >= MAX_FIELD_DEPTH:
        return (prefix or "$",)

    paths: set[str] = set()

    if isinstance(value, Mapping):
        if not value:
            paths.add(prefix or "$")
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            paths.update(
                _flatten_field_paths(
                    item,
                    prefix=child,
                    depth=depth + 1,
                )
            )
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        if not value:
            paths.add(prefix or "$")
        else:
            child = f"{prefix}[]" if prefix else "[]"
            for item in list(value)[:25]:
                paths.update(
                    _flatten_field_paths(
                        item,
                        prefix=child,
                        depth=depth + 1,
                    )
                )
    else:
        paths.add(prefix or "$")

    return tuple(sorted(paths))


def _searchable_text(value: Any) -> str:
    parts: list[str] = []

    def visit(item: Any, depth: int = 0) -> None:
        if depth >= MAX_FIELD_DEPTH:
            return
        if isinstance(item, Mapping):
            for key, value in sorted(item.items(), key=lambda pair: str(pair[0])):
                parts.append(str(key))
                visit(value, depth + 1)
        elif isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            for value in list(item)[:100]:
                visit(value, depth + 1)
        elif item is not None:
            parts.append(str(item))

    visit(value)
    return " ".join(parts).lower()


def _extract_records(payload: Any) -> tuple[str, tuple[Any, ...]]:
    if isinstance(payload, Mapping):
        for key in RECORD_CONTAINER_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return key, tuple(value[:MAX_RECORDS_PER_ARTIFACT])
        return "$", (payload,)
    if isinstance(payload, list):
        return "$", tuple(payload[:MAX_RECORDS_PER_ARTIFACT])
    return "$", (payload,)


def _record_id(
    *,
    artifact_sha256: str,
    local_index: int,
    payload: Any,
) -> str:
    if isinstance(payload, Mapping):
        for key in (
            "record_id",
            "artifact_id",
            "market_id",
            "prediction_id",
            "candidate_id",
            "id",
            "ticker",
            "symbol",
            "slug",
        ):
            value = payload.get(key)
            if value not in (None, ""):
                return str(value)
    return f"{artifact_sha256[:16]}:{local_index}"


def _build_record(
    *,
    global_index: int,
    artifact: IntelligenceArtifactView,
    local_index: int,
    payload: Any,
) -> QueryableIntelligenceRecord:
    body = {
        "global_record_index": global_index,
        "artifact_index": artifact.artifact_index,
        "artifact_relative_path": artifact.relative_path,
        "artifact_sha256": artifact.sha256,
        "local_record_index": local_index,
        "record_id": _record_id(
            artifact_sha256=artifact.sha256,
            local_index=local_index,
            payload=payload,
        ),
        "payload": _canonical(payload),
        "field_paths": _flatten_field_paths(payload),
        "searchable_text": _searchable_text(payload),
        "read_only": True,
    }
    return QueryableIntelligenceRecord(
        **body,
        record_hash=_stable_hash(body),
    )


def _build_artifact_model(
    *,
    artifact: IntelligenceArtifactView,
    records: tuple[QueryableIntelligenceRecord, ...],
    container: str,
) -> QueryableIntelligenceArtifact:
    fields: set[str] = set()
    for record in records:
        fields.update(record.field_paths)
    body = {
        "artifact_index": artifact.artifact_index,
        "relative_path": artifact.relative_path,
        "sha256": artifact.sha256,
        "source_payload_kind": artifact.payload_kind,
        "source_record_count": artifact.record_count,
        "normalized_record_count": len(records),
        "record_container": container,
        "field_paths": tuple(sorted(fields)),
        "read_only": True,
    }
    return QueryableIntelligenceArtifact(
        **body,
        artifact_model_hash=_stable_hash(body),
    )


def verify_queryable_record(
    record: QueryableIntelligenceRecord,
) -> bool:
    body = asdict(record)
    supplied = body.pop("record_hash")
    if _stable_hash(body) != supplied:
        raise OracleQueryableIntelligenceInvariantError(
            "OIT-007 record hash mismatch"
        )
    if not record.read_only:
        raise OracleQueryableIntelligenceInvariantError(
            "queryable record is not read-only"
        )
    if record.global_record_index < 1 or record.local_record_index < 1:
        raise OracleQueryableIntelligenceInvariantError(
            "invalid record index"
        )
    return True


def verify_queryable_artifact(
    artifact: QueryableIntelligenceArtifact,
) -> bool:
    body = asdict(artifact)
    supplied = body.pop("artifact_model_hash")
    if _stable_hash(body) != supplied:
        raise OracleQueryableIntelligenceInvariantError(
            "OIT-007 artifact model hash mismatch"
        )
    if not artifact.read_only:
        raise OracleQueryableIntelligenceInvariantError(
            "queryable artifact is not read-only"
        )
    return True


def build_queryable_intelligence_read_model(
    *,
    repository_root: Path,
) -> OracleQueryableIntelligenceReadModel:
    root = repository_root.resolve()
    consumption = consume_admitted_intelligence(
        repository_root=root
    )
    verify_intelligence_consumption(consumption)

    artifact_models: list[QueryableIntelligenceArtifact] = []
    all_records: list[QueryableIntelligenceRecord] = []
    global_index = 1

    if consumption.terminal_consumption_ready:
        for artifact in consumption.artifacts:
            verify_intelligence_artifact_view(artifact)
            container, raw_records = _extract_records(artifact.preview)
            artifact_records: list[QueryableIntelligenceRecord] = []
            for local_index, payload in enumerate(raw_records, start=1):
                record = _build_record(
                    global_index=global_index,
                    artifact=artifact,
                    local_index=local_index,
                    payload=payload,
                )
                verify_queryable_record(record)
                artifact_records.append(record)
                all_records.append(record)
                global_index += 1
            artifact_model = _build_artifact_model(
                artifact=artifact,
                records=tuple(artifact_records),
                container=container,
            )
            verify_queryable_artifact(artifact_model)
            artifact_models.append(artifact_model)

    ready = bool(
        consumption.terminal_consumption_ready
        and artifact_models
        and all_records
    )
    failure = consumption.failure_reason
    if not ready and failure is None:
        failure = "no genuine intelligence records were normalized"

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "queryable_intelligence_read_model_ready"
            if ready
            else "queryable_intelligence_read_model_blocked"
        ),
        "repository_root": root.as_posix(),
        "artifacts": tuple(artifact_models),
        "records": tuple(all_records),
        "artifact_count": len(artifact_models),
        "record_count": len(all_records),
        "query_ready": ready,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": failure,
    }
    model = OracleQueryableIntelligenceReadModel(
        **body,
        model_hash=_stable_hash(body),
    )
    verify_queryable_intelligence_read_model(model)
    return model


def verify_queryable_intelligence_read_model(
    model: OracleQueryableIntelligenceReadModel,
) -> bool:
    body = asdict(model)
    supplied = body.pop("model_hash")
    if _stable_hash(body) != supplied:
        raise OracleQueryableIntelligenceInvariantError(
            "OIT-007 read model hash mismatch"
        )
    if not model.read_only:
        raise OracleQueryableIntelligenceInvariantError(
            "OIT-007 is not read-only"
        )
    if model.analytics_execution_performed:
        raise OracleQueryableIntelligenceInvariantError(
            "analytics execution occurred"
        )
    if model.database_access_performed:
        raise OracleQueryableIntelligenceInvariantError(
            "database access occurred"
        )
    if model.publication_allowed or model.qseries_execution_allowed:
        raise OracleQueryableIntelligenceInvariantError(
            "unsafe query boundary"
        )
    for artifact in model.artifacts:
        verify_queryable_artifact(artifact)
    for record in model.records:
        verify_queryable_record(record)
    if model.query_ready:
        if not model.artifacts or not model.records:
            raise OracleQueryableIntelligenceInvariantError(
                "query-ready model lacks artifacts or records"
            )
        if model.artifact_count != len(model.artifacts):
            raise OracleQueryableIntelligenceInvariantError(
                "artifact count mismatch"
            )
        if model.record_count != len(model.records):
            raise OracleQueryableIntelligenceInvariantError(
                "record count mismatch"
            )
    return True


def search_queryable_records(
    model: OracleQueryableIntelligenceReadModel,
    *,
    query: str,
) -> tuple[QueryableIntelligenceRecord, ...]:
    verify_queryable_intelligence_read_model(model)
    normalized = " ".join(query.lower().split())
    if not normalized:
        raise OracleQueryableIntelligenceInvariantError(
            "search query is required"
        )
    terms = tuple(part for part in normalized.split(" ") if part)
    return tuple(
        record
        for record in model.records
        if all(term in record.searchable_text for term in terms)
    )


def select_queryable_record(
    model: OracleQueryableIntelligenceReadModel,
    *,
    selector: str,
) -> QueryableIntelligenceRecord:
    verify_queryable_intelligence_read_model(model)
    normalized = selector.strip()
    if not normalized:
        raise OracleQueryableIntelligenceInvariantError(
            "record selector is required"
        )
    if normalized.isdigit():
        index = int(normalized)
        for record in model.records:
            if record.global_record_index == index:
                return record
    for record in model.records:
        if record.record_id == normalized:
            return record
    raise OracleQueryableIntelligenceInvariantError(
        f"queryable record not found: {selector}"
    )


def queryable_intelligence_status_lines(
    model: OracleQueryableIntelligenceReadModel,
) -> tuple[str, ...]:
    verify_queryable_intelligence_read_model(model)
    return (
        "ORACLE QUERYABLE INTELLIGENCE READ MODEL",
        f"artifact_count: {model.artifact_count}",
        f"record_count: {model.record_count}",
        f"query_ready: {str(model.query_ready).lower()}",
        f"failure_reason: {model.failure_reason or 'none'}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    )


def queryable_schema_lines(
    model: OracleQueryableIntelligenceReadModel,
) -> tuple[str, ...]:
    verify_queryable_intelligence_read_model(model)
    lines = [
        "ORACLE QUERYABLE INTELLIGENCE SCHEMA",
        f"artifact_count: {model.artifact_count}",
    ]
    if not model.artifacts:
        lines.append("artifacts: none")
    for artifact in model.artifacts:
        lines.extend((
            f"[{artifact.artifact_index}] {artifact.relative_path}",
            f"    record_container: {artifact.record_container}",
            f"    normalized_record_count: {artifact.normalized_record_count}",
            f"    field_paths: {', '.join(artifact.field_paths) or 'none'}",
        ))
    lines.append("read_only: true")
    return tuple(lines)


def queryable_record_inventory_lines(
    records: tuple[QueryableIntelligenceRecord, ...],
    *,
    heading: str = "ORACLE QUERYABLE INTELLIGENCE RECORDS",
) -> tuple[str, ...]:
    lines = [heading, f"record_count: {len(records)}"]
    if not records:
        lines.append("records: none")
    for record in records:
        lines.extend((
            f"[{record.global_record_index}] {record.record_id}",
            f"    artifact: {record.artifact_relative_path}",
            f"    local_record_index: {record.local_record_index}",
            f"    field_paths: {', '.join(record.field_paths) or 'none'}",
        ))
    lines.append("read_only: true")
    return tuple(lines)


def queryable_record_lines(
    record: QueryableIntelligenceRecord,
) -> tuple[str, ...]:
    verify_queryable_record(record)
    payload = json.dumps(
        _canonical(record.payload),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    return (
        "ORACLE QUERYABLE INTELLIGENCE RECORD",
        f"global_record_index: {record.global_record_index}",
        f"record_id: {record.record_id}",
        f"artifact_index: {record.artifact_index}",
        f"artifact_path: {record.artifact_relative_path}",
        f"artifact_sha256: {record.artifact_sha256}",
        f"local_record_index: {record.local_record_index}",
        f"field_paths: {', '.join(record.field_paths) or 'none'}",
        "payload:",
        payload,
        "read_only: true",
    )
