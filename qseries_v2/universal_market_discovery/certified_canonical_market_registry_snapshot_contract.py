from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_materialized_market_admission_registry import (
    ReadOnlyMaterializedMarketAdmissionRegistry,
)

UMD_016_BUILD_ID = "UMD-016"
UMD_016_BUILD_NAME = "Certified Canonical Market Registry Snapshot Contract"
UMD_016_REVISION = (
    "UMD_016_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_CONTRACT_V1"
)
UMD_016_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_snapshot_persistence",
    "registry_mutation",
    "market_deletion",
    "market_reordering",
    "oracle_memory_mutation",
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


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedCanonicalMarketRegistrySnapshot:
    snapshot_sequence: int
    previous_snapshot_hash: str | None
    source_registry_hash: str
    markets: Tuple[CertifiedCanonicalMarket, ...]
    created_at: datetime
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage
    _by_market_id: Mapping[str, CertifiedCanonicalMarket] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot_sequence, int):
            raise TypeError("snapshot_sequence must be an integer")
        if self.snapshot_sequence < 1:
            raise ValueError("snapshot_sequence must be positive")

        if self.previous_snapshot_hash is None:
            if self.snapshot_sequence != 1:
                raise ValueError(
                    "only the first snapshot may omit previous_snapshot_hash"
                )
        else:
            previous = _text(
                self.previous_snapshot_hash,
                "previous_snapshot_hash",
            ).lower()
            if len(previous) != 64:
                raise ValueError(
                    "previous_snapshot_hash must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in previous
            ):
                raise ValueError(
                    "previous_snapshot_hash must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                "previous_snapshot_hash",
                previous,
            )

        source_hash = _text(
            self.source_registry_hash,
            "source_registry_hash",
        ).lower()
        if len(source_hash) != 64:
            raise ValueError(
                "source_registry_hash must contain 64 hexadecimal characters"
            )
        if any(
            character not in "0123456789abcdef"
            for character in source_hash
        ):
            raise ValueError(
                "source_registry_hash must be lowercase SHA-256 hexadecimal"
            )
        object.__setattr__(
            self,
            "source_registry_hash",
            source_hash,
        )

        ordered_markets = tuple(
            sorted(
                self.markets,
                key=lambda market: market.canonical_market_id,
            )
        )
        object.__setattr__(self, "markets", ordered_markets)

        by_market_id = {
            market.canonical_market_id: market
            for market in ordered_markets
        }
        if len(by_market_id) != len(ordered_markets):
            raise ValueError(
                "snapshot contains duplicate canonical market IDs"
            )
        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )

        object.__setattr__(
            self,
            "created_at",
            _utc(self.created_at, "created_at"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("snapshot lineage must belong to UMD")
        if self.lineage.build_id != UMD_016_BUILD_ID:
            raise ValueError(
                "snapshot lineage must use build_id UMD-016"
            )
        if self.source_registry_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "snapshot lineage must include source registry hash"
            )
        if (
            self.previous_snapshot_hash is not None
            and self.previous_snapshot_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "snapshot lineage must include previous snapshot hash"
            )

    @classmethod
    def from_admission_registry(
        cls,
        registry: ReadOnlyMaterializedMarketAdmissionRegistry,
        *,
        snapshot_sequence: int,
        previous_snapshot_hash: str | None,
        created_at: datetime,
        metadata: Mapping[str, Any],
        lineage: ImmutableLineage,
    ) -> "CertifiedCanonicalMarketRegistrySnapshot":
        return cls(
            snapshot_sequence=snapshot_sequence,
            previous_snapshot_hash=previous_snapshot_hash,
            source_registry_hash=registry.registry_hash,
            markets=registry.complete_market_view(),
            created_at=created_at,
            metadata=metadata,
            lineage=lineage,
        )

    @property
    def snapshot_id(self) -> str:
        return "umd:market-registry-snapshot:" + deterministic_sha256(
            {
                "snapshot_sequence": self.snapshot_sequence,
                "previous_snapshot_hash": self.previous_snapshot_hash,
                "source_registry_hash": self.source_registry_hash,
                "market_record_hashes": tuple(
                    market.record_hash for market in self.markets
                ),
            }
        )

    def get(
        self,
        canonical_market_id: str,
    ) -> CertifiedCanonicalMarket | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def contains(
        self,
        canonical_market_id: str,
    ) -> bool:
        return self.get(canonical_market_id) is not None

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_sequence": self.snapshot_sequence,
            "previous_snapshot_hash": self.previous_snapshot_hash,
            "source_registry_hash": self.source_registry_hash,
            "markets": self.markets,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def snapshot_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyCanonicalMarketRegistrySnapshotChain:
    snapshots: Tuple[CertifiedCanonicalMarketRegistrySnapshot, ...]
    chain_lineage: ImmutableLineage
    _by_snapshot_id: Mapping[
        str,
        CertifiedCanonicalMarketRegistrySnapshot,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.snapshots,
                key=lambda snapshot: snapshot.snapshot_sequence,
            )
        )
        object.__setattr__(self, "snapshots", ordered)

        if self.chain_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("snapshot-chain lineage must belong to UMD")
        if self.chain_lineage.build_id != UMD_016_BUILD_ID:
            raise ValueError(
                "snapshot-chain lineage must use build_id UMD-016"
            )

        by_snapshot_id = {}
        previous_snapshot = None

        for expected_sequence, snapshot in enumerate(
            ordered,
            start=1,
        ):
            if snapshot.snapshot_sequence != expected_sequence:
                raise ValueError(
                    "snapshot sequence must be contiguous and start at 1"
                )

            if previous_snapshot is None:
                if snapshot.previous_snapshot_hash is not None:
                    raise ValueError(
                        "first snapshot must not have previous hash"
                    )
            else:
                if (
                    snapshot.previous_snapshot_hash
                    != previous_snapshot.snapshot_hash
                ):
                    raise ValueError(
                        "snapshot previous-hash chain mismatch"
                    )

                previous_market_ids = {
                    market.canonical_market_id
                    for market in previous_snapshot.markets
                }
                current_market_ids = {
                    market.canonical_market_id
                    for market in snapshot.markets
                }
                if not previous_market_ids.issubset(
                    current_market_ids
                ):
                    raise ValueError(
                        "snapshot chain cannot delete canonical markets"
                    )

            if snapshot.snapshot_id in by_snapshot_id:
                raise ValueError("duplicate snapshot ID")

            by_snapshot_id[snapshot.snapshot_id] = snapshot
            previous_snapshot = snapshot

        object.__setattr__(
            self,
            "_by_snapshot_id",
            MappingProxyType(by_snapshot_id),
        )

    def latest(
        self,
    ) -> CertifiedCanonicalMarketRegistrySnapshot | None:
        if not self.snapshots:
            return None
        return self.snapshots[-1]

    def get(
        self,
        snapshot_id: str,
    ) -> CertifiedCanonicalMarketRegistrySnapshot | None:
        return self._by_snapshot_id.get(
            _text(snapshot_id, "snapshot_id")
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "chain_mode": "append_only_read_only",
            "snapshots": self.snapshots,
            "chain_lineage": self.chain_lineage,
        }

    @property
    def chain_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD016CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    snapshot_mode: str
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
            "snapshot_mode": self.snapshot_mode,
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


def build_umd_016_certification_manifest() -> UMD016CertificationManifest:
    return UMD016CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_016_BUILD_ID,
        build_name=UMD_016_BUILD_NAME,
        revision=UMD_016_REVISION,
        schema_version=UMD_016_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 16)
        ),
        snapshot_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_canonical_market_registry_snapshot_chain(
    chain: ReadOnlyCanonicalMarketRegistrySnapshotChain,
) -> Mapping[str, Any]:
    checks = {
        "snapshot_ids_unique": len(
            {
                snapshot.snapshot_id
                for snapshot in chain.snapshots
            }
        )
        == len(chain.snapshots),
        "sequence_contiguous": tuple(
            snapshot.snapshot_sequence
            for snapshot in chain.snapshots
        )
        == tuple(range(1, len(chain.snapshots) + 1)),
        "markets_never_deleted": all(
            {
                market.canonical_market_id
                for market in prior.markets
            }.issubset(
                {
                    market.canonical_market_id
                    for market in current.markets
                }
            )
            for prior, current in zip(
                chain.snapshots,
                chain.snapshots[1:],
            )
        ),
        "deterministic_replay": (
            chain.chain_hash
            == deterministic_sha256(chain.to_canonical_dict())
        ),
        "read_only_index": isinstance(
            chain._by_snapshot_id,
            MappingProxyType,
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    latest = chain.latest()

    return MappingProxyType(
        {
            "certified": not failed,
            "chain_hash": chain.chain_hash,
            "snapshot_count": len(chain.snapshots),
            "latest_market_count": (
                0 if latest is None else len(latest.markets)
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_016_foundation() -> Mapping[str, Any]:
    manifest = build_umd_016_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-016",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}" for number in range(1, 16)
        ),
        "append_only_read_only": (
            manifest.snapshot_mode
            == "append_only_read_only"
        ),
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(manifest.to_canonical_dict())
        ),
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


def verify_umd_016_certified_canonical_market_registry_snapshot_contract() -> bool:
    result = certify_umd_016_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-016 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_016_BUILD_ID",
    "UMD_016_BUILD_NAME",
    "UMD_016_REVISION",
    "UMD_016_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedCanonicalMarketRegistrySnapshot",
    "ReadOnlyCanonicalMarketRegistrySnapshotChain",
    "UMD016CertificationManifest",
    "build_umd_016_certification_manifest",
    "certify_canonical_market_registry_snapshot_chain",
    "certify_umd_016_foundation",
    "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
]
