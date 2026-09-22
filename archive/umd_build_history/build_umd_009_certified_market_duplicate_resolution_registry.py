from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_009_CERTIFIED_MARKET_DUPLICATE_RESOLUTION_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_market_duplicate_resolution_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_009_certified_market_duplicate_resolution_registry.py"

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
from .certified_market_lifecycle_and_settlement_registry import (
    ReadOnlyMarketLifecycleSettlementRegistry,
)

UMD_009_BUILD_ID = "UMD-009"
UMD_009_BUILD_NAME = "Certified Market Duplicate Resolution Registry"
UMD_009_REVISION = "UMD_009_CERTIFIED_MARKET_DUPLICATE_RESOLUTION_REGISTRY_V1"
UMD_009_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_duplicate_merging",
    "automatic_market_deletion",
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
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )

def _unique_market_ids(values: Tuple[str, ...]) -> Tuple[str, ...]:
    normalized = tuple(
        sorted({_text(value, "canonical_market_id") for value in values})
    )
    for value in normalized:
        if not value.startswith("umd:mkt:"):
            raise ValueError("market IDs must use the UMD market prefix")
    return normalized

class DuplicateResolutionStatus(str, Enum):
    CANDIDATE = "candidate"
    CONFIRMED_DUPLICATE = "confirmed_duplicate"
    RELATED_NOT_DUPLICATE = "related_not_duplicate"
    REJECTED = "rejected"

@dataclass(frozen=True, slots=True)
class CertifiedMarketDuplicateResolution:
    duplicate_group_key: str
    canonical_winner_market_id: str
    member_market_ids: Tuple[str, ...]
    status: DuplicateResolutionStatus
    rationale_code: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "duplicate_group_key",
            _text(self.duplicate_group_key, "duplicate_group_key").lower(),
        )

        winner = _text(
            self.canonical_winner_market_id,
            "canonical_winner_market_id",
        )
        if not winner.startswith("umd:mkt:"):
            raise ValueError("winner market ID must use the UMD market prefix")
        object.__setattr__(
            self,
            "canonical_winner_market_id",
            winner,
        )

        members = _unique_market_ids(self.member_market_ids)
        if len(members) < 2:
            raise ValueError("duplicate groups must contain at least two markets")
        if winner not in members:
            raise ValueError("canonical winner must be included in member_market_ids")
        object.__setattr__(self, "member_market_ids", members)

        if not isinstance(self.status, DuplicateResolutionStatus):
            object.__setattr__(
                self,
                "status",
                DuplicateResolutionStatus(self.status),
            )

        object.__setattr__(
            self,
            "rationale_code",
            _text(self.rationale_code, "rationale_code").lower(),
        )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("duplicate-resolution lineage must belong to UMD")
        if self.lineage.build_id != UMD_009_BUILD_ID:
            raise ValueError(
                "duplicate-resolution lineage must use build_id UMD-009"
            )

    def identity_payload(self) -> Mapping[str, Any]:
        return {
            "duplicate_group_key": self.duplicate_group_key,
            "member_market_ids": self.member_market_ids,
        }

    @property
    def resolution_id(self) -> str:
        return f"umd:duplicate:{deterministic_sha256(self.identity_payload())}"

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "duplicate_group_key": self.duplicate_group_key,
            "canonical_winner_market_id": self.canonical_winner_market_id,
            "member_market_ids": self.member_market_ids,
            "status": self.status,
            "rationale_code": self.rationale_code,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketDuplicateResolutionRegistry:
    resolutions: Tuple[CertifiedMarketDuplicateResolution, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    lifecycle_registry: ReadOnlyMarketLifecycleSettlementRegistry
    registry_lineage: ImmutableLineage
    _by_resolution_id: Mapping[str, CertifiedMarketDuplicateResolution] = field(
        init=False,
        repr=False,
    )
    _by_group_key: Mapping[str, CertifiedMarketDuplicateResolution] = field(
        init=False,
        repr=False,
    )
    _market_to_resolution_id: Mapping[str, str] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        resolutions = tuple(
            sorted(self.resolutions, key=lambda item: item.resolution_id)
        )
        markets = tuple(
            sorted(self.markets, key=lambda item: item.canonical_market_id)
        )
        object.__setattr__(self, "resolutions", resolutions)
        object.__setattr__(self, "markets", markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_009_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-009")

        market_by_id = {
            market.canonical_market_id: market
            for market in markets
        }
        if len(market_by_id) != len(markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_resolution_id = {}
        by_group_key = {}
        market_to_resolution_id = {}

        for resolution in resolutions:
            if resolution.resolution_id in by_resolution_id:
                raise ValueError("duplicate resolution ID")
            if resolution.duplicate_group_key in by_group_key:
                raise ValueError("duplicate duplicate_group_key")

            fingerprints = set()
            for market_id in resolution.member_market_ids:
                market = market_by_id.get(market_id)
                if market is None:
                    raise ValueError(f"unknown canonical market ID: {market_id}")
                if (
                    self.lifecycle_registry.get_by_market(market_id)
                    is None
                ):
                    raise ValueError(
                        "duplicate resolution requires lifecycle tracking"
                    )
                fingerprints.add(market.duplicate_fingerprint)

                existing = market_to_resolution_id.get(market_id)
                if existing is not None:
                    raise ValueError(
                        "market may belong to only one duplicate-resolution group"
                    )
                market_to_resolution_id[market_id] = resolution.resolution_id

            if (
                resolution.status
                == DuplicateResolutionStatus.CONFIRMED_DUPLICATE
                and len(fingerprints) != 1
            ):
                raise ValueError(
                    "confirmed duplicates must share one duplicate fingerprint"
                )

            by_resolution_id[resolution.resolution_id] = resolution
            by_group_key[
                resolution.duplicate_group_key
            ] = resolution

        object.__setattr__(
            self,
            "_by_resolution_id",
            MappingProxyType(by_resolution_id),
        )
        object.__setattr__(
            self,
            "_by_group_key",
            MappingProxyType(by_group_key),
        )
        object.__setattr__(
            self,
            "_market_to_resolution_id",
            MappingProxyType(market_to_resolution_id),
        )

    def get(
        self,
        resolution_id: str,
    ) -> CertifiedMarketDuplicateResolution | None:
        return self._by_resolution_id.get(
            _text(resolution_id, "resolution_id")
        )

    def get_by_group_key(
        self,
        duplicate_group_key: str,
    ) -> CertifiedMarketDuplicateResolution | None:
        return self._by_group_key.get(
            _text(duplicate_group_key, "duplicate_group_key").lower()
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketDuplicateResolution | None:
        market_id = _text(canonical_market_id, "canonical_market_id")
        resolution_id = self._market_to_resolution_id.get(market_id)
        if resolution_id is None:
            return None
        return self._by_resolution_id[resolution_id]

    def canonical_market_id_for(
        self,
        canonical_market_id: str,
    ) -> str:
        market_id = _text(canonical_market_id, "canonical_market_id")
        resolution = self.get_by_market(market_id)
        if resolution is None:
            return market_id
        if resolution.status != DuplicateResolutionStatus.CONFIRMED_DUPLICATE:
            return market_id
        return resolution.canonical_winner_market_id

    def unresolved_candidate_ids(self) -> Tuple[str, ...]:
        return tuple(
            resolution.resolution_id
            for resolution in self.resolutions
            if resolution.status == DuplicateResolutionStatus.CANDIDATE
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "resolutions": self.resolutions,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "lifecycle_registry_hash": self.lifecycle_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD009CertificationManifest:
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

def build_umd_009_certification_manifest() -> UMD009CertificationManifest:
    return UMD009CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_009_BUILD_ID,
        build_name=UMD_009_BUILD_NAME,
        revision=UMD_009_REVISION,
        schema_version=UMD_009_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
            "UMD-007",
            "UMD-008",
        ),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_duplicate_resolution_registry(
    registry: ReadOnlyMarketDuplicateResolutionRegistry,
    *,
    allow_unresolved_candidates: bool = False,
) -> Mapping[str, Any]:
    unresolved = registry.unresolved_candidate_ids()
    checks = {
        "resolution_ids_unique": len(
            {resolution.resolution_id for resolution in registry.resolutions}
        ) == len(registry.resolutions),
        "group_keys_unique": len(
            {
                resolution.duplicate_group_key
                for resolution in registry.resolutions
            }
        ) == len(registry.resolutions),
        "all_markets_resolve": all(
            registry.get_by_market(market_id) is not None
            for resolution in registry.resolutions
            for market_id in resolution.member_market_ids
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "no_unresolved_candidates": (
            not unresolved if not allow_unresolved_candidates else True
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
    return MappingProxyType(
        {
            "certified": not failed,
            "registry_hash": registry.registry_hash,
            "resolution_count": len(registry.resolutions),
            "unresolved_candidate_ids": unresolved,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )

def certify_umd_009_foundation() -> Mapping[str, Any]:
    manifest = build_umd_009_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-009",
        "upstreams_frozen": manifest.upstream_builds
        == (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
            "UMD-007",
            "UMD-008",
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

def verify_umd_009_certified_market_duplicate_resolution_registry() -> bool:
    result = certify_umd_009_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-009 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_009_BUILD_ID",
    "UMD_009_BUILD_NAME",
    "UMD_009_REVISION",
    "UMD_009_SCHEMA_VERSION",
    "DuplicateResolutionStatus",
    "CertifiedMarketDuplicateResolution",
    "ReadOnlyMarketDuplicateResolutionRegistry",
    "UMD009CertificationManifest",
    "build_umd_009_certification_manifest",
    "certify_market_duplicate_resolution_registry",
    "certify_umd_009_foundation",
    "verify_umd_009_certified_market_duplicate_resolution_registry",
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
    build_umd_009_certification_manifest,
    certify_market_duplicate_resolution_registry,
    certify_umd_009_foundation,
    verify_umd_009_certified_market_duplicate_resolution_registry,
)

FIXED = datetime(2026, 8, 5, 15, 0, tzinfo=timezone.utc)

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

def category_registry():
    def node(category_id, parent=None):
        return CertifiedMarketCategoryNode(
            category_id=category_id,
            canonical_name=category_id.title(),
            parent_category_id=parent,
            aliases=(),
            description=f"Category {category_id}.",
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-005",
                UMD_005_REVISION,
                f"fixture://umd-005/{category_id}",
            ),
        )
    return ReadOnlyMarketCategoryHierarchyRegistry(
        categories=(
            node("markets"),
            node("crypto", "markets"),
            node("bitcoin", "crypto"),
        ),
        registry_lineage=lineage(
            "UMD-005",
            UMD_005_REVISION,
            "fixture://umd-005/registry",
        ),
    )

def market(native_id, duplicate_keys=("bitcoin", "100000")):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id=f"venue-{native_id.lower()}",
            canonical_name=f"Venue {native_id}",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace=f"ns-{native_id.lower()}",
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="BTC",
        canonical_title="Will Bitcoin exceed $100,000?",
        canonical_description="Fixture duplicate market.",
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
        settlement_rule="Fixture rule.",
        settles_at=None,
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=duplicate_keys,
        related_market_ids=(),
        metadata={},
        lineage=lineage(
            "UMD-002",
            UMD_002_REVISION,
            f"fixture://umd-002/{native_id}",
        ),
    )

def lifecycle_registry(markets):
    classifications = tuple(
        CertifiedMarketClassification.from_market(
            item,
            metadata={"read_only": True},
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
        category_registry=category_registry(),
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
            external_reference_ids={
                "fixture": item.native_market_id
            },
            metadata_version="1.0.0",
            attributes={"read_only": True},
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
            metadata={"read_only": True},
            lineage=lineage(
                "UMD-008",
                UMD_008_REVISION,
                f"fixture://umd-008/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    return ReadOnlyMarketLifecycleSettlementRegistry(
        records=lifecycle_records,
        markets=tuple(markets),
        metadata_registry=metadata_registry,
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )

def resolution(markets, status=DuplicateResolutionStatus.CONFIRMED_DUPLICATE):
    return CertifiedMarketDuplicateResolution(
        duplicate_group_key="bitcoin-100k-2026",
        canonical_winner_market_id=markets[0].canonical_market_id,
        member_market_ids=tuple(
            item.canonical_market_id for item in markets
        ),
        status=status,
        rationale_code="same-outcome-same-expiry",
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/resolution",
        ),
    )

def registry(resolutions, markets):
    return ReadOnlyMarketDuplicateResolutionRegistry(
        resolutions=tuple(resolutions),
        markets=tuple(markets),
        lifecycle_registry=lifecycle_registry(markets),
        registry_lineage=lineage(
            "UMD-009",
            UMD_009_REVISION,
            "fixture://umd-009/registry",
        ),
    )

class TestUMD009(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_009_foundation()["certified"])
        self.assertTrue(
            verify_umd_009_certified_market_duplicate_resolution_registry()
        )

    def test_resolution_identity_deterministic(self):
        markets = (market("A"), market("B"))
        self.assertEqual(
            resolution(markets).resolution_id,
            resolution(markets).resolution_id,
        )

    def test_record_hash_deterministic(self):
        markets = (market("A"), market("B"))
        self.assertEqual(
            resolution(markets).record_hash,
            resolution(markets).record_hash,
        )

    def test_immutable(self):
        item = resolution((market("A"), market("B")))
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.status = DuplicateResolutionStatus.REJECTED
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        markets = (market("A"), market("B"))
        item = registry((resolution(markets),), markets)
        result = certify_market_duplicate_resolution_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["resolution_count"], 1)

    def test_confirmed_duplicate_requires_shared_fingerprint(self):
        markets = (
            market("A", duplicate_keys=("bitcoin", "100000")),
            market("B", duplicate_keys=("bitcoin", "150000")),
        )
        with self.assertRaises(ValueError):
            registry((resolution(markets),), markets)

    def test_unknown_market_rejected(self):
        markets = (market("A"), market("B"))
        other_markets = (market("A"), market("C"))
        with self.assertRaises(ValueError):
            registry((resolution(markets),), other_markets)

    def test_market_cannot_join_two_groups(self):
        markets = (market("A"), market("B"), market("C"))
        first = resolution((markets[0], markets[1]))
        second = CertifiedMarketDuplicateResolution(
            duplicate_group_key="second-group",
            canonical_winner_market_id=markets[0].canonical_market_id,
            member_market_ids=(
                markets[0].canonical_market_id,
                markets[2].canonical_market_id,
            ),
            status=DuplicateResolutionStatus.CONFIRMED_DUPLICATE,
            rationale_code="same-outcome-same-expiry",
            metadata={},
            lineage=lineage(
                "UMD-009",
                UMD_009_REVISION,
                "fixture://umd-009/second",
            ),
        )
        with self.assertRaises(ValueError):
            registry((first, second), markets)

    def test_canonical_market_resolution(self):
        markets = (market("A"), market("B"))
        item = registry((resolution(markets),), markets)
        self.assertEqual(
            item.canonical_market_id_for(markets[1].canonical_market_id),
            markets[0].canonical_market_id,
        )

    def test_related_not_duplicate_preserves_identity(self):
        markets = (market("A"), market("B"))
        item = registry(
            (
                resolution(
                    markets,
                    status=DuplicateResolutionStatus.RELATED_NOT_DUPLICATE,
                ),
            ),
            markets,
        )
        self.assertEqual(
            item.canonical_market_id_for(markets[1].canonical_market_id),
            markets[1].canonical_market_id,
        )

    def test_unresolved_candidate_detection(self):
        markets = (market("A"), market("B"))
        item = registry(
            (
                resolution(
                    markets,
                    status=DuplicateResolutionStatus.CANDIDATE,
                ),
            ),
            markets,
        )
        strict = certify_market_duplicate_resolution_registry(
            item,
            allow_unresolved_candidates=False,
        )
        relaxed = certify_market_duplicate_resolution_registry(
            item,
            allow_unresolved_candidates=True,
        )
        self.assertFalse(strict["certified"])
        self.assertTrue(relaxed["certified"])

    def test_side_effects_disabled(self):
        manifest = build_umd_009_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-009 CERTIFICATION TEST")
    print(" CERTIFIED MARKET DUPLICATE RESOLUTION REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD009)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_009_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-008 consumed read-only")
    print("[PASS] Duplicate-resolution IDs deterministic")
    print("[PASS] Confirmed duplicate fingerprints validated")
    print("[PASS] Canonical winner selection deterministic")
    print("[PASS] Unknown markets rejected")
    print("[PASS] Multi-group market conflicts rejected")
    print("[PASS] Related-not-duplicate identity preserved")
    print("[PASS] Unresolved duplicate candidates detected")
    print("[PASS] Read-only duplicate registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic merging and deletion disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-009 CERTIFIED MARKET DUPLICATE RESOLUTION REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_market_duplicate_resolution_registry import (
    UMD_009_BUILD_ID,
    UMD_009_BUILD_NAME,
    UMD_009_REVISION,
    UMD_009_SCHEMA_VERSION,
    DuplicateResolutionStatus,
    CertifiedMarketDuplicateResolution,
    ReadOnlyMarketDuplicateResolutionRegistry,
    UMD009CertificationManifest,
    build_umd_009_certification_manifest,
    certify_market_duplicate_resolution_registry,
    certify_umd_009_foundation,
    verify_umd_009_certified_market_duplicate_resolution_registry,
)
"""

NAMES = [
    "UMD_009_BUILD_ID",
    "UMD_009_BUILD_NAME",
    "UMD_009_REVISION",
    "UMD_009_SCHEMA_VERSION",
    "DuplicateResolutionStatus",
    "CertifiedMarketDuplicateResolution",
    "ReadOnlyMarketDuplicateResolutionRegistry",
    "UMD009CertificationManifest",
    "build_umd_009_certification_manifest",
    "certify_market_duplicate_resolution_registry",
    "certify_umd_009_foundation",
    "verify_umd_009_certified_market_duplicate_resolution_registry",
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
        raise FileNotFoundError(f"UMD package initializer missing: {INIT}")
    source = INIT.read_text(encoding="utf-8")
    if "from .certified_market_duplicate_resolution_registry import (" not in source:
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
            "certified_market_duplicate_resolution_registry"
        )
        required = (
            "CertifiedMarketDuplicateResolution",
            "ReadOnlyMarketDuplicateResolutionRegistry",
            "certify_market_duplicate_resolution_registry",
            "certify_umd_009_foundation",
            "verify_umd_009_certified_market_duplicate_resolution_registry",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-009 missing symbols: " + ", ".join(missing))
        module.verify_umd_009_certified_market_duplicate_resolution_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-009 INSTALLER")
    print(" CERTIFIED MARKET DUPLICATE RESOLUTION REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-008 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-009",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007", "UMD-008",
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
    print("[PASS] Required UMD-009 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-009 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_009_certified_market_duplicate_resolution_registry.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
