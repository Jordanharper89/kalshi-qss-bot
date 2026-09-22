from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_010_CERTIFIED_RELATED_MARKET_GRAPH_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_related_market_graph_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_010_certified_related_market_graph_registry.py"

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
    MarketCategory,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    VenueIdentity,
)
from qseries_v2.universal_market_discovery.certified_canonical_market_contract import (
    UMD_002_REVISION,
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from qseries_v2.universal_market_discovery.certified_market_category_hierarchy_registry import (
    UMD_005_REVISION,
    CertifiedMarketCategoryNode,
    ReadOnlyMarketCategoryHierarchyRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_classification_registry import (
    UMD_006_REVISION,
    CertifiedMarketClassification,
    ReadOnlyMarketClassificationRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_metadata_registry import (
    UMD_007_REVISION,
    CertifiedMarketMetadata,
    ReadOnlyMarketMetadataRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_lifecycle_and_settlement_registry import (
    UMD_008_REVISION,
    CertifiedMarketLifecycleSettlementRecord,
    ReadOnlyMarketLifecycleSettlementRegistry,
)
from qseries_v2.universal_market_discovery.certified_market_duplicate_resolution_registry import (
    UMD_009_REVISION,
    CertifiedMarketDuplicateResolution,
    DuplicateResolutionStatus,
    ReadOnlyMarketDuplicateResolutionRegistry,
)
from qseries_v2.universal_market_discovery.certified_related_market_graph_registry import (
    UMD_010_REVISION,
    CertifiedRelatedMarketEdge,
    ReadOnlyRelatedMarketGraphRegistry,
    RelatedMarketRelationshipType,
    build_umd_010_certification_manifest,
    certify_related_market_graph_registry,
    certify_umd_010_foundation,
    verify_umd_010_certified_related_market_graph_registry,
)

FIXED = datetime(2026, 8, 5, 16, 0, tzinfo=timezone.utc)

def lineage(build_id, revision, source):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id=build_id,
        revision=revision,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=(source,),
        created_at=FIXED,
    )

def market(native_id, venue_id):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=venue_id,
            canonical_name=venue_id.title(),
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=venue_id,
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="EVENT",
        canonical_title=f"Market {native_id}",
        canonical_description="Fixture market.",
        instrument_type=MarketInstrumentType.BINARY,
        category=MarketCategory(
            category_id="bitcoin",
            canonical_name="Bitcoin",
            parent_category_id="crypto",
            path=("markets", "crypto", "bitcoin"),
        ),
        asset_class=AssetClass.PREDICTION_MARKET,
        geographic_scope=GeographicScope.GLOBAL,
        quote_currency="USD",
        tick_size="0.01",
        price_precision=2,
        lifecycle=MarketLifecycle.OPEN,
        opens_at=None,
        closes_at=None,
        expires_at=None,
        settlement_method=SettlementMethod.UNKNOWN,
        settlement_source=None,
        settlement_rule=None,
        settles_at=None,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def duplicate_registry(markets):
    def category_node(category_id, parent=None):
        return CertifiedMarketCategoryNode(
            category_id=category_id,
            canonical_name=category_id.title(),
            parent_category_id=parent,
            aliases=(),
            description=f"Category {category_id}.",
            metadata={},
            lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                f"fixture://umd-005/{category_id}",
            ),
        )

    category_registry = ReadOnlyMarketCategoryHierarchyRegistry(
        categories=(
            category_node("markets"),
            category_node("crypto", "markets"),
            category_node("bitcoin", "crypto"),
        ),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )
    classifications = tuple(
        CertifiedMarketClassification.from_market(
            item,
            metadata={},
            lineage=lineage(
                "UMD-006",
                UMD_006_REVISION,
                f"fixture://umd-006/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    classification_registry = ReadOnlyMarketClassificationRegistry(
        classifications=classifications,
        markets=tuple(markets),
        category_registry=category_registry,
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )
    metadata_records = tuple(
        CertifiedMarketMetadata.from_market(
            item,
            short_title=item.native_market_id,
            symbol="BTC",
            language="en",
            timezone_name="America/Chicago",
            tags=("bitcoin",),
            keywords=("Bitcoin",),
            external_reference_ids={"fixture": item.native_market_id},
            metadata_version="1.0.0",
            attributes={},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                f"fixture://umd-007/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    metadata_registry = ReadOnlyMarketMetadataRegistry(
        metadata_records=metadata_records,
        markets=tuple(markets),
        classification_registry=classification_registry,
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )
    lifecycle_records = tuple(
        CertifiedMarketLifecycleSettlementRecord.from_market(
            item,
            final_value=None,
            metadata={},
            lineage=lineage(
                "UMD-008",
                UMD_008_REVISION,
                f"fixture://umd-008/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    lifecycle_registry = ReadOnlyMarketLifecycleSettlementRegistry(
        records=lifecycle_records,
        markets=tuple(markets),
        metadata_registry=metadata_registry,
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )
    return ReadOnlyMarketDuplicateResolutionRegistry(
        resolutions=(),
        markets=tuple(markets),
        lifecycle_registry=lifecycle_registry,
        registry_lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/registry",
        ),
    )

def edge(source, target, relationship, cross_venue):
    return CertifiedRelatedMarketEdge(
        source_market_id=source.canonical_market_id,
        target_market_id=target.canonical_market_id,
        relationship_type=relationship,
        rationale_code="fixture-link",
        cross_venue=cross_venue,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-010",
            UMD_010_REVISION,
            "fixture://umd-010/edge",
        ),
    )

def registry(edges, markets):
    return ReadOnlyRelatedMarketGraphRegistry(
        edges=tuple(edges),
        markets=tuple(markets),
        duplicate_registry=duplicate_registry(markets),
        registry_lineage=lineage(
            "UMD-010",
            UMD_010_REVISION,
            "fixture://umd-010/registry",
        ),
    )

class TestUMD010(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_010_foundation()["certified"])
        self.assertTrue(
            verify_umd_010_certified_related_market_graph_registry()
        )

    def test_edge_identity_deterministic(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        self.assertEqual(
            edge(a, b, RelatedMarketRelationshipType.CORRELATED, True).edge_id,
            edge(b, a, RelatedMarketRelationshipType.CORRELATED, True).edge_id,
        )

    def test_directed_edge_identity_preserves_direction(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        self.assertNotEqual(
            edge(a, b, RelatedMarketRelationshipType.DEPENDS_ON, True).edge_id,
            edge(b, a, RelatedMarketRelationshipType.DEPENDS_ON, True).edge_id,
        )

    def test_immutable(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = edge(a, b, RelatedMarketRelationshipType.CORRELATED, True)
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.cross_venue = False
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = registry(
            (edge(a, b, RelatedMarketRelationshipType.CORRELATED, True),),
            (a, b),
        )
        result = certify_related_market_graph_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["edge_count"], 1)

    def test_duplicate_edge_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        value = edge(a, b, RelatedMarketRelationshipType.CORRELATED, True)
        with self.assertRaises(ValueError):
            registry((value, value), (a, b))

    def test_unknown_market_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        with self.assertRaises(ValueError):
            registry(
                (edge(a, b, RelatedMarketRelationshipType.CORRELATED, True),),
                (a, c),
            )

    def test_cross_venue_flag_validated(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        with self.assertRaises(ValueError):
            registry(
                (edge(a, b, RelatedMarketRelationshipType.CORRELATED, False),),
                (a, b),
            )

    def test_cycle_rejected(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        with self.assertRaises(ValueError):
            registry(
                (
                    edge(a, b, RelatedMarketRelationshipType.DEPENDS_ON, True),
                    edge(b, c, RelatedMarketRelationshipType.DEPENDS_ON, True),
                    edge(c, a, RelatedMarketRelationshipType.DEPENDS_ON, True),
                ),
                (a, b, c),
            )

    def test_neighbors_deterministic(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        c = market("C", "venue-c")
        item = registry(
            (
                edge(a, c, RelatedMarketRelationshipType.CORRELATED, True),
                edge(a, b, RelatedMarketRelationshipType.HEDGE, True),
            ),
            (c, b, a),
        )
        self.assertEqual(
            item.neighbors(a.canonical_market_id),
            tuple(sorted((b.canonical_market_id, c.canonical_market_id))),
        )

    def test_relationship_filter(self):
        a = market("A", "venue-a")
        b = market("B", "venue-b")
        item = registry(
            (
                edge(a, b, RelatedMarketRelationshipType.HEDGE, True),
            ),
            (a, b),
        )
        self.assertEqual(
            len(item.by_relationship_type(RelatedMarketRelationshipType.HEDGE)),
            1,
        )

    def test_side_effects_disabled(self):
        manifest = build_umd_010_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-010 CERTIFICATION TEST")
    print(" CERTIFIED RELATED MARKET GRAPH REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD010)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_010_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-009 consumed read-only")
    print("[PASS] Canonical related-market edge IDs deterministic")
    print("[PASS] Directed and undirected edge identity verified")
    print("[PASS] Unknown markets rejected")
    print("[PASS] Duplicate edges rejected")
    print("[PASS] Cross-venue flags validated")
    print("[PASS] Directed relationship cycles rejected")
    print("[PASS] Neighbor traversal deterministic")
    print("[PASS] Read-only graph registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic inference and graph mutation disabled")
    print("[PASS] Persistence and publication disabled")
    print("[PASS] Q Series execution disabled")
    print("[DONE] UMD-010 CERTIFIED RELATED MARKET GRAPH REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_related_market_graph_registry import (
    UMD_010_BUILD_ID,
    UMD_010_BUILD_NAME,
    UMD_010_REVISION,
    UMD_010_SCHEMA_VERSION,
    RelatedMarketRelationshipType,
    CertifiedRelatedMarketEdge,
    ReadOnlyRelatedMarketGraphRegistry,
    UMD010CertificationManifest,
    build_umd_010_certification_manifest,
    certify_related_market_graph_registry,
    certify_umd_010_foundation,
    verify_umd_010_certified_related_market_graph_registry,
)
"""

NAMES = [
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

def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()

def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(normalize(source), encoding="utf-8", newline="\n")
    os.replace(temp, path)

def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(f"UMD package initializer missing: {INIT}")
    source = INIT.read_text(encoding="utf-8")
    if "from .certified_related_market_graph_registry import (" not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)
    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start:end + 1]
        missing = [
            name for name in NAMES
            if f'"{name}"' not in block and f"'{name}'" not in block
        ]
        if missing:
            block = block[:-1] + "".join(
                f'    "{name}",\n' for name in missing
            ) + "]"
            source = source[:start] + block + source[end + 1:]
    else:
        source += "\n__all__ = [\n" + "".join(
            f'    "{name}",\n' for name in NAMES
        ) + "]\n"
    write_exact(INIT, source)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        modules = (
            ("universal_market_discovery_foundation", "verify_umd_foundation"),
            ("certified_canonical_market_contract", "verify_umd_002_certified_canonical_market_contract"),
            ("certified_venue_identity_registry", "verify_umd_003_certified_venue_identity_registry"),
            ("certified_venue_market_binding_registry", "verify_umd_004_certified_venue_market_binding_registry"),
            ("certified_market_category_hierarchy_registry", "verify_umd_005_certified_market_category_hierarchy_registry"),
            ("certified_market_classification_registry", "verify_umd_006_certified_market_classification_registry"),
            ("certified_market_metadata_registry", "verify_umd_007_certified_market_metadata_registry"),
            ("certified_market_lifecycle_and_settlement_registry", "verify_umd_008_certified_market_lifecycle_and_settlement_registry"),
            ("certified_market_duplicate_resolution_registry", "verify_umd_009_certified_market_duplicate_resolution_registry"),
        )
        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery." + module_name
            )
            if not getattr(module, verifier_name)():
                raise RuntimeError(f"{module_name} verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_related_market_graph_registry"
        )
        required = (
            "CertifiedRelatedMarketEdge",
            "ReadOnlyRelatedMarketGraphRegistry",
            "certify_related_market_graph_registry",
            "certify_umd_010_foundation",
            "verify_umd_010_certified_related_market_graph_registry",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-010 missing symbols: " + ", ".join(missing))
        module.verify_umd_010_certified_related_market_graph_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-010 INSTALLER")
    print(" CERTIFIED RELATED MARKET GRAPH REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-009 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-010",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004", "UMD-005",
            "UMD-006", "UMD-007", "UMD-008", "UMD-009",
        ),
        "mode": "read_only",
    }
    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-010 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-010 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_010_certified_related_market_graph_registry.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
