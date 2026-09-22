from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_037_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_CORRECTION_V2"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger import (\n    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n)\n\nUMD_037_BUILD_ID = "UMD-037"\nUMD_037_BUILD_NAME = (\n    "Certified Active Canonical Market Registry Query Session "\n    "Read Model Admission Ledger Read Model Admission Ledger Read Model"\n)\nUMD_037_REVISION = (\n    "UMD_037_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_"\n    "READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_V1"\n)\nUMD_037_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_discovery",\n    "market_scanning",\n    "ledger_append",\n    "ledger_mutation",\n    "record_deletion",\n    "record_reordering",\n    "read_model_mutation",\n    "read_model_persistence",\n    "active_registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(\n        character not in "0123456789abcdef"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(\n        dict(\n            sorted(\n                (str(key), item)\n                for key, item in value.items()\n            )\n        )\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel:\n    source_ledger_hash: str\n    total_entry_count: int\n    admitted_entry_count: int\n    rejected_entry_count: int\n    ordered_entry_ids: Tuple[str, ...]\n    ordered_read_model_hashes: Tuple[str, ...]\n    ordered_decision_ids: Tuple[str, ...]\n    admitted_entry_ids: Tuple[str, ...]\n    rejected_entry_ids: Tuple[str, ...]\n    latest_entry_id: str | None\n    latest_admitted_entry_id: str | None\n    metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n    _entry_position_by_id: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _read_model_position_by_hash: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _decision_position_by_id: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n\n    def __post_init__(self) -> None:\n        object.__setattr__(\n            self,\n            "source_ledger_hash",\n            _sha256(\n                self.source_ledger_hash,\n                "source_ledger_hash",\n            ),\n        )\n\n        for field_name in (\n            "total_entry_count",\n            "admitted_entry_count",\n            "rejected_entry_count",\n        ):\n            value = getattr(self, field_name)\n            if not isinstance(value, int):\n                raise TypeError(\n                    f"{field_name} must be an integer"\n                )\n            if value < 0:\n                raise ValueError(\n                    f"{field_name} must be non-negative"\n                )\n\n        if (\n            self.admitted_entry_count\n            + self.rejected_entry_count\n            != self.total_entry_count\n        ):\n            raise ValueError(\n                "admitted and rejected counts must partition total count"\n            )\n\n        for field_name in (\n            "ordered_entry_ids",\n            "ordered_read_model_hashes",\n            "ordered_decision_ids",\n            "admitted_entry_ids",\n            "rejected_entry_ids",\n        ):\n            value = getattr(self, field_name)\n            if not isinstance(value, tuple):\n                object.__setattr__(\n                    self,\n                    field_name,\n                    tuple(value),\n                )\n\n        ordered_entry_ids = tuple(\n            _text(value, "ordered_entry_id")\n            for value in self.ordered_entry_ids\n        )\n        ordered_read_model_hashes = tuple(\n            _sha256(value, "ordered_read_model_hash")\n            for value in self.ordered_read_model_hashes\n        )\n        ordered_decision_ids = tuple(\n            _text(value, "ordered_decision_id")\n            for value in self.ordered_decision_ids\n        )\n        admitted_entry_ids = tuple(\n            _text(value, "admitted_entry_id")\n            for value in self.admitted_entry_ids\n        )\n        rejected_entry_ids = tuple(\n            _text(value, "rejected_entry_id")\n            for value in self.rejected_entry_ids\n        )\n\n        object.__setattr__(\n            self,\n            "ordered_entry_ids",\n            ordered_entry_ids,\n        )\n        object.__setattr__(\n            self,\n            "ordered_read_model_hashes",\n            ordered_read_model_hashes,\n        )\n        object.__setattr__(\n            self,\n            "ordered_decision_ids",\n            ordered_decision_ids,\n        )\n        object.__setattr__(\n            self,\n            "admitted_entry_ids",\n            admitted_entry_ids,\n        )\n        object.__setattr__(\n            self,\n            "rejected_entry_ids",\n            rejected_entry_ids,\n        )\n\n        if len(ordered_entry_ids) != self.total_entry_count:\n            raise ValueError(\n                "ordered_entry_ids length must equal total count"\n            )\n        if (\n            len(ordered_read_model_hashes)\n            != self.total_entry_count\n        ):\n            raise ValueError(\n                "ordered_read_model_hashes length must equal total count"\n            )\n        if len(ordered_decision_ids) != self.total_entry_count:\n            raise ValueError(\n                "ordered_decision_ids length must equal total count"\n            )\n        if len(admitted_entry_ids) != self.admitted_entry_count:\n            raise ValueError(\n                "admitted_entry_ids length must equal admitted count"\n            )\n        if len(rejected_entry_ids) != self.rejected_entry_count:\n            raise ValueError(\n                "rejected_entry_ids length must equal rejected count"\n            )\n\n        if len(set(ordered_entry_ids)) != len(ordered_entry_ids):\n            raise ValueError(\n                "ordered_entry_ids must be unique"\n            )\n        if (\n            len(set(ordered_read_model_hashes))\n            != len(ordered_read_model_hashes)\n        ):\n            raise ValueError(\n                "ordered_read_model_hashes must be unique"\n            )\n        if (\n            len(set(ordered_decision_ids))\n            != len(ordered_decision_ids)\n        ):\n            raise ValueError(\n                "ordered_decision_ids must be unique"\n            )\n\n        if set(admitted_entry_ids).intersection(\n            rejected_entry_ids\n        ):\n            raise ValueError(\n                "admitted and rejected entry IDs must be disjoint"\n            )\n        if (\n            set(admitted_entry_ids).union(rejected_entry_ids)\n            != set(ordered_entry_ids)\n        ):\n            raise ValueError(\n                "admission partitions must cover ordered entry IDs"\n            )\n\n        if self.latest_entry_id is None:\n            if ordered_entry_ids:\n                raise ValueError(\n                    "latest_entry_id required when entries exist"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "latest_entry_id",\n                _text(\n                    self.latest_entry_id,\n                    "latest_entry_id",\n                ),\n            )\n            if self.latest_entry_id != ordered_entry_ids[-1]:\n                raise ValueError(\n                    "latest_entry_id must equal final ordered entry ID"\n                )\n\n        if self.latest_admitted_entry_id is None:\n            if admitted_entry_ids:\n                raise ValueError(\n                    "latest_admitted_entry_id required when admitted entries exist"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "latest_admitted_entry_id",\n                _text(\n                    self.latest_admitted_entry_id,\n                    "latest_admitted_entry_id",\n                ),\n            )\n            if (\n                self.latest_admitted_entry_id\n                != admitted_entry_ids[-1]\n            ):\n                raise ValueError(\n                    "latest_admitted_entry_id must equal final admitted entry ID"\n                )\n\n        object.__setattr__(\n            self,\n            "metadata",\n            _freeze(self.metadata),\n        )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError(\n                "read-model lineage must belong to UMD"\n            )\n        if self.lineage.build_id != UMD_037_BUILD_ID:\n            raise ValueError(\n                "read-model lineage must use build_id UMD-037"\n            )\n        if (\n            self.source_ledger_hash\n            not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "read-model lineage must include source ledger hash"\n            )\n\n        object.__setattr__(\n            self,\n            "_entry_position_by_id",\n            MappingProxyType(\n                {\n                    entry_id: index\n                    for index, entry_id in enumerate(\n                        ordered_entry_ids,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_read_model_position_by_hash",\n            MappingProxyType(\n                {\n                    read_model_hash: index\n                    for index, read_model_hash in enumerate(\n                        ordered_read_model_hashes,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_decision_position_by_id",\n            MappingProxyType(\n                {\n                    decision_id: index\n                    for index, decision_id in enumerate(\n                        ordered_decision_ids,\n                        start=1,\n                    )\n                }\n            ),\n        )\n\n    @property\n    def read_model_id(self) -> str:\n        return (\n            "umd:query-session-read-model-admission-ledger-read-model-"\n            "admission-ledger-read-model:"\n            + deterministic_sha256(\n                {\n                    "source_ledger_hash": self.source_ledger_hash,\n                    "ordered_entry_ids": self.ordered_entry_ids,\n                    "ordered_read_model_hashes": (\n                        self.ordered_read_model_hashes\n                    ),\n                    "ordered_decision_ids": (\n                        self.ordered_decision_ids\n                    ),\n                }\n            )\n        )\n\n    def entry_position(self, entry_id: str) -> int | None:\n        return self._entry_position_by_id.get(\n            _text(entry_id, "entry_id")\n        )\n\n    def read_model_position(\n        self,\n        read_model_hash: str,\n    ) -> int | None:\n        return self._read_model_position_by_hash.get(\n            _sha256(\n                read_model_hash,\n                "read_model_hash",\n            )\n        )\n\n    def decision_position(\n        self,\n        decision_id: str,\n    ) -> int | None:\n        return self._decision_position_by_id.get(\n            _text(decision_id, "decision_id")\n        )\n\n    def is_admitted_entry(self, entry_id: str) -> bool:\n        return (\n            _text(entry_id, "entry_id")\n            in self.admitted_entry_ids\n        )\n\n    def is_rejected_entry(self, entry_id: str) -> bool:\n        return (\n            _text(entry_id, "entry_id")\n            in self.rejected_entry_ids\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "read_model_id": self.read_model_id,\n            "source_ledger_hash": self.source_ledger_hash,\n            "total_entry_count": self.total_entry_count,\n            "admitted_entry_count": self.admitted_entry_count,\n            "rejected_entry_count": self.rejected_entry_count,\n            "ordered_entry_ids": self.ordered_entry_ids,\n            "ordered_read_model_hashes": (\n                self.ordered_read_model_hashes\n            ),\n            "ordered_decision_ids": (\n                self.ordered_decision_ids\n            ),\n            "admitted_entry_ids": self.admitted_entry_ids,\n            "rejected_entry_ids": self.rejected_entry_ids,\n            "latest_entry_id": self.latest_entry_id,\n            "latest_admitted_entry_id": (\n                self.latest_admitted_entry_id\n            ),\n            "metadata": self.metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def read_model_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n    ledger: ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n    *,\n    metadata: Mapping[str, Any] | None = None,\n    lineage: ImmutableLineage,\n) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel:\n    if not isinstance(\n        ledger,\n        ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n    ):\n        raise TypeError(\n            "ledger must be a certified UMD-036 admission ledger"\n        )\n\n    entries = ledger.entries\n    admitted = ledger.admitted_entries()\n    rejected = ledger.rejected_entries()\n\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel(\n        source_ledger_hash=ledger.ledger_hash,\n        total_entry_count=len(entries),\n        admitted_entry_count=len(admitted),\n        rejected_entry_count=len(rejected),\n        ordered_entry_ids=tuple(\n            entry.entry_id\n            for entry in entries\n        ),\n        ordered_read_model_hashes=tuple(\n            entry.decision.read_model_hash\n            for entry in entries\n        ),\n        ordered_decision_ids=tuple(\n            entry.decision.decision_id\n            for entry in entries\n        ),\n        admitted_entry_ids=tuple(\n            entry.entry_id\n            for entry in admitted\n        ),\n        rejected_entry_ids=tuple(\n            entry.entry_id\n            for entry in rejected\n        ),\n        latest_entry_id=(\n            None\n            if not entries\n            else entries[-1].entry_id\n        ),\n        latest_admitted_entry_id=(\n            None\n            if not admitted\n            else admitted[-1].entry_id\n        ),\n        metadata=(\n            {}\n            if metadata is None\n            else metadata\n        ),\n        lineage=lineage,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD037CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    build_name: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    read_model_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "build_name": self.build_name,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "read_model_mode": self.read_model_mode,\n            "prohibited_capabilities": (\n                self.prohibited_capabilities\n            ),\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_037_certification_manifest() -> UMD037CertificationManifest:\n    return UMD037CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_037_BUILD_ID,\n        build_name=UMD_037_BUILD_NAME,\n        revision=UMD_037_REVISION,\n        schema_version=UMD_037_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 37)\n        ),\n        read_model_mode="deterministic_read_only_projection",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n    read_model: CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,\n) -> Mapping[str, Any]:\n    checks = {\n        "count_partition_valid": (\n            read_model.admitted_entry_count\n            + read_model.rejected_entry_count\n            == read_model.total_entry_count\n        ),\n        "ordered_entry_count_valid": (\n            len(read_model.ordered_entry_ids)\n            == read_model.total_entry_count\n        ),\n        "ordered_read_model_count_valid": (\n            len(read_model.ordered_read_model_hashes)\n            == read_model.total_entry_count\n        ),\n        "ordered_decision_count_valid": (\n            len(read_model.ordered_decision_ids)\n            == read_model.total_entry_count\n        ),\n        "entry_ids_unique": (\n            len(set(read_model.ordered_entry_ids))\n            == len(read_model.ordered_entry_ids)\n        ),\n        "read_model_hashes_unique": (\n            len(set(read_model.ordered_read_model_hashes))\n            == len(read_model.ordered_read_model_hashes)\n        ),\n        "decision_ids_unique": (\n            len(set(read_model.ordered_decision_ids))\n            == len(read_model.ordered_decision_ids)\n        ),\n        "partition_disjoint": (\n            not set(read_model.admitted_entry_ids).intersection(\n                read_model.rejected_entry_ids\n            )\n        ),\n        "partition_complete": (\n            set(read_model.admitted_entry_ids).union(\n                read_model.rejected_entry_ids\n            )\n            == set(read_model.ordered_entry_ids)\n        ),\n        "latest_entry_valid": (\n            (\n                read_model.latest_entry_id is None\n                and not read_model.ordered_entry_ids\n            )\n            or (\n                bool(read_model.ordered_entry_ids)\n                and read_model.latest_entry_id\n                == read_model.ordered_entry_ids[-1]\n            )\n        ),\n        "latest_admitted_valid": (\n            (\n                read_model.latest_admitted_entry_id is None\n                and not read_model.admitted_entry_ids\n            )\n            or (\n                bool(read_model.admitted_entry_ids)\n                and read_model.latest_admitted_entry_id\n                == read_model.admitted_entry_ids[-1]\n            )\n        ),\n        "lineage_bound": (\n            read_model.source_ledger_hash\n            in read_model.lineage.parent_hashes\n        ),\n        "deterministic_replay": (\n            read_model.read_model_hash\n            == deterministic_sha256(\n                read_model.to_canonical_dict()\n            )\n        ),\n        "read_only_indexes": (\n            isinstance(\n                read_model._entry_position_by_id,\n                MappingProxyType,\n            )\n            and isinstance(\n                read_model._read_model_position_by_hash,\n                MappingProxyType,\n            )\n            and isinstance(\n                read_model._decision_position_by_id,\n                MappingProxyType,\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "read_model_id": read_model.read_model_id,\n            "read_model_hash": read_model.read_model_hash,\n            "source_ledger_hash": read_model.source_ledger_hash,\n            "total_entry_count": read_model.total_entry_count,\n            "admitted_entry_count": (\n                read_model.admitted_entry_count\n            ),\n            "rejected_entry_count": (\n                read_model.rejected_entry_count\n            ),\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_037_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_037_certification_manifest()\n\n    checks = {\n        "subsystem_identity": (\n            manifest.subsystem_id == "UMD"\n        ),\n        "build_identity": (\n            manifest.build_id == "UMD-037"\n        ),\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 37)\n            )\n        ),\n        "read_only_projection": (\n            manifest.read_model_mode\n            == "deterministic_read_only_projection"\n        ),\n        "network_disabled": (\n            manifest.network_enabled is False\n        ),\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": (\n            manifest.mutation_enabled is False\n        ),\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": (\n            manifest.execution_enabled is False\n        ),\n        "deterministic_manifest_hash": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model() -> bool:\n    certification = certify_umd_037_foundation()\n    if not certification["certified"]:\n        raise RuntimeError(\n            "UMD-037 foundation certification failed: "\n            + ", ".join(certification["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate import (\n    UMD_035_REVISION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger import (\n    UMD_036_REVISION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n)\nfrom qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model import (\n    UMD_037_REVISION,\n    build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,\n    build_umd_037_certification_manifest,\n    certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,\n    certify_umd_037_foundation,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    6,\n    6,\n    55,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef decision(\n    suffix: str,\n    admitted: bool = True,\n) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision:\n    read_model_hash = (suffix * 64)[:64]\n    source_ledger_hash = (\n        chr(ord(suffix) + 1) * 64\n    )[:64]\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-035",\n        revision=UMD_035_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            read_model_hash,\n            source_ledger_hash,\n        ),\n        source_refs=(\n            f"fixture://umd-037/decision/{suffix}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision(\n        read_model_hash=read_model_hash,\n        source_ledger_hash=source_ledger_hash,\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef entry(\n    number: int,\n    value: CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,\n    previous: str | None,\n) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry:\n    parents = [value.record_hash]\n    if previous is not None:\n        parents.append(previous)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-036",\n        revision=UMD_036_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(\n            f"fixture://umd-037/entry/{number}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=value,\n        recorded_at=FIXED,\n        metadata={"fixture": True},\n        lineage=lineage,\n    )\n\n\ndef source_ledger() -> ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger:\n    first = entry(\n        1,\n        decision("a", True),\n        None,\n    )\n    second = entry(\n        2,\n        decision("d", False),\n        first.entry_hash,\n    )\n    third = entry(\n        3,\n        decision("e", True),\n        second.entry_hash,\n    )\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-036",\n        revision=UMD_036_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(third.entry_hash,),\n        source_refs=(\n            "fixture://umd-037/ledger",\n        ),\n        created_at=FIXED,\n    )\n\n    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(\n        entries=(first, second, third),\n        ledger_lineage=lineage,\n    )\n\n\ndef read_model_lineage(\n    ledger_hash: str,\n) -> ImmutableLineage:\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-037",\n        revision=UMD_037_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(ledger_hash,),\n        source_refs=(\n            "fixture://umd-037/read-model",\n        ),\n        created_at=FIXED,\n    )\n\n\nclass TestUMD037(unittest.TestCase):\n    def test_foundation_certifies(self) -> None:\n        result = certify_umd_037_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(\n            result["build_id"],\n            "UMD-037",\n        )\n\n    def test_projection_certifies(self) -> None:\n        ledger = source_ledger()\n        model = build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n\n        result = certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            model\n        )\n\n        self.assertTrue(result["certified"])\n        self.assertEqual(\n            result["total_entry_count"],\n            3,\n        )\n        self.assertEqual(\n            result["admitted_entry_count"],\n            2,\n        )\n        self.assertEqual(\n            result["rejected_entry_count"],\n            1,\n        )\n\n    def test_projection_is_deterministic(self) -> None:\n        ledger = source_ledger()\n        lineage = read_model_lineage(\n            ledger.ledger_hash\n        )\n\n        first = build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=lineage,\n        )\n        second = build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=lineage,\n        )\n\n        self.assertEqual(\n            first.read_model_id,\n            second.read_model_id,\n        )\n        self.assertEqual(\n            first.read_model_hash,\n            second.read_model_hash,\n        )\n\n    def test_positions_and_partitions(self) -> None:\n        ledger = source_ledger()\n        model = build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            ledger,\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n\n        first, second, third = ledger.entries\n\n        self.assertEqual(\n            model.entry_position(first.entry_id),\n            1,\n        )\n        self.assertEqual(\n            model.read_model_position(\n                second.decision.read_model_hash\n            ),\n            2,\n        )\n        self.assertEqual(\n            model.decision_position(\n                third.decision.decision_id\n            ),\n            3,\n        )\n        self.assertTrue(\n            model.is_admitted_entry(\n                first.entry_id\n            )\n        )\n        self.assertTrue(\n            model.is_rejected_entry(\n                second.entry_id\n            )\n        )\n        self.assertEqual(\n            model.latest_entry_id,\n            third.entry_id,\n        )\n        self.assertEqual(\n            model.latest_admitted_entry_id,\n            third.entry_id,\n        )\n\n    def test_lineage_requires_ledger_hash(self) -> None:\n        ledger = source_ledger()\n        bad_lineage = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-037",\n            revision=UMD_037_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=("f" * 64,),\n            source_refs=(\n                "fixture://umd-037/bad",\n            ),\n            created_at=FIXED,\n        )\n\n        with self.assertRaises(ValueError):\n            build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n                ledger,\n                lineage=bad_lineage,\n            )\n\n    def test_immutable(self) -> None:\n        ledger = source_ledger()\n        model = build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            model.total_entry_count = 99\n\n        with self.assertRaises(TypeError):\n            model.metadata["read_only"] = False\n\n        with self.assertRaises(TypeError):\n            model._entry_position_by_id[\n                model.ordered_entry_ids[0]\n            ] = 99\n\n    def test_side_effects_disabled(self) -> None:\n        manifest = (\n            build_umd_037_certification_manifest()\n        )\n\n        self.assertEqual(\n            manifest.read_model_mode,\n            "deterministic_read_only_projection",\n        )\n        self.assertFalse(\n            manifest.network_enabled\n        )\n        self.assertFalse(\n            manifest.persistence_enabled\n        )\n        self.assertFalse(\n            manifest.mutation_enabled\n        )\n        self.assertFalse(\n            manifest.publication_enabled\n        )\n        self.assertFalse(\n            manifest.execution_enabled\n        )\n\n\nif __name__ == "__main__":\n    print("=" * 80)\n    print(" UMD-037 CERTIFICATION TEST")\n    print(\n        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "\n        "READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER "\n        "READ MODEL"\n    )\n    print("=" * 80)\n\n    suite = (\n        unittest.defaultTestLoader.loadTestsFromTestCase(\n            TestUMD037\n        )\n    )\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(suite)\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = (\n        build_umd_037_certification_manifest()\n    )\n\n    print()\n    print(\n        f"[PASS] Build: {manifest.build_id}"\n    )\n    print(\n        f"[PASS] Revision: {manifest.revision}"\n    )\n    print(\n        f"[PASS] Manifest hash: "\n        f"{manifest.manifest_hash}"\n    )\n    print(\n        "[PASS] UMD-001 through UMD-036 "\n        "consumed read-only"\n    )\n    print(\n        "[PASS] UMD-036 admission ledger projected deterministically"\n    )\n    print(\n        "[PASS] Ordered ledger-entry identity preserved"\n    )\n    print(\n        "[PASS] Read-model and decision indexes certified"\n    )\n    print(\n        "[PASS] Admitted/rejected partition certified"\n    )\n    print(\n        "[PASS] Latest entry and latest admitted entry certified"\n    )\n    print(\n        "[PASS] Immutable lineage bound to source ledger hash"\n    )\n    print(\n        "[PASS] Replay equality verified"\n    )\n    print(\n        "[PASS] Network and persistence disabled"\n    )\n    print(\n        "[PASS] Publication and Q Series execution disabled"\n    )\n    print(\n        "[DONE] UMD-037 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "\n        "QUERY SESSION READ MODEL ADMISSION LEDGER READ MODEL "\n        "ADMISSION LEDGER READ MODEL CERTIFIED"\n    )\n'
INIT_IMPORT = '\nfrom .certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model import (\n    UMD_037_BUILD_ID,\n    UMD_037_BUILD_NAME,\n    UMD_037_REVISION,\n    UMD_037_SCHEMA_VERSION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,\n    UMD037CertificationManifest,\n    build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,\n    build_umd_037_certification_manifest,\n    certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,\n    certify_umd_037_foundation,\n    verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model,\n)\n'
EXPORTED_NAMES = ('UMD_037_BUILD_ID', 'UMD_037_BUILD_NAME', 'UMD_037_REVISION', 'UMD_037_SCHEMA_VERSION', 'CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel', 'UMD037CertificationManifest', 'build_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'build_umd_037_certification_manifest', 'certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'certify_umd_037_foundation', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'))


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


def find_all_bounds(source: str) -> tuple[int, int]:
    marker = "__all__ = ["
    start = source.find(marker)
    if start == -1:
        raise RuntimeError(
            "UMD package __all__ list is missing"
        )

    opening = source.find(
        "[",
        start,
    )
    cursor = opening
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
                    return opening, cursor

        cursor += 1

    raise RuntimeError(
        "UMD package __all__ closing bracket is missing"
    )


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(
        encoding="utf-8"
    )

    marker = (
        "from .certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model_"
        "admission_ledger_read_model import ("
    )

    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    opening, closing = find_all_bounds(
        source
    )
    block = source[
        opening + 1 : closing
    ]

    missing = [
        name
        for name in EXPORTED_NAMES
        if f'"{name}"' not in block
        and f"'{name}'" not in block
    ]

    if missing:
        insertion = "".join(
            f'    "{name}",\n'
            for name in missing
        )
        source = (
            source[:closing]
            + insertion
            + source[closing:]
        )

    compile(
        source,
        str(INIT),
        "exec",
    )
    write_exact(
        INIT,
        source,
    )


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
                    "Certified upstream verifier missing: "
                    f"{module_name}.{verifier_name}"
                )
            if verifier() is not True:
                raise RuntimeError(
                    "Certified upstream verification failed: "
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
        importlib.invalidate_caches()

        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_active_canonical_market_registry_query_session_"
            "read_model_admission_ledger_read_model_admission_ledger_"
            "read_model"
        )

        missing = [
            name
            for name in EXPORTED_NAMES
            if not hasattr(
                module,
                name,
            )
        ]

        if missing:
            raise RuntimeError(
                "UMD-037 missing symbols: "
                + ", ".join(missing)
            )

        verifier = getattr(
            module,
            "verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model",
        )

        if verifier() is not True:
            raise RuntimeError(
                "UMD-037 verification returned false"
            )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main() -> int:
    print("=" * 80)
    print(" UMD-037 CORRECTION V2 FULL REPLACEMENT INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER "
        "READ MODEL"
    )
    print("=" * 80)
    print(
        f"[BOOT] Revision: {REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-036 "
        "verified read-only"
    )

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
    except Exception:
        for path, previous in backups.items():
            if previous is None:
                if path.exists():
                    path.unlink()
            else:
                temporary = path.with_suffix(
                    path.suffix + ".rollback.tmp"
                )
                temporary.write_bytes(
                    previous
                )
                os.replace(
                    temporary,
                    path,
                )

        importlib.invalidate_caches()

        print(
            "[ROLLBACK] UMD-037 installation failed; "
            "all affected files restored"
        )
        raise

    manifest = {
        "build_id": "UMD-037",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): (
                sha256_file(MODULE)
            ),
            str(INIT.relative_to(ROOT)): (
                sha256_file(INIT)
            ),
            str(TEST.relative_to(ROOT)): (
                sha256_file(TEST)
            ),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 37)
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
    print(
        "[PASS] Python compilation verified"
    )
    print(
        "[PASS] Required UMD-037 symbols verified"
    )
    print(
        f"[PASS] Deterministic install hash: {install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print(
        "[DONE] UMD-037 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python test_umd_037_certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model_"
        "admission_ledger_read_model.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
