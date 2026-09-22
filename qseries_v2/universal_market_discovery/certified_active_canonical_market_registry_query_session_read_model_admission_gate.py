from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_session_read_model import (
    CertifiedActiveMarketQuerySessionReadModel,
)

UMD_032_BUILD_ID = "UMD-032"
UMD_032_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Session Read Model Admission Gate"
)
UMD_032_REVISION = (
    "UMD_032_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_GATE_V1"
)
UMD_032_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_read_model_commit",
    "read_model_persistence",
    "read_model_mutation",
    "session_registry_mutation",
    "session_ledger_mutation",
    "execution_ledger_mutation",
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
class CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash: str
    session_registry_hash: str
    admission_ledger_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "read_model_hash",
            _sha256(
                self.read_model_hash,
                "read_model_hash",
            ),
        )
        object.__setattr__(
            self,
            "session_registry_hash",
            _sha256(
                self.session_registry_hash,
                "session_registry_hash",
            ),
        )
        object.__setattr__(
            self,
            "admission_ledger_hash",
            _sha256(
                self.admission_ledger_hash,
                "admission_ledger_hash",
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
        reasons = tuple(
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
            reasons,
        )

        if self.admitted:
            if failed_checks or reasons:
                raise ValueError(
                    "admitted decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decision requires failed checks"
                )
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "read-model admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_032_BUILD_ID:
            raise ValueError(
                "read-model admission lineage must use build_id UMD-032"
            )

        required_parents = {
            self.read_model_hash,
            self.session_registry_hash,
            self.admission_ledger_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "read-model admission lineage is missing required parent hashes"
            )

    @property
    def decision_id(self) -> str:
        return "umd:query-session-read-model-admission:" + deterministic_sha256(
            {
                "read_model_hash": self.read_model_hash,
                "session_registry_hash": self.session_registry_hash,
                "admission_ledger_hash": self.admission_ledger_hash,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "read_model_hash": self.read_model_hash,
            "session_registry_hash": self.session_registry_hash,
            "admission_ledger_hash": self.admission_ledger_hash,
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


def evaluate_active_market_query_session_read_model(
    read_model: CertifiedActiveMarketQuerySessionReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    latest_session = read_model.latest_session()

    checks = {
        "read_model_hash_deterministic": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "session_registry_hash_matches": (
            read_model.session_registry.registry_hash
            == read_model.to_canonical_dict()[
                "session_registry_hash"
            ]
        ),
        "admission_ledger_hash_matches": (
            read_model.admission_ledger.ledger_hash
            == read_model.to_canonical_dict()[
                "admission_ledger_hash"
            ]
        ),
        "session_count_matches_registry": (
            read_model.session_count
            == len(read_model.session_registry.sessions)
        ),
        "admitted_count_matches_ledger": (
            read_model.session_count
            == len(
                read_model.admission_ledger.admitted_entries()
            )
        ),
        "rejected_count_matches_ledger": (
            read_model.rejected_count
            == len(
                read_model.admission_ledger.rejected_entries()
            )
        ),
        "execution_membership_count_valid": (
            read_model.execution_membership_count
            == len(read_model.execution_ids())
        ),
        "session_ids_unique": (
            len(set(read_model.session_ids()))
            == read_model.session_count
        ),
        "execution_ids_unique": (
            len(set(read_model.execution_ids()))
            == read_model.execution_membership_count
        ),
        "latest_session_consistent": (
            latest_session is None
            if read_model.session_count == 0
            else (
                latest_session is not None
                and latest_session.session_id
                == read_model.session_ids()[-1]
            )
        ),
        "registry_and_ledger_lineage_bound": (
            read_model.session_registry.registry_hash
            in read_model.lineage.parent_hashes
            and read_model.admission_ledger.ledger_hash
            in read_model.lineage.parent_hashes
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model.read_model_hash,
        session_registry_hash=(
            read_model.session_registry.registry_hash
        ),
        admission_ledger_hash=(
            read_model.admission_ledger.ledger_hash
        ),
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD032CertificationManifest:
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


def build_umd_032_certification_manifest() -> UMD032CertificationManifest:
    return UMD032CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_032_BUILD_ID,
        build_name=UMD_032_BUILD_NAME,
        revision=UMD_032_REVISION,
        schema_version=UMD_032_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 32)
        ),
        gate_mode="read_only_read_model_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_032_foundation() -> Mapping[str, Any]:
    manifest = build_umd_032_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-032"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 32)
            )
        ),
        "read_only_read_model_validation": (
            manifest.gate_mode
            == "read_only_read_model_validation"
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


def verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate() -> bool:
    result = certify_umd_032_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-032 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_032_BUILD_ID",
    "UMD_032_BUILD_NAME",
    "UMD_032_REVISION",
    "UMD_032_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQuerySessionReadModelAdmissionDecision",
    "evaluate_active_market_query_session_read_model",
    "UMD032CertificationManifest",
    "build_umd_032_certification_manifest",
    "certify_umd_032_foundation",
    "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate",
]
