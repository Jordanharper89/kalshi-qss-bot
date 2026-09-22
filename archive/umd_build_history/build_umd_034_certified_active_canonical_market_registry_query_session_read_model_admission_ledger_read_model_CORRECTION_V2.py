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
    "UMD_034_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_CORRECTION_V2"
)
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / (
    "certified_active_canonical_market_registry_"
    "query_session_read_model_admission_ledger_read_model.py"
)
INIT = PKG / "__init__.py"
TEST = ROOT / (
    "test_umd_034_certified_active_canonical_market_registry_"
    "query_session_read_model_admission_ledger_read_model.py"
)

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_session_read_model_admission_ledger import (
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
)

UMD_034_BUILD_ID = "UMD-034"
UMD_034_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Session Read Model Admission Ledger Read Model"
)
UMD_034_REVISION = (
    "UMD_034_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_CORRECTION_V2"
)
UMD_034_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "ledger_append",
    "ledger_mutation",
    "record_deletion",
    "record_reordering",
    "read_model_persistence",
    "query_session_mutation",
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
class CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel:
    source_ledger_hash: str
    total_entry_count: int
    admitted_entry_count: int
    rejected_entry_count: int
    ordered_entry_ids: Tuple[str, ...]
    ordered_read_model_hashes: Tuple[str, ...]
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
    _read_model_position_by_hash: Mapping[str, int] = field(
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
                raise TypeError(
                    f"{field_name} must be an integer"
                )
            if value < 0:
                raise ValueError(
                    f"{field_name} must be non-negative"
                )

        if (
            self.admitted_entry_count
            + self.rejected_entry_count
            != self.total_entry_count
        ):
            raise ValueError(
                "admitted and rejected counts must partition total count"
            )

        tuple_fields = (
            "ordered_entry_ids",
            "ordered_read_model_hashes",
            "ordered_decision_ids",
            "admitted_entry_ids",
            "rejected_entry_ids",
        )
        for field_name in tuple_fields:
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
        ordered_read_model_hashes = tuple(
            _sha256(value, "ordered_read_model_hash")
            for value in self.ordered_read_model_hashes
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

        object.__setattr__(
            self,
            "ordered_entry_ids",
            ordered_entry_ids,
        )
        object.__setattr__(
            self,
            "ordered_read_model_hashes",
            ordered_read_model_hashes,
        )
        object.__setattr__(
            self,
            "ordered_decision_ids",
            ordered_decision_ids,
        )
        object.__setattr__(
            self,
            "admitted_entry_ids",
            admitted_entry_ids,
        )
        object.__setattr__(
            self,
            "rejected_entry_ids",
            rejected_entry_ids,
        )

        if len(ordered_entry_ids) != self.total_entry_count:
            raise ValueError(
                "ordered_entry_ids length must equal total count"
            )
        if len(ordered_read_model_hashes) != self.total_entry_count:
            raise ValueError(
                "ordered_read_model_hashes length must equal total count"
            )
        if len(ordered_decision_ids) != self.total_entry_count:
            raise ValueError(
                "ordered_decision_ids length must equal total count"
            )
        if len(admitted_entry_ids) != self.admitted_entry_count:
            raise ValueError(
                "admitted_entry_ids length must equal admitted count"
            )
        if len(rejected_entry_ids) != self.rejected_entry_count:
            raise ValueError(
                "rejected_entry_ids length must equal rejected count"
            )

        if len(set(ordered_entry_ids)) != len(ordered_entry_ids):
            raise ValueError("ordered_entry_ids must be unique")
        if (
            len(set(ordered_read_model_hashes))
            != len(ordered_read_model_hashes)
        ):
            raise ValueError(
                "ordered_read_model_hashes must be unique"
            )
        if (
            len(set(ordered_decision_ids))
            != len(ordered_decision_ids)
        ):
            raise ValueError(
                "ordered_decision_ids must be unique"
            )

        if set(admitted_entry_ids).intersection(
            rejected_entry_ids
        ):
            raise ValueError(
                "admitted and rejected entry IDs must be disjoint"
            )
        if (
            set(admitted_entry_ids).union(rejected_entry_ids)
            != set(ordered_entry_ids)
        ):
            raise ValueError(
                "admission partitions must cover ordered entry IDs"
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
            if self.latest_admitted_entry_id != admitted_entry_ids[-1]:
                raise ValueError(
                    "latest_admitted_entry_id must equal final admitted entry ID"
                )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_034_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-034"
            )
        if self.source_ledger_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "read-model lineage must include source ledger hash"
            )

        object.__setattr__(
            self,
            "_entry_position_by_id",
            MappingProxyType(
                {
                    entry_id: index
                    for index, entry_id in enumerate(
                        ordered_entry_ids,
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
                    read_model_hash: index
                    for index, read_model_hash in enumerate(
                        ordered_read_model_hashes,
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
                    decision_id: index
                    for index, decision_id in enumerate(
                        ordered_decision_ids,
                        start=1,
                    )
                }
            ),
        )

    @property
    def read_model_id(self) -> str:
        return (
            "umd:query-session-read-model-admission-ledger-read-model:"
            + deterministic_sha256(
                {
                    "source_ledger_hash": self.source_ledger_hash,
                    "ordered_entry_ids": self.ordered_entry_ids,
                    "ordered_read_model_hashes": self.ordered_read_model_hashes,
                    "ordered_decision_ids": self.ordered_decision_ids,
                }
            )
        )

    def entry_position(self, entry_id: str) -> int | None:
        return self._entry_position_by_id.get(
            _text(entry_id, "entry_id")
        )

    def read_model_position(
        self,
        read_model_hash: str,
    ) -> int | None:
        return self._read_model_position_by_hash.get(
            _sha256(
                read_model_hash,
                "read_model_hash",
            )
        )

    def decision_position(
        self,
        decision_id: str,
    ) -> int | None:
        return self._decision_position_by_id.get(
            _text(decision_id, "decision_id")
        )

    def is_admitted_entry(self, entry_id: str) -> bool:
        return (
            _text(entry_id, "entry_id")
            in self.admitted_entry_ids
        )

    def is_rejected_entry(self, entry_id: str) -> bool:
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
            "ordered_read_model_hashes": self.ordered_read_model_hashes,
            "ordered_decision_ids": self.ordered_decision_ids,
            "admitted_entry_ids": self.admitted_entry_ids,
            "rejected_entry_ids": self.rejected_entry_ids,
            "latest_entry_id": self.latest_entry_id,
            "latest_admitted_entry_id": self.latest_admitted_entry_id,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_active_market_query_session_read_model_admission_ledger_read_model(
    ledger: ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
    *,
    metadata: Mapping[str, Any] | None = None,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel:
    if not isinstance(
        ledger,
        ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger,
    ):
        raise TypeError(
            "ledger must be a certified UMD-033 admission ledger"
        )

    entries = ledger.entries
    admitted = ledger.admitted_entries()
    rejected = ledger.rejected_entries()

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel(
        source_ledger_hash=ledger.ledger_hash,
        total_entry_count=len(entries),
        admitted_entry_count=len(admitted),
        rejected_entry_count=len(rejected),
        ordered_entry_ids=tuple(
            entry.entry_id
            for entry in entries
        ),
        ordered_read_model_hashes=tuple(
            entry.decision.read_model_hash
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
class UMD034CertificationManifest:
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


def build_umd_034_certification_manifest() -> UMD034CertificationManifest:
    return UMD034CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_034_BUILD_ID,
        build_name=UMD_034_BUILD_NAME,
        revision=UMD_034_REVISION,
        schema_version=UMD_034_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 34)
        ),
        read_model_mode="deterministic_read_only_projection",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_session_read_model_admission_ledger_read_model(
    read_model: CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel,
) -> Mapping[str, Any]:
    checks = {
        "count_partition_valid": (
            read_model.admitted_entry_count
            + read_model.rejected_entry_count
            == read_model.total_entry_count
        ),
        "ordered_entry_count_valid": (
            len(read_model.ordered_entry_ids)
            == read_model.total_entry_count
        ),
        "ordered_read_model_count_valid": (
            len(read_model.ordered_read_model_hashes)
            == read_model.total_entry_count
        ),
        "ordered_decision_count_valid": (
            len(read_model.ordered_decision_ids)
            == read_model.total_entry_count
        ),
        "entry_ids_unique": (
            len(set(read_model.ordered_entry_ids))
            == len(read_model.ordered_entry_ids)
        ),
        "read_model_hashes_unique": (
            len(set(read_model.ordered_read_model_hashes))
            == len(read_model.ordered_read_model_hashes)
        ),
        "decision_ids_unique": (
            len(set(read_model.ordered_decision_ids))
            == len(read_model.ordered_decision_ids)
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
        "latest_entry_valid": (
            (
                read_model.latest_entry_id is None
                and not read_model.ordered_entry_ids
            )
            or (
                bool(read_model.ordered_entry_ids)
                and read_model.latest_entry_id
                == read_model.ordered_entry_ids[-1]
            )
        ),
        "latest_admitted_valid": (
            (
                read_model.latest_admitted_entry_id is None
                and not read_model.admitted_entry_ids
            )
            or (
                bool(read_model.admitted_entry_ids)
                and read_model.latest_admitted_entry_id
                == read_model.admitted_entry_ids[-1]
            )
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
        "read_only_indexes": (
            isinstance(
                read_model._entry_position_by_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._read_model_position_by_hash,
                MappingProxyType,
            )
            and isinstance(
                read_model._decision_position_by_id,
                MappingProxyType,
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
            "admitted_entry_count": read_model.admitted_entry_count,
            "rejected_entry_count": read_model.rejected_entry_count,
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_034_foundation() -> Mapping[str, Any]:
    manifest = build_umd_034_certification_manifest()

    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-034",
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 34)
            )
        ),
        "read_only_projection": (
            manifest.read_model_mode
            == "deterministic_read_only_projection"
        ),
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
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


def verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model() -> bool:
    certification = certify_umd_034_foundation()
    if not certification["certified"]:
        raise RuntimeError(
            "UMD-034 foundation certification failed: "
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
)
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model import (
    UMD_034_REVISION,
    build_active_market_query_session_read_model_admission_ledger_read_model,
    build_umd_034_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger_read_model,
    certify_umd_034_foundation,
)

FIXED = datetime(
    2026,
    8,
    6,
    5,
    38,
    0,
    tzinfo=timezone.utc,
)


def decision(
    suffix: str,
    admitted: bool = True,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash = (suffix.lower() * 64)[:64]
    session_registry_hash = (
        chr(ord(suffix.lower()) + 1) * 64
    )[:64]
    admission_ledger_hash = (
        chr(ord(suffix.lower()) + 2) * 64
    )[:64]

    checks = {
        "read_model_hash_deterministic": admitted,
    }
    rejection_reasons = (
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
            f"fixture://umd-034/decision/{suffix}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model_hash,
        session_registry_hash=session_registry_hash,
        admission_ledger_hash=admission_ledger_hash,
        admitted=admitted,
        checks=checks,
        rejection_reasons=rejection_reasons,
        lineage=lineage,
    )


def ledger_entry(
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
            f"fixture://umd-034/entry/{sequence_number}",
        ),
        created_at=FIXED,
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerEntry(
        sequence_number=sequence_number,
        previous_entry_hash=previous_entry_hash,
        decision=value,
        recorded_at=FIXED,
        metadata={"fixture": True},
        lineage=lineage,
    )


def source_ledger() -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger:
    first = ledger_entry(
        1,
        decision("a", admitted=True),
        None,
    )
    second = ledger_entry(
        2,
        decision("d", admitted=False),
        first.entry_hash,
    )
    third = ledger_entry(
        3,
        decision("c", admitted=True),
        second.entry_hash,
    )

    lineage = ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-033",
        revision=UMD_033_REVISION,
        schema_version="1.0.0",
        parent_hashes=(third.entry_hash,),
        source_refs=("fixture://umd-034/ledger",),
        created_at=FIXED,
    )

    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedger(
        entries=(first, second, third),
        ledger_lineage=lineage,
    )


def read_model_lineage(
    ledger_hash: str,
) -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-034",
        revision=UMD_034_REVISION,
        schema_version="1.0.0",
        parent_hashes=(ledger_hash,),
        source_refs=("fixture://umd-034/read-model",),
        created_at=FIXED,
    )


class TestUMD034(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        result = certify_umd_034_foundation()
        self.assertTrue(result["certified"])
        self.assertEqual(result["build_id"], "UMD-034")

    def test_projection_certifies(self) -> None:
        ledger = source_ledger()
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
        )

        result = (
            certify_active_market_query_session_read_model_admission_ledger_read_model(
                model
            )
        )

        self.assertTrue(result["certified"])
        self.assertEqual(result["total_entry_count"], 3)
        self.assertEqual(result["admitted_entry_count"], 2)
        self.assertEqual(result["rejected_entry_count"], 1)

    def test_projection_is_deterministic(self) -> None:
        ledger = source_ledger()
        lineage = read_model_lineage(
            ledger.ledger_hash
        )

        first = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=lineage,
            )
        )
        second = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=lineage,
            )
        )

        self.assertEqual(
            first.read_model_id,
            second.read_model_id,
        )
        self.assertEqual(
            first.read_model_hash,
            second.read_model_hash,
        )

    def test_positions_and_partitions(self) -> None:
        ledger = source_ledger()
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
        )

        first = ledger.entries[0]
        second = ledger.entries[1]
        third = ledger.entries[2]

        self.assertEqual(
            model.entry_position(first.entry_id),
            1,
        )
        self.assertEqual(
            model.read_model_position(
                second.decision.read_model_hash
            ),
            2,
        )
        self.assertEqual(
            model.decision_position(
                third.decision.decision_id
            ),
            3,
        )
        self.assertTrue(
            model.is_admitted_entry(first.entry_id)
        )
        self.assertTrue(
            model.is_rejected_entry(second.entry_id)
        )
        self.assertEqual(
            model.latest_entry_id,
            third.entry_id,
        )
        self.assertEqual(
            model.latest_admitted_entry_id,
            third.entry_id,
        )

    def test_lineage_requires_ledger_hash(self) -> None:
        ledger = source_ledger()
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-034",
            revision=UMD_034_REVISION,
            schema_version="1.0.0",
            parent_hashes=("f" * 64,),
            source_refs=("fixture://umd-034/bad",),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                lineage=bad_lineage,
            )

    def test_immutable(self) -> None:
        ledger = source_ledger()
        model = (
            build_active_market_query_session_read_model_admission_ledger_read_model(
                ledger,
                metadata={"read_only": True},
                lineage=read_model_lineage(
                    ledger.ledger_hash
                ),
            )
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            model.total_entry_count = 99

        with self.assertRaises(TypeError):
            model.metadata["read_only"] = False

        with self.assertRaises(TypeError):
            model._entry_position_by_id[
                model.ordered_entry_ids[0]
            ] = 99

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_034_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "deterministic_read_only_projection",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 72)
    print(" UMD-034 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL"
    )
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD034
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_034_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-033 "
        "consumed read-only"
    )
    print(
        "[PASS] UMD-033 admission ledger projected deterministically"
    )
    print(
        "[PASS] Ordered ledger-entry identity preserved"
    )
    print(
        "[PASS] Read-model and decision indexes certified"
    )
    print(
        "[PASS] Admitted/rejected partition certified"
    )
    print(
        "[PASS] Latest entry and latest admitted entry certified"
    )
    print(
        "[PASS] Immutable lineage bound to source ledger hash"
    )
    print(
        "[PASS] Replay equality verified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-034 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION LEDGER READ MODEL CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model import (
    UMD_034_BUILD_ID,
    UMD_034_BUILD_NAME,
    UMD_034_REVISION,
    UMD_034_SCHEMA_VERSION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel,
    UMD034CertificationManifest,
    build_active_market_query_session_read_model_admission_ledger_read_model,
    build_umd_034_certification_manifest,
    certify_active_market_query_session_read_model_admission_ledger_read_model,
    certify_umd_034_foundation,
    verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model,
)
"""

EXPORTED_NAMES = (
    "UMD_034_BUILD_ID",
    "UMD_034_BUILD_NAME",
    "UMD_034_REVISION",
    "UMD_034_SCHEMA_VERSION",
    "CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModel",
    "UMD034CertificationManifest",
    "build_active_market_query_session_read_model_admission_ledger_read_model",
    "build_umd_034_certification_manifest",
    "certify_active_market_query_session_read_model_admission_ledger_read_model",
    "certify_umd_034_foundation",
    "verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model",
)

UPSTREAM_MODULES = (
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
    ("certified_active_canonical_market_registry_query_execution_ledger", "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger"),
    ("certified_active_canonical_market_registry_query_execution_read_model", "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model"),
    ("certified_active_canonical_market_registry_query_session_contract", "verify_umd_028_certified_active_canonical_market_registry_query_session_contract"),
    ("certified_active_canonical_market_registry_query_session_admission_gate", "verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate"),
    ("certified_active_canonical_market_registry_query_session_admission_ledger", "verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger"),
    ("certified_active_canonical_market_registry_query_session_read_model", "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model"),
    ("certified_active_canonical_market_registry_query_session_read_model_admission_gate", "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate"),
    ("certified_active_canonical_market_registry_query_session_read_model_admission_ledger", "verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger"),
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


def repair_and_update_init(*, include_umd_034: bool = True) -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(encoding="utf-8")

    malformed_umd_033 = """    verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger,
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
)"""
    corrected_umd_033 = """    verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger,
)"""
    if malformed_umd_033 in source:
        source = source.replace(
            malformed_umd_033,
            corrected_umd_033,
            1,
        )

    marker = (
        "from "
        ".certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model "
        "import ("
    )
    if include_umd_034 and marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

    start = source.find("__all__ = [")
    if start == -1:
        raise RuntimeError("UMD __init__.py missing __all__ list")
    end = source.find("]", start)
    if end == -1:
        raise RuntimeError("UMD __init__.py __all__ list is unterminated")
    block = source[start:end + 1]

    umd_033_names = (
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
    all_names = (
        umd_033_names + EXPORTED_NAMES
        if include_umd_034
        else umd_033_names
    )

    missing = [
        name
        for name in all_names
        if f'"{name}"' not in block
        and f"'{name}'" not in block
    ]
    if missing:
        block = (
            block[:-1]
            + "".join(f'    "{name}",\n' for name in missing)
            + "]"
        )
        source = source[:start] + block + source[end + 1:]

    write_exact(INIT, source)

    try:
        py_compile.compile(str(INIT), doraise=True)
    except Exception:
        raise RuntimeError(
            "UMD __init__.py repair/update failed compilation; "
            "installation stopped before UMD-034 verification"
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
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            verifier = getattr(
                module,
                verifier_name,
                None,
            )
            if verifier is None:
                raise RuntimeError(
                    f"Certified upstream verifier missing: "
                    f"{module_name}.{verifier_name}"
                )
            if verifier() is not True:
                raise RuntimeError(
                    f"Certified upstream verification failed: "
                    f"{module_name}"
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
            "query_session_read_model_admission_ledger_read_model"
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
                "UMD-034 missing symbols: "
                + ", ".join(missing)
            )

        verifier = getattr(
            module,
            "verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model",
        )
        if verifier() is not True:
            raise RuntimeError(
                "UMD-034 verification returned false"
            )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 72)
    print(" UMD-034 CORRECTION V2 FULL REPLACEMENT INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL"
    )
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    repair_and_update_init(include_umd_034=False)
    print(
        "[PASS] Existing UMD package initializer repaired and compiled"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-033 "
        "verified read-only"
    )

    write_exact(
        MODULE,
        MODULE_SOURCE,
    )
    repair_and_update_init()
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

    manifest = {
        "build_id": "UMD-034",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 34)
        ),
        "mode": "deterministic_read_only_projection",
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
    print("[PASS] Required UMD-034 symbols verified")
    print(
        f"[PASS] Deterministic install hash: {install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-034 CORRECTION V2 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_034_certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
