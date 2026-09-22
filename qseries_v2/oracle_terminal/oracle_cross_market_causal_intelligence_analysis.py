from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .oracle_cross_market_intelligence_relationship_analysis import (
    OracleCrossMarketIntelligenceReport,
    OracleCrossMarketRelationship,
    OracleCrossMarketRelationshipInvariantError,
    build_cross_market_intelligence_report,
    verify_cross_market_intelligence_report,
)

SCHEMA_VERSION = "OIT-015"
ENGINE_ID = "OIT-015"
POLICY_ID = "oracle.cross-market-causal-intelligence-analysis.v1"
MAX_CAUSAL_CONFIDENCE = 0.85


class OracleCausalIntelligenceInvariantError(
    OracleCrossMarketRelationshipInvariantError
):
    pass


@dataclass(frozen=True)
class OracleCausalHypothesis:
    hypothesis_index: int
    cause_record_id: str
    effect_record_id: str
    shared_entities: tuple[str, ...]
    temporal_order: str
    causal_direction: str
    causal_type: str
    evidence_class: str
    probability_distance: float | None
    relationship_score: float
    causal_confidence: float
    supports_causation: bool
    contradicts_causation: bool
    limitations: tuple[str, ...]
    rationale: tuple[str, ...]
    source_relationship_hash: str
    read_only: bool
    hypothesis_hash: str


@dataclass(frozen=True)
class OracleCausalIntelligenceReport:
    schema_version: str
    engine_id: str
    policy_id: str
    status: str
    repository_root: str
    query: str
    cross_market_report_hash: str
    hypotheses: tuple[OracleCausalHypothesis, ...]
    hypothesis_count: int
    supportive_hypothesis_count: int
    suppressive_hypothesis_count: int
    associative_hypothesis_count: int
    insufficient_hypothesis_count: int
    causal_state: str
    causal_summary: str
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


def _bounded(value: float) -> float:
    return round(max(0.0, min(MAX_CAUSAL_CONFIDENCE, value)), 6)


def _temporal_order(
    relationship: OracleCrossMarketRelationship,
) -> tuple[str, str, str]:
    temporal = relationship.temporal_relationship.strip().lower()
    if temporal == "left_leads_right":
        return (
            relationship.left_record_id,
            relationship.right_record_id,
            "left_precedes_right",
        )
    if temporal == "right_leads_left":
        return (
            relationship.right_record_id,
            relationship.left_record_id,
            "right_precedes_left",
        )
    return (
        relationship.left_record_id,
        relationship.right_record_id,
        temporal or "undetermined",
    )


def _classify(
    relationship: OracleCrossMarketRelationship,
) -> tuple[str, str, bool, bool, float, tuple[str, ...], tuple[str, ...]]:
    shared = relationship.shared_entity_count > 0
    temporal = relationship.temporal_relationship.strip().lower()
    directional = relationship.directional_relationship.strip().lower()
    has_order = temporal in {"left_leads_right", "right_leads_left"}
    strong_enough = relationship.relationship_score >= 0.50

    limitations = [
        "observational evidence cannot establish causation by itself",
        "unobserved confounders may explain the relationship",
    ]
    rationale = [
        f"shared semantic entities: {relationship.shared_entity_count}",
        f"temporal relationship: {relationship.temporal_relationship}",
        f"directional relationship: {relationship.directional_relationship}",
        f"relationship score: {relationship.relationship_score:.6f}",
    ]

    base = relationship.relationship_score * 0.55
    if shared:
        base += 0.10
    if has_order:
        base += 0.10
    if relationship.probability_distance is not None:
        base += max(0.0, 0.10 * (1.0 - relationship.probability_distance))

    if shared and has_order and directional == "aligned" and strong_enough:
        rationale.append("ordered and aligned evidence supports a causal hypothesis")
        limitations.append("mechanism has not yet been independently verified")
        return (
            "supportive",
            "candidate_influence",
            True,
            False,
            _bounded(base),
            tuple(limitations),
            tuple(rationale),
        )

    if shared and has_order and directional == "contradictory":
        rationale.append(
            "ordered contradictory movement supports a suppressive hypothesis"
        )
        limitations.append(
            "inverse movement may reflect hedging, substitution, or a confounder"
        )
        return (
            "suppressive",
            "candidate_inhibitory_influence",
            True,
            True,
            _bounded(base - 0.05),
            tuple(limitations),
            tuple(rationale),
        )

    if shared and not has_order:
        rationale.append("semantic relationship exists without stable lead-lag order")
        limitations.append("temporal precedence is not established")
        return (
            "associative",
            "non_directional_association",
            False,
            False,
            _bounded(base - 0.15),
            tuple(limitations),
            tuple(rationale),
        )

    rationale.append("available relationship evidence is insufficient for causation")
    limitations.append("minimum semantic and temporal conditions are unmet")
    return (
        "insufficient",
        "no_causal_classification",
        False,
        False,
        _bounded(base - 0.25),
        tuple(limitations),
        tuple(rationale),
    )


def _build_hypothesis(
    relationship: OracleCrossMarketRelationship,
    index: int,
) -> OracleCausalHypothesis:
    cause, effect, temporal_order = _temporal_order(relationship)
    (
        evidence_class,
        causal_type,
        supports,
        contradicts,
        confidence,
        limitations,
        rationale,
    ) = _classify(relationship)

    body = {
        "hypothesis_index": index,
        "cause_record_id": cause,
        "effect_record_id": effect,
        "shared_entities": tuple(relationship.shared_entities),
        "temporal_order": temporal_order,
        "causal_direction": f"{cause}->{effect}",
        "causal_type": causal_type,
        "evidence_class": evidence_class,
        "probability_distance": relationship.probability_distance,
        "relationship_score": relationship.relationship_score,
        "causal_confidence": confidence,
        "supports_causation": supports,
        "contradicts_causation": contradicts,
        "limitations": limitations,
        "rationale": rationale,
        "source_relationship_hash": relationship.relationship_hash,
        "read_only": True,
    }
    return OracleCausalHypothesis(
        **body,
        hypothesis_hash=_stable_hash(body),
    )


def verify_causal_hypothesis(hypothesis: OracleCausalHypothesis) -> bool:
    body = asdict(hypothesis)
    supplied = body.pop("hypothesis_hash")
    if _stable_hash(body) != supplied:
        raise OracleCausalIntelligenceInvariantError(
            "causal hypothesis hash mismatch"
        )
    if not hypothesis.read_only:
        raise OracleCausalIntelligenceInvariantError(
            "causal hypothesis is not read-only"
        )
    if not (0.0 <= hypothesis.causal_confidence <= MAX_CAUSAL_CONFIDENCE):
        raise OracleCausalIntelligenceInvariantError(
            "causal confidence exceeds bounded policy"
        )
    if not hypothesis.source_relationship_hash:
        raise OracleCausalIntelligenceInvariantError(
            "source relationship lineage missing"
        )
    if hypothesis.cause_record_id == hypothesis.effect_record_id:
        raise OracleCausalIntelligenceInvariantError(
            "self-causation hypothesis forbidden"
        )
    return True


def _summary(hypotheses: tuple[OracleCausalHypothesis, ...]) -> tuple[str, str]:
    if not hypotheses:
        return (
            "no_causal_evidence",
            "No certified cross-market relationships were available for causal inspection.",
        )
    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)
    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)
    associative = sum(item.evidence_class == "associative" for item in hypotheses)
    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)
    if supportive or suppressive:
        state = "bounded_causal_hypotheses_present"
    elif associative:
        state = "associations_without_causal_order"
    else:
        state = "insufficient_causal_evidence"
    return (
        state,
        (
            f"{len(hypotheses)} bounded causal inspections: "
            f"{supportive} supportive, {suppressive} suppressive, "
            f"{associative} associative, {insufficient} insufficient. "
            "No hypothesis is treated as proof of causation."
        ),
    )


def build_causal_intelligence_report(
    repository_root: str | Path,
    query: str,
    *,
    cross_market_report: OracleCrossMarketIntelligenceReport | None = None,
) -> OracleCausalIntelligenceReport:
    root = Path(repository_root).resolve()
    source = cross_market_report
    if source is None:
        source = build_cross_market_intelligence_report(
            repository_root=root,
            query=query,
        )
    verify_cross_market_intelligence_report(source)

    hypotheses = tuple(
        _build_hypothesis(relationship, index)
        for index, relationship in enumerate(source.relationships, start=1)
    )
    for hypothesis in hypotheses:
        verify_causal_hypothesis(hypothesis)

    causal_state, causal_summary = _summary(hypotheses)
    supportive = sum(item.evidence_class == "supportive" for item in hypotheses)
    suppressive = sum(item.evidence_class == "suppressive" for item in hypotheses)
    associative = sum(item.evidence_class == "associative" for item in hypotheses)
    insufficient = sum(item.evidence_class == "insufficient" for item in hypotheses)

    body = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "policy_id": POLICY_ID,
        "status": "certified_read_only",
        "repository_root": str(root),
        "query": str(query),
        "cross_market_report_hash": source.report_hash,
        "hypotheses": hypotheses,
        "hypothesis_count": len(hypotheses),
        "supportive_hypothesis_count": supportive,
        "suppressive_hypothesis_count": suppressive,
        "associative_hypothesis_count": associative,
        "insufficient_hypothesis_count": insufficient,
        "causal_state": causal_state,
        "causal_summary": causal_summary,
        "read_only": True,
        "analytics_execution_performed": False,
        "database_access_performed": False,
        "publication_allowed": False,
        "qseries_execution_allowed": False,
        "failure_reason": None,
    }
    report = OracleCausalIntelligenceReport(
        **body,
        report_hash=_stable_hash(body),
    )
    verify_causal_intelligence_report(report)
    return report


def verify_causal_intelligence_report(
    report: OracleCausalIntelligenceReport,
) -> bool:
    body = asdict(report)
    supplied = body.pop("report_hash")
    if _stable_hash(body) != supplied:
        raise OracleCausalIntelligenceInvariantError(
            "causal intelligence report hash mismatch"
        )
    if report.schema_version != SCHEMA_VERSION:
        raise OracleCausalIntelligenceInvariantError("schema mismatch")
    if report.policy_id != POLICY_ID:
        raise OracleCausalIntelligenceInvariantError("policy mismatch")
    if not report.read_only:
        raise OracleCausalIntelligenceInvariantError("report is not read-only")
    if (
        report.analytics_execution_performed
        or report.database_access_performed
        or report.publication_allowed
        or report.qseries_execution_allowed
    ):
        raise OracleCausalIntelligenceInvariantError(
            "forbidden runtime capability enabled"
        )
    if report.hypothesis_count != len(report.hypotheses):
        raise OracleCausalIntelligenceInvariantError(
            "hypothesis count mismatch"
        )
    counts = {
        "supportive": report.supportive_hypothesis_count,
        "suppressive": report.suppressive_hypothesis_count,
        "associative": report.associative_hypothesis_count,
        "insufficient": report.insufficient_hypothesis_count,
    }
    for evidence_class, expected in counts.items():
        actual = sum(
            item.evidence_class == evidence_class
            for item in report.hypotheses
        )
        if actual != expected:
            raise OracleCausalIntelligenceInvariantError(
                f"{evidence_class} count mismatch"
            )
    if sum(counts.values()) != report.hypothesis_count:
        raise OracleCausalIntelligenceInvariantError(
            "classified hypothesis count mismatch"
        )
    for hypothesis in report.hypotheses:
        verify_causal_hypothesis(hypothesis)
    return True
