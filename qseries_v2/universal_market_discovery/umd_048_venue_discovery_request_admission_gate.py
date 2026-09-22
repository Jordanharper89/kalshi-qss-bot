from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_047_venue_discovery_request_contract import (
    ALLOWED_DISCOVERY_SCOPES,
    CertifiedVenueDiscoveryRequestContract,
)

UMD_048_BUILD_ID = "UMD-048"
UMD_048_BUILD_NAME = "Certified Venue Discovery Request Admission Gate"
UMD_048_REVISION = (
    "UMD_048_CERTIFIED_VENUE_DISCOVERY_REQUEST_ADMISSION_GATE_V1"
)
UMD_048_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_pagination",
    "automatic_admission_commit",
    "ledger_append",
    "request_persistence",
    "registry_mutation",
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
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


def _normalized_text_tuple(
    values: Tuple[str, ...],
    field_name: str,
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(sorted({_text(value, field_name) for value in values}))


def _normalized_hash_tuple(
    values: Tuple[str, ...],
    field_name: str,
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(sorted({_sha256(value, field_name) for value in values}))


@dataclass(frozen=True, slots=True)
class CertifiedVenueDiscoveryRequestAdmissionDecision:
    request_id: str
    request_hash: str
    source_id: str
    source_contract_hash: str
    source_registry_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(self, "request_id", _text(self.request_id, "request_id"))
        object.__setattr__(self, "request_hash", _sha256(self.request_hash, "request_hash"))
        object.__setattr__(self, "source_id", _text(self.source_id, "source_id"))
        object.__setattr__(
            self,
            "source_contract_hash",
            _sha256(self.source_contract_hash, "source_contract_hash"),
        )
        object.__setattr__(
            self,
            "source_registry_hash",
            _sha256(self.source_registry_hash, "source_registry_hash"),
        )

        normalized_checks = MappingProxyType(
            dict(
                sorted(
                    (_text(str(name), "check name"), bool(passed))
                    for name, passed in self.checks.items()
                )
            )
        )
        object.__setattr__(self, "checks", normalized_checks)

        failed_checks = tuple(
            name for name, passed in normalized_checks.items() if not passed
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

        if self.admitted:
            if failed_checks or reasons:
                raise ValueError(
                    "admitted decisions cannot contain failed checks"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decisions require at least one failed check"
                )
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must exactly match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("decision lineage must belong to UMD")
        if self.lineage.build_id != UMD_048_BUILD_ID:
            raise ValueError("decision lineage must use build_id UMD-048")

        required_parent_hashes = {
            self.request_hash,
            self.source_contract_hash,
            self.source_registry_hash,
        }
        if not required_parent_hashes.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "decision lineage must include request, source-contract, "
                "and source-registry hashes"
            )

    @property
    def decision_id(self) -> str:
        return "umd:venue-discovery-request-admission:" + deterministic_sha256(
            {
                "request_id": self.request_id,
                "request_hash": self.request_hash,
                "source_id": self.source_id,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "source_id": self.source_id,
            "source_contract_hash": self.source_contract_hash,
            "source_registry_hash": self.source_registry_hash,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def evaluate_venue_discovery_request_admission(
    request: CertifiedVenueDiscoveryRequestContract,
    *,
    known_request_ids: Tuple[str, ...] = (),
    known_request_hashes: Tuple[str, ...] = (),
    lineage: ImmutableLineage,
) -> CertifiedVenueDiscoveryRequestAdmissionDecision:
    if not isinstance(request, CertifiedVenueDiscoveryRequestContract):
        raise TypeError("request must be a certified UMD-047 request")

    normalized_request_ids = _normalized_text_tuple(
        known_request_ids,
        "known_request_id",
    )
    normalized_request_hashes = _normalized_hash_tuple(
        known_request_hashes,
        "known_request_hash",
    )

    checks = {
        "request_hash_deterministic": (
            request.request_hash
            == deterministic_sha256(request.to_canonical_dict())
        ),
        "request_lineage_bound": (
            {
                request.source_contract_hash,
                request.source_registry_hash,
            }.issubset(set(request.lineage.parent_hashes))
        ),
        "request_read_only": request.read_only is True,
        "discovery_scope_certified": (
            request.discovery_scope in ALLOWED_DISCOVERY_SCOPES
        ),
        "requested_statuses_present": bool(request.requested_statuses),
        "requested_market_families_present": bool(
            request.requested_market_families
        ),
        "time_window_order_valid": (
            request.window_start is None
            or request.window_end is None
            or request.window_end >= request.window_start
        ),
        "page_size_valid": (
            request.page_size is None
            or 1 <= request.page_size <= 10000
        ),
        "request_id_not_previously_seen": (
            request.request_id not in normalized_request_ids
        ),
        "request_hash_not_previously_seen": (
            request.request_hash not in normalized_request_hashes
        ),
        "network_not_invoked": True,
        "persistence_not_invoked": True,
    }

    failed = tuple(name for name, passed in checks.items() if not passed)

    return CertifiedVenueDiscoveryRequestAdmissionDecision(
        request_id=request.request_id,
        request_hash=request.request_hash,
        source_id=request.source_id,
        source_contract_hash=request.source_contract_hash,
        source_registry_hash=request.source_registry_hash,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD048CertificationManifest:
    subsystem_id: str
    build_id: str
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


def build_umd_048_certification_manifest() -> UMD048CertificationManifest:
    return UMD048CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_048_BUILD_ID,
        revision=UMD_048_REVISION,
        schema_version=UMD_048_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 48)
        ),
        gate_mode="deterministic_read_only_admission",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_048_foundation() -> Mapping[str, Any]:
    manifest = build_umd_048_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-048",
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}" for number in range(1, 48)
            )
        ),
        "gate_mode": (
            manifest.gate_mode == "deterministic_read_only_admission"
        ),
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest": (
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


def verify_umd_048_venue_discovery_request_admission_gate() -> bool:
    result = certify_umd_048_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-048 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
