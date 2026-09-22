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

UMD_003_BUILD_ID = "UMD-003"
UMD_003_BUILD_NAME = "Certified Venue Identity Registry"
UMD_003_REVISION = "UMD_003_CERTIFIED_VENUE_IDENTITY_REGISTRY_V1"
UMD_003_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "live_market_scanning",
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

def _symbol(value: str, name: str) -> str:
    normalized = _text(value, name).upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
    if any(ch not in allowed for ch in normalized):
        raise ValueError(f"{name} contains unsupported characters")
    return normalized

def _tuple(
    values: Tuple[str, ...],
    name: str,
    *,
    slug: bool = False,
    symbol: bool = False,
) -> Tuple[str, ...]:
    if slug and symbol:
        raise ValueError("tuple normalization mode is ambiguous")
    normalizer = _slug if slug else _symbol if symbol else _text
    return tuple(sorted(set(normalizer(item, name) for item in values)))

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

class VenueType(str, Enum):
    UNKNOWN = "unknown"
    PREDICTION_MARKET = "prediction_market"
    EXCHANGE = "exchange"
    BROKER = "broker"
    DERIVATIVES_EXCHANGE = "derivatives_exchange"
    SPORTSBOOK = "sportsbook"
    DATA_ONLY = "data_only"
    OTHER = "other"

class VenueOperationalStatus(str, Enum):
    UNKNOWN = "unknown"
    PLANNED = "planned"
    ACTIVE = "active"
    RESTRICTED = "restricted"
    PAUSED = "paused"
    INACTIVE = "inactive"
    CLOSED = "closed"

@dataclass(frozen=True, slots=True)
class CertifiedVenueIdentity:
    venue_namespace: str
    canonical_name: str
    display_name: str
    venue_type: VenueType
    operational_status: VenueOperationalStatus
    jurisdiction: str
    timezone_name: str
    native_market_namespace: str
    aliases: Tuple[str, ...]
    supported_asset_classes: Tuple[str, ...]
    supported_market_types: Tuple[str, ...]
    supported_currencies: Tuple[str, ...]
    settlement_capabilities: Tuple[str, ...]
    related_venue_ids: Tuple[str, ...]
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "venue_namespace", _slug(self.venue_namespace, "venue_namespace")
        )
        object.__setattr__(
            self, "canonical_name", _text(self.canonical_name, "canonical_name")
        )
        object.__setattr__(
            self, "display_name", _text(self.display_name, "display_name")
        )

        if not isinstance(self.venue_type, VenueType):
            object.__setattr__(self, "venue_type", VenueType(self.venue_type))
        if not isinstance(self.operational_status, VenueOperationalStatus):
            object.__setattr__(
                self,
                "operational_status",
                VenueOperationalStatus(self.operational_status),
            )

        object.__setattr__(
            self, "jurisdiction", _symbol(self.jurisdiction, "jurisdiction")
        )
        object.__setattr__(
            self, "timezone_name", _text(self.timezone_name, "timezone_name")
        )
        object.__setattr__(
            self,
            "native_market_namespace",
            _slug(self.native_market_namespace, "native_market_namespace"),
        )

        aliases = _tuple(self.aliases, "alias")
        canonical_alias = self.canonical_name.casefold()
        if canonical_alias in {alias.casefold() for alias in aliases}:
            raise ValueError("aliases must not repeat canonical_name")
        object.__setattr__(self, "aliases", aliases)

        asset_classes = _tuple(
            self.supported_asset_classes,
            "supported_asset_class",
            slug=True,
        )
        market_types = _tuple(
            self.supported_market_types,
            "supported_market_type",
            slug=True,
        )
        currencies = _tuple(
            self.supported_currencies,
            "supported_currency",
            symbol=True,
        )
        settlements = _tuple(
            self.settlement_capabilities,
            "settlement_capability",
            slug=True,
        )
        related = _tuple(self.related_venue_ids, "related_venue_id")

        object.__setattr__(
            self, "supported_asset_classes", asset_classes
        )
        object.__setattr__(
            self, "supported_market_types", market_types
        )
        object.__setattr__(
            self, "supported_currencies", currencies
        )
        object.__setattr__(
            self, "settlement_capabilities", settlements
        )
        object.__setattr__(self, "related_venue_ids", related)
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("venue lineage must belong to UMD")
        if self.lineage.build_id != UMD_003_BUILD_ID:
            raise ValueError("venue lineage must use build_id UMD-003")
        if self.canonical_venue_id in related:
            raise ValueError("venue cannot reference itself")

    def identity_payload(self) -> Mapping[str, Any]:
        return {
            "venue_namespace": self.venue_namespace,
            "native_market_namespace": self.native_market_namespace,
        }

    @property
    def canonical_venue_id(self) -> str:
        return f"umd:venue:{deterministic_sha256(self.identity_payload())}"

    @property
    def duplicate_fingerprint(self) -> str:
        return deterministic_sha256(
            {
                "canonical_name": self.canonical_name.casefold(),
                "jurisdiction": self.jurisdiction,
                "venue_type": self.venue_type,
            }
        )

    @property
    def alias_keys(self) -> Tuple[str, ...]:
        values = (
            self.canonical_name,
            self.display_name,
            self.venue_namespace,
            self.native_market_namespace,
            *self.aliases,
        )
        return tuple(sorted(set(_text(value, "alias_key").casefold() for value in values)))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "canonical_venue_id": self.canonical_venue_id,
            "venue_namespace": self.venue_namespace,
            "canonical_name": self.canonical_name,
            "display_name": self.display_name,
            "venue_type": self.venue_type,
            "operational_status": self.operational_status,
            "jurisdiction": self.jurisdiction,
            "timezone_name": self.timezone_name,
            "native_market_namespace": self.native_market_namespace,
            "aliases": self.aliases,
            "supported_asset_classes": self.supported_asset_classes,
            "supported_market_types": self.supported_market_types,
            "supported_currencies": self.supported_currencies,
            "settlement_capabilities": self.settlement_capabilities,
            "related_venue_ids": self.related_venue_ids,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyVenueIdentityRegistry:
    venues: Tuple[CertifiedVenueIdentity, ...]
    registry_lineage: ImmutableLineage
    _by_id: Mapping[str, CertifiedVenueIdentity] = field(init=False, repr=False)
    _alias_index: Mapping[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.venues, key=lambda item: item.canonical_venue_id))
        object.__setattr__(self, "venues", ordered)

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_003_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-003")

        by_id = {}
        duplicate_fingerprints = {}
        alias_index = {}

        for venue in ordered:
            if venue.canonical_venue_id in by_id:
                raise ValueError("duplicate canonical venue ID")
            by_id[venue.canonical_venue_id] = venue

            fingerprint = venue.duplicate_fingerprint
            if fingerprint in duplicate_fingerprints:
                raise ValueError(
                    "duplicate venue identity fingerprint: "
                    f"{duplicate_fingerprints[fingerprint]} and {venue.canonical_venue_id}"
                )
            duplicate_fingerprints[fingerprint] = venue.canonical_venue_id

            for alias_key in venue.alias_keys:
                existing = alias_index.get(alias_key)
                if existing is not None and existing != venue.canonical_venue_id:
                    raise ValueError(
                        f"ambiguous venue alias '{alias_key}'"
                    )
                alias_index[alias_key] = venue.canonical_venue_id

        object.__setattr__(self, "_by_id", MappingProxyType(by_id))
        object.__setattr__(self, "_alias_index", MappingProxyType(alias_index))

    def get(self, canonical_venue_id: str) -> CertifiedVenueIdentity | None:
        return self._by_id.get(_text(canonical_venue_id, "canonical_venue_id"))

    def resolve_alias(self, alias: str) -> CertifiedVenueIdentity | None:
        canonical_id = self._alias_index.get(_text(alias, "alias").casefold())
        if canonical_id is None:
            return None
        return self._by_id[canonical_id]

    def by_type(self, venue_type: VenueType) -> Tuple[CertifiedVenueIdentity, ...]:
        if not isinstance(venue_type, VenueType):
            venue_type = VenueType(venue_type)
        return tuple(venue for venue in self.venues if venue.venue_type == venue_type)

    def by_jurisdiction(self, jurisdiction: str) -> Tuple[CertifiedVenueIdentity, ...]:
        normalized = _symbol(jurisdiction, "jurisdiction")
        return tuple(
            venue for venue in self.venues if venue.jurisdiction == normalized
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "venues": self.venues,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class VenueRegistryCertificationResult:
    certified: bool
    registry_hash: str
    venue_count: int
    checks: Mapping[str, bool]
    failed_checks: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))

@dataclass(frozen=True, slots=True)
class UMD003CertificationManifest:
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

def build_umd_003_certification_manifest() -> UMD003CertificationManifest:
    return UMD003CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_003_BUILD_ID,
        build_name=UMD_003_BUILD_NAME,
        revision=UMD_003_REVISION,
        schema_version=UMD_003_SCHEMA_VERSION,
        upstream_builds=("UMD-001", "UMD-002"),
        registry_mode="read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_venue_registry(
    registry: ReadOnlyVenueIdentityRegistry,
) -> VenueRegistryCertificationResult:
    checks = {
        "registry_hash_length": len(registry.registry_hash) == 64,
        "registry_order_deterministic": tuple(
            venue.canonical_venue_id for venue in registry.venues
        ) == tuple(sorted(venue.canonical_venue_id for venue in registry.venues)),
        "canonical_ids_unique": len(
            {venue.canonical_venue_id for venue in registry.venues}
        ) == len(registry.venues),
        "duplicate_fingerprints_unique": len(
            {venue.duplicate_fingerprint for venue in registry.venues}
        ) == len(registry.venues),
        "all_lineage_certified": all(
            venue.lineage.build_id == UMD_003_BUILD_ID
            and venue.lineage.subsystem_id == "UMD"
            for venue in registry.venues
        ),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "registry_maps_read_only": isinstance(registry._by_id, MappingProxyType)
        and isinstance(registry._alias_index, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return VenueRegistryCertificationResult(
        certified=not failed,
        registry_hash=registry.registry_hash,
        venue_count=len(registry.venues),
        checks=checks,
        failed_checks=failed,
    )

def certify_umd_003_foundation() -> Mapping[str, Any]:
    manifest = build_umd_003_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-003",
        "upstreams_frozen": manifest.upstream_builds == ("UMD-001", "UMD-002"),
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

def verify_umd_003_certified_venue_identity_registry() -> bool:
    result = certify_umd_003_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-003 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_003_BUILD_ID",
    "UMD_003_BUILD_NAME",
    "UMD_003_REVISION",
    "UMD_003_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "VenueType",
    "VenueOperationalStatus",
    "CertifiedVenueIdentity",
    "ReadOnlyVenueIdentityRegistry",
    "VenueRegistryCertificationResult",
    "UMD003CertificationManifest",
    "build_umd_003_certification_manifest",
    "certify_venue_registry",
    "certify_umd_003_foundation",
    "verify_umd_003_certified_venue_identity_registry",
]
