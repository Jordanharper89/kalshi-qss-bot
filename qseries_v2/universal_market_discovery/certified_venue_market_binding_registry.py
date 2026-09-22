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
