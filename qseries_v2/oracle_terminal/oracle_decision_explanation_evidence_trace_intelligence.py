from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_decision_readiness_abstention_intelligence import (
    OracleDecisionReadinessFinding,
    OracleDecisionReadinessInvariantError,
    OracleDecisionReadinessReport,
    build_decision_readiness_report,
    verify_decision_readiness_report,
)

SCHEMA_VERSION = "OIT-021"
ENGINE_ID = "OIT-021"
POLICY_ID = "oracle.decision-explanation-evidence-trace-intelligence.v1"


class OracleDecisionExplanationInvariantError(
    OracleDecisionReadinessInvariantError
):
    pass


@dataclass(frozen=True)
class OracleDecisionEvidenceTrace:
    trace_index: int
    source_debate_hash: str
    readiness_finding_hash: str
    evidence_role: str
    evidence_statement: str
    supports_state: str
    trace_hash: str


@dataclass(frozen=True)
class OracleDecisionExplanationFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_readiness_hash: str
    readiness_state: str
    directional_interpretation: str
    readiness_score: float
    abstention_pressure: float
    concise_explanation: str
    evidence_trace: tuple[OracleDecisionEvidenceTrace, ...]
    confirmation_plan: tuple[str, ...]
    blocking_conditions: tuple[str, ...]
    explanation_complete: bool
    operator_attention_required: bool
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleDecisionExplanationReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    readiness_report_hash: str
    findings: tuple[OracleDecisionExplanationFinding, ...]
    finding_count: int
    explained_count: int
    ready_explained_count: int
    observe_explained_count: int
    abstain_explained_count: int
    operator_attention_count: int
    aggregate_state: str
    aggregate_direction: str
    explanation_state: str
    explanation_summary: str
    read_only: bool
    analytics_execution_performed: bool
    database_access_performed: bool
    publication_allowed: bool
    qseries_execution_allowed: bool
    action_authorization_allowed: bool
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


def _trace(
    index: int,
    source: OracleDecisionReadinessFinding,
    role: str,
    statement: str,
) -> OracleDecisionEvidenceTrace:
    body = {
        "trace_index": index,
        "source_debate_hash": source.source_debate_hash,
        "readiness_finding_hash": source.finding_hash,
        "evidence_role": role,
        "evidence_statement": statement,
        "supports_state": source.readiness_state,
    }
    return OracleDecisionEvidenceTrace(
        **body,
        trace_hash=_stable_hash(body),
    )


def _explain(source: OracleDecisionReadinessFinding) -> str:
    if source.readiness_state == "ready":
        return (
            f"{source.directional_interpretation} interpretation is ready for "
            f"operator consideration because readiness {source.readiness_score:.6f} "
            f"exceeds abstention pressure {source.abstention_pressure:.6f}, "
            f"with debate margin {source.debate_margin:.6f}."
        )
    if source.readiness_state == "observe":
        return (
            f"{source.directional_interpretation} remains observational because "
            f"readiness {source.readiness_score:.6f} is not yet sufficient to "
            f"clear confirmation requirements while abstention pressure remains "
            f"{source.abstention_pressure:.6f}."
        )
    return (
        f"{source.directional_interpretation} is blocked by abstention because "
        f"abstention pressure is {source.abstention_pressure:.6f}, debate conflict "
        f"is {source.debate_conflict:.6f}, and human review is "
        f"{'required' if source.requires_human_review else 'not required'}."
    )


def _build_finding(
    source: OracleDecisionReadinessFinding,
    index: int,
) -> OracleDecisionExplanationFinding:
    statements = (
        ("readiness", f"readiness score = {source.readiness_score:.6f}"),
        ("abstention", f"abstention pressure = {source.abstention_pressure:.6f}"),
        ("margin", f"debate margin = {source.debate_margin:.6f}"),
        ("conflict", f"debate conflict = {source.debate_conflict:.6f}"),
        (
            "confidence",
            f"adjudicated confidence = {source.adjudicated_confidence:.6f}",
        ),
        (
            "review",
            f"human review required = {source.requires_human_review}",
        ),
    )
    traces = tuple(
        _trace(i, source, role, statement)
        for i, (role, statement) in enumerate(statements, start=1)
    )
    complete = bool(
        traces
        and source.required_confirmations
        and source.disqualifying_conditions
        and source.source_debate_hash
    )
    attention = (
        source.requires_human_review
        or source.readiness_state == "abstain"
        or not complete
    )
    body = {
        "finding_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_readiness_hash": source.finding_hash,
        "readiness_state": source.readiness_state,
        "directional_interpretation": source.directional_interpretation,
        "readiness_score": source.readiness_score,
        "abstention_pressure": source.abstention_pressure,
        "concise_explanation": _explain(source),
        "evidence_trace": traces,
        "confirmation_plan": tuple(source.required_confirmations),
        "blocking_conditions": tuple(source.disqualifying_conditions),
        "explanation_complete": complete,
        "operator_attention_required": attention,
        "read_only": True,
    }
    return OracleDecisionExplanationFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_decision_evidence_trace(trace: OracleDecisionEvidenceTrace) -> bool:
    body = asdict(trace)
    supplied = body.pop("trace_hash")
    if _stable_hash(body) != supplied:
        raise OracleDecisionExplanationInvariantError(
            "decision evidence trace hash mismatch"
        )
    if trace.supports_state not in {"ready", "observe", "abstain"}:
        raise OracleDecisionExplanationInvariantError(
            "unsupported trace readiness state"
        )
    if not trace.source_debate_hash or not trace.readiness_finding_hash:
        raise OracleDecisionExplanationInvariantError(
            "decision evidence lineage missing"
        )
    if not trace.evidence_statement:
        raise OracleDecisionExplanationInvariantError(
            "decision evidence statement missing"
        )
    return True


def verify_decision_explanation_finding(
    finding: OracleDecisionExplanationFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleDecisionExplanationInvariantError(
            "decision explanation finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleDecisionExplanationInvariantError(
            "decision explanation finding is not read-only"
        )
    if finding.readiness_state not in {"ready", "observe", "abstain"}:
        raise OracleDecisionExplanationInvariantError(
            "unsupported explanation readiness state"
        )
    if not finding.source_readiness_hash:
        raise OracleDecisionExplanationInvariantError(
            "readiness lineage missing"
        )
    if not finding.concise_explanation:
        raise OracleDecisionExplanationInvariantError(
            "concise explanation missing"
        )
    if not finding.evidence_trace:
        raise OracleDecisionExplanationInvariantError(
            "evidence trace missing"
        )
    for trace in finding.evidence_trace:
        verify_decision_evidence_trace(trace)
        if trace.readiness_finding_hash != finding.source_readiness_hash:
            raise OracleDecisionExplanationInvariantError(
                "evidence trace readiness lineage mismatch"
            )
    if finding.explanation_complete and (
        not finding.confirmation_plan or not finding.blocking_conditions
    ):
        raise OracleDecisionExplanationInvariantError(
            "complete explanation missing controls"
        )
    return True


def build_decision_explanation_report(
    repository_root: str | Path,
    query: str,
    *,
    readiness_report: OracleDecisionReadinessReport | None = None,
) -> OracleDecisionExplanationReport:
    root = Path(repository_root).resolve()
    source = readiness_report
    if source is None:
        source = build_decision_readiness_report(root, query)
    verify_decision_readiness_report(source)

    findings = tuple(
        _build_finding(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    for finding in findings:
        verify_decision_explanation_finding(finding)

    explained_count = sum(item.explanation_complete for item in findings)
    attention_count = sum(
        item.operator_attention_required for item in findings
    )
    explanation_state = (
        "complete"
        if explained_count == len(findings)
        else "incomplete"
    )
    summary = (
        f"{len(findings)} readiness findings explained; "
        f"{explained_count} complete; {attention_count} require operator attention; "
        f"aggregate state {source.aggregate_state}."
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "readiness_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "explained_count": explained_count,
        "ready_explained_count": sum(
            item.readiness_state == "ready" for item in findings
        ),
        "observe_explained_count": sum(
            item.readiness_state == "observe" for item in findings
        ),
        "abstain_explained_count": sum(
            item.readiness_state == "abstain" for item in findings
        ),
        "operator_attention_count": attention_count,
        "aggregate_state": source.aggregate_state,
        "aggregate_direction": source.aggregate_direction,
        "explanation_state": explanation_state,
        "explanation_summary": summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    report = OracleDecisionExplanationReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_decision_explanation_report(report)
    return report


def verify_decision_explanation_report(
    report: OracleDecisionExplanationReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleDecisionExplanationInvariantError(
            "decision explanation report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleDecisionExplanationInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleDecisionExplanationInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleDecisionExplanationInvariantError(
            "decision explanation report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
        or report.action_authorization_allowed
    ):
        raise OracleDecisionExplanationInvariantError(
            "forbidden capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleDecisionExplanationInvariantError(
            "decision explanation finding count mismatch"
        )
    if report.explained_count != sum(
        item.explanation_complete for item in report.findings
    ):
        raise OracleDecisionExplanationInvariantError(
            "explained count mismatch"
        )
    if report.operator_attention_count != sum(
        item.operator_attention_required for item in report.findings
    ):
        raise OracleDecisionExplanationInvariantError(
            "operator attention count mismatch"
        )
    counts = {
        "ready": report.ready_explained_count,
        "observe": report.observe_explained_count,
        "abstain": report.abstain_explained_count,
    }
    for state, expected in counts.items():
        actual = sum(
            item.readiness_state == state for item in report.findings
        )
        if actual != expected:
            raise OracleDecisionExplanationInvariantError(
                f"{state} explanation count mismatch"
            )
    if sum(counts.values()) != report.finding_count:
        raise OracleDecisionExplanationInvariantError(
            "classified explanation count mismatch"
        )
    if report.aggregate_state not in {"ready", "observe", "abstain"}:
        raise OracleDecisionExplanationInvariantError(
            "invalid aggregate state"
        )
    if report.aggregate_direction not in {"bull", "bear", "neutral"}:
        raise OracleDecisionExplanationInvariantError(
            "invalid aggregate direction"
        )
    if report.explanation_state not in {"complete", "incomplete"}:
        raise OracleDecisionExplanationInvariantError(
            "invalid explanation state"
        )
    for finding in report.findings:
        verify_decision_explanation_finding(finding)
    return True
