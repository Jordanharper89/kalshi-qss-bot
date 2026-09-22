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
from .certified_canonical_market_registry_snapshot_activation_gate import (
    CertifiedSnapshotActivationDecision,
)

UMD_021_BUILD_ID = "UMD-021"
UMD_021_BUILD_NAME = (
    "Certified Canonical Market Registry Snapshot Activation Ledger"
)
UMD_021_REVISION = (
    "UMD_021_CERTIFIED_CANONICAL_MARKET_REGISTRY_"
    "SNAPSHOT_ACTIVATION_LEDGER_V1"
)
UMD_021_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_activation_commit",
    "activation_persistence",
    "ledger_mutation",
    "record_deletion",
    "record_reordering",
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
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedSnapshotActivationLedgerEntry:
    sequence_number: int
    previous_entry_hash: str | None
    decision: CertifiedSnapshotActivationDecision
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
            raise ValueError("ledger-entry lineage must belong to UMD")
        if self.lineage.build_id != UMD_021_BUILD_ID:
            raise ValueError(
                "ledger-entry lineage must use build_id UMD-021"
            )
        if self.decision.record_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "ledger-entry lineage must include decision record hash"
            )
        if (
            self.previous_entry_hash is not None
            and self.previous_entry_hash
            not in self.lineage.parent_hashes
        ):
            raise ValueError(
                "ledger-entry lineage must include previous entry hash"
            )

    @property
    def entry_id(self) -> str:
        return "umd:snapshot-activation-ledger-entry:" + deterministic_sha256(
            {
                "sequence_number": self.sequence_number,
                "previous_entry_hash": self.previous_entry_hash,
                "decision_id": self.decision.decision_id,
                "decision_record_hash": self.decision.record_hash,
            }
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
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class ReadOnlySnapshotActivationLedger:
    entries: Tuple[CertifiedSnapshotActivationLedgerEntry, ...]
    ledger_lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedSnapshotActivationLedgerEntry,
    ] = field(init=False, repr=False)
    _by_activation_id: Mapping[
        str,
        CertifiedSnapshotActivationLedgerEntry,
    ] = field(init=False, repr=False)
    _by_decision_id: Mapping[
        str,
        CertifiedSnapshotActivationLedgerEntry,
    ] = field(init=False, repr=False)
    _by_snapshot_id: Mapping[
        str,
        CertifiedSnapshotActivationLedgerEntry,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.entries,
                key=lambda entry: entry.sequence_number,
            )
        )
        object.__setattr__(self, "entries", ordered)

        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("ledger lineage must belong to UMD")
        if self.ledger_lineage.build_id != UMD_021_BUILD_ID:
            raise ValueError("ledger lineage must use build_id UMD-021")

        by_entry_id = {}
        by_activation_id = {}
        by_decision_id = {}
        by_snapshot_id = {}
        previous_entry = None
        latest_admitted_snapshot_sequence = 0

        for expected_sequence, entry in enumerate(
            ordered,
            start=1,
        ):
            if entry.sequence_number != expected_sequence:
                raise ValueError(
                    "ledger sequence must be contiguous and start at 1"
                )

            if previous_entry is None:
                if entry.previous_entry_hash is not None:
                    raise ValueError(
                        "first ledger entry must not have previous hash"
                    )
            else:
                if (
                    entry.previous_entry_hash
                    != previous_entry.entry_hash
                ):
                    raise ValueError(
                        "ledger previous-entry hash chain mismatch"
                    )

            decision = entry.decision

            if entry.entry_id in by_entry_id:
                raise ValueError("duplicate ledger entry ID")
            if decision.activation_id in by_activation_id:
                raise ValueError(
                    "activation may appear only once in activation ledger"
                )
            if decision.decision_id in by_decision_id:
                raise ValueError(
                    "decision may appear only once in activation ledger"
                )
            if (
                decision.admitted
                and decision.snapshot_id in by_snapshot_id
            ):
                raise ValueError(
                    "admitted snapshot may be activated only once"
                )

            if decision.admitted:
                snapshot_sequence = entry.sequence_number
                if snapshot_sequence <= latest_admitted_snapshot_sequence:
                    raise ValueError(
                        "admitted activation order must advance"
                    )
                latest_admitted_snapshot_sequence = snapshot_sequence
                by_snapshot_id[decision.snapshot_id] = entry

            by_entry_id[entry.entry_id] = entry
            by_activation_id[decision.activation_id] = entry
            by_decision_id[decision.decision_id] = entry
            previous_entry = entry

        object.__setattr__(
            self,
            "_by_entry_id",
            MappingProxyType(by_entry_id),
        )
        object.__setattr__(
            self,
            "_by_activation_id",
            MappingProxyType(by_activation_id),
        )
        object.__setattr__(
            self,
            "_by_decision_id",
            MappingProxyType(by_decision_id),
        )
        object.__setattr__(
            self,
            "_by_snapshot_id",
            MappingProxyType(by_snapshot_id),
        )

    def get(
        self,
        entry_id: str,
    ) -> CertifiedSnapshotActivationLedgerEntry | None:
        return self._by_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_by_activation(
        self,
        activation_id: str,
    ) -> CertifiedSnapshotActivationLedgerEntry | None:
        return self._by_activation_id.get(
            _text(activation_id, "activation_id")
        )

    def get_by_decision(
        self,
        decision_id: str,
    ) -> CertifiedSnapshotActivationLedgerEntry | None:
        return self._by_decision_id.get(
            _text(decision_id, "decision_id")
        )

    def get_by_snapshot(
        self,
        snapshot_id: str,
    ) -> CertifiedSnapshotActivationLedgerEntry | None:
        return self._by_snapshot_id.get(
            _text(snapshot_id, "snapshot_id")
        )

    def admitted_entries(
        self,
    ) -> Tuple[CertifiedSnapshotActivationLedgerEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.decision.admitted
        )

    def rejected_entries(
        self,
    ) -> Tuple[CertifiedSnapshotActivationLedgerEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if not entry.decision.admitted
        )

    def latest_admitted(
        self,
    ) -> CertifiedSnapshotActivationLedgerEntry | None:
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
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD021CertificationManifest:
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
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_021_certification_manifest() -> UMD021CertificationManifest:
    return UMD021CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_021_BUILD_ID,
        build_name=UMD_021_BUILD_NAME,
        revision=UMD_021_REVISION,
        schema_version=UMD_021_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 21)
        ),
        ledger_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_snapshot_activation_ledger(
    ledger: ReadOnlySnapshotActivationLedger,
) -> Mapping[str, Any]:
    checks = {
        "entry_ids_unique": len(
            {entry.entry_id for entry in ledger.entries}
        )
        == len(ledger.entries),
        "activation_ids_unique": len(
            {
                entry.decision.activation_id
                for entry in ledger.entries
            }
        )
        == len(ledger.entries),
        "decision_ids_unique": len(
            {
                entry.decision.decision_id
                for entry in ledger.entries
            }
        )
        == len(ledger.entries),
        "admitted_snapshot_ids_unique": len(
            {
                entry.decision.snapshot_id
                for entry in ledger.admitted_entries()
            }
        )
        == len(ledger.admitted_entries()),
        "sequence_contiguous": tuple(
            entry.sequence_number
            for entry in ledger.entries
        )
        == tuple(range(1, len(ledger.entries) + 1)),
        "deterministic_replay": (
            ledger.ledger_hash
            == deterministic_sha256(ledger.to_canonical_dict())
        ),
        "read_only_indexes": isinstance(
            ledger._by_entry_id,
            MappingProxyType,
        )
        and isinstance(
            ledger._by_activation_id,
            MappingProxyType,
        )
        and isinstance(
            ledger._by_decision_id,
            MappingProxyType,
        )
        and isinstance(
            ledger._by_snapshot_id,
            MappingProxyType,
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    latest = ledger.latest_admitted()

    return MappingProxyType(
        {
            "certified": not failed,
            "ledger_hash": ledger.ledger_hash,
            "entry_count": len(ledger.entries),
            "admitted_count": len(ledger.admitted_entries()),
            "rejected_count": len(ledger.rejected_entries()),
            "latest_admitted_snapshot_id": (
                None
                if latest is None
                else latest.decision.snapshot_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_021_foundation() -> Mapping[str, Any]:
    manifest = build_umd_021_certification_manifest()

    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-021",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}"
            for number in range(1, 21)
        ),
        "append_only_read_only": (
            manifest.ledger_mode
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


def verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger() -> bool:
    result = certify_umd_021_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-021 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_021_BUILD_ID",
    "UMD_021_BUILD_NAME",
    "UMD_021_REVISION",
    "UMD_021_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedSnapshotActivationLedgerEntry",
    "ReadOnlySnapshotActivationLedger",
    "UMD021CertificationManifest",
    "build_umd_021_certification_manifest",
    "certify_snapshot_activation_ledger",
    "certify_umd_021_foundation",
    "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger",
]
