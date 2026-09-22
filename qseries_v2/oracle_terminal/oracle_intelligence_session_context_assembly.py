from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_certified_real_intelligence_source_envelope import (
    OracleRealIntelligenceSourceEnvelope,
    verify_real_intelligence_source_envelope,
)
from .oracle_certified_real_intelligence_normalization import (
    OracleNormalizedIntelligenceField,
    OracleNormalizedIntelligenceRecord,
    OracleRealIntelligenceNormalizationInvariantError,
    OracleRealIntelligenceNormalizationReport,
    verify_normalized_field,
    verify_normalized_record,
    verify_real_intelligence_normalization_report,
)

SCHEMA_VERSION = "OIT-040"
ENGINE_ID = "OIT-040"
POLICY_ID = "oracle.intelligence-session-context-assembly.v1"

CONTEXT_FIELD_LIMIT = 4096


class OracleIntelligenceSessionContextInvariantError(
    OracleRealIntelligenceNormalizationInvariantError
):
    pass


@dataclass(frozen=True)
class OracleIntelligenceContextField:
    context_key: str
    source_field_path: str
    source_field_hash: str
    field_type: str
    canonical_value: Any
    searchable_text: str
    ordinal: int
    context_field_hash: str


@dataclass(frozen=True)
class OracleIntelligenceSessionContext:
    context_id: str
    source_normalization_report_hash: str
    source_normalized_record_hash: str
    source_envelope_hash: str
    source_execution_report_hash: str
    source_validation_report_hash: str
    source_invocation_result_hash: str
    context_fields: tuple[OracleIntelligenceContextField, ...]
    context_field_count: int
    searchable_field_count: int
    root_field_present: bool
    deterministic_ordering_applied: bool
    full_lineage_preserved: bool
    bounded_context: bool
    context_ready: bool
    read_only: bool
    context_hash: str


@dataclass(frozen=True)
class OracleIntelligenceSessionContextAssemblyReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    normalization_report_hash: str
    session_context: OracleIntelligenceSessionContext
    context_assembled: bool
    query_planning_ready: bool
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
    raise OracleIntelligenceSessionContextInvariantError(
        f"unsupported context value type: "
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


def _searchable_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def _context_key(field_path: str) -> str:
    if field_path == "$":
        return "root"
    value = field_path[2:] if field_path.startswith("$.") else field_path
    value = value.replace("[", ".").replace("]", "")
    pieces = [
        piece.strip().lower()
        for piece in value.split(".")
        if piece.strip()
    ]
    return ".".join(pieces)


def _assemble_context_field(
    field: OracleNormalizedIntelligenceField,
    ordinal: int,
) -> OracleIntelligenceContextField:
    verify_normalized_field(field)
    body = {
        "context_key": _context_key(field.field_path),
        "source_field_path": field.field_path,
        "source_field_hash": field.field_hash,
        "field_type": field.field_type,
        "canonical_value": field.canonical_value,
        "searchable_text": _searchable_text(field.canonical_value),
        "ordinal": ordinal,
    }
    context_field = OracleIntelligenceContextField(
        **body,
        context_field_hash=_stable_hash(body),
    )
    verify_context_field(context_field)
    return context_field


def verify_context_field(
    field: OracleIntelligenceContextField,
) -> bool:
    body = asdict(field)
    supplied = body.pop("context_field_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceSessionContextInvariantError(
            "context field hash mismatch"
        )
    if not field.context_key:
        raise OracleIntelligenceSessionContextInvariantError(
            "context field key missing"
        )
    if not field.source_field_path or not field.source_field_hash:
        raise OracleIntelligenceSessionContextInvariantError(
            "context field lineage missing"
        )
    if field.ordinal < 0:
        raise OracleIntelligenceSessionContextInvariantError(
            "context field ordinal invalid"
        )
    return True


def verify_session_context(
    context: OracleIntelligenceSessionContext,
) -> bool:
    body = asdict(context)
    supplied = body.pop("context_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context hash mismatch"
        )
    if not context.context_id:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context ID missing"
        )
    if context.context_field_count != len(context.context_fields):
        raise OracleIntelligenceSessionContextInvariantError(
            "session context field count mismatch"
        )
    for index, field in enumerate(context.context_fields):
        verify_context_field(field)
        if field.ordinal != index:
            raise OracleIntelligenceSessionContextInvariantError(
                "session context field ordering mismatch"
            )
    if context.searchable_field_count != sum(
        bool(field.searchable_text)
        for field in context.context_fields
    ):
        raise OracleIntelligenceSessionContextInvariantError(
            "searchable field count mismatch"
        )
    if context.root_field_present != any(
        field.source_field_path == "$"
        for field in context.context_fields
    ):
        raise OracleIntelligenceSessionContextInvariantError(
            "root field presence mismatch"
        )
    if not context.deterministic_ordering_applied:
        raise OracleIntelligenceSessionContextInvariantError(
            "deterministic context ordering not applied"
        )
    if not context.full_lineage_preserved:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context lineage incomplete"
        )
    if context.bounded_context != (
        context.context_field_count <= CONTEXT_FIELD_LIMIT
    ):
        raise OracleIntelligenceSessionContextInvariantError(
            "bounded context state mismatch"
        )
    expected_ready = bool(
        context.context_fields
        and context.root_field_present
        and context.deterministic_ordering_applied
        and context.full_lineage_preserved
        and context.bounded_context
        and context.read_only
    )
    if context.context_ready != expected_ready:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context readiness mismatch"
        )
    return True


def build_intelligence_session_context_assembly_report(
    repository_root: str | Path,
    *,
    normalization_report: OracleRealIntelligenceNormalizationReport,
) -> OracleIntelligenceSessionContextAssemblyReport:
    root = Path(repository_root).resolve()
    verify_real_intelligence_normalization_report(
        normalization_report
    )

    if not normalization_report.normalized_record_available:
        raise OracleIntelligenceSessionContextInvariantError(
            normalization_report.failure_reason
            or "normalized record unavailable"
        )

    record: OracleNormalizedIntelligenceRecord = (
        normalization_report.normalized_record
    )
    verify_normalized_record(record)

    ordered_fields = tuple(
        sorted(
            record.normalized_fields,
            key=lambda field: (
                field.field_path,
                field.field_hash,
            ),
        )
    )
    context_fields = tuple(
        _assemble_context_field(field, index)
        for index, field in enumerate(ordered_fields)
    )

    lineage_preserved = bool(
        record.source_envelope_hash
        == normalization_report.source_envelope_hash
        and all(
            field.source_envelope_hash
            == record.source_envelope_hash
            for field in record.normalized_fields
        )
        and all(
            context_field.source_field_hash
            == normalized_field.field_hash
            for context_field, normalized_field in zip(
                context_fields,
                ordered_fields,
            )
        )
    )

    context_body = {
        "context_id": _stable_hash(
            {
                "normalization_report_hash": (
                    normalization_report.report_hash
                ),
                "normalized_record_hash": record.record_hash,
                "context_fields": context_fields,
            }
        )[:24],
        "source_normalization_report_hash": (
            normalization_report.report_hash
        ),
        "source_normalized_record_hash": record.record_hash,
        "source_envelope_hash": record.source_envelope_hash,
        "source_execution_report_hash": (
            record.source_execution_report_hash
        ),
        "source_validation_report_hash": (
            record.source_validation_report_hash
        ),
        "source_invocation_result_hash": (
            record.source_invocation_result_hash
        ),
        "context_fields": context_fields,
        "context_field_count": len(context_fields),
        "searchable_field_count": sum(
            bool(field.searchable_text)
            for field in context_fields
        ),
        "root_field_present": any(
            field.source_field_path == "$"
            for field in context_fields
        ),
        "deterministic_ordering_applied": True,
        "full_lineage_preserved": lineage_preserved,
        "bounded_context": len(context_fields) <= CONTEXT_FIELD_LIMIT,
        "context_ready": bool(
            context_fields
            and lineage_preserved
            and len(context_fields) <= CONTEXT_FIELD_LIMIT
            and any(
                field.source_field_path == "$"
                for field in context_fields
            )
        ),
        "read_only": True,
    }
    context = OracleIntelligenceSessionContext(
        **context_body,
        context_hash=_stable_hash(context_body),
    )
    verify_session_context(context)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "normalization_report_hash": (
            normalization_report.report_hash
        ),
        "session_context": context,
        "context_assembled": context.context_ready,
        "query_planning_ready": context.context_ready,
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
            None if context.context_ready
            else "session_context_not_ready"
        ),
    }
    report = OracleIntelligenceSessionContextAssemblyReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_intelligence_session_context_assembly_report(report)
    return report


def verify_intelligence_session_context_assembly_report(
    report: OracleIntelligenceSessionContextAssemblyReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context assembly report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context policy mismatch"
        )
    verify_session_context(report.session_context)
    if not report.read_only:
        raise OracleIntelligenceSessionContextInvariantError(
            "session context report is not read-only"
        )
    if (
        report.multi_turn_memory_enabled
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
        raise OracleIntelligenceSessionContextInvariantError(
            "forbidden context capability enabled"
        )
    expected = bool(
        report.session_context.context_ready
        and report.session_context.full_lineage_preserved
        and report.session_context.bounded_context
    )
    if report.context_assembled != expected:
        raise OracleIntelligenceSessionContextInvariantError(
            "context assembly state mismatch"
        )
    if report.query_planning_ready != expected:
        raise OracleIntelligenceSessionContextInvariantError(
            "query planning readiness mismatch"
        )
    return True
