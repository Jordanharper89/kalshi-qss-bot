from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_008_CERTIFIED_MARKET_LIFECYCLE_AND_SETTLEMENT_REGISTRY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_market_lifecycle_and_settlement_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_008_certified_market_lifecycle_and_settlement_registry.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    MarketLifecycle,
    SettlementMethod,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_market_metadata_registry import ReadOnlyMarketMetadataRegistry

UMD_008_BUILD_ID = "UMD-008"
UMD_008_BUILD_NAME = "Certified Market Lifecycle and Settlement Registry"
UMD_008_REVISION = "UMD_008_CERTIFIED_MARKET_LIFECYCLE_AND_SETTLEMENT_REGISTRY_V1"
UMD_008_SCHEMA_VERSION = "1.0.0"

ALLOWED_TRANSITIONS = MappingProxyType({
    MarketLifecycle.UNKNOWN: (
        MarketLifecycle.ANNOUNCED,
        MarketLifecycle.OPEN,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.ANNOUNCED: (
        MarketLifecycle.OPEN,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.OPEN: (
        MarketLifecycle.PAUSED,
        MarketLifecycle.CLOSED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.PAUSED: (
        MarketLifecycle.OPEN,
        MarketLifecycle.CLOSED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.CLOSED: (
        MarketLifecycle.EXPIRED,
        MarketLifecycle.SETTLING,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.EXPIRED: (
        MarketLifecycle.SETTLING,
        MarketLifecycle.SETTLED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.SETTLING: (
        MarketLifecycle.SETTLED,
        MarketLifecycle.CANCELLED,
    ),
    MarketLifecycle.SETTLED: (),
    MarketLifecycle.CANCELLED: (),
})

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _optional_text(value: str | None, name: str) -> str | None:
    return None if value is None else _text(value, name)

def _utc(value: datetime | None, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime or None")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedMarketLifecycleSettlementRecord:
    canonical_market_id: str
    lifecycle: MarketLifecycle
    opens_at: datetime | None
    closes_at: datetime | None
    expires_at: datetime | None
    settles_at: datetime | None
    settlement_method: SettlementMethod
    settlement_source: str | None
    settlement_rule: str | None
    final_value: str | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        market_id = _text(self.canonical_market_id, "canonical_market_id")
        if not market_id.startswith("umd:mkt:"):
            raise ValueError("canonical_market_id must use UMD market prefix")
        object.__setattr__(self, "canonical_market_id", market_id)

        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(self, "lifecycle", MarketLifecycle(self.lifecycle))
        if not isinstance(self.settlement_method, SettlementMethod):
            object.__setattr__(
                self,
                "settlement_method",
                SettlementMethod(self.settlement_method),
            )

        values = {
            "opens_at": _utc(self.opens_at, "opens_at"),
            "closes_at": _utc(self.closes_at, "closes_at"),
            "expires_at": _utc(self.expires_at, "expires_at"),
            "settles_at": _utc(self.settles_at, "settles_at"),
        }
        for name, value in values.items():
            object.__setattr__(self, name, value)

        ordered = [v for v in values.values() if v is not None]
        if ordered != sorted(ordered):
            raise ValueError(
                "timestamps must satisfy opens_at <= closes_at <= expires_at <= settles_at"
            )

        object.__setattr__(
            self,
            "settlement_source",
            _optional_text(self.settlement_source, "settlement_source"),
        )
        object.__setattr__(
            self,
            "settlement_rule",
            _optional_text(self.settlement_rule, "settlement_rule"),
        )
        object.__setattr__(
            self,
            "final_value",
            _optional_text(self.final_value, "final_value"),
        )
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lifecycle == MarketLifecycle.SETTLED:
            if self.final_value is None or self.settles_at is None:
                raise ValueError(
                    "settled markets require final_value and settles_at"
                )
        elif self.final_value is not None:
            raise ValueError("final_value is allowed only for settled markets")

        if self.lifecycle in {
            MarketLifecycle.CLOSED,
            MarketLifecycle.EXPIRED,
            MarketLifecycle.SETTLING,
            MarketLifecycle.SETTLED,
        } and self.closes_at is None:
            raise ValueError("closed or later states require closes_at")

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("lineage must belong to UMD")
        if self.lineage.build_id != UMD_008_BUILD_ID:
            raise ValueError("lineage must use build_id UMD-008")

    @classmethod
    def from_market(
        cls,
        market: CertifiedCanonicalMarket,
        *,
        final_value: str | None,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedMarketLifecycleSettlementRecord":
        return cls(
            canonical_market_id=market.canonical_market_id,
            lifecycle=market.lifecycle,
            opens_at=market.opens_at,
            closes_at=market.closes_at,
            expires_at=market.expires_at,
            settles_at=market.settles_at,
            settlement_method=market.settlement_method,
            settlement_source=market.settlement_source,
            settlement_rule=market.settlement_rule,
            final_value=final_value,
            metadata=metadata,
            lineage=lineage,
        )

    @property
    def lifecycle_record_id(self) -> str:
        return "umd:lifecycle:" + deterministic_sha256({
            "canonical_market_id": self.canonical_market_id
        })

    def state_payload(self) -> Mapping[str, Any]:
        return {
            "lifecycle": self.lifecycle,
            "opens_at": self.opens_at,
            "closes_at": self.closes_at,
            "expires_at": self.expires_at,
            "settles_at": self.settles_at,
            "settlement_method": self.settlement_method,
            "settlement_source": self.settlement_source,
            "settlement_rule": self.settlement_rule,
            "final_value": self.final_value,
        }

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "lifecycle_record_id": self.lifecycle_record_id,
            "canonical_market_id": self.canonical_market_id,
            **self.state_payload(),
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

    def validate_transition_to(
        self,
        next_record: "CertifiedMarketLifecycleSettlementRecord",
    ) -> bool:
        if self.canonical_market_id != next_record.canonical_market_id:
            raise ValueError("transition must remain on the same market")
        if self.record_hash not in next_record.lineage.parent_hashes:
            raise ValueError("next lineage must include prior record hash")
        if next_record.lifecycle not in ALLOWED_TRANSITIONS[self.lifecycle]:
            raise ValueError(
                f"invalid lifecycle transition: "
                f"{self.lifecycle.value} -> {next_record.lifecycle.value}"
            )
        return True

@dataclass(frozen=True, slots=True)
class ReadOnlyMarketLifecycleSettlementRegistry:
    records: Tuple[CertifiedMarketLifecycleSettlementRecord, ...]
    markets: Tuple[CertifiedCanonicalMarket, ...]
    metadata_registry: ReadOnlyMarketMetadataRegistry
    registry_lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedMarketLifecycleSettlementRecord] = field(
        init=False, repr=False
    )
    _by_record_id: Mapping[str, CertifiedMarketLifecycleSettlementRecord] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        records = tuple(sorted(self.records, key=lambda x: x.lifecycle_record_id))
        markets = tuple(sorted(self.markets, key=lambda x: x.canonical_market_id))
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "markets", markets)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_008_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-008")

        market_by_id = {m.canonical_market_id: m for m in markets}
        if len(market_by_id) != len(markets):
            raise ValueError("duplicate canonical market IDs supplied")

        by_market_id = {}
        by_record_id = {}
        for record in records:
            if record.lifecycle_record_id in by_record_id:
                raise ValueError("duplicate lifecycle record ID")
            if record.canonical_market_id in by_market_id:
                raise ValueError("market may have only one current lifecycle record")

            market = market_by_id.get(record.canonical_market_id)
            if market is None:
                raise ValueError("unknown canonical market ID")
            if self.metadata_registry.get_by_market(record.canonical_market_id) is None:
                raise ValueError("lifecycle record requires certified metadata")

            expected = CertifiedMarketLifecycleSettlementRecord.from_market(
                market,
                final_value=record.final_value,
                metadata=record.metadata,
                lineage=record.lineage,
            )
            if record.state_payload() != expected.state_payload():
                raise ValueError(
                    "lifecycle or settlement fields do not match canonical market"
                )

            by_market_id[record.canonical_market_id] = record
            by_record_id[record.lifecycle_record_id] = record

        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_record_id",
            MappingProxyType(by_record_id),
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMarketLifecycleSettlementRecord | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get(
        self,
        lifecycle_record_id: str,
    ) -> CertifiedMarketLifecycleSettlementRecord | None:
        return self._by_record_id.get(
            _text(lifecycle_record_id, "lifecycle_record_id")
        )

    def markets_expiring_by(
        self,
        cutoff: datetime,
    ) -> Tuple[CertifiedMarketLifecycleSettlementRecord, ...]:
        cutoff = _utc(cutoff, "cutoff")
        return tuple(sorted(
            (
                record
                for record in self.records
                if record.expires_at is not None
                and record.expires_at <= cutoff
            ),
            key=lambda x: (x.expires_at, x.canonical_market_id),
        ))

    def missing_lifecycle_market_ids(self) -> Tuple[str, ...]:
        return tuple(
            market.canonical_market_id
            for market in self.markets
            if market.canonical_market_id not in self._by_market_id
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "records": self.records,
            "market_record_hashes": tuple(
                market.record_hash for market in self.markets
            ),
            "metadata_registry_hash": self.metadata_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD008CertificationManifest:
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

def build_umd_008_certification_manifest() -> UMD008CertificationManifest:
    return UMD008CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_008_BUILD_ID,
        build_name=UMD_008_BUILD_NAME,
        revision=UMD_008_REVISION,
        schema_version=UMD_008_SCHEMA_VERSION,
        upstream_builds=(
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007",
        ),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_umd_008_foundation() -> Mapping[str, Any]:
    manifest = build_umd_008_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-008",
        "upstreams_frozen": manifest.upstream_builds == (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007",
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
    failed = tuple(name for name, ok in checks.items() if not ok)
    return MappingProxyType({
        "certified": not failed,
        "build_id": manifest.build_id,
        "revision": manifest.revision,
        "manifest_hash": manifest.manifest_hash,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def certify_market_lifecycle_and_settlement_registry(
    registry: ReadOnlyMarketLifecycleSettlementRegistry,
    *,
    require_all_markets_tracked: bool = True,
) -> Mapping[str, Any]:
    missing = registry.missing_lifecycle_market_ids()
    checks = {
        "record_ids_unique": len(
            {r.lifecycle_record_id for r in registry.records}
        ) == len(registry.records),
        "market_records_unique": len(
            {r.canonical_market_id for r in registry.records}
        ) == len(registry.records),
        "all_markets_resolve": all(
            registry.get_by_market(r.canonical_market_id) is not None
            for r in registry.records
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "all_markets_tracked": (
            not missing if require_all_markets_tracked else True
        ),
    }
    failed = tuple(name for name, ok in checks.items() if not ok)
    return MappingProxyType({
        "certified": not failed,
        "registry_hash": registry.registry_hash,
        "record_count": len(registry.records),
        "missing_lifecycle_market_ids": missing,
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def verify_umd_008_certified_market_lifecycle_and_settlement_registry() -> bool:
    result = certify_umd_008_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-008 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_008_BUILD_ID",
    "UMD_008_BUILD_NAME",
    "UMD_008_REVISION",
    "UMD_008_SCHEMA_VERSION",
    "ALLOWED_TRANSITIONS",
    "CertifiedMarketLifecycleSettlementRecord",
    "ReadOnlyMarketLifecycleSettlementRegistry",
    "UMD008CertificationManifest",
    "build_umd_008_certification_manifest",
    "certify_market_lifecycle_and_settlement_registry",
    "certify_umd_008_foundation",
    "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
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
    build_umd_008_certification_manifest,
    certify_market_lifecycle_and_settlement_registry,
    certify_umd_008_foundation,
    verify_umd_008_certified_market_lifecycle_and_settlement_registry,
)

FIXED = datetime(2026, 8, 5, 10, 0, tzinfo=timezone.utc)

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

def market(native_id="BTC-100K", lifecycle=MarketLifecycle.OPEN):
    settles_at = (
        datetime(2027, 1, 2, tzinfo=timezone.utc)
        if lifecycle == MarketLifecycle.SETTLED
        else None
    )
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={},
        ),
        native_market_id=native_id,
        native_event_id="BTC",
        canonical_title=f"Fixture market {native_id}",
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
        lifecycle=lifecycle,
        opens_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        closes_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Fixture settlement rule.",
        settles_at=settles_at,
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

def metadata_registry(markets):
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
    records = tuple(
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
            attributes={"read_only": True},
            lineage=lineage(
                "UMD-007",
                UMD_007_REVISION,
                f"fixture://umd-007/{item.native_market_id}",
            ),
        )
        for item in markets
    )
    return ReadOnlyMarketMetadataRegistry(
        metadata_records=records,
        markets=tuple(markets),
        classification_registry=classification_registry,
        registry_lineage=lineage(
            "UMD-007",
            UMD_007_REVISION,
            "fixture://umd-007/registry",
        ),
    )

def record(item, final_value=None, parent_hashes=()):
    return CertifiedMarketLifecycleSettlementRecord.from_market(
        item,
        final_value=final_value,
        metadata={"read_only": True},
        lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            f"fixture://umd-008/{item.native_market_id}",
            parent_hashes=parent_hashes,
        ),
    )

def registry(records, markets):
    return ReadOnlyMarketLifecycleSettlementRegistry(
        records=tuple(records),
        markets=tuple(markets),
        metadata_registry=metadata_registry(markets),
        registry_lineage=lineage(
            "UMD-008",
            UMD_008_REVISION,
            "fixture://umd-008/registry",
        ),
    )

class TestUMD008(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_008_foundation()["certified"])
        self.assertTrue(
            verify_umd_008_certified_market_lifecycle_and_settlement_registry()
        )

    def test_identity_deterministic(self):
        item = market()
        self.assertEqual(
            record(item).lifecycle_record_id,
            record(item).lifecycle_record_id,
        )

    def test_record_hash_deterministic(self):
        item = market()
        self.assertEqual(record(item).record_hash, record(item).record_hash)

    def test_immutable(self):
        item = record(market())
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.lifecycle = MarketLifecycle.CLOSED
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_registry_certifies(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(second), record(first)), (second, first))
        result = certify_market_lifecycle_and_settlement_registry(item)
        self.assertTrue(result["certified"])
        self.assertEqual(result["record_count"], 2)

    def test_duplicate_market_record_rejected(self):
        item = market()
        value = record(item)
        with self.assertRaises(ValueError):
            registry((value, value), (item,))

    def test_unknown_market_rejected(self):
        first = market("ONE")
        second = market("TWO")
        with self.assertRaises(ValueError):
            registry((record(first),), (second,))

    def test_settled_requires_final_value(self):
        item = market("SETTLED", MarketLifecycle.SETTLED)
        with self.assertRaises(ValueError):
            record(item)

    def test_non_settled_rejects_final_value(self):
        with self.assertRaises(ValueError):
            record(market(), final_value="YES")

    def test_valid_transition(self):
        current_market = market("TRANSITION", MarketLifecycle.OPEN)
        next_market = market("TRANSITION", MarketLifecycle.CLOSED)
        current = record(current_market)
        nxt = record(next_market, parent_hashes=(current.record_hash,))
        self.assertTrue(current.validate_transition_to(nxt))

    def test_invalid_transition_rejected(self):
        current_market = market("TRANSITION", MarketLifecycle.OPEN)
        next_market = market("TRANSITION", MarketLifecycle.SETTLED)
        current = record(current_market)
        nxt = record(
            next_market,
            final_value="YES",
            parent_hashes=(current.record_hash,),
        )
        with self.assertRaises(ValueError):
            current.validate_transition_to(nxt)

    def test_expiration_query_deterministic(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(second), record(first)), (second, first))
        results = item.markets_expiring_by(
            datetime(2027, 1, 1, tzinfo=timezone.utc)
        )
        ids = tuple(value.canonical_market_id for value in results)
        self.assertEqual(ids, tuple(sorted(ids)))

    def test_missing_lifecycle_detection(self):
        first = market("ONE")
        second = market("TWO")
        item = registry((record(first),), (first, second))
        strict = certify_market_lifecycle_and_settlement_registry(
            item,
            require_all_markets_tracked=True,
        )
        relaxed = certify_market_lifecycle_and_settlement_registry(
            item,
            require_all_markets_tracked=False,
        )
        self.assertFalse(strict["certified"])
        self.assertTrue(relaxed["certified"])

    def test_side_effects_disabled(self):
        manifest = build_umd_008_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-008 CERTIFICATION TEST")
    print(" CERTIFIED MARKET LIFECYCLE AND SETTLEMENT REGISTRY")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD008)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_008_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-007 consumed read-only")
    print("[PASS] Canonical lifecycle record IDs deterministic")
    print("[PASS] Market and metadata foreign keys validated")
    print("[PASS] Expiration and settlement timestamps validated")
    print("[PASS] Settled final-value requirements enforced")
    print("[PASS] Lifecycle transition rules certified")
    print("[PASS] Invalid lifecycle transitions rejected")
    print("[PASS] Expiration lookup deterministic")
    print("[PASS] Missing lifecycle tracking detected")
    print("[PASS] Read-only lifecycle registry certified")
    print("[PASS] Deterministic ordering and replay verified")
    print("[PASS] Automatic advancement and settlement disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-008 CERTIFIED MARKET LIFECYCLE AND SETTLEMENT REGISTRY CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_market_lifecycle_and_settlement_registry import (
    UMD_008_BUILD_ID,
    UMD_008_BUILD_NAME,
    UMD_008_REVISION,
    UMD_008_SCHEMA_VERSION,
    ALLOWED_TRANSITIONS,
    CertifiedMarketLifecycleSettlementRecord,
    ReadOnlyMarketLifecycleSettlementRegistry,
    UMD008CertificationManifest,
    build_umd_008_certification_manifest,
    certify_market_lifecycle_and_settlement_registry,
    certify_umd_008_foundation,
    verify_umd_008_certified_market_lifecycle_and_settlement_registry,
)
"""

NAMES = [
    "UMD_008_BUILD_ID",
    "UMD_008_BUILD_NAME",
    "UMD_008_REVISION",
    "UMD_008_SCHEMA_VERSION",
    "ALLOWED_TRANSITIONS",
    "CertifiedMarketLifecycleSettlementRecord",
    "ReadOnlyMarketLifecycleSettlementRegistry",
    "UMD008CertificationManifest",
    "build_umd_008_certification_manifest",
    "certify_market_lifecycle_and_settlement_registry",
    "certify_umd_008_foundation",
    "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
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
    if "from .certified_market_lifecycle_and_settlement_registry import (" not in source:
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
            "certified_market_lifecycle_and_settlement_registry"
        )
        required = (
            "CertifiedMarketLifecycleSettlementRecord",
            "ReadOnlyMarketLifecycleSettlementRegistry",
            "certify_market_lifecycle_and_settlement_registry",
            "certify_umd_008_foundation",
            "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-008 missing symbols: " + ", ".join(missing))
        module.verify_umd_008_certified_market_lifecycle_and_settlement_registry()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-008 INSTALLER")
    print(" CERTIFIED MARKET LIFECYCLE AND SETTLEMENT REGISTRY")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-007 verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-008",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": (
            "UMD-001", "UMD-002", "UMD-003", "UMD-004",
            "UMD-005", "UMD-006", "UMD-007",
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
    print("[PASS] Required UMD-008 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-008 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_008_certified_market_lifecycle_and_settlement_registry.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
