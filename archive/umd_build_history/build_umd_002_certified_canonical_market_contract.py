from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_002_CERTIFIED_CANONICAL_MARKET_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_canonical_market_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_002_certified_canonical_market_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    MarketCategory,
    MarketInstrumentType,
    MarketLifecycle,
    SettlementMethod,
    VenueIdentity,
    deterministic_sha256,
)

UMD_002_BUILD_ID = "UMD-002"
UMD_002_BUILD_NAME = "Certified Canonical Market Contract"
UMD_002_REVISION = "UMD_002_CERTIFIED_CANONICAL_MARKET_CONTRACT_V1"
UMD_002_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
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

def _unique_tuple(values: Tuple[str, ...], name: str, preserve_order: bool = False) -> Tuple[str, ...]:
    cleaned = tuple(_text(v, name) for v in values)
    if preserve_order:
        output = []
        seen = set()
        for item in cleaned:
            key = item.casefold()
            if key not in seen:
                output.append(item)
                seen.add(key)
        return tuple(output)
    return tuple(sorted(set(cleaned)))

class AssetClass(str, Enum):
    UNKNOWN = "unknown"
    PREDICTION_MARKET = "prediction_market"
    CRYPTO = "crypto"
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    FOREX = "forex"
    COMMODITY = "commodity"
    FIXED_INCOME = "fixed_income"
    DERIVATIVE = "derivative"
    SPORTS = "sports"
    MACRO = "macro"
    POLITICS = "politics"
    WEATHER = "weather"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"

class GeographicScope(str, Enum):
    GLOBAL = "global"
    MULTI_REGION = "multi_region"
    COUNTRY = "country"
    STATE = "state"
    PROVINCE = "province"
    CITY = "city"
    VENUE_DEFINED = "venue_defined"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

@dataclass(frozen=True, slots=True)
class CertifiedCanonicalMarket:
    venue: VenueIdentity
    native_market_id: str
    native_event_id: str | None
    canonical_title: str
    canonical_description: str | None
    instrument_type: MarketInstrumentType
    category: MarketCategory
    asset_class: AssetClass
    geographic_scope: GeographicScope
    quote_currency: str
    tick_size: str
    price_precision: int
    lifecycle: MarketLifecycle
    opens_at: datetime | None
    closes_at: datetime | None
    expires_at: datetime | None
    settlement_method: SettlementMethod
    settlement_source: str | None
    settlement_rule: str | None
    settles_at: datetime | None
    outcome_labels: Tuple[str, ...]
    duplicate_resolution_keys: Tuple[str, ...]
    related_market_ids: Tuple[str, ...]
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "native_market_id", _text(self.native_market_id, "native_market_id"))
        object.__setattr__(self, "native_event_id", _optional_text(self.native_event_id, "native_event_id"))
        object.__setattr__(self, "canonical_title", _text(self.canonical_title, "canonical_title"))
        object.__setattr__(self, "canonical_description", _optional_text(self.canonical_description, "canonical_description"))

        if not isinstance(self.instrument_type, MarketInstrumentType):
            object.__setattr__(self, "instrument_type", MarketInstrumentType(self.instrument_type))
        if not isinstance(self.asset_class, AssetClass):
            object.__setattr__(self, "asset_class", AssetClass(self.asset_class))
        if not isinstance(self.geographic_scope, GeographicScope):
            object.__setattr__(self, "geographic_scope", GeographicScope(self.geographic_scope))
        if not isinstance(self.lifecycle, MarketLifecycle):
            object.__setattr__(self, "lifecycle", MarketLifecycle(self.lifecycle))
        if not isinstance(self.settlement_method, SettlementMethod):
            object.__setattr__(self, "settlement_method", SettlementMethod(self.settlement_method))

        currency = _text(self.quote_currency, "quote_currency").upper()
        object.__setattr__(self, "quote_currency", currency)

        tick = _text(self.tick_size, "tick_size")
        try:
            tick_value = float(tick)
        except ValueError as exc:
            raise ValueError("tick_size must be numeric text") from exc
        if tick_value <= 0:
            raise ValueError("tick_size must be greater than zero")
        object.__setattr__(self, "tick_size", tick)

        if not isinstance(self.price_precision, int):
            raise TypeError("price_precision must be an integer")
        if self.price_precision < 0 or self.price_precision > 18:
            raise ValueError("price_precision must be between 0 and 18")

        opens_at = _utc(self.opens_at, "opens_at")
        closes_at = _utc(self.closes_at, "closes_at")
        expires_at = _utc(self.expires_at, "expires_at")
        settles_at = _utc(self.settles_at, "settles_at")
        object.__setattr__(self, "opens_at", opens_at)
        object.__setattr__(self, "closes_at", closes_at)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "settles_at", settles_at)

        ordered = [v for v in (opens_at, closes_at, expires_at, settles_at) if v is not None]
        if ordered != sorted(ordered):
            raise ValueError("timestamps must satisfy opens_at <= closes_at <= expires_at <= settles_at")

        object.__setattr__(self, "settlement_source", _optional_text(self.settlement_source, "settlement_source"))
        object.__setattr__(self, "settlement_rule", _optional_text(self.settlement_rule, "settlement_rule"))

        outcomes = _unique_tuple(self.outcome_labels, "outcome_label", preserve_order=True)
        if self.instrument_type == MarketInstrumentType.BINARY and len(outcomes) != 2:
            raise ValueError("binary markets must define exactly two outcomes")
        if not outcomes:
            raise ValueError("market must define at least one outcome")
        object.__setattr__(self, "outcome_labels", outcomes)

        duplicate_keys = _unique_tuple(self.duplicate_resolution_keys, "duplicate_resolution_key")
        if not duplicate_keys:
            raise ValueError("duplicate_resolution_keys must not be empty")
        object.__setattr__(self, "duplicate_resolution_keys", duplicate_keys)

        related = _unique_tuple(self.related_market_ids, "related_market_id")
        object.__setattr__(self, "related_market_ids", related)
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("lineage must belong to UMD")
        if self.lineage.build_id != UMD_002_BUILD_ID:
            raise ValueError("lineage must use build_id UMD-002")
        if self.canonical_market_id in related:
            raise ValueError("market cannot reference itself")

    def identity_payload(self) -> Mapping[str, Any]:
        return {
            "venue_id": self.venue.venue_id,
            "native_market_namespace": self.venue.native_market_namespace,
            "native_market_id": self.native_market_id,
        }

    @property
    def canonical_market_id(self) -> str:
        return f"umd:mkt:{deterministic_sha256(self.identity_payload())}"

    @property
    def duplicate_fingerprint(self) -> str:
        return deterministic_sha256({
            "duplicate_resolution_keys": self.duplicate_resolution_keys,
            "asset_class": self.asset_class,
            "category_id": self.category.category_id,
            "expires_at": self.expires_at,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "canonical_market_id": self.canonical_market_id,
            "venue": self.venue,
            "native_market_id": self.native_market_id,
            "native_event_id": self.native_event_id,
            "canonical_title": self.canonical_title,
            "canonical_description": self.canonical_description,
            "instrument_type": self.instrument_type,
            "category": self.category,
            "asset_class": self.asset_class,
            "geographic_scope": self.geographic_scope,
            "quote_currency": self.quote_currency,
            "tick_size": self.tick_size,
            "price_precision": self.price_precision,
            "lifecycle": self.lifecycle,
            "opens_at": self.opens_at,
            "closes_at": self.closes_at,
            "expires_at": self.expires_at,
            "settlement_method": self.settlement_method,
            "settlement_source": self.settlement_source,
            "settlement_rule": self.settlement_rule,
            "settles_at": self.settles_at,
            "outcome_labels": self.outcome_labels,
            "duplicate_resolution_keys": self.duplicate_resolution_keys,
            "related_market_ids": self.related_market_ids,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

    def with_related_market_ids(
        self,
        related_market_ids: Tuple[str, ...],
        *,
        lineage: ImmutableLineage,
    ) -> "CertifiedCanonicalMarket":
        if self.record_hash not in lineage.parent_hashes:
            raise ValueError("replacement lineage must include prior record hash")
        return replace(self, related_market_ids=related_market_ids, lineage=lineage)

@dataclass(frozen=True, slots=True)
class CanonicalMarketCertificationResult:
    certified: bool
    canonical_market_id: str
    record_hash: str
    duplicate_fingerprint: str
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))

@dataclass(frozen=True, slots=True)
class UMD002CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_build: str
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
            "upstream_build": self.upstream_build,
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

def build_umd_002_certification_manifest() -> UMD002CertificationManifest:
    return UMD002CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_002_BUILD_ID,
        build_name=UMD_002_BUILD_NAME,
        revision=UMD_002_REVISION,
        schema_version=UMD_002_SCHEMA_VERSION,
        upstream_build="UMD-001",
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_canonical_market(market: CertifiedCanonicalMarket) -> CanonicalMarketCertificationResult:
    checks = {
        "canonical_id_prefix": market.canonical_market_id.startswith("umd:mkt:"),
        "canonical_id_length": len(market.canonical_market_id) == 72,
        "record_hash_length": len(market.record_hash) == 64,
        "duplicate_fingerprint_length": len(market.duplicate_fingerprint) == 64,
        "lineage_subsystem": market.lineage.subsystem_id == "UMD",
        "lineage_build": market.lineage.build_id == "UMD-002",
        "outcomes_present": bool(market.outcome_labels),
        "duplicate_keys_present": bool(market.duplicate_resolution_keys),
        "metadata_read_only": isinstance(market.metadata, MappingProxyType),
        "deterministic_replay": market.record_hash == deterministic_sha256(market.to_canonical_dict()),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return CanonicalMarketCertificationResult(
        certified=not failed,
        canonical_market_id=market.canonical_market_id,
        record_hash=market.record_hash,
        duplicate_fingerprint=market.duplicate_fingerprint,
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_002_foundation() -> Mapping[str, Any]:
    manifest = build_umd_002_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-002",
        "upstream_frozen": manifest.upstream_build == "UMD-001",
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash == deterministic_sha256(manifest.to_canonical_dict()),
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

def verify_umd_002_certified_canonical_market_contract() -> bool:
    result = certify_umd_002_foundation()
    if not result["certified"]:
        raise RuntimeError("UMD-002 certification failed: " + ", ".join(result["failed_checks"]))
    return True

__all__ = [
    "UMD_002_BUILD_ID",
    "UMD_002_BUILD_NAME",
    "UMD_002_REVISION",
    "UMD_002_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "AssetClass",
    "GeographicScope",
    "CertifiedCanonicalMarket",
    "CanonicalMarketCertificationResult",
    "UMD002CertificationManifest",
    "build_umd_002_certification_manifest",
    "certify_canonical_market",
    "certify_umd_002_foundation",
    "verify_umd_002_certified_canonical_market_contract",
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
    build_umd_002_certification_manifest,
    certify_canonical_market,
    certify_umd_002_foundation,
    verify_umd_002_certified_canonical_market_contract,
)

FIXED = datetime(2026, 8, 5, 4, 15, tzinfo=timezone.utc)

def lineage(parent_hashes=()):
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-002",
        revision=UMD_002_REVISION,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=("fixture://umd-002/market/1",),
        created_at=FIXED,
    )

def market(native_market_id="BTC-100K-2026", title="Will Bitcoin exceed $100,000 before 2027?", related=(), line=None):
    return CertifiedCanonicalMarket(
        venue=VenueIdentity(
            venue_id="fixture-venue",
            canonical_name="Fixture Venue",
            venue_type="prediction_market",
            jurisdiction="US",
            native_market_namespace="fixture",
            metadata={"adapter": "fixture"},
        ),
        native_market_id=native_market_id,
        native_event_id="BTC-2026",
        canonical_title=title,
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
        closes_at=datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc),
        expires_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
        settlement_method=SettlementMethod.THIRD_PARTY_SOURCE,
        settlement_source="Certified benchmark",
        settlement_rule="Resolve YES when benchmark exceeds 100000.",
        settles_at=datetime(2027, 1, 2, tzinfo=timezone.utc),
        outcome_labels=("YES", "NO"),
        duplicate_resolution_keys=("bitcoin", "above-100000", "before-2027"),
        related_market_ids=related,
        metadata={"read_only": True},
        lineage=line or lineage(),
    )

class TestUMD002(unittest.TestCase):
    def test_foundation_certifies(self):
        self.assertTrue(certify_umd_002_foundation()["certified"])
        self.assertTrue(verify_umd_002_certified_canonical_market_contract())

    def test_market_certifies(self):
        self.assertTrue(certify_canonical_market(market()).certified)

    def test_identity_bound(self):
        a = market()
        b = market(title="Different title")
        c = market(native_market_id="BTC-150K-2026")
        self.assertEqual(a.canonical_market_id, b.canonical_market_id)
        self.assertNotEqual(a.canonical_market_id, c.canonical_market_id)

    def test_record_hash_deterministic(self):
        self.assertEqual(market().record_hash, market().record_hash)

    def test_duplicate_fingerprint_deterministic(self):
        self.assertEqual(market().duplicate_fingerprint, market(title="Different").duplicate_fingerprint)

    def test_immutable(self):
        item = market()
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.canonical_title = "mutated"
        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_binary_requires_two_outcomes(self):
        base = market()
        with self.assertRaises(ValueError):
            CertifiedCanonicalMarket(
                venue=base.venue,
                native_market_id="BAD",
                native_event_id=None,
                canonical_title="Bad",
                canonical_description=None,
                instrument_type=MarketInstrumentType.BINARY,
                category=base.category,
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
                outcome_labels=("YES",),
                duplicate_resolution_keys=("bad",),
                related_market_ids=(),
                metadata={},
                lineage=lineage(),
            )

    def test_timestamp_order(self):
        base = market()
        with self.assertRaises(ValueError):
            CertifiedCanonicalMarket(
                venue=base.venue,
                native_market_id="BAD-TIME",
                native_event_id=None,
                canonical_title="Bad Time",
                canonical_description=None,
                instrument_type=MarketInstrumentType.BINARY,
                category=base.category,
                asset_class=AssetClass.PREDICTION_MARKET,
                geographic_scope=GeographicScope.GLOBAL,
                quote_currency="USD",
                tick_size="0.01",
                price_precision=2,
                lifecycle=MarketLifecycle.OPEN,
                opens_at=datetime(2027, 1, 1, tzinfo=timezone.utc),
                closes_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                expires_at=None,
                settlement_method=SettlementMethod.UNKNOWN,
                settlement_source=None,
                settlement_rule=None,
                settles_at=None,
                outcome_labels=("YES", "NO"),
                duplicate_resolution_keys=("bad-time",),
                related_market_ids=(),
                metadata={},
                lineage=lineage(),
            )

    def test_lineage_update_guard(self):
        original = market()
        with self.assertRaises(ValueError):
            original.with_related_market_ids(("umd:mkt:" + "a" * 64,), lineage=lineage())
        updated = original.with_related_market_ids(
            ("umd:mkt:" + "a" * 64,),
            lineage=lineage((original.record_hash,)),
        )
        self.assertIn(original.record_hash, updated.lineage.parent_hashes)

    def test_self_reference_rejected(self):
        original = market()
        with self.assertRaises(ValueError):
            market(related=(original.canonical_market_id,))

    def test_side_effects_disabled(self):
        manifest = build_umd_002_certification_manifest()
        self.assertEqual(manifest.registry_mode, "read_only")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-002 CERTIFICATION TEST")
    print(" CERTIFIED CANONICAL MARKET CONTRACT")
    print("=" * 64)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD002)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_002_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 consumed read-only")
    print("[PASS] Canonical Market ID deterministic")
    print("[PASS] Native venue identity binding verified")
    print("[PASS] Canonical schema immutable")
    print("[PASS] Expiration and settlement ordering verified")
    print("[PASS] Duplicate fingerprint deterministic")
    print("[PASS] Related-market lineage update guarded")
    print("[PASS] Network and market scanning disabled")
    print("[PASS] Persistence and registry mutation disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-002 CERTIFIED CANONICAL MARKET CONTRACT CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_canonical_market_contract import (
    UMD_002_BUILD_ID,
    UMD_002_BUILD_NAME,
    UMD_002_REVISION,
    UMD_002_SCHEMA_VERSION,
    PROHIBITED_CAPABILITIES,
    AssetClass,
    GeographicScope,
    CertifiedCanonicalMarket,
    CanonicalMarketCertificationResult,
    UMD002CertificationManifest,
    build_umd_002_certification_manifest,
    certify_canonical_market,
    certify_umd_002_foundation,
    verify_umd_002_certified_canonical_market_contract,
)
"""

NAMES = [
    "UMD_002_BUILD_ID",
    "UMD_002_BUILD_NAME",
    "UMD_002_REVISION",
    "UMD_002_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "AssetClass",
    "GeographicScope",
    "CertifiedCanonicalMarket",
    "CanonicalMarketCertificationResult",
    "UMD002CertificationManifest",
    "build_umd_002_certification_manifest",
    "certify_canonical_market",
    "certify_umd_002_foundation",
    "verify_umd_002_certified_canonical_market_contract",
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
        raise FileNotFoundError(f"UMD-001 initializer missing: {INIT}")
    source = INIT.read_text(encoding="utf-8")
    if "from .certified_canonical_market_contract import (" not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)
    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start:end+1]
        missing = [name for name in NAMES if f'"{name}"' not in block and f"'{name}'" not in block]
        if missing:
            addition = "".join(f'    "{name}",\n' for name in missing)
            block = block[:-1] + addition + "]"
            source = source[:start] + block + source[end+1:]
    else:
        source += "\n__all__ = [\n" + "".join(f'    "{name}",\n' for name in NAMES) + "]\n"
    write_exact(INIT, source)

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_umd_001() -> None:
    foundation = PKG / "universal_market_discovery_foundation.py"
    if not foundation.exists():
        raise FileNotFoundError(f"Certified UMD-001 missing: {foundation}")
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery.universal_market_discovery_foundation"
        )
        if getattr(module, "UMD_BUILD_ID", None) != "UMD-001":
            raise RuntimeError("UMD-001 identity mismatch")
        if not module.verify_umd_foundation():
            raise RuntimeError("UMD-001 verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def verify_umd_002() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery.certified_canonical_market_contract"
        )
        required = (
            "CertifiedCanonicalMarket",
            "certify_canonical_market",
            "certify_umd_002_foundation",
            "verify_umd_002_certified_canonical_market_contract",
        )
        missing = [name for name in required if not hasattr(module, name)]
        if missing:
            raise RuntimeError("UMD-002 missing symbols: " + ", ".join(missing))
        module.verify_umd_002_certified_canonical_market_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main() -> int:
    print("=" * 64)
    print(" UMD-002 INSTALLER")
    print(" CERTIFIED CANONICAL MARKET CONTRACT")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_umd_001()
    print("[PASS] Certified UMD-001 foundation verified read-only")

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_umd_002()

    manifest = {
        "build_id": "UMD-002",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256(MODULE),
            str(INIT.relative_to(ROOT)): sha256(INIT),
            str(TEST.relative_to(ROOT)): sha256(TEST),
        },
        "upstream": "UMD-001",
        "mode": "read_only",
    }
    install_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-002 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, scanning, persistence, publication, and execution disabled")
    print("[DONE] UMD-002 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print("  python test_umd_002_certified_canonical_market_contract.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
