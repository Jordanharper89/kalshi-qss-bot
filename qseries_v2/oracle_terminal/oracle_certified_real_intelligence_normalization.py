from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_certified_real_intelligence_source_envelope import (
    OracleRealIntelligenceSourceEnvelope,
    OracleRealIntelligenceSourceEnvelopeInvariantError,
    build_real_intelligence_source_envelope,
    verify_real_intelligence_source_envelope,
)

SCHEMA_VERSION = "OIT-039"
ENGINE_ID = "OIT-039"
POLICY_ID = "oracle.certified-real-intelligence-normalization.v2"


class OracleRealIntelligenceNormalizationInvariantError(
    OracleRealIntelligenceSourceEnvelopeInvariantError
):
    pass


@dataclass(frozen=True)
class OracleNormalizedIntelligenceField:
    field_path: str
    field_name: str
    field_type: str
    canonical_value: Any
    source_result_hash: str
    source_envelope_hash: str
    field_hash: str


@dataclass(frozen=True)
class OracleNormalizedIntelligenceRecord:
    record_id: str
    source_execution_report_hash: str
    source_validation_report_hash: str
    source_envelope_hash: str
    source_invocation_result_hash: str
    normalized_fields: tuple[OracleNormalizedIntelligenceField, ...]
    normalized_field_count: int
    root_type: str
    lossy_coercion_performed: bool
    source_structure_preserved: bool
    deterministic_ordering_applied: bool
    normalization_complete: bool
    record_hash: str


@dataclass(frozen=True)
class OracleRealIntelligenceNormalizationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    source_envelope_hash: str
    normalized_record: OracleNormalizedIntelligenceRecord
    normalized_record_available: bool
    source_result_preserved: bool
    source_response_modified: bool
    lossy_coercion_performed: bool
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
    raise OracleRealIntelligenceNormalizationInvariantError(
        f"unsupported normalization type: "
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


def _field_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, Mapping):
        return "mapping"
    if isinstance(value, (list, tuple)):
        return "sequence"
    raise OracleRealIntelligenceNormalizationInvariantError(
        "unsupported normalized field type"
    )


def _flatten(
    value: Any,
    *,
    path: str,
    name: str,
    envelope: OracleRealIntelligenceSourceEnvelope,
    output: list[OracleNormalizedIntelligenceField],
) -> None:
    canonical_value = _canonical(value)
    body = {
        "field_path": path,
        "field_name": name,
        "field_type": _field_type(value),
        "canonical_value": canonical_value,
        "source_result_hash": envelope.invocation_result_hash,
        "source_envelope_hash": envelope.envelope_hash,
    }
    field = OracleNormalizedIntelligenceField(
        **body,
        field_hash=_stable_hash(body),
    )
    verify_normalized_field(field)
    output.append(field)

    if isinstance(value, Mapping):
        for key in sorted(value, key=lambda item: str(item)):
            text = str(key)
            _flatten(
                value[key],
                path=f"{path}.{text}",
                name=text,
                envelope=envelope,
                output=output,
            )
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _flatten(
                item,
                path=f"{path}[{index}]",
                name=str(index),
                envelope=envelope,
                output=output,
            )


def verify_normalized_field(
    field: OracleNormalizedIntelligenceField,
) -> bool:
    body = asdict(field)
    supplied = body.pop("field_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalized field hash mismatch"
        )
    if not field.field_path or not field.field_name:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalized field identity missing"
        )
    if not field.source_result_hash or not field.source_envelope_hash:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalized field lineage missing"
        )
    return True


def verify_normalized_record(
    record: OracleNormalizedIntelligenceRecord,
) -> bool:
    body = asdict(record)
    supplied = body.pop("record_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalized record hash mismatch"
        )
    if record.normalized_field_count != len(record.normalized_fields):
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalized field count mismatch"
        )
    for field in record.normalized_fields:
        verify_normalized_field(field)
    if record.lossy_coercion_performed:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "lossy coercion is forbidden"
        )
    if not record.source_structure_preserved:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "source structure was not preserved"
        )
    if not record.deterministic_ordering_applied:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "deterministic ordering not applied"
        )
    expected = bool(
        record.normalized_fields
        and not record.lossy_coercion_performed
        and record.source_structure_preserved
        and record.deterministic_ordering_applied
    )
    if record.normalization_complete != expected:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization completion mismatch"
        )
    return True


def build_real_intelligence_normalization_report(
    repository_root: str | Path,
    *,
    source_envelope: OracleRealIntelligenceSourceEnvelope,
) -> OracleRealIntelligenceNormalizationReport:
    root = Path(repository_root).resolve()
    verify_real_intelligence_source_envelope(source_envelope)

    if not source_envelope.execution_validation_lineage_verified:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "source envelope lineage is not verified"
        )

    fields: list[OracleNormalizedIntelligenceField] = []
    _flatten(
        source_envelope.canonical_result,
        path="$",
        name="$",
        envelope=source_envelope,
        output=fields,
    )

    preserved = bool(
        _stable_hash(source_envelope.canonical_result)
        == source_envelope.canonical_result_hash
        == source_envelope.invocation_result_hash
    )

    record_body = {
        "record_id": _stable_hash(
            {
                "source_envelope_hash": source_envelope.envelope_hash,
                "normalized_fields": fields,
            }
        )[:24],
        "source_execution_report_hash": (
            source_envelope.execution_report_hash
        ),
        "source_validation_report_hash": (
            source_envelope.validation_report_hash
        ),
        "source_envelope_hash": source_envelope.envelope_hash,
        "source_invocation_result_hash": (
            source_envelope.invocation_result_hash
        ),
        "normalized_fields": tuple(fields),
        "normalized_field_count": len(fields),
        "root_type": (
            f"{type(source_envelope.canonical_result).__module__}."
            f"{type(source_envelope.canonical_result).__qualname__}"
        ),
        "lossy_coercion_performed": False,
        "source_structure_preserved": preserved,
        "deterministic_ordering_applied": True,
        "normalization_complete": bool(fields and preserved),
    }
    record = OracleNormalizedIntelligenceRecord(
        **record_body,
        record_hash=_stable_hash(record_body),
    )
    verify_normalized_record(record)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "source_envelope_hash": source_envelope.envelope_hash,
        "normalized_record": record,
        "normalized_record_available": record.normalization_complete,
        "source_result_preserved": preserved,
        "source_response_modified": False,
        "lossy_coercion_performed": False,
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
            None if record.normalization_complete
            else "normalization_incomplete"
        ),
    }
    report = OracleRealIntelligenceNormalizationReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_real_intelligence_normalization_report(report)
    return report


def verify_real_intelligence_normalization_report(
    report: OracleRealIntelligenceNormalizationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization schema mismatch"
        )
    if report.policy_id != POLICY_ID:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization policy mismatch"
        )
    verify_normalized_record(report.normalized_record)
    if not report.read_only:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization report is not read-only"
        )
    if report.source_response_modified:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "source response modification detected"
        )
    if report.lossy_coercion_performed:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "lossy coercion detected"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.runtime_artifact_created
        or report.runtime_artifact_modified
        or report.networking_performed
        or report.publication_allowed
        or report.action_authorization_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleRealIntelligenceNormalizationInvariantError(
            "forbidden normalization capability enabled"
        )
    expected = bool(
        report.normalized_record_available
        and report.source_result_preserved
        and not report.lossy_coercion_performed
    )
    if report.normalized_record.normalization_complete != expected:
        raise OracleRealIntelligenceNormalizationInvariantError(
            "normalization availability mismatch"
        )
    return True
