from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_026_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_EXECUTION_LEDGER_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_execution_ledger.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_026_certified_active_canonical_market_registry_query_execution_ledger.py"

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
from .certified_active_canonical_market_registry_query_execution_admission_gate import (
    CertifiedActiveMarketQueryExecutionAdmissionDecision,
)

UMD_026_BUILD_ID = "UMD-026"
UMD_026_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Execution Ledger"
)
UMD_026_REVISION = (
    "UMD_026_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_EXECUTION_LEDGER_V1"
)
UMD_026_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_execution_commit",
    "execution_persistence",
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
class CertifiedActiveMarketQueryExecutionLedgerEntry:
    sequence_number: int
    previous_entry_hash: str | None
    decision: CertifiedActiveMarketQueryExecutionAdmissionDecision
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
        if self.lineage.build_id != UMD_026_BUILD_ID:
            raise ValueError(
                "ledger-entry lineage must use build_id UMD-026"
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
        return "umd:market-query-execution-ledger-entry:" + deterministic_sha256(
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
class ReadOnlyActiveMarketQueryExecutionAdmissionLedger:
    entries: Tuple[CertifiedActiveMarketQueryExecutionLedgerEntry, ...]
    ledger_lineage: ImmutableLineage
    _by_entry_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_decision_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_result_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
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
        if self.ledger_lineage.build_id != UMD_026_BUILD_ID:
            raise ValueError("ledger lineage must use build_id UMD-026")

        by_entry_id = {}
        by_execution_id = {}
        by_decision_id = {}
        by_result_id = {}
        previous_entry = None

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
            if decision.execution_id in by_execution_id:
                raise ValueError(
                    "execution may appear only once in execution ledger"
                )
            if decision.decision_id in by_decision_id:
                raise ValueError(
                    "admission decision may appear only once in execution ledger"
                )
            if decision.result_id in by_result_id:
                raise ValueError(
                    "query result may appear only once in execution ledger"
                )

            by_entry_id[entry.entry_id] = entry
            by_execution_id[decision.execution_id] = entry
            by_decision_id[decision.decision_id] = entry
            by_result_id[decision.result_id] = entry
            previous_entry = entry

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
            "_by_decision_id",
            MappingProxyType(by_decision_id),
        )
        object.__setattr__(
            self,
            "_by_result_id",
            MappingProxyType(by_result_id),
        )

    def get(
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

    def get_by_decision(
        self,
        decision_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_decision_id.get(
            _text(decision_id, "decision_id")
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
    ) -> Tuple[CertifiedActiveMarketQueryExecutionLedgerEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.decision.admitted
        )

    def rejected_entries(
        self,
    ) -> Tuple[CertifiedActiveMarketQueryExecutionLedgerEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if not entry.decision.admitted
        )

    def latest_admitted(
        self,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
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
class UMD026CertificationManifest:
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


def build_umd_026_certification_manifest() -> UMD026CertificationManifest:
    return UMD026CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_026_BUILD_ID,
        build_name=UMD_026_BUILD_NAME,
        revision=UMD_026_REVISION,
        schema_version=UMD_026_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 26)
        ),
        ledger_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_execution_admission_ledger(
    ledger: ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
) -> Mapping[str, Any]:
    checks = {
        "entry_ids_unique": len(
            {entry.entry_id for entry in ledger.entries}
        )
        == len(ledger.entries),
        "execution_ids_unique": len(
            {
                entry.decision.execution_id
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
        "result_ids_unique": len(
            {
                entry.decision.result_id
                for entry in ledger.entries
            }
        )
        == len(ledger.entries),
        "sequence_contiguous": tuple(
            entry.sequence_number for entry in ledger.entries
        )
        == tuple(range(1, len(ledger.entries) + 1)),
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
                ledger._by_execution_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_decision_id,
                MappingProxyType,
            )
            and isinstance(
                ledger._by_result_id,
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
            "entry_count": len(ledger.entries),
            "admitted_count": len(ledger.admitted_entries()),
            "rejected_count": len(ledger.rejected_entries()),
            "latest_admitted_execution_id": (
                None
                if latest is None
                else latest.decision.execution_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_026_foundation() -> Mapping[str, Any]:
    manifest = build_umd_026_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-026"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 26)
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


def verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger() -> bool:
    result = certify_umd_026_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-026 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_026_BUILD_ID",
    "UMD_026_BUILD_NAME",
    "UMD_026_REVISION",
    "UMD_026_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQueryExecutionLedgerEntry",
    "ReadOnlyActiveMarketQueryExecutionAdmissionLedger",
    "UMD026CertificationManifest",
    "build_umd_026_certification_manifest",
    "certify_active_market_query_execution_admission_ledger",
    "certify_umd_026_foundation",
    "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_admission_gate import (
    UMD_025_REVISION,
    CertifiedActiveMarketQueryExecutionAdmissionDecision,
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_execution_ledger import (
    UMD_026_REVISION,
    CertifiedActiveMarketQueryExecutionLedgerEntry,
    ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
    build_umd_026_certification_manifest,
    certify_active_market_query_execution_admission_ledger,
    certify_umd_026_foundation,
    verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger,
)

FIXED = datetime(
    2026,
    8,
    6,
    7,
    30,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool,
) -> CertifiedActiveMarketQueryExecutionAdmissionDecision:
    execution_hash = suffix * 64

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-025",
        revision=UMD_025_REVISION,
        schema_version="1.0.0",
        parent_hashes=(execution_hash,),
        source_refs=(
            f"fixture://umd-025/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    checks = {
        "execution_id_not_seen": admitted,
    }

    return CertifiedActiveMarketQueryExecutionAdmissionDecision(
        execution_id=(
            "umd:market-query-execution:"
            + suffix * 64
        ),
        execution_hash=execution_hash,
        query_id=(
            "umd:market-query:"
            + suffix * 64
        ),
        result_id=(
            "umd:market-query-result:"
            + suffix * 64
        ),
        admitted=admitted,
        checks=checks,
        rejection_reasons=(
            ()
            if admitted
            else ("execution_id_not_seen",)
        ),
        lineage=lineage,
    )


def entry(
    sequence_number: int,
    value: CertifiedActiveMarketQueryExecutionAdmissionDecision,
    previous_entry_hash: str | None,
) -> CertifiedActiveMarketQueryExecutionLedgerEntry:
    parents = [value.record_hash]

    if previous_entry_hash is not None:
        parents.append(previous_entry_hash)

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-026",
        revision=UMD_026_REVISION,
        schema_version="1.0.0",
        parent_hashes=tuple(parents),
        source_refs=(
            f"fixture://umd-026/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQueryExecutionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"read_only": True},
        lineage=lineage,
    )


def ledger(entries) -> ReadOnlyActiveMarketQueryExecutionAdmissionLedger:
    return ReadOnlyActiveMarketQueryExecutionAdmissionLedger(
        entries=tuple(entries),
        ledger_lineage=ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-026",
            revision=UMD_026_REVISION,
            schema_version="1.0.0",
            parent_hashes=tuple(
                item.entry_hash
                for item in entries
            ),
            source_refs=(
                "fixture://umd-026/ledger",
            ),
            created_at=FIXED,
        ),
    )


class TestUMD026(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_026_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger()
        )

    def test_entry_identity_deterministic(self) -> None:
        value = decision("a", True)
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
            decision("a", True),
            None,
        )
        second = entry(
            2,
            decision("b", False),
            first.entry_hash,
        )

        result = certify_active_market_query_execution_admission_ledger(
            ledger((second, first))
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["entry_count"], 2)
        self.assertEqual(result["admitted_count"], 1)
        self.assertEqual(result["rejected_count"], 1)

    def test_sequence_gap_rejected(self) -> None:
        first = entry(
            1,
            decision("a", True),
            None,
        )
        third = entry(
            3,
            decision("b", True),
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, third))

    def test_previous_hash_mismatch_rejected(self) -> None:
        first = entry(
            1,
            decision("a", True),
            None,
        )
        second = entry(
            2,
            decision("b", True),
            "c" * 64,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_duplicate_execution_rejected(self) -> None:
        value = decision("a", True)
        first = entry(1, value, None)
        second = entry(
            2,
            value,
            first.entry_hash,
        )

        with self.assertRaises(ValueError):
            ledger((first, second))

    def test_lineage_requires_decision_hash(self) -> None:
        value = decision("a", True)

        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-026",
            revision=UMD_026_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=(
                "fixture://umd-026/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQueryExecutionLedgerEntry(
                sequence_number=1,
                previous_entry_hash=None,
                decision=value,
                recorded_at=FIXED,
                metadata={},
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        item = entry(
            1,
            decision("a", True),
            None,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.sequence_number = 2

        with self.assertRaises(TypeError):
            item.metadata["read_only"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_026_certification_manifest()

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
    print(" UMD-026 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION LEDGER"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD026
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_026_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-025 "
        "consumed read-only"
    )
    print(
        "[PASS] Query execution ledger entry IDs deterministic"
    )
    print(
        "[PASS] Append-only sequence continuity enforced"
    )
    print(
        "[PASS] Previous-entry hash chain verified"
    )
    print(
        "[PASS] Execution-admission decision lineage verified"
    )
    print(
        "[PASS] Duplicate execution, decision, and result replay rejected"
    )
    print(
        "[PASS] Admitted and rejected execution indexes verified"
    )
    print(
        "[PASS] Latest admitted execution view deterministic"
    )
    print(
        "[PASS] Read-only query execution ledger certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-026 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY EXECUTION LEDGER CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_execution_ledger import (
    UMD_026_BUILD_ID,
    UMD_026_BUILD_NAME,
    UMD_026_REVISION,
    UMD_026_SCHEMA_VERSION,
    CertifiedActiveMarketQueryExecutionLedgerEntry,
    ReadOnlyActiveMarketQueryExecutionAdmissionLedger,
    UMD026CertificationManifest,
    build_umd_026_certification_manifest,
    certify_active_market_query_execution_admission_ledger,
    certify_umd_026_foundation,
    verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger,
)
"""

EXPORTED_NAMES = (
    "UMD_026_BUILD_ID",
    "UMD_026_BUILD_NAME",
    "UMD_026_REVISION",
    "UMD_026_SCHEMA_VERSION",
    "CertifiedActiveMarketQueryExecutionLedgerEntry",
    "ReadOnlyActiveMarketQueryExecutionAdmissionLedger",
    "UMD026CertificationManifest",
    "build_umd_026_certification_manifest",
    "certify_active_market_query_execution_admission_ledger",
    "certify_umd_026_foundation",
    "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger",
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
    os.replace(temporary, path)


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(
        encoding="utf-8"
    )
    marker = (
        "from "
        ".certified_active_canonical_market_registry_"
        "query_execution_ledger import ("
    )

    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    if "__all__" in source:
        start = source.index(
            "__all__ = ["
        )
        end = source.index(
            "]",
            start,
        )
        block = source[start : end + 1]

        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]

        if missing:
            block = (
                block[:-1]
                + "".join(
                    f'    "{name}",\n'
                    for name in missing
                )
                + "]"
            )
            source = (
                source[:start]
                + block
                + source[end + 1 :]
            )
    else:
        source += (
            "\n__all__ = [\n"
            + "".join(
                f'    "{name}",\n'
                for name in EXPORTED_NAMES
            )
            + "]\n"
        )

    write_exact(INIT, source)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        modules = (
            ("universal_market_discovery_foundation", "verify_umd_foundation"),
            ("certified_canonical_market_contract", "verify_umd_002_certified_canonical_market_contract"),
            ("certified_venue_identity_registry", "verify_umd_003_certified_venue_identity_registry"),
            ("certified_venue_market_binding_registry", "verify_umd_004_certified_venue_market_binding_registry"),
            ("certified_market_category_hierarchy_registry", "verify_umd_005_certified_market_category_hierarchy_registry"),
            ("certified_market_classification_registry", "verify_umd_006_certified_market_classification_registry"),
            ("certified_market_metadata_registry", "verify_umd_007_certified_market_metadata_registry"),
            ("certified_market_lifecycle_and_settlement_registry", "verify_umd_008_certified_market_lifecycle_and_settlement_registry"),
            ("certified_market_duplicate_resolution_registry", "verify_umd_009_certified_market_duplicate_resolution_registry"),
            ("certified_related_market_graph_registry", "verify_umd_010_certified_related_market_graph_registry"),
            ("certified_incremental_discovery_batch_contract", "verify_umd_011_certified_incremental_discovery_batch_contract"),
            ("certified_incremental_discovery_admission_gate", "verify_umd_012_certified_incremental_discovery_admission_gate"),
            ("certified_discovery_admission_ledger", "verify_umd_013_certified_discovery_admission_ledger"),
            ("certified_admitted_market_materialization_contract", "verify_umd_014_certified_admitted_market_materialization_contract"),
            ("certified_materialized_market_admission_registry", "verify_umd_015_certified_materialized_market_admission_registry"),
            ("certified_canonical_market_registry_snapshot_contract", "verify_umd_016_certified_canonical_market_registry_snapshot_contract"),
            ("certified_canonical_market_registry_snapshot_admission_gate", "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate"),
            ("certified_canonical_market_registry_snapshot_admission_ledger", "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger"),
            ("certified_canonical_market_registry_snapshot_activation_contract", "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract"),
            ("certified_canonical_market_registry_snapshot_activation_gate", "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate"),
            ("certified_canonical_market_registry_snapshot_activation_ledger", "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger"),
            ("certified_active_canonical_market_registry_read_model", "verify_umd_022_certified_active_canonical_market_registry_read_model"),
            ("certified_active_canonical_market_registry_query_contract", "verify_umd_023_certified_active_canonical_market_registry_query_contract"),
            ("certified_active_canonical_market_registry_query_execution_engine", "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine"),
            ("certified_active_canonical_market_registry_query_execution_admission_gate", "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate"),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2."
                "universal_market_discovery."
                + module_name
            )

            verifier = getattr(
                module,
                verifier_name,
            )

            if not verifier():
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
        module = importlib.import_module(
            "qseries_v2."
            "universal_market_discovery."
            "certified_active_canonical_market_registry_"
            "query_execution_ledger"
        )

        required = (
            "CertifiedActiveMarketQueryExecutionLedgerEntry",
            "ReadOnlyActiveMarketQueryExecutionAdmissionLedger",
            "build_umd_026_certification_manifest",
            "certify_active_market_query_execution_admission_ledger",
            "certify_umd_026_foundation",
            "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger",
        )

        missing = [
            name
            for name in required
            if not hasattr(
                module,
                name,
            )
        ]

        if missing:
            raise RuntimeError(
                "UMD-026 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-026 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY EXECUTION LEDGER"
    )
    print("=" * 64)
    print(
        f"[BOOT] Revision: {REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-025 "
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
    update_init()

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

    manifest = {
        "build_id": "UMD-026",
        "revision": REVISION,
        "files": {
            str(
                MODULE.relative_to(ROOT)
            ): sha256_file(MODULE),
            str(
                INIT.relative_to(ROOT)
            ): sha256_file(INIT),
            str(
                TEST.relative_to(ROOT)
            ): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 26)
        ),
        "mode": "append_only_read_only",
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(
        f"[PASS] Wrote: "
        f"{MODULE.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Updated: "
        f"{INIT.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Wrote: "
        f"{TEST.relative_to(ROOT)}"
    )
    print(
        "[PASS] Python compilation verified"
    )
    print(
        "[PASS] Required UMD-026 symbols verified"
    )
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print(
        "[DONE] UMD-026 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_026_certified_active_canonical_market_"
        "registry_query_execution_ledger.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
