from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .umd_059_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger import (
    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
)

UMD_060_BUILD_ID = "UMD-060"
UMD_060_BUILD_NAME = (
    "Certified Raw Venue Market Observation Admission Ledger "
    "Read Model Admission Ledger Read Model Admission Ledger Read Model"
)
UMD_060_REVISION = (
    "UMD_060_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"
    "ADMISSION_LEDGER_READ_MODEL_V1"
)
UMD_060_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_observation_creation",
    "automatic_admission",
    "ledger_append",
    "ledger_mutation",
    "read_model_mutation",
    "read_model_persistence",
    "canonical_market_construction",
    "classification_inference",
    "duplicate_resolution",
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
class CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel:
    source_ledger_hash: str
    total_entry_count: int
    admitted_entry_count: int
    rejected_entry_count: int
    ordered_entry_ids: Tuple[str, ...]
    ordered_read_model_ids: Tuple[str, ...]
    ordered_read_model_hashes: Tuple[str, ...]
    ordered_source_ledger_hashes: Tuple[str, ...]
    ordered_decision_ids: Tuple[str, ...]
    admitted_entry_ids: Tuple[str, ...]
    rejected_entry_ids: Tuple[str, ...]
    latest_entry_id: str | None
    latest_admitted_entry_id: str | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage
    _entry_position_by_id: Mapping[str, int] = field(
        init=False,
        repr=False,
    )
    _read_model_position_by_id: Mapping[str, int] = field(
        init=False,
        repr=False,
    )
    _read_model_position_by_hash: Mapping[str, int] = field(
        init=False,
        repr=False,
    )
    _source_ledger_position_by_hash: Mapping[str, int] = field(
        init=False,
        repr=False,
    )
    _decision_position_by_id: Mapping[str, int] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_ledger_hash",
            _sha256(
                self.source_ledger_hash,
                "source_ledger_hash",
            ),
        )

        for field_name in (
            "total_entry_count",
            "admitted_entry_count",
            "rejected_entry_count",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")

        if (
            self.admitted_entry_count
            + self.rejected_entry_count
            != self.total_entry_count
        ):
            raise ValueError(
                "admitted and rejected counts must partition total count"
            )

        for field_name in (
            "ordered_entry_ids",
            "ordered_read_model_ids",
            "ordered_read_model_hashes",
            "ordered_source_ledger_hashes",
            "ordered_decision_ids",
            "admitted_entry_ids",
            "rejected_entry_ids",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, tuple):
                object.__setattr__(
                    self,
                    field_name,
                    tuple(value),
                )

        ordered_entry_ids = tuple(
            _text(value, "ordered_entry_id")
            for value in self.ordered_entry_ids
        )
        ordered_read_model_ids = tuple(
            _text(value, "ordered_read_model_id")
            for value in self.ordered_read_model_ids
        )
        ordered_read_model_hashes = tuple(
            _sha256(value, "ordered_read_model_hash")
            for value in self.ordered_read_model_hashes
        )
        ordered_source_ledger_hashes = tuple(
            _sha256(value, "ordered_source_ledger_hash")
            for value in self.ordered_source_ledger_hashes
        )
        ordered_decision_ids = tuple(
            _text(value, "ordered_decision_id")
            for value in self.ordered_decision_ids
        )
        admitted_entry_ids = tuple(
            _text(value, "admitted_entry_id")
            for value in self.admitted_entry_ids
        )
        rejected_entry_ids = tuple(
            _text(value, "rejected_entry_id")
            for value in self.rejected_entry_ids
        )

        for field_name, value in (
            ("ordered_entry_ids", ordered_entry_ids),
            ("ordered_read_model_ids", ordered_read_model_ids),
            ("ordered_read_model_hashes", ordered_read_model_hashes),
            (
                "ordered_source_ledger_hashes",
                ordered_source_ledger_hashes,
            ),
            ("ordered_decision_ids", ordered_decision_ids),
            ("admitted_entry_ids", admitted_entry_ids),
            ("rejected_entry_ids", rejected_entry_ids),
        ):
            object.__setattr__(self, field_name, value)

        for values in (
            ordered_entry_ids,
            ordered_read_model_ids,
            ordered_read_model_hashes,
            ordered_source_ledger_hashes,
            ordered_decision_ids,
        ):
            if len(values) != self.total_entry_count:
                raise ValueError(
                    "ordered identity collections must equal total count"
                )

        for name, values in (
            ("ordered_entry_ids", ordered_entry_ids),
            ("ordered_read_model_ids", ordered_read_model_ids),
            ("ordered_read_model_hashes", ordered_read_model_hashes),
            (
                "ordered_source_ledger_hashes",
                ordered_source_ledger_hashes,
            ),
            ("ordered_decision_ids", ordered_decision_ids),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must be unique")

        if len(admitted_entry_ids) != self.admitted_entry_count:
            raise ValueError(
                "admitted_entry_ids length must equal admitted count"
            )
        if len(rejected_entry_ids) != self.rejected_entry_count:
            raise ValueError(
                "rejected_entry_ids length must equal rejected count"
            )

        if set(admitted_entry_ids).intersection(rejected_entry_ids):
            raise ValueError(
                "admitted and rejected entry IDs must be disjoint"
            )
        if (
            set(admitted_entry_ids).union(rejected_entry_ids)
            != set(ordered_entry_ids)
        ):
            raise ValueError(
                "admission partitions must cover all ordered entries"
            )

        if self.latest_entry_id is None:
            if ordered_entry_ids:
                raise ValueError(
                    "latest_entry_id required when entries exist"
                )
        else:
            object.__setattr__(
                self,
                "latest_entry_id",
                _text(
                    self.latest_entry_id,
                    "latest_entry_id",
                ),
            )
            if self.latest_entry_id != ordered_entry_ids[-1]:
                raise ValueError(
                    "latest_entry_id must equal final ordered entry ID"
                )

        if self.latest_admitted_entry_id is None:
            if admitted_entry_ids:
                raise ValueError(
                    "latest_admitted_entry_id required when admitted entries exist"
                )
        else:
            object.__setattr__(
                self,
                "latest_admitted_entry_id",
                _text(
                    self.latest_admitted_entry_id,
                    "latest_admitted_entry_id",
                ),
            )
            if (
                self.latest_admitted_entry_id
                != admitted_entry_ids[-1]
            ):
                raise ValueError(
                    "latest_admitted_entry_id must equal final admitted entry ID"
                )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "read-model lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_060_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-060"
            )
        if (
            self.source_ledger_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "read-model lineage must include source ledger hash"
            )

        object.__setattr__(
            self,
            "_entry_position_by_id",
            MappingProxyType(
                {
                    value: index
                    for index, value in enumerate(
                        ordered_entry_ids,
                        start=1,
                    )
                }
            ),
        )
        object.__setattr__(
            self,
            "_read_model_position_by_id",
            MappingProxyType(
                {
                    value: index
                    for index, value in enumerate(
                        ordered_read_model_ids,
                        start=1,
                    )
                }
            ),
        )
        object.__setattr__(
            self,
            "_read_model_position_by_hash",
            MappingProxyType(
                {
                    value: index
                    for index, value in enumerate(
                        ordered_read_model_hashes,
                        start=1,
                    )
                }
            ),
        )
        object.__setattr__(
            self,
            "_source_ledger_position_by_hash",
            MappingProxyType(
                {
                    value: index
                    for index, value in enumerate(
                        ordered_source_ledger_hashes,
                        start=1,
                    )
                }
            ),
        )
        object.__setattr__(
            self,
            "_decision_position_by_id",
            MappingProxyType(
                {
                    value: index
                    for index, value in enumerate(
                        ordered_decision_ids,
                        start=1,
                    )
                }
            ),
        )

    @property
    def read_model_id(self) -> str:
        return (
            "umd:raw-observation-rm-admission-ledger-"
            "rm-admission-ledger-read-model:"
            + deterministic_sha256(
                {
                    "source_ledger_hash": self.source_ledger_hash,
                    "ordered_entry_ids": self.ordered_entry_ids,
                    "ordered_read_model_ids": self.ordered_read_model_ids,
                    "ordered_read_model_hashes": (
                        self.ordered_read_model_hashes
                    ),
                    "ordered_source_ledger_hashes": (
                        self.ordered_source_ledger_hashes
                    ),
                    "ordered_decision_ids": (
                        self.ordered_decision_ids
                    ),
                }
            )
        )

    def entry_position(
        self,
        entry_id: str,
    ) -> int | None:
        return self._entry_position_by_id.get(
            _text(entry_id, "entry_id")
        )

    def read_model_position(
        self,
        read_model_id: str,
    ) -> int | None:
        return self._read_model_position_by_id.get(
            _text(read_model_id, "read_model_id")
        )

    def read_model_hash_position(
        self,
        read_model_hash: str,
    ) -> int | None:
        return self._read_model_position_by_hash.get(
            _sha256(
                read_model_hash,
                "read_model_hash",
            )
        )

    def source_ledger_hash_position(
        self,
        source_ledger_hash: str,
    ) -> int | None:
        return self._source_ledger_position_by_hash.get(
            _sha256(
                source_ledger_hash,
                "source_ledger_hash",
            )
        )

    def decision_position(
        self,
        decision_id: str,
    ) -> int | None:
        return self._decision_position_by_id.get(
            _text(decision_id, "decision_id")
        )

    def is_admitted_entry(
        self,
        entry_id: str,
    ) -> bool:
        return (
            _text(entry_id, "entry_id")
            in self.admitted_entry_ids
        )

    def is_rejected_entry(
        self,
        entry_id: str,
    ) -> bool:
        return (
            _text(entry_id, "entry_id")
            in self.rejected_entry_ids
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_id": self.read_model_id,
            "source_ledger_hash": self.source_ledger_hash,
            "total_entry_count": self.total_entry_count,
            "admitted_entry_count": self.admitted_entry_count,
            "rejected_entry_count": self.rejected_entry_count,
            "ordered_entry_ids": self.ordered_entry_ids,
            "ordered_read_model_ids": (
                self.ordered_read_model_ids
            ),
            "ordered_read_model_hashes": (
                self.ordered_read_model_hashes
            ),
            "ordered_source_ledger_hashes": (
                self.ordered_source_ledger_hashes
            ),
            "ordered_decision_ids": (
                self.ordered_decision_ids
            ),
            "admitted_entry_ids": self.admitted_entry_ids,
            "rejected_entry_ids": self.rejected_entry_ids,
            "latest_entry_id": self.latest_entry_id,
            "latest_admitted_entry_id": (
                self.latest_admitted_entry_id
            ),
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_060_admission_ledger_read_model(
    ledger: ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
    *,
    metadata: Mapping[str, Any] | None = None,
    lineage: ImmutableLineage,
) -> CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel:
    if not isinstance(
        ledger,
        ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,
    ):
        raise TypeError(
            "ledger must be the exact certified UMD-059 admission ledger"
        )

    entries = ledger.entries
    admitted = ledger.admitted_entries()
    rejected = ledger.rejected_entries()

    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel(
        source_ledger_hash=ledger.ledger_hash,
        total_entry_count=len(entries),
        admitted_entry_count=len(admitted),
        rejected_entry_count=len(rejected),
        ordered_entry_ids=tuple(
            entry.entry_id
            for entry in entries
        ),
        ordered_read_model_ids=tuple(
            entry.decision.read_model_id
            for entry in entries
        ),
        ordered_read_model_hashes=tuple(
            entry.decision.read_model_hash
            for entry in entries
        ),
        ordered_source_ledger_hashes=tuple(
            entry.decision.source_ledger_hash
            for entry in entries
        ),
        ordered_decision_ids=tuple(
            entry.decision.decision_id
            for entry in entries
        ),
        admitted_entry_ids=tuple(
            entry.entry_id
            for entry in admitted
        ),
        rejected_entry_ids=tuple(
            entry.entry_id
            for entry in rejected
        ),
        latest_entry_id=(
            None
            if not entries
            else entries[-1].entry_id
        ),
        latest_admitted_entry_id=(
            None
            if not admitted
            else admitted[-1].entry_id
        ),
        metadata=(
            {}
            if metadata is None
            else metadata
        ),
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD060CertificationManifest:
    subsystem_id: str
    build_id: str
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
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "read_model_mode": self.read_model_mode,
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


def build_umd_060_certification_manifest() -> UMD060CertificationManifest:
    return UMD060CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_060_BUILD_ID,
        revision=UMD_060_REVISION,
        schema_version=UMD_060_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 60)
        ),
        read_model_mode="deterministic_read_only_projection",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_060_read_model(
    read_model: CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,
) -> Mapping[str, Any]:
    checks = {
        "count_partition_valid": (
            read_model.admitted_entry_count
            + read_model.rejected_entry_count
            == read_model.total_entry_count
        ),
        "ordered_collections_valid": all(
            len(values) == read_model.total_entry_count
            for values in (
                read_model.ordered_entry_ids,
                read_model.ordered_read_model_ids,
                read_model.ordered_read_model_hashes,
                read_model.ordered_source_ledger_hashes,
                read_model.ordered_decision_ids,
            )
        ),
        "ordered_identities_unique": all(
            len(set(values)) == len(values)
            for values in (
                read_model.ordered_entry_ids,
                read_model.ordered_read_model_ids,
                read_model.ordered_read_model_hashes,
                read_model.ordered_source_ledger_hashes,
                read_model.ordered_decision_ids,
            )
        ),
        "partition_disjoint": (
            not set(read_model.admitted_entry_ids).intersection(
                read_model.rejected_entry_ids
            )
        ),
        "partition_complete": (
            set(read_model.admitted_entry_ids).union(
                read_model.rejected_entry_ids
            )
            == set(read_model.ordered_entry_ids)
        ),
        "lineage_bound": (
            read_model.source_ledger_hash
            in read_model.lineage.parent_hashes
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": all(
            isinstance(index, MappingProxyType)
            for index in (
                read_model._entry_position_by_id,
                read_model._read_model_position_by_id,
                read_model._read_model_position_by_hash,
                read_model._source_ledger_position_by_hash,
                read_model._decision_position_by_id,
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
            "read_model_id": read_model.read_model_id,
            "read_model_hash": read_model.read_model_hash,
            "source_ledger_hash": read_model.source_ledger_hash,
            "total_entry_count": read_model.total_entry_count,
            "admitted_entry_count": (
                read_model.admitted_entry_count
            ),
            "rejected_entry_count": (
                read_model.rejected_entry_count
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_060_foundation() -> Mapping[str, Any]:
    manifest = build_umd_060_certification_manifest()
    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-060"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 60)
            )
        ),
        "read_only_projection": (
            manifest.read_model_mode
            == "deterministic_read_only_projection"
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


def verify_umd_060_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model() -> bool:
    result = certify_umd_060_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-060 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
