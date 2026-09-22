from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_045_venue_discovery_source_contract import (
    CertifiedVenueDiscoverySourceContract,
)

UMD_046_BUILD_ID = "UMD-046"
UMD_046_BUILD_NAME = "Certified Venue Discovery Source Registry"
UMD_046_REVISION = "UMD_046_CERTIFIED_VENUE_DISCOVERY_SOURCE_REGISTRY_V1"
UMD_046_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "market_scanning",
    "automatic_discovery",
    "automatic_registration",
    "registry_mutation",
    "registry_persistence",
    "publication",
    "order_submission",
    "trade_execution",
)


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedVenueDiscoverySourceRegistry:
    sources: Tuple[CertifiedVenueDiscoverySourceContract, ...]
    registry_metadata: Mapping[str, Any]
    lineage: ImmutableLineage
    _by_source_id: Mapping[str, CertifiedVenueDiscoverySourceContract] = field(
        init=False,
        repr=False,
    )
    _by_venue_adapter: Mapping[
        str,
        CertifiedVenueDiscoverySourceContract,
    ] = field(init=False, repr=False)
    _source_ids_by_venue: Mapping[str, Tuple[str, ...]] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.sources, tuple):
            object.__setattr__(self, "sources", tuple(self.sources))

        ordered = tuple(
            sorted(
                self.sources,
                key=lambda source: (
                    source.canonical_venue_id,
                    source.adapter_key,
                    source.source_id,
                ),
            )
        )
        object.__setattr__(self, "sources", ordered)

        metadata = MappingProxyType(
            dict(
                sorted(
                    (str(key), value)
                    for key, value in self.registry_metadata.items()
                )
            )
        )
        object.__setattr__(self, "registry_metadata", metadata)

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.lineage.build_id != UMD_046_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-046")

        by_source_id = {}
        by_venue_adapter = {}
        source_ids_by_venue = {}

        for source in ordered:
            if not isinstance(source, CertifiedVenueDiscoverySourceContract):
                raise TypeError(
                    "sources must contain certified UMD-045 source contracts"
                )
            if source.read_only is not True:
                raise ValueError("all registered sources must be read-only")
            if source.contract_hash not in self.lineage.parent_hashes:
                raise ValueError(
                    "registry lineage must include every source contract hash"
                )
            if source.source_id in by_source_id:
                raise ValueError("duplicate venue discovery source ID")

            venue_adapter_key = (
                f"{source.canonical_venue_id}:{source.adapter_key}"
            )
            if venue_adapter_key in by_venue_adapter:
                raise ValueError(
                    "duplicate canonical venue and adapter binding"
                )

            by_source_id[source.source_id] = source
            by_venue_adapter[venue_adapter_key] = source
            source_ids_by_venue.setdefault(
                source.canonical_venue_id,
                [],
            ).append(source.source_id)

        object.__setattr__(
            self,
            "_by_source_id",
            MappingProxyType(by_source_id),
        )
        object.__setattr__(
            self,
            "_by_venue_adapter",
            MappingProxyType(by_venue_adapter),
        )
        object.__setattr__(
            self,
            "_source_ids_by_venue",
            MappingProxyType(
                {
                    venue_id: tuple(sorted(source_ids))
                    for venue_id, source_ids in source_ids_by_venue.items()
                }
            ),
        )

    @property
    def registry_id(self) -> str:
        return "umd:venue-discovery-source-registry:" + deterministic_sha256(
            {
                "ordered_source_ids": tuple(
                    source.source_id
                    for source in self.sources
                ),
                "ordered_contract_hashes": tuple(
                    source.contract_hash
                    for source in self.sources
                ),
            }
        )

    def get(
        self,
        source_id: str,
    ) -> CertifiedVenueDiscoverySourceContract | None:
        return self._by_source_id.get(_text(source_id, "source_id"))

    def get_by_venue_adapter(
        self,
        canonical_venue_id: str,
        adapter_key: str,
    ) -> CertifiedVenueDiscoverySourceContract | None:
        key = (
            f"{_text(canonical_venue_id, 'canonical_venue_id').upper()}:"
            f"{_text(adapter_key, 'adapter_key').upper().replace('-', '_')}"
        )
        return self._by_venue_adapter.get(key)

    def list_by_venue(
        self,
        canonical_venue_id: str,
    ) -> Tuple[CertifiedVenueDiscoverySourceContract, ...]:
        venue_id = _text(
            canonical_venue_id,
            "canonical_venue_id",
        ).upper()
        source_ids = self._source_ids_by_venue.get(venue_id, ())
        return tuple(self._by_source_id[source_id] for source_id in source_ids)

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_id": self.registry_id,
            "sources": self.sources,
            "registry_metadata": self.registry_metadata,
            "lineage": self.lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD046CertificationManifest:
    subsystem_id: str
    build_id: str
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


def build_umd_046_certification_manifest() -> UMD046CertificationManifest:
    return UMD046CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_046_BUILD_ID,
        revision=UMD_046_REVISION,
        schema_version=UMD_046_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 46)
        ),
        registry_mode="deterministic_read_only_registry",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_venue_discovery_source_registry(
    registry: CertifiedVenueDiscoverySourceRegistry,
) -> Mapping[str, Any]:
    if not isinstance(registry, CertifiedVenueDiscoverySourceRegistry):
        raise TypeError("registry must be a certified UMD-046 registry")

    checks = {
        "source_ids_unique": (
            len({source.source_id for source in registry.sources})
            == len(registry.sources)
        ),
        "venue_adapter_bindings_unique": (
            len(
                {
                    (
                        source.canonical_venue_id,
                        source.adapter_key,
                    )
                    for source in registry.sources
                }
            )
            == len(registry.sources)
        ),
        "all_sources_read_only": all(
            source.read_only is True
            for source in registry.sources
        ),
        "all_source_lineage_bound": all(
            source.contract_hash in registry.lineage.parent_hashes
            for source in registry.sources
        ),
        "deterministic_registry_hash": (
            registry.registry_hash
            == deterministic_sha256(registry.to_canonical_dict())
        ),
        "read_only_indexes": (
            isinstance(registry._by_source_id, MappingProxyType)
            and isinstance(registry._by_venue_adapter, MappingProxyType)
            and isinstance(registry._source_ids_by_venue, MappingProxyType)
        ),
        "network_not_invoked": True,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)

    return MappingProxyType(
        {
            "certified": not failed,
            "registry_id": registry.registry_id,
            "registry_hash": registry.registry_hash,
            "source_count": len(registry.sources),
            "venue_count": len(registry._source_ids_by_venue),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_046_foundation() -> Mapping[str, Any]:
    manifest = build_umd_046_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-046",
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}" for number in range(1, 46)
            )
        ),
        "registry_mode": (
            manifest.registry_mode
            == "deterministic_read_only_registry"
        ),
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest": (
            manifest.manifest_hash
            == deterministic_sha256(manifest.to_canonical_dict())
        ),
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


def verify_umd_046_venue_discovery_source_registry() -> bool:
    result = certify_umd_046_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-046 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
