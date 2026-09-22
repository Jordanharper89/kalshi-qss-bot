from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_bull_bear_neutral_debate_synthesis import (
    OracleDebateFinding,
    OracleDebateSynthesisInvariantError,
    OracleDebateSynthesisReport,
    build_debate_synthesis_report,
    verify_debate_synthesis_report,
)

SCHEMA_VERSION = "OIT-020"
ENGINE_ID = "OIT-020"
POLICY_ID = "oracle.decision-readiness-abstention-intelligence.v1"


class OracleDecisionReadinessInvariantError(
    OracleDebateSynthesisInvariantError
):
    pass


@dataclass(frozen=True)
class OracleDecisionReadinessFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_debate_hash: str
    leading_position: str
    debate_margin: float
    debate_conflict: float
    adjudicated_confidence: float
    requires_human_review: bool
    readiness_score: float
    abstention_pressure: float
    readiness_state: str
    directional_interpretation: str
    minimum_confirmation_count: int
    required_confirmations: tuple[str, ...]
    disqualifying_conditions: tuple[str, ...]
    rationale: tuple[str, ...]
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleDecisionReadinessReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    debate_report_hash: str
    findings: tuple[OracleDecisionReadinessFinding, ...]
    finding_count: int
    ready_count: int
    observe_count: int
    abstain_count: int
    human_review_count: int
    aggregate_state: str
    aggregate_direction: str
    aggregate_readiness: float
    aggregate_abstention_pressure: float
    readiness_summary: str
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


def _bounded(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _classify(source: OracleDebateFinding) -> tuple[str, float, float]:
    readiness = _bounded(
        (0.45 * source.adjudicated_confidence)
        + (0.35 * source.debate_margin)
        + (0.20 * (1.0 - source.debate_conflict))
    )
    abstention = _bounded(
        (0.45 * source.debate_conflict)
        + (0.30 * (1.0 - source.debate_margin))
        + (0.15 * (1.0 - source.adjudicated_confidence))
        + (0.10 if source.requires_human_review else 0.0)
    )

    if (
        source.requires_human_review
        or source.adjudication_state in {"contested", "challenge_conflict"}
        or abstention >= 0.68
    ):
        state = "abstain"
    elif (
        readiness >= 0.58
        and source.debate_margin >= 0.12
        and source.adjudicated_confidence >= 0.45
        and abstention < 0.60
    ):
        state = "ready"
    else:
        state = "observe"
    return state, readiness, abstention


def _build_finding(
    source: OracleDebateFinding,
    index: int,
) -> OracleDecisionReadinessFinding:
    state, readiness, abstention = _classify(source)

    if state == "ready":
        minimum_confirmations = 1
    elif state == "observe":
        minimum_confirmations = 2
    else:
        minimum_confirmations = 3

    confirmations = (
        f"confirm the {source.leading_position} lead persists on refresh",
        "confirm debate margin does not contract materially",
        "confirm no new contradiction raises human-review pressure",
    )
    disqualifiers = (
        "leading position changes after certified evidence refresh",
        "debate conflict rises above the bounded readiness threshold",
        "human review becomes required",
        "source lineage or report hash fails verification",
    )
    interpretation = (
        source.leading_position
        if state == "ready"
        else "non_actionable_" + source.leading_position
    )
    rationale = (
        f"readiness score: {readiness:.6f}",
        f"abstention pressure: {abstention:.6f}",
        f"debate margin: {source.debate_margin:.6f}",
        f"debate conflict: {source.debate_conflict:.6f}",
        f"adjudicated confidence: {source.adjudicated_confidence:.6f}",
        f"readiness state: {state}",
        "classification is intelligence-only and cannot authorize action",
    )

    body = {
        "finding_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_debate_hash": source.finding_hash,
        "leading_position": source.leading_position,
        "debate_margin": source.debate_margin,
        "debate_conflict": source.debate_conflict,
        "adjudicated_confidence": source.adjudicated_confidence,
        "requires_human_review": source.requires_human_review,
        "readiness_score": readiness,
        "abstention_pressure": abstention,
        "readiness_state": state,
        "directional_interpretation": interpretation,
        "minimum_confirmation_count": minimum_confirmations,
        "required_confirmations": confirmations,
        "disqualifying_conditions": disqualifiers,
        "rationale": rationale,
        "read_only": True,
    }
    return OracleDecisionReadinessFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_decision_readiness_finding(
    finding: OracleDecisionReadinessFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleDecisionReadinessInvariantError(
            "decision-readiness finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleDecisionReadinessInvariantError(
            "decision-readiness finding is not read-only"
        )
    if finding.readiness_state not in {"ready", "observe", "abstain"}:
        raise OracleDecisionReadinessInvariantError(
            "unsupported readiness state"
        )
    if finding.leading_position not in {"bull", "bear", "neutral"}:
        raise OracleDecisionReadinessInvariantError(
            "unsupported directional position"
        )
    for value in (
        finding.debate_margin,
        finding.debate_conflict,
        finding.adjudicated_confidence,
        finding.readiness_score,
        finding.abstention_pressure,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleDecisionReadinessInvariantError(
                "readiness metric outside bounded range"
            )
    if finding.minimum_confirmation_count < 1:
        raise OracleDecisionReadinessInvariantError(
            "minimum confirmation count invalid"
        )
    if not finding.required_confirmations:
        raise OracleDecisionReadinessInvariantError(
            "required confirmations missing"
        )
    if not finding.disqualifying_conditions:
        raise OracleDecisionReadinessInvariantError(
            "disqualifying conditions missing"
        )
    if not finding.source_debate_hash:
        raise OracleDecisionReadinessInvariantError(
            "debate lineage missing"
        )
    return True


def _aggregate(
    findings: tuple[OracleDecisionReadinessFinding, ...],
) -> tuple[str, str, float, float, str]:
    if not findings:
        return (
            "abstain",
            "neutral",
            0.0,
            1.0,
            "No certified debate findings were available; abstention required.",
        )

    ready = sum(item.readiness_state == "ready" for item in findings)
    observe = sum(item.readiness_state == "observe" for item in findings)
    abstain = sum(item.readiness_state == "abstain" for item in findings)

    if abstain:
        state = "abstain"
    elif ready == len(findings):
        state = "ready"
    else:
        state = "observe"

    directional_scores = {"bull": 0.0, "bear": 0.0, "neutral": 0.0}
    for item in findings:
        multiplier = (
            1.0 if item.readiness_state == "ready"
            else 0.5 if item.readiness_state == "observe"
            else 0.0
        )
        directional_scores[item.leading_position] += (
            item.readiness_score * multiplier
        )
    direction = sorted(
        directional_scores.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )[0][0]

    aggregate_readiness = _bounded(
        sum(item.readiness_score for item in findings) / len(findings)
    )
    aggregate_abstention = _bounded(
        sum(item.abstention_pressure for item in findings) / len(findings)
    )
    summary = (
        f"{len(findings)} findings classified: {ready} ready, "
        f"{observe} observe, {abstain} abstain; aggregate state {state}; "
        f"non-authorizing direction {direction}."
    )
    return (
        state,
        direction,
        aggregate_readiness,
        aggregate_abstention,
        summary,
    )


def build_decision_readiness_report(
    repository_root: str | Path,
    query: str,
    *,
    debate_report: OracleDebateSynthesisReport | None = None,
) -> OracleDecisionReadinessReport:
    root = Path(repository_root).resolve()
    source = debate_report
    if source is None:
        source = build_debate_synthesis_report(root, query)
    verify_debate_synthesis_report(source)

    findings = tuple(
        _build_finding(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    for finding in findings:
        verify_decision_readiness_finding(finding)

    state, direction, readiness, abstention, summary = _aggregate(findings)
    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "debate_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "ready_count": sum(
            item.readiness_state == "ready" for item in findings
        ),
        "observe_count": sum(
            item.readiness_state == "observe" for item in findings
        ),
        "abstain_count": sum(
            item.readiness_state == "abstain" for item in findings
        ),
        "human_review_count": sum(
            item.requires_human_review for item in findings
        ),
        "aggregate_state": state,
        "aggregate_direction": direction,
        "aggregate_readiness": readiness,
        "aggregate_abstention_pressure": abstention,
        "readiness_summary": summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "action_authorization_allowed": False,
        "failure_reason": None,
    }
    report = OracleDecisionReadinessReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_decision_readiness_report(report)
    return report


def verify_decision_readiness_report(
    report: OracleDecisionReadinessReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleDecisionReadinessInvariantError(
            "decision-readiness report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleDecisionReadinessInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleDecisionReadinessInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleDecisionReadinessInvariantError(
            "decision-readiness report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
        or report.action_authorization_allowed
    ):
        raise OracleDecisionReadinessInvariantError(
            "forbidden capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleDecisionReadinessInvariantError(
            "decision-readiness finding count mismatch"
        )
    counts = {
        "ready": report.ready_count,
        "observe": report.observe_count,
        "abstain": report.abstain_count,
    }
    for state, expected in counts.items():
        actual = sum(
            item.readiness_state == state for item in report.findings
        )
        if actual != expected:
            raise OracleDecisionReadinessInvariantError(
                f"{state} readiness count mismatch"
            )
    if sum(counts.values()) != report.finding_count:
        raise OracleDecisionReadinessInvariantError(
            "classified readiness count mismatch"
        )
    actual_review = sum(
        item.requires_human_review for item in report.findings
    )
    if actual_review != report.human_review_count:
        raise OracleDecisionReadinessInvariantError(
            "human review count mismatch"
        )
    if report.aggregate_state not in {"ready", "observe", "abstain"}:
        raise OracleDecisionReadinessInvariantError(
            "invalid aggregate readiness state"
        )
    if report.aggregate_direction not in {"bull", "bear", "neutral"}:
        raise OracleDecisionReadinessInvariantError(
            "invalid aggregate direction"
        )
    for value in (
        report.aggregate_readiness,
        report.aggregate_abstention_pressure,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleDecisionReadinessInvariantError(
                "aggregate readiness metric outside bounded range"
            )
    for finding in report.findings:
        verify_decision_readiness_finding(finding)
    return True
