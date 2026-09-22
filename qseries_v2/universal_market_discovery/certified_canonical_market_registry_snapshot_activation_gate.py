from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_registry_snapshot_activation_contract import (
    CertifiedCanonicalMarketRegistrySnapshotActivation,
    ReadOnlyActiveCanonicalMarketRegistry,
)

UMD_020_BUILD_ID = "UMD-020"
UMD_020_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Activation Gate"
)
UMD_020_REVISION = (
    "UMD_020_CERTIFIED_CANONICAL_MARKET_REGISTRY_"
    "SNAPSHOT_ACTIVATION_GATE_V1"
)
UMD_020_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_activation_commit",
    "activation_persistence",
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


def _sha256(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    if any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedSnapshotActivationDecision:
    activation_id: str
    activation_hash: str
    snapshot_id: str
    snapshot_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        activation_id = _text(
            self.activation_id,
            "activation_id",
        )
        if not activation_id.startswith(
            "umd:snapshot-activation:"
        ):
            raise ValueError(
                "activation_id must use the UMD activation prefix"
            )
        object.__setattr__(
            self,
            "activation_id",
            activation_id,
        )

        object.__setattr__(
            self,
            "activation_hash",
            _sha256(
                self.activation_hash,
                "activation_hash",
            ),
        )

        snapshot_id = _text(
            self.snapshot_id,
            "snapshot_id",
        )
        if not snapshot_id.startswith(
            "umd:market-registry-snapshot:"
        ):
            raise ValueError(
                "snapshot_id must use the UMD snapshot prefix"
            )
        object.__setattr__(
            self,
            "snapshot_id",
            snapshot_id,
        )

        object.__setattr__(
            self,
            "snapshot_hash",
            _sha256(
                self.snapshot_hash,
                "snapshot_hash",
            ),
        )

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
                    "admitted activation decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected activation decision requires failed checks"
                )
            if normalized_reasons != tuple(
                sorted(failed_checks)
            ):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "activation-decision lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_020_BUILD_ID:
            raise ValueError(
                "activation-decision lineage must use build_id UMD-020"
            )
        if self.activation_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "activation-decision lineage must include activation hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:snapshot-activation-decision:" + deterministic_sha256(
            {
                "activation_id": self.activation_id,
                "activation_hash": self.activation_hash,
                "snapshot_id": self.snapshot_id,
                "snapshot_hash": self.snapshot_hash,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "activation_id": self.activation_id,
            "activation_hash": self.activation_hash,
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def evaluate_snapshot_activation(
    activation: CertifiedCanonicalMarketRegistrySnapshotActivation,
    current_registry: ReadOnlyActiveCanonicalMarketRegistry | None,
    prior_activation_ids: Tuple[str, ...],
    prior_activation_hashes: Tuple[str, ...],
    *,
    lineage: ImmutableLineage,
) -> CertifiedSnapshotActivationDecision:
    normalized_prior_ids = tuple(
        sorted(
            {
                _text(
                    activation_id,
                    "prior activation id",
                )
                for activation_id in prior_activation_ids
            }
        )
    )
    normalized_prior_hashes = tuple(
        sorted(
            {
                _sha256(
                    activation_hash,
                    "prior activation hash",
                )
                for activation_hash in prior_activation_hashes
            }
        )
    )

    current_snapshot_sequence = (
        0
        if current_registry is None
        else current_registry.snapshot.snapshot_sequence
    )
    current_snapshot_hash = (
        None
        if current_registry is None
        else current_registry.active_snapshot_hash
    )

    checks = {
        "activation_id_not_seen": (
            activation.activation_id
            not in normalized_prior_ids
        ),
        "activation_hash_not_seen": (
            activation.activation_hash
            not in normalized_prior_hashes
        ),
        "snapshot_is_admitted": (
            activation.admission_entry.decision.admitted
        ),
        "snapshot_id_matches_admission": (
            activation.snapshot.snapshot_id
            == activation.admission_entry.decision.snapshot_id
        ),
        "snapshot_hash_matches_admission": (
            activation.snapshot.snapshot_hash
            == activation.admission_entry.decision.snapshot_hash
        ),
        "snapshot_sequence_matches_admission": (
            activation.snapshot.snapshot_sequence
            == activation.admission_entry.decision.snapshot_sequence
        ),
        "activation_hash_deterministic": (
            activation.activation_hash
            == deterministic_sha256(
                activation.to_canonical_dict()
            )
        ),
        "single_active_snapshot_transition": (
            current_registry is None
            or activation.snapshot.snapshot_sequence
            == current_snapshot_sequence + 1
        ),
        "active_snapshot_changes": (
            current_snapshot_hash
            != activation.snapshot.snapshot_hash
        ),
        "no_snapshot_rollback": (
            current_registry is None
            or activation.snapshot.snapshot_sequence
            > current_snapshot_sequence
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedSnapshotActivationDecision(
        activation_id=activation.activation_id,
        activation_hash=activation.activation_hash,
        snapshot_id=activation.snapshot.snapshot_id,
        snapshot_hash=activation.snapshot.snapshot_hash,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD020CertificationManifest:
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


def build_umd_020_certification_manifest() -> UMD020CertificationManifest:
    return UMD020CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_020_BUILD_ID,
        build_name=UMD_020_BUILD_NAME,
        revision=UMD_020_REVISION,
        schema_version=UMD_020_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 20)
        ),
        gate_mode="read_only_activation_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_020_foundation() -> Mapping[str, Any]:
    manifest = build_umd_020_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-020"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 20)
            )
        ),
        "read_only_activation_validation": (
            manifest.gate_mode
            == "read_only_activation_validation"
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
        name
        for name, passed in checks.items()
        if not passed
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


def verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate() -> bool:
    result = certify_umd_020_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-020 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_020_BUILD_ID",
    "UMD_020_BUILD_NAME",
    "UMD_020_REVISION",
    "UMD_020_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedSnapshotActivationDecision",
    "evaluate_snapshot_activation",
    "UMD020CertificationManifest",
    "build_umd_020_certification_manifest",
    "certify_umd_020_foundation",
    "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate",
]
