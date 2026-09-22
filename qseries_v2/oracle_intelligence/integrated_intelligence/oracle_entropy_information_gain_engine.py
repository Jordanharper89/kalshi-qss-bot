from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_redundancy_novelty_engine import (
    RedundancyNoveltyPackage,
    verify_redundancy_novelty_package,
)

ENGINE_ID = "OII-006"
SCHEMA_VERSION = "OII-006.v1"
ALGORITHM_VERSION = "entropy-information-gain.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_HALF = Decimal("0.5")


class OracleEntropyInformationGainInvariantError(ValueError):
    """Raised when an OII-006 entropy/information-gain invariant is violated."""


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


def _q(value: Decimal) -> str:
    bounded = min(_ONE, max(_ZERO, value))
    return format(bounded.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _d(value: str | Decimal | int | float) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise OracleEntropyInformationGainInvariantError(
            f"invalid decimal value: {value!r}"
        ) from exc
    if result.is_nan() or result.is_infinite():
        raise OracleEntropyInformationGainInvariantError(
            "decimal values must be finite"
        )
    return result


def _binary_entropy(probability: Decimal) -> Decimal:
    """
    Deterministic normalized binary-entropy approximation.

    The implementation deliberately avoids platform-dependent transcendental
    functions. It uses the Gini impurity equivalent 4p(1-p), normalized to
    [0,1], which preserves the core entropy ordering:
      - 0 at certainty
      - 1 at maximal uncertainty
      - symmetric around p=0.5
    """
    p = min(_ONE, max(_ZERO, probability))
    return Decimal("4") * p * (_ONE - p)


def _classification(value: Decimal, labels: tuple[str, str, str]) -> str:
    if value >= Decimal("0.750000"):
        return labels[0]
    if value >= Decimal("0.400000"):
        return labels[1]
    return labels[2]


@dataclass(frozen=True)
class EvidenceEntropyAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    novelty_score: str
    redundancy_score: str
    source_independence_score: str
    prior_uncertainty_score: str
    posterior_uncertainty_score: str
    entropy_reduction_score: str
    effective_information_content_score: str
    uncertainty_classification: str
    assessment_hash: str


@dataclass(frozen=True)
class EvidenceInformationGainAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    entropy_reduction_score: str
    novelty_weight: str
    independence_weight: str
    redundancy_discount: str
    effective_information_gain_score: str
    information_gain_classification: str
    information_gain_basis: tuple[str, ...]
    assessment_hash: str


@dataclass(frozen=True)
class InformationGainRankingEntry:
    rank: int
    evidence_node_id: str
    evidence_id: str
    effective_information_gain_score: str
    novelty_score: str
    redundancy_score: str
    ranking_hash: str


@dataclass(frozen=True)
class EntropyInformationGainPackage:
    package_id: str
    source_redundancy_novelty_package_id: str
    source_redundancy_novelty_package_hash: str
    entropy_assessments: tuple[EvidenceEntropyAssessment, ...]
    information_gain_assessments: tuple[EvidenceInformationGainAssessment, ...]
    information_gain_ranking: tuple[InformationGainRankingEntry, ...]
    aggregate_prior_uncertainty_score: str
    aggregate_posterior_uncertainty_score: str
    aggregate_entropy_reduction_score: str
    mean_effective_information_gain_score: str
    maximum_effective_information_gain_score: str
    minimum_effective_information_gain_score: str
    high_information_gain_evidence_count: int
    medium_information_gain_evidence_count: int
    low_information_gain_evidence_count: int
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


def analyze_entropy_and_information_gain(
    *,
    redundancy_novelty_package: RedundancyNoveltyPackage,
) -> EntropyInformationGainPackage:
    if not isinstance(redundancy_novelty_package, RedundancyNoveltyPackage):
        raise OracleEntropyInformationGainInvariantError(
            "source must be the canonical OII-005 package"
        )

    try:
        verify_redundancy_novelty_package(redundancy_novelty_package)
    except Exception as exc:
        raise OracleEntropyInformationGainInvariantError(
            "OII-005 package verification failed"
        ) from exc

    forbidden = (
        redundancy_novelty_package.publication_allowed,
        redundancy_novelty_package.alerting_allowed,
        redundancy_novelty_package.final_intelligence_conclusion_allowed,
        redundancy_novelty_package.probability_estimation_allowed,
        redundancy_novelty_package.qseries_handoff_allowed,
        redundancy_novelty_package.qseries_execution_allowed,
        redundancy_novelty_package.order_creation_allowed,
        redundancy_novelty_package.funds_movement_allowed,
        redundancy_novelty_package.portfolio_mutation_allowed,
    )
    if redundancy_novelty_package.read_only is not True or any(forbidden):
        raise OracleEntropyInformationGainInvariantError(
            "OII-005 package violates permanent safety boundary"
        )

    redundancy_by_node = {
        item.evidence_node_id: item
        for item in redundancy_novelty_package.evidence_redundancy_assessments
    }
    novelty_by_node = {
        item.evidence_node_id: item
        for item in redundancy_novelty_package.evidence_novelty_assessments
    }

    if set(redundancy_by_node) != set(novelty_by_node):
        raise OracleEntropyInformationGainInvariantError(
            "OII-005 redundancy/novelty node sets do not match"
        )

    entropy_assessments: list[EvidenceEntropyAssessment] = []
    gain_assessments: list[EvidenceInformationGainAssessment] = []

    for node_id in sorted(novelty_by_node):
        novelty = novelty_by_node[node_id]
        redundancy = redundancy_by_node[node_id]

        novelty_score = _d(novelty.novelty_score)
        redundancy_score = _d(redundancy.redundancy_score)
        independence_score = _d(novelty.source_independence_score)

        for name, value in (
            ("novelty_score", novelty_score),
            ("redundancy_score", redundancy_score),
            ("source_independence_score", independence_score),
        ):
            if value < _ZERO or value > _ONE:
                raise OracleEntropyInformationGainInvariantError(
                    f"{name} must be within [0,1]"
                )

        prior_probability = _HALF
        prior_uncertainty = _binary_entropy(prior_probability)

        directional_strength = (
            novelty_score * Decimal("0.500000")
            + independence_score * Decimal("0.350000")
            + (_ONE - redundancy_score) * Decimal("0.150000")
        )
        directional_strength = min(_ONE, max(_ZERO, directional_strength))

        posterior_probability = _HALF + (
            directional_strength * Decimal("0.490000")
        )
        posterior_probability = min(
            Decimal("0.990000"),
            max(Decimal("0.010000"), posterior_probability),
        )
        posterior_uncertainty = _binary_entropy(posterior_probability)
        entropy_reduction = max(
            _ZERO,
            prior_uncertainty - posterior_uncertainty,
        )

        effective_information_content = (
            entropy_reduction * Decimal("0.500000")
            + novelty_score * Decimal("0.300000")
            + independence_score * Decimal("0.200000")
        ) * (_ONE - redundancy_score * Decimal("0.500000"))
        effective_information_content = min(
            _ONE,
            max(_ZERO, effective_information_content),
        )

        uncertainty_classification = _classification(
            posterior_uncertainty,
            (
                "high_remaining_uncertainty",
                "moderate_remaining_uncertainty",
                "low_remaining_uncertainty",
            ),
        )

        entropy_body = {
            "evidence_node_id": node_id,
            "evidence_id": novelty.evidence_id,
            "source_id": novelty.source_id,
            "novelty_score": _q(novelty_score),
            "redundancy_score": _q(redundancy_score),
            "source_independence_score": _q(independence_score),
            "prior_uncertainty_score": _q(prior_uncertainty),
            "posterior_uncertainty_score": _q(posterior_uncertainty),
            "entropy_reduction_score": _q(entropy_reduction),
            "effective_information_content_score":
                _q(effective_information_content),
            "uncertainty_classification": uncertainty_classification,
        }
        entropy_assessments.append(
            EvidenceEntropyAssessment(
                **entropy_body,
                assessment_hash=stable_hash(entropy_body),
            )
        )

        novelty_weight = novelty_score
        independence_weight = independence_score
        redundancy_discount = _ONE - redundancy_score

        effective_information_gain = (
            entropy_reduction * Decimal("0.450000")
            + novelty_weight * Decimal("0.300000")
            + independence_weight * Decimal("0.200000")
            + redundancy_discount * Decimal("0.050000")
        )
        effective_information_gain *= (
            Decimal("0.600000")
            + redundancy_discount * Decimal("0.400000")
        )
        effective_information_gain = min(
            _ONE,
            max(_ZERO, effective_information_gain),
        )

        gain_classification = _classification(
            effective_information_gain,
            (
                "high_information_gain",
                "medium_information_gain",
                "low_information_gain",
            ),
        )

        basis: list[str] = []
        basis.append(
            "high_novelty"
            if novelty_score >= Decimal("0.750000")
            else "moderate_novelty"
            if novelty_score >= Decimal("0.400000")
            else "low_novelty"
        )
        basis.append(
            "high_independence"
            if independence_score >= Decimal("0.750000")
            else "moderate_independence"
            if independence_score >= Decimal("0.400000")
            else "low_independence"
        )
        basis.append(
            "limited_redundancy_discount"
            if redundancy_score <= Decimal("0.250000")
            else "material_redundancy_discount"
            if redundancy_score <= Decimal("0.650000")
            else "severe_redundancy_discount"
        )
        basis.append(
            "material_entropy_reduction"
            if entropy_reduction >= Decimal("0.400000")
            else "limited_entropy_reduction"
        )

        gain_body = {
            "evidence_node_id": node_id,
            "evidence_id": novelty.evidence_id,
            "source_id": novelty.source_id,
            "entropy_reduction_score": _q(entropy_reduction),
            "novelty_weight": _q(novelty_weight),
            "independence_weight": _q(independence_weight),
            "redundancy_discount": _q(redundancy_discount),
            "effective_information_gain_score":
                _q(effective_information_gain),
            "information_gain_classification": gain_classification,
            "information_gain_basis": tuple(basis),
        }
        gain_assessments.append(
            EvidenceInformationGainAssessment(
                **gain_body,
                assessment_hash=stable_hash(gain_body),
            )
        )

    entropy_tuple = tuple(
        sorted(entropy_assessments, key=lambda item: item.evidence_node_id)
    )
    gain_tuple = tuple(
        sorted(gain_assessments, key=lambda item: item.evidence_node_id)
    )

    ranked = sorted(
        gain_tuple,
        key=lambda item: (
            -_d(item.effective_information_gain_score),
            item.evidence_node_id,
        ),
    )
    ranking: list[InformationGainRankingEntry] = []
    for index, item in enumerate(ranked, start=1):
        novelty = novelty_by_node[item.evidence_node_id]
        redundancy = redundancy_by_node[item.evidence_node_id]
        body = {
            "rank": index,
            "evidence_node_id": item.evidence_node_id,
            "evidence_id": item.evidence_id,
            "effective_information_gain_score":
                item.effective_information_gain_score,
            "novelty_score": novelty.novelty_score,
            "redundancy_score": redundancy.redundancy_score,
        }
        ranking.append(
            InformationGainRankingEntry(
                **body,
                ranking_hash=stable_hash(body),
            )
        )

    prior_scores = [
        _d(item.prior_uncertainty_score)
        for item in entropy_tuple
    ]
    posterior_scores = [
        _d(item.posterior_uncertainty_score)
        for item in entropy_tuple
    ]
    reductions = [
        _d(item.entropy_reduction_score)
        for item in entropy_tuple
    ]
    gains = [
        _d(item.effective_information_gain_score)
        for item in gain_tuple
    ]

    def mean(values: list[Decimal]) -> Decimal:
        if not values:
            return _ZERO
        return sum(values, _ZERO) / Decimal(len(values))

    package_body = {
        "source_redundancy_novelty_package_id":
            redundancy_novelty_package.package_id,
        "source_redundancy_novelty_package_hash":
            redundancy_novelty_package.package_hash,
        "entropy_assessments": entropy_tuple,
        "information_gain_assessments": gain_tuple,
        "information_gain_ranking": tuple(ranking),
        "aggregate_prior_uncertainty_score": _q(mean(prior_scores)),
        "aggregate_posterior_uncertainty_score": _q(mean(posterior_scores)),
        "aggregate_entropy_reduction_score": _q(mean(reductions)),
        "mean_effective_information_gain_score": _q(mean(gains)),
        "maximum_effective_information_gain_score":
            _q(max(gains) if gains else _ZERO),
        "minimum_effective_information_gain_score":
            _q(min(gains) if gains else _ZERO),
        "high_information_gain_evidence_count": sum(
            item.information_gain_classification
            == "high_information_gain"
            for item in gain_tuple
        ),
        "medium_information_gain_evidence_count": sum(
            item.information_gain_classification
            == "medium_information_gain"
            for item in gain_tuple
        ),
        "low_information_gain_evidence_count": sum(
            item.information_gain_classification
            == "low_information_gain"
            for item in gain_tuple
        ),
    }
    package_hash = stable_hash(package_body)

    return EntropyInformationGainPackage(
        package_id="entropy-information-gain:" + package_hash,
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


def verify_entropy_information_gain_package(
    package: EntropyInformationGainPackage,
) -> bool:
    if not isinstance(package, EntropyInformationGainPackage):
        raise OracleEntropyInformationGainInvariantError(
            "invalid OII-006 package type"
        )

    for item in package.entropy_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleEntropyInformationGainInvariantError(
                "entropy assessment hash verification failed"
            )

    for item in package.information_gain_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleEntropyInformationGainInvariantError(
                "information-gain assessment hash verification failed"
            )

    for item in package.information_gain_ranking:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "ranking_hash"
        }
        if stable_hash(body) != item.ranking_hash:
            raise OracleEntropyInformationGainInvariantError(
                "ranking-entry hash verification failed"
            )

    expected_ranks = tuple(
        range(1, len(package.information_gain_ranking) + 1)
    )
    actual_ranks = tuple(
        item.rank for item in package.information_gain_ranking
    )
    if actual_ranks != expected_ranks:
        raise OracleEntropyInformationGainInvariantError(
            "information-gain ranking is not contiguous"
        )

    package_body = {
        "source_redundancy_novelty_package_id":
            package.source_redundancy_novelty_package_id,
        "source_redundancy_novelty_package_hash":
            package.source_redundancy_novelty_package_hash,
        "entropy_assessments": package.entropy_assessments,
        "information_gain_assessments":
            package.information_gain_assessments,
        "information_gain_ranking": package.information_gain_ranking,
        "aggregate_prior_uncertainty_score":
            package.aggregate_prior_uncertainty_score,
        "aggregate_posterior_uncertainty_score":
            package.aggregate_posterior_uncertainty_score,
        "aggregate_entropy_reduction_score":
            package.aggregate_entropy_reduction_score,
        "mean_effective_information_gain_score":
            package.mean_effective_information_gain_score,
        "maximum_effective_information_gain_score":
            package.maximum_effective_information_gain_score,
        "minimum_effective_information_gain_score":
            package.minimum_effective_information_gain_score,
        "high_information_gain_evidence_count":
            package.high_information_gain_evidence_count,
        "medium_information_gain_evidence_count":
            package.medium_information_gain_evidence_count,
        "low_information_gain_evidence_count":
            package.low_information_gain_evidence_count,
    }
    if stable_hash(package_body) != package.package_hash:
        raise OracleEntropyInformationGainInvariantError(
            "package hash verification failed"
        )
    if package.package_id != "entropy-information-gain:" + package.package_hash:
        raise OracleEntropyInformationGainInvariantError(
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
        raise OracleEntropyInformationGainInvariantError(
            "OII-006 safety boundary violated"
        )
    return True


def serialize_entropy_information_gain_package(
    package: EntropyInformationGainPackage,
) -> str:
    verify_entropy_information_gain_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "EvidenceEntropyAssessment",
    "EvidenceInformationGainAssessment",
    "InformationGainRankingEntry",
    "EntropyInformationGainPackage",
    "OracleEntropyInformationGainInvariantError",
    "analyze_entropy_and_information_gain",
    "verify_entropy_information_gain_package",
    "serialize_entropy_information_gain_package",
]
