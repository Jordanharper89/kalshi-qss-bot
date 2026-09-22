from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_market_duplicate_resolution_registry import (
    ReadOnlyMarketDuplicateResolutionRegistry,
)

UMD_010_BUILD_ID = "UMD-010"
UMD_010_BUILD_NAME = "Certified Related Market Graph Registry"
UMD_010_REVISION = "UMD_010_CERTIFIED_RELATED_MARKET_GRAPH_REGISTRY_V1"
UMD_010_SCHEMA_VERSION = "1.0.0"

class RelatedMarketRelationshipType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    EQUIVALENT = "equivalent"
    DEPENDS_ON = "depends_on"
    HEDGE = "hedge"
    CORRELATED = "correlated"
    INVERSE = "inverse"
    SAME_EVENT = "same_event"
    SAME_UNDERLYING = "same_underlying"
    OTHER = "other"

UNDIRECTED_RELATIONSHIPS = frozenset({
    RelatedMarketRelationshipType.EQUIVALENT,
    RelatedMarketRelationshipType.HEDGE,
    RelatedMarketRelationshipType.CORRELATED,
    RelatedMarketRelationshipType.INVERSE,
    RelatedMarketRelationshipType.SAME_EVENT,
    RelatedMarketRelationshipType.SAME_UNDERLYING,
})

ACYCLIC_DIRECTED_RELATIONSHIPS = frozenset({
    RelatedMarketRelationshipType.PARENT,
    RelatedMarketRelationshipType.CHILD,
    RelatedMarketRelationshipType.DEPENDS_ON,
})

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _market_id(value: str, name: str) -> str:
    value = _text(value, name)
    if not value.startswith("umd:mkt:"):
        raise ValueError(f"{name} must use UMD market prefix")
    return value

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedRelatedMarketEdge:
    source_market_id: str
    target_market_id: str
    relationship_type: RelatedMarketRelationshipType
    rationale_code: str
    cross_venue: bool
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        source = _market_id(self.source_market_id, "source_market_id")
        target = _market_id(self.target_market_id, "target_market_id")
        if source == target:
            raise ValueError("edge cannot self-reference")
        object.__setattr__(self, "source_market_id", source)
        object.__setattr__(self, "target_market_id", target)

        if not isinstance(self.relationship_type, RelatedMarketRelationshipType):
            object.__setattr__(
                self,
                "relationship_type",
                RelatedMarketRelationshipType(self.relationship_type),
            )

        object.__setattr__(
            self,
            "rationale_code",
            _text(self.rationale_code, "rationale_code").lower(),
        )
        if not isinstance(self.cross_venue, bool):
            raise TypeError("cross_venue must be boolean")
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("edge lineage must belong to UMD")
        if self.lineage.build_id != UMD_010_BUILD_ID:
            raise ValueError("edge lineage must use build_id UMD-010")

    def identity_payload(self) -> Mapping[str, Any]:
        source = self.source_market_id
        target = self.target_market_id
        if self.relationship_type in UNDIRECTED_RELATIONSHIPS:
            source, target = sorted((source, target))
        return {
            "source_market_id": source,
            "target_market_id": target,
            "relationship_type": self.relationship_type,
        }

    @property
    def edge_id(self) -> str:
        return "umd:edge:" + deterministic_sha256(self.identity_payload())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_market_id": self.source_market_id,
            "target_market_id": self.target_market_id,
            "relationship_type": self.relationship_type,
            "rationale_code": self.rationale_code,
            "cross_venue": self.cross_venue,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyRelatedMarketGraphRegistry:
    edges: Tuple[CertifiedRelatedMarketEdge, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    duplicate_registry: ReadOnlyMarketDuplicateResolutionRegistry
    registry_lineage: ImmutableLineage
    _by_edge_id: Mapping[str, CertifiedRelatedMarketEdge] = field(init=False, repr=False)
    _outgoing: Mapping[str, Tuple[CertifiedRelatedMarketEdge, ...]] = field(init=False, repr=False)
    _incoming: Mapping[str, Tuple[CertifiedRelatedMarketEdge, ...]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        edges = tuple(sorted(self.edges, key=lambda edge: edge.edge_id))
        markets = tuple(sorted(self.markets, key=lambda market: market.canonical_market_id))
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "markets", markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_010_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-010")

        market_by_id = {market.canonical_market_id: market for market in markets}
        if len(market_by_id) != len(markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_edge_id = {}
        outgoing = {}
        incoming = {}

        for edge in edges:
            if edge.edge_id in by_edge_id:
                raise ValueError("duplicate related-market edge")
            source = market_by_id.get(edge.source_market_id)
            target = market_by_id.get(edge.target_market_id)
            if source is None:
                raise ValueError("unknown source market")
            if target is None:
                raise ValueError("unknown target market")

            expected_cross_venue = source.venue.venue_id != target.venue.venue_id
            if edge.cross_venue != expected_cross_venue:
                raise ValueError("cross_venue flag mismatch")

            canonical_source = self.duplicate_registry.canonical_market_id_for(
                edge.source_market_id
            )
            canonical_target = self.duplicate_registry.canonical_market_id_for(
                edge.target_market_id
            )
            if (
                canonical_source == canonical_target
                and edge.relationship_type
                != RelatedMarketRelationshipType.EQUIVALENT
            ):
                raise ValueError(
                    "duplicate-equivalent markets may only use EQUIVALENT relationship"
                )

            by_edge_id[edge.edge_id] = edge
            outgoing.setdefault(edge.source_market_id, []).append(edge)
            incoming.setdefault(edge.target_market_id, []).append(edge)

            if edge.relationship_type in UNDIRECTED_RELATIONSHIPS:
                outgoing.setdefault(edge.target_market_id, []).append(edge)
                incoming.setdefault(edge.source_market_id, []).append(edge)

        self._validate_cycles(edges)

        object.__setattr__(
            self,
            "_by_edge_id",
            MappingProxyType(by_edge_id),
        )
        object.__setattr__(
            self,
            "_outgoing",
            MappingProxyType({
                key: tuple(sorted(value, key=lambda edge: edge.edge_id))
                for key, value in outgoing.items()
            }),
        )
        object.__setattr__(
            self,
            "_incoming",
            MappingProxyType({
                key: tuple(sorted(value, key=lambda edge: edge.edge_id))
                for key, value in incoming.items()
            }),
        )

    @staticmethod
    def _validate_cycles(
        edges: Tuple[CertifiedRelatedMarketEdge, ...]
    ) -> None:
        for relationship_type in ACYCLIC_DIRECTED_RELATIONSHIPS:
            adjacency = {}
            for edge in edges:
                if edge.relationship_type == relationship_type:
                    adjacency.setdefault(
                        edge.source_market_id,
                        [],
                    ).append(edge.target_market_id)

            visiting = set()
            visited = set()

            def visit(node: str) -> None:
                if node in visiting:
                    raise ValueError(
                        f"cycle detected for relationship {relationship_type.value}"
                    )
                if node in visited:
                    return
                visiting.add(node)
                for target in adjacency.get(node, ()):
                    visit(target)
                visiting.remove(node)
                visited.add(node)

            for node in tuple(adjacency):
                visit(node)

    def get(self, edge_id: str) -> CertifiedRelatedMarketEdge | None:
        return self._by_edge_id.get(_text(edge_id, "edge_id"))

    def outgoing_from(
        self,
        canonical_market_id: str,
    ) -> Tuple[CertifiedRelatedMarketEdge, ...]:
        return self._outgoing.get(
            _market_id(canonical_market_id, "canonical_market_id"),
            (),
        )

    def incoming_to(
        self,
        canonical_market_id: str,
    ) -> Tuple[CertifiedRelatedMarketEdge, ...]:
        return self._incoming.get(
            _market_id(canonical_market_id, "canonical_market_id"),
            (),
        )

    def neighbors(self, canonical_market_id: str) -> Tuple[str, ...]:
        market_id = _market_id(canonical_market_id, "canonical_market_id")
        neighbors = set()
        for edge in self.outgoing_from(market_id):
            neighbors.add(
                edge.target_market_id
                if edge.source_market_id == market_id
                else edge.source_market_id
            )
        for edge in self.incoming_to(market_id):
            neighbors.add(
                edge.source_market_id
                if edge.target_market_id == market_id
                else edge.target_market_id
            )
        return tuple(sorted(neighbors))

    def by_relationship_type(
        self,
        relationship_type: RelatedMarketRelationshipType,
    ) -> Tuple[CertifiedRelatedMarketEdge, ...]:
        if not isinstance(relationship_type, RelatedMarketRelationshipType):
            relationship_type = RelatedMarketRelationshipType(relationship_type)
        return tuple(
            edge for edge in self.edges
            if edge.relationship_type == relationship_type
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "edges": self.edges,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "duplicate_registry_hash": self.duplicate_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD010CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "subsystem_id": self.subsystem_id,
            "build_id": self.build_id,
            "build_name": self.build_name,
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "registry_mode": self.registry_mode,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

def build_umd_010_certification_manifest() -> UMD010CertificationManifest:
    return UMD010CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_010_BUILD_ID,
        build_name=UMD_010_BUILD_NAME,
        revision=UMD_010_REVISION,
        schema_version=UMD_010_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001", "UMD-002", "UMD-003", "UMD-004", "UMD-005",
            "UMD-006", "UMD-007", "UMD-008", "UMD-009",
        ),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_related_market_graph_registry(
    registry: ReadOnlyRelatedMarketGraphRegistry,
) -> Mapping[str, Any]:
    checks = {
        "edge_ids_unique": len(
            {edge.edge_id for edge in registry.edges}
        ) == len(registry.edges),
        "deterministic_ordering": tuple(
            edge.edge_id for edge in registry.edges
        ) == tuple(sorted(edge.edge_id for edge in registry.edges)),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "read_only_indexes": isinstance(registry._by_edge_id, MappingProxyType)
        and isinstance(registry._outgoing, MappingProxyType)
        and isinstance(registry._incoming, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType({
        "certified": not failed,
        "registry_hash": registry.registry_hash,
        "edge_count": len(registry.edges),
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def certify_umd_010_foundation() -> Mapping[str, Any]:
    manifest = build_umd_010_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-010",
        "upstreams_frozen": manifest.upstream_builds == (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004", "UMD-005",
            "UMD-006", "UMD-007", "UMD-008", "UMD-009",
        ),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType({
        "certified": not failed,
        "build_id": manifest.build_id,
        "revision": manifest.revision,
        "manifest_hash": manifest.manifest_hash,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def verify_umd_010_certified_related_market_graph_registry() -> bool:
    result = certify_umd_010_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-010 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_010_BUILD_ID",
    "UMD_010_BUILD_NAME",
    "UMD_010_REVISION",
    "UMD_010_SCHEMA_VERSION",
    "RelatedMarketRelationshipType",
    "CertifiedRelatedMarketEdge",
    "ReadOnlyRelatedMarketGraphRegistry",
    "UMD010CertificationManifest",
    "build_umd_010_certification_manifest",
    "certify_related_market_graph_registry",
    "certify_umd_010_foundation",
    "verify_umd_010_certified_related_market_graph_registry",
]
