from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_entropy_information_gain_engine import (
    EntropyInformationGainPackage,
    verify_entropy_information_gain_package,
)

ENGINE_ID = "OII-007"
SCHEMA_VERSION = "OII-007.v1"
ALGORITHM_VERSION = "provenance-confidence.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")


class OracleProvenanceConfidenceInvariantError(ValueError):
    """Raised when an OII-007 provenance-confidence invariant is violated."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if hasattr(value, "__dataclass_fields__"):
        return _canonical(asdict(value))
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_canonical(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ),
        )
    if isinstance(value, Decimal):
        return format(value.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")
    if isinstance(value, float):
        return format(
            Decimal(str(value)).quantize(_QUANT, rounding=ROUND_HALF_EVEN),
            "f",
        )
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _d(value: str | Decimal | int | float) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise OracleProvenanceConfidenceInvariantError(
            f"invalid decimal value: {value!r}"
        ) from exc
    if result.is_nan() or result.is_infinite():
        raise OracleProvenanceConfidenceInvariantError(
            "decimal values must be finite"
        )
    return result


def _q(value: Decimal) -> str:
    bounded = min(_ONE, max(_ZERO, value))
    return format(bounded.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _classification(score: Decimal) -> str:
    if score >= Decimal("0.800000"):
        return "high_provenance_confidence"
    if score >= Decimal("0.550000"):
        return "moderate_provenance_confidence"
    if score >= Decimal("0.300000"):
        return "low_provenance_confidence"
    return "insufficient_provenance_confidence"


@dataclass(frozen=True)
class EvidenceProvenanceConfidenceAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    information_gain_score: str
    entropy_reduction_score: str
    novelty_weight: str
    independence_weight: str
    redundancy_discount: str
    source_traceability_score: str
    lineage_integrity_score: str
    replay_integrity_score: str
    circularity_penalty: str
    provenance_confidence_score: str
    provenance_confidence_classification: str
    confidence_basis: tuple[str, ...]
    assessment_hash: str


@dataclass(frozen=True)
class ProvenanceConfidenceRankingEntry:
    rank: int
    evidence_node_id: str
    evidence_id: str
    provenance_confidence_score: str
    information_gain_score: str
    ranking_hash: str


@dataclass(frozen=True)
class ProvenanceConfidencePackage:
    package_id: str
    source_entropy_information_gain_package_id: str
    source_entropy_information_gain_package_hash: str
    evidence_confidence_assessments: tuple[
        EvidenceProvenanceConfidenceAssessment, ...
    ]
    provenance_confidence_ranking: tuple[
        ProvenanceConfidenceRankingEntry, ...
    ]
    mean_provenance_confidence_score: str
    maximum_provenance_confidence_score: str
    minimum_provenance_confidence_score: str
    high_confidence_evidence_count: int
    moderate_confidence_evidence_count: int
    low_confidence_evidence_count: int
    insufficient_confidence_evidence_count: int
    package_hash: str
    engine_id: str
    schema_version: str
    algorithm_version: str
    read_only: bool
    publication_allowed: bool
    alerting_allowed: bool
    final_intelligence_conclusion_allowed: bool
    probability_estimation_allowed: bool
    qseries_handoff_allowed: bool
    qseries_execution_allowed: bool
    order_creation_allowed: bool
    funds_movement_allowed: bool
    portfolio_mutation_allowed: bool


def analyze_provenance_confidence(
    *,
    entropy_information_gain_package: EntropyInformationGainPackage,
) -> ProvenanceConfidencePackage:
    if not isinstance(
        entropy_information_gain_package,
        EntropyInformationGainPackage,
    ):
        raise OracleProvenanceConfidenceInvariantError(
            "source must be the canonical OII-006 package"
        )

    try:
        verify_entropy_information_gain_package(
            entropy_information_gain_package
        )
    except Exception as exc:
        raise OracleProvenanceConfidenceInvariantError(
            "OII-006 package verification failed"
        ) from exc

    forbidden = (
        entropy_information_gain_package.publication_allowed,
        entropy_information_gain_package.alerting_allowed,
        entropy_information_gain_package.final_intelligence_conclusion_allowed,
        entropy_information_gain_package.probability_estimation_allowed,
        entropy_information_gain_package.qseries_handoff_allowed,
        entropy_information_gain_package.qseries_execution_allowed,
        entropy_information_gain_package.order_creation_allowed,
        entropy_information_gain_package.funds_movement_allowed,
        entropy_information_gain_package.portfolio_mutation_allowed,
    )
    if entropy_information_gain_package.read_only is not True or any(forbidden):
        raise OracleProvenanceConfidenceInvariantError(
            "OII-006 package violates permanent safety boundary"
        )

    entropy_by_node = {
        item.evidence_node_id: item
        for item in entropy_information_gain_package.entropy_assessments
    }
    gain_by_node = {
        item.evidence_node_id: item
        for item in entropy_information_gain_package.information_gain_assessments
    }
    ranking_nodes = {
        item.evidence_node_id
        for item in entropy_information_gain_package.information_gain_ranking
    }

    if (
        set(entropy_by_node) != set(gain_by_node)
        or set(gain_by_node) != ranking_nodes
    ):
        raise OracleProvenanceConfidenceInvariantError(
            "OII-006 evidence node sets do not match"
        )

    assessments: list[EvidenceProvenanceConfidenceAssessment] = []

    for node_id in sorted(gain_by_node):
        entropy = entropy_by_node[node_id]
        gain = gain_by_node[node_id]

        information_gain = _d(gain.effective_information_gain_score)
        entropy_reduction = _d(gain.entropy_reduction_score)
        novelty = _d(gain.novelty_weight)
        independence = _d(gain.independence_weight)
        redundancy_discount = _d(gain.redundancy_discount)

        for name, value in (
            ("information_gain", information_gain),
            ("entropy_reduction", entropy_reduction),
            ("novelty", novelty),
            ("independence", independence),
            ("redundancy_discount", redundancy_discount),
        ):
            if value < _ZERO or value > _ONE:
                raise OracleProvenanceConfidenceInvariantError(
                    f"{name} must be within [0,1]"
                )

        source_traceability = (
            independence * Decimal("0.500000")
            + redundancy_discount * Decimal("0.300000")
            + novelty * Decimal("0.200000")
        )

        lineage_integrity = (
            Decimal("0.550000")
            + information_gain * Decimal("0.250000")
            + entropy_reduction * Decimal("0.200000")
        )
        lineage_integrity = min(_ONE, max(_ZERO, lineage_integrity))

        replay_integrity = Decimal("1.000000")

        circularity_penalty = (
            Decimal("0.150000")
            if "circular_dependency_penalty_applied"
            in gain.information_gain_basis
            else Decimal("0.000000")
        )

        confidence = (
            source_traceability * Decimal("0.350000")
            + lineage_integrity * Decimal("0.300000")
            + replay_integrity * Decimal("0.200000")
            + information_gain * Decimal("0.150000")
            - circularity_penalty
        )
        confidence = min(_ONE, max(_ZERO, confidence))
        classification = _classification(confidence)

        basis: list[str] = []
        basis.append(
            "strong_source_traceability"
            if source_traceability >= Decimal("0.750000")
            else "moderate_source_traceability"
            if source_traceability >= Decimal("0.400000")
            else "weak_source_traceability"
        )
        basis.append(
            "strong_lineage_integrity"
            if lineage_integrity >= Decimal("0.800000")
            else "moderate_lineage_integrity"
        )
        basis.append("replay_integrity_verified")
        basis.append(
            "high_information_gain_support"
            if information_gain >= Decimal("0.750000")
            else "moderate_information_gain_support"
            if information_gain >= Decimal("0.400000")
            else "low_information_gain_support"
        )
        if circularity_penalty:
            basis.append("circularity_penalty_applied")
        else:
            basis.append("no_circularity_penalty")

        body = {
            "evidence_node_id": node_id,
            "evidence_id": gain.evidence_id,
            "source_id": gain.source_id,
            "information_gain_score": _q(information_gain),
            "entropy_reduction_score": _q(entropy_reduction),
            "novelty_weight": _q(novelty),
            "independence_weight": _q(independence),
            "redundancy_discount": _q(redundancy_discount),
            "source_traceability_score": _q(source_traceability),
            "lineage_integrity_score": _q(lineage_integrity),
            "replay_integrity_score": _q(replay_integrity),
            "circularity_penalty": _q(circularity_penalty),
            "provenance_confidence_score": _q(confidence),
            "provenance_confidence_classification": classification,
            "confidence_basis": tuple(basis),
        }
        assessments.append(
            EvidenceProvenanceConfidenceAssessment(
                **body,
                assessment_hash=stable_hash(body),
            )
        )

    assessment_tuple = tuple(
        sorted(assessments, key=lambda item: item.evidence_node_id)
    )
    ranked = sorted(
        assessment_tuple,
        key=lambda item: (
            -_d(item.provenance_confidence_score),
            item.evidence_node_id,
        ),
    )

    ranking: list[ProvenanceConfidenceRankingEntry] = []
    for index, item in enumerate(ranked, start=1):
        body = {
            "rank": index,
            "evidence_node_id": item.evidence_node_id,
            "evidence_id": item.evidence_id,
            "provenance_confidence_score":
                item.provenance_confidence_score,
            "information_gain_score": item.information_gain_score,
        }
        ranking.append(
            ProvenanceConfidenceRankingEntry(
                **body,
                ranking_hash=stable_hash(body),
            )
        )

    scores = [
        _d(item.provenance_confidence_score)
        for item in assessment_tuple
    ]
    mean_score = (
        sum(scores, _ZERO) / Decimal(len(scores))
        if scores
        else _ZERO
    )

    package_body = {
        "source_entropy_information_gain_package_id":
            entropy_information_gain_package.package_id,
        "source_entropy_information_gain_package_hash":
            entropy_information_gain_package.package_hash,
        "evidence_confidence_assessments": assessment_tuple,
        "provenance_confidence_ranking": tuple(ranking),
        "mean_provenance_confidence_score": _q(mean_score),
        "maximum_provenance_confidence_score":
            _q(max(scores) if scores else _ZERO),
        "minimum_provenance_confidence_score":
            _q(min(scores) if scores else _ZERO),
        "high_confidence_evidence_count": sum(
            item.provenance_confidence_classification
            == "high_provenance_confidence"
            for item in assessment_tuple
        ),
        "moderate_confidence_evidence_count": sum(
            item.provenance_confidence_classification
            == "moderate_provenance_confidence"
            for item in assessment_tuple
        ),
        "low_confidence_evidence_count": sum(
            item.provenance_confidence_classification
            == "low_provenance_confidence"
            for item in assessment_tuple
        ),
        "insufficient_confidence_evidence_count": sum(
            item.provenance_confidence_classification
            == "insufficient_provenance_confidence"
            for item in assessment_tuple
        ),
    }
    package_hash = stable_hash(package_body)

    return ProvenanceConfidencePackage(
        package_id="provenance-confidence:" + package_hash,
        **package_body,
        package_hash=package_hash,
        engine_id=ENGINE_ID,
        schema_version=SCHEMA_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        read_only=True,
        publication_allowed=False,
        alerting_allowed=False,
        final_intelligence_conclusion_allowed=False,
        probability_estimation_allowed=False,
        qseries_handoff_allowed=False,
        qseries_execution_allowed=False,
        order_creation_allowed=False,
        funds_movement_allowed=False,
        portfolio_mutation_allowed=False,
    )


def verify_provenance_confidence_package(
    package: ProvenanceConfidencePackage,
) -> bool:
    if not isinstance(package, ProvenanceConfidencePackage):
        raise OracleProvenanceConfidenceInvariantError(
            "invalid OII-007 package type"
        )

    for item in package.evidence_confidence_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleProvenanceConfidenceInvariantError(
                "confidence assessment hash verification failed"
            )

    expected_ranks = tuple(
        range(1, len(package.provenance_confidence_ranking) + 1)
    )
    actual_ranks = tuple(
        item.rank for item in package.provenance_confidence_ranking
    )
    if actual_ranks != expected_ranks:
        raise OracleProvenanceConfidenceInvariantError(
            "confidence ranking is not contiguous"
        )

    for item in package.provenance_confidence_ranking:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "ranking_hash"
        }
        if stable_hash(body) != item.ranking_hash:
            raise OracleProvenanceConfidenceInvariantError(
                "confidence ranking hash verification failed"
            )

    package_body = {
        "source_entropy_information_gain_package_id":
            package.source_entropy_information_gain_package_id,
        "source_entropy_information_gain_package_hash":
            package.source_entropy_information_gain_package_hash,
        "evidence_confidence_assessments":
            package.evidence_confidence_assessments,
        "provenance_confidence_ranking":
            package.provenance_confidence_ranking,
        "mean_provenance_confidence_score":
            package.mean_provenance_confidence_score,
        "maximum_provenance_confidence_score":
            package.maximum_provenance_confidence_score,
        "minimum_provenance_confidence_score":
            package.minimum_provenance_confidence_score,
        "high_confidence_evidence_count":
            package.high_confidence_evidence_count,
        "moderate_confidence_evidence_count":
            package.moderate_confidence_evidence_count,
        "low_confidence_evidence_count":
            package.low_confidence_evidence_count,
        "insufficient_confidence_evidence_count":
            package.insufficient_confidence_evidence_count,
    }
    if stable_hash(package_body) != package.package_hash:
        raise OracleProvenanceConfidenceInvariantError(
            "package hash verification failed"
        )
    if package.package_id != "provenance-confidence:" + package.package_hash:
        raise OracleProvenanceConfidenceInvariantError(
            "package identity verification failed"
        )

    forbidden = (
        package.publication_allowed,
        package.alerting_allowed,
        package.final_intelligence_conclusion_allowed,
        package.probability_estimation_allowed,
        package.qseries_handoff_allowed,
        package.qseries_execution_allowed,
        package.order_creation_allowed,
        package.funds_movement_allowed,
        package.portfolio_mutation_allowed,
    )
    if package.read_only is not True or any(forbidden):
        raise OracleProvenanceConfidenceInvariantError(
            "OII-007 safety boundary violated"
        )
    return True


def serialize_provenance_confidence_package(
    package: ProvenanceConfidencePackage,
) -> str:
    verify_provenance_confidence_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "EvidenceProvenanceConfidenceAssessment",
    "ProvenanceConfidenceRankingEntry",
    "ProvenanceConfidencePackage",
    "OracleProvenanceConfidenceInvariantError",
    "analyze_provenance_confidence",
    "verify_provenance_confidence_package",
    "serialize_provenance_confidence_package",
]
