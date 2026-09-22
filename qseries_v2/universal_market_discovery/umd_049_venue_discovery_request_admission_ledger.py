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
from .umd_048_venue_discovery_request_admission_gate import (
    CertifiedVenueDiscoveryRequestAdmissionDecision,
)

UMD_049_BUILD_ID = "UMD-049"
UMD_049_BUILD_NAME = (
    "Certified Venue Discovery Request Admission Ledger"
)
UMD_049_REVISION = (
    "UMD_049_CERTIFIED_VENUE_DISCOVERY_REQUEST_ADMISSION_LEDGER_V1"
)
UMD_049_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_invocation",
    "authentication_execution",
    "credential_storage",
    "automatic_discovery",
    "automatic_admission",
    "automatic_append",
    "ledger_mutation",
    "record_deletion",
    "record_reordering",
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
class CertifiedVenueDiscoveryRequestAdmissionLedgerEntry:
    sequence_number: int
    previous_entry_hash: str | None
    decision: CertifiedVenueDiscoveryRequestAdmissionDecision
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
                    "only the first entry may omit previous_entry_hash"
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
            CertifiedVenueDiscoveryRequestAdmissionDecision,
        ):
            raise TypeError(
                "decision must be a certified UMD-048 admission decision"
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
            raise ValueError("entry lineage must belong to UMD")
        if self.lineage.build_id != UMD_049_BUILD_ID:
            raise ValueError(
                "entry lineage must use build_id UMD-049"
            )
        if self.decision.record_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "entry lineage must include UMD-048 decision record hash"
            )
        if (
            self.previous_entry_hash is not None
            and self.previous_entry_hash not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "entry lineage must include previous_entry_hash"
            )

    @property
    def entry_id(self) -> str:
        return (
            "umd:venue-discovery-request-admission-ledger-entry:"
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
class ReadOnlyVenueDiscoveryRequestAdmissionLedger:
    entries: Tuple[
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
        ...,
    ]
    ledger_lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_request_id: Mapping[
        str,
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_request_hash: Mapping[
        str,
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_decision_id: Mapping[
        str,
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _entry_ids_by_source_id: Mapping[
        str,
        Tuple[str, ...],
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
        object.__setattr__(self, "entries", ordered)

        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("ledger lineage must belong to UMD")
        if self.ledger_lineage.build_id != UMD_049_BUILD_ID:
            raise ValueError(
                "ledger lineage must use build_id UMD-049"
            )

        by_entry_id = {}
        by_request_id = {}
        by_request_hash = {}
        by_decision_id = {}
        entry_ids_by_source_id = {}
        previous = None

        for expected_sequence, entry in enumerate(
            ordered,
            start=1,
        ):
            if not isinstance(
                entry,
                CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
            ):
                raise TypeError(
                    "entries must contain certified UMD-049 entries"
                )
            if entry.sequence_number != expected_sequence:
                raise ValueError(
                    "sequence must be contiguous and begin at 1"
                )

            if previous is None:
                if entry.previous_entry_hash is not None:
                    raise ValueError(
                        "first entry must not have previous_entry_hash"
                    )
            elif entry.previous_entry_hash != previous.entry_hash:
                raise ValueError(
                    "previous-entry hash chain mismatch"
                )

            if entry.entry_id in by_entry_id:
                raise ValueError("duplicate ledger entry ID")
            if entry.decision.request_id in by_request_id:
                raise ValueError("duplicate request ID replay")
            if entry.decision.request_hash in by_request_hash:
                raise ValueError("duplicate request hash replay")
            if entry.decision.decision_id in by_decision_id:
                raise ValueError("duplicate decision replay")

            by_entry_id[entry.entry_id] = entry
            by_request_id[entry.decision.request_id] = entry
            by_request_hash[entry.decision.request_hash] = entry
            by_decision_id[entry.decision.decision_id] = entry
            entry_ids_by_source_id.setdefault(
                entry.decision.source_id,
                [],
            ).append(entry.entry_id)
            previous = entry

        if (
            ordered
            and ordered[-1].entry_hash
            not in self.ledger_lineage.parent_hashes
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
            "_by_request_id",
            MappingProxyType(by_request_id),
        )
        object.__setattr__(
            self,
            "_by_request_hash",
            MappingProxyType(by_request_hash),
        )
        object.__setattr__(
            self,
            "_by_decision_id",
            MappingProxyType(by_decision_id),
        )
        object.__setattr__(
            self,
            "_entry_ids_by_source_id",
            MappingProxyType(
                {
                    source_id: tuple(entry_ids)
                    for source_id, entry_ids
                    in entry_ids_by_source_id.items()
                }
            ),
        )

    def get(
        self,
        entry_id: str,
    ) -> CertifiedVenueDiscoveryRequestAdmissionLedgerEntry | None:
        return self._by_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_by_request_id(
        self,
        request_id: str,
    ) -> CertifiedVenueDiscoveryRequestAdmissionLedgerEntry | None:
        return self._by_request_id.get(
            _text(request_id, "request_id")
        )

    def get_by_request_hash(
        self,
        request_hash: str,
    ) -> CertifiedVenueDiscoveryRequestAdmissionLedgerEntry | None:
        return self._by_request_hash.get(
            _sha256(request_hash, "request_hash")
        )

    def get_by_decision_id(
        self,
        decision_id: str,
    ) -> CertifiedVenueDiscoveryRequestAdmissionLedgerEntry | None:
        return self._by_decision_id.get(
            _text(decision_id, "decision_id")
        )

    def list_by_source_id(
        self,
        source_id: str,
    ) -> Tuple[
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
        ...,
    ]:
        normalized_source_id = _text(
            source_id,
            "source_id",
        )
        entry_ids = self._entry_ids_by_source_id.get(
            normalized_source_id,
            (),
        )
        return tuple(
            self._by_entry_id[entry_id]
            for entry_id in entry_ids
        )

    def admitted_entries(
        self,
    ) -> Tuple[
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
        ...,
    ]:
        return tuple(
            entry
            for entry in self.entries
            if entry.decision.admitted
        )

    def rejected_entries(
        self,
    ) -> Tuple[
        CertifiedVenueDiscoveryRequestAdmissionLedgerEntry,
        ...,
    ]:
        return tuple(
            entry
            for entry in self.entries
            if not entry.decision.admitted
        )

    def latest_admitted(
        self,
    ) -> CertifiedVenueDiscoveryRequestAdmissionLedgerEntry | None:
        admitted = self.admitted_entries()
        return None if not admitted else admitted[-1]

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
class UMD049CertificationManifest:
    subsystem_id: str
    build_id: str
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
            "revision": self.revision,
            "schema_version": self.schema_version,
            "upstream_builds": self.upstream_builds,
            "ledger_mode": self.ledger_mode,
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


def build_umd_049_certification_manifest() -> UMD049CertificationManifest:
    return UMD049CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_049_BUILD_ID,
        revision=UMD_049_REVISION,
        schema_version=UMD_049_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 49)
        ),
        ledger_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_venue_discovery_request_admission_ledger(
    ledger: ReadOnlyVenueDiscoveryRequestAdmissionLedger,
) -> Mapping[str, Any]:
    if not isinstance(
        ledger,
        ReadOnlyVenueDiscoveryRequestAdmissionLedger,
    ):
        raise TypeError(
            "ledger must be a certified UMD-049 ledger"
        )

    admitted = ledger.admitted_entries()
    rejected = ledger.rejected_entries()
    checks = {
        "sequence_contiguous": (
            tuple(
                entry.sequence_number
                for entry in ledger.entries
            )
            == tuple(
                range(1, len(ledger.entries) + 1)
            )
        ),
        "previous_hash_chain_valid": all(
            entry.previous_entry_hash
            == ledger.entries[index - 1].entry_hash
            for index, entry in enumerate(ledger.entries)
            if index > 0
        ),
        "entry_ids_unique": (
            len(
                {
                    entry.entry_id
                    for entry in ledger.entries
                }
            )
            == len(ledger.entries)
        ),
        "request_ids_unique": (
            len(
                {
                    entry.decision.request_id
                    for entry in ledger.entries
                }
            )
            == len(ledger.entries)
        ),
        "request_hashes_unique": (
            len(
                {
                    entry.decision.request_hash
                    for entry in ledger.entries
                }
            )
            == len(ledger.entries)
        ),
        "decision_ids_unique": (
            len(
                {
                    entry.decision.decision_id
                    for entry in ledger.entries
                }
            )
            == len(ledger.entries)
        ),
        "partition_complete": (
            len(admitted)
            + len(rejected)
            == len(ledger.entries)
        ),
        "latest_lineage_bound": (
            not ledger.entries
            or ledger.entries[-1].entry_hash
            in ledger.ledger_lineage.parent_hashes
        ),
        "deterministic_replay": (
            ledger.ledger_hash
            == deterministic_sha256(
                ledger.to_canonical_dict()
            )
        ),
        "read_only_indexes": all(
            isinstance(index, MappingProxyType)
            for index in (
                ledger._by_entry_id,
                ledger._by_request_id,
                ledger._by_request_hash,
                ledger._by_decision_id,
                ledger._entry_ids_by_source_id,
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
            "ledger_hash": ledger.ledger_hash,
            "entry_count": len(ledger.entries),
            "admitted_count": len(admitted),
            "rejected_count": len(rejected),
            "source_count": len(
                ledger._entry_ids_by_source_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_049_foundation() -> Mapping[str, Any]:
    manifest = build_umd_049_certification_manifest()
    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-049"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 49)
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


def verify_umd_049_venue_discovery_request_admission_ledger() -> bool:
    result = certify_umd_049_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-049 foundation certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True
