from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_materialized_market_admission_registry import (
    ReadOnlyMaterializedMarketAdmissionRegistry,
)
from .certified_canonical_market_registry_snapshot_contract import (
    CertifiedCanonicalMarketRegistrySnapshot,
    ReadOnlyCanonicalMarketRegistrySnapshotChain,
)

UMD_017_BUILD_ID = "UMD-017"
UMD_017_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Admission Gate"
)
UMD_017_REVISION = (
    "UMD_017_CERTIFIED_CANONICAL_MARKET_REGISTRY_SNAPSHOT_ADMISSION_GATE_V1"
)
UMD_017_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_snapshot_commit",
    "snapshot_persistence",
    "registry_mutation",
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


@dataclass(frozen=True, slots=True)
class CertifiedSnapshotAdmissionDecision:
    snapshot_id: str
    snapshot_hash: str
    snapshot_sequence: int
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        snapshot_id = _text(self.snapshot_id, "snapshot_id")
        if not snapshot_id.startswith(
            "umd:market-registry-snapshot:"
        ):
            raise ValueError(
                "snapshot_id must use the UMD snapshot prefix"
            )
        object.__setattr__(self, "snapshot_id", snapshot_id)

        snapshot_hash = _text(
            self.snapshot_hash,
            "snapshot_hash",
        ).lower()
        if len(snapshot_hash) != 64:
            raise ValueError(
                "snapshot_hash must contain 64 hexadecimal characters"
            )
        if any(
            character not in "0123456789abcdef"
            for character in snapshot_hash
        ):
            raise ValueError(
                "snapshot_hash must be lowercase SHA-256 hexadecimal"
            )
        object.__setattr__(
            self,
            "snapshot_hash",
            snapshot_hash,
        )

        if not isinstance(self.snapshot_sequence, int):
            raise TypeError("snapshot_sequence must be an integer")
        if self.snapshot_sequence < 1:
            raise ValueError("snapshot_sequence must be positive")

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(
                dict(sorted(normalized_checks.items()))
            ),
        )

        failed_checks = tuple(
            name
            for name, passed in self.checks.items()
            if not passed
        )
        normalized_reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            normalized_reasons,
        )

        if self.admitted:
            if failed_checks or normalized_reasons:
                raise ValueError(
                    "admitted decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decision requires failed checks"
                )
            if normalized_reasons != tuple(
                sorted(failed_checks)
            ):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "snapshot-admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_017_BUILD_ID:
            raise ValueError(
                "snapshot-admission lineage must use build_id UMD-017"
            )
        if self.snapshot_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "snapshot-admission lineage must include snapshot hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:snapshot-admission:" + deterministic_sha256(
            {
                "snapshot_id": self.snapshot_id,
                "snapshot_hash": self.snapshot_hash,
                "snapshot_sequence": self.snapshot_sequence,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "snapshot_sequence": self.snapshot_sequence,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def evaluate_canonical_market_registry_snapshot(
    snapshot: CertifiedCanonicalMarketRegistrySnapshot,
    source_registry: ReadOnlyMaterializedMarketAdmissionRegistry,
    existing_chain: ReadOnlyCanonicalMarketRegistrySnapshotChain,
    *,
    lineage: ImmutableLineage,
) -> CertifiedSnapshotAdmissionDecision:
    latest = existing_chain.latest()

    source_markets = source_registry.complete_market_view()
    source_market_hashes = tuple(
        market.record_hash for market in source_markets
    )
    snapshot_market_hashes = tuple(
        market.record_hash for market in snapshot.markets
    )

    previous_market_ids = (
        set()
        if latest is None
        else {
            market.canonical_market_id
            for market in latest.markets
        }
    )
    current_market_ids = {
        market.canonical_market_id
        for market in snapshot.markets
    }

    checks = {
        "snapshot_id_not_seen": (
            existing_chain.get(snapshot.snapshot_id) is None
        ),
        "snapshot_hash_not_seen": all(
            prior.snapshot_hash != snapshot.snapshot_hash
            for prior in existing_chain.snapshots
        ),
        "snapshot_sequence_valid": (
            snapshot.snapshot_sequence == 1
            if latest is None
            else (
                snapshot.snapshot_sequence
                == latest.snapshot_sequence + 1
            )
        ),
        "previous_snapshot_hash_valid": (
            snapshot.previous_snapshot_hash is None
            if latest is None
            else (
                snapshot.previous_snapshot_hash
                == latest.snapshot_hash
            )
        ),
        "source_registry_hash_valid": (
            snapshot.source_registry_hash
            == source_registry.registry_hash
        ),
        "market_count_matches_source": (
            len(snapshot.markets) == len(source_markets)
        ),
        "market_hashes_match_source": (
            snapshot_market_hashes == source_market_hashes
        ),
        "canonical_market_ids_unique": (
            len(current_market_ids)
            == len(snapshot.markets)
        ),
        "no_canonical_market_deletion": (
            previous_market_ids.issubset(current_market_ids)
        ),
        "snapshot_hash_deterministic": (
            snapshot.snapshot_hash
            == deterministic_sha256(
                snapshot.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return CertifiedSnapshotAdmissionDecision(
        snapshot_id=snapshot.snapshot_id,
        snapshot_hash=snapshot.snapshot_hash,
        snapshot_sequence=snapshot.snapshot_sequence,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD017CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    gate_mode: str
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
            "gate_mode": self.gate_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_017_certification_manifest() -> UMD017CertificationManifest:
    return UMD017CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_017_BUILD_ID,
        build_name=UMD_017_BUILD_NAME,
        revision=UMD_017_REVISION,
        schema_version=UMD_017_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 17)
        ),
        gate_mode="read_only_snapshot_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_017_foundation() -> Mapping[str, Any]:
    manifest = build_umd_017_certification_manifest()
    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-017"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 17)
            )
        ),
        "read_only_snapshot_validation": (
            manifest.gate_mode
            == "read_only_snapshot_validation"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
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


def verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate() -> bool:
    result = certify_umd_017_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-017 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_017_BUILD_ID",
    "UMD_017_BUILD_NAME",
    "UMD_017_REVISION",
    "UMD_017_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedSnapshotAdmissionDecision",
    "evaluate_canonical_market_registry_snapshot",
    "UMD017CertificationManifest",
    "build_umd_017_certification_manifest",
    "certify_umd_017_foundation",
    "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate",
]
