from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_043_query_session_read_model_admission_ledger_read_model import (
    CertifiedUMD043AdmissionLedgerReadModel,
)

UMD_044_BUILD_ID = "UMD-044"
UMD_044_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Session "
    "Read Model Admission Ledger Read Model Admission Ledger Read Model Admission Gate"
)
UMD_044_REVISION = (
    "UMD_044_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_"
    "READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_GATE_V1"
)
UMD_044_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_admission_commit",
    "ledger_append",
    "ledger_mutation",
    "read_model_mutation",
    "read_model_persistence",
    "active_registry_mutation",
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
        raise ValueError(f"{field_name} must contain 64 hexadecimal characters")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hexadecimal")
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedUMD044AdmissionDecision:
    read_model_hash: str
    source_ledger_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "read_model_hash", _sha256(self.read_model_hash, "read_model_hash"))
        object.__setattr__(self, "source_ledger_hash", _sha256(self.source_ledger_hash, "source_ledger_hash"))

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(sorted(normalized_checks.items()))),
        )

        failed = tuple(name for name, passed in self.checks.items() if not passed)
        reasons = tuple(sorted({_text(reason, "rejection reason") for reason in self.rejection_reasons}))
        object.__setattr__(self, "rejection_reasons", reasons)

        if self.admitted:
            if failed or reasons:
                raise ValueError("admitted decision cannot contain failures")
        else:
            if not failed:
                raise ValueError("rejected decision requires failed checks")
            if reasons != tuple(sorted(failed)):
                raise ValueError("rejection reasons must match failed checks")

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("admission lineage must belong to UMD")
        if self.lineage.build_id != UMD_044_BUILD_ID:
            raise ValueError("admission lineage must use build_id UMD-044")
        required = {self.read_model_hash, self.source_ledger_hash}
        if not required.issubset(set(self.lineage.parent_hashes)):
            raise ValueError("admission lineage is missing required parent hashes")

    @property
    def decision_id(self) -> str:
        return (
            "umd:query-session-read-model-admission-ledger-read-model-admission:"
            + deterministic_sha256(
                {
                    "read_model_hash": self.read_model_hash,
                    "source_ledger_hash": self.source_ledger_hash,
                    "admitted": self.admitted,
                    "checks": self.checks,
                }
            )
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "read_model_hash": self.read_model_hash,
            "source_ledger_hash": self.source_ledger_hash,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def evaluate_umd_044_admission(
    read_model: CertifiedUMD043AdmissionLedgerReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedUMD044AdmissionDecision:
    if not isinstance(
        read_model,
        CertifiedUMD043AdmissionLedgerReadModel,
    ):
        raise TypeError("read_model must be a certified UMD-037 read model")

    checks = {
        "read_model_hash_deterministic": (
            read_model.read_model_hash
            == deterministic_sha256(read_model.to_canonical_dict())
        ),
        "count_partition_valid": (
            read_model.admitted_entry_count
            + read_model.rejected_entry_count
            == read_model.total_entry_count
        ),
        "ordered_entry_count_valid": (
            len(read_model.ordered_entry_ids) == read_model.total_entry_count
        ),
        "ordered_read_model_count_valid": (
            len(read_model.ordered_read_model_hashes) == read_model.total_entry_count
        ),
        "ordered_decision_count_valid": (
            len(read_model.ordered_decision_ids) == read_model.total_entry_count
        ),
        "entry_ids_unique": (
            len(set(read_model.ordered_entry_ids))
            == len(read_model.ordered_entry_ids)
        ),
        "read_model_hashes_unique": (
            len(set(read_model.ordered_read_model_hashes))
            == len(read_model.ordered_read_model_hashes)
        ),
        "decision_ids_unique": (
            len(set(read_model.ordered_decision_ids))
            == len(read_model.ordered_decision_ids)
        ),
        "admission_partition_disjoint": (
            not set(read_model.admitted_entry_ids).intersection(
                read_model.rejected_entry_ids
            )
        ),
        "admission_partition_complete": (
            set(read_model.admitted_entry_ids).union(
                read_model.rejected_entry_ids
            )
            == set(read_model.ordered_entry_ids)
        ),
        "latest_entry_consistent": (
            (
                read_model.latest_entry_id is None
                and not read_model.ordered_entry_ids
            )
            or (
                bool(read_model.ordered_entry_ids)
                and read_model.latest_entry_id
                == read_model.ordered_entry_ids[-1]
            )
        ),
        "latest_admitted_entry_consistent": (
            (
                read_model.latest_admitted_entry_id is None
                and not read_model.admitted_entry_ids
            )
            or (
                bool(read_model.admitted_entry_ids)
                and read_model.latest_admitted_entry_id
                == read_model.admitted_entry_ids[-1]
            )
        ),
        "entry_positions_contiguous": all(
            read_model.entry_position(entry_id) == index
            for index, entry_id in enumerate(read_model.ordered_entry_ids, start=1)
        ),
        "read_model_positions_contiguous": all(
            read_model.read_model_position(read_model_hash) == index
            for index, read_model_hash in enumerate(
                read_model.ordered_read_model_hashes,
                start=1,
            )
        ),
        "decision_positions_contiguous": all(
            read_model.decision_position(decision_id) == index
            for index, decision_id in enumerate(
                read_model.ordered_decision_ids,
                start=1,
            )
        ),
        "lineage_bound_to_source_ledger": (
            read_model.source_ledger_hash in read_model.lineage.parent_hashes
        ),
    }

    failed = tuple(name for name, passed in checks.items() if not passed)

    return CertifiedUMD044AdmissionDecision(
        read_model_hash=read_model.read_model_hash,
        source_ledger_hash=read_model.source_ledger_hash,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD044CertificationManifest:
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


def build_umd_044_certification_manifest() -> UMD044CertificationManifest:
    return UMD044CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_044_BUILD_ID,
        build_name=UMD_044_BUILD_NAME,
        revision=UMD_044_REVISION,
        schema_version=UMD_044_SCHEMA_VERSION,
        upstream_builds=tuple(f"UMD-{number:03d}" for number in range(1, 44)),
        gate_mode="deterministic_read_only_admission",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_044_foundation() -> Mapping[str, Any]:
    manifest = build_umd_044_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-044",
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(f"UMD-{number:03d}" for number in range(1, 44))
        ),
        "deterministic_read_only_admission": (
            manifest.gate_mode == "deterministic_read_only_admission"
        ),
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": (
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


def verify_umd_044_query_session_read_model_admission_gate() -> bool:
    certification = certify_umd_044_foundation()
    if not certification["certified"]:
        raise RuntimeError(
            "UMD-044 foundation certification failed: "
            + ", ".join(certification["failed_checks"])
        )
    return True
