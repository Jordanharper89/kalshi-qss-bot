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
from .certified_related_market_graph_registry import (
    ReadOnlyRelatedMarketGraphRegistry,
)

UMD_011_BUILD_ID = "UMD-011"
UMD_011_BUILD_NAME = "Certified Incremental Discovery Batch Contract"
UMD_011_REVISION = "UMD_011_CERTIFIED_INCREMENTAL_DISCOVERY_BATCH_CONTRACT_V1"
UMD_011_SCHEMA_VERSION = "1.0.0"

def _text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    value = " ".join(value.strip().split())
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value

def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((str(k), v) for k, v in value.items())))

@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryCursor:
    source_id: str
    partition_key: str
    cursor_value: str
    observed_at: datetime
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id").lower())
        object.__setattr__(
            self,
            "partition_key",
            _text(self.partition_key, "partition_key").lower(),
        )
        object.__setattr__(
            self,
            "cursor_value",
            _text(self.cursor_value, "cursor_value"),
        )
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, "observed_at"),
        )
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("cursor lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("cursor lineage must use build_id UMD-011")

    @property
    def cursor_id(self) -> str:
        return "umd:cursor:" + deterministic_sha256({
            "source_id": self.source_id,
            "partition_key": self.partition_key,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "cursor_id": self.cursor_id,
            "source_id": self.source_id,
            "partition_key": self.partition_key,
            "cursor_value": self.cursor_value,
            "observed_at": self.observed_at,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryCandidate:
    source_id: str
    source_market_key: str
    market: CertifiedCanonicalMarket
    discovered_at: datetime
    payload_hash: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id").lower())
        object.__setattr__(
            self,
            "source_market_key",
            _text(self.source_market_key, "source_market_key"),
        )
        object.__setattr__(
            self,
            "discovered_at",
            _utc(self.discovered_at, "discovered_at"),
        )
        payload_hash = _text(self.payload_hash, "payload_hash").lower()
        if len(payload_hash) != 64 or any(ch not in "0123456789abcdef" for ch in payload_hash):
            raise ValueError("payload_hash must be lowercase SHA-256 hex")
        object.__setattr__(self, "payload_hash", payload_hash)
        object.__setattr__(self, "metadata", _freeze(self.metadata))
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("candidate lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("candidate lineage must use build_id UMD-011")

    @property
    def candidate_id(self) -> str:
        return "umd:candidate:" + deterministic_sha256({
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "payload_hash": self.payload_hash,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "canonical_market_id": self.market.canonical_market_id,
            "market_record_hash": self.market.record_hash,
            "discovered_at": self.discovered_at,
            "payload_hash": self.payload_hash,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class CertifiedIncrementalDiscoveryBatch:
    source_id: str
    batch_sequence: int
    previous_batch_hash: str | None
    start_cursor: CertifiedDiscoveryCursor | None
    end_cursor: CertifiedDiscoveryCursor
    candidates: Tuple[CertifiedDiscoveryCandidate, ...]
    created_at: datetime
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        source_id = _text(self.source_id, "source_id").lower()
        object.__setattr__(self, "source_id", source_id)
        if not isinstance(self.batch_sequence, int) or self.batch_sequence < 1:
            raise ValueError("batch_sequence must be a positive integer")

        if self.previous_batch_hash is not None:
            previous = _text(self.previous_batch_hash, "previous_batch_hash").lower()
            if len(previous) != 64 or any(ch not in "0123456789abcdef" for ch in previous):
                raise ValueError("previous_batch_hash must be lowercase SHA-256 hex")
            object.__setattr__(self, "previous_batch_hash", previous)
        elif self.batch_sequence != 1:
            raise ValueError("non-initial batches require previous_batch_hash")

        if self.start_cursor is not None and self.start_cursor.source_id != source_id:
            raise ValueError("start_cursor source mismatch")
        if self.end_cursor.source_id != source_id:
            raise ValueError("end_cursor source mismatch")

        candidates = tuple(sorted(self.candidates, key=lambda item: item.candidate_id))
        if any(candidate.source_id != source_id for candidate in candidates):
            raise ValueError("candidate source mismatch")
        if len({candidate.candidate_id for candidate in candidates}) != len(candidates):
            raise ValueError("duplicate candidate ID")
        if len({candidate.source_market_key for candidate in candidates}) != len(candidates):
            raise ValueError("duplicate source_market_key in batch")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("batch lineage must belong to UMD")
        if self.lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("batch lineage must use build_id UMD-011")
        if self.batch_sequence > 1 and self.previous_batch_hash not in self.lineage.parent_hashes:
            raise ValueError("lineage must include previous_batch_hash")

    @property
    def batch_id(self) -> str:
        return "umd:batch:" + deterministic_sha256({
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "previous_batch_hash": self.previous_batch_hash,
            "end_cursor_hash": self.end_cursor.record_hash,
        })

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "previous_batch_hash": self.previous_batch_hash,
            "start_cursor": self.start_cursor,
            "end_cursor": self.end_cursor,
            "candidates": self.candidates,
            "created_at": self.created_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def batch_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class ReadOnlyIncrementalDiscoveryBatchRegistry:
    batches: Tuple[CertifiedIncrementalDiscoveryBatch, ...]
    graph_registry: ReadOnlyRelatedMarketGraphRegistry
    registry_lineage: ImmutableLineage
    _by_batch_id: Mapping[str, CertifiedIncrementalDiscoveryBatch] = field(init=False, repr=False)
    _latest_by_source: Mapping[str, CertifiedIncrementalDiscoveryBatch] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        batches = tuple(sorted(self.batches, key=lambda item: (item.source_id, item.batch_sequence)))
        object.__setattr__(self, "batches", batches)
        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_011_BUILD_ID:
            raise ValueError("registry lineage must use build_id UMD-011")

        known_market_ids = {
            market.canonical_market_id
            for market in self.graph_registry.markets
        }
        by_batch_id = {}
        latest_by_source = {}
        seen_source_market_keys = set()

        for batch in batches:
            if batch.batch_id in by_batch_id:
                raise ValueError("duplicate batch ID")

            previous = latest_by_source.get(batch.source_id)
            if previous is None:
                if batch.batch_sequence != 1 or batch.previous_batch_hash is not None:
                    raise ValueError("source chain must begin at sequence 1")
            else:
                if batch.batch_sequence != previous.batch_sequence + 1:
                    raise ValueError("source batch sequence must be contiguous")
                if batch.previous_batch_hash != previous.batch_hash:
                    raise ValueError("previous batch hash mismatch")
                if batch.start_cursor is None:
                    raise ValueError("continuation batch requires start_cursor")
                if batch.start_cursor.record_hash != previous.end_cursor.record_hash:
                    raise ValueError("cursor continuity mismatch")

            for candidate in batch.candidates:
                key = (candidate.source_id, candidate.source_market_key)
                if key in seen_source_market_keys:
                    raise ValueError("source market key replayed across batches")
                seen_source_market_keys.add(key)
                if candidate.market.canonical_market_id in known_market_ids:
                    raise ValueError("candidate market already exists in certified graph")

            by_batch_id[batch.batch_id] = batch
            latest_by_source[batch.source_id] = batch

        object.__setattr__(self, "_by_batch_id", MappingProxyType(by_batch_id))
        object.__setattr__(self, "_latest_by_source", MappingProxyType(latest_by_source))

    def get(self, batch_id: str) -> CertifiedIncrementalDiscoveryBatch | None:
        return self._by_batch_id.get(_text(batch_id, "batch_id"))

    def latest_for_source(
        self,
        source_id: str,
    ) -> CertifiedIncrementalDiscoveryBatch | None:
        return self._latest_by_source.get(_text(source_id, "source_id").lower())

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "batches": self.batches,
            "graph_registry_hash": self.graph_registry.registry_hash,
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())

@dataclass(frozen=True, slots=True)
class UMD011CertificationManifest:
    build_id: str
    revision: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
    network_enabled: bool
    persistence_enabled: bool
    mutation_enabled: bool
    publication_enabled: bool
    execution_enabled: bool

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "build_id": self.build_id,
            "revision": self.revision,
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

def build_umd_011_certification_manifest() -> UMD011CertificationManifest:
    return UMD011CertificationManifest(
        build_id=UMD_011_BUILD_ID,
        revision=UMD_011_REVISION,
        upstream_builds=tuple(f"UMD-{number:03d}" for number in range(1, 11)),
        registry_mode="read_only",
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )

def certify_incremental_discovery_batch_registry(
    registry: ReadOnlyIncrementalDiscoveryBatchRegistry,
) -> Mapping[str, Any]:
    checks = {
        "batch_ids_unique": len({batch.batch_id for batch in registry.batches}) == len(registry.batches),
        "deterministic_replay": registry.registry_hash
        == deterministic_sha256(registry.to_canonical_dict()),
        "read_only_indexes": isinstance(registry._by_batch_id, MappingProxyType)
        and isinstance(registry._latest_by_source, MappingProxyType),
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    return MappingProxyType({
        "certified": not failed,
        "registry_hash": registry.registry_hash,
        "batch_count": len(registry.batches),
        "checks": MappingProxyType(checks),
        "failed_checks": failed,
    })

def certify_umd_011_foundation() -> Mapping[str, Any]:
    manifest = build_umd_011_certification_manifest()
    checks = {
        "build_identity": manifest.build_id == "UMD-011",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(f"UMD-{number:03d}" for number in range(1, 11)),
        "read_only": manifest.registry_mode == "read_only",
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
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

def verify_umd_011_certified_incremental_discovery_batch_contract() -> bool:
    result = certify_umd_011_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-011 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True

__all__ = [
    "UMD_011_BUILD_ID",
    "UMD_011_BUILD_NAME",
    "UMD_011_REVISION",
    "UMD_011_SCHEMA_VERSION",
    "CertifiedDiscoveryCursor",
    "CertifiedDiscoveryCandidate",
    "CertifiedIncrementalDiscoveryBatch",
    "ReadOnlyIncrementalDiscoveryBatchRegistry",
    "UMD011CertificationManifest",
    "build_umd_011_certification_manifest",
    "certify_incremental_discovery_batch_registry",
    "certify_umd_011_foundation",
    "verify_umd_011_certified_incremental_discovery_batch_contract",
]
