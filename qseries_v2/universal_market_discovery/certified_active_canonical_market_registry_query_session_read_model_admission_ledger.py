from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
)

UMD_033_BUILD_ID = "UMD-033"
UMD_033_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Session Read Model Admission Ledger"
)
UMD_033_REVISION = (
    "UMD_033_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_CORRECTION_V4"
)
UMD_033_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_read_model_commit",
    "read_model_persistence",
    "ledger_mutation",
    "record_deletion",
    "record_reordering",
    "session_registry_mutation",
    "session_admission_ledger_mutation",
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


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


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
class CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry:
    sequence_number: int
    previous_entry_hash: str | None
    decision: CertifiedActiveMarketQuerySessionReadModelAdmissionDecision
    recorded_at: datetime
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        if not isinstance(self.sequence_number, int):
            raise TypeError("sequence_number must be an integer")
        if self.sequence_number < 1:
            raise ValueError("sequence_number must be positive")

        if self.previous_entry_hash is None:
            if self.sequence_number != 1:
                raise ValueError(
                    "only the first ledger entry may omit previous_entry_hash"
                )
        else:
            object.__setattr__(
                self,
                "previous_entry_hash",
                _sha256(
                    self.previous_entry_hash,
                    "previous_entry_hash",
                ),
            )

        if not isinstance(
            self.decision,
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
        ):
            raise TypeError(
                "decision must be a certified UMD-032 read-model "
                "admission decision"
            )

        object.__setattr__(
            self,
            "recorded_at",
            _utc(self.recorded_at, "recorded_at"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "ledger-entry lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_033_BUILD_ID:
            raise ValueError(
                "ledger-entry lineage must use build_id UMD-033"
            )
        if self.decision.record_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "ledger-entry lineage must include decision record hash"
            )
        if (
            self.previous_entry_hash is not None
            and self.previous_entry_hash not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "ledger-entry lineage must include previous entry hash"
            )

    @property
    def entry_id(self) -> str:
        return (
            "umd:query-session-read-model-admission-ledger-entry:"
            + deterministic_sha256(
                {
                    "sequence_number": self.sequence_number,
                    "previous_entry_hash": self.previous_entry_hash,
                    "decision_id": self.decision.decision_id,
                    "decision_record_hash": self.decision.record_hash,
                }
            )
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "entry_id": self.entry_id,
            "sequence_number": self.sequence_number,
            "previous_entry_hash": self.previous_entry_hash,
            "decision": self.decision,
            "recorded_at": self.recorded_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def entry_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger:
    entries: Tuple[
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
        ...
    ]
    ledger_lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_read_model_hash: Mapping[
        str,
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_decision_id: Mapping[
        str,
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            object.__setattr__(
                self,
                "entries",
                tuple(self.entries),
            )

        ordered = tuple(
            sorted(
                self.entries,
                key=lambda entry: entry.sequence_number,
            )
        )
        object.__setattr__(
            self,
            "entries",
            ordered,
        )

        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "ledger lineage must belong to UMD"
            )
        if self.ledger_lineage.build_id != UMD_033_BUILD_ID:
            raise ValueError(
                "ledger lineage must use build_id UMD-033"
            )

        by_entry_id = {}
        by_read_model_hash = {}
        by_decision_id = {}
        previous_entry = None

        for expected_sequence, entry in enumerate(
            ordered,
            start=1,
        ):
            if not isinstance(
                entry,
                CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
            ):
                raise TypeError(
                    "entries must contain certified UMD-033 ledger entries"
                )

            if entry.sequence_number != expected_sequence:
                raise ValueError(
                    "ledger sequence must be contiguous and start at 1"
                )

            if previous_entry is None:
                if entry.previous_entry_hash is not None:
                    raise ValueError(
                        "first ledger entry must not have previous hash"
                    )
            elif (
                entry.previous_entry_hash
                != previous_entry.entry_hash
            ):
                raise ValueError(
                    "ledger previous-entry hash chain mismatch"
                )

            decision = entry.decision

            if entry.entry_id in by_entry_id:
                raise ValueError(
                    "duplicate ledger entry ID"
                )
            if decision.read_model_hash in by_read_model_hash:
                raise ValueError(
                    "read model may appear only once in admission ledger"
                )
            if decision.decision_id in by_decision_id:
                raise ValueError(
                    "admission decision may appear only once in ledger"
                )

            by_entry_id[entry.entry_id] = entry
            by_read_model_hash[
                decision.read_model_hash
            ] = entry
            by_decision_id[
                decision.decision_id
            ] = entry
            previous_entry = entry

        if ordered:
            if ordered[-1].entry_hash not in (
                self.ledger_lineage.parent_hashes
            ):
                raise ValueError(
                    "ledger lineage must include latest entry hash"
                )

        object.__setattr__(
            self,
            "_by_entry_id",
            MappingProxyType(by_entry_id),
        )
        object.__setattr__(
            self,
            "_by_read_model_hash",
            MappingProxyType(by_read_model_hash),
        )
        object.__setattr__(
            self,
            "_by_decision_id",
            MappingProxyType(by_decision_id),
        )

    def get(
        self,
        entry_id: str,
    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry | None:
        return self._by_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_by_read_model_hash(
        self,
        read_model_hash: str,
    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry | None:
        return self._by_read_model_hash.get(
            _sha256(
                read_model_hash,
                "read_model_hash",
            )
        )

    def get_by_decision(
        self,
        decision_id: str,
    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry | None:
        return self._by_decision_id.get(
            _text(decision_id, "decision_id")
        )

    def admitted_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
        ...
    ]:
        return tuple(
            entry
            for entry in self.entries
            if entry.decision.admitted
        )

    def rejected_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
        ...
    ]:
        return tuple(
            entry
            for entry in self.entries
            if not entry.decision.admitted
        )

    def latest_admitted(
        self,
    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry | None:
        admitted = self.admitted_entries()
        if not admitted:
            return None
        return admitted[-1]

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "ledger_mode": "append_only_read_only",
            "entries": self.entries,
            "ledger_lineage": self.ledger_lineage,
        }

    @property
    def ledger_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD033CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    ledger_mode: str
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
            "ledger_mode": self.ledger_mode,
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


def build_umd_033_certification_manifest() -> UMD033CertificationManifest:
    return UMD033CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_033_BUILD_ID,
        build_name=UMD_033_BUILD_NAME,
        revision=UMD_033_REVISION,
        schema_version=UMD_033_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 33)
        ),
        ledger_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_session_read_model_admission_ledger(
    ledger: ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
) -> Mapping[str, Any]:
    entries = ledger.entries
    admitted = ledger.admitted_entries()
    rejected = ledger.rejected_entries()

    checks = {
        "sequence_contiguous": (
            tuple(
                entry.sequence_number
                for entry in entries
            )
            == tuple(
                range(1, len(entries) + 1)
            )
        ),
        "previous_hash_chain_valid": all(
            entry.previous_entry_hash
            == entries[index - 1].entry_hash
            for index, entry in enumerate(entries)
            if index > 0
        ),
        "entry_ids_unique": (
            len(
                {
                    entry.entry_id
                    for entry in entries
                }
            )
            == len(entries)
        ),
        "read_model_hashes_unique": (
            len(
                {
                    entry.decision.read_model_hash
                    for entry in entries
                }
            )
            == len(entries)
        ),
        "decision_ids_unique": (
            len(
                {
                    entry.decision.decision_id
                    for entry in entries
                }
            )
            == len(entries)
        ),
        "admission_partition_complete": (
            len(admitted) + len(rejected)
            == len(entries)
        ),
        "latest_entry_lineage_bound": (
            not entries
            or entries[-1].entry_hash
            in ledger.ledger_lineage.parent_hashes
        ),
        "deterministic_replay": (
            ledger.ledger_hash
            == deterministic_sha256(
                ledger.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                ledger._by_entry_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_read_model_hash,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_decision_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = ledger.latest_admitted()

    return MappingProxyType(
        {
            "certified": not failed,
            "ledger_hash": ledger.ledger_hash,
            "entry_count": len(entries),
            "admitted_count": len(admitted),
            "rejected_count": len(rejected),
            "latest_admitted_read_model_hash": (
                None
                if latest is None
                else latest.decision.read_model_hash
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_033_foundation() -> Mapping[str, Any]:
    manifest = build_umd_033_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-033"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 33)
            )
        ),
        "append_only_read_only": (
            manifest.ledger_mode
            == "append_only_read_only"
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


def verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger() -> bool:
    certification = certify_umd_033_foundation()
    if not certification["certified"]:
        raise RuntimeError(
            "UMD-033 foundation certification failed: "
            + ", ".join(certification["failed_checks"])
        )
    return True
