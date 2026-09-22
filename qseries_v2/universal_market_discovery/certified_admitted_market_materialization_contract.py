from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_incremental_discovery_batch_contract import (
    CertifiedIncrementalDiscoveryBatch,
)
from .certified_discovery_admission_ledger import (
    CertifiedDiscoveryAdmissionLedgerEntry,
)

UMD_014_BUILD_ID = "UMD-014"
UMD_014_BUILD_NAME = "Certified Admitted Market Materialization Contract"
UMD_014_REVISION = (
    "UMD_014_CERTIFIED_ADMITTED_MARKET_MATERIALIZATION_CONTRACT_V1"
)
UMD_014_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_registry_commit",
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


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedAdmittedMarketMaterialization:
    ledger_entry_id: str
    admission_decision_id: str
    batch_id: str
    source_id: str
    source_market_key: str
    candidate_id: str
    market: CertifiedCanonicalMarket
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        for field_name, prefix in (
            ("ledger_entry_id", "umd:admission-ledger-entry:"),
            ("admission_decision_id", "umd:admission:"),
            ("batch_id", "umd:batch:"),
            ("candidate_id", "umd:candidate:"),
        ):
            value = _text(getattr(self, field_name), field_name)
            if not value.startswith(prefix):
                raise ValueError(
                    f"{field_name} must use prefix {prefix}"
                )
            object.__setattr__(self, field_name, value)

        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, "source_id").lower(),
        )
        object.__setattr__(
            self,
            "source_market_key",
            _text(self.source_market_key, "source_market_key"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("materialization lineage must belong to UMD")
        if self.lineage.build_id != UMD_014_BUILD_ID:
            raise ValueError(
                "materialization lineage must use build_id UMD-014"
            )

    @property
    def materialization_id(self) -> str:
        return "umd:materialization:" + deterministic_sha256(
            {
                "ledger_entry_id": self.ledger_entry_id,
                "candidate_id": self.candidate_id,
                "canonical_market_id": self.market.canonical_market_id,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "materialization_id": self.materialization_id,
            "ledger_entry_id": self.ledger_entry_id,
            "admission_decision_id": self.admission_decision_id,
            "batch_id": self.batch_id,
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "candidate_id": self.candidate_id,
            "canonical_market_id": self.market.canonical_market_id,
            "market_record_hash": self.market.record_hash,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def materialize_admitted_batch(
    batch: CertifiedIncrementalDiscoveryBatch,
    ledger_entry: CertifiedDiscoveryAdmissionLedgerEntry,
    *,
    metadata: Mapping[str, Any],
    lineage_factory,
) -> Tuple[CertifiedAdmittedMarketMaterialization, ...]:
    decision = ledger_entry.decision

    if not decision.admitted:
        raise ValueError("rejected admission decisions cannot be materialized")
    if decision.batch_id != batch.batch_id:
        raise ValueError("ledger decision batch_id does not match batch")
    if decision.batch_hash != batch.batch_hash:
        raise ValueError("ledger decision batch_hash does not match batch")
    if decision.source_id != batch.source_id:
        raise ValueError("ledger decision source_id does not match batch")
    if decision.batch_sequence != batch.batch_sequence:
        raise ValueError(
            "ledger decision batch_sequence does not match batch"
        )

    materializations = []
    seen_market_ids = set()

    for candidate in batch.candidates:
        market_id = candidate.market.canonical_market_id
        if market_id in seen_market_ids:
            raise ValueError(
                "batch cannot materialize the same canonical market twice"
            )
        seen_market_ids.add(market_id)

        lineage = lineage_factory(
            candidate,
            ledger_entry,
        )
        required_parents = {
            candidate.record_hash,
            ledger_entry.entry_hash,
            decision.record_hash,
            batch.batch_hash,
        }
        if not required_parents.issubset(
            set(lineage.parent_hashes)
        ):
            raise ValueError(
                "materialization lineage is missing required parents"
            )

        materializations.append(
            CertifiedAdmittedMarketMaterialization(
                ledger_entry_id=ledger_entry.entry_id,
                admission_decision_id=decision.decision_id,
                batch_id=batch.batch_id,
                source_id=candidate.source_id,
                source_market_key=candidate.source_market_key,
                candidate_id=candidate.candidate_id,
                market=candidate.market,
                metadata=metadata,
                lineage=lineage,
            )
        )

    return tuple(
        sorted(
            materializations,
            key=lambda item: item.materialization_id,
        )
    )


@dataclass(frozen=True, slots=True)
class ReadOnlyAdmittedMarketMaterializationRegistry:
    materializations: Tuple[
        CertifiedAdmittedMarketMaterialization,
        ...
    ]

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.materializations,
                key=lambda item: item.materialization_id,
            )
        )
        object.__setattr__(self, "materializations", ordered)

        materialization_ids = {
            item.materialization_id for item in ordered
        }
        candidate_ids = {
            item.candidate_id for item in ordered
        }
        market_ids = {
            item.market.canonical_market_id for item in ordered
        }

        if len(materialization_ids) != len(ordered):
            raise ValueError("duplicate materialization ID")
        if len(candidate_ids) != len(ordered):
            raise ValueError("candidate may be materialized only once")
        if len(market_ids) != len(ordered):
            raise ValueError(
                "canonical market may be materialized only once"
            )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "materializations": self.materializations,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD014CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
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
            "build_name": self.build_name,
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
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_014_certification_manifest() -> UMD014CertificationManifest:
    return UMD014CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_014_BUILD_ID,
        build_name=UMD_014_BUILD_NAME,
        revision=UMD_014_REVISION,
        schema_version=UMD_014_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 14)
        ),
        contract_mode="read_only_materialization",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_014_foundation() -> Mapping[str, Any]:
    manifest = build_umd_014_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-014",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}" for number in range(1, 14)
        ),
        "read_only_materialization": (
            manifest.contract_mode
            == "read_only_materialization"
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


def verify_umd_014_certified_admitted_market_materialization_contract() -> bool:
    result = certify_umd_014_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-014 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_014_BUILD_ID",
    "UMD_014_BUILD_NAME",
    "UMD_014_REVISION",
    "UMD_014_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedAdmittedMarketMaterialization",
    "materialize_admitted_batch",
    "ReadOnlyAdmittedMarketMaterializationRegistry",
    "UMD014CertificationManifest",
    "build_umd_014_certification_manifest",
    "certify_umd_014_foundation",
    "verify_umd_014_certified_admitted_market_materialization_contract",
]
