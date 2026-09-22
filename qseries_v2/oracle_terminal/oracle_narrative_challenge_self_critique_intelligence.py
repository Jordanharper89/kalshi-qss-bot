from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_cross_market_narrative_evolution_intelligence import (
    OracleNarrativeEvolutionFinding,
    OracleNarrativeEvolutionInvariantError,
    OracleNarrativeEvolutionReport,
    build_narrative_evolution_report,
    verify_narrative_evolution_report,
)

SCHEMA_VERSION = "OIT-018"
ENGINE_ID = "OIT-018"
POLICY_ID = "oracle.narrative-challenge-self-critique-intelligence.v1"


class OracleNarrativeChallengeInvariantError(
    OracleNarrativeEvolutionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleNarrativeChallengeFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_narrative_hash: str
    original_narrative_state: str
    challenge_state: str
    fragility_score: float
    counter_evidence_pressure: float
    assumption_risk: float
    falsifiability_score: float
    surviving_confidence: float
    challenge_passed: bool
    fragile_assumptions: tuple[str, ...]
    counter_arguments: tuple[str, ...]
    falsification_tests: tuple[str, ...]
    critique_rationale: tuple[str, ...]
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleNarrativeChallengeReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    narrative_report_hash: str
    findings: tuple[OracleNarrativeChallengeFinding, ...]
    finding_count: int
    passed_count: int
    weakened_count: int
    failed_count: int
    fragile_count: int
    monitoring_required_count: int
    challenge_state: str
    challenge_summary: str
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


def _challenge(
    source: OracleNarrativeEvolutionFinding,
) -> tuple[
    str,
    float,
    float,
    float,
    float,
    float,
    bool,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    contradiction = source.contradiction_pressure
    uncertainty = source.uncertainty_pressure
    reversal = source.reversal_risk
    support_gap = 1.0 - source.evidence_support
    instability = 1.0 - source.narrative_stability

    counter_pressure = _bounded(
        (0.45 * contradiction)
        + (0.30 * reversal)
        + (0.25 * uncertainty)
    )
    assumption_risk = _bounded(
        (0.35 * uncertainty)
        + (0.35 * instability)
        + (0.30 * support_gap)
    )
    fragility = _bounded(
        (0.40 * counter_pressure)
        + (0.35 * assumption_risk)
        + (0.25 * instability)
    )
    falsifiability = _bounded(
        0.55
        + (0.15 if source.evolution_signals else 0.0)
        + (0.15 if source.requires_monitoring else 0.0)
        - (0.20 * uncertainty)
    )
    surviving_confidence = _bounded(
        source.narrative_strength
        * (1.0 - (0.55 * fragility))
        * (1.0 - (0.25 * counter_pressure))
    )

    if fragility >= 0.70 or surviving_confidence < 0.25:
        challenge_state = "failed"
        challenge_passed = False
    elif fragility >= 0.45 or surviving_confidence < 0.50:
        challenge_state = "weakened"
        challenge_passed = False
    else:
        challenge_state = "passed"
        challenge_passed = True

    assumptions: list[str] = []
    if source.evidence_support < 0.60:
        assumptions.append("supporting evidence is representative and sufficiently complete")
    if source.narrative_stability < 0.60:
        assumptions.append("the observed narrative relationship remains stable")
    if source.reversal_risk >= 0.50:
        assumptions.append("opposing evidence will not dominate the narrative")
    if source.uncertainty_pressure >= 0.50:
        assumptions.append("unresolved uncertainty does not conceal a confounder")
    if not assumptions:
        assumptions.append("the observed cross-market relationship persists out of sample")

    counter_arguments: list[str] = []
    if contradiction >= 0.40:
        counter_arguments.append("directional contradiction may invalidate the dominant interpretation")
    if reversal >= 0.50:
        counter_arguments.append("current evidence may represent an early narrative reversal")
    if uncertainty >= 0.50:
        counter_arguments.append("missing evidence may support a materially different explanation")
    if source.narrative_state == "strengthening":
        counter_arguments.append("recent support may be temporary momentum rather than durable structure")
    elif source.narrative_state == "reversing":
        counter_arguments.append("the apparent reversal may be transient hedging or substitution")
    else:
        counter_arguments.append("the narrative may be associative rather than causally durable")

    falsification_tests = (
        "observe whether the proposed effect persists after the cause weakens",
        "seek independent evidence from a separate source and venue",
        "test whether the relationship survives contradictory observations",
        "recalculate after the next certified temporal update",
    )

    rationale = (
        f"counter-evidence pressure: {counter_pressure:.6f}",
        f"assumption risk: {assumption_risk:.6f}",
        f"fragility score: {fragility:.6f}",
        f"falsifiability score: {falsifiability:.6f}",
        f"surviving confidence: {surviving_confidence:.6f}",
        "self-critique cannot modify certified source evidence",
    )

    return (
        challenge_state,
        fragility,
        counter_pressure,
        assumption_risk,
        falsifiability,
        surviving_confidence,
        challenge_passed,
        tuple(assumptions),
        tuple(counter_arguments),
        falsification_tests,
        rationale,
    )


def _build_finding(
    source: OracleNarrativeEvolutionFinding,
    index: int,
) -> OracleNarrativeChallengeFinding:
    (
        challenge_state,
        fragility,
        counter_pressure,
        assumption_risk,
        falsifiability,
        surviving_confidence,
        challenge_passed,
        assumptions,
        counter_arguments,
        falsification_tests,
        rationale,
    ) = _challenge(source)

    body = {
        "finding_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_narrative_hash": source.finding_hash,
        "original_narrative_state": source.narrative_state,
        "challenge_state": challenge_state,
        "fragility_score": fragility,
        "counter_evidence_pressure": counter_pressure,
        "assumption_risk": assumption_risk,
        "falsifiability_score": falsifiability,
        "surviving_confidence": surviving_confidence,
        "challenge_passed": challenge_passed,
        "fragile_assumptions": assumptions,
        "counter_arguments": counter_arguments,
        "falsification_tests": falsification_tests,
        "critique_rationale": rationale,
        "read_only": True,
    }
    return OracleNarrativeChallengeFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_narrative_challenge_finding(
    finding: OracleNarrativeChallengeFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleNarrativeChallengeInvariantError(
            "narrative challenge finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleNarrativeChallengeInvariantError(
            "narrative challenge finding is not read-only"
        )
    for value in (
        finding.fragility_score,
        finding.counter_evidence_pressure,
        finding.assumption_risk,
        finding.falsifiability_score,
        finding.surviving_confidence,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleNarrativeChallengeInvariantError(
                "challenge metric outside bounded range"
            )
    if finding.challenge_passed != (finding.challenge_state == "passed"):
        raise OracleNarrativeChallengeInvariantError(
            "challenge pass state mismatch"
        )
    if not finding.source_narrative_hash:
        raise OracleNarrativeChallengeInvariantError(
            "source narrative lineage missing"
        )
    if not finding.fragile_assumptions:
        raise OracleNarrativeChallengeInvariantError(
            "fragile assumptions missing"
        )
    if not finding.counter_arguments:
        raise OracleNarrativeChallengeInvariantError(
            "counter arguments missing"
        )
    if not finding.falsification_tests:
        raise OracleNarrativeChallengeInvariantError(
            "falsification tests missing"
        )
    return True


def _summary(
    findings: tuple[OracleNarrativeChallengeFinding, ...],
) -> tuple[str, str]:
    if not findings:
        return (
            "no_narratives_to_challenge",
            "No certified narrative findings were available for self-critique.",
        )

    passed = sum(item.challenge_state == "passed" for item in findings)
    weakened = sum(item.challenge_state == "weakened" for item in findings)
    failed = sum(item.challenge_state == "failed" for item in findings)
    fragile = sum(item.fragility_score >= 0.45 for item in findings)
    monitoring = sum(
        item.challenge_state != "passed"
        or item.fragility_score >= 0.45
        for item in findings
    )

    if failed:
        state = "one_or_more_narratives_failed_challenge"
    elif weakened:
        state = "one_or_more_narratives_weakened"
    else:
        state = "all_narratives_survived_bounded_challenge"

    return (
        state,
        (
            f"{len(findings)} challenged narratives: "
            f"{passed} passed, {weakened} weakened, {failed} failed; "
            f"{fragile} fragile and {monitoring} require monitoring."
        ),
    )


def build_narrative_challenge_report(
    repository_root: str | Path,
    query: str,
    *,
    narrative_report: OracleNarrativeEvolutionReport | None = None,
) -> OracleNarrativeChallengeReport:
    root = Path(repository_root).resolve()
    source = narrative_report
    if source is None:
        source = build_narrative_evolution_report(root, query)
    verify_narrative_evolution_report(source)

    findings = tuple(
        _build_finding(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    for finding in findings:
        verify_narrative_challenge_finding(finding)

    challenge_state, challenge_summary = _summary(findings)
    passed = sum(item.challenge_state == "passed" for item in findings)
    weakened = sum(item.challenge_state == "weakened" for item in findings)
    failed = sum(item.challenge_state == "failed" for item in findings)
    fragile = sum(item.fragility_score >= 0.45 for item in findings)
    monitoring = sum(
        item.challenge_state != "passed"
        or item.fragility_score >= 0.45
        for item in findings
    )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "narrative_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "passed_count": passed,
        "weakened_count": weakened,
        "failed_count": failed,
        "fragile_count": fragile,
        "monitoring_required_count": monitoring,
        "challenge_state": challenge_state,
        "challenge_summary": challenge_summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleNarrativeChallengeReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_narrative_challenge_report(report)
    return report


def verify_narrative_challenge_report(
    report: OracleNarrativeChallengeReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleNarrativeChallengeInvariantError(
            "narrative challenge report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleNarrativeChallengeInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleNarrativeChallengeInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleNarrativeChallengeInvariantError(
            "report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleNarrativeChallengeInvariantError(
            "forbidden runtime capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleNarrativeChallengeInvariantError(
            "finding count mismatch"
        )

    expected = {
        "passed": report.passed_count,
        "weakened": report.weakened_count,
        "failed": report.failed_count,
    }
    for state, count in expected.items():
        actual = sum(
            item.challenge_state == state
            for item in report.findings
        )
        if actual != count:
            raise OracleNarrativeChallengeInvariantError(
                f"{state} challenge count mismatch"
            )
    if sum(expected.values()) != report.finding_count:
        raise OracleNarrativeChallengeInvariantError(
            "classified challenge count mismatch"
        )

    actual_fragile = sum(
        item.fragility_score >= 0.45 for item in report.findings
    )
    if actual_fragile != report.fragile_count:
        raise OracleNarrativeChallengeInvariantError(
            "fragile finding count mismatch"
        )
    actual_monitoring = sum(
        item.challenge_state != "passed"
        or item.fragility_score >= 0.45
        for item in report.findings
    )
    if actual_monitoring != report.monitoring_required_count:
        raise OracleNarrativeChallengeInvariantError(
            "monitoring count mismatch"
        )

    for finding in report.findings:
        verify_narrative_challenge_finding(finding)
    return True
