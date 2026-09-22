from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_narrative_challenge_self_critique_intelligence import (
    OracleNarrativeChallengeFinding,
    OracleNarrativeChallengeInvariantError,
    OracleNarrativeChallengeReport,
    build_narrative_challenge_report,
    verify_narrative_challenge_report,
)

SCHEMA_VERSION = "OIT-019"
ENGINE_ID = "OIT-019"
POLICY_ID = "oracle.bull-bear-neutral-debate-synthesis.v1"


class OracleDebateSynthesisInvariantError(
    OracleNarrativeChallengeInvariantError
):
    pass


@dataclass(frozen=True)
class OracleDebatePosition:
    position: str
    score: float
    confidence: float
    supporting_points: tuple[str, ...]
    opposing_points: tuple[str, ...]
    required_confirmation: tuple[str, ...]
    position_hash: str


@dataclass(frozen=True)
class OracleDebateFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_challenge_hash: str
    original_narrative_state: str
    bull: OracleDebatePosition
    bear: OracleDebatePosition
    neutral: OracleDebatePosition
    leading_position: str
    debate_margin: float
    debate_conflict: float
    adjudicated_confidence: float
    adjudication_state: str
    requires_human_review: bool
    adjudication_rationale: tuple[str, ...]
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleDebateSynthesisReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    challenge_report_hash: str
    findings: tuple[OracleDebateFinding, ...]
    finding_count: int
    bull_leading_count: int
    bear_leading_count: int
    neutral_leading_count: int
    contested_count: int
    human_review_count: int
    aggregate_leading_position: str
    aggregate_confidence: float
    debate_state: str
    debate_summary: str
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


def _position(
    position: str,
    score: float,
    supporting_points: tuple[str, ...],
    opposing_points: tuple[str, ...],
    required_confirmation: tuple[str, ...],
) -> OracleDebatePosition:
    bounded_score = _bounded(score)
    confidence = _bounded(0.50 + abs(bounded_score - 0.50))
    body = {
        "position": position,
        "score": bounded_score,
        "confidence": confidence,
        "supporting_points": supporting_points,
        "opposing_points": opposing_points,
        "required_confirmation": required_confirmation,
    }
    return OracleDebatePosition(
        **body,
        position_hash=_stable_hash(body),
    )


def _derive_positions(
    source: OracleNarrativeChallengeFinding,
) -> tuple[OracleDebatePosition, OracleDebatePosition, OracleDebatePosition]:
    survival = source.surviving_confidence
    fragility = source.fragility_score
    counter = source.counter_evidence_pressure
    assumption = source.assumption_risk
    falsifiability = source.falsifiability_score

    bull_score = _bounded(
        (0.55 * survival)
        + (0.20 * (1.0 - fragility))
        + (0.15 * falsifiability)
        + (0.10 * (1.0 - counter))
    )
    bear_score = _bounded(
        (0.45 * counter)
        + (0.30 * fragility)
        + (0.15 * assumption)
        + (0.10 * (1.0 - survival))
    )
    neutral_score = _bounded(
        (0.40 * (1.0 - abs(bull_score - bear_score)))
        + (0.30 * assumption)
        + (0.20 * (1.0 - falsifiability))
        + (0.10 * min(bull_score, bear_score))
    )

    bull = _position(
        "bull",
        bull_score,
        (
            f"surviving narrative confidence is {survival:.6f}",
            f"challenge fragility is bounded at {fragility:.6f}",
            "certified narrative support survived adversarial review",
        ),
        tuple(source.counter_arguments),
        (
            "confirm support persists across the next certified update",
            "confirm evidence remains independent across venues",
        ),
    )
    bear = _position(
        "bear",
        bear_score,
        (
            f"counter-evidence pressure is {counter:.6f}",
            f"assumption risk is {assumption:.6f}",
            *tuple(source.counter_arguments),
        ),
        (
            "surviving confidence may still reflect durable support",
            "apparent reversal pressure may be temporary",
        ),
        (
            "confirm contradiction persists after temporal refresh",
            "confirm fragile assumptions fail under new evidence",
        ),
    )
    neutral = _position(
        "neutral",
        neutral_score,
        (
            f"falsifiability is bounded at {falsifiability:.6f}",
            "bull and bear interpretations remain explicitly testable",
            "insufficient separation supports temporary non-directionality",
        ),
        (
            "a meaningful score margin may justify directional preference",
            "new evidence may resolve the current ambiguity",
        ),
        tuple(source.falsification_tests),
    )
    return bull, bear, neutral


def _build_finding(
    source: OracleNarrativeChallengeFinding,
    index: int,
) -> OracleDebateFinding:
    bull, bear, neutral = _derive_positions(source)
    scores = {
        "bull": bull.score,
        "bear": bear.score,
        "neutral": neutral.score,
    }
    ordered = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    )
    leader, leading_score = ordered[0]
    runner_up_score = ordered[1][1]
    margin = _bounded(leading_score - runner_up_score)
    conflict = _bounded(
        1.0 - (max(scores.values()) - min(scores.values()))
    )

    if margin < 0.08:
        adjudication_state = "contested"
        requires_review = True
    elif source.challenge_state == "failed" and leader != "bear":
        adjudication_state = "challenge_conflict"
        requires_review = True
    elif source.challenge_state == "passed" and leader == "bear":
        adjudication_state = "challenge_conflict"
        requires_review = True
    else:
        adjudication_state = f"{leader}_leading"
        requires_review = False

    adjudicated_confidence = _bounded(
        (0.55 * leading_score)
        + (0.25 * margin)
        + (0.20 * (1.0 - conflict))
    )

    rationale = (
        f"bull score: {bull.score:.6f}",
        f"bear score: {bear.score:.6f}",
        f"neutral score: {neutral.score:.6f}",
        f"leading position: {leader}",
        f"debate margin: {margin:.6f}",
        f"debate conflict: {conflict:.6f}",
        f"adjudicated confidence: {adjudicated_confidence:.6f}",
        "adjudication is observational and cannot authorize action",
    )

    body = {
        "finding_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_challenge_hash": source.finding_hash,
        "original_narrative_state": source.original_narrative_state,
        "bull": bull,
        "bear": bear,
        "neutral": neutral,
        "leading_position": leader,
        "debate_margin": margin,
        "debate_conflict": conflict,
        "adjudicated_confidence": adjudicated_confidence,
        "adjudication_state": adjudication_state,
        "requires_human_review": requires_review,
        "adjudication_rationale": rationale,
        "read_only": True,
    }
    return OracleDebateFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_debate_position(position: OracleDebatePosition) -> bool:
    body = asdict(position)
    supplied = body.pop("position_hash")
    if _stable_hash(body) != supplied:
        raise OracleDebateSynthesisInvariantError(
            "debate position hash mismatch"
        )
    if position.position not in {"bull", "bear", "neutral"}:
        raise OracleDebateSynthesisInvariantError(
            "unsupported debate position"
        )
    for value in (position.score, position.confidence):
        if not 0.0 <= value <= 1.0:
            raise OracleDebateSynthesisInvariantError(
                "debate position metric outside bounded range"
            )
    if not position.supporting_points:
        raise OracleDebateSynthesisInvariantError(
            "debate supporting points missing"
        )
    if not position.opposing_points:
        raise OracleDebateSynthesisInvariantError(
            "debate opposing points missing"
        )
    if not position.required_confirmation:
        raise OracleDebateSynthesisInvariantError(
            "debate confirmation requirements missing"
        )
    return True


def verify_debate_finding(finding: OracleDebateFinding) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleDebateSynthesisInvariantError(
            "debate finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleDebateSynthesisInvariantError(
            "debate finding is not read-only"
        )
    for position in (finding.bull, finding.bear, finding.neutral):
        verify_debate_position(position)
    if finding.leading_position not in {"bull", "bear", "neutral"}:
        raise OracleDebateSynthesisInvariantError(
            "invalid leading debate position"
        )
    for value in (
        finding.debate_margin,
        finding.debate_conflict,
        finding.adjudicated_confidence,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleDebateSynthesisInvariantError(
                "debate metric outside bounded range"
            )
    scores = {
        "bull": finding.bull.score,
        "bear": finding.bear.score,
        "neutral": finding.neutral.score,
    }
    expected_leader = sorted(
        scores.items(),
        key=lambda item: (-item[1], item[0]),
    )[0][0]
    if finding.leading_position != expected_leader:
        raise OracleDebateSynthesisInvariantError(
            "leading debate position mismatch"
        )
    if not finding.source_challenge_hash:
        raise OracleDebateSynthesisInvariantError(
            "challenge lineage missing"
        )
    return True


def _aggregate(
    findings: tuple[OracleDebateFinding, ...],
) -> tuple[str, float, str, str]:
    if not findings:
        return (
            "neutral",
            0.0,
            "no_debate_evidence",
            "No certified challenge findings were available for debate.",
        )

    totals = {
        position: sum(
            getattr(item, position).score for item in findings
        )
        for position in ("bull", "bear", "neutral")
    }
    ordered = sorted(
        totals.items(),
        key=lambda item: (-item[1], item[0]),
    )
    leader = ordered[0][0]
    total_score = sum(totals.values())
    confidence = _bounded(
        ordered[0][1] / total_score if total_score else 0.0
    )
    contested = sum(
        item.adjudication_state in {"contested", "challenge_conflict"}
        for item in findings
    )
    state = (
        "aggregate_debate_contested"
        if contested
        else f"aggregate_{leader}_leading"
    )
    summary = (
        f"{len(findings)} debate findings; aggregate {leader} position "
        f"leads with normalized confidence {confidence:.6f}; "
        f"{contested} findings remain contested."
    )
    return leader, confidence, state, summary


def build_debate_synthesis_report(
    repository_root: str | Path,
    query: str,
    *,
    challenge_report: OracleNarrativeChallengeReport | None = None,
) -> OracleDebateSynthesisReport:
    root = Path(repository_root).resolve()
    source = challenge_report
    if source is None:
        source = build_narrative_challenge_report(root, query)
    verify_narrative_challenge_report(source)

    findings = tuple(
        _build_finding(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    for finding in findings:
        verify_debate_finding(finding)

    leader, confidence, state, summary = _aggregate(findings)
    bull_count = sum(item.leading_position == "bull" for item in findings)
    bear_count = sum(item.leading_position == "bear" for item in findings)
    neutral_count = sum(item.leading_position == "neutral" for item in findings)
    contested_count = sum(
        item.adjudication_state in {"contested", "challenge_conflict"}
        for item in findings
    )
    human_review_count = sum(item.requires_human_review for item in findings)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "challenge_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "bull_leading_count": bull_count,
        "bear_leading_count": bear_count,
        "neutral_leading_count": neutral_count,
        "contested_count": contested_count,
        "human_review_count": human_review_count,
        "aggregate_leading_position": leader,
        "aggregate_confidence": confidence,
        "debate_state": state,
        "debate_summary": summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleDebateSynthesisReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_debate_synthesis_report(report)
    return report


def verify_debate_synthesis_report(
    report: OracleDebateSynthesisReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleDebateSynthesisInvariantError(
            "debate synthesis report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleDebateSynthesisInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleDebateSynthesisInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleDebateSynthesisInvariantError(
            "debate report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleDebateSynthesisInvariantError(
            "forbidden runtime capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleDebateSynthesisInvariantError(
            "debate finding count mismatch"
        )
    expected = {
        "bull": report.bull_leading_count,
        "bear": report.bear_leading_count,
        "neutral": report.neutral_leading_count,
    }
    for position, count in expected.items():
        actual = sum(
            item.leading_position == position
            for item in report.findings
        )
        if actual != count:
            raise OracleDebateSynthesisInvariantError(
                f"{position} leading count mismatch"
            )
    if sum(expected.values()) != report.finding_count:
        raise OracleDebateSynthesisInvariantError(
            "classified debate count mismatch"
        )
    actual_contested = sum(
        item.adjudication_state in {"contested", "challenge_conflict"}
        for item in report.findings
    )
    if actual_contested != report.contested_count:
        raise OracleDebateSynthesisInvariantError(
            "contested debate count mismatch"
        )
    actual_review = sum(
        item.requires_human_review for item in report.findings
    )
    if actual_review != report.human_review_count:
        raise OracleDebateSynthesisInvariantError(
            "human review count mismatch"
        )
    if report.aggregate_leading_position not in {
        "bull", "bear", "neutral"
    }:
        raise OracleDebateSynthesisInvariantError(
            "invalid aggregate debate position"
        )
    if not 0.0 <= report.aggregate_confidence <= 1.0:
        raise OracleDebateSynthesisInvariantError(
            "aggregate confidence outside bounded range"
        )
    for finding in report.findings:
        verify_debate_finding(finding)
    return True
