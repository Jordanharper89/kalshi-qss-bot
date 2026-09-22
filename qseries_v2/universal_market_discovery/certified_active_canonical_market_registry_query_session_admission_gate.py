from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_session_contract import (
    CertifiedActiveMarketQuerySession,
    ReadOnlyActiveMarketQuerySessionRegistry,
)
from .certified_active_canonical_market_registry_query_execution_read_model import (
    CertifiedActiveMarketQueryExecutionReadModel,
)

UMD_029_BUILD_ID = "UMD-029"
UMD_029_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Session Admission Gate"
)
UMD_029_REVISION = (
    "UMD_029_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_ADMISSION_GATE_V1"
)
UMD_029_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_session_commit",
    "session_persistence",
    "session_registry_mutation",
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
class CertifiedActiveMarketQuerySessionAdmissionDecision:
    session_id: str
    session_hash: str
    session_sequence: int
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        session_id = _text(
            self.session_id,
            "session_id",
        )
        if not session_id.startswith(
            "umd:market-query-session:"
        ):
            raise ValueError(
                "session_id must use UMD query-session prefix"
            )
        object.__setattr__(
            self,
            "session_id",
            session_id,
        )

        object.__setattr__(
            self,
            "session_hash",
            _sha256(
                self.session_hash,
                "session_hash",
            ),
        )

        if not isinstance(self.session_sequence, int):
            raise TypeError("session_sequence must be an integer")
        if self.session_sequence < 1:
            raise ValueError("session_sequence must be positive")

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
                "session-admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_029_BUILD_ID:
            raise ValueError(
                "session-admission lineage must use build_id UMD-029"
            )
        if self.session_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "session-admission lineage must include session hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:market-query-session-admission:" + deterministic_sha256(
            {
                "session_id": self.session_id,
                "session_hash": self.session_hash,
                "session_sequence": self.session_sequence,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "session_id": self.session_id,
            "session_hash": self.session_hash,
            "session_sequence": self.session_sequence,
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


def evaluate_active_market_query_session(
    session: CertifiedActiveMarketQuerySession,
    existing_registry: ReadOnlyActiveMarketQuerySessionRegistry,
    execution_read_model: CertifiedActiveMarketQueryExecutionReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQuerySessionAdmissionDecision:
    latest = existing_registry.latest()

    session_execution_ids = session.execution_ids()
    session_entry_ids = tuple(
        entry.entry_id
        for entry in session.execution_entries
    )

    checks = {
        "session_id_not_seen": (
            existing_registry.get(session.session_id) is None
        ),
        "session_hash_not_seen": all(
            prior.session_hash != session.session_hash
            for prior in existing_registry.sessions
        ),
        "session_sequence_valid": (
            session.session_sequence == 1
            if latest is None
            else (
                session.session_sequence
                == latest.session_sequence + 1
            )
        ),
        "previous_session_hash_valid": (
            session.previous_session_hash is None
            if latest is None
            else (
                session.previous_session_hash
                == latest.session_hash
            )
        ),
        "session_hash_deterministic": (
            session.session_hash
            == deterministic_sha256(
                session.to_canonical_dict()
            )
        ),
        "execution_ids_unique": (
            len(set(session_execution_ids))
            == len(session_execution_ids)
        ),
        "entry_ids_unique": (
            len(set(session_entry_ids))
            == len(session_entry_ids)
        ),
        "execution_order_strictly_increasing": all(
            session.execution_entries[index].sequence_number
            < session.execution_entries[index + 1].sequence_number
            for index in range(
                len(session.execution_entries) - 1
            )
        ),
        "executions_exist_in_read_model": all(
            execution_read_model.get_by_execution(
                execution_id
            )
            is not None
            for execution_id in session_execution_ids
        ),
        "entry_identity_matches_read_model": all(
            (
                execution_read_model.get_entry(
                    entry.entry_id
                )
                is not None
                and execution_read_model.get_entry(
                    entry.entry_id
                ).entry_hash
                == entry.entry_hash
            )
            for entry in session.execution_entries
        ),
        "execution_not_already_assigned": all(
            all(
                execution_id
                not in prior.execution_ids()
                for prior in existing_registry.sessions
            )
            for execution_id in session_execution_ids
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedActiveMarketQuerySessionAdmissionDecision(
        session_id=session.session_id,
        session_hash=session.session_hash,
        session_sequence=session.session_sequence,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD029CertificationManifest:
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


def build_umd_029_certification_manifest() -> UMD029CertificationManifest:
    return UMD029CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_029_BUILD_ID,
        build_name=UMD_029_BUILD_NAME,
        revision=UMD_029_REVISION,
        schema_version=UMD_029_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 29)
        ),
        gate_mode="read_only_session_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_029_foundation() -> Mapping[str, Any]:
    manifest = build_umd_029_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-029"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 29)
            )
        ),
        "read_only_session_validation": (
            manifest.gate_mode
            == "read_only_session_validation"
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


def verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate() -> bool:
    result = certify_umd_029_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-029 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_029_BUILD_ID",
    "UMD_029_BUILD_NAME",
    "UMD_029_REVISION",
    "UMD_029_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQuerySessionAdmissionDecision",
    "evaluate_active_market_query_session",
    "UMD029CertificationManifest",
    "build_umd_029_certification_manifest",
    "certify_umd_029_foundation",
    "verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate",
]
