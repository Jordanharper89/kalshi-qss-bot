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
