from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_intelligence_session_context_assembly import (
    OracleIntelligenceSessionContextAssemblyReport,
    verify_intelligence_session_context_assembly_report,
)
from .oracle_multi_turn_follow_up_query_context_resolution import (
    OracleFollowUpQueryResolutionReport,
    OracleFollowUpQueryResolutionInvariantError,
    verify_follow_up_query_resolution_report,
)
from .oracle_natural_language_intelligence_response_projection import (
    OracleNaturalLanguageIntelligenceProjectionReport,
    build_natural_language_intelligence_projection_report,
    verify_natural_language_intelligence_projection_report,
)

SCHEMA_VERSION = "OIT-045"
ENGINE_ID = "OIT-045"
POLICY_ID = "oracle.resolved-follow-up-projection-reentry.v1"


class OracleResolvedFollowUpProjectionReentryInvariantError(
    OracleFollowUpQueryResolutionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleResolvedFollowUpProjectionBinding:
    source_follow_up_report_hash: str
    source_context_assembly_report_hash: str
    source_session_context_hash: str
    resolved_query: str
    normalized_query: str
    follow_up_detected: bool
    primary_reference_turn_index: int | None
    resolution_confidence: float
    projection_report_hash: str
    projection_hash: str
    projected_field_count: int
    relevant_context_found: bool
    exact_cross_stage_lineage_verified: bool
    read_only: bool
    binding_hash: str


@dataclass(frozen=True)
class OracleResolvedFollowUpProjectionReentryReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    follow_up_resolution_report_hash: str
    context_assembly_report_hash: str
    projection_report: OracleNaturalLanguageIntelligenceProjectionReport
    projection_binding: OracleResolvedFollowUpProjectionBinding
    reentry_performed: bool
    answer_generation_ready: bool
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
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise OracleResolvedFollowUpProjectionReentryInvariantError(
        "unsupported OIT-045 value type: "
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


def verify_projection_binding(
    binding: OracleResolvedFollowUpProjectionBinding,
) -> bool:
    body = asdict(binding)
    supplied = body.pop("binding_hash")

    if _stable_hash(body) != supplied:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projection binding hash mismatch"
        )

    if not binding.source_follow_up_report_hash:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 follow-up report lineage missing"
        )

    if not binding.source_context_assembly_report_hash:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 context assembly lineage missing"
        )

    if not binding.source_session_context_hash:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 session context lineage missing"
        )

    if not binding.resolved_query or not binding.normalized_query:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 resolved query missing"
        )

    if not 0.0 <= binding.resolution_confidence <= 1.0:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 resolution confidence outside bounds"
        )

    if not binding.projection_report_hash or not binding.projection_hash:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projection lineage missing"
        )

    if binding.projected_field_count < 0:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projected field count invalid"
        )

    if binding.relevant_context_found != (
        binding.projected_field_count > 0
    ):
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 relevant-context state mismatch"
        )

    if not binding.exact_cross_stage_lineage_verified:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 exact cross-stage lineage not verified"
        )

    if not binding.read_only:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projection binding is not read-only"
        )

    return True


def build_resolved_follow_up_projection_reentry_report(
    repository_root: str | Path,
    *,
    follow_up_resolution_report: OracleFollowUpQueryResolutionReport,
    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,
) -> OracleResolvedFollowUpProjectionReentryReport:
    root = Path(repository_root).resolve()

    verify_follow_up_query_resolution_report(
        follow_up_resolution_report
    )
    verify_intelligence_session_context_assembly_report(
        context_assembly_report
    )

    if not follow_up_resolution_report.downstream_projection_ready:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            follow_up_resolution_report.failure_reason
            or "OIT-044 resolution is not projection-ready"
        )

    if not context_assembly_report.query_planning_ready:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            context_assembly_report.failure_reason
            or "OIT-040 context is not query-planning ready"
        )

    resolved = (
        follow_up_resolution_report.resolved_follow_up_query
    )

    projection_report = (
        build_natural_language_intelligence_projection_report(
            root,
            context_assembly_report=context_assembly_report,
            query=resolved.resolved_query,
        )
    )
    verify_natural_language_intelligence_projection_report(
        projection_report
    )

    projection = projection_report.projection
    context = context_assembly_report.session_context

    exact_lineage = bool(
        follow_up_resolution_report.source_session_context_hash
        and follow_up_resolution_report.source_session_context_hash
        != context.context_hash
        and projection_report.context_assembly_report_hash
        == context_assembly_report.report_hash
        and projection.source_context_hash == context.context_hash
        and projection.source_context_report_hash
        == context_assembly_report.report_hash
        and projection.query_intent.raw_query
        == resolved.resolved_query
        and projection.query_intent.normalized_query
        == " ".join(resolved.resolved_query.strip().split())
    )

    # OIT-044 references the volatile OIT-043 session context.
    # OIT-040 is the certified intelligence context used for projection.
    # They must remain distinct but both must be preserved exactly.
    if not exact_lineage:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 exact OIT-040/OIT-044 lineage mismatch"
        )

    binding_body = {
        "source_follow_up_report_hash": (
            follow_up_resolution_report.report_hash
        ),
        "source_context_assembly_report_hash": (
            context_assembly_report.report_hash
        ),
        "source_session_context_hash": (
            follow_up_resolution_report.source_session_context_hash
        ),
        "resolved_query": resolved.resolved_query,
        "normalized_query": resolved.normalized_query,
        "follow_up_detected": resolved.follow_up_detected,
        "primary_reference_turn_index": (
            resolved.primary_reference_turn_index
        ),
        "resolution_confidence": resolved.resolution_confidence,
        "projection_report_hash": projection_report.report_hash,
        "projection_hash": projection.projection_hash,
        "projected_field_count": projection.projected_field_count,
        "relevant_context_found": bool(
            projection.projected_fields
        ),
        "exact_cross_stage_lineage_verified": True,
        "read_only": True,
    }
    binding = OracleResolvedFollowUpProjectionBinding(
        **binding_body,
        binding_hash=_stable_hash(binding_body),
    )
    verify_projection_binding(binding)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "follow_up_resolution_report_hash": (
            follow_up_resolution_report.report_hash
        ),
        "context_assembly_report_hash": (
            context_assembly_report.report_hash
        ),
        "projection_report": projection_report,
        "projection_binding": binding,
        "reentry_performed": True,
        "answer_generation_ready": bool(
            projection_report.answer_generation_ready
            and binding.relevant_context_found
            and binding.exact_cross_stage_lineage_verified
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
            if projection_report.answer_generation_ready
            and binding.relevant_context_found
            else "OIT-045 projection reentry not answer-ready"
        ),
    }
    report = OracleResolvedFollowUpProjectionReentryReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_resolved_follow_up_projection_reentry_report(
        report
    )
    return report


def verify_resolved_follow_up_projection_reentry_report(
    report: OracleResolvedFollowUpProjectionReentryReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 policy mismatch"
        )

    verify_natural_language_intelligence_projection_report(
        report.projection_report
    )
    verify_projection_binding(report.projection_binding)

    if not report.read_only:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 report is not read-only"
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
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "forbidden OIT-045 capability enabled"
        )

    if report.follow_up_resolution_report_hash != (
        report.projection_binding.source_follow_up_report_hash
    ):
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 follow-up report lineage mismatch"
        )

    if report.context_assembly_report_hash != (
        report.projection_binding.source_context_assembly_report_hash
    ):
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 context assembly lineage mismatch"
        )

    if report.projection_report.report_hash != (
        report.projection_binding.projection_report_hash
    ):
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projection report lineage mismatch"
        )

    if report.projection_report.projection.projection_hash != (
        report.projection_binding.projection_hash
    ):
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 projection hash lineage mismatch"
        )

    expected_ready = bool(
        report.reentry_performed
        and report.projection_report.answer_generation_ready
        and report.projection_binding.relevant_context_found
        and report.projection_binding.exact_cross_stage_lineage_verified
    )

    if report.answer_generation_ready != expected_ready:
        raise OracleResolvedFollowUpProjectionReentryInvariantError(
            "OIT-045 answer-generation readiness mismatch"
        )

    return True
