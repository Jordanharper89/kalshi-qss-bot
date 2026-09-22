from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .oracle_source_dependency_independence_engine import (
    EvidenceIndependenceAssessment,
    SourceDependencyIndependencePackage,
    verify_independence_package,
)

ENGINE_ID = "OII-005"
SCHEMA_VERSION = "OII-005.v1"
ALGORITHM_VERSION = "redundancy-novelty.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")


class OracleRedundancyNoveltyInvariantError(ValueError):
    """Raised when an OII-005 redundancy/novelty invariant is violated."""


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
        values = [_canonical(item) for item in value]
        return sorted(
            values,
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
    bounded = min(Decimal("1"), max(Decimal("0"), value))
    return format(bounded.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return Decimal(numerator) / Decimal(denominator)


@dataclass(frozen=True)
class EvidenceRedundancyAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    compared_evidence_node_ids: tuple[str, ...]
    redundant_evidence_node_ids: tuple[str, ...]
    nonredundant_evidence_node_ids: tuple[str, ...]
    shared_primary_origin_node_ids: tuple[str, ...]
    shared_origin_group_ids: tuple[str, ...]
    redundancy_ratio: str
    origin_reuse_ratio: str
    dependency_reuse_ratio: str
    circularity_penalty: str
    redundancy_score: str
    redundancy_classification: str
    assessment_hash: str


@dataclass(frozen=True)
class EvidenceNoveltyAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    source_independence_score: str
    redundancy_score: str
    novelty_score: str
    novelty_classification: str
    novelty_basis: tuple[str, ...]
    assessment_hash: str


@dataclass(frozen=True)
class RedundancyCluster:
    cluster_id: str
    evidence_node_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    shared_primary_origin_node_ids: tuple[str, ...]
    shared_origin_group_ids: tuple[str, ...]
    cluster_redundancy_score: str
    cluster_hash: str


@dataclass(frozen=True)
class RedundancyNoveltyPackage:
    package_id: str
    source_independence_package_id: str
    source_independence_package_hash: str
    evidence_redundancy_assessments: tuple[EvidenceRedundancyAssessment, ...]
    evidence_novelty_assessments: tuple[EvidenceNoveltyAssessment, ...]
    redundancy_clusters: tuple[RedundancyCluster, ...]
    mean_redundancy_score: str
    mean_novelty_score: str
    maximum_redundancy_score: str
    minimum_novelty_score: str
    high_novelty_evidence_count: int
    medium_novelty_evidence_count: int
    low_novelty_evidence_count: int
    high_redundancy_evidence_count: int
    cluster_count: int
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


def _redundancy_classification(score: Decimal) -> str:
    if score >= Decimal("0.750000"):
        return "high_redundancy"
    if score >= Decimal("0.350000"):
        return "moderate_redundancy"
    return "low_redundancy"


def _novelty_classification(score: Decimal) -> str:
    if score >= Decimal("0.750000"):
        return "high_novelty"
    if score >= Decimal("0.400000"):
        return "medium_novelty"
    return "low_novelty"


def _build_cluster_components(
    assessments: tuple[EvidenceRedundancyAssessment, ...],
) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, set[str]] = {
        item.evidence_node_id: set()
        for item in assessments
    }
    for item in assessments:
        for other in item.redundant_evidence_node_ids:
            adjacency[item.evidence_node_id].add(other)
            adjacency.setdefault(other, set()).add(item.evidence_node_id)

    unseen = set(adjacency)
    components: list[tuple[str, ...]] = []
    while unseen:
        seed = min(unseen)
        component: set[str] = set()
        pending = [seed]
        while pending:
            current = pending.pop()
            if current in component:
                continue
            component.add(current)
            pending.extend(sorted(adjacency.get(current, ()), reverse=True))
        unseen.difference_update(component)
        if len(component) > 1:
            components.append(tuple(sorted(component)))
    return tuple(sorted(components))


def analyze_redundancy_and_novelty(
    *,
    source_independence_package: SourceDependencyIndependencePackage,
) -> RedundancyNoveltyPackage:
    if not isinstance(
        source_independence_package,
        SourceDependencyIndependencePackage,
    ):
        raise OracleRedundancyNoveltyInvariantError(
            "source must be the canonical OII-004 package"
        )

    try:
        verify_independence_package(source_independence_package)
    except Exception as exc:
        raise OracleRedundancyNoveltyInvariantError(
            "OII-004 package verification failed"
        ) from exc

    forbidden = (
        source_independence_package.publication_allowed,
        source_independence_package.alerting_allowed,
        source_independence_package.final_intelligence_conclusion_allowed,
        source_independence_package.probability_estimation_allowed,
        source_independence_package.qseries_handoff_allowed,
        source_independence_package.qseries_execution_allowed,
        source_independence_package.order_creation_allowed,
        source_independence_package.funds_movement_allowed,
        source_independence_package.portfolio_mutation_allowed,
    )
    if source_independence_package.read_only is not True or any(forbidden):
        raise OracleRedundancyNoveltyInvariantError(
            "OII-004 package violates permanent safety boundary"
        )

    evidence_items = tuple(
        sorted(
            source_independence_package.evidence_independence_assessments,
            key=lambda item: item.evidence_node_id,
        )
    )
    by_node = {
        item.evidence_node_id: item
        for item in evidence_items
    }

    redundancy_assessments: list[EvidenceRedundancyAssessment] = []
    novelty_assessments: list[EvidenceNoveltyAssessment] = []

    for current in evidence_items:
        comparison_count = len(current.compared_evidence_node_ids)
        dependent_set = set(current.dependent_evidence_node_ids)
        redundant: list[str] = []
        nonredundant: list[str] = []
        origin_overlap_events = 0
        dependency_overlap_events = 0

        for other_node_id in current.compared_evidence_node_ids:
            other = by_node[other_node_id]
            shared_primary = set(current.shared_primary_origin_node_ids) & set(
                other.shared_primary_origin_node_ids
            )
            shared_groups = set(current.shared_origin_group_ids) & set(
                other.shared_origin_group_ids
            )
            dependency_overlap = (
                other_node_id in dependent_set
                or current.evidence_node_id
                in set(other.dependent_evidence_node_ids)
            )

            if shared_primary or shared_groups:
                origin_overlap_events += 1
            if dependency_overlap:
                dependency_overlap_events += 1

            if shared_primary or shared_groups or dependency_overlap:
                redundant.append(other_node_id)
            else:
                nonredundant.append(other_node_id)

        redundancy_ratio = _ratio(len(redundant), comparison_count)
        origin_reuse_ratio = _ratio(origin_overlap_events, comparison_count)
        dependency_reuse_ratio = _ratio(
            dependency_overlap_events,
            comparison_count,
        )
        circularity_penalty = Decimal(current.circular_dependency_penalty)

        redundancy_score = (
            redundancy_ratio * Decimal("0.500000")
            + origin_reuse_ratio * Decimal("0.300000")
            + dependency_reuse_ratio * Decimal("0.200000")
            + circularity_penalty
        )
        redundancy_score = min(
            Decimal("1"),
            max(Decimal("0"), redundancy_score),
        )
        redundancy_classification = _redundancy_classification(
            redundancy_score
        )

        redundancy_body = {
            "evidence_node_id": current.evidence_node_id,
            "evidence_id": current.evidence_id,
            "source_id": current.source_id,
            "compared_evidence_node_ids": current.compared_evidence_node_ids,
            "redundant_evidence_node_ids": tuple(sorted(redundant)),
            "nonredundant_evidence_node_ids": tuple(sorted(nonredundant)),
            "shared_primary_origin_node_ids": current.shared_primary_origin_node_ids,
            "shared_origin_group_ids": current.shared_origin_group_ids,
            "redundancy_ratio": _q(redundancy_ratio),
            "origin_reuse_ratio": _q(origin_reuse_ratio),
            "dependency_reuse_ratio": _q(dependency_reuse_ratio),
            "circularity_penalty": _q(circularity_penalty),
            "redundancy_score": _q(redundancy_score),
            "redundancy_classification": redundancy_classification,
        }
        redundancy_assessments.append(
            EvidenceRedundancyAssessment(
                **redundancy_body,
                assessment_hash=stable_hash(redundancy_body),
            )
        )

        independence = Decimal(current.source_independence_score)
        novelty_score = (
            independence * Decimal("0.650000")
            + (Decimal("1") - redundancy_score)
            * Decimal("0.350000")
        )
        novelty_score = min(
            Decimal("1"),
            max(Decimal("0"), novelty_score),
        )
        novelty_classification = _novelty_classification(novelty_score)

        basis: list[str] = []
        if independence >= Decimal("0.750000"):
            basis.append("high_source_independence")
        elif independence >= Decimal("0.400000"):
            basis.append("moderate_source_independence")
        else:
            basis.append("low_source_independence")

        if redundancy_score <= Decimal("0.250000"):
            basis.append("limited_evidence_reuse")
        elif redundancy_score <= Decimal("0.650000"):
            basis.append("material_evidence_reuse")
        else:
            basis.append("substantial_evidence_reuse")

        if circularity_penalty > Decimal("0"):
            basis.append("circular_dependency_penalty_applied")
        else:
            basis.append("no_circular_dependency_penalty")

        novelty_body = {
            "evidence_node_id": current.evidence_node_id,
            "evidence_id": current.evidence_id,
            "source_id": current.source_id,
            "source_independence_score": current.source_independence_score,
            "redundancy_score": _q(redundancy_score),
            "novelty_score": _q(novelty_score),
            "novelty_classification": novelty_classification,
            "novelty_basis": tuple(basis),
        }
        novelty_assessments.append(
            EvidenceNoveltyAssessment(
                **novelty_body,
                assessment_hash=stable_hash(novelty_body),
            )
        )

    redundancy_tuple = tuple(
        sorted(
            redundancy_assessments,
            key=lambda item: item.evidence_node_id,
        )
    )
    novelty_tuple = tuple(
        sorted(
            novelty_assessments,
            key=lambda item: item.evidence_node_id,
        )
    )

    redundancy_by_node = {
        item.evidence_node_id: item
        for item in redundancy_tuple
    }
    evidence_by_node = {
        item.evidence_node_id: item
        for item in evidence_items
    }

    clusters: list[RedundancyCluster] = []
    for component in _build_cluster_components(redundancy_tuple):
        component_assessments = [
            redundancy_by_node[node_id]
            for node_id in component
        ]
        evidence_ids = tuple(
            sorted(
                evidence_by_node[node_id].evidence_id
                for node_id in component
            )
        )
        primary_origins = tuple(
            sorted(
                {
                    origin
                    for item in component_assessments
                    for origin in item.shared_primary_origin_node_ids
                }
            )
        )
        origin_groups = tuple(
            sorted(
                {
                    group
                    for item in component_assessments
                    for group in item.shared_origin_group_ids
                }
            )
        )
        cluster_score = sum(
            (
                Decimal(item.redundancy_score)
                for item in component_assessments
            ),
            Decimal("0"),
        ) / Decimal(len(component_assessments))
        cluster_body = {
            "evidence_node_ids": component,
            "evidence_ids": evidence_ids,
            "shared_primary_origin_node_ids": primary_origins,
            "shared_origin_group_ids": origin_groups,
            "cluster_redundancy_score": _q(cluster_score),
        }
        cluster_hash = stable_hash(cluster_body)
        clusters.append(
            RedundancyCluster(
                cluster_id="redundancy-cluster:" + cluster_hash,
                **cluster_body,
                cluster_hash=cluster_hash,
            )
        )

    clusters_tuple = tuple(
        sorted(clusters, key=lambda item: item.cluster_id)
    )
    redundancy_scores = [
        Decimal(item.redundancy_score)
        for item in redundancy_tuple
    ]
    novelty_scores = [
        Decimal(item.novelty_score)
        for item in novelty_tuple
    ]
    mean_redundancy = (
        sum(redundancy_scores, Decimal("0"))
        / Decimal(len(redundancy_scores))
        if redundancy_scores
        else Decimal("0")
    )
    mean_novelty = (
        sum(novelty_scores, Decimal("0"))
        / Decimal(len(novelty_scores))
        if novelty_scores
        else Decimal("0")
    )

    package_body = {
        "source_independence_package_id":
            source_independence_package.package_id,
        "source_independence_package_hash":
            source_independence_package.package_hash,
        "evidence_redundancy_assessments": redundancy_tuple,
        "evidence_novelty_assessments": novelty_tuple,
        "redundancy_clusters": clusters_tuple,
        "mean_redundancy_score": _q(mean_redundancy),
        "mean_novelty_score": _q(mean_novelty),
        "maximum_redundancy_score": _q(
            max(redundancy_scores)
            if redundancy_scores
            else Decimal("0")
        ),
        "minimum_novelty_score": _q(
            min(novelty_scores)
            if novelty_scores
            else Decimal("0")
        ),
        "high_novelty_evidence_count": sum(
            item.novelty_classification == "high_novelty"
            for item in novelty_tuple
        ),
        "medium_novelty_evidence_count": sum(
            item.novelty_classification == "medium_novelty"
            for item in novelty_tuple
        ),
        "low_novelty_evidence_count": sum(
            item.novelty_classification == "low_novelty"
            for item in novelty_tuple
        ),
        "high_redundancy_evidence_count": sum(
            item.redundancy_classification == "high_redundancy"
            for item in redundancy_tuple
        ),
        "cluster_count": len(clusters_tuple),
    }
    package_hash = stable_hash(package_body)

    return RedundancyNoveltyPackage(
        package_id="redundancy-novelty:" + package_hash,
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


def verify_redundancy_novelty_package(
    package: RedundancyNoveltyPackage,
) -> bool:
    if not isinstance(package, RedundancyNoveltyPackage):
        raise OracleRedundancyNoveltyInvariantError(
            "invalid OII-005 package type"
        )

    for item in package.evidence_redundancy_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleRedundancyNoveltyInvariantError(
                "redundancy assessment hash verification failed"
            )

    for item in package.evidence_novelty_assessments:
        body = {
            key: value
            for key, value in asdict(item).items()
            if key != "assessment_hash"
        }
        if stable_hash(body) != item.assessment_hash:
            raise OracleRedundancyNoveltyInvariantError(
                "novelty assessment hash verification failed"
            )

    for item in package.redundancy_clusters:
        body = {
            "evidence_node_ids": item.evidence_node_ids,
            "evidence_ids": item.evidence_ids,
            "shared_primary_origin_node_ids":
                item.shared_primary_origin_node_ids,
            "shared_origin_group_ids": item.shared_origin_group_ids,
            "cluster_redundancy_score": item.cluster_redundancy_score,
        }
        if stable_hash(body) != item.cluster_hash:
            raise OracleRedundancyNoveltyInvariantError(
                "cluster hash verification failed"
            )
        if item.cluster_id != "redundancy-cluster:" + item.cluster_hash:
            raise OracleRedundancyNoveltyInvariantError(
                "cluster identity verification failed"
            )

    package_body = {
        "source_independence_package_id":
            package.source_independence_package_id,
        "source_independence_package_hash":
            package.source_independence_package_hash,
        "evidence_redundancy_assessments":
            package.evidence_redundancy_assessments,
        "evidence_novelty_assessments":
            package.evidence_novelty_assessments,
        "redundancy_clusters": package.redundancy_clusters,
        "mean_redundancy_score": package.mean_redundancy_score,
        "mean_novelty_score": package.mean_novelty_score,
        "maximum_redundancy_score": package.maximum_redundancy_score,
        "minimum_novelty_score": package.minimum_novelty_score,
        "high_novelty_evidence_count":
            package.high_novelty_evidence_count,
        "medium_novelty_evidence_count":
            package.medium_novelty_evidence_count,
        "low_novelty_evidence_count":
            package.low_novelty_evidence_count,
        "high_redundancy_evidence_count":
            package.high_redundancy_evidence_count,
        "cluster_count": package.cluster_count,
    }
    if stable_hash(package_body) != package.package_hash:
        raise OracleRedundancyNoveltyInvariantError(
            "package hash verification failed"
        )
    if package.package_id != "redundancy-novelty:" + package.package_hash:
        raise OracleRedundancyNoveltyInvariantError(
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
        raise OracleRedundancyNoveltyInvariantError(
            "OII-005 safety boundary violated"
        )
    return True


def serialize_redundancy_novelty_package(
    package: RedundancyNoveltyPackage,
) -> str:
    verify_redundancy_novelty_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "EvidenceRedundancyAssessment",
    "EvidenceNoveltyAssessment",
    "RedundancyCluster",
    "RedundancyNoveltyPackage",
    "OracleRedundancyNoveltyInvariantError",
    "analyze_redundancy_and_novelty",
    "verify_redundancy_novelty_package",
    "serialize_redundancy_novelty_package",
]
