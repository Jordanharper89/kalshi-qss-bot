from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_cross_market_uncertainty_contradiction_synthesis import (
    OracleUncertaintyContradictionFinding,
    OracleUncertaintyContradictionInvariantError,
    OracleUncertaintyContradictionReport,
    build_uncertainty_contradiction_report,
    verify_uncertainty_contradiction_report,
)

SCHEMA_VERSION = "OIT-017"
ENGINE_ID = "OIT-017"
POLICY_ID = "oracle.cross-market-narrative-evolution-intelligence.v1"


class OracleNarrativeEvolutionInvariantError(
    OracleUncertaintyContradictionInvariantError
):
    pass


@dataclass(frozen=True)
class OracleNarrativeEvolutionFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_finding_hash: str
    narrative_state: str
    narrative_direction: str
    narrative_strength: float
    narrative_stability: float
    reversal_risk: float
    contradiction_pressure: float
    uncertainty_pressure: float
    evidence_support: float
    requires_monitoring: bool
    evolution_signals: tuple[str, ...]
    rationale: tuple[str, ...]
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleNarrativeEvolutionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    uncertainty_report_hash: str
    findings: tuple[OracleNarrativeEvolutionFinding, ...]
    finding_count: int
    strengthening_count: int
    weakening_count: int
    fragmented_count: int
    reversing_count: int
    stable_count: int
    monitoring_required_count: int
    narrative_state: str
    narrative_summary: str
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


def _classify_narrative(
    source: OracleUncertaintyContradictionFinding,
) -> tuple[str, str, float, float, float, tuple[str, ...], tuple[str, ...]]:
    contradiction = source.contradiction_severity
    uncertainty = source.uncertainty_score
    evidence_support = _bounded(
        (0.65 * source.evidence_completeness)
        + (0.35 * (1.0 - source.confidence_gap))
    )
    stability = _bounded(
        (0.55 * evidence_support)
        + (0.25 * (1.0 - uncertainty))
        + (0.20 * (1.0 - contradiction))
    )
    reversal_risk = _bounded(
        (0.50 * contradiction)
        + (0.35 * uncertainty)
        + (0.15 * (1.0 - evidence_support))
    )

    signals: list[str] = []
    rationale = [
        f"evidence support: {evidence_support:.6f}",
        f"narrative stability: {stability:.6f}",
        f"reversal risk: {reversal_risk:.6f}",
        f"contradiction pressure: {contradiction:.6f}",
        f"uncertainty pressure: {uncertainty:.6f}",
    ]

    if contradiction >= 0.75 and reversal_risk >= 0.65:
        state = "reversing"
        direction = "opposing_evidence_dominant"
        strength = _bounded(reversal_risk)
        signals.extend(
            (
                "material contradiction dominates current narrative",
                "directional reversal risk exceeds stability",
            )
        )
    elif contradiction >= 0.45 and uncertainty >= 0.45:
        state = "fragmented"
        direction = "competing_interpretations"
        strength = _bounded(max(contradiction, uncertainty))
        signals.extend(
            (
                "conflicting evidence supports multiple interpretations",
                "narrative consensus is unstable",
            )
        )
    elif evidence_support >= 0.65 and uncertainty <= 0.40:
        state = "strengthening"
        direction = "support_accumulating"
        strength = _bounded(
            (0.60 * evidence_support)
            + (0.40 * stability)
        )
        signals.extend(
            (
                "evidence support exceeds uncertainty pressure",
                "narrative consistency is increasing",
            )
        )
    elif evidence_support < 0.45 or uncertainty >= 0.65:
        state = "weakening"
        direction = "support_eroding"
        strength = _bounded(
            (0.55 * (1.0 - evidence_support))
            + (0.45 * uncertainty)
        )
        signals.extend(
            (
                "supporting evidence is incomplete or eroding",
                "uncertainty pressure exceeds narrative support",
            )
        )
    else:
        state = "stable"
        direction = "bounded_continuity"
        strength = stability
        signals.extend(
            (
                "support and uncertainty remain within bounded range",
                "no material reversal signal detected",
            )
        )

    rationale.append(
        "narrative classification is deterministic and observational"
    )
    return (
        state,
        direction,
        strength,
        stability,
        reversal_risk,
        tuple(signals),
        tuple(rationale),
    )


def _build_finding(
    source: OracleUncertaintyContradictionFinding,
    index: int,
) -> OracleNarrativeEvolutionFinding:
    (
        narrative_state,
        narrative_direction,
        narrative_strength,
        narrative_stability,
        reversal_risk,
        signals,
        rationale,
    ) = _classify_narrative(source)

    evidence_support = _bounded(
        (0.65 * source.evidence_completeness)
        + (0.35 * (1.0 - source.confidence_gap))
    )

    body = {
        "finding_index": index,
        "cause_record_id": source.cause_record_id,
        "effect_record_id": source.effect_record_id,
        "source_finding_hash": source.finding_hash,
        "narrative_state": narrative_state,
        "narrative_direction": narrative_direction,
        "narrative_strength": narrative_strength,
        "narrative_stability": narrative_stability,
        "reversal_risk": reversal_risk,
        "contradiction_pressure": source.contradiction_severity,
        "uncertainty_pressure": source.uncertainty_score,
        "evidence_support": evidence_support,
        "requires_monitoring": (
            narrative_state in {"weakening", "fragmented", "reversing"}
            or reversal_risk >= 0.50
        ),
        "evolution_signals": signals,
        "rationale": rationale,
        "read_only": True,
    }
    return OracleNarrativeEvolutionFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_narrative_evolution_finding(
    finding: OracleNarrativeEvolutionFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleNarrativeEvolutionInvariantError(
            "narrative finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleNarrativeEvolutionInvariantError(
            "narrative finding is not read-only"
        )
    for value in (
        finding.narrative_strength,
        finding.narrative_stability,
        finding.reversal_risk,
        finding.contradiction_pressure,
        finding.uncertainty_pressure,
        finding.evidence_support,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleNarrativeEvolutionInvariantError(
                "narrative metric outside bounded range"
            )
    if not finding.source_finding_hash:
        raise OracleNarrativeEvolutionInvariantError(
            "source uncertainty lineage missing"
        )
    if not finding.evolution_signals:
        raise OracleNarrativeEvolutionInvariantError(
            "narrative evolution signals missing"
        )
    return True


def _summary(
    findings: tuple[OracleNarrativeEvolutionFinding, ...],
) -> tuple[str, str]:
    if not findings:
        return (
            "no_narrative_evidence",
            "No certified uncertainty findings were available for narrative analysis.",
        )

    counts = {
        state: sum(item.narrative_state == state for item in findings)
        for state in (
            "strengthening",
            "weakening",
            "fragmented",
            "reversing",
            "stable",
        )
    }

    if counts["reversing"]:
        state = "narrative_reversal_detected"
    elif counts["fragmented"]:
        state = "narrative_fragmentation_detected"
    elif counts["weakening"] > counts["strengthening"]:
        state = "narrative_support_weakening"
    elif counts["strengthening"]:
        state = "narrative_support_strengthening"
    else:
        state = "narrative_bounded_stability"

    monitored = sum(item.requires_monitoring for item in findings)
    summary = (
        f"{len(findings)} narrative findings: "
        f"{counts['strengthening']} strengthening, "
        f"{counts['weakening']} weakening, "
        f"{counts['fragmented']} fragmented, "
        f"{counts['reversing']} reversing, "
        f"{counts['stable']} stable; "
        f"{monitored} require continued monitoring."
    )
    return state, summary


def build_narrative_evolution_report(
    repository_root: str | Path,
    query: str,
    *,
    uncertainty_report: OracleUncertaintyContradictionReport | None = None,
) -> OracleNarrativeEvolutionReport:
    root = Path(repository_root).resolve()
    source = uncertainty_report
    if source is None:
        source = build_uncertainty_contradiction_report(root, query)
    verify_uncertainty_contradiction_report(source)

    findings = tuple(
        _build_finding(item, index)
        for index, item in enumerate(source.findings, start=1)
    )
    for finding in findings:
        verify_narrative_evolution_finding(finding)

    narrative_state, narrative_summary = _summary(findings)
    counts = {
        state: sum(item.narrative_state == state for item in findings)
        for state in (
            "strengthening",
            "weakening",
            "fragmented",
            "reversing",
            "stable",
        )
    }

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "uncertainty_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "strengthening_count": counts["strengthening"],
        "weakening_count": counts["weakening"],
        "fragmented_count": counts["fragmented"],
        "reversing_count": counts["reversing"],
        "stable_count": counts["stable"],
        "monitoring_required_count": sum(
            item.requires_monitoring for item in findings
        ),
        "narrative_state": narrative_state,
        "narrative_summary": narrative_summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleNarrativeEvolutionReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_narrative_evolution_report(report)
    return report


def verify_narrative_evolution_report(
    report: OracleNarrativeEvolutionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleNarrativeEvolutionInvariantError(
            "narrative evolution report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleNarrativeEvolutionInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleNarrativeEvolutionInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleNarrativeEvolutionInvariantError(
            "report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleNarrativeEvolutionInvariantError(
            "forbidden runtime capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleNarrativeEvolutionInvariantError(
            "finding count mismatch"
        )

    expected = {
        "strengthening": report.strengthening_count,
        "weakening": report.weakening_count,
        "fragmented": report.fragmented_count,
        "reversing": report.reversing_count,
        "stable": report.stable_count,
    }
    for state, count in expected.items():
        actual = sum(
            item.narrative_state == state
            for item in report.findings
        )
        if actual != count:
            raise OracleNarrativeEvolutionInvariantError(
                f"{state} narrative count mismatch"
            )
    if sum(expected.values()) != report.finding_count:
        raise OracleNarrativeEvolutionInvariantError(
            "classified narrative count mismatch"
        )

    actual_monitoring = sum(
        item.requires_monitoring for item in report.findings
    )
    if actual_monitoring != report.monitoring_required_count:
        raise OracleNarrativeEvolutionInvariantError(
            "monitoring count mismatch"
        )

    for finding in report.findings:
        verify_narrative_evolution_finding(finding)
    return True
