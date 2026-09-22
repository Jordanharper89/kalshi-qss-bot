from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_registry_snapshot_contract import (
    CertifiedCanonicalMarketRegistrySnapshot,
)
from .certified_canonical_market_registry_snapshot_admission_ledger import (
    CertifiedSnapshotAdmissionLedgerEntry,
)

UMD_019_BUILD_ID = "UMD-019"
UMD_019_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Activation Contract"
)
UMD_019_REVISION = (
    "UMD_019_CERTIFIED_CANONICAL_MARKET_REGISTRY_"
    "SNAPSHOT_ACTIVATION_CONTRACT_V1"
)
UMD_019_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_activation_commit",
    "snapshot_persistence",
    "active_registry_mutation",
    "market_deletion",
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
class CertifiedCanonicalMarketRegistrySnapshotActivation:
    snapshot: CertifiedCanonicalMarketRegistrySnapshot
    admission_entry: CertifiedSnapshotAdmissionLedgerEntry
    activated_at: datetime
    activation_reason: str
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not self.admission_entry.decision.admitted:
            raise ValueError(
                "only admitted snapshots may be activated"
            )

        decision = self.admission_entry.decision
        if decision.snapshot_id != self.snapshot.snapshot_id:
            raise ValueError(
                "admission decision snapshot_id does not match snapshot"
            )
        if decision.snapshot_hash != self.snapshot.snapshot_hash:
            raise ValueError(
                "admission decision snapshot_hash does not match snapshot"
            )
        if (
            decision.snapshot_sequence
            != self.snapshot.snapshot_sequence
        ):
            raise ValueError(
                "admission decision snapshot_sequence does not match snapshot"
            )

        object.__setattr__(
            self,
            "activated_at",
            _utc(self.activated_at, "activated_at"),
        )
        object.__setattr__(
            self,
            "activation_reason",
            _text(self.activation_reason, "activation_reason").lower(),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("activation lineage must belong to UMD")
        if self.lineage.build_id != UMD_019_BUILD_ID:
            raise ValueError(
                "activation lineage must use build_id UMD-019"
            )

        required_parents = {
            self.snapshot.snapshot_hash,
            self.admission_entry.entry_hash,
            self.admission_entry.decision.record_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "activation lineage is missing required parent hashes"
            )

    @property
    def activation_id(self) -> str:
        return "umd:snapshot-activation:" + deterministic_sha256(
            {
                "snapshot_id": self.snapshot.snapshot_id,
                "snapshot_hash": self.snapshot.snapshot_hash,
                "admission_entry_id": self.admission_entry.entry_id,
                "activation_reason": self.activation_reason,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "activation_id": self.activation_id,
            "snapshot_id": self.snapshot.snapshot_id,
            "snapshot_hash": self.snapshot.snapshot_hash,
            "snapshot_sequence": self.snapshot.snapshot_sequence,
            "admission_entry_id": self.admission_entry.entry_id,
            "admission_entry_hash": self.admission_entry.entry_hash,
            "activated_at": self.activated_at,
            "activation_reason": self.activation_reason,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def activation_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveCanonicalMarketRegistry:
    activation: CertifiedCanonicalMarketRegistrySnapshotActivation

    @property
    def snapshot(self) -> CertifiedCanonicalMarketRegistrySnapshot:
        return self.activation.snapshot

    @property
    def active_snapshot_id(self) -> str:
        return self.snapshot.snapshot_id

    @property
    def active_snapshot_hash(self) -> str:
        return self.snapshot.snapshot_hash

    @property
    def market_count(self) -> int:
        return len(self.snapshot.markets)

    def get(self, canonical_market_id: str):
        return self.snapshot.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def contains(self, canonical_market_id: str) -> bool:
        return self.snapshot.contains(
            _text(canonical_market_id, "canonical_market_id")
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "single_active_read_only_snapshot",
            "activation": self.activation,
            "active_snapshot_id": self.active_snapshot_id,
            "active_snapshot_hash": self.active_snapshot_hash,
            "market_count": self.market_count,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD019CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    activation_mode: str
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
            "activation_mode": self.activation_mode,
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


def build_umd_019_certification_manifest() -> UMD019CertificationManifest:
    return UMD019CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_019_BUILD_ID,
        build_name=UMD_019_BUILD_NAME,
        revision=UMD_019_REVISION,
        schema_version=UMD_019_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 19)
        ),
        activation_mode="single_active_read_only_snapshot",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_canonical_market_registry(
    registry: ReadOnlyActiveCanonicalMarketRegistry,
) -> Mapping[str, Any]:
    checks = {
        "admission_is_approved": (
            registry.activation.admission_entry.decision.admitted
        ),
        "snapshot_identity_matches_decision": (
            registry.activation.admission_entry.decision.snapshot_id
            == registry.active_snapshot_id
        ),
        "snapshot_hash_matches_decision": (
            registry.activation.admission_entry.decision.snapshot_hash
            == registry.active_snapshot_hash
        ),
        "market_count_matches_snapshot": (
            registry.market_count
            == len(registry.snapshot.markets)
        ),
        "deterministic_replay": (
            registry.registry_hash
            == deterministic_sha256(registry.to_canonical_dict())
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "registry_hash": registry.registry_hash,
            "active_snapshot_id": registry.active_snapshot_id,
            "active_snapshot_hash": registry.active_snapshot_hash,
            "market_count": registry.market_count,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_019_foundation() -> Mapping[str, Any]:
    manifest = build_umd_019_certification_manifest()

    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-019",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}"
            for number in range(1, 19)
        ),
        "single_active_read_only_snapshot": (
            manifest.activation_mode
            == "single_active_read_only_snapshot"
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


def verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract() -> bool:
    result = certify_umd_019_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-019 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_019_BUILD_ID",
    "UMD_019_BUILD_NAME",
    "UMD_019_REVISION",
    "UMD_019_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedCanonicalMarketRegistrySnapshotActivation",
    "ReadOnlyActiveCanonicalMarketRegistry",
    "UMD019CertificationManifest",
    "build_umd_019_certification_manifest",
    "certify_active_canonical_market_registry",
    "certify_umd_019_foundation",
    "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
]
