from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_051_raw_venue_market_observation_contract import (
    CertifiedRawVenueMarketObservation,
    certify_raw_venue_market_observation,
)

UMD_052_BUILD_ID = "UMD-052"
UMD_052_BUILD_NAME = (
    "Certified Raw Venue Market Observation Admission Gate"
)
UMD_052_REVISION = (
    "UMD_052_CERTIFIED_RAW_VENUE_MARKET_"
    "OBSERVATION_ADMISSION_GATE_V1"
)
UMD_052_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_observation_creation",
    "automatic_admission_commit",
    "ledger_append",
    "canonical_market_construction",
    "classification_inference",
    "duplicate_resolution",
    "observation_persistence",
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


def _normalized_text_tuple(
    values: Tuple[str, ...],
    field_name: str,
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(
        sorted(
            {
                _text(value, field_name)
                for value in values
            }
        )
    )


def _normalized_hash_tuple(
    values: Tuple[str, ...],
    field_name: str,
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    return tuple(
        sorted(
            {
                _sha256(value, field_name)
                for value in values
            }
        )
    )


def _freeze_checks(
    checks: Mapping[str, bool],
) -> Mapping[str, bool]:
    if not isinstance(checks, Mapping):
        raise TypeError("checks must be a mapping")
    normalized = {}
    for key, value in checks.items():
        normalized_key = _text(str(key), "check name")
        if not isinstance(value, bool):
            raise TypeError(
                f"check {normalized_key!r} must be boolean"
            )
        normalized[normalized_key] = value
    return MappingProxyType(dict(sorted(normalized.items())))


@dataclass(frozen=True, slots=True)
class CertifiedRawVenueMarketObservationAdmissionDecision:
    observation_id: str
    observation_hash: str
    request_id: str
    request_hash: str
    admission_decision_id: str
    admission_decision_record_hash: str
    source_id: str
    source_contract_hash: str
    source_registry_hash: str
    raw_payload_hash: str
    canonical_venue_id: str
    adapter_key: str
    venue_market_id: str
    retrieval_sequence: int
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        for field_name in (
            "observation_id",
            "request_id",
            "admission_decision_id",
            "source_id",
            "canonical_venue_id",
            "adapter_key",
            "venue_market_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _text(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        for field_name in (
            "observation_hash",
            "request_hash",
            "admission_decision_record_hash",
            "source_contract_hash",
            "source_registry_hash",
            "raw_payload_hash",
        ):
            object.__setattr__(
                self,
                field_name,
                _sha256(
                    getattr(self, field_name),
                    field_name,
                ),
            )

        if not isinstance(self.retrieval_sequence, int):
            raise TypeError(
                "retrieval_sequence must be an integer"
            )
        if self.retrieval_sequence < 1:
            raise ValueError(
                "retrieval_sequence must be positive"
            )
        if not isinstance(self.admitted, bool):
            raise TypeError("admitted must be boolean")

        frozen_checks = _freeze_checks(self.checks)
        object.__setattr__(
            self,
            "checks",
            frozen_checks,
        )
        normalized_reasons = _normalized_text_tuple(
            self.rejection_reasons,
            "rejection_reason",
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            normalized_reasons,
        )

        failed_checks = tuple(
            sorted(
                name
                for name, passed in frozen_checks.items()
                if not passed
            )
        )
        if self.admitted:
            if failed_checks:
                raise ValueError(
                    "admitted decisions cannot contain failed checks"
                )
            if normalized_reasons:
                raise ValueError(
                    "admitted decisions cannot contain rejection reasons"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decisions require at least one failed check"
                )
            if normalized_reasons != failed_checks:
                raise ValueError(
                    "rejection reasons must exactly match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "decision lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_052_BUILD_ID:
            raise ValueError(
                "decision lineage must use build_id UMD-052"
            )

        required_parent_hashes = {
            self.observation_hash,
            self.request_hash,
            self.admission_decision_record_hash,
            self.source_contract_hash,
            self.source_registry_hash,
            self.raw_payload_hash,
        }
        if not required_parent_hashes.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "decision lineage must include observation, request, "
                "request-decision, source-contract, source-registry, "
                "and raw-payload hashes"
            )

    @property
    def decision_id(self) -> str:
        return (
            "umd:raw-venue-market-observation-admission-decision:"
            + deterministic_sha256(
                {
                    "observation_id": self.observation_id,
                    "observation_hash": self.observation_hash,
                    "admitted": self.admitted,
                    "checks": self.checks,
                    "rejection_reasons": self.rejection_reasons,
                }
            )
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "observation_id": self.observation_id,
            "observation_hash": self.observation_hash,
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "admission_decision_id": (
                self.admission_decision_id
            ),
            "admission_decision_record_hash": (
                self.admission_decision_record_hash
            ),
            "source_id": self.source_id,
            "source_contract_hash": self.source_contract_hash,
            "source_registry_hash": self.source_registry_hash,
            "raw_payload_hash": self.raw_payload_hash,
            "canonical_venue_id": self.canonical_venue_id,
            "adapter_key": self.adapter_key,
            "venue_market_id": self.venue_market_id,
            "retrieval_sequence": self.retrieval_sequence,
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


def evaluate_raw_venue_market_observation_admission(
    observation: CertifiedRawVenueMarketObservation,
    *,
    seen_observation_ids: Tuple[str, ...] = (),
    seen_observation_hashes: Tuple[str, ...] = (),
    seen_source_market_retrieval_keys: Tuple[str, ...] = (),
    lineage: ImmutableLineage,
) -> CertifiedRawVenueMarketObservationAdmissionDecision:
    if not isinstance(
        observation,
        CertifiedRawVenueMarketObservation,
    ):
        raise TypeError(
            "observation must be the certified UMD-051 raw observation"
        )

    certification = certify_raw_venue_market_observation(
        observation
    )
    normalized_ids = set(
        _normalized_text_tuple(
            seen_observation_ids,
            "seen_observation_id",
        )
    )
    normalized_hashes = set(
        _normalized_hash_tuple(
            seen_observation_hashes,
            "seen_observation_hash",
        )
    )
    normalized_retrieval_keys = set(
        _normalized_text_tuple(
            seen_source_market_retrieval_keys,
            "seen_source_market_retrieval_key",
        )
    )

    retrieval_key = (
        f"{observation.source_id}|"
        f"{observation.venue_market_id}|"
        f"{observation.retrieval_sequence}"
    )

    checks = {
        "observation_contract_certified": (
            certification["certified"] is True
        ),
        "observation_hash_matches_contract": (
            certification["observation_hash"]
            == observation.observation_hash
        ),
        "observation_identity_matches_contract": (
            certification["observation_id"]
            == observation.observation_id
        ),
        "raw_payload_hash_matches": (
            observation.raw_payload_hash
            == deterministic_sha256(
                observation.raw_payload
            )
        ),
        "observation_read_only": (
            observation.read_only is True
        ),
        "source_emission_time_valid": (
            observation.source_emitted_at is None
            or observation.source_emitted_at
            <= observation.observed_at
        ),
        "observation_id_not_seen": (
            observation.observation_id
            not in normalized_ids
        ),
        "observation_hash_not_seen": (
            observation.observation_hash
            not in normalized_hashes
        ),
        "source_market_retrieval_not_seen": (
            retrieval_key
            not in normalized_retrieval_keys
        ),
        "lineage_build_valid": (
            observation.lineage.build_id == "UMD-051"
        ),
    }
    rejection_reasons = tuple(
        sorted(
            name
            for name, passed in checks.items()
            if not passed
        )
    )
    admitted = not rejection_reasons

    return CertifiedRawVenueMarketObservationAdmissionDecision(
        observation_id=observation.observation_id,
        observation_hash=observation.observation_hash,
        request_id=observation.request_id,
        request_hash=observation.request_hash,
        admission_decision_id=(
            observation.admission_decision_id
        ),
        admission_decision_record_hash=(
            observation.admission_decision_record_hash
        ),
        source_id=observation.source_id,
        source_contract_hash=(
            observation.source_contract_hash
        ),
        source_registry_hash=(
            observation.source_registry_hash
        ),
        raw_payload_hash=observation.raw_payload_hash,
        canonical_venue_id=observation.canonical_venue_id,
        adapter_key=observation.adapter_key,
        venue_market_id=observation.venue_market_id,
        retrieval_sequence=observation.retrieval_sequence,
        admitted=admitted,
        checks=checks,
        rejection_reasons=rejection_reasons,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD052CertificationManifest:
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
            "prohibited_capabilities": (
                self.prohibited_capabilities
            ),
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


def build_umd_052_certification_manifest() -> UMD052CertificationManifest:
    return UMD052CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_052_BUILD_ID,
        revision=UMD_052_REVISION,
        schema_version=UMD_052_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 52)
        ),
        gate_mode=(
            "deterministic_read_only_raw_observation_admission"
        ),
        prohibited_capabilities=(
            PROHIBITED_CAPABILITIES
        ),
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_052_foundation() -> Mapping[str, Any]:
    manifest = build_umd_052_certification_manifest()
    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-052"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 52)
            )
        ),
        "gate_mode": (
            manifest.gate_mode
            == "deterministic_read_only_raw_observation_admission"
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
        "deterministic_manifest": (
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


def verify_umd_052_raw_venue_market_observation_admission_gate() -> bool:
    result = certify_umd_052_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-052 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
