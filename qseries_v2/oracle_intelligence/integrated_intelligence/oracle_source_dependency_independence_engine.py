from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_EVEN, getcontext
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from .oracle_source_identity_provenance_graph_contract import (
    EvidenceIdentityNode,
    SourceProvenanceGraph,
    verify_graph,
)

ENGINE_ID = "OII-004"
SCHEMA_VERSION = "OII-004.v1"
ALGORITHM_VERSION = "source-dependency-independence.v1"

getcontext().prec = 50
_QUANT = Decimal("0.000001")


class OracleSourceDependencyIndependenceInvariantError(ValueError):
    """Raised when an OII-004 invariant is violated."""


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
        items = [_canonical(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ),
        )
    if isinstance(value, Decimal):
        return format(value.quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return format(Decimal(str(value)).quantize(_QUANT), "f")
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
class SourceDependencyAssessment:
    node_id: str
    direct_dependency_node_ids: tuple[str, ...]
    transitive_dependency_node_ids: tuple[str, ...]
    primary_origin_node_ids: tuple[str, ...]
    shared_origin_group_ids: tuple[str, ...]
    direct_dependency_count: int
    transitive_dependency_count: int
    circular_dependency_detected: bool
    dependency_depth: int
    dependency_density: str
    assessment_hash: str


@dataclass(frozen=True)
class EvidenceIndependenceAssessment:
    evidence_node_id: str
    evidence_id: str
    source_id: str
    compared_evidence_node_ids: tuple[str, ...]
    dependent_evidence_node_ids: tuple[str, ...]
    independent_evidence_node_ids: tuple[str, ...]
    shared_primary_origin_node_ids: tuple[str, ...]
    shared_origin_group_ids: tuple[str, ...]
    dependency_overlap_ratio: str
    source_independence_score: str
    circular_dependency_penalty: str
    independence_classification: str
    assessment_hash: str


@dataclass(frozen=True)
class SourceDependencyIndependencePackage:
    package_id: str
    source_graph_id: str
    source_graph_hash: str
    dependency_assessments: tuple[SourceDependencyAssessment, ...]
    evidence_independence_assessments: tuple[EvidenceIndependenceAssessment, ...]
    mean_source_independence_score: str
    minimum_source_independence_score: str
    maximum_source_independence_score: str
    fully_independent_evidence_count: int
    partially_independent_evidence_count: int
    dependent_evidence_count: int
    circular_dependency_evidence_count: int
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


def _adjacency(graph: SourceProvenanceGraph) -> dict[str, tuple[str, ...]]:
    dependency_relationships = {
        "derived_from",
        "quotes",
        "summarizes",
        "duplicates",
        "depends_on",
        "same_primary_origin",
    }
    mapping: dict[str, list[str]] = {
        node_id: [] for node_id in graph.deterministic_traversal
    }
    for edge in graph.edges:
        if edge.relationship in dependency_relationships:
            mapping[edge.from_node_id].append(edge.to_node_id)
    return {key: tuple(sorted(values)) for key, values in mapping.items()}


def _depth(start: str, adjacency: Mapping[str, tuple[str, ...]]) -> int:
    maximum = 0
    pending: list[tuple[str, int, frozenset[str]]] = [
        (start, 0, frozenset({start}))
    ]
    while pending:
        node_id, depth, path = pending.pop()
        maximum = max(maximum, depth)
        for target in adjacency.get(node_id, ()):
            if target not in path:
                pending.append((target, depth + 1, path | {target}))
    return maximum


def _resolution_maps(graph: SourceProvenanceGraph):
    return {
        resolution.node_id: resolution
        for resolution in graph.origin_resolutions
    }


def _classify(score: Decimal, dependent_count: int) -> str:
    if dependent_count == 0 and score >= Decimal("0.999999"):
        return "fully_independent"
    if score >= Decimal("0.500000"):
        return "partially_independent"
    return "dependent"


def analyze_source_dependency_and_independence(
    *,
    graph: SourceProvenanceGraph,
) -> SourceDependencyIndependencePackage:
    if not isinstance(graph, SourceProvenanceGraph):
        raise OracleSourceDependencyIndependenceInvariantError(
            "source must be the canonical OII-003 provenance graph"
        )
    try:
        verify_graph(graph)
    except Exception as exc:
        raise OracleSourceDependencyIndependenceInvariantError(
            "OII-003 provenance graph verification failed"
        ) from exc

    if not graph.read_only:
        raise OracleSourceDependencyIndependenceInvariantError(
            "OII-003 graph is not read-only"
        )

    forbidden = (
        graph.publication_allowed,
        graph.alerting_allowed,
        graph.qseries_handoff_allowed,
        graph.qseries_execution_allowed,
        graph.order_creation_allowed,
        graph.funds_movement_allowed,
        graph.portfolio_mutation_allowed,
    )
    if any(forbidden):
        raise OracleSourceDependencyIndependenceInvariantError(
            "OII-003 graph contains forbidden authority"
        )

    adjacency = _adjacency(graph)
    resolutions = _resolution_maps(graph)
    node_count = len(graph.deterministic_traversal)

    dependency_assessments: list[SourceDependencyAssessment] = []
    for node_id in graph.deterministic_traversal:
        resolution = resolutions[node_id]
        direct = adjacency.get(node_id, ())
        transitive = resolution.dependency_chain_node_ids
        body = {
            "node_id": node_id,
            "direct_dependency_node_ids": direct,
            "transitive_dependency_node_ids": transitive,
            "primary_origin_node_ids": resolution.primary_origin_node_ids,
            "shared_origin_group_ids": resolution.shared_origin_group_ids,
            "direct_dependency_count": len(direct),
            "transitive_dependency_count": len(transitive),
            "circular_dependency_detected": resolution.circular_dependency_detected,
            "dependency_depth": _depth(node_id, adjacency),
            "dependency_density": _q(
                _ratio(len(transitive), max(1, node_count - 1))
            ),
        }
        dependency_assessments.append(
            SourceDependencyAssessment(
                **body,
                assessment_hash=stable_hash(body),
            )
        )

    evidence_nodes = tuple(
        sorted(graph.evidence_nodes, key=lambda item: item.node_id)
    )
    evidence_assessments: list[EvidenceIndependenceAssessment] = []

    for current in evidence_nodes:
        current_resolution = resolutions[current.node_id]
        current_dependencies = set(
            current_resolution.dependency_chain_node_ids
        )
        current_origins = set(current_resolution.primary_origin_node_ids)
        current_groups = set(current_resolution.shared_origin_group_ids)

        dependent: list[str] = []
        independent: list[str] = []
        shared_primary: set[str] = set()
        shared_groups: set[str] = set()
        overlap_total = Decimal("0")
        comparisons = 0

        for other in evidence_nodes:
            if other.node_id == current.node_id:
                continue
            other_resolution = resolutions[other.node_id]
            other_dependencies = set(
                other_resolution.dependency_chain_node_ids
            )
            other_origins = set(other_resolution.primary_origin_node_ids)
            other_groups = set(other_resolution.shared_origin_group_ids)

            shared_dependency = current_dependencies & other_dependencies
            common_origins = current_origins & other_origins
            common_groups = current_groups & other_groups

            union = current_dependencies | other_dependencies
            overlap = _ratio(len(shared_dependency), len(union))
            overlap_total += overlap
            comparisons += 1

            relationship_exists = bool(
                shared_dependency or common_origins or common_groups
            )
            if relationship_exists:
                dependent.append(other.node_id)
            else:
                independent.append(other.node_id)

            shared_primary.update(common_origins)
            shared_groups.update(common_groups)

        mean_overlap = (
            overlap_total / Decimal(comparisons)
            if comparisons
            else Decimal("0")
        )
        dependency_fraction = _ratio(
            len(dependent),
            max(1, len(evidence_nodes) - 1),
        )
        circular_penalty = (
            Decimal("0.250000")
            if current_resolution.circular_dependency_detected
            else Decimal("0")
        )
        independence = Decimal("1") - (
            dependency_fraction * Decimal("0.700000")
        ) - (
            mean_overlap * Decimal("0.300000")
        ) - circular_penalty
        independence = min(Decimal("1"), max(Decimal("0"), independence))
        classification = _classify(independence, len(dependent))

        body = {
            "evidence_node_id": current.node_id,
            "evidence_id": current.evidence_id,
            "source_id": current.source_id,
            "compared_evidence_node_ids": tuple(
                sorted(
                    item.node_id
                    for item in evidence_nodes
                    if item.node_id != current.node_id
                )
            ),
            "dependent_evidence_node_ids": tuple(sorted(dependent)),
            "independent_evidence_node_ids": tuple(sorted(independent)),
            "shared_primary_origin_node_ids": tuple(sorted(shared_primary)),
            "shared_origin_group_ids": tuple(sorted(shared_groups)),
            "dependency_overlap_ratio": _q(mean_overlap),
            "source_independence_score": _q(independence),
            "circular_dependency_penalty": _q(circular_penalty),
            "independence_classification": classification,
        }
        evidence_assessments.append(
            EvidenceIndependenceAssessment(
                **body,
                assessment_hash=stable_hash(body),
            )
        )

    scores = [
        Decimal(item.source_independence_score)
        for item in evidence_assessments
    ]
    mean_score = (
        sum(scores, Decimal("0")) / Decimal(len(scores))
        if scores
        else Decimal("0")
    )
    minimum = min(scores) if scores else Decimal("0")
    maximum = max(scores) if scores else Decimal("0")

    package_body = {
        "source_graph_id": graph.graph_id,
        "source_graph_hash": graph.graph_hash,
        "dependency_assessments": tuple(dependency_assessments),
        "evidence_independence_assessments": tuple(evidence_assessments),
        "mean_source_independence_score": _q(mean_score),
        "minimum_source_independence_score": _q(minimum),
        "maximum_source_independence_score": _q(maximum),
        "fully_independent_evidence_count": sum(
            item.independence_classification == "fully_independent"
            for item in evidence_assessments
        ),
        "partially_independent_evidence_count": sum(
            item.independence_classification == "partially_independent"
            for item in evidence_assessments
        ),
        "dependent_evidence_count": sum(
            item.independence_classification == "dependent"
            for item in evidence_assessments
        ),
        "circular_dependency_evidence_count": sum(
            resolutions[item.node_id].circular_dependency_detected
            for item in evidence_nodes
        ),
    }
    package_hash = stable_hash(package_body)

    return SourceDependencyIndependencePackage(
        package_id="source-independence:" + package_hash,
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


def verify_independence_package(
    package: SourceDependencyIndependencePackage,
) -> bool:
    if not isinstance(package, SourceDependencyIndependencePackage):
        raise OracleSourceDependencyIndependenceInvariantError(
            "invalid OII-004 package type"
        )

    dependency_hashes_valid = all(
        stable_hash(
            {
                key: value
                for key, value in asdict(item).items()
                if key != "assessment_hash"
            }
        ) == item.assessment_hash
        for item in package.dependency_assessments
    )
    evidence_hashes_valid = all(
        stable_hash(
            {
                key: value
                for key, value in asdict(item).items()
                if key != "assessment_hash"
            }
        ) == item.assessment_hash
        for item in package.evidence_independence_assessments
    )
    if not dependency_hashes_valid or not evidence_hashes_valid:
        raise OracleSourceDependencyIndependenceInvariantError(
            "assessment hash verification failed"
        )

    body = {
        "source_graph_id": package.source_graph_id,
        "source_graph_hash": package.source_graph_hash,
        "dependency_assessments": package.dependency_assessments,
        "evidence_independence_assessments": package.evidence_independence_assessments,
        "mean_source_independence_score": package.mean_source_independence_score,
        "minimum_source_independence_score": package.minimum_source_independence_score,
        "maximum_source_independence_score": package.maximum_source_independence_score,
        "fully_independent_evidence_count": package.fully_independent_evidence_count,
        "partially_independent_evidence_count": package.partially_independent_evidence_count,
        "dependent_evidence_count": package.dependent_evidence_count,
        "circular_dependency_evidence_count": package.circular_dependency_evidence_count,
    }
    if stable_hash(body) != package.package_hash:
        raise OracleSourceDependencyIndependenceInvariantError(
            "package hash verification failed"
        )
    if package.package_id != "source-independence:" + package.package_hash:
        raise OracleSourceDependencyIndependenceInvariantError(
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
        raise OracleSourceDependencyIndependenceInvariantError(
            "OII-004 safety boundary violated"
        )
    return True


def serialize_independence_package(
    package: SourceDependencyIndependencePackage,
) -> str:
    verify_independence_package(package)
    return canonical_json(package)


__all__ = [
    "ENGINE_ID",
    "SCHEMA_VERSION",
    "ALGORITHM_VERSION",
    "SourceDependencyAssessment",
    "EvidenceIndependenceAssessment",
    "SourceDependencyIndependencePackage",
    "OracleSourceDependencyIndependenceInvariantError",
    "analyze_source_dependency_and_independence",
    "verify_independence_package",
    "serialize_independence_package",
]
