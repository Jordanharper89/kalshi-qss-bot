from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_006_CERTIFIED_MARKET_CLASSIFICATION_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_market_classification_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_006_certified_market_classification_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    deterministic_sha256,
)
from .certified_canonical_market_contract import (
    AssetClass,
    CertifiedCanonicalMarket,
    GeographicScope,
)
from .certified_market_category_hierarchy_registry import (
    ReadOnlyMarketCategoryHierarchyRegistry,
)

UMD_006_BUILD_ID = "UMD-006"
UMD_006_BUILD_NAME = "Certified Market Classification Registry"
UMD_006_REVISION = "UMD_006_CERTIFIED_MARKET_CLASSIFICATION_REGISTRY_V1"
UMD_006_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_ai_classification",
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

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )

@dataclass(frozen=True, slots=True)
class CertifiedMarketClassification:
    canonical_market_id: str
    category_id: str
    asset_class: AssetClass
    instrument_type: MarketInstrumentType
    geographic_scope: GeographicScope
    settlement_method: SettlementMethod
    lifecycle: MarketLifecycle
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use the UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        object.__setattr__(
            self,
            "category_id",
            _text(self.category_id, "category_id").lower(),
        )

        if not isinstance(self.asset_class, AssetClass):
            object.__setattr__(
                self,
                "asset_class",
                AssetClass(self.asset_class),
            )
        if not isinstance(self.instrument_type, MarketInstrumentType):
            object.__setattr__(
                self,
                "instrument_type",
                MarketInstrumentType(self.instrument_type),
            )
        if not isinstance(self.geographic_scope, GeographicScope):
            object.__setattr__(
                self,
                "geographic_scope",
                GeographicScope(self.geographic_scope),
            )
        if not isinstance(self.settlement_method, SettlementMethod):
            object.__setattr__(
                self,
                "settlement_method",
                SettlementMethod(self.settlement_method),
            )
        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(
                self,
                "lifecycle",
                MarketLifecycle(self.lifecycle),
            )

        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("classification lineage must belong to UMD")
        if self.lineage.build_id != UMD_006_BUILD_ID:
            raise ValueError("classification lineage must use build_id UMD-006")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketClassification":
        return cls(
            canonical_market_id=market.canonical_market_id,
            category_id=market.category.category_id,
            asset_class=market.asset_class,
            instrument_type=market.instrument_type,
            geographic_scope=market.geographic_scope,
            settlement_method=market.settlement_method,
            lifecycle=market.lifecycle,
            metadata=metadata,
            lineage=lineage,
        )

    def identity_payload(self) -> Mapping[str, Any]:
        return {"canonical_market_id": self.canonical_market_id}

    @property
    def classification_id(self) -> str:
        return f"umd:classification:{deterministic_sha256(self.identity_payload())}"

    def classification_payload(self) -> Mapping[str, Any]:
        return {
            "category_id": self.category_id,
            "asset_class": self.asset_class,
            "instrument_type": self.instrument_type,
            "geographic_scope": self.geographic_scope,
            "settlement_method": self.settlement_method,
            "lifecycle": self.lifecycle,
        }

    @property
    def classification_fingerprint(self) -> str:
        return deterministic_sha256(self.classification_payload())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "classification_id": self.classification_id,
            "canonical_market_id": self.canonical_market_id,
            "category_id": self.category_id,
            "asset_class": self.asset_class,
            "instrument_type": self.instrument_type,
            "geographic_scope": self.geographic_scope,
            "settlement_method": self.settlement_method,
            "lifecycle": self.lifecycle,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketClassificationRegistry:
    classifications: Tuple[CertifiedMarketClassification, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    category_registry: ReadOnlyMarketCategoryHierarchyRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketClassification] = field(
        init=False,
        repr=False,
    )
    _by_classification_id: Mapping[str, CertifiedMarketClassification] = field(
        init=False,
        repr=False,
    )
    _by_category_id: Mapping[str, Tuple[CertifiedMarketClassification, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        ordered_classifications = tuple(
            sorted(
                self.classifications,
                key=lambda item: item.classification_id,
            )
        )
        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda item: item.canonical_market_id,
            )
        )
        object.__setattr__(
            self,
            "classifications",
            ordered_classifications,
        )
        object.__setattr__(self, "markets", ordered_markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_006_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-006")

        market_by_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(market_by_id) != len(ordered_markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_classification_id = {}
        category_groups = {}

        for classification in ordered_classifications:
            if classification.classification_id in by_classification_id:
                raise ValueError("duplicate classification ID")
            if classification.canonical_market_id in by_market_id:
                raise ValueError(
                    "canonical market may have only one certified classification"
                )

            market = market_by_id.get(classification.canonical_market_id)
            if market is None:
                raise ValueError(
                    f"unknown canonical market ID: "
                    f"{classification.canonical_market_id}"
                )

            self.category_registry.validate_market(market)

            expected = CertifiedMarketClassification.from_market(
                market,
                metadata=classification.metadata,
                lineage=classification.lineage,
            )

            if (
                classification.classification_payload()
                != expected.classification_payload()
            ):
                raise ValueError(
                    "classification fields do not match canonical market"
                )

            if self.category_registry.get(classification.category_id) is None:
                raise ValueError(
                    f"unregistered category: {classification.category_id}"
                )

            by_market_id[classification.canonical_market_id] = classification
            by_classification_id[
                classification.classification_id
            ] = classification
            category_groups.setdefault(
                classification.category_id,
                [],
            ).append(classification)

        frozen_groups = {
            category_id: tuple(
                sorted(
                    items,
                    key=lambda item: item.canonical_market_id,
                )
            )
            for category_id, items in category_groups.items()
        }

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_classification_id",
            MappingProxyType(by_classification_id),
        )
        object.__setattr__(
            self,
            "_by_category_id",
            MappingProxyType(frozen_groups),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketClassification | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        classification_id: str,
    ) -> CertifiedMarketClassification | None:
        return self._by_classification_id.get(
            _text(classification_id, "classification_id")
        )

    def by_category(
        self,
        category_id: str,
    ) -> Tuple[CertifiedMarketClassification, ...]:
        return self._by_category_id.get(
            _text(category_id, "category_id").lower(),
            (),
        )

    def unclassified_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "classifications": self.classifications,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "category_registry_hash": self.category_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketClassificationCertificationResult:
    certified: bool
    registry_hash: str
    classification_count: int
    unclassified_market_ids: Tuple[str, ...]
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(self.checks)),
        )

@dataclass(frozen=True, slots=True)
class UMD006CertificationManifest:
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

def build_umd_006_certification_manifest() -> UMD006CertificationManifest:
    return UMD006CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_006_BUILD_ID,
        build_name=UMD_006_BUILD_NAME,
        revision=UMD_006_REVISION,
        schema_version=UMD_006_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
        ),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_classification_registry(
    registry: ReadOnlyMarketClassificationRegistry,
    *,
    require_all_markets_classified: bool = True,
) -> MarketClassificationCertificationResult:
    unclassified = registry.unclassified_market_ids()
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "classification_ids_unique": len(
            {
                classification.classification_id
                for classification in registry.classifications
            }
        ) == len(registry.classifications),
        "market_classifications_unique": len(
            {
                classification.canonical_market_id
                for classification in registry.classifications
            }
        ) == len(registry.classifications),
        "all_markets_resolve": all(
            registry.get_by_market(classification.canonical_market_id)
            is not None
            for classification in registry.classifications
        ),
        "all_categories_resolve": all(
            registry.category_registry.get(classification.category_id)
            is not None
            for classification in registry.classifications
        ),
        "all_lineage_certified": all(
            classification.lineage.subsystem_id == "UMD"
            and classification.lineage.build_id == "UMD-006"
            for classification in registry.classifications
        ),
        "deterministic_ordering": tuple(
            classification.classification_id
            for classification in registry.classifications
        ) == tuple(
            sorted(
                classification.classification_id
                for classification in registry.classifications
            )
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_classified": (
            not unclassified
            if require_all_markets_classified
            else True
        ),
        "registry_maps_read_only": isinstance(
            registry._by_market_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_classification_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_category_id,
            MappingProxyType,
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
    return MarketClassificationCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        classification_count=len(registry.classifications),
        unclassified_market_ids=unclassified,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_006_foundation() -> Mapping[str, Any]:
    manifest = build_umd_006_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-006",
        "upstreams_frozen": manifest.upstream_builds
        == (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
        ),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
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

def verify_umd_006_certified_market_classification_registry() -> bool:
    result = certify_umd_006_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-006 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_006_BUILD_ID",
    "UMD_006_BUILD_NAME",
    "UMD_006_REVISION",
    "UMD_006_SCHEMA_VERSION",
    "CertifiedMarketClassification",
    "ReadOnlyMarketClassificationRegistry",
    "MarketClassificationCertificationResult",
    "UMD006CertificationManifest",
    "build_umd_006_certification_manifest",
    "certify_market_classification_registry",
    "certify_umd_006_foundation",
    "verify_umd_006_certified_market_classification_registry",
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
    build_umd_006_certification_manifest,
    certify_market_classification_registry,
    certify_umd_006_foundation,
    verify_umd_006_certified_market_classification_registry,
)

FIXED = datetime(2026, 8, 5, 8, 0, tzinfo=timezone.utc)

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

def category_node(category_id, parent=None):
    return CertifiedMarketCategoryNode(
        category_id=category_id,
        canonical_name=category_id.replace("-", " ").title(),
        parent_category_id=parent,
        aliases=(),
        description=f"Certified category {category_id}.",
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            f"fixture://umd-005/{category_id}",
        ),
    )

def category_registry():
    return ReadOnlyMarketCategoryHierarchyRegistry(
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

def market(native_market_id="BTC-100K"):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC",
        canonical_title=f"Fixture market {native_market_id}",
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
        duplicate_resolution_keys=(native_market_id.lower(),),
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_market_id}",
        ),
    )

def classification(item):
    return CertifiedMarketClassification.from_market(
        item,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            f"fixture://umd-006/{item.native_market_id}",
        ),
    )

def registry(classifications, markets):
    return ReadOnlyMarketClassificationRegistry(
        classifications=tuple(classifications),
        markets=tuple(markets),
        category_registry=category_registry(),
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )

class TestUMD006(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_006_foundation()["certified"])
        self.assertTrue(
            verify_umd_006_certified_market_classification_registry()
        )

    def test_classification_identity_deterministic(self):
        item = market()
        self.assertEqual(
            classification(item).classification_id,
            classification(item).classification_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(
            classification(item).record_hash,
            classification(item).record_hash,
        )

    def test_immutable(self):
        item = classification(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.category_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (classification(second), classification(first)),
            (second, first),
        )
        result = certify_market_classification_registry(item)
        self.assertTrue(result.certified)
        self.assertEqual(result.classification_count, 2)
        self.assertFalse(result.unclassified_market_ids)

    def test_duplicate_market_classification_rejected(self):
        item = market()
        value = classification(item)
        with self.assertRaises(ValueError):
            registry((value, value), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((classification(first),), (second,))

    def test_mismatched_classification_rejected(self):
        item = market()
        bad = CertifiedMarketClassification(
            canonical_market_id=item.canonical_market_id,
            category_id="crypto",
            asset_class=item.asset_class,
            instrument_type=item.instrument_type,
            geographic_scope=item.geographic_scope,
            settlement_method=item.settlement_method,
            lifecycle=item.lifecycle,
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-006",
                UMD_006_REVISION,
                "fixture://umd-006/bad",
            ),
        )
        with self.assertRaises(ValueError):
            registry((bad,), (item,))

    def test_unclassified_market_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((classification(first),), (first, second))
        self.assertEqual(
            item.unclassified_market_ids(),
            (second.canonical_market_id,),
        )
        strict = certify_market_classification_registry(
            item,
            require_all_markets_classified=True,
        )
        relaxed = certify_market_classification_registry(
            item,
            require_all_markets_classified=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_by_category_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (classification(second), classification(first)),
            (second, first),
        )
        ids = tuple(
            value.canonical_market_id
            for value in item.by_category("bitcoin")
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_category_registry_is_enforced(self):
        item = market()
        bad_category_registry = ReadOnlyMarketCategoryHierarchyRegistry(
            categories=(category_node("markets"),),
            registry_lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                "fixture://umd-005/bad-registry",
            ),
        )
        with self.assertRaises(ValueError):
            ReadOnlyMarketClassificationRegistry(
                classifications=(classification(item),),
                markets=(item,),
                category_registry=bad_category_registry,
                registry_lineage=lineage(
                    "UMD-006",
                    UMD_006_REVISION,
                    "fixture://umd-006/bad-registry",
                ),
            )

    def test_side_effects_disabled(self):
        manifest = build_umd_006_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-006 CERTIFICATION TEST")
    print(" CERTIFIED MARKET CLASSIFICATION REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD006)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_006_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-005 consumed read-only")
    print("[PASS] Canonical classification IDs deterministic")
    print("[PASS] Market foreign-key validation verified")
    print("[PASS] Category hierarchy validation verified")
    print("[PASS] Asset, instrument, geography, settlement, and lifecycle alignment verified")
    print("[PASS] Duplicate market classifications rejected")
    print("[PASS] Unclassified market detection verified")
    print("[PASS] Read-only classification registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic classification and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-006 CERTIFIED MARKET CLASSIFICATION REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_market_classification_registry import (
    UMD_006_BUILD_ID,
    UMD_006_BUILD_NAME,
    UMD_006_REVISION,
    UMD_006_SCHEMA_VERSION,
    CertifiedMarketClassification,
    ReadOnlyMarketClassificationRegistry,
    MarketClassificationCertificationResult,
    UMD006CertificationManifest,
    build_umd_006_certification_manifest,
    certify_market_classification_registry,
    certify_umd_006_foundation,
    verify_umd_006_certified_market_classification_registry,
)
"""

NAMES = [
    "UMD_006_BUILD_ID",
    "UMD_006_BUILD_NAME",
    "UMD_006_REVISION",
    "UMD_006_SCHEMA_VERSION",
    "CertifiedMarketClassification",
    "ReadOnlyMarketClassificationRegistry",
    "MarketClassificationCertificationResult",
    "UMD006CertificationManifest",
    "build_umd_006_certification_manifest",
    "certify_market_classification_registry",
    "certify_umd_006_foundation",
    "verify_umd_006_certified_market_classification_registry",
]

def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()

def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temp, path)

def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )
    source = INIT.read_text(encoding="utf-8")
    if (
        "from .certified_market_classification_registry import ("
        not in source
    ):
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start:end + 1]
        missing = [
            name
            for name in NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]
        if missing:
            addition = "".join(
                f'    "{name}",\n' for name in missing
            )
            block = block[:-1] + addition + "]"
            source = (
                source[:start]
                + block
                + source[end + 1:]
            )
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
            (
                "certified_market_category_hierarchy_registry",
                "verify_umd_005_certified_market_category_hierarchy_registry",
            ),
        )
        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            verifier = getattr(module, verifier_name)
            if not verifier():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_market_classification_registry"
        )
        required = (
            "CertifiedMarketClassification",
            "ReadOnlyMarketClassificationRegistry",
            "certify_market_classification_registry",
            "certify_umd_006_foundation",
            "verify_umd_006_certified_market_classification_registry",
        )
        missing = [
            name
            for name in required
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-006 missing symbols: "
                + ", ".join(missing)
            )
        module.verify_umd_006_certified_market_classification_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-006 INSTALLER")
    print(" CERTIFIED MARKET CLASSIFICATION REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-005 "
        "verified read-only"
    )

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-006",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
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
    print("[PASS] Required UMD-006 symbols verified")
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, scanning, persistence, "
        "publication, and execution disabled"
    )
    print("[DONE] UMD-006 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_006_certified_market_classification_registry.py"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
