from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_execution_ledger import (
    CertifiedActiveMarketQueryExecutionLedgerEntry,
    ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
)

UMD_027_BUILD_ID = "UMD-027"
UMD_027_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Execution Read Model"
)
UMD_027_REVISION = (
    "UMD_027_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_READ_MODEL_V1"
)
UMD_027_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_execution_commit",
    "execution_persistence",
    "ledger_mutation",
    "read_model_mutation",
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


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQueryExecutionReadModel:
    ledger: ReadOnlyActiveMarketQueryExecutionAdmissionLedger
    lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_query_id: Mapping[
        str,
        Tuple[CertifiedActiveMarketQueryExecutionLedgerEntry, ...],
    ] = field(init=False, repr=False)
    _by_result_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _admitted_entries: Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ] = field(init=False, repr=False)
    _rejected_entries: Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_027_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-027"
            )
        if self.ledger.ledger_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "read-model lineage must include execution ledger hash"
            )

        by_entry_id = {}
        by_execution_id = {}
        by_query_id = {}
        by_result_id = {}
        admitted_entries = []
        rejected_entries = []

        for entry in self.ledger.entries:
            decision = entry.decision

            if entry.entry_id in by_entry_id:
                raise ValueError("duplicate execution-ledger entry ID")
            if decision.execution_id in by_execution_id:
                raise ValueError("duplicate execution ID")
            if decision.result_id in by_result_id:
                raise ValueError("duplicate result ID")

            by_entry_id[entry.entry_id] = entry
            by_execution_id[decision.execution_id] = entry
            by_result_id[decision.result_id] = entry
            by_query_id.setdefault(
                decision.query_id,
                [],
            ).append(entry)

            if decision.admitted:
                admitted_entries.append(entry)
            else:
                rejected_entries.append(entry)

        object.__setattr__(
            self,
            "_by_entry_id",
            MappingProxyType(by_entry_id),
        )
        object.__setattr__(
            self,
            "_by_execution_id",
            MappingProxyType(by_execution_id),
        )
        object.__setattr__(
            self,
            "_by_query_id",
            MappingProxyType(
                {
                    query_id: tuple(
                        sorted(
                            entries,
                            key=lambda item: item.sequence_number,
                        )
                    )
                    for query_id, entries in by_query_id.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_result_id",
            MappingProxyType(by_result_id),
        )
        object.__setattr__(
            self,
            "_admitted_entries",
            tuple(admitted_entries),
        )
        object.__setattr__(
            self,
            "_rejected_entries",
            tuple(rejected_entries),
        )

    @property
    def entry_count(self) -> int:
        return len(self.ledger.entries)

    @property
    def admitted_count(self) -> int:
        return len(self._admitted_entries)

    @property
    def rejected_count(self) -> int:
        return len(self._rejected_entries)

    def get_entry(
        self,
        entry_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_by_execution(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_execution_id.get(
            _text(execution_id, "execution_id")
        )

    def by_query(
        self,
        query_id: str,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._by_query_id.get(
            _text(query_id, "query_id"),
            (),
        )

    def get_by_result(
        self,
        result_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_result_id.get(
            _text(result_id, "result_id")
        )

    def admitted_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._admitted_entries

    def rejected_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._rejected_entries

    def latest_entry(
        self,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        if not self.ledger.entries:
            return None
        return self.ledger.entries[-1]

    def latest_admitted(
        self,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        if not self._admitted_entries:
            return None
        return self._admitted_entries[-1]

    def query_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_query_id))

    def execution_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_execution_id))

    def result_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_result_id))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_mode": "execution_history_read_only",
            "ledger_hash": self.ledger.ledger_hash,
            "entry_ids": tuple(
                entry.entry_id
                for entry in self.ledger.entries
            ),
            "admitted_entry_ids": tuple(
                entry.entry_id
                for entry in self._admitted_entries
            ),
            "rejected_entry_ids": tuple(
                entry.entry_id
                for entry in self._rejected_entries
            ),
            "query_index": {
                query_id: tuple(
                    entry.entry_id
                    for entry in self._by_query_id[query_id]
                )
                for query_id in self.query_ids()
            },
            "execution_ids": self.execution_ids(),
            "result_ids": self.result_ids(),
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD027CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    read_model_mode: str
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
            "read_model_mode": self.read_model_mode,
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


def build_umd_027_certification_manifest() -> UMD027CertificationManifest:
    return UMD027CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_027_BUILD_ID,
        build_name=UMD_027_BUILD_NAME,
        revision=UMD_027_REVISION,
        schema_version=UMD_027_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 27)
        ),
        read_model_mode="execution_history_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_execution_read_model(
    read_model: CertifiedActiveMarketQueryExecutionReadModel,
) -> Mapping[str, Any]:
    checks = {
        "entry_count_matches": (
            read_model.entry_count
            == len(read_model.ledger.entries)
        ),
        "admitted_rejected_partition": (
            read_model.admitted_count
            + read_model.rejected_count
            == read_model.entry_count
        ),
        "execution_ids_unique": (
            len(read_model.execution_ids())
            == read_model.entry_count
        ),
        "result_ids_unique": (
            len(read_model.result_ids())
            == read_model.entry_count
        ),
        "query_ids_deterministic": (
            read_model.query_ids()
            == tuple(sorted(read_model.query_ids()))
        ),
        "execution_ids_deterministic": (
            read_model.execution_ids()
            == tuple(sorted(read_model.execution_ids()))
        ),
        "result_ids_deterministic": (
            read_model.result_ids()
            == tuple(sorted(read_model.result_ids()))
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                read_model._by_entry_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_execution_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_query_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_result_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = read_model.latest_admitted()

    return MappingProxyType(
        {
            "certified": not failed,
            "read_model_hash": read_model.read_model_hash,
            "ledger_hash": read_model.ledger.ledger_hash,
            "entry_count": read_model.entry_count,
            "admitted_count": read_model.admitted_count,
            "rejected_count": read_model.rejected_count,
            "query_count": len(read_model.query_ids()),
            "latest_admitted_execution_id": (
                None
                if latest is None
                else latest.decision.execution_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_027_foundation() -> Mapping[str, Any]:
    manifest = build_umd_027_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-027"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 27)
            )
        ),
        "execution_history_read_only": (
            manifest.read_model_mode
            == "execution_history_read_only"
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


def verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model() -> bool:
    result = certify_umd_027_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-027 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_027_BUILD_ID",
    "UMD_027_BUILD_NAME",
    "UMD_027_REVISION",
    "UMD_027_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecutionReadModel",
    "UMD027CertificationManifest",
    "build_umd_027_certification_manifest",
    "certify_active_market_query_execution_read_model",
    "certify_umd_027_foundation",
    "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model",
]
