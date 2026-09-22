from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_cross_market_causal_intelligence_analysis import (
    MAX_CAUSAL_CONFIDENCE,
    OracleCausalHypothesis,
    OracleCausalIntelligenceInvariantError,
    OracleCausalIntelligenceReport,
    build_causal_intelligence_report,
    verify_causal_intelligence_report,
)

SCHEMA_VERSION = "OIT-016"
ENGINE_ID = "OIT-016"
POLICY_ID = "oracle.cross-market-uncertainty-contradiction-synthesis.v1"


class OracleUncertaintyContradictionInvariantError(
    OracleCausalIntelligenceInvariantError
):
    pass


@dataclass(frozen=True)
class OracleUncertaintyContradictionFinding:
    finding_index: int
    cause_record_id: str
    effect_record_id: str
    source_hypothesis_hash: str
    evidence_class: str
    contradiction_state: str
    uncertainty_state: str
    uncertainty_score: float
    confidence_gap: float
    evidence_completeness: float
    contradiction_severity: float
    requires_additional_evidence: bool
    unresolved_questions: tuple[str, ...]
    rationale: tuple[str, ...]
    read_only: bool
    finding_hash: str


@dataclass(frozen=True)
class OracleUncertaintyContradictionReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    causal_report_hash: str
    findings: tuple[OracleUncertaintyContradictionFinding, ...]
    finding_count: int
    high_uncertainty_count: int
    moderate_uncertainty_count: int
    low_uncertainty_count: int
    material_contradiction_count: int
    unresolved_evidence_count: int
    synthesis_state: str
    synthesis_summary: str
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


def _classify_uncertainty(score: float) -> str:
    if score >= 0.67:
        return "high"
    if score >= 0.34:
        return "moderate"
    return "low"


def _finding(
    hypothesis: OracleCausalHypothesis,
    index: int,
) -> OracleUncertaintyContradictionFinding:
    confidence_gap = _bounded(1.0 - hypothesis.causal_confidence)

    limitation_penalty = min(0.35, 0.07 * len(hypothesis.limitations))
    evidence_completeness = _bounded(
        hypothesis.causal_confidence
        + (0.10 if hypothesis.supports_causation else 0.0)
        - limitation_penalty
    )

    contradiction_severity = 0.0
    contradiction_state = "none_detected"
    if hypothesis.contradicts_causation:
        contradiction_severity = _bounded(
            0.45
            + (0.30 * hypothesis.causal_confidence)
            + (
                0.15
                if hypothesis.evidence_class == "suppressive"
                else 0.0
            )
        )
        contradiction_state = (
            "material_directional_contradiction"
            if contradiction_severity >= 0.60
            else "bounded_directional_contradiction"
        )
    elif hypothesis.evidence_class == "associative":
        contradiction_state = "not_a_contradiction_temporal_order_missing"
    elif hypothesis.evidence_class == "insufficient":
        contradiction_state = "not_a_contradiction_evidence_insufficient"

    uncertainty_score = _bounded(
        (0.60 * confidence_gap)
        + (0.25 * (1.0 - evidence_completeness))
        + (0.15 * contradiction_severity)
    )
    uncertainty_state = _classify_uncertainty(uncertainty_score)

    unresolved = []
    if hypothesis.causal_confidence < 0.50:
        unresolved.append("What independent evidence would strengthen the hypothesis?")
    if "mechanism has not yet been independently verified" in hypothesis.limitations:
        unresolved.append("What mechanism links the proposed cause to the effect?")
    if hypothesis.contradicts_causation:
        unresolved.append("Is the inverse movement causal, hedging, substitution, or confounding?")
    if hypothesis.evidence_class in {"associative", "insufficient"}:
        unresolved.append("Can stable temporal precedence be established?")
    if "unobserved confounders may explain the relationship" in hypothesis.limitations:
        unresolved.append("Which confounders could explain both records?")
    if not unresolved:
        unresolved.append("What evidence would falsify the current causal interpretation?")

    rationale = (
        f"causal confidence: {hypothesis.causal_confidence:.6f}",
        f"confidence gap: {confidence_gap:.6f}",
        f"evidence completeness: {evidence_completeness:.6f}",
        f"contradiction severity: {contradiction_severity:.6f}",
        f"uncertainty score: {uncertainty_score:.6f}",
        (
            "uncertainty reflects incomplete or conflicting evidence, "
            "not stochastic model training"
        ),
    )

    body = {
        "finding_index": index,
        "cause_record_id": hypothesis.cause_record_id,
        "effect_record_id": hypothesis.effect_record_id,
        "source_hypothesis_hash": hypothesis.hypothesis_hash,
        "evidence_class": hypothesis.evidence_class,
        "contradiction_state": contradiction_state,
        "uncertainty_state": uncertainty_state,
        "uncertainty_score": uncertainty_score,
        "confidence_gap": confidence_gap,
        "evidence_completeness": evidence_completeness,
        "contradiction_severity": contradiction_severity,
        "requires_additional_evidence": uncertainty_state != "low"
        or contradiction_severity > 0.0,
        "unresolved_questions": tuple(unresolved),
        "rationale": rationale,
        "read_only": True,
    }
    return OracleUncertaintyContradictionFinding(
        **body,
        finding_hash=_stable_hash(body),
    )


def verify_uncertainty_contradiction_finding(
    finding: OracleUncertaintyContradictionFinding,
) -> bool:
    body = asdict(finding)
    supplied = body.pop("finding_hash")
    if _stable_hash(body) != supplied:
        raise OracleUncertaintyContradictionInvariantError(
            "uncertainty finding hash mismatch"
        )
    if not finding.read_only:
        raise OracleUncertaintyContradictionInvariantError(
            "uncertainty finding is not read-only"
        )
    for value in (
        finding.uncertainty_score,
        finding.confidence_gap,
        finding.evidence_completeness,
        finding.contradiction_severity,
    ):
        if not 0.0 <= value <= 1.0:
            raise OracleUncertaintyContradictionInvariantError(
                "bounded uncertainty metric outside range"
            )
    if not finding.source_hypothesis_hash:
        raise OracleUncertaintyContradictionInvariantError(
            "source hypothesis lineage missing"
        )
    if not finding.unresolved_questions:
        raise OracleUncertaintyContradictionInvariantError(
            "uncertainty finding lacks unresolved questions"
        )
    return True


def _summary(
    findings: tuple[OracleUncertaintyContradictionFinding, ...],
) -> tuple[str, str]:
    if not findings:
        return (
            "no_causal_hypotheses",
            "No certified causal hypotheses were available for uncertainty synthesis.",
        )
    high = sum(item.uncertainty_state == "high" for item in findings)
    moderate = sum(item.uncertainty_state == "moderate" for item in findings)
    low = sum(item.uncertainty_state == "low" for item in findings)
    contradictions = sum(
        item.contradiction_severity >= 0.60 for item in findings
    )
    unresolved = sum(item.requires_additional_evidence for item in findings)

    if contradictions:
        state = "material_contradictions_require_review"
    elif high:
        state = "high_uncertainty_requires_more_evidence"
    elif moderate:
        state = "bounded_uncertainty_present"
    else:
        state = "low_uncertainty_bounded_evidence"

    return (
        state,
        (
            f"{len(findings)} findings: {high} high uncertainty, "
            f"{moderate} moderate, {low} low; "
            f"{contradictions} material contradictions and "
            f"{unresolved} findings requiring additional evidence."
        ),
    )


def build_uncertainty_contradiction_report(
    repository_root: str | Path,
    query: str,
    *,
    causal_report: OracleCausalIntelligenceReport | None = None,
) -> OracleUncertaintyContradictionReport:
    root = Path(repository_root).resolve()
    source = causal_report
    if source is None:
        source = build_causal_intelligence_report(root, query)
    verify_causal_intelligence_report(source)

    findings = tuple(
        _finding(hypothesis, index)
        for index, hypothesis in enumerate(source.hypotheses, start=1)
    )
    for finding in findings:
        verify_uncertainty_contradiction_finding(finding)

    synthesis_state, synthesis_summary = _summary(findings)
    high = sum(item.uncertainty_state == "high" for item in findings)
    moderate = sum(item.uncertainty_state == "moderate" for item in findings)
    low = sum(item.uncertainty_state == "low" for item in findings)
    material = sum(
        item.contradiction_severity >= 0.60 for item in findings
    )
    unresolved = sum(item.requires_additional_evidence for item in findings)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "causal_report_hash": source.report_hash,
        "findings": findings,
        "finding_count": len(findings),
        "high_uncertainty_count": high,
        "moderate_uncertainty_count": moderate,
        "low_uncertainty_count": low,
        "material_contradiction_count": material,
        "unresolved_evidence_count": unresolved,
        "synthesis_state": synthesis_state,
        "synthesis_summary": synthesis_summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleUncertaintyContradictionReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_uncertainty_contradiction_report(report)
    return report


def verify_uncertainty_contradiction_report(
    report: OracleUncertaintyContradictionReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleUncertaintyContradictionInvariantError(
            "uncertainty contradiction report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleUncertaintyContradictionInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleUncertaintyContradictionInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleUncertaintyContradictionInvariantError(
            "report is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleUncertaintyContradictionInvariantError(
            "forbidden runtime capability enabled"
        )
    if report.finding_count != len(report.findings):
        raise OracleUncertaintyContradictionInvariantError(
            "finding count mismatch"
        )

    expected = {
        "high": report.high_uncertainty_count,
        "moderate": report.moderate_uncertainty_count,
        "low": report.low_uncertainty_count,
    }
    for state, count in expected.items():
        actual = sum(
            item.uncertainty_state == state
            for item in report.findings
        )
        if actual != count:
            raise OracleUncertaintyContradictionInvariantError(
                f"{state} uncertainty count mismatch"
            )
    if sum(expected.values()) != report.finding_count:
        raise OracleUncertaintyContradictionInvariantError(
            "classified uncertainty count mismatch"
        )

    actual_material = sum(
        item.contradiction_severity >= 0.60
        for item in report.findings
    )
    if actual_material != report.material_contradiction_count:
        raise OracleUncertaintyContradictionInvariantError(
            "material contradiction count mismatch"
        )
    actual_unresolved = sum(
        item.requires_additional_evidence
        for item in report.findings
    )
    if actual_unresolved != report.unresolved_evidence_count:
        raise OracleUncertaintyContradictionInvariantError(
            "unresolved evidence count mismatch"
        )
    for finding in report.findings:
        verify_uncertainty_contradiction_finding(finding)
    return True
