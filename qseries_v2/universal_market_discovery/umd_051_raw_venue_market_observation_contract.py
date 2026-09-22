from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_047_venue_discovery_request_contract import (
    CertifiedVenueDiscoveryRequestContract,
)
from .umd_048_venue_discovery_request_admission_gate import (
    CertifiedVenueDiscoveryRequestAdmissionDecision,
)

UMD_051_BUILD_ID = "UMD-051"
UMD_051_BUILD_NAME = "Certified Raw Venue Market Observation Contract"
UMD_051_REVISION = (
    "UMD_051_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_CONTRACT_V1"
)
UMD_051_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_pagination",
    "automatic_observation_creation",
    "canonical_market_construction",
    "classification_inference",
    "duplicate_resolution",
    "registry_mutation",
    "observation_persistence",
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


def _optional_text(
    value: str | None,
    field_name: str,
) -> str | None:
    if value is None:
        return None
    return _text(value, field_name)


def _token(value: str, field_name: str) -> str:
    normalized = _text(
        value,
        field_name,
    ).upper().replace("-", "_")
    if not all(
        character.isalnum() or character == "_"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} contains invalid characters"
        )
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


def _utc(
    value: datetime | None,
    field_name: str,
) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime or None")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _deep_freeze(value: Any, field_name: str) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(
                f"{field_name} cannot contain NaN or infinity"
            )
        return value
    if isinstance(value, Mapping):
        normalized = {}
        for key, item in value.items():
            normalized_key = _text(
                str(key),
                f"{field_name} key",
            )
            if normalized_key in normalized:
                raise ValueError(
                    f"{field_name} contains duplicate normalized keys"
                )
            normalized[normalized_key] = _deep_freeze(
                item,
                f"{field_name}.{normalized_key}",
            )
        return MappingProxyType(
            dict(sorted(normalized.items()))
        )
    if isinstance(value, (tuple, list)):
        return tuple(
            _deep_freeze(
                item,
                f"{field_name}[{index}]",
            )
            for index, item in enumerate(value)
        )
    raise TypeError(
        f"{field_name} must contain JSON-compatible immutable values"
    )


@dataclass(frozen=True, slots=True)
class CertifiedRawVenueMarketObservation:
    request_id: str
    request_hash: str
    admission_decision_id: str
    admission_decision_record_hash: str
    source_id: str
    source_contract_hash: str
    source_registry_hash: str
    canonical_venue_id: str
    adapter_key: str
    venue_market_id: str
    venue_event_id: str | None
    source_record_type: str
    raw_title: str
    raw_status: str
    raw_market_family: str
    source_schema_version: str
    raw_payload: Mapping[str, Any]
    raw_payload_hash: str
    retrieval_sequence: int
    observed_at: datetime
    source_emitted_at: datetime | None
    read_only: bool
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "request_id",
            _text(self.request_id, "request_id"),
        )
        object.__setattr__(
            self,
            "request_hash",
            _sha256(self.request_hash, "request_hash"),
        )
        object.__setattr__(
            self,
            "admission_decision_id",
            _text(
                self.admission_decision_id,
                "admission_decision_id",
            ),
        )
        object.__setattr__(
            self,
            "admission_decision_record_hash",
            _sha256(
                self.admission_decision_record_hash,
                "admission_decision_record_hash",
            ),
        )
        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, "source_id"),
        )
        object.__setattr__(
            self,
            "source_contract_hash",
            _sha256(
                self.source_contract_hash,
                "source_contract_hash",
            ),
        )
        object.__setattr__(
            self,
            "source_registry_hash",
            _sha256(
                self.source_registry_hash,
                "source_registry_hash",
            ),
        )
        object.__setattr__(
            self,
            "canonical_venue_id",
            _token(
                self.canonical_venue_id,
                "canonical_venue_id",
            ),
        )
        object.__setattr__(
            self,
            "adapter_key",
            _token(self.adapter_key, "adapter_key"),
        )
        object.__setattr__(
            self,
            "venue_market_id",
            _text(self.venue_market_id, "venue_market_id"),
        )
        object.__setattr__(
            self,
            "venue_event_id",
            _optional_text(
                self.venue_event_id,
                "venue_event_id",
            ),
        )
        object.__setattr__(
            self,
            "source_record_type",
            _token(
                self.source_record_type,
                "source_record_type",
            ),
        )
        object.__setattr__(
            self,
            "raw_title",
            _text(self.raw_title, "raw_title"),
        )
        object.__setattr__(
            self,
            "raw_status",
            _text(self.raw_status, "raw_status"),
        )
        object.__setattr__(
            self,
            "raw_market_family",
            _text(
                self.raw_market_family,
                "raw_market_family",
            ),
        )
        object.__setattr__(
            self,
            "source_schema_version",
            _text(
                self.source_schema_version,
                "source_schema_version",
            ),
        )

        frozen_payload = _deep_freeze(
            self.raw_payload,
            "raw_payload",
        )
        if not isinstance(frozen_payload, MappingProxyType):
            raise TypeError("raw_payload must be a mapping")
        object.__setattr__(
            self,
            "raw_payload",
            frozen_payload,
        )

        expected_payload_hash = deterministic_sha256(
            frozen_payload
        )
        supplied_payload_hash = _sha256(
            self.raw_payload_hash,
            "raw_payload_hash",
        )
        if supplied_payload_hash != expected_payload_hash:
            raise ValueError(
                "raw_payload_hash must match the exact raw payload"
            )
        object.__setattr__(
            self,
            "raw_payload_hash",
            supplied_payload_hash,
        )

        if not isinstance(self.retrieval_sequence, int):
            raise TypeError(
                "retrieval_sequence must be an integer"
            )
        if self.retrieval_sequence < 1:
            raise ValueError(
                "retrieval_sequence must be positive"
            )

        observed_at = _utc(
            self.observed_at,
            "observed_at",
        )
        source_emitted_at = _utc(
            self.source_emitted_at,
            "source_emitted_at",
        )
        object.__setattr__(
            self,
            "observed_at",
            observed_at,
        )
        object.__setattr__(
            self,
            "source_emitted_at",
            source_emitted_at,
        )
        if (
            source_emitted_at is not None
            and source_emitted_at > observed_at
        ):
            raise ValueError(
                "source_emitted_at must not follow observed_at"
            )

        if self.read_only is not True:
            raise ValueError(
                "raw venue market observations must be read-only"
            )

        frozen_metadata = _deep_freeze(
            self.metadata,
            "metadata",
        )
        if not isinstance(
            frozen_metadata,
            MappingProxyType,
        ):
            raise TypeError("metadata must be a mapping")
        object.__setattr__(
            self,
            "metadata",
            frozen_metadata,
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "observation lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_051_BUILD_ID:
            raise ValueError(
                "observation lineage must use build_id UMD-051"
            )

        required_parent_hashes = {
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
                "observation lineage must include request, decision, "
                "source-contract, source-registry, and raw-payload hashes"
            )

    @property
    def observation_id(self) -> str:
        return "umd:raw-venue-market-observation:" + deterministic_sha256(
            {
                "request_id": self.request_id,
                "source_id": self.source_id,
                "venue_market_id": self.venue_market_id,
                "retrieval_sequence": self.retrieval_sequence,
                "observed_at": self.observed_at,
                "raw_payload_hash": self.raw_payload_hash,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "observation_id": self.observation_id,
            "request_id": self.request_id,
            "request_hash": self.request_hash,
            "admission_decision_id": (
                self.admission_decision_id
            ),
            "admission_decision_record_hash": (
                self.admission_decision_record_hash
            ),
            "source_id": self.source_id,
            "source_contract_hash": (
                self.source_contract_hash
            ),
            "source_registry_hash": (
                self.source_registry_hash
            ),
            "canonical_venue_id": (
                self.canonical_venue_id
            ),
            "adapter_key": self.adapter_key,
            "venue_market_id": self.venue_market_id,
            "venue_event_id": self.venue_event_id,
            "source_record_type": (
                self.source_record_type
            ),
            "raw_title": self.raw_title,
            "raw_status": self.raw_status,
            "raw_market_family": (
                self.raw_market_family
            ),
            "source_schema_version": (
                self.source_schema_version
            ),
            "raw_payload": self.raw_payload,
            "raw_payload_hash": self.raw_payload_hash,
            "retrieval_sequence": (
                self.retrieval_sequence
            ),
            "observed_at": self.observed_at,
            "source_emitted_at": (
                self.source_emitted_at
            ),
            "read_only": self.read_only,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def observation_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_raw_venue_market_observation(
    request: CertifiedVenueDiscoveryRequestContract,
    admission_decision: CertifiedVenueDiscoveryRequestAdmissionDecision,
    *,
    venue_market_id: str,
    venue_event_id: str | None,
    source_record_type: str,
    raw_title: str,
    raw_status: str,
    raw_market_family: str,
    source_schema_version: str,
    raw_payload: Mapping[str, Any],
    retrieval_sequence: int,
    observed_at: datetime,
    source_emitted_at: datetime | None,
    metadata: Mapping[str, Any] | None,
    lineage: ImmutableLineage,
) -> CertifiedRawVenueMarketObservation:
    if not isinstance(
        request,
        CertifiedVenueDiscoveryRequestContract,
    ):
        raise TypeError(
            "request must be the certified UMD-047 request contract"
        )
    if not isinstance(
        admission_decision,
        CertifiedVenueDiscoveryRequestAdmissionDecision,
    ):
        raise TypeError(
            "admission_decision must be the certified UMD-048 decision"
        )
    if admission_decision.admitted is not True:
        raise ValueError(
            "raw observations require an admitted UMD-048 request"
        )

    if admission_decision.request_id != request.request_id:
        raise ValueError(
            "admission decision request_id does not match request"
        )
    if admission_decision.request_hash != request.request_hash:
        raise ValueError(
            "admission decision request_hash does not match request"
        )
    if admission_decision.source_id != request.source_id:
        raise ValueError(
            "admission decision source_id does not match request"
        )
    if (
        admission_decision.source_contract_hash
        != request.source_contract_hash
    ):
        raise ValueError(
            "source-contract hash mismatch"
        )
    if (
        admission_decision.source_registry_hash
        != request.source_registry_hash
    ):
        raise ValueError(
            "source-registry hash mismatch"
        )

    frozen_payload = _deep_freeze(
        raw_payload,
        "raw_payload",
    )
    if not isinstance(
        frozen_payload,
        MappingProxyType,
    ):
        raise TypeError("raw_payload must be a mapping")

    return CertifiedRawVenueMarketObservation(
        request_id=request.request_id,
        request_hash=request.request_hash,
        admission_decision_id=(
            admission_decision.decision_id
        ),
        admission_decision_record_hash=(
            admission_decision.record_hash
        ),
        source_id=request.source_id,
        source_contract_hash=(
            request.source_contract_hash
        ),
        source_registry_hash=(
            request.source_registry_hash
        ),
        canonical_venue_id=(
            request.canonical_venue_id
        ),
        adapter_key=request.adapter_key,
        venue_market_id=venue_market_id,
        venue_event_id=venue_event_id,
        source_record_type=source_record_type,
        raw_title=raw_title,
        raw_status=raw_status,
        raw_market_family=raw_market_family,
        source_schema_version=(
            source_schema_version
        ),
        raw_payload=frozen_payload,
        raw_payload_hash=deterministic_sha256(
            frozen_payload
        ),
        retrieval_sequence=retrieval_sequence,
        observed_at=observed_at,
        source_emitted_at=source_emitted_at,
        read_only=True,
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD051CertificationManifest:
    subsystem_id: str
    build_id: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    contract_mode: str
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
            "upstream_builds": (
                self.upstream_builds
            ),
            "contract_mode": self.contract_mode,
            "prohibited_capabilities": (
                self.prohibited_capabilities
            ),
            "network_enabled": self.network_enabled,
            "persistence_enabled": (
                self.persistence_enabled
            ),
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": (
                self.publication_enabled
            ),
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_051_certification_manifest() -> UMD051CertificationManifest:
    return UMD051CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_051_BUILD_ID,
        revision=UMD_051_REVISION,
        schema_version=UMD_051_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 51)
        ),
        contract_mode=(
            "deterministic_read_only_raw_observation"
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


def certify_raw_venue_market_observation(
    observation: CertifiedRawVenueMarketObservation,
) -> Mapping[str, Any]:
    if not isinstance(
        observation,
        CertifiedRawVenueMarketObservation,
    ):
        raise TypeError(
            "observation must be a certified UMD-051 raw observation"
        )

    checks = {
        "observation_identity_deterministic": (
            observation.observation_id
            == "umd:raw-venue-market-observation:"
            + deterministic_sha256(
                {
                    "request_id": observation.request_id,
                    "source_id": observation.source_id,
                    "venue_market_id": (
                        observation.venue_market_id
                    ),
                    "retrieval_sequence": (
                        observation.retrieval_sequence
                    ),
                    "observed_at": (
                        observation.observed_at
                    ),
                    "raw_payload_hash": (
                        observation.raw_payload_hash
                    ),
                }
            )
        ),
        "raw_payload_hash_valid": (
            observation.raw_payload_hash
            == deterministic_sha256(
                observation.raw_payload
            )
        ),
        "observation_hash_deterministic": (
            observation.observation_hash
            == deterministic_sha256(
                observation.to_canonical_dict()
            )
        ),
        "read_only_required": (
            observation.read_only is True
        ),
        "lineage_build_valid": (
            observation.lineage.build_id
            == UMD_051_BUILD_ID
        ),
        "lineage_complete": {
            observation.request_hash,
            observation.admission_decision_record_hash,
            observation.source_contract_hash,
            observation.source_registry_hash,
            observation.raw_payload_hash,
        }.issubset(
            set(observation.lineage.parent_hashes)
        ),
        "raw_payload_immutable": isinstance(
            observation.raw_payload,
            MappingProxyType,
        ),
        "network_not_invoked": True,
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "observation_id": (
                observation.observation_id
            ),
            "observation_hash": (
                observation.observation_hash
            ),
            "request_id": observation.request_id,
            "source_id": observation.source_id,
            "venue_market_id": (
                observation.venue_market_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_051_foundation() -> Mapping[str, Any]:
    manifest = build_umd_051_certification_manifest()
    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-051"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 51)
            )
        ),
        "raw_observation_mode": (
            manifest.contract_mode
            == "deterministic_read_only_raw_observation"
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


def verify_umd_051_raw_venue_market_observation_contract() -> bool:
    result = certify_umd_051_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-051 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
