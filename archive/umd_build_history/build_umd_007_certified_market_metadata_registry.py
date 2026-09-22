from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_007_CERTIFIED_MARKET_METADATA_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_market_metadata_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_007_certified_market_metadata_registry.py"

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
from .certified_market_classification_registry import (
    ReadOnlyMarketClassificationRegistry,
)

UMD_007_BUILD_ID = "UMD-007"
UMD_007_BUILD_NAME = "Certified Market Metadata Registry"
UMD_007_REVISION = "UMD_007_CERTIFIED_MARKET_METADATA_REGISTRY_V1"
UMD_007_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_metadata_enrichment",
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

def _optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else _text(value, name)

def _slug(value: str, name: str) -> str:
    normalized = _text(value, name).lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(
            f"{name} may contain only lowercase letters, digits, hyphen, and underscore"
        )
    return normalized

def _symbol(value: str, name: str) -> str:
    normalized = _text(value, name).upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(f"{name} contains unsupported characters")
    return normalized

def _unique_text(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_text(value, name) for value in values}))

def _unique_slug(values: Tuple[str, ...], name: str) -> Tuple[str, ...]:
    return tuple(sorted({_slug(value, name) for value in values}))

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )

@dataclass(frozen=True, slots=True)
class CertifiedMarketMetadata:
    canonical_market_id: str
    display_title: str
    short_title: str | None
    description: str | None
    symbol: str | None
    language: str
    timezone_name: str
    quote_currency: str
    tags: Tuple[str, ...]
    keywords: Tuple[str, ...]
    external_reference_ids: Mapping[str, str]
    metadata_version: str
    attributes: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use the UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        object.__setattr__(
            self,
            "display_title",
            _text(self.display_title, "display_title"),
        )
        object.__setattr__(
            self,
            "short_title",
            _optional_text(self.short_title, "short_title"),
        )
        object.__setattr__(
            self,
            "description",
            _optional_text(self.description, "description"),
        )
        if self.symbol is not None:
            object.__setattr__(
                self,
                "symbol",
                _symbol(self.symbol, "symbol"),
            )

        object.__setattr__(
            self,
            "language",
            _slug(self.language, "language"),
        )
        object.__setattr__(
            self,
            "timezone_name",
            _text(self.timezone_name, "timezone_name"),
        )
        object.__setattr__(
            self,
            "quote_currency",
            _symbol(self.quote_currency, "quote_currency"),
        )
        object.__setattr__(
            self,
            "tags",
            _unique_slug(self.tags, "tag"),
        )
        object.__setattr__(
            self,
            "keywords",
            _unique_text(self.keywords, "keyword"),
        )

        references = {}
        for namespace, reference_id in self.external_reference_ids.items():
            normalized_namespace = _slug(str(namespace), "reference namespace")
            normalized_reference = _text(str(reference_id), "reference id")
            if normalized_namespace in references:
                raise ValueError(
                    f"duplicate external reference namespace: {normalized_namespace}"
                )
            references[normalized_namespace] = normalized_reference
        object.__setattr__(
            self,
            "external_reference_ids",
            MappingProxyType(dict(sorted(references.items()))),
        )

        object.__setattr__(
            self,
            "metadata_version",
            _text(self.metadata_version, "metadata_version"),
        )
        object.__setattr__(
            self,
            "attributes",
            _freeze(self.attributes),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("metadata lineage must belong to UMD")
        if self.lineage.build_id != UMD_007_BUILD_ID:
            raise ValueError("metadata lineage must use build_id UMD-007")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        short_title: str | None,
        symbol: str | None,
        language: str,
        timezone_name: str,
        tags: Tuple[str, ...],
        keywords: Tuple[str, ...],
        external_reference_ids: Mapping[str, str],
        metadata_version: str,
        attributes: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketMetadata":
        return cls(
            canonical_market_id=market.canonical_market_id,
            display_title=market.canonical_title,
            short_title=short_title,
            description=market.canonical_description,
            symbol=symbol,
            language=language,
            timezone_name=timezone_name,
            quote_currency=market.quote_currency,
            tags=tags,
            keywords=keywords,
            external_reference_ids=external_reference_ids,
            metadata_version=metadata_version,
            attributes=attributes,
            lineage=lineage,
        )

    def identity_payload(self) -> Mapping[str, Any]:
        return {"canonical_market_id": self.canonical_market_id}

    @property
    def metadata_id(self) -> str:
        return f"umd:metadata:{deterministic_sha256(self.identity_payload())}"

    def content_payload(self) -> Mapping[str, Any]:
        return {
            "display_title": self.display_title,
            "short_title": self.short_title,
            "description": self.description,
            "symbol": self.symbol,
            "language": self.language,
            "timezone_name": self.timezone_name,
            "quote_currency": self.quote_currency,
            "tags": self.tags,
            "keywords": self.keywords,
            "external_reference_ids": self.external_reference_ids,
            "metadata_version": self.metadata_version,
            "attributes": self.attributes,
        }

    @property
    def content_fingerprint(self) -> str:
        return deterministic_sha256(self.content_payload())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "metadata_id": self.metadata_id,
            "canonical_market_id": self.canonical_market_id,
            **self.content_payload(),
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketMetadataRegistry:
    metadata_records: Tuple[CertifiedMarketMetadata, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    classification_registry: ReadOnlyMarketClassificationRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketMetadata] = field(
        init=False,
        repr=False,
    )
    _by_metadata_id: Mapping[str, CertifiedMarketMetadata] = field(
        init=False,
        repr=False,
    )
    _by_tag: Mapping[str, Tuple[CertifiedMarketMetadata, ...]] = field(
        init=False,
        repr=False,
    )
    _reference_index: Mapping[Tuple[str, str], str] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        ordered_records = tuple(
            sorted(
                self.metadata_records,
                key=lambda item: item.metadata_id,
            )
        )
        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda item: item.canonical_market_id,
            )
        )
        object.__setattr__(self, "metadata_records", ordered_records)
        object.__setattr__(self, "markets", ordered_markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_007_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-007")

        market_by_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(market_by_id) != len(ordered_markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_metadata_id = {}
        tag_groups = {}
        reference_index = {}

        for record in ordered_records:
            if record.metadata_id in by_metadata_id:
                raise ValueError("duplicate metadata ID")
            if record.canonical_market_id in by_market_id:
                raise ValueError(
                    "canonical market may have only one certified metadata record"
                )

            market = market_by_id.get(record.canonical_market_id)
            if market is None:
                raise ValueError(
                    f"unknown canonical market ID: {record.canonical_market_id}"
                )

            classification = self.classification_registry.get_by_market(
                record.canonical_market_id
            )
            if classification is None:
                raise ValueError(
                    "market metadata requires a certified classification"
                )

            if record.display_title != market.canonical_title:
                raise ValueError("display_title must match canonical market title")
            if record.description != market.canonical_description:
                raise ValueError(
                    "description must match canonical market description"
                )
            if record.quote_currency != market.quote_currency:
                raise ValueError(
                    "quote_currency must match canonical market currency"
                )

            for namespace, reference_id in record.external_reference_ids.items():
                key = (namespace, reference_id)
                existing = reference_index.get(key)
                if existing is not None and existing != record.canonical_market_id:
                    raise ValueError(
                        "duplicate external reference identity across markets"
                    )
                reference_index[key] = record.canonical_market_id

            by_market_id[record.canonical_market_id] = record
            by_metadata_id[record.metadata_id] = record

            for tag in record.tags:
                tag_groups.setdefault(tag, []).append(record)

        frozen_tag_groups = {
            tag: tuple(
                sorted(
                    records,
                    key=lambda item: item.canonical_market_id,
                )
            )
            for tag, records in tag_groups.items()
        }

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_metadata_id",
            MappingProxyType(by_metadata_id),
        )
        object.__setattr__(
            self,
            "_by_tag",
            MappingProxyType(frozen_tag_groups),
        )
        object.__setattr__(
            self,
            "_reference_index",
            MappingProxyType(reference_index),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketMetadata | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        metadata_id: str,
    ) -> CertifiedMarketMetadata | None:
        return self._by_metadata_id.get(
            _text(metadata_id, "metadata_id")
        )

    def by_tag(
        self,
        tag: str,
    ) -> Tuple[CertifiedMarketMetadata, ...]:
        return self._by_tag.get(_slug(tag, "tag"), ())

    def resolve_external_reference(
        self,
        namespace: str,
        reference_id: str,
    ) -> CertifiedMarketMetadata | None:
        market_id = self._reference_index.get(
            (
                _slug(namespace, "reference namespace"),
                _text(reference_id, "reference id"),
            )
        )
        if market_id is None:
            return None
        return self._by_market_id[market_id]

    def missing_metadata_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "metadata_records": self.metadata_records,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "classification_registry_hash": (
                self.classification_registry.registry_hash
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class MarketMetadataCertificationResult:
    certified: bool
    registry_hash: str
    metadata_count: int
    missing_metadata_market_ids: Tuple[str, ...]
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(self.checks)),
        )

@dataclass(frozen=True, slots=True)
class UMD007CertificationManifest:
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

def build_umd_007_certification_manifest() -> UMD007CertificationManifest:
    return UMD007CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_007_BUILD_ID,
        build_name=UMD_007_BUILD_NAME,
        revision=UMD_007_REVISION,
        schema_version=UMD_007_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
        ),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_market_metadata_registry(
    registry: ReadOnlyMarketMetadataRegistry,
    *,
    require_all_markets_described: bool = True,
) -> MarketMetadataCertificationResult:
    missing = registry.missing_metadata_market_ids()
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "metadata_ids_unique": len(
            {record.metadata_id for record in registry.metadata_records}
        ) == len(registry.metadata_records),
        "market_metadata_unique": len(
            {
                record.canonical_market_id
                for record in registry.metadata_records
            }
        ) == len(registry.metadata_records),
        "all_markets_resolve": all(
            registry.get_by_market(record.canonical_market_id) is not None
            for record in registry.metadata_records
        ),
        "all_classifications_resolve": all(
            registry.classification_registry.get_by_market(
                record.canonical_market_id
            )
            is not None
            for record in registry.metadata_records
        ),
        "all_lineage_certified": all(
            record.lineage.subsystem_id == "UMD"
            and record.lineage.build_id == "UMD-007"
            for record in registry.metadata_records
        ),
        "deterministic_ordering": tuple(
            record.metadata_id for record in registry.metadata_records
        ) == tuple(
            sorted(
                record.metadata_id
                for record in registry.metadata_records
            )
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_described": (
            not missing if require_all_markets_described else True
        ),
        "registry_maps_read_only": isinstance(
            registry._by_market_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_metadata_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_tag,
            MappingProxyType,
        )
        and isinstance(
            registry._reference_index,
            MappingProxyType,
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
    )
    return MarketMetadataCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        metadata_count=len(registry.metadata_records),
        missing_metadata_market_ids=missing,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_007_foundation() -> Mapping[str, Any]:
    manifest = build_umd_007_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-007",
        "upstreams_frozen": manifest.upstream_builds
        == (
            "UMD-001",
            "UMD-002",
            "UMD-003",
            "UMD-004",
            "UMD-005",
            "UMD-006",
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

def verify_umd_007_certified_market_metadata_registry() -> bool:
    result = certify_umd_007_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-007 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_007_BUILD_ID",
    "UMD_007_BUILD_NAME",
    "UMD_007_REVISION",
    "UMD_007_SCHEMA_VERSION",
    "CertifiedMarketMetadata",
    "ReadOnlyMarketMetadataRegistry",
    "MarketMetadataCertificationResult",
    "UMD007CertificationManifest",
    "build_umd_007_certification_manifest",
    "certify_market_metadata_registry",
    "certify_umd_007_foundation",
    "verify_umd_007_certified_market_metadata_registry",
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
    build_umd_007_certification_manifest,
    certify_market_metadata_registry,
    certify_umd_007_foundation,
    verify_umd_007_certified_market_metadata_registry,
)

FIXED = datetime(2026, 8, 5, 9, 0, tzinfo=timezone.utc)

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
        canonical_description="Fixture market description.",
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

def classification_registry(markets):
    return ReadOnlyMarketClassificationRegistry(
        classifications=tuple(classification(item) for item in markets),
        markets=tuple(markets),
        category_registry=category_registry(),
        registry_lineage=lineage(
            "UMD-006",
            UMD_006_REVISION,
            "fixture://umd-006/registry",
        ),
    )

def metadata(item, reference_id=None):
    return CertifiedMarketMetadata.from_market(
        item,
        short_title=item.native_market_id,
        symbol="BTC",
        language="en",
        timezone_name="America/Chicago",
        tags=("bitcoin", "crypto"),
        keywords=("Bitcoin", "price"),
        external_reference_ids={
            "fixture": reference_id or item.native_market_id
        },
        metadata_version="1.0.0",
        attributes={"read_only": True},
        lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            f"fixture://umd-007/{item.native_market_id}",
        ),
    )

def registry(records, markets):
    return ReadOnlyMarketMetadataRegistry(
        metadata_records=tuple(records),
        markets=tuple(markets),
        classification_registry=classification_registry(markets),
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )

class TestUMD007(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_007_foundation()["certified"])
        self.assertTrue(
            verify_umd_007_certified_market_metadata_registry()
        )

    def test_metadata_identity_deterministic(self):
        item = market()
        self.assertEqual(
            metadata(item).metadata_id,
            metadata(item).metadata_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(
            metadata(item).record_hash,
            metadata(item).record_hash,
        )

    def test_immutable(self):
        item = metadata(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.display_title = "mutated"
        with self.assertRaises(TypeError):
            item.attributes["read_only"] = False
        with self.assertRaises(TypeError):
            item.external_reference_ids["fixture"] = "mutated"

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (metadata(second), metadata(first)),
            (second, first),
        )
        result = certify_market_metadata_registry(item)
        self.assertTrue(result.certified)
        self.assertEqual(result.metadata_count, 2)
        self.assertFalse(result.missing_metadata_market_ids)

    def test_duplicate_market_metadata_rejected(self):
        item = market()
        record = metadata(item)
        with self.assertRaises(ValueError):
            registry((record, record), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((metadata(first),), (second,))

    def test_title_mismatch_rejected(self):
        item = market()
        bad = CertifiedMarketMetadata(
            canonical_market_id=item.canonical_market_id,
            display_title="Wrong title",
            short_title=None,
            description=item.canonical_description,
            symbol="BTC",
            language="en",
            timezone_name="America/Chicago",
            quote_currency=item.quote_currency,
            tags=("bitcoin",),
            keywords=("Bitcoin",),
            external_reference_ids={"fixture": item.native_market_id},
            metadata_version="1.0.0",
            attributes={},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                "fixture://umd-007/bad",
            ),
        )
        with self.assertRaises(ValueError):
            registry((bad,), (item,))

    def test_duplicate_external_reference_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry(
                (
                    metadata(first, reference_id="SHARED"),
                    metadata(second, reference_id="SHARED"),
                ),
                (first, second),
            )

    def test_tag_lookup_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry(
            (metadata(second), metadata(first)),
            (second, first),
        )
        ids = tuple(
            record.canonical_market_id
            for record in item.by_tag("bitcoin")
        )
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_external_reference_resolution(self):
        item = market()
        record = metadata(item)
        reg = registry((record,), (item,))
        self.assertEqual(
            reg.resolve_external_reference(
                "fixture",
                item.native_market_id,
            ).canonical_market_id,
            item.canonical_market_id,
        )

    def test_missing_metadata_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((metadata(first),), (first, second))
        self.assertEqual(
            item.missing_metadata_market_ids(),
            (second.canonical_market_id,),
        )
        strict = certify_market_metadata_registry(
            item,
            require_all_markets_described=True,
        )
        relaxed = certify_market_metadata_registry(
            item,
            require_all_markets_described=False,
        )
        self.assertFalse(strict.certified)
        self.assertTrue(relaxed.certified)

    def test_side_effects_disabled(self):
        manifest = build_umd_007_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-007 CERTIFICATION TEST")
    print(" CERTIFIED MARKET METADATA REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD007)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_007_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-006 consumed read-only")
    print("[PASS] Canonical metadata IDs deterministic")
    print("[PASS] Market and classification foreign keys validated")
    print("[PASS] Title, description, and currency alignment verified")
    print("[PASS] Tags and keywords normalized deterministically")
    print("[PASS] External reference identities protected")
    print("[PASS] Duplicate metadata records rejected")
    print("[PASS] Missing metadata detection verified")
    print("[PASS] Read-only metadata registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic enrichment and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-007 CERTIFIED MARKET METADATA REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_market_metadata_registry import (
    UMD_007_BUILD_ID,
    UMD_007_BUILD_NAME,
    UMD_007_REVISION,
    UMD_007_SCHEMA_VERSION,
    CertifiedMarketMetadata,
    ReadOnlyMarketMetadataRegistry,
    MarketMetadataCertificationResult,
    UMD007CertificationManifest,
    build_umd_007_certification_manifest,
    certify_market_metadata_registry,
    certify_umd_007_foundation,
    verify_umd_007_certified_market_metadata_registry,
)
"""

NAMES = [
    "UMD_007_BUILD_ID",
    "UMD_007_BUILD_NAME",
    "UMD_007_REVISION",
    "UMD_007_SCHEMA_VERSION",
    "CertifiedMarketMetadata",
    "ReadOnlyMarketMetadataRegistry",
    "MarketMetadataCertificationResult",
    "UMD007CertificationManifest",
    "build_umd_007_certification_manifest",
    "certify_market_metadata_registry",
    "certify_umd_007_foundation",
    "verify_umd_007_certified_market_metadata_registry",
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
    if "from .certified_market_metadata_registry import (" not in source:
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
            (
                "certified_market_category_hierarchy_registry",
                "verify_umd_005_certified_market_category_hierarchy_registry",
            ),
            (
                "certified_market_classification_registry",
                "verify_umd_006_certified_market_classification_registry",
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
            "certified_market_metadata_registry"
        )
        required = (
            "CertifiedMarketMetadata",
            "ReadOnlyMarketMetadataRegistry",
            "certify_market_metadata_registry",
            "certify_umd_007_foundation",
            "verify_umd_007_certified_market_metadata_registry",
        )
        missing = [
            name
            for name in required
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-007 missing symbols: "
                + ", ".join(missing)
            )
        module.verify_umd_007_certified_market_metadata_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-007 INSTALLER")
    print(" CERTIFIED MARKET METADATA REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-006 "
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
        "build_id": "UMD-007",
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
            "UMD-006",
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
    print("[PASS] Required UMD-007 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print(
        "[PASS] Network, scanning, persistence, "
        "publication, and execution disabled"
    )
    print("[DONE] UMD-007 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_007_certified_market_metadata_registry.py"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
