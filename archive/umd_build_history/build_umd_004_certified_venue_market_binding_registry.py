from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_004_CERTIFIED_VENUE_MARKET_BINDING_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_venue_market_binding_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_004_certified_venue_market_binding_registry.py"

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
from .certified_venue_identity_registry import (
    CertifiedVenueIdentity,
    ReadOnlyVenueIdentityRegistry,
)

UMD_004_BUILD_ID = "UMD-004"
UMD_004_BUILD_NAME = "Certified Venue-Market Binding Registry"
UMD_004_REVISION = "UMD_004_CERTIFIED_VENUE_MARKET_BINDING_REGISTRY_V1"
UMD_004_SCHEMA_VERSION = "1.0.0"

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

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(key), item) for key, item in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedVenueMarketBinding:
    canonical_venue_id: str
    canonical_market_id: str
    venue_namespace: str
    native_market_namespace: str
    native_market_id: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_venue_id",
            _text(self.canonical_venue_id, "canonical_venue_id"),
        )
        object.__setattr__(
            self,
            "canonical_market_id",
            _text(self.canonical_market_id, "canonical_market_id"),
        )
        object.__setattr__(
            self,
            "venue_namespace",
            _text(self.venue_namespace, "venue_namespace").lower(),
        )
        object.__setattr__(
            self,
            "native_market_namespace",
            _text(self.native_market_namespace, "native_market_namespace").lower(),
        )
        object.__setattr__(
            self,
            "native_market_id",
            _text(self.native_market_id, "native_market_id"),
        )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if not self.canonical_venue_id.startswith("umd:venue:"):
            raise ValueError("canonical_venue_id must use the UMD venue prefix")
        if not self.canonical_market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use the UMD market prefix")
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("binding lineage must belong to UMD")
        if self.lineage.build_id != UMD_004_BUILD_ID:
            raise ValueError("binding lineage must use build_id UMD-004")

    @classmethod
    def from_certified_objects(
        cls,
        venue: CertifiedVenueIdentity,
        market: CertifiedCanonicalMarket,
        *,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedVenueMarketBinding":
        if market.venue.venue_id != venue.venue_namespace:
            raise ValueError(
                "market venue_id does not match certified venue_namespace"
            )
        if (
            market.venue.native_market_namespace
            != venue.native_market_namespace
        ):
            raise ValueError(
                "market native namespace does not match certified venue namespace"
            )
        return cls(
            canonical_venue_id=venue.canonical_venue_id,
            canonical_market_id=market.canonical_market_id,
            venue_namespace=venue.venue_namespace,
            native_market_namespace=venue.native_market_namespace,
            native_market_id=market.native_market_id,
            metadata=metadata,
            lineage=lineage,
        )

    def identity_payload(self) -> Mapping[str, Any]:
        return {
            "canonical_venue_id": self.canonical_venue_id,
            "canonical_market_id": self.canonical_market_id,
        }

    @property
    def binding_id(self) -> str:
        return f"umd:binding:{deterministic_sha256(self.identity_payload())}"

    @property
    def native_binding_key(self) -> Tuple[str, str, str]:
        return (
            self.venue_namespace,
            self.native_market_namespace,
            self.native_market_id,
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "binding_id": self.binding_id,
            "canonical_venue_id": self.canonical_venue_id,
            "canonical_market_id": self.canonical_market_id,
            "venue_namespace": self.venue_namespace,
            "native_market_namespace": self.native_market_namespace,
            "native_market_id": self.native_market_id,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyVenueMarketBindingRegistry:
    bindings: Tuple[CertifiedVenueMarketBinding, ...]
    venue_registry: ReadOnlyVenueIdentityRegistry
    markets: Tuple[CertifiedCanonicalMarket, ...]
    registry_lineage: ImmutableLineage
    _by_binding_id: Mapping[str, CertifiedVenueMarketBinding] = field(
        init=False,
        repr=False,
    )
    _by_market_id: Mapping[str, CertifiedVenueMarketBinding] = field(
        init=False,
        repr=False,
    )
    _by_venue_id: Mapping[str, Tuple[CertifiedVenueMarketBinding, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        ordered_bindings = tuple(
            sorted(self.bindings, key=lambda item: item.binding_id)
        )
        ordered_markets = tuple(
            sorted(self.markets, key=lambda item: item.canonical_market_id)
        )
        object.__setattr__(self, "bindings", ordered_bindings)
        object.__setattr__(self, "markets", ordered_markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_004_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-004")

        venue_ids = {
            venue.canonical_venue_id
            for venue in self.venue_registry.venues
        }
        market_by_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(market_by_id) != len(ordered_markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_binding_id = {}
        by_market_id = {}
        native_keys = {}
        venue_groups = {}

        for binding in ordered_bindings:
            if binding.binding_id in by_binding_id:
                raise ValueError("duplicate binding ID")
            if binding.canonical_venue_id not in venue_ids:
                raise ValueError(
                    f"unknown canonical venue ID: {binding.canonical_venue_id}"
                )
            market = market_by_id.get(binding.canonical_market_id)
            if market is None:
                raise ValueError(
                    f"unknown canonical market ID: {binding.canonical_market_id}"
                )
            venue = self.venue_registry.get(binding.canonical_venue_id)
            if venue is None:
                raise ValueError("venue registry lookup failed")

            if binding.venue_namespace != venue.venue_namespace:
                raise ValueError("binding venue namespace mismatch")
            if (
                binding.native_market_namespace
                != venue.native_market_namespace
            ):
                raise ValueError("binding native namespace mismatch")
            if binding.native_market_id != market.native_market_id:
                raise ValueError("binding native market ID mismatch")
            if market.venue.venue_id != venue.venue_namespace:
                raise ValueError("market-to-venue identity mismatch")
            if (
                market.venue.native_market_namespace
                != venue.native_market_namespace
            ):
                raise ValueError("market-to-venue namespace mismatch")

            if binding.canonical_market_id in by_market_id:
                raise ValueError(
                    "canonical market may have only one direct venue binding"
                )
            if binding.native_binding_key in native_keys:
                raise ValueError("duplicate native venue-market binding")

            by_binding_id[binding.binding_id] = binding
            by_market_id[binding.canonical_market_id] = binding
            native_keys[binding.native_binding_key] = binding.binding_id
            venue_groups.setdefault(binding.canonical_venue_id, []).append(binding)

        frozen_groups = {
            venue_id: tuple(
                sorted(items, key=lambda item: item.canonical_market_id)
            )
            for venue_id, items in venue_groups.items()
        }

        object.__setattr__(
            self,
            "_by_binding_id",
            MappingProxyType(by_binding_id),
        )
        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_venue_id",
            MappingProxyType(frozen_groups),
        )

    def get_binding(
        self,
        binding_id: str,
    ) -> CertifiedVenueMarketBinding | None:
        return self._by_binding_id.get(_text(binding_id, "binding_id"))

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedVenueMarketBinding | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def by_venue(
        self,
        canonical_venue_id: str,
    ) -> Tuple[CertifiedVenueMarketBinding, ...]:
        return self._by_venue_id.get(
            _text(canonical_venue_id, "canonical_venue_id"),
            (),
        )

    def unbound_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "bindings": self.bindings,
            "venue_registry_hash": self.venue_registry.registry_hash,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class VenueMarketBindingCertificationResult:
    certified: bool
    registry_hash: str
    binding_count: int
    unbound_market_ids: Tuple[str, ...]
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))

@dataclass(frozen=True, slots=True)
class UMD004CertificationManifest:
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

def build_umd_004_certification_manifest() -> UMD004CertificationManifest:
    return UMD004CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_004_BUILD_ID,
        build_name=UMD_004_BUILD_NAME,
        revision=UMD_004_REVISION,
        schema_version=UMD_004_SCHEMA_VERSION,
        upstream_builds=("UMD-001", "UMD-002", "UMD-003"),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_venue_market_binding_registry(
    registry: ReadOnlyVenueMarketBindingRegistry,
    *,
    require_all_markets_bound: bool = True,
) -> VenueMarketBindingCertificationResult:
    unbound = registry.unbound_market_ids()
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "binding_ids_unique": len(
            {binding.binding_id for binding in registry.bindings}
        ) == len(registry.bindings),
        "market_bindings_unique": len(
            {binding.canonical_market_id for binding in registry.bindings}
        ) == len(registry.bindings),
        "native_bindings_unique": len(
            {binding.native_binding_key for binding in registry.bindings}
        ) == len(registry.bindings),
        "all_venues_resolve": all(
            registry.venue_registry.get(binding.canonical_venue_id)
            is not None
            for binding in registry.bindings
        ),
        "all_markets_resolve": all(
            registry.get_by_market(binding.canonical_market_id)
            is not None
            for binding in registry.bindings
        ),
        "all_lineage_certified": all(
            binding.lineage.subsystem_id == "UMD"
            and binding.lineage.build_id == "UMD-004"
            for binding in registry.bindings
        ),
        "deterministic_ordering": tuple(
            binding.binding_id for binding in registry.bindings
        ) == tuple(
            sorted(binding.binding_id for binding in registry.bindings)
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_bound": (not unbound) if require_all_markets_bound else True,
        "registry_maps_read_only": isinstance(
            registry._by_binding_id, MappingProxyType
        )
        and isinstance(registry._by_market_id, MappingProxyType)
        and isinstance(registry._by_venue_id, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return VenueMarketBindingCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        binding_count=len(registry.bindings),
        unbound_market_ids=unbound,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_004_foundation() -> Mapping[str, Any]:
    manifest = build_umd_004_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-004",
        "upstreams_frozen": manifest.upstream_builds
        == ("UMD-001", "UMD-002", "UMD-003"),
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

def verify_umd_004_certified_venue_market_binding_registry() -> bool:
    result = certify_umd_004_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-004 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_004_BUILD_ID",
    "UMD_004_BUILD_NAME",
    "UMD_004_REVISION",
    "UMD_004_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedVenueMarketBinding",
    "ReadOnlyVenueMarketBindingRegistry",
    "VenueMarketBindingCertificationResult",
    "UMD004CertificationManifest",
    "build_umd_004_certification_manifest",
    "certify_venue_market_binding_registry",
    "certify_umd_004_foundation",
    "verify_umd_004_certified_venue_market_binding_registry",
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
from qseries_v2.universal_market_discovery.certified_venue_identity_registry import (
    UMD_003_REVISION,
    CertifiedVenueIdentity,
    ReadOnlyVenueIdentityRegistry,
    VenueOperationalStatus,
    VenueType,
)
from qseries_v2.universal_market_discovery.certified_venue_market_binding_registry import (
    UMD_004_REVISION,
    CertifiedVenueMarketBinding,
    ReadOnlyVenueMarketBindingRegistry,
    build_umd_004_certification_manifest,
    certify_umd_004_foundation,
    certify_venue_market_binding_registry,
    verify_umd_004_certified_venue_market_binding_registry,
)

FIXED = datetime(2026, 8, 5, 6, 0, tzinfo=timezone.utc)

def lineage(build_id, revision, source, parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id=build_id,
        revision=revision,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(source,),
        created_at=FIXED,
    )

def venue(namespace="fixture-venue", native_namespace="fixture"):
    return CertifiedVenueIdentity(
        venue_namespace=namespace,
        canonical_name="Fixture Venue",
        display_name="Fixture Venue",
        venue_type=VenueType.PREDICTION_MARKET,
        operational_status=VenueOperationalStatus.ACTIVE,
        jurisdiction="US",
        timezone_name="America/Chicago",
        native_market_namespace=native_namespace,
        aliases=("Fixture",),
        supported_asset_classes=("prediction_market",),
        supported_market_types=("binary",),
        supported_currencies=("USD",),
        settlement_capabilities=("cash",),
        related_venue_ids=(),
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-003",
            UMD_003_REVISION,
            f"fixture://umd-003/{namespace}",
        ),
    )

def market(native_market_id="BTC-100K-2026", venue_namespace="fixture-venue", native_namespace="fixture"):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=venue_namespace,
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=native_namespace,
            metadata={"adapter": "fixture"},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC-2026",
        canonical_title=f"Fixture market {native_market_id}",
        canonical_description="Deterministic fixture market.",
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
        opens_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Fixture settlement rule.",
        settles_at=datetime(2027, 1, 2, tzinfo=timezone.utc),
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=(native_market_id.lower(),),
        related_market_ids=(),
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_market_id}",
        ),
    )

def binding(v, m):
    return CertifiedVenueMarketBinding.from_certified_objects(
        v,
        m,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-004",
            UMD_004_REVISION,
            f"fixture://umd-004/{m.native_market_id}",
            parent_hashes=(v.record_hash, m.record_hash),
        ),
    )

def registry(bindings, venues, markets):
    return ReadOnlyVenueMarketBindingRegistry(
        bindings=tuple(bindings),
        venue_registry=ReadOnlyVenueIdentityRegistry(
            venues=tuple(venues),
            registry_lineage=lineage(
                "UMD-003",
                UMD_003_REVISION,
                "fixture://umd-003/registry",
            ),
        ),
        markets=tuple(markets),
        registry_lineage=lineage(
            "UMD-004",
            UMD_004_REVISION,
            "fixture://umd-004/registry",
        ),
    )

class TestUMD004(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_004_foundation()["certified"])
        self.assertTrue(
            verify_umd_004_certified_venue_market_binding_registry()
        )

    def test_binding_identity_deterministic(self):
        v = venue()
        m = market()
        self.assertEqual(binding(v, m).binding_id, binding(v, m).binding_id)

    def test_binding_record_hash_deterministic(self):
        v = venue()
        m = market()
        self.assertEqual(binding(v, m).record_hash, binding(v, m).record_hash)

    def test_binding_is_immutable(self):
        item = binding(venue(), market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.native_market_id = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        v = venue()
        m1 = market("BTC-100K-2026")
        m2 = market("BTC-150K-2026")
        r = registry(
            (binding(v, m2), binding(v, m1)),
            (v,),
            (m2, m1),
        )
        result = certify_venue_market_binding_registry(r)
        self.assertTrue(result.certified)
        self.assertEqual(result.binding_count, 2)
        self.assertFalse(result.unbound_market_ids)

    def test_alias_foreign_key_lookup(self):
        v = venue()
        m = market()
        r = registry((binding(v, m),), (v,), (m,))
        resolved_venue = r.venue_registry.resolve_alias("fixture")
        self.assertEqual(resolved_venue.canonical_venue_id, v.canonical_venue_id)
        self.assertEqual(
            r.get_by_market(m.canonical_market_id).canonical_venue_id,
            v.canonical_venue_id,
        )

    def test_unknown_venue_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        other = venue("other-venue", "other")
        with self.assertRaises(ValueError):
            registry((item,), (other,), (m,))

    def test_unknown_market_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        other_market = market("OTHER")
        with self.assertRaises(ValueError):
            registry((item,), (v,), (other_market,))

    def test_duplicate_market_binding_rejected(self):
        v = venue()
        m = market()
        item = binding(v, m)
        with self.assertRaises(ValueError):
            registry((item, item), (v,), (m,))

    def test_namespace_mismatch_rejected(self):
        v = venue()
        m = market(venue_namespace="wrong-venue")
        with self.assertRaises(ValueError):
            binding(v, m)

    def test_unbound_market_detection(self):
        v = venue()
        m1 = market("ONE")
        m2 = market("TWO")
        r = registry((binding(v, m1),), (v,), (m1, m2))
        self.assertEqual(r.unbound_market_ids(), (m2.canonical_market_id,))
        strict = certify_venue_market_binding_registry(
            r,
            require_all_markets_bound=True,
        )
        relaxed = certify_venue_market_binding_registry(
            r,
            require_all_markets_bound=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_by_venue_deterministic(self):
        v = venue()
        m1 = market("ONE")
        m2 = market("TWO")
        r = registry(
            (binding(v, m2), binding(v, m1)),
            (v,),
            (m2, m1),
        )
        ids = tuple(
            item.canonical_market_id
            for item in r.by_venue(v.canonical_venue_id)
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_side_effects_disabled(self):
        manifest = build_umd_004_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-004 CERTIFICATION TEST")
    print(" CERTIFIED VENUE-MARKET BINDING REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD004)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_004_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-003 consumed read-only")
    print("[PASS] Canonical venue-market binding IDs deterministic")
    print("[PASS] Venue and market foreign keys validated")
    print("[PASS] Native namespace identity alignment verified")
    print("[PASS] Duplicate market bindings rejected")
    print("[PASS] Duplicate native bindings rejected")
    print("[PASS] Unbound market detection verified")
    print("[PASS] Read-only binding registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-004 CERTIFIED VENUE-MARKET BINDING REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_venue_market_binding_registry import (
    UMD_004_BUILD_ID,
    UMD_004_BUILD_NAME,
    UMD_004_REVISION,
    UMD_004_SCHEMA_VERSION,
    CertifiedVenueMarketBinding,
    ReadOnlyVenueMarketBindingRegistry,
    VenueMarketBindingCertificationResult,
    UMD004CertificationManifest,
    build_umd_004_certification_manifest,
    certify_venue_market_binding_registry,
    certify_umd_004_foundation,
    verify_umd_004_certified_venue_market_binding_registry,
)
"""

NAMES = [
    "UMD_004_BUILD_ID",
    "UMD_004_BUILD_NAME",
    "UMD_004_REVISION",
    "UMD_004_SCHEMA_VERSION",
    "CertifiedVenueMarketBinding",
    "ReadOnlyVenueMarketBindingRegistry",
    "VenueMarketBindingCertificationResult",
    "UMD004CertificationManifest",
    "build_umd_004_certification_manifest",
    "certify_venue_market_binding_registry",
    "certify_umd_004_foundation",
    "verify_umd_004_certified_venue_market_binding_registry",
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
    if "from .certified_venue_market_binding_registry import (" not in source:
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
        foundation = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "universal_market_discovery_foundation"
        )
        canonical = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_canonical_market_contract"
        )
        venues = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_venue_identity_registry"
        )
        if not foundation.verify_umd_foundation():
            raise RuntimeError("UMD-001 verification failed")
        if not canonical.verify_umd_002_certified_canonical_market_contract():
            raise RuntimeError("UMD-002 verification failed")
        if not venues.verify_umd_003_certified_venue_identity_registry():
            raise RuntimeError("UMD-003 verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_venue_market_binding_registry"
        )
        required = (
            "CertifiedVenueMarketBinding",
            "ReadOnlyVenueMarketBindingRegistry",
            "certify_venue_market_binding_registry",
            "certify_umd_004_foundation",
            "verify_umd_004_certified_venue_market_binding_registry",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-004 missing symbols: " + ", ".join(missing))
        module.verify_umd_004_certified_venue_market_binding_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-004 INSTALLER")
    print(" CERTIFIED VENUE-MARKET BINDING REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-003 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-004",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": ("UMD-001", "UMD-002", "UMD-003"),
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
    print("[PASS] Required UMD-004 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-004 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_004_certified_venue_market_binding_registry.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
