from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_evidence_inspection_and_answer_explainability import (
    OracleAnswerExplainabilityReport,
    OracleEvidenceExplainabilityInvariantError,
    OracleEvidenceInspection,
    build_answer_explainability_report,
    verify_answer_explainability_report,
    verify_evidence_inspection,
)

SCHEMA_VERSION = "OIT-011"
ENGINE_ID = "OIT-011"
POLICY_ID = "oracle.contradiction-and-uncertainty-inspection.v1"

STANCE_FIELDS = ("stance", "direction", "signal", "position", "bias")
PROBABILITY_FIELDS = ("probability", "confidence", "score", "likelihood")
STATUS_FIELDS = ("status", "outcome", "result", "state")
CONTRADICTION_TOLERANCE = 0.20


class OracleContradictionInspectionInvariantError(
    OracleEvidenceExplainabilityInvariantError
):
    pass


@dataclass(frozen=True)
class OracleEvidenceClaim:
    evidence_index: int
    record_id: str
    claim_path: str
    claim_kind: str
    claim_value: Any
    normalized_value: str
    artifact_relative_path: str
    artifact_sha256: str
    record_hash: str
    evidence_hash: str
    read_only: bool
    claim_hash: str


@dataclass(frozen=True)
class OracleContradictionPair:
    pair_index: int
    left_evidence_index: int
    right_evidence_index: int
    left_record_id: str
    right_record_id: str
    claim_kind: str
    left_value: Any
    right_value: Any
    contradiction_type: str
    contradiction_reason: str
    severity: str
    read_only: bool
    pair_hash: str


@dataclass(frozen=True)
class OracleContradictionAndUncertaintyReport:
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
    claims: tuple[OracleEvidenceClaim, ...]
    contradictions: tuple[OracleContradictionPair, ...]
    claim_count: int
    contradiction_count: int
    agreement_count: int
    evidence_count: int
    corroboration_state: str
    contradiction_state: str
    uncertainty_level: str
    uncertainty_reasons: tuple[str, ...]
    conclusion_text: str
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


def _normalize_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.12g}"
    if isinstance(value, int):
        return str(value)
    if value is None:
        return "null"
    return str(value).strip().lower()


def _claim_kind(path: str) -> str | None:
    leaf = path.rsplit(".", 1)[-1].lower()
    if leaf in STANCE_FIELDS:
        return "stance"
    if leaf in PROBABILITY_FIELDS:
        return "probability"
    if leaf in STATUS_FIELDS:
        return "status"
    return None


def _selected_claims(
    inspection: OracleEvidenceInspection,
) -> tuple[OracleEvidenceClaim, ...]:
    verify_evidence_inspection(inspection)
    claims = []
    for path, value in inspection.selected_fields:
        kind = _claim_kind(path)
        if kind is None:
            continue
        body = {
            "evidence_index": inspection.evidence_index,
            "record_id": inspection.record_id,
            "claim_path": path,
            "claim_kind": kind,
            "claim_value": _canonical(value),
            "normalized_value": _normalize_value(value),
            "artifact_relative_path": inspection.artifact_relative_path,
            "artifact_sha256": inspection.artifact_sha256,
            "record_hash": inspection.record_hash,
            "evidence_hash": inspection.evidence_hash,
            "read_only": True,
        }
        claim = OracleEvidenceClaim(
            **body,
            claim_hash=_stable_hash(body),
        )
        verify_evidence_claim(claim)
        claims.append(claim)
    return tuple(claims)


def verify_evidence_claim(claim: OracleEvidenceClaim) -> bool:
    body = asdict(claim)
    supplied = body.pop("claim_hash")
    if _stable_hash(body) != supplied:
        raise OracleContradictionInspectionInvariantError(
            "OIT-011 claim hash mismatch"
        )
    if not claim.read_only:
        raise OracleContradictionInspectionInvariantError(
            "evidence claim is not read-only"
        )
    if claim.evidence_index < 1:
        raise OracleContradictionInspectionInvariantError(
            "invalid evidence claim index"
        )
    if (
        len(claim.artifact_sha256) != 64
        or not claim.record_hash
        or not claim.evidence_hash
    ):
        raise OracleContradictionInspectionInvariantError(
            "evidence claim lineage is incomplete"
        )
    return True


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _stance_opposed(left: str, right: str) -> bool:
    opposed = {
        ("bull", "bear"),
        ("bear", "bull"),
        ("yes", "no"),
        ("no", "yes"),
        ("long", "short"),
        ("short", "long"),
        ("positive", "negative"),
        ("negative", "positive"),
    }
    return (left, right) in opposed


def _compare_claims(
    left: OracleEvidenceClaim,
    right: OracleEvidenceClaim,
    *,
    pair_index: int,
) -> OracleContradictionPair | None:
    verify_evidence_claim(left)
    verify_evidence_claim(right)
    if left.claim_kind != right.claim_kind:
        return None
    if left.record_id == right.record_id:
        return None

    contradiction_type = None
    reason = None
    severity = None

    if left.claim_kind == "stance":
        if _stance_opposed(left.normalized_value, right.normalized_value):
            contradiction_type = "opposed_stance"
            reason = (
                f"{left.record_id} reports {left.normalized_value} while "
                f"{right.record_id} reports {right.normalized_value}"
            )
            severity = "high"
    elif left.claim_kind == "probability":
        left_number = _numeric(left.claim_value)
        right_number = _numeric(right.claim_value)
        if left_number is not None and right_number is not None:
            delta = abs(left_number - right_number)
            if delta >= CONTRADICTION_TOLERANCE:
                contradiction_type = "probability_divergence"
                reason = (
                    f"probability values differ by {delta:.6g}, meeting the "
                    f"{CONTRADICTION_TOLERANCE:.2f} contradiction threshold"
                )
                severity = "high" if delta >= 0.40 else "medium"
    elif left.claim_kind == "status":
        if left.normalized_value != right.normalized_value:
            contradiction_type = "status_disagreement"
            reason = (
                f"{left.record_id} reports {left.normalized_value} while "
                f"{right.record_id} reports {right.normalized_value}"
            )
            severity = "medium"

    if contradiction_type is None:
        return None

    body = {
        "pair_index": pair_index,
        "left_evidence_index": left.evidence_index,
        "right_evidence_index": right.evidence_index,
        "left_record_id": left.record_id,
        "right_record_id": right.record_id,
        "claim_kind": left.claim_kind,
        "left_value": _canonical(left.claim_value),
        "right_value": _canonical(right.claim_value),
        "contradiction_type": contradiction_type,
        "contradiction_reason": reason,
        "severity": severity,
        "read_only": True,
    }
    pair = OracleContradictionPair(
        **body,
        pair_hash=_stable_hash(body),
    )
    verify_contradiction_pair(pair)
    return pair


def verify_contradiction_pair(
    pair: OracleContradictionPair,
) -> bool:
    body = asdict(pair)
    supplied = body.pop("pair_hash")
    if _stable_hash(body) != supplied:
        raise OracleContradictionInspectionInvariantError(
            "OIT-011 contradiction-pair hash mismatch"
        )
    if not pair.read_only:
        raise OracleContradictionInspectionInvariantError(
            "contradiction pair is not read-only"
        )
    if pair.left_evidence_index == pair.right_evidence_index:
        raise OracleContradictionInspectionInvariantError(
            "contradiction pair references one evidence item twice"
        )
    if pair.severity not in {"low", "medium", "high"}:
        raise OracleContradictionInspectionInvariantError(
            "invalid contradiction severity"
        )
    return True


def _contradictions(
    claims: tuple[OracleEvidenceClaim, ...],
) -> tuple[OracleContradictionPair, ...]:
    pairs = []
    pair_index = 1
    for left_index, left in enumerate(claims):
        for right in claims[left_index + 1:]:
            pair = _compare_claims(
                left,
                right,
                pair_index=pair_index,
            )
            if pair is not None:
                pairs.append(pair)
                pair_index += 1
    return tuple(pairs)


def _agreement_count(
    claims: tuple[OracleEvidenceClaim, ...],
) -> int:
    count = 0
    for left_index, left in enumerate(claims):
        for right in claims[left_index + 1:]:
            if left.record_id == right.record_id:
                continue
            if (
                left.claim_kind == right.claim_kind
                and left.normalized_value == right.normalized_value
            ):
                count += 1
    return count


def _uncertainty(
    report: OracleAnswerExplainabilityReport,
    contradictions: tuple[OracleContradictionPair, ...],
    claims: tuple[OracleEvidenceClaim, ...],
) -> tuple[str, tuple[str, ...]]:
    reasons = []

    if not report.answer_grounded:
        reasons.append("no grounded answer is available")
    if report.evidence_count == 0:
        reasons.append("no matching evidence record was found")
    elif report.evidence_count == 1:
        reasons.append("only one admitted evidence record supports the answer")

    if contradictions:
        reasons.append(
            f"{len(contradictions)} material contradiction pair(s) were detected"
        )

    claim_kinds = {claim.claim_kind for claim in claims}
    if report.evidence_count > 0 and not claims:
        reasons.append(
            "matched records expose no bounded stance, probability, or status claims"
        )
    elif "probability" not in claim_kinds:
        reasons.append("no comparable probability claim is available")

    if any(pair.severity == "high" for pair in contradictions):
        level = "high"
    elif contradictions or report.evidence_count <= 1:
        level = "medium"
    elif reasons:
        level = "medium"
    else:
        level = "low"

    return level, tuple(reasons)


def build_contradiction_and_uncertainty_report(
    *,
    repository_root: Path,
    query: str,
    result_limit: int = 10,
) -> OracleContradictionAndUncertaintyReport:
    root = repository_root.resolve()
    explainability = build_answer_explainability_report(
        repository_root=root,
        query=query,
        result_limit=result_limit,
    )
    verify_answer_explainability_report(explainability)

    claims = tuple(
        claim
        for inspection in explainability.inspections
        for claim in _selected_claims(inspection)
    )
    contradictions = _contradictions(claims)
    agreements = _agreement_count(claims)
    uncertainty_level, uncertainty_reasons = _uncertainty(
        explainability,
        contradictions,
        claims,
    )

    if explainability.evidence_count == 0:
        corroboration_state = "no_evidence"
    elif explainability.evidence_count == 1:
        corroboration_state = "single_source"
    elif agreements > 0:
        corroboration_state = "partially_corroborated"
    else:
        corroboration_state = "multiple_sources_unconfirmed"

    contradiction_state = (
        "material_contradictions_detected"
        if contradictions
        else "no_material_contradiction_detected"
    )

    if contradictions:
        conclusion = (
            f"Oracle detected {len(contradictions)} material contradiction "
            "pair(s). The answer should be treated as contested until the "
            "underlying evidence is reconciled."
        )
    elif explainability.evidence_count == 1:
        conclusion = (
            "Oracle detected no contradiction, but only one admitted evidence "
            "record supports the answer; absence of contradiction is not "
            "independent corroboration."
        )
    elif explainability.evidence_count == 0:
        conclusion = (
            "Oracle has no admitted matching evidence and cannot assess "
            "agreement or contradiction."
        )
    else:
        conclusion = (
            "Oracle detected no material contradiction among the bounded "
            "comparable claims. This does not establish source independence "
            "or factual truth."
        )

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": (
            "contradiction_and_uncertainty_inspection_completed"
            if explainability.answer_grounded
            else "contradiction_and_uncertainty_inspection_limited"
        ),
        "repository_root": root.as_posix(),
        "query": explainability.query,
        "answer_text": explainability.answer_text,
        "answer_hash": explainability.answer_hash,
        "query_plan_hash": explainability.query_plan_hash,
        "query_result_hash": explainability.query_result_hash,
        "explainability_report_hash": explainability.report_hash,
        "claims": claims,
        "contradictions": contradictions,
        "claim_count": len(claims),
        "contradiction_count": len(contradictions),
        "agreement_count": agreements,
        "evidence_count": explainability.evidence_count,
        "corroboration_state": corroboration_state,
        "contradiction_state": contradiction_state,
        "uncertainty_level": uncertainty_level,
        "uncertainty_reasons": uncertainty_reasons,
        "conclusion_text": conclusion,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": explainability.failure_reason,
    }
    report = OracleContradictionAndUncertaintyReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_contradiction_and_uncertainty_report(report)
    return report


def verify_contradiction_and_uncertainty_report(
    report: OracleContradictionAndUncertaintyReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleContradictionInspectionInvariantError(
            "OIT-011 report hash mismatch"
        )
    for claim in report.claims:
        verify_evidence_claim(claim)
    for pair in report.contradictions:
        verify_contradiction_pair(pair)
    if not report.read_only:
        raise OracleContradictionInspectionInvariantError(
            "OIT-011 is not read-only"
        )
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleContradictionInspectionInvariantError(
            "unsafe contradiction-inspection boundary"
        )
    if report.claim_count != len(report.claims):
        raise OracleContradictionInspectionInvariantError(
            "claim count mismatch"
        )
    if report.contradiction_count != len(report.contradictions):
        raise OracleContradictionInspectionInvariantError(
            "contradiction count mismatch"
        )
    if report.uncertainty_level not in {"low", "medium", "high"}:
        raise OracleContradictionInspectionInvariantError(
            "invalid uncertainty level"
        )
    return True


def contradiction_and_uncertainty_lines(
    report: OracleContradictionAndUncertaintyReport,
) -> tuple[str, ...]:
    verify_contradiction_and_uncertainty_report(report)
    lines = [
        "ORACLE CONTRADICTION AND UNCERTAINTY REPORT",
        f"query: {report.query}",
        f"answer: {report.answer_text}",
        f"evidence_count: {report.evidence_count}",
        f"claim_count: {report.claim_count}",
        f"agreement_count: {report.agreement_count}",
        f"contradiction_count: {report.contradiction_count}",
        f"corroboration_state: {report.corroboration_state}",
        f"contradiction_state: {report.contradiction_state}",
        f"uncertainty_level: {report.uncertainty_level}",
        f"failure_reason: {report.failure_reason or 'none'}",
        f"conclusion: {report.conclusion_text}",
    ]
    if report.uncertainty_reasons:
        lines.append("uncertainty_reasons:")
        lines.extend(
            f"  - {reason}" for reason in report.uncertainty_reasons
        )
    else:
        lines.append("uncertainty_reasons: none")

    if report.contradictions:
        lines.append("contradictions:")
        for pair in report.contradictions:
            lines.extend((
                f"  [C{pair.pair_index}] {pair.contradiction_type}",
                f"      records: {pair.left_record_id} vs {pair.right_record_id}",
                f"      claim_kind: {pair.claim_kind}",
                f"      left_value: {json.dumps(_canonical(pair.left_value), ensure_ascii=False)}",
                f"      right_value: {json.dumps(_canonical(pair.right_value), ensure_ascii=False)}",
                f"      severity: {pair.severity}",
                f"      reason: {pair.contradiction_reason}",
            ))
    else:
        lines.append("contradictions: none")

    lines.extend((
        f"query_plan_hash: {report.query_plan_hash}",
        f"query_result_hash: {report.query_result_hash}",
        f"answer_hash: {report.answer_hash}",
        f"explainability_report_hash: {report.explainability_report_hash}",
        f"report_hash: {report.report_hash}",
        "analytics_execution_performed: false",
        "database_access_performed: false",
        "publication_allowed: false",
        "qseries_execution_allowed: false",
        "read_only: true",
    ))
    return tuple(lines)
