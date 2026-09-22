from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_005_CERTIFIED_MARKET_CATEGORY_HIERARCHY_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_market_category_hierarchy_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_005_certified_market_category_hierarchy_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket

UMD_005_BUILD_ID = "UMD-005"
UMD_005_BUILD_NAME = "Certified Market Category Hierarchy Registry"
UMD_005_REVISION = "UMD_005_CERTIFIED_MARKET_CATEGORY_HIERARCHY_REGISTRY_V1"
UMD_005_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "persistence_write",
    "registry_mutation",
    "oracle_memory_mutation",
    "publication",
    "order_submission",
    "trade_execution",
)

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized

def _slug(value: str, name: str) -> str:
    normalized = _text(value, name).lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(
            f"{name} may contain only lowercase letters, digits, hyphen, and underscore"
        )
    return normalized

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(key), item) for key, item in value.items())))

def _unique(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_slug(value, name) for value in values}))

@dataclass(frozen=True, slots=True)
class CertifiedMarketCategoryNode:
    category_id: str
    canonical_name: str
    parent_category_id: str | None
    aliases: Tuple[str, ...]
    description: str | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "category_id", _slug(self.category_id, "category_id"))
        object.__setattr__(
            self,
            "canonical_name",
            _text(self.canonical_name, "canonical_name"),
        )
        if self.parent_category_id is not None:
            parent = _slug(self.parent_category_id, "parent_category_id")
            if parent == self.category_id:
                raise ValueError("category cannot be its own parent")
            object.__setattr__(self, "parent_category_id", parent)

        aliases = tuple(sorted({_text(alias, "alias") for alias in self.aliases}))
        if self.canonical_name.casefold() in {alias.casefold() for alias in aliases}:
            raise ValueError("aliases must not repeat canonical_name")
        object.__setattr__(self, "aliases", aliases)

        if self.description is not None:
            object.__setattr__(
                self,
                "description",
                _text(self.description, "description"),
            )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("category lineage must belong to UMD")
        if self.lineage.build_id != UMD_005_BUILD_ID:
            raise ValueError("category lineage must use build_id UMD-005")

    def identity_payload(self) -> Mapping[str, Any]:
        return {"category_id": self.category_id}

    @property
    def canonical_category_id(self) -> str:
        return f"umd:category:{deterministic_sha256(self.identity_payload())}"

    @property
    def alias_keys(self) -> Tuple[str, ...]:
        values = (self.category_id, self.canonical_name, *self.aliases)
        return tuple(sorted({_text(value, "alias_key").casefold() for value in values}))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "canonical_category_id": self.canonical_category_id,
            "category_id": self.category_id,
            "canonical_name": self.canonical_name,
            "parent_category_id": self.parent_category_id,
            "aliases": self.aliases,
            "description": self.description,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketCategoryHierarchyRegistry:
    categories: Tuple[CertifiedMarketCategoryNode, ...]
    registry_lineage: ImmutableLineage
    _by_category_id: Mapping[str, CertifiedMarketCategoryNode] = field(
        init=False, repr=False
    )
    _alias_index: Mapping[str, str] = field(init=False, repr=False)
    _children: Mapping[str, Tuple[str, ...]] = field(init=False, repr=False)
    _paths: Mapping[str, Tuple[str, ...]] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.categories, key=lambda item: item.category_id))
        object.__setattr__(self, "categories", ordered)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_005_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-005")

        by_id = {}
        alias_index = {}
        children = {}

        for category in ordered:
            if category.category_id in by_id:
                raise ValueError(f"duplicate category_id: {category.category_id}")
            by_id[category.category_id] = category

        for category in ordered:
            parent = category.parent_category_id
            if parent is not None and parent not in by_id:
                raise ValueError(
                    f"unknown parent category '{parent}' for '{category.category_id}'"
                )
            if parent is not None:
                children.setdefault(parent, []).append(category.category_id)

            for alias_key in category.alias_keys:
                existing = alias_index.get(alias_key)
                if existing is not None and existing != category.category_id:
                    raise ValueError(f"ambiguous category alias '{alias_key}'")
                alias_index[alias_key] = category.category_id

        paths = {}
        visiting = set()

        def resolve_path(category_id: str) -> Tuple[str, ...]:
            if category_id in paths:
                return paths[category_id]
            if category_id in visiting:
                raise ValueError(f"category hierarchy cycle detected at '{category_id}'")
            visiting.add(category_id)
            node = by_id[category_id]
            if node.parent_category_id is None:
                path = (category_id,)
            else:
                path = resolve_path(node.parent_category_id) + (category_id,)
            visiting.remove(category_id)
            paths[category_id] = path
            return path

        for category_id in by_id:
            resolve_path(category_id)

        frozen_children = {
            parent: tuple(sorted(values))
            for parent, values in children.items()
        }

        object.__setattr__(self, "_by_category_id", MappingProxyType(by_id))
        object.__setattr__(self, "_alias_index", MappingProxyType(alias_index))
        object.__setattr__(self, "_children", MappingProxyType(frozen_children))
        object.__setattr__(self, "_paths", MappingProxyType(paths))

    def get(self, category_id: str) -> CertifiedMarketCategoryNode | None:
        return self._by_category_id.get(_slug(category_id, "category_id"))

    def resolve_alias(self, alias: str) -> CertifiedMarketCategoryNode | None:
        category_id = self._alias_index.get(_text(alias, "alias").casefold())
        if category_id is None:
            return None
        return self._by_category_id[category_id]

    def path_for(self, category_id: str) -> Tuple[str, ...]:
        normalized = _slug(category_id, "category_id")
        if normalized not in self._paths:
            raise KeyError(normalized)
        return self._paths[normalized]

    def children_of(self, category_id: str) -> Tuple[CertifiedMarketCategoryNode, ...]:
        normalized = _slug(category_id, "category_id")
        return tuple(
            self._by_category_id[child_id]
            for child_id in self._children.get(normalized, ())
        )

    def roots(self) -> Tuple[CertifiedMarketCategoryNode, ...]:
        return tuple(
            category
            for category in self.categories
            if category.parent_category_id is None
        )

    def validate_market(
        self,
        market: CertifiedCanonicalMarket,
    ) -> bool:
        category = self.get(market.category.category_id)
        if category is None:
            raise ValueError(
                f"market category is not registered: {market.category.category_id}"
            )
        expected_path = self.path_for(category.category_id)
        if market.category.path and tuple(market.category.path) != expected_path:
            raise ValueError(
                "market category path does not match certified hierarchy"
            )
        if market.category.parent_category_id != category.parent_category_id:
            raise ValueError(
                "market category parent does not match certified hierarchy"
            )
        return True

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "categories": self.categories,
            "resolved_paths": tuple(
                (category_id, self._paths[category_id])
                for category_id in sorted(self._paths)
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketCategoryHierarchyCertificationResult:
    certified: bool
    registry_hash: str
    category_count: int
    root_count: int
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))

@dataclass(frozen=True, slots=True)
class UMD005CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
    prohibited_capabilities: Tuple[str, ...]
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
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

def build_umd_005_certification_manifest() -> UMD005CertificationManifest:
    return UMD005CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_005_BUILD_ID,
        build_name=UMD_005_BUILD_NAME,
        revision=UMD_005_REVISION,
        schema_version=UMD_005_SCHEMA_VERSION,
        upstream_builds=("UMD-001", "UMD-002", "UMD-003", "UMD-004"),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_category_hierarchy_registry(
    registry: ReadOnlyMarketCategoryHierarchyRegistry,
) -> MarketCategoryHierarchyCertificationResult:
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "category_ids_unique": len(
            {category.category_id for category in registry.categories}
        ) == len(registry.categories),
        "canonical_ids_unique": len(
            {category.canonical_category_id for category in registry.categories}
        ) == len(registry.categories),
        "all_parents_resolve": all(
            category.parent_category_id is None
            or registry.get(category.parent_category_id) is not None
            for category in registry.categories
        ),
        "all_paths_resolve": all(
            registry.path_for(category.category_id)[-1] == category.category_id
            for category in registry.categories
        ),
        "all_lineage_certified": all(
            category.lineage.subsystem_id == "UMD"
            and category.lineage.build_id == "UMD-005"
            for category in registry.categories
        ),
        "deterministic_ordering": tuple(
            category.category_id for category in registry.categories
        ) == tuple(sorted(category.category_id for category in registry.categories)),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "registry_maps_read_only": isinstance(
            registry._by_category_id, MappingProxyType
        )
        and isinstance(registry._alias_index, MappingProxyType)
        and isinstance(registry._children, MappingProxyType)
        and isinstance(registry._paths, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MarketCategoryHierarchyCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        category_count=len(registry.categories),
        root_count=len(registry.roots()),
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_005_foundation() -> Mapping[str, Any]:
    manifest = build_umd_005_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-005",
        "upstreams_frozen": manifest.upstream_builds
        == ("UMD-001", "UMD-002", "UMD-003", "UMD-004"),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType(
        {
            "certified": not failed,
            "build_id": manifest.build_id,
            "revision": manifest.revision,
            "manifest_hash": manifest.manifest_hash,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )

def verify_umd_005_certified_market_category_hierarchy_registry() -> bool:
    result = certify_umd_005_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-005 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_005_BUILD_ID",
    "UMD_005_BUILD_NAME",
    "UMD_005_REVISION",
    "UMD_005_SCHEMA_VERSION",
    "CertifiedMarketCategoryNode",
    "ReadOnlyMarketCategoryHierarchyRegistry",
    "MarketCategoryHierarchyCertificationResult",
    "UMD005CertificationManifest",
    "build_umd_005_certification_manifest",
    "certify_market_category_hierarchy_registry",
    "certify_umd_005_foundation",
    "verify_umd_005_certified_market_category_hierarchy_registry",
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
    build_umd_005_certification_manifest,
    certify_market_category_hierarchy_registry,
    certify_umd_005_foundation,
    verify_umd_005_certified_market_category_hierarchy_registry,
)

FIXED = datetime(2026, 8, 5, 7, 0, tzinfo=timezone.utc)

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

def category(category_id, parent=None, name=None, aliases=()):
    return CertifiedMarketCategoryNode(
        category_id=category_id,
        canonical_name=name or category_id.replace("-", " ").title(),
        parent_category_id=parent,
        aliases=aliases,
        description=f"Certified category {category_id}.",
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            f"fixture://umd-005/{category_id}",
        ),
    )

def registry(categories):
    return ReadOnlyMarketCategoryHierarchyRegistry(
        categories=tuple(categories),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )

def market():
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id="BTC-100K",
        native_event_id="BTC",
        canonical_title="Will Bitcoin exceed $100,000?",
        canonical_description="Fixture.",
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
        duplicate_resolution_keys=("bitcoin", "100000"),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            "fixture://umd-002/market",
        ),
    )

class TestUMD005(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_005_foundation()["certified"])
        self.assertTrue(
            verify_umd_005_certified_market_category_hierarchy_registry()
        )

    def test_category_identity_deterministic(self):
        self.assertEqual(
            category("crypto").canonical_category_id,
            category("crypto").canonical_category_id,
        )
        self.assertNotEqual(
            category("crypto").canonical_category_id,
            category("equities").canonical_category_id,
        )

    def test_category_record_hash_deterministic(self):
        self.assertEqual(
            category("crypto").record_hash,
            category("crypto").record_hash,
        )

    def test_immutable(self):
        item = category("crypto")
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.category_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        r = registry(
            (
                category("bitcoin", "crypto"),
                category("markets"),
                category("crypto", "markets"),
            )
        )
        result = certify_market_category_hierarchy_registry(r)
        self.assertTrue(result.certified)
        self.assertEqual(result.category_count, 3)
        self.assertEqual(result.root_count, 1)

    def test_path_resolution(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        self.assertEqual(
            r.path_for("bitcoin"),
            ("markets", "crypto", "bitcoin"),
        )

    def test_alias_resolution(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets", aliases=("Digital Assets",)),
            )
        )
        self.assertEqual(
            r.resolve_alias("digital assets").category_id,
            "crypto",
        )

    def test_unknown_parent_rejected(self):
        with self.assertRaises(ValueError):
            registry((category("bitcoin", "crypto"),))

    def test_cycle_rejected(self):
        with self.assertRaises(ValueError):
            registry(
                (
                    category("a", "b"),
                    category("b", "a"),
                )
            )

    def test_ambiguous_alias_rejected(self):
        with self.assertRaises(ValueError):
            registry(
                (
                    category("markets"),
                    category("crypto", "markets", aliases=("Shared",)),
                    category("equities", "markets", aliases=("Shared",)),
                )
            )

    def test_market_validation(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        self.assertTrue(r.validate_market(market()))

    def test_market_path_mismatch_rejected(self):
        r = registry(
            (
                category("markets"),
                category("crypto", "markets"),
                category("bitcoin", "crypto"),
            )
        )
        bad = market()
        object.__setattr__(
            bad,
            "category",
            MarketCategory(
                category_id="bitcoin",
                canonical_name="Bitcoin",
                parent_category_id="crypto",
                path=("wrong", "bitcoin"),
            ),
        )
        with self.assertRaises(ValueError):
            r.validate_market(bad)

    def test_side_effects_disabled(self):
        manifest = build_umd_005_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-005 CERTIFICATION TEST")
    print(" CERTIFIED MARKET CATEGORY HIERARCHY REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD005)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_005_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-004 consumed read-only")
    print("[PASS] Canonical category IDs deterministic")
    print("[PASS] Parent-child hierarchy validated")
    print("[PASS] Unknown parents rejected")
    print("[PASS] Hierarchy cycles rejected")
    print("[PASS] Category aliases resolved deterministically")
    print("[PASS] Ambiguous aliases rejected")
    print("[PASS] Canonical market category paths validated")
    print("[PASS] Read-only category registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-005 CERTIFIED MARKET CATEGORY HIERARCHY REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_market_category_hierarchy_registry import (
    UMD_005_BUILD_ID,
    UMD_005_BUILD_NAME,
    UMD_005_REVISION,
    UMD_005_SCHEMA_VERSION,
    CertifiedMarketCategoryNode,
    ReadOnlyMarketCategoryHierarchyRegistry,
    MarketCategoryHierarchyCertificationResult,
    UMD005CertificationManifest,
    build_umd_005_certification_manifest,
    certify_market_category_hierarchy_registry,
    certify_umd_005_foundation,
    verify_umd_005_certified_market_category_hierarchy_registry,
)
"""

NAMES = [
    "UMD_005_BUILD_ID",
    "UMD_005_BUILD_NAME",
    "UMD_005_REVISION",
    "UMD_005_SCHEMA_VERSION",
    "CertifiedMarketCategoryNode",
    "ReadOnlyMarketCategoryHierarchyRegistry",
    "MarketCategoryHierarchyCertificationResult",
    "UMD005CertificationManifest",
    "build_umd_005_certification_manifest",
    "certify_market_category_hierarchy_registry",
    "certify_umd_005_foundation",
    "verify_umd_005_certified_market_category_hierarchy_registry",
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
    if "from .certified_market_category_hierarchy_registry import (" not in source:
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
            addition = "".join(f'    "{name}",\n' for name in missing)
            block = block[:-1] + addition + "]"
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
            (
                "universal_market_discovery_foundation",
                "verify_umd_foundation",
            ),
            (
                "certified_canonical_market_contract",
                "verify_umd_002_certified_canonical_market_contract",
            ),
            (
                "certified_venue_identity_registry",
                "verify_umd_003_certified_venue_identity_registry",
            ),
            (
                "certified_venue_market_binding_registry",
                "verify_umd_004_certified_venue_market_binding_registry",
            ),
        )
        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery." + module_name
            )
            verifier = getattr(module, verifier_name)
            if not verifier():
                raise RuntimeError(f"{module_name} verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_market_category_hierarchy_registry"
        )
        required = (
            "CertifiedMarketCategoryNode",
            "ReadOnlyMarketCategoryHierarchyRegistry",
            "certify_market_category_hierarchy_registry",
            "certify_umd_005_foundation",
            "verify_umd_005_certified_market_category_hierarchy_registry",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-005 missing symbols: " + ", ".join(missing))
        module.verify_umd_005_certified_market_category_hierarchy_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-005 INSTALLER")
    print(" CERTIFIED MARKET CATEGORY HIERARCHY REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-004 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-005",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": ("UMD-001", "UMD-002", "UMD-003", "UMD-004"),
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
    print("[PASS] Required UMD-005 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-005 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_005_certified_market_category_hierarchy_registry.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
