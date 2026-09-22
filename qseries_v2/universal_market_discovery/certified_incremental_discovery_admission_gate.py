from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_incremental_discovery_batch_contract import (
    CertifiedIncrementalDiscoveryBatch,
    ReadOnlyIncrementalDiscoveryBatchRegistry,
)

UMD_012_BUILD_ID = "UMD-012"
UMD_012_BUILD_NAME = "Certified Incremental Discovery Admission Gate"
UMD_012_REVISION = (
    "UMD_012_CERTIFIED_INCREMENTAL_DISCOVERY_ADMISSION_GATE_CORRECTION_V2"
)
UMD_012_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_admission_commit",
    "persistence_write",
    "registry_mutation",
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


def _sha256_text(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(f"{field_name} must contain 64 hexadecimal characters")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hexadecimal")
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryAdmissionDecision:
    batch_id: str
    batch_hash: str
    source_id: str
    batch_sequence: int
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        batch_id = _text(self.batch_id, "batch_id")
        if not batch_id.startswith("umd:batch:"):
            raise ValueError("batch_id must use the UMD batch prefix")
        object.__setattr__(self, "batch_id", batch_id)
        object.__setattr__(
            self,
            "batch_hash",
            _sha256_text(self.batch_hash, "batch_hash"),
        )
        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, "source_id").lower(),
        )

        if not isinstance(self.batch_sequence, int):
            raise TypeError("batch_sequence must be an integer")
        if self.batch_sequence < 1:
            raise ValueError("batch_sequence must be positive")

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(sorted(normalized_checks.items()))),
        )

        reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(self, "rejection_reasons", reasons)

        failed_checks = tuple(
            name for name, passed in self.checks.items() if not passed
        )
        if self.admitted:
            if failed_checks:
                raise ValueError("admitted decisions cannot contain failed checks")
            if reasons:
                raise ValueError(
                    "admitted decisions cannot contain rejection reasons"
                )
        else:
            if not failed_checks:
                raise ValueError("rejected decisions require a failed check")
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must exactly match failed check names"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("decision lineage must belong to UMD")
        if self.lineage.build_id != UMD_012_BUILD_ID:
            raise ValueError("decision lineage must use build_id UMD-012")
        if self.batch_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "decision lineage must include the evaluated batch hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:admission:" + deterministic_sha256(
            {
                "batch_id": self.batch_id,
                "batch_hash": self.batch_hash,
                "checks": self.checks,
                "admitted": self.admitted,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "batch_id": self.batch_id,
            "batch_hash": self.batch_hash,
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def evaluate_incremental_discovery_batch(
    batch: CertifiedIncrementalDiscoveryBatch,
    existing_registry: ReadOnlyIncrementalDiscoveryBatchRegistry,
    *,
    lineage: ImmutableLineage,
) -> CertifiedDiscoveryAdmissionDecision:
    latest = existing_registry.latest_for_source(batch.source_id)

    known_market_ids = {
        market.canonical_market_id
        for market in existing_registry.graph_registry.markets
    }
    prior_source_keys = {
        (candidate.source_id, candidate.source_market_key)
        for prior_batch in existing_registry.batches
        for candidate in prior_batch.candidates
    }

    checks = {
        "batch_id_not_seen": existing_registry.get(batch.batch_id) is None,
        "batch_hash_not_seen": all(
            prior_batch.batch_hash != batch.batch_hash
            for prior_batch in existing_registry.batches
        ),
        "source_sequence_valid": (
            batch.batch_sequence == 1
            if latest is None
            else batch.batch_sequence == latest.batch_sequence + 1
        ),
        "previous_hash_valid": (
            batch.previous_batch_hash is None
            if latest is None
            else batch.previous_batch_hash == latest.batch_hash
        ),
        "cursor_chain_valid": (
            batch.start_cursor is None
            if latest is None
            else (
                batch.start_cursor is not None
                and batch.start_cursor.record_hash
                == latest.end_cursor.record_hash
            )
        ),
        "candidate_ids_unique": len(
            {candidate.candidate_id for candidate in batch.candidates}
        )
        == len(batch.candidates),
        "source_market_keys_unique": len(
            {candidate.source_market_key for candidate in batch.candidates}
        )
        == len(batch.candidates),
        "candidate_sources_match": all(
            candidate.source_id == batch.source_id
            for candidate in batch.candidates
        ),
        "candidate_markets_new": all(
            candidate.market.canonical_market_id not in known_market_ids
            for candidate in batch.candidates
        ),
        "candidate_keys_not_replayed": all(
            (candidate.source_id, candidate.source_market_key)
            not in prior_source_keys
            for candidate in batch.candidates
        ),
        "batch_hash_deterministic": (
            batch.batch_hash
            == deterministic_sha256(batch.to_canonical_dict())
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return CertifiedDiscoveryAdmissionDecision(
        batch_id=batch.batch_id,
        batch_hash=batch.batch_hash,
        source_id=batch.source_id,
        batch_sequence=batch.batch_sequence,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD012CertificationManifest:
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
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_012_certification_manifest() -> UMD012CertificationManifest:
    return UMD012CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_012_BUILD_ID,
        build_name=UMD_012_BUILD_NAME,
        revision=UMD_012_REVISION,
        schema_version=UMD_012_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 12)
        ),
        gate_mode="read_only_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_012_foundation() -> Mapping[str, Any]:
    manifest = build_umd_012_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-012",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(f"UMD-{number:03d}" for number in range(1, 12)),
        "read_only_gate": manifest.gate_mode == "read_only_validation",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
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


def verify_umd_012_certified_incremental_discovery_admission_gate() -> bool:
    result = certify_umd_012_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-012 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_012_BUILD_ID",
    "UMD_012_BUILD_NAME",
    "UMD_012_REVISION",
    "UMD_012_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedDiscoveryAdmissionDecision",
    "evaluate_incremental_discovery_batch",
    "UMD012CertificationManifest",
    "build_umd_012_certification_manifest",
    "certify_umd_012_foundation",
    "verify_umd_012_certified_incremental_discovery_admission_gate",
]
