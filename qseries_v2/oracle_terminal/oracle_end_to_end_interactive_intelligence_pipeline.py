from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_bounded_multi_turn_intelligence_session_context import (
    OracleBoundedMultiTurnSessionContext,
    OracleBoundedMultiTurnSessionUpdateReport,
    append_answer_to_bounded_multi_turn_session,
    verify_bounded_multi_turn_session_update_report,
    verify_multi_turn_session_context,
)
from .oracle_conversation_response_rendering import (
    OracleConversationResponseRenderingReport,
    build_conversation_response_rendering_report,
    verify_conversation_response_rendering_report,
)
from .oracle_final_intelligence_answer_assembly import (
    OracleFinalIntelligenceAnswerAssemblyReport,
    build_final_intelligence_answer_assembly_report,
    verify_final_intelligence_answer_assembly_report,
)
from .oracle_intelligence_session_context_assembly import (
    OracleIntelligenceSessionContextAssemblyReport,
    verify_intelligence_session_context_assembly_report,
)
from .oracle_multi_turn_follow_up_query_context_resolution import (
    OracleFollowUpQueryResolutionReport,
    resolve_multi_turn_follow_up_query,
    verify_follow_up_query_resolution_report,
)
from .oracle_resolved_follow_up_projection_reentry_gate import (
    OracleResolvedFollowUpProjectionReentryReport,
    build_resolved_follow_up_projection_reentry_report,
    verify_resolved_follow_up_projection_reentry_report,
)

SCHEMA_VERSION = "OIT-048"
ENGINE_ID = "OIT-048"
POLICY_ID = "oracle.end-to-end-interactive-intelligence-pipeline.v1"


class OracleInteractiveIntelligencePipelineInvariantError(RuntimeError):
    pass


@dataclass(frozen=True)
class OracleInteractiveIntelligencePipelineLineage:
    source_context_assembly_report_hash: str
    source_prior_session_context_hash: str
    follow_up_resolution_report_hash: str
    projection_reentry_report_hash: str
    final_answer_assembly_report_hash: str
    conversation_rendering_report_hash: str
    updated_session_context_hash: str
    exact_stage_order_verified: bool
    exact_cross_stage_lineage_verified: bool
    lineage_hash: str


@dataclass(frozen=True)
class OracleInteractiveIntelligencePipelineResult:
    pipeline_id: str
    query: str
    context_assembly_report_hash: str
    prior_session_context_hash: str
    follow_up_resolution_report: OracleFollowUpQueryResolutionReport
    projection_reentry_report: OracleResolvedFollowUpProjectionReentryReport
    final_answer_assembly_report: OracleFinalIntelligenceAnswerAssemblyReport
    conversation_rendering_report: OracleConversationResponseRenderingReport
    session_update_report: OracleBoundedMultiTurnSessionUpdateReport
    lineage: OracleInteractiveIntelligencePipelineLineage
    rendered_lines: tuple[str, ...]
    rendered_line_count: int
    session_turn_count: int
    pipeline_completed: bool
    terminal_display_ready: bool
    session_continuation_ready: bool
    read_only: bool
    result_hash: str


@dataclass(frozen=True)
class OracleInteractiveIntelligencePipelineReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    pipeline_result: OracleInteractiveIntelligencePipelineResult
    end_to_end_pipeline_certified: bool
    live_runner_binding_ready: bool
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
    raise OracleInteractiveIntelligencePipelineInvariantError(
        "unsupported OIT-048 value type: "
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


def verify_pipeline_lineage(
    lineage: OracleInteractiveIntelligencePipelineLineage,
) -> bool:
    body = asdict(lineage)
    supplied = body.pop("lineage_hash")

    if _stable_hash(body) != supplied:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 lineage hash mismatch"
        )

    required = (
        lineage.source_context_assembly_report_hash,
        lineage.source_prior_session_context_hash,
        lineage.follow_up_resolution_report_hash,
        lineage.projection_reentry_report_hash,
        lineage.final_answer_assembly_report_hash,
        lineage.conversation_rendering_report_hash,
        lineage.updated_session_context_hash,
    )
    if not all(required):
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 lineage incomplete"
        )

    if not lineage.exact_stage_order_verified:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 stage order not verified"
        )

    if not lineage.exact_cross_stage_lineage_verified:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 cross-stage lineage not verified"
        )

    return True


def verify_pipeline_result(
    result: OracleInteractiveIntelligencePipelineResult,
) -> bool:
    body = asdict(result)
    supplied = body.pop("result_hash")

    if _stable_hash(body) != supplied:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 result hash mismatch"
        )

    if not result.pipeline_id or not result.query:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 pipeline identity missing"
        )

    verify_follow_up_query_resolution_report(
        result.follow_up_resolution_report
    )
    verify_resolved_follow_up_projection_reentry_report(
        result.projection_reentry_report
    )
    verify_final_intelligence_answer_assembly_report(
        result.final_answer_assembly_report
    )
    verify_conversation_response_rendering_report(
        result.conversation_rendering_report
    )
    verify_bounded_multi_turn_session_update_report(
        result.session_update_report
    )
    verify_pipeline_lineage(result.lineage)

    if result.rendered_line_count != len(result.rendered_lines):
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 rendered line count mismatch"
        )

    if result.session_turn_count != (
        result.session_update_report.updated_session_context.turn_count
    ):
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 session turn count mismatch"
        )

    expected_completed = bool(
        result.follow_up_resolution_report.downstream_projection_ready
        and result.projection_reentry_report.answer_generation_ready
        and result.final_answer_assembly_report.final_answer_assembled
        and result.conversation_rendering_report.rendering_completed
        and result.session_update_report.turn_appended
        and result.lineage.exact_stage_order_verified
        and result.lineage.exact_cross_stage_lineage_verified
        and result.read_only
    )

    if result.pipeline_completed != expected_completed:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 pipeline completion mismatch"
        )

    if result.terminal_display_ready != (
        result.pipeline_completed
        and result.conversation_rendering_report
        .response_frame.terminal_display_ready
    ):
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 terminal display readiness mismatch"
        )

    if result.session_continuation_ready != (
        result.pipeline_completed
        and result.session_update_report.session_continuation_ready
    ):
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 session continuation readiness mismatch"
        )

    return True


def execute_end_to_end_interactive_intelligence_pipeline(
    repository_root: str | Path,
    *,
    context_assembly_report: OracleIntelligenceSessionContextAssemblyReport,
    prior_session_context: OracleBoundedMultiTurnSessionContext,
    query: str,
) -> OracleInteractiveIntelligencePipelineReport:
    root = Path(repository_root).resolve()

    verify_intelligence_session_context_assembly_report(
        context_assembly_report
    )
    verify_multi_turn_session_context(prior_session_context)

    follow_up = resolve_multi_turn_follow_up_query(
        root,
        session_context=prior_session_context,
        query=query,
    )
    verify_follow_up_query_resolution_report(follow_up)

    reentry = build_resolved_follow_up_projection_reentry_report(
        root,
        follow_up_resolution_report=follow_up,
        context_assembly_report=context_assembly_report,
    )
    verify_resolved_follow_up_projection_reentry_report(reentry)

    assembly = build_final_intelligence_answer_assembly_report(
        root,
        reentry_report=reentry,
    )
    verify_final_intelligence_answer_assembly_report(assembly)

    rendering = build_conversation_response_rendering_report(
        root,
        final_answer_assembly_report=assembly,
    )
    verify_conversation_response_rendering_report(rendering)

    session_update = append_answer_to_bounded_multi_turn_session(
        root,
        answer_report=assembly.answer_generation_report,
        prior_session_context=prior_session_context,
    )
    verify_bounded_multi_turn_session_update_report(session_update)

    exact_stage_order = bool(
        follow_up.report_hash
        == reentry.follow_up_resolution_report_hash
        and reentry.report_hash
        == assembly.reentry_report_hash
        and assembly.report_hash
        == rendering.final_answer_assembly_report_hash
        and assembly.answer_generation_report.report_hash
        == session_update.source_answer_report_hash
    )

    exact_cross_stage = bool(
        follow_up.source_session_context_hash
        == prior_session_context.context_hash
        and reentry.context_assembly_report_hash
        == context_assembly_report.report_hash
        and reentry.projection_binding.source_session_context_hash
        == prior_session_context.context_hash
        and assembly.final_answer_package.lineage.source_session_context_hash
        == prior_session_context.context_hash
        and rendering.response_frame.source_package_hash
        == assembly.final_answer_package.package_hash
        and rendering.response_frame.source_answer_hash
        == assembly.final_answer_package.answer.answer_hash
        and session_update.updated_session_context.turns[-1].answer_hash
        == assembly.final_answer_package.answer.answer_hash
    )

    if not exact_stage_order or not exact_cross_stage:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 end-to-end lineage mismatch"
        )

    lineage_body = {
        "source_context_assembly_report_hash": (
            context_assembly_report.report_hash
        ),
        "source_prior_session_context_hash": (
            prior_session_context.context_hash
        ),
        "follow_up_resolution_report_hash": follow_up.report_hash,
        "projection_reentry_report_hash": reentry.report_hash,
        "final_answer_assembly_report_hash": assembly.report_hash,
        "conversation_rendering_report_hash": rendering.report_hash,
        "updated_session_context_hash": (
            session_update.updated_session_context.context_hash
        ),
        "exact_stage_order_verified": True,
        "exact_cross_stage_lineage_verified": True,
    }
    lineage = OracleInteractiveIntelligencePipelineLineage(
        **lineage_body,
        lineage_hash=_stable_hash(lineage_body),
    )
    verify_pipeline_lineage(lineage)

    rendered_lines = tuple(
        line.text for line in rendering.response_frame.lines
    )

    result_body = {
        "pipeline_id": _stable_hash(
            {
                "query": query,
                "context_hash": context_assembly_report.report_hash,
                "prior_session_hash": prior_session_context.context_hash,
                "rendering_hash": rendering.report_hash,
                "updated_session_hash": (
                    session_update.updated_session_context.context_hash
                ),
            }
        )[:24],
        "query": str(query),
        "context_assembly_report_hash": (
            context_assembly_report.report_hash
        ),
        "prior_session_context_hash": (
            prior_session_context.context_hash
        ),
        "follow_up_resolution_report": follow_up,
        "projection_reentry_report": reentry,
        "final_answer_assembly_report": assembly,
        "conversation_rendering_report": rendering,
        "session_update_report": session_update,
        "lineage": lineage,
        "rendered_lines": rendered_lines,
        "rendered_line_count": len(rendered_lines),
        "session_turn_count": (
            session_update.updated_session_context.turn_count
        ),
        "pipeline_completed": True,
        "terminal_display_ready": True,
        "session_continuation_ready": True,
        "read_only": True,
    }
    result = OracleInteractiveIntelligencePipelineResult(
        **result_body,
        result_hash=_stable_hash(result_body),
    )
    verify_pipeline_result(result)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "pipeline_result": result,
        "end_to_end_pipeline_certified": result.pipeline_completed,
        "live_runner_binding_ready": (
            result.pipeline_completed
            and result.terminal_display_ready
            and result.session_continuation_ready
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
        "failure_reason": None,
    }
    report = OracleInteractiveIntelligencePipelineReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_interactive_intelligence_pipeline_report(report)
    return report


def verify_interactive_intelligence_pipeline_report(
    report: OracleInteractiveIntelligencePipelineReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 policy mismatch"
        )

    verify_pipeline_result(report.pipeline_result)

    if not report.read_only:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 report is not read-only"
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
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "forbidden OIT-048 capability enabled"
        )

    expected = bool(
        report.pipeline_result.pipeline_completed
        and report.pipeline_result.terminal_display_ready
        and report.pipeline_result.session_continuation_ready
    )

    if report.end_to_end_pipeline_certified != expected:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 certification state mismatch"
        )

    if report.live_runner_binding_ready != expected:
        raise OracleInteractiveIntelligencePipelineInvariantError(
            "OIT-048 runner-binding readiness mismatch"
        )

    return True
