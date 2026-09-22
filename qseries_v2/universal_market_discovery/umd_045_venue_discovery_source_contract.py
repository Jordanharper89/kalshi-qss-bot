from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)

UMD_045_BUILD_ID = "UMD-045"
UMD_045_BUILD_NAME = "Certified Venue Discovery Source Contract"
UMD_045_REVISION = (
    "UMD_045_CERTIFIED_VENUE_DISCOVERY_SOURCE_CONTRACT_V1"
)
UMD_045_SCHEMA_VERSION = "1.0.0"

ALLOWED_DISCOVERY_METHODS = (
    "REST_CATALOG",
    "GRAPHQL_CATALOG",
    "WEBSOCKET_CATALOG",
    "FILE_CATALOG",
    "DATABASE_CATALOG",
    "MANUAL_IMPORT",
)

ALLOWED_AUTHENTICATION_MODES = (
    "NONE",
    "API_KEY",
    "BEARER_TOKEN",
    "OAUTH2",
    "SIGNED_REQUEST",
    "SESSION_COOKIE",
)

ALLOWED_PAGINATION_MODES = (
    "NONE",
    "OFFSET",
    "PAGE_NUMBER",
    "CURSOR",
    "TOKEN",
    "TIME_WINDOW",
)

ALLOWED_MARKET_STATUS_CAPABILITIES = (
    "ACTIVE",
    "INACTIVE",
    "CLOSED",
    "SETTLED",
    "CANCELLED",
    "ARCHIVED",
)

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "credential_resolution",
    "market_scanning",
    "continuous_runtime",
    "automatic_discovery",
    "automatic_admission",
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


def _token(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).upper().replace("-", "_")
    if not all(
        character.isalnum() or character == "_"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, and underscores"
        )
    return normalized


def _sorted_unique_tokens(
    values: Tuple[str, ...],
    field_name: str,
) -> Tuple[str, ...]:
    if not isinstance(values, tuple):
        values = tuple(values)
    normalized = tuple(
        sorted(
            {
                _token(value, field_name)
                for value in values
            }
        )
    )
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("metadata must be a mapping")
    return MappingProxyType(
        dict(
            sorted(
                (str(key), item)
                for key, item in value.items()
            )
        )
    )


@dataclass(frozen=True, slots=True)
class CertifiedVenueDiscoverySourceContract:
    canonical_venue_id: str
    adapter_key: str
    display_name: str
    discovery_method: str
    authentication_mode: str
    pagination_mode: str
    supported_market_families: Tuple[str, ...]
    supported_statuses: Tuple[str, ...]
    source_schema_version: str
    supports_incremental_discovery: bool
    supports_historical_markets: bool
    supports_settlement_status: bool
    supports_cursor_resume: bool
    rate_limit_metadata_available: bool
    read_only: bool
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_venue_id",
            _token(self.canonical_venue_id, "canonical_venue_id"),
        )
        object.__setattr__(
            self,
            "adapter_key",
            _token(self.adapter_key, "adapter_key"),
        )
        object.__setattr__(
            self,
            "display_name",
            _text(self.display_name, "display_name"),
        )

        discovery_method = _token(
            self.discovery_method,
            "discovery_method",
        )
        if discovery_method not in ALLOWED_DISCOVERY_METHODS:
            raise ValueError(
                "discovery_method is not certified"
            )
        object.__setattr__(
            self,
            "discovery_method",
            discovery_method,
        )

        authentication_mode = _token(
            self.authentication_mode,
            "authentication_mode",
        )
        if authentication_mode not in ALLOWED_AUTHENTICATION_MODES:
            raise ValueError(
                "authentication_mode is not certified"
            )
        object.__setattr__(
            self,
            "authentication_mode",
            authentication_mode,
        )

        pagination_mode = _token(
            self.pagination_mode,
            "pagination_mode",
        )
        if pagination_mode not in ALLOWED_PAGINATION_MODES:
            raise ValueError(
                "pagination_mode is not certified"
            )
        object.__setattr__(
            self,
            "pagination_mode",
            pagination_mode,
        )

        object.__setattr__(
            self,
            "supported_market_families",
            _sorted_unique_tokens(
                self.supported_market_families,
                "supported_market_family",
            ),
        )

        statuses = _sorted_unique_tokens(
            self.supported_statuses,
            "supported_status",
        )
        unknown_statuses = tuple(
            status
            for status in statuses
            if status not in ALLOWED_MARKET_STATUS_CAPABILITIES
        )
        if unknown_statuses:
            raise ValueError(
                "unsupported market statuses: "
                + ", ".join(unknown_statuses)
            )
        object.__setattr__(
            self,
            "supported_statuses",
            statuses,
        )

        object.__setattr__(
            self,
            "source_schema_version",
            _text(
                self.source_schema_version,
                "source_schema_version",
            ),
        )

        for field_name in (
            "supports_incremental_discovery",
            "supports_historical_markets",
            "supports_settlement_status",
            "supports_cursor_resume",
            "rate_limit_metadata_available",
            "read_only",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"{field_name} must be boolean")

        if self.read_only is not True:
            raise ValueError(
                "venue discovery source contracts must be read-only"
            )

        if (
            self.supports_cursor_resume
            and self.pagination_mode not in ("CURSOR", "TOKEN")
        ):
            raise ValueError(
                "cursor resume requires CURSOR or TOKEN pagination"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "source-contract lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_045_BUILD_ID:
            raise ValueError(
                "source-contract lineage must use build_id UMD-045"
            )

    @property
    def source_id(self) -> str:
        return "umd:venue-discovery-source:" + deterministic_sha256(
            {
                "canonical_venue_id": self.canonical_venue_id,
                "adapter_key": self.adapter_key,
                "discovery_method": self.discovery_method,
                "source_schema_version": self.source_schema_version,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "source_id": self.source_id,
            "canonical_venue_id": self.canonical_venue_id,
            "adapter_key": self.adapter_key,
            "display_name": self.display_name,
            "discovery_method": self.discovery_method,
            "authentication_mode": self.authentication_mode,
            "pagination_mode": self.pagination_mode,
            "supported_market_families": (
                self.supported_market_families
            ),
            "supported_statuses": self.supported_statuses,
            "source_schema_version": self.source_schema_version,
            "supports_incremental_discovery": (
                self.supports_incremental_discovery
            ),
            "supports_historical_markets": (
                self.supports_historical_markets
            ),
            "supports_settlement_status": (
                self.supports_settlement_status
            ),
            "supports_cursor_resume": self.supports_cursor_resume,
            "rate_limit_metadata_available": (
                self.rate_limit_metadata_available
            ),
            "read_only": self.read_only,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def contract_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD045CertificationManifest:
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
            "upstream_builds": self.upstream_builds,
            "contract_mode": self.contract_mode,
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


def build_umd_045_certification_manifest() -> UMD045CertificationManifest:
    return UMD045CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_045_BUILD_ID,
        revision=UMD_045_REVISION,
        schema_version=UMD_045_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 45)
        ),
        contract_mode="deterministic_read_only_source_definition",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_venue_discovery_source_contract(
    source: CertifiedVenueDiscoverySourceContract,
) -> Mapping[str, Any]:
    if not isinstance(
        source,
        CertifiedVenueDiscoverySourceContract,
    ):
        raise TypeError(
            "source must be a certified UMD-045 source contract"
        )

    checks = {
        "source_identity_deterministic": (
            source.source_id
            == "umd:venue-discovery-source:"
            + deterministic_sha256(
                {
                    "canonical_venue_id": source.canonical_venue_id,
                    "adapter_key": source.adapter_key,
                    "discovery_method": source.discovery_method,
                    "source_schema_version": (
                        source.source_schema_version
                    ),
                }
            )
        ),
        "contract_hash_deterministic": (
            source.contract_hash
            == deterministic_sha256(
                source.to_canonical_dict()
            )
        ),
        "read_only_required": source.read_only is True,
        "market_families_present": (
            bool(source.supported_market_families)
        ),
        "statuses_present": bool(source.supported_statuses),
        "lineage_build_valid": (
            source.lineage.build_id == UMD_045_BUILD_ID
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
            "source_id": source.source_id,
            "contract_hash": source.contract_hash,
            "canonical_venue_id": source.canonical_venue_id,
            "adapter_key": source.adapter_key,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_045_foundation() -> Mapping[str, Any]:
    manifest = build_umd_045_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-045",
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 45)
            )
        ),
        "source_contract_mode": (
            manifest.contract_mode
            == "deterministic_read_only_source_definition"
        ),
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": manifest.execution_enabled is False,
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


def verify_umd_045_venue_discovery_source_contract() -> bool:
    result = certify_umd_045_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-045 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
