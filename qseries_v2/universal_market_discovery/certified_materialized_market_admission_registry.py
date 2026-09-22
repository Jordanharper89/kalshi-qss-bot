from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_admitted_market_materialization_contract import (
    CertifiedAdmittedMarketMaterialization,
)

UMD_015_BUILD_ID = "UMD-015"
UMD_015_BUILD_NAME = "Certified Materialized Market Admission Registry"
UMD_015_REVISION = (
    "UMD_015_CERTIFIED_MATERIALIZED_MARKET_ADMISSION_REGISTRY_V1"
)
UMD_015_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_registry_commit",
    "persistence_write",
    "registry_mutation",
    "market_deletion",
    "market_reordering",
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


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedMaterializedMarketAdmission:
    sequence_number: int
    previous_admission_hash: str | None
    materialization: CertifiedAdmittedMarketMaterialization
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.sequence_number, int):
            raise TypeError("sequence_number must be an integer")
        if self.sequence_number < 1:
            raise ValueError("sequence_number must be positive")

        if self.previous_admission_hash is None:
            if self.sequence_number != 1:
                raise ValueError(
                    "only the first admission may omit previous_admission_hash"
                )
        else:
            previous = _text(
                self.previous_admission_hash,
                "previous_admission_hash",
            ).lower()
            if len(previous) != 64:
                raise ValueError(
                    "previous_admission_hash must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in previous
            ):
                raise ValueError(
                    "previous_admission_hash must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                "previous_admission_hash",
                previous,
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("admission lineage must belong to UMD")
        if self.lineage.build_id != UMD_015_BUILD_ID:
            raise ValueError(
                "admission lineage must use build_id UMD-015"
            )
        if (
            self.materialization.record_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "admission lineage must include materialization record hash"
            )
        if (
            self.previous_admission_hash is not None
            and self.previous_admission_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "admission lineage must include previous admission hash"
            )

    @property
    def admission_id(self) -> str:
        return "umd:market-admission:" + deterministic_sha256(
            {
                "sequence_number": self.sequence_number,
                "previous_admission_hash": self.previous_admission_hash,
                "materialization_id": (
                    self.materialization.materialization_id
                ),
                "canonical_market_id": (
                    self.materialization.market.canonical_market_id
                ),
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "admission_id": self.admission_id,
            "sequence_number": self.sequence_number,
            "previous_admission_hash": self.previous_admission_hash,
            "materialization": self.materialization,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def admission_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlyMaterializedMarketAdmissionRegistry:
    admissions: Tuple[CertifiedMaterializedMarketAdmission, ...]
    preexisting_markets: Tuple[CertifiedCanonicalMarket, ...]
    registry_lineage: ImmutableLineage
    _by_admission_id: Mapping[
        str,
        CertifiedMaterializedMarketAdmission,
    ] = field(init=False, repr=False)
    _by_market_id: Mapping[
        str,
        CertifiedMaterializedMarketAdmission,
    ] = field(init=False, repr=False)
    _by_materialization_id: Mapping[
        str,
        CertifiedMaterializedMarketAdmission,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered_admissions = tuple(
            sorted(
                self.admissions,
                key=lambda admission: admission.sequence_number,
            )
        )
        ordered_preexisting = tuple(
            sorted(
                self.preexisting_markets,
                key=lambda market: market.canonical_market_id,
            )
        )

        object.__setattr__(
            self,
            "admissions",
            ordered_admissions,
        )
        object.__setattr__(
            self,
            "preexisting_markets",
            ordered_preexisting,
        )

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("registry lineage must belong to UMD")
        if self.registry_lineage.build_id != UMD_015_BUILD_ID:
            raise ValueError(
                "registry lineage must use build_id UMD-015"
            )

        preexisting_market_ids = {
            market.canonical_market_id
            for market in ordered_preexisting
        }
        if len(preexisting_market_ids) != len(ordered_preexisting):
            raise ValueError(
                "duplicate canonical market IDs in preexisting markets"
            )

        by_admission_id = {}
        by_market_id = {}
        by_materialization_id = {}
        previous_admission = None

        for expected_sequence, admission in enumerate(
            ordered_admissions,
            start=1,
        ):
            if admission.sequence_number != expected_sequence:
                raise ValueError(
                    "admission sequence must be contiguous and start at 1"
                )

            if previous_admission is None:
                if admission.previous_admission_hash is not None:
                    raise ValueError(
                        "first admission must not have previous hash"
                    )
            else:
                if (
                    admission.previous_admission_hash
                    != previous_admission.admission_hash
                ):
                    raise ValueError(
                        "previous-admission hash chain mismatch"
                    )

            market_id = (
                admission.materialization.market.canonical_market_id
            )
            materialization_id = (
                admission.materialization.materialization_id
            )

            if market_id in preexisting_market_ids:
                raise ValueError(
                    "materialized market already exists in canonical registry"
                )
            if admission.admission_id in by_admission_id:
                raise ValueError("duplicate admission ID")
            if market_id in by_market_id:
                raise ValueError(
                    "canonical market may be admitted only once"
                )
            if materialization_id in by_materialization_id:
                raise ValueError(
                    "materialization may be admitted only once"
                )

            by_admission_id[admission.admission_id] = admission
            by_market_id[market_id] = admission
            by_materialization_id[
                materialization_id
            ] = admission
            previous_admission = admission

        object.__setattr__(
            self,
            "_by_admission_id",
            MappingProxyType(by_admission_id),
        )
        object.__setattr__(
            self,
            "_by_market_id",
            MappingProxyType(by_market_id),
        )
        object.__setattr__(
            self,
            "_by_materialization_id",
            MappingProxyType(by_materialization_id),
        )

    def get(
        self,
        admission_id: str,
    ) -> CertifiedMaterializedMarketAdmission | None:
        return self._by_admission_id.get(
            _text(admission_id, "admission_id")
        )

    def get_by_market(
        self,
        canonical_market_id: str,
    ) -> CertifiedMaterializedMarketAdmission | None:
        return self._by_market_id.get(
            _text(canonical_market_id, "canonical_market_id")
        )

    def get_by_materialization(
        self,
        materialization_id: str,
    ) -> CertifiedMaterializedMarketAdmission | None:
        return self._by_materialization_id.get(
            _text(materialization_id, "materialization_id")
        )

    def admitted_markets(
        self,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        return tuple(
            admission.materialization.market
            for admission in self.admissions
        )

    def complete_market_view(
        self,
    ) -> Tuple[CertifiedCanonicalMarket, ...]:
        combined = (
            self.preexisting_markets
            + self.admitted_markets()
        )
        return tuple(
            sorted(
                combined,
                key=lambda market: market.canonical_market_id,
            )
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "append_only_read_only",
            "admissions": self.admissions,
            "preexisting_market_hashes": tuple(
                market.record_hash
                for market in self.preexisting_markets
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD015CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    registry_mode: str
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
            "registry_mode": self.registry_mode,
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


def build_umd_015_certification_manifest() -> UMD015CertificationManifest:
    return UMD015CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_015_BUILD_ID,
        build_name=UMD_015_BUILD_NAME,
        revision=UMD_015_REVISION,
        schema_version=UMD_015_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 15)
        ),
        registry_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_materialized_market_admission_registry(
    registry: ReadOnlyMaterializedMarketAdmissionRegistry,
) -> Mapping[str, Any]:
    checks = {
        "admission_ids_unique": len(
            {
                admission.admission_id
                for admission in registry.admissions
            }
        )
        == len(registry.admissions),
        "market_ids_unique": len(
            {
                admission.materialization.market.canonical_market_id
                for admission in registry.admissions
            }
        )
        == len(registry.admissions),
        "materialization_ids_unique": len(
            {
                admission.materialization.materialization_id
                for admission in registry.admissions
            }
        )
        == len(registry.admissions),
        "sequence_contiguous": tuple(
            admission.sequence_number
            for admission in registry.admissions
        )
        == tuple(range(1, len(registry.admissions) + 1)),
        "complete_view_unique": len(
            {
                market.canonical_market_id
                for market in registry.complete_market_view()
            }
        )
        == len(registry.complete_market_view()),
        "deterministic_replay": (
            registry.registry_hash
            == deterministic_sha256(registry.to_canonical_dict())
        ),
        "read_only_indexes": isinstance(
            registry._by_admission_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_market_id,
            MappingProxyType,
        )
        and isinstance(
            registry._by_materialization_id,
            MappingProxyType,
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return MappingProxyType(
        {
            "certified": not failed,
            "registry_hash": registry.registry_hash,
            "admission_count": len(registry.admissions),
            "preexisting_market_count": len(
                registry.preexisting_markets
            ),
            "complete_market_count": len(
                registry.complete_market_view()
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_015_foundation() -> Mapping[str, Any]:
    manifest = build_umd_015_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-015",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}" for number in range(1, 15)
        ),
        "append_only_read_only": (
            manifest.registry_mode
            == "append_only_read_only"
        ),
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(manifest.to_canonical_dict())
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


def verify_umd_015_certified_materialized_market_admission_registry() -> bool:
    result = certify_umd_015_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-015 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_015_BUILD_ID",
    "UMD_015_BUILD_NAME",
    "UMD_015_REVISION",
    "UMD_015_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedMaterializedMarketAdmission",
    "ReadOnlyMaterializedMarketAdmissionRegistry",
    "UMD015CertificationManifest",
    "build_umd_015_certification_manifest",
    "certify_materialized_market_admission_registry",
    "certify_umd_015_foundation",
    "verify_umd_015_certified_materialized_market_admission_registry",
]
