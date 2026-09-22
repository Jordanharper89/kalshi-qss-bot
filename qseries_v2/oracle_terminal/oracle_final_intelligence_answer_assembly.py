from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_resolved_follow_up_projection_reentry_gate import (
    OracleResolvedFollowUpProjectionReentryInvariantError,
    OracleResolvedFollowUpProjectionReentryReport,
    verify_resolved_follow_up_projection_reentry_report,
)
from .oracle_terminal_intelligence_answer_generation import (
    OracleTerminalIntelligenceAnswer,
    OracleTerminalIntelligenceAnswerGenerationReport,
    build_terminal_intelligence_answer_generation_report,
    verify_terminal_intelligence_answer,
    verify_terminal_intelligence_answer_generation_report,
)

SCHEMA_VERSION = "OIT-046"
ENGINE_ID = "OIT-046"
POLICY_ID = "oracle.final-intelligence-answer-assembly.v1"


class OracleFinalIntelligenceAnswerAssemblyInvariantError(
    OracleResolvedFollowUpProjectionReentryInvariantError
):
    pass


@dataclass(frozen=True)
class OracleFinalIntelligenceAnswerLineage:
    source_reentry_report_hash: str
    source_follow_up_resolution_report_hash: str
    source_context_assembly_report_hash: str
    source_projection_report_hash: str
    source_projection_hash: str
    source_answer_generation_report_hash: str
    source_answer_hash: str
    source_session_context_hash: str
    primary_reference_turn_index: int | None
    exact_lineage_verified: bool
    lineage_hash: str


@dataclass(frozen=True)
class OracleFinalIntelligenceAnswerPackage:
    package_id: str
    query: str
    resolved_query: str
    follow_up_detected: bool
    resolution_confidence: float
    answer: OracleTerminalIntelligenceAnswer
    lineage: OracleFinalIntelligenceAnswerLineage
    answer_line_count: int
    all_claims_evidence_linked: bool
    deterministic_assembly: bool
    bounded_answer: bool
    terminal_render_ready: bool
    read_only: bool
    package_hash: str


@dataclass(frozen=True)
class OracleFinalIntelligenceAnswerAssemblyReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    reentry_report_hash: str
    answer_generation_report: OracleTerminalIntelligenceAnswerGenerationReport
    final_answer_package: OracleFinalIntelligenceAnswerPackage
    final_answer_assembled: bool
    conversation_rendering_ready: bool
    unsupported_claims_generated: bool
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
    raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
        "unsupported OIT-046 value type: "
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


def verify_final_answer_lineage(
    lineage: OracleFinalIntelligenceAnswerLineage,
) -> bool:
    body = asdict(lineage)
    supplied = body.pop("lineage_hash")

    if _stable_hash(body) != supplied:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 lineage hash mismatch"
        )

    required = (
        lineage.source_reentry_report_hash,
        lineage.source_follow_up_resolution_report_hash,
        lineage.source_context_assembly_report_hash,
        lineage.source_projection_report_hash,
        lineage.source_projection_hash,
        lineage.source_answer_generation_report_hash,
        lineage.source_answer_hash,
        lineage.source_session_context_hash,
    )
    if not all(required):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 lineage is incomplete"
        )

    if (
        lineage.primary_reference_turn_index is not None
        and lineage.primary_reference_turn_index < 0
    ):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 primary turn index invalid"
        )

    if not lineage.exact_lineage_verified:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 exact lineage not verified"
        )

    return True


def verify_final_answer_package(
    package: OracleFinalIntelligenceAnswerPackage,
) -> bool:
    body = asdict(package)
    supplied = body.pop("package_hash")

    if _stable_hash(body) != supplied:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 final answer package hash mismatch"
        )

    if not package.package_id:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 package ID missing"
        )

    if not package.query or not package.resolved_query:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 query identity missing"
        )

    if not 0.0 <= package.resolution_confidence <= 1.0:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 resolution confidence outside bounds"
        )

    verify_terminal_intelligence_answer(package.answer)
    verify_final_answer_lineage(package.lineage)

    if package.answer_line_count != package.answer.answer_line_count:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 answer line count mismatch"
        )

    if package.all_claims_evidence_linked != (
        package.answer.all_claims_evidence_linked
    ):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 evidence-link state mismatch"
        )

    if package.bounded_answer != package.answer.bounded_answer:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 bounded-answer state mismatch"
        )

    expected_ready = bool(
        package.answer.answer_ready
        and package.all_claims_evidence_linked
        and package.deterministic_assembly
        and package.bounded_answer
        and package.lineage.exact_lineage_verified
        and package.read_only
    )

    if package.terminal_render_ready != expected_ready:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 terminal-render readiness mismatch"
        )

    return True


def build_final_intelligence_answer_assembly_report(
    repository_root: str | Path,
    *,
    reentry_report: OracleResolvedFollowUpProjectionReentryReport,
) -> OracleFinalIntelligenceAnswerAssemblyReport:
    root = Path(repository_root).resolve()

    verify_resolved_follow_up_projection_reentry_report(
        reentry_report
    )

    if not reentry_report.answer_generation_ready:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            reentry_report.failure_reason
            or "OIT-045 reentry is not answer-generation ready"
        )

    answer_report = build_terminal_intelligence_answer_generation_report(
        root,
        projection_report=reentry_report.projection_report,
    )
    verify_terminal_intelligence_answer_generation_report(
        answer_report
    )

    if not answer_report.answer_generated:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            answer_report.failure_reason
            or "OIT-042 answer generation failed"
        )

    binding = reentry_report.projection_binding
    projection = reentry_report.projection_report.projection
    answer = answer_report.answer

    exact_lineage = bool(
        reentry_report.report_hash
        and reentry_report.follow_up_resolution_report_hash
        == binding.source_follow_up_report_hash
        and reentry_report.context_assembly_report_hash
        == binding.source_context_assembly_report_hash
        and reentry_report.projection_report.report_hash
        == binding.projection_report_hash
        and projection.projection_hash
        == binding.projection_hash
        and answer_report.projection_report_hash
        == reentry_report.projection_report.report_hash
        and answer.source_projection_report_hash
        == reentry_report.projection_report.report_hash
        and answer.source_projection_hash
        == projection.projection_hash
        and answer.query
        == projection.query_intent.normalized_query
        and binding.exact_cross_stage_lineage_verified
    )

    if not exact_lineage:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 cross-stage lineage mismatch"
        )

    lineage_body = {
        "source_reentry_report_hash": reentry_report.report_hash,
        "source_follow_up_resolution_report_hash": (
            binding.source_follow_up_report_hash
        ),
        "source_context_assembly_report_hash": (
            binding.source_context_assembly_report_hash
        ),
        "source_projection_report_hash": (
            reentry_report.projection_report.report_hash
        ),
        "source_projection_hash": projection.projection_hash,
        "source_answer_generation_report_hash": (
            answer_report.report_hash
        ),
        "source_answer_hash": answer.answer_hash,
        "source_session_context_hash": (
            binding.source_session_context_hash
        ),
        "primary_reference_turn_index": (
            binding.primary_reference_turn_index
        ),
        "exact_lineage_verified": True,
    }
    lineage = OracleFinalIntelligenceAnswerLineage(
        **lineage_body,
        lineage_hash=_stable_hash(lineage_body),
    )
    verify_final_answer_lineage(lineage)

    query = reentry_report.projection_report.projection.query_intent.raw_query

    package_body = {
        "package_id": _stable_hash(
            {
                "reentry_report_hash": reentry_report.report_hash,
                "answer_report_hash": answer_report.report_hash,
                "answer_hash": answer.answer_hash,
            }
        )[:24],
        "query": query,
        "resolved_query": binding.resolved_query,
        "follow_up_detected": binding.follow_up_detected,
        "resolution_confidence": binding.resolution_confidence,
        "answer": answer,
        "lineage": lineage,
        "answer_line_count": answer.answer_line_count,
        "all_claims_evidence_linked": (
            answer.all_claims_evidence_linked
        ),
        "deterministic_assembly": True,
        "bounded_answer": answer.bounded_answer,
        "terminal_render_ready": bool(
            answer.answer_ready
            and answer.all_claims_evidence_linked
            and answer.bounded_answer
            and exact_lineage
        ),
        "read_only": True,
    }
    package = OracleFinalIntelligenceAnswerPackage(
        **package_body,
        package_hash=_stable_hash(package_body),
    )
    verify_final_answer_package(package)

    report_body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "reentry_report_hash": reentry_report.report_hash,
        "answer_generation_report": answer_report,
        "final_answer_package": package,
        "final_answer_assembled": package.terminal_render_ready,
        "conversation_rendering_ready": package.terminal_render_ready,
        "unsupported_claims_generated": False,
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
            if package.terminal_render_ready
            else "OIT-046 final answer assembly failed"
        ),
    }
    report = OracleFinalIntelligenceAnswerAssemblyReport(
        **report_body,
        report_hash=_stable_hash(report_body),
    )
    verify_final_intelligence_answer_assembly_report(report)
    return report


def verify_final_intelligence_answer_assembly_report(
    report: OracleFinalIntelligenceAnswerAssemblyReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")

    if _stable_hash(body) != supplied:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 report hash mismatch"
        )

    if report.schema_version != SCHEMA_VERSION:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 schema mismatch"
        )

    if report.policy_id != POLICY_ID:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 policy mismatch"
        )

    verify_terminal_intelligence_answer_generation_report(
        report.answer_generation_report
    )
    verify_final_answer_package(
        report.final_answer_package
    )

    if not report.read_only:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 report is not read-only"
        )

    if (
        report.unsupported_claims_generated
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
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "forbidden OIT-046 capability enabled"
        )

    if report.reentry_report_hash != (
        report.final_answer_package.lineage.source_reentry_report_hash
    ):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 reentry lineage mismatch"
        )

    if report.answer_generation_report.report_hash != (
        report.final_answer_package.lineage
        .source_answer_generation_report_hash
    ):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 answer-generation lineage mismatch"
        )

    if report.answer_generation_report.answer.answer_hash != (
        report.final_answer_package.answer.answer_hash
    ):
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 answer identity mismatch"
        )

    expected = bool(
        report.final_answer_package.terminal_render_ready
        and report.final_answer_package.lineage.exact_lineage_verified
        and report.final_answer_package.answer.answer_ready
    )

    if report.final_answer_assembled != expected:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 final-answer state mismatch"
        )

    if report.conversation_rendering_ready != expected:
        raise OracleFinalIntelligenceAnswerAssemblyInvariantError(
            "OIT-046 rendering readiness mismatch"
        )

    return True
