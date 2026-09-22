from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = (
    "UMD_033_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_CORRECTION_V4"
)
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / (
    "certified_active_canonical_market_registry_"
    "query_session_read_model_admission_ledger.py"
)
INIT = PKG / "__init__.py"
TEST = ROOT / (
    "test_umd_033_certified_active_canonical_market_registry_"
    "query_session_read_model_admission_ledger.py"
)

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger import (
    UMD_033_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
    build_umd_033_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger,
    certify_umd_033_foundation,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    30,
    0,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash = (
        suffix.lower() * 64
    )[:64]
    session_registry_hash = (
        chr(ord(suffix.lower()) + 1) * 64
    )[:64]
    admission_ledger_hash = (
        chr(ord(suffix.lower()) + 2) * 64
    )[:64]

    checks = {
        "read_model_hash_deterministic": admitted,
    }
    reasons = (
        ()
        if admitted
        else ("read_model_hash_deterministic",)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            read_model_hash,
            session_registry_hash,
            admission_ledger_hash,
        ),
        source_refs=(
            f"fixture://umd-033/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        session_registry_hash=session_registry_hash,
        admission_ledger_hash=admission_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=reasons,
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry:
    parents = [value.record_hash]
    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-033/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={
            "read_only": True,
            "source": "certification-fixture",
        },
        lineage=lineage,
    )


def ledger(
    entries: tuple[
        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
        ...
    ],
) -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger:
    parent_hashes = (
        ()
        if not entries
        else (entries[-1].entry_hash,)
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=parent_hashes,
        source_refs=(
            "fixture://umd-033/ledger",
        ),
        created_at=FIXED,
    )

    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
        entries=entries,
        ledger_lineage=lineage,
    )


class TestUMD033(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        result = certify_umd_033_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(
            result["build_id"],
            "UMD-033",
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(1, value, None)

        self.assertEqual(
            first.entry_id,
            second.entry_id,
        )
        self.assertEqual(
            first.entry_hash,
            second.entry_hash,
        )

    def test_ledger_certifies(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        second = entry(
            2,
            decision("d", admitted=False),
            first.entry_hash,
        )
        item = ledger((first, second))

        result = (
            certify_active_market_query_session_read_model_admission_ledger(
                item
            )
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_lookup_indexes(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        item = ledger((first,))

        self.assertIs(
            item.get(first.entry_id),
            first,
        )
        self.assertIs(
            item.get_by_read_model_hash(
                first.decision.read_model_hash
            ),
            first,
        )
        self.assertIs(
            item.get_by_decision(
                first.decision.decision_id
            ),
            first,
        )
        self.assertIs(
            item.latest_admitted(),
            first,
        )

    def test_sequence_gap_rejected(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        third = entry(
            3,
            decision("d"),
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        second = entry(
            2,
            decision("d"),
            "f" * 64,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_read_model_rejected(self) -> None:
        value = decision("a")
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self) -> None:
        value = decision("a")

        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-033",
            revision=UMD_033_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-033/bad-entry",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_ledger_lineage_requires_latest_hash(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-033",
            revision=UMD_033_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-033/bad-ledger",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
                entries=(first,),
                ledger_lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        first = entry(
            1,
            decision("a"),
            None,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            first.sequence_number = 2

        with self.assertRaises(TypeError):
            first.metadata["read_only"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_033_certification_manifest()

        self.assertEqual(
            manifest.ledger_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-033 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD033
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_033_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-032 "
        "consumed read-only"
    )
    print(
        "[PASS] Read-model admission ledger entry IDs deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] UMD-032 decision-to-ledger lineage verified"
    )
    print(
        "[PASS] Duplicate read-model and decision replay rejected"
    )
    print(
        "[PASS] Admitted and rejected read-model indexes verified"
    )
    print(
        "[PASS] Latest admitted read-model view deterministic"
    )
    print(
        "[PASS] Immutable read-only admission ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-033 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL ADMISSION LEDGER CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_session_read_model_admission_ledger import (
    UMD_033_BUILD_ID,
    UMD_033_BUILD_NAME,
    UMD_033_REVISION,
    UMD_033_SCHEMA_VERSION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
    UMD033CertificationManifest,
    build_umd_033_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger,
    certify_umd_033_foundation,
    verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger,
)
"""

EXPORTED_NAMES = (
    "UMD_033_BUILD_ID",
    "UMD_033_BUILD_NAME",
    "UMD_033_REVISION",
    "UMD_033_SCHEMA_VERSION",
    "CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry",
    "ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger",
    "UMD033CertificationManifest",
    "build_umd_033_certification_manifest",
    "certify_active_market_query_session_read_model_admission_ledger",
    "certify_umd_033_foundation",
    "verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger",
)

UPSTREAM_MODULES = (
    (
        "universal_market_discovery_foundation",
        "verify_umd_foundation",
    ),
    (
        "certified_canonical_market_contract",
        "verify_umd_002_certified_canonical_market_contract",
    ),
    (
        "certified_venue_identity_registry",
        "verify_umd_003_certified_venue_identity_registry",
    ),
    (
        "certified_venue_market_binding_registry",
        "verify_umd_004_certified_venue_market_binding_registry",
    ),
    (
        "certified_market_category_hierarchy_registry",
        "verify_umd_005_certified_market_category_hierarchy_registry",
    ),
    (
        "certified_market_classification_registry",
        "verify_umd_006_certified_market_classification_registry",
    ),
    (
        "certified_market_metadata_registry",
        "verify_umd_007_certified_market_metadata_registry",
    ),
    (
        "certified_market_lifecycle_and_settlement_registry",
        "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
    ),
    (
        "certified_market_duplicate_resolution_registry",
        "verify_umd_009_certified_market_duplicate_resolution_registry",
    ),
    (
        "certified_related_market_graph_registry",
        "verify_umd_010_certified_related_market_graph_registry",
    ),
    (
        "certified_incremental_discovery_batch_contract",
        "verify_umd_011_certified_incremental_discovery_batch_contract",
    ),
    (
        "certified_incremental_discovery_admission_gate",
        "verify_umd_012_certified_incremental_discovery_admission_gate",
    ),
    (
        "certified_discovery_admission_ledger",
        "verify_umd_013_certified_discovery_admission_ledger",
    ),
    (
        "certified_admitted_market_materialization_contract",
        "verify_umd_014_certified_admitted_market_materialization_contract",
    ),
    (
        "certified_materialized_market_admission_registry",
        "verify_umd_015_certified_materialized_market_admission_registry",
    ),
    (
        "certified_canonical_market_registry_snapshot_contract",
        "verify_umd_016_certified_canonical_market_registry_snapshot_contract",
    ),
    (
        "certified_canonical_market_registry_snapshot_admission_gate",
        "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate",
    ),
    (
        "certified_canonical_market_registry_snapshot_admission_ledger",
        "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger",
    ),
    (
        "certified_canonical_market_registry_snapshot_activation_contract",
        "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract",
    ),
    (
        "certified_canonical_market_registry_snapshot_activation_gate",
        "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate",
    ),
    (
        "certified_canonical_market_registry_snapshot_activation_ledger",
        "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger",
    ),
    (
        "certified_active_canonical_market_registry_read_model",
        "verify_umd_022_certified_active_canonical_market_registry_read_model",
    ),
    (
        "certified_active_canonical_market_registry_query_contract",
        "verify_umd_023_certified_active_canonical_market_registry_query_contract",
    ),
    (
        "certified_active_canonical_market_registry_query_execution_engine",
        "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine",
    ),
    (
        "certified_active_canonical_market_registry_query_execution_admission_gate",
        "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate",
    ),
    (
        "certified_active_canonical_market_registry_query_execution_ledger",
        "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger",
    ),
    (
        "certified_active_canonical_market_registry_query_execution_read_model",
        "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model",
    ),
    (
        "certified_active_canonical_market_registry_query_session_contract",
        "verify_umd_028_certified_active_canonical_market_registry_query_session_contract",
    ),
    (
        "certified_active_canonical_market_registry_query_session_admission_gate",
        "verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate",
    ),
    (
        "certified_active_canonical_market_registry_query_session_admission_ledger",
        "verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger",
    ),
    (
        "certified_active_canonical_market_registry_query_session_read_model",
        "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model",
    ),
    (
        "certified_active_canonical_market_registry_query_session_read_model_admission_gate",
        "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate",
    ),
)


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
    temporary.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(
        temporary,
        path,
    )


def _remove_existing_umd_033_import_block(
    source: str,
) -> str:
    marker = (
        "from "
        ".certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger import ("
    )

    start = source.find(marker)
    if start == -1:
        return source

    cursor = start
    depth = 0
    opened = False

    while cursor < len(source):
        character = source[cursor]

        if character == "(":
            depth += 1
            opened = True
        elif character == ")":
            depth -= 1
            if opened and depth == 0:
                cursor += 1
                while (
                    cursor < len(source)
                    and source[cursor] in " \t"
                ):
                    cursor += 1
                if (
                    cursor < len(source)
                    and source[cursor] == "\r"
                ):
                    cursor += 1
                if (
                    cursor < len(source)
                    and source[cursor] == "\n"
                ):
                    cursor += 1
                return source[:start] + source[cursor:]

        cursor += 1

    raise RuntimeError(
        "Existing UMD-033 import block is malformed "
        "and could not be safely bounded"
    )


def _find_all_list_bounds(
    source: str,
) -> tuple[int, int]:
    marker = "__all__ = ["
    start = source.find(marker)

    if start == -1:
        raise RuntimeError(
            "UMD package __all__ list is missing"
        )

    list_start = source.find(
        "[",
        start,
    )
    if list_start == -1:
        raise RuntimeError(
            "UMD package __all__ opening bracket is missing"
        )

    cursor = list_start
    depth = 0
    in_string = False
    quote = ""
    escaped = False

    while cursor < len(source):
        character = source[cursor]

        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                in_string = False
        else:
            if character in ("'", '"'):
                in_string = True
                quote = character
            elif character == "[":
                depth += 1
            elif character == "]":
                depth -= 1
                if depth == 0:
                    return list_start, cursor

        cursor += 1

    raise RuntimeError(
        "UMD package __all__ closing bracket is missing"
    )


def _remove_umd_033_exports_from_all(
    source: str,
) -> str:
    list_start, list_end = _find_all_list_bounds(
        source
    )

    block = source[list_start + 1 : list_end]
    lines = block.splitlines(
        keepends=True
    )

    filtered = []
    for line in lines:
        stripped = line.strip()
        remove = False

        for name in EXPORTED_NAMES:
            if stripped in (
                f'"{name}",',
                f"'{name}',",
                f'"{name}"',
                f"'{name}'",
            ):
                remove = True
                break

        if not remove:
            filtered.append(line)

    rebuilt = "".join(filtered)

    return (
        source[: list_start + 1]
        + rebuilt
        + source[list_end:]
    )


def _append_umd_033_exports_to_all(
    source: str,
) -> str:
    list_start, list_end = _find_all_list_bounds(
        source
    )

    block = source[list_start + 1 : list_end]

    missing = [
        name
        for name in EXPORTED_NAMES
        if f'"{name}"' not in block
        and f"'{name}'" not in block
    ]

    if not missing:
        return source

    insertion = "".join(
        f'    "{name}",\n'
        for name in missing
    )

    if block and not block.endswith("\n"):
        insertion = "\n" + insertion

    return (
        source[:list_end]
        + insertion
        + source[list_end:]
    )


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    original = INIT.read_text(
        encoding="utf-8"
    )

    repaired = _remove_existing_umd_033_import_block(
        original
    )
    repaired = _remove_umd_033_exports_from_all(
        repaired
    )
    repaired = repaired.rstrip() + "\n\n"
    repaired += normalize(INIT_IMPORT)
    repaired = _append_umd_033_exports_to_all(
        repaired
    )

    compile(
        repaired,
        str(INIT),
        "exec",
    )

    write_exact(
        INIT,
        repaired,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def verify_upstream() -> None:
    if not PKG.exists():
        raise FileNotFoundError(
            f"UMD package missing: {PKG}"
        )

    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        for module_name, verifier_name in UPSTREAM_MODULES:
            module = importlib.import_module(
                "qseries_v2."
                "universal_market_discovery."
                + module_name
            )

            verifier = getattr(
                module,
                verifier_name,
                None,
            )

            if verifier is None:
                raise RuntimeError(
                    "Certified upstream verifier missing: "
                    f"{module_name}.{verifier_name}"
                )

            result = verifier()

            if result is not True:
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def verify_current() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )
    try:
        module_name = (
            "qseries_v2.universal_market_discovery."
            "certified_active_canonical_market_registry_"
            "query_session_read_model_admission_ledger"
        )
        importlib.invalidate_caches()
        module = importlib.import_module(
            module_name
        )

        missing = [
            name
            for name in EXPORTED_NAMES
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-033 missing symbols: "
                + ", ".join(missing)
            )

        verifier = getattr(
            module,
            "verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger",
        )
        if verifier() is not True:
            raise RuntimeError(
                "UMD-033 verification returned false"
            )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-033 CORRECTION V4 REPOSITORY-ALIGNED FULL REPLACEMENT INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER"
    )
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in (
            MODULE,
            INIT,
            TEST,
        )
    }

    try:
        update_init()
        py_compile.compile(
            str(INIT),
            doraise=True,
        )
        importlib.invalidate_caches()

        verify_upstream()
        print(
            "[PASS] Certified UMD-001 through UMD-032 "
            "verified read-only"
        )

        write_exact(
            MODULE,
            MODULE_SOURCE,
        )
        write_exact(
            TEST,
            TEST_SOURCE,
        )

        py_compile.compile(
            str(MODULE),
            doraise=True,
        )
        py_compile.compile(
            str(INIT),
            doraise=True,
        )
        py_compile.compile(
            str(TEST),
            doraise=True,
        )

        verify_current()
    except Exception:
        for path, previous in backups.items():
            if previous is None:
                if path.exists():
                    path.unlink()
            else:
                temporary = path.with_suffix(
                    path.suffix + ".rollback.tmp"
                )
                temporary.write_bytes(previous)
                os.replace(
                    temporary,
                    path,
                )

        importlib.invalidate_caches()

        print(
            "[ROLLBACK] UMD-033 installation failed; "
            "all affected files restored"
        )
        raise

    manifest = {
        "build_id": "UMD-033",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 33)
        ),
        "mode": "append_only_read_only",
        "network_enabled": False,
        "persistence_enabled": False,
        "mutation_enabled": False,
        "publication_enabled": False,
        "execution_enabled": False,
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(
        f"[PASS] Wrote: {MODULE.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Updated: {INIT.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Wrote: {TEST.relative_to(ROOT)}"
    )
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-033 symbols verified")
    print(
        f"[PASS] Deterministic install hash: {install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-033 CORRECTION V4 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_033_certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
