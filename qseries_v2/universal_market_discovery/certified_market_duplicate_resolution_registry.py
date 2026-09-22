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
