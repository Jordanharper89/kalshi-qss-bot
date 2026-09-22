from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_contradiction_and_uncertainty_inspection import (
    OracleContradictionAndUncertaintyReport,
    OracleContradictionInspectionInvariantError,
    OracleEvidenceClaim,
    build_contradiction_and_uncertainty_report,
    verify_contradiction_and_uncertainty_report,
    verify_evidence_claim,
)

SCHEMA_VERSION = "OIT-012"
ENGINE_ID = "OIT-012"
POLICY_ID = "oracle.adversarial-perspective-debate-and-challenge.v1"

PERSPECTIVES = ("bull", "bear", "neutral", "challenge")


class OracleAdversarialDebateInvariantError(
    OracleContradictionInspectionInvariantError
):
    pass


@dataclass(frozen=True)
class OraclePerspectiveEvidenceReference:
    evidence_index: int
    record_id: str
    claim_kind: str
    claim_path: str
    claim_value: Any
    claim_hash: str
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    evidence_hash: str
    read_only: bool
    reference_hash: str


@dataclass(frozen=True)
class OracleDebatePerspective:
    perspective: str
    position: str
    evidence_references: tuple[OraclePerspectiveEvidenceReference, ...]
    evidence_reference_count: int
    reasoning_text: str
    limitations: tuple[str, ...]
    supported: bool
    read_only: bool
    perspective_hash: str


@dataclass(frozen=True)
class OracleAdversarialDebateReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    answer_text: str
    answer_hash: str
    query_plan_hash: str
    query_result_hash: str
    explainability_report_hash: str
    contradiction_report_hash: str
    perspectives: tuple[OracleDebatePerspective, ...]
    perspective_count: int
    contradiction_count: int
    uncertainty_level: str
    corroboration_state: str
    debate_ready: bool
    dominant_perspective: str
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
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
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


def _normalized(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value).strip().lower()


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _reference_from_claim(
    claim: OracleEvidenceClaim,
) -> OraclePerspectiveEvidenceReference:
    verify_evidence_claim(claim)
    body = {
        "evidence_index": claim.evidence_index,
        "record_id": claim.record_id,
        "claim_kind": claim.claim_kind,
        "claim_path": claim.claim_path,
        "claim_value": _canonical(claim.claim_value),
        "claim_hash": claim.claim_hash,
        "artifact_relative_path": claim.artifact_relative_path,
        "artifact_sha256": claim.artifact_sha256,
        "record_hash": claim.record_hash,
        "evidence_hash": claim.evidence_hash,
        "read_only": True,
    }
    reference = OraclePerspectiveEvidenceReference(
        **body,
        reference_hash=_stable_hash(body),
    )
    verify_perspective_evidence_reference(reference)
    return reference


def verify_perspective_evidence_reference(
    reference: OraclePerspectiveEvidenceReference,
) -> bool:
    body = asdict(reference)
    supplied = body.pop("reference_hash")
    if _stable_hash(body) != supplied:
        raise OracleAdversarialDebateInvariantError(
            "OIT-012 evidence-reference hash mismatch"
        )
    if not reference.read_only:
        raise OracleAdversarialDebateInvariantError(
            "perspective evidence reference is not read-only"
        )
    if (
        len(reference.artifact_sha256) != 64
        or not reference.record_hash
        or not reference.evidence_hash
        or not reference.claim_hash
    ):
        raise OracleAdversarialDebateInvariantError(
            "perspective evidence lineage is incomplete"
        )
    return True


def _bull_claim(claim: OracleEvidenceClaim) -> bool:
    value = _normalized(claim.claim_value)
    if claim.claim_kind == "stance":
        return value in {"bull", "yes", "long", "positive"}
    if claim.claim_kind == "probability":
        number = _numeric(claim.claim_value)
        return number is not None and number >= 0.55
    if claim.claim_kind == "status":
        return value in {"won", "confirmed", "resolved_yes", "active", "open"}
    return False


def _bear_claim(claim: OracleEvidenceClaim) -> bool:
    value = _normalized(claim.claim_value)
    if claim.claim_kind == "stance":
        return value in {"bear", "no", "short", "negative"}
    if claim.claim_kind == "probability":
        number = _numeric(claim.claim_value)
        return number is not None and number <= 0.45
    if claim.claim_kind == "status":
        return value in {"lost", "rejected", "resolved_no", "closed", "failed"}
    return False


def _neutral_claim(claim: OracleEvidenceClaim) -> bool:
    value = _normalized(claim.claim_value)
    if claim.claim_kind == "stance":
        return value in {"neutral", "mixed", "uncertain", "hold"}
    if claim.claim_kind == "probability":
        number = _numeric(claim.claim_value)
        return number is not None and 0.45 < number < 0.55
    return False


def _build_perspective(
    *,
    perspective: str,
    report: OracleContradictionAndUncertaintyReport,
) -> OracleDebatePerspective:
    if perspective not in PERSPECTIVES:
        raise OracleAdversarialDebateInvariantError(
            f"unsupported perspective: {perspective}"
        )

    if perspective == "bull":
        claims = tuple(claim for claim in report.claims if _bull_claim(claim))
        position = "supportive"
        if claims:
            reasoning = (
                "The bull case is supported by admitted claims indicating "
                "positive direction, probability above the bounded bullish "
                "threshold, or a favorable/open status."
            )
        else:
            reasoning = (
                "No admitted bounded claim directly supports a bull case."
            )
        limits = (
            "Bull evidence may originate from one source.",
            "A favorable claim is not proof of outcome.",
            "Contradictory bear evidence remains material when present.",
        )
    elif perspective == "bear":
        claims = tuple(claim for claim in report.claims if _bear_claim(claim))
        position = "opposing"
        if claims:
            reasoning = (
                "The bear case is supported by admitted claims indicating "
                "negative direction, probability below the bounded bearish "
                "threshold, or an unfavorable/closed status."
            )
        else:
            reasoning = (
                "No admitted bounded claim directly supports a bear case."
            )
        limits = (
            "Bear evidence may originate from one source.",
            "A negative claim is not proof of failure.",
            "Contradictory bull evidence remains material when present.",
        )
    elif perspective == "neutral":
        claims = tuple(
            claim for claim in report.claims
            if _neutral_claim(claim)
        )
        position = "uncertain"
        if claims:
            reasoning = (
                "The neutral case is supported by admitted claims explicitly "
                "marked neutral or probabilities near the bounded midpoint."
            )
        elif report.contradiction_count:
            claims = report.claims
            reasoning = (
                "The neutral case is supported indirectly by material conflict "
                "between admitted claims; Oracle does not collapse contested "
                "evidence into a directional conclusion."
            )
        else:
            reasoning = (
                "No explicit neutral claim exists. Neutrality is retained as "
                "a limitation because absence of contradiction does not prove "
                "a directional conclusion."
            )
        limits = (
            "Neutrality may reflect missing evidence rather than balance.",
            "Source independence has not been established.",
            "Freshness is limited to admitted artifact contents.",
        )
    else:
        claims = report.claims
        position = "self_critique"
        if report.contradiction_count:
            reasoning = (
                f"The challenge view identifies {report.contradiction_count} "
                "material contradiction pair(s), requiring reconciliation "
                "before treating the grounded answer as stable."
            )
        elif report.evidence_count <= 1:
            reasoning = (
                "The challenge view identifies insufficient independent "
                "corroboration because the answer has zero or one admitted "
                "supporting evidence record."
            )
        else:
            reasoning = (
                "The challenge view found no material bounded contradiction, "
                "but still rejects any inference of factual truth, source "
                "independence, or completeness."
            )
        limits = tuple(report.uncertainty_reasons) or (
            "No explicit uncertainty reason was emitted upstream.",
        )

    references = tuple(_reference_from_claim(claim) for claim in claims)
    body = {
        "perspective": perspective,
        "position": position,
        "evidence_references": references,
        "evidence_reference_count": len(references),
        "reasoning_text": reasoning,
        "limitations": tuple(limits),
        "supported": bool(references),
        "read_only": True,
    }
    result = OracleDebatePerspective(
        **body,
        perspective_hash=_stable_hash(body),
    )
    verify_debate_perspective(result)
    return result


def verify_debate_perspective(
    perspective: OracleDebatePerspective,
) -> bool:
    body = asdict(perspective)
    supplied = body.pop("perspective_hash")
    if _stable_hash(body) != supplied:
        raise OracleAdversarialDebateInvariantError(
            "OIT-012 perspective hash mismatch"
        )
    for reference in perspective.evidence_references:
        verify_perspective_evidence_reference(reference)
    if perspective.perspective not in PERSPECTIVES:
        raise OracleAdversarialDebateInvariantError(
            "invalid debate perspective"
        )
    if perspective.evidence_reference_count != len(
        perspective.evidence_references
    ):
        raise OracleAdversarialDebateInvariantError(
            "perspective evidence-reference count mismatch"
        )
    if not perspective.read_only:
        raise OracleAdversarialDebateInvariantError(
            "debate perspective is not read-only"
        )
    return True


def _dominant_perspective(
    perspectives: tuple[OracleDebatePerspective, ...],
    report: OracleContradictionAndUncertaintyReport,
) -> str:
    counts = {
        perspective.perspective: perspective.evidence_reference_count
        for perspective in perspectives
        if perspective.perspective in {"bull", "bear", "neutral"}
    }
    bull = counts.get("bull", 0)
    bear = counts.get("bear", 0)
    neutral = counts.get("neutral", 0)

    if report.contradiction_count or report.uncertainty_level == "high":
        return "contested"
    if bull > bear and bull > neutral:
        return "bull"
    if bear > bull and bear > neutral:
        return "bear"
    if neutral > bull and neutral > bear:
        return "neutral"
    if bull == bear == neutral == 0:
        return "unsupported"
    return "mixed"


def build_adversarial_debate_report(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleAdversarialDebateReport:
    root = repository_root.resolve()
    contradiction_report = build_contradiction_and_uncertainty_report(
        repository_root=root,
        query=query,
        result_limit=result_limit,
    )
    verify_contradiction_and_uncertainty_report(contradiction_report)

    perspectives = tuple(
        _build_perspective(
            perspective=perspective,
            report=contradiction_report,
        )
        for perspective in PERSPECTIVES
    )
    debate_ready = bool(contradiction_report.evidence_count > 0)
    dominant = _dominant_perspective(
        perspectives,
        contradiction_report,
    )

    if contradiction_report.contradiction_count:
        challenge_summary = (
            "The grounded answer is contested by material internal evidence "
            "conflict and must not be presented as a settled conclusion."
        )
    elif contradiction_report.evidence_count <= 1:
        challenge_summary = (
            "The grounded answer lacks independent corroboration and must be "
            "presented as a single-source or no-source result."
        )
    else:
        challenge_summary = (
            "No material bounded contradiction was detected, but source "
            "independence, completeness, and factual truth remain unproven."
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "adversarial_debate_ready"
            if debate_ready
            else "adversarial_debate_limited"
        ),
        "repository_root": root.as_posix(),
        "query": contradiction_report.query,
        "answer_text": contradiction_report.answer_text,
        "answer_hash": contradiction_report.answer_hash,
        "query_plan_hash": contradiction_report.query_plan_hash,
        "query_result_hash": contradiction_report.query_result_hash,
        "explainability_report_hash": (
            contradiction_report.explainability_report_hash
        ),
        "contradiction_report_hash": contradiction_report.report_hash,
        "perspectives": perspectives,
        "perspective_count": len(perspectives),
        "contradiction_count": contradiction_report.contradiction_count,
        "uncertainty_level": contradiction_report.uncertainty_level,
        "corroboration_state": contradiction_report.corroboration_state,
        "debate_ready": debate_ready,
        "dominant_perspective": dominant,
        "challenge_summary": challenge_summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": contradiction_report.failure_reason,
    }
    debate = OracleAdversarialDebateReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_adversarial_debate_report(debate)
    return debate


def verify_adversarial_debate_report(
    report: OracleAdversarialDebateReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleAdversarialDebateInvariantError(
            "OIT-012 report hash mismatch"
        )
    for perspective in report.perspectives:
        verify_debate_perspective(perspective)
    if tuple(p.perspective for p in report.perspectives) != PERSPECTIVES:
        raise OracleAdversarialDebateInvariantError(
            "debate perspective order or completeness mismatch"
        )
    if report.perspective_count != len(report.perspectives):
        raise OracleAdversarialDebateInvariantError(
            "perspective count mismatch"
        )
    if not report.read_only:
        raise OracleAdversarialDebateInvariantError(
            "OIT-012 is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleAdversarialDebateInvariantError(
            "unsafe adversarial-debate boundary"
        )
    return True


def select_debate_perspective(
    report: OracleAdversarialDebateReport,
    *,
    selector: str,
) -> OracleDebatePerspective:
    verify_adversarial_debate_report(report)
    normalized = selector.strip().lower()
    for perspective in report.perspectives:
        if perspective.perspective == normalized:
            return perspective
    raise OracleAdversarialDebateInvariantError(
        f"debate perspective not found: {selector}"
    )


def adversarial_debate_lines(
    report: OracleAdversarialDebateReport,
) -> tuple[str, ...]:
    verify_adversarial_debate_report(report)
    lines = [
        "ORACLE ADVERSARIAL PERSPECTIVE DEBATE",
        f"query: {report.query}",
        f"grounded_answer: {report.answer_text}",
        f"debate_ready: {str(report.debate_ready).lower()}",
        f"dominant_perspective: {report.dominant_perspective}",
        f"uncertainty_level: {report.uncertainty_level}",
        f"corroboration_state: {report.corroboration_state}",
        f"contradiction_count: {report.contradiction_count}",
        f"challenge_summary: {report.challenge_summary}",
        f"failure_reason: {report.failure_reason or 'none'}",
    ]
    for perspective in report.perspectives:
        lines.extend((
            f"[{perspective.perspective.upper()}]",
            f"    position: {perspective.position}",
            f"    supported: {str(perspective.supported).lower()}",
            f"    evidence_reference_count: {perspective.evidence_reference_count}",
            f"    reasoning: {perspective.reasoning_text}",
            "    limitations:",
            *tuple(f"      - {item}" for item in perspective.limitations),
        ))
        for reference in perspective.evidence_references:
            lines.extend((
                f"    [E{reference.evidence_index}] {reference.record_id}",
                f"        {reference.claim_path}={json.dumps(_canonical(reference.claim_value), ensure_ascii=False)}",
                f"        claim_kind: {reference.claim_kind}",
                f"        claim_hash: {reference.claim_hash}",
            ))
    lines.extend((
        f"query_plan_hash: {report.query_plan_hash}",
        f"query_result_hash: {report.query_result_hash}",
        f"answer_hash: {report.answer_hash}",
        f"explainability_report_hash: {report.explainability_report_hash}",
        f"contradiction_report_hash: {report.contradiction_report_hash}",
        f"report_hash: {report.report_hash}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)


def debate_perspective_lines(
    perspective: OracleDebatePerspective,
) -> tuple[str, ...]:
    verify_debate_perspective(perspective)
    lines = [
        f"ORACLE {perspective.perspective.upper()} PERSPECTIVE",
        f"position: {perspective.position}",
        f"supported: {str(perspective.supported).lower()}",
        f"evidence_reference_count: {perspective.evidence_reference_count}",
        f"reasoning: {perspective.reasoning_text}",
        "limitations:",
        *tuple(f"  - {item}" for item in perspective.limitations),
    ]
    if not perspective.evidence_references:
        lines.append("evidence_references: none")
    for reference in perspective.evidence_references:
        lines.extend((
            f"[E{reference.evidence_index}] {reference.record_id}",
            f"    claim_kind: {reference.claim_kind}",
            f"    claim_path: {reference.claim_path}",
            f"    claim_value: {json.dumps(_canonical(reference.claim_value), ensure_ascii=False)}",
            f"    artifact: {reference.artifact_relative_path}",
            f"    artifact_sha256: {reference.artifact_sha256}",
            f"    record_hash: {reference.record_hash}",
            f"    evidence_hash: {reference.evidence_hash}",
            f"    claim_hash: {reference.claim_hash}",
            f"    reference_hash: {reference.reference_hash}",
        ))
    lines.extend((
        f"perspective_hash: {perspective.perspective_hash}",
        "read_only: true",
    ))
    return tuple(lines)
