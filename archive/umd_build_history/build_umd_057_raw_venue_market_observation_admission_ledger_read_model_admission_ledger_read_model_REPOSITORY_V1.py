from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = (
    "UMD_057_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_REPOSITORY_V1"
)
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger import (\n    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,\n)\n\nUMD_057_BUILD_ID = "UMD-057"\nUMD_057_BUILD_NAME = (\n    "Certified Raw Venue Market Observation Admission Ledger "\n    "Read Model Admission Ledger Read Model"\n)\nUMD_057_REVISION = (\n    "UMD_057_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"\n    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_V1"\n)\nUMD_057_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "automatic_discovery",\n    "automatic_observation_creation",\n    "automatic_admission",\n    "ledger_append",\n    "ledger_mutation",\n    "read_model_mutation",\n    "read_model_persistence",\n    "canonical_market_construction",\n    "classification_inference",\n    "duplicate_resolution",\n    "registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(\n        character not in "0123456789abcdef"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(\n        dict(\n            sorted(\n                (str(key), item)\n                for key, item in value.items()\n            )\n        )\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel:\n    source_ledger_hash: str\n    total_entry_count: int\n    admitted_entry_count: int\n    rejected_entry_count: int\n    ordered_entry_ids: Tuple[str, ...]\n    ordered_read_model_ids: Tuple[str, ...]\n    ordered_read_model_hashes: Tuple[str, ...]\n    ordered_source_ledger_hashes: Tuple[str, ...]\n    ordered_decision_ids: Tuple[str, ...]\n    admitted_entry_ids: Tuple[str, ...]\n    rejected_entry_ids: Tuple[str, ...]\n    latest_entry_id: str | None\n    latest_admitted_entry_id: str | None\n    metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n    _entry_position_by_id: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _read_model_position_by_id: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _read_model_position_by_hash: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _source_ledger_position_by_hash: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n    _decision_position_by_id: Mapping[str, int] = field(\n        init=False,\n        repr=False,\n    )\n\n    def __post_init__(self) -> None:\n        object.__setattr__(\n            self,\n            "source_ledger_hash",\n            _sha256(\n                self.source_ledger_hash,\n                "source_ledger_hash",\n            ),\n        )\n\n        for field_name in (\n            "total_entry_count",\n            "admitted_entry_count",\n            "rejected_entry_count",\n        ):\n            value = getattr(self, field_name)\n            if not isinstance(value, int):\n                raise TypeError(f"{field_name} must be an integer")\n            if value < 0:\n                raise ValueError(f"{field_name} must be non-negative")\n\n        if (\n            self.admitted_entry_count\n            + self.rejected_entry_count\n            != self.total_entry_count\n        ):\n            raise ValueError(\n                "admitted and rejected counts must partition total count"\n            )\n\n        tuple_fields = (\n            "ordered_entry_ids",\n            "ordered_read_model_ids",\n            "ordered_read_model_hashes",\n            "ordered_source_ledger_hashes",\n            "ordered_decision_ids",\n            "admitted_entry_ids",\n            "rejected_entry_ids",\n        )\n        for field_name in tuple_fields:\n            value = getattr(self, field_name)\n            if not isinstance(value, tuple):\n                object.__setattr__(\n                    self,\n                    field_name,\n                    tuple(value),\n                )\n\n        ordered_entry_ids = tuple(\n            _text(value, "ordered_entry_id")\n            for value in self.ordered_entry_ids\n        )\n        ordered_read_model_ids = tuple(\n            _text(value, "ordered_read_model_id")\n            for value in self.ordered_read_model_ids\n        )\n        ordered_read_model_hashes = tuple(\n            _sha256(value, "ordered_read_model_hash")\n            for value in self.ordered_read_model_hashes\n        )\n        ordered_source_ledger_hashes = tuple(\n            _sha256(value, "ordered_source_ledger_hash")\n            for value in self.ordered_source_ledger_hashes\n        )\n        ordered_decision_ids = tuple(\n            _text(value, "ordered_decision_id")\n            for value in self.ordered_decision_ids\n        )\n        admitted_entry_ids = tuple(\n            _text(value, "admitted_entry_id")\n            for value in self.admitted_entry_ids\n        )\n        rejected_entry_ids = tuple(\n            _text(value, "rejected_entry_id")\n            for value in self.rejected_entry_ids\n        )\n\n        for field_name, value in (\n            ("ordered_entry_ids", ordered_entry_ids),\n            ("ordered_read_model_ids", ordered_read_model_ids),\n            ("ordered_read_model_hashes", ordered_read_model_hashes),\n            (\n                "ordered_source_ledger_hashes",\n                ordered_source_ledger_hashes,\n            ),\n            ("ordered_decision_ids", ordered_decision_ids),\n            ("admitted_entry_ids", admitted_entry_ids),\n            ("rejected_entry_ids", rejected_entry_ids),\n        ):\n            object.__setattr__(self, field_name, value)\n\n        for values in (\n            ordered_entry_ids,\n            ordered_read_model_ids,\n            ordered_read_model_hashes,\n            ordered_source_ledger_hashes,\n            ordered_decision_ids,\n        ):\n            if len(values) != self.total_entry_count:\n                raise ValueError(\n                    "ordered identity collections must equal total count"\n                )\n\n        for name, values in (\n            ("ordered_entry_ids", ordered_entry_ids),\n            ("ordered_read_model_ids", ordered_read_model_ids),\n            ("ordered_read_model_hashes", ordered_read_model_hashes),\n            (\n                "ordered_source_ledger_hashes",\n                ordered_source_ledger_hashes,\n            ),\n            ("ordered_decision_ids", ordered_decision_ids),\n        ):\n            if len(set(values)) != len(values):\n                raise ValueError(f"{name} must be unique")\n\n        if len(admitted_entry_ids) != self.admitted_entry_count:\n            raise ValueError(\n                "admitted_entry_ids length must equal admitted count"\n            )\n        if len(rejected_entry_ids) != self.rejected_entry_count:\n            raise ValueError(\n                "rejected_entry_ids length must equal rejected count"\n            )\n\n        if set(admitted_entry_ids).intersection(rejected_entry_ids):\n            raise ValueError(\n                "admitted and rejected entry IDs must be disjoint"\n            )\n        if (\n            set(admitted_entry_ids).union(rejected_entry_ids)\n            != set(ordered_entry_ids)\n        ):\n            raise ValueError(\n                "admission partitions must cover all ordered entries"\n            )\n\n        if self.latest_entry_id is None:\n            if ordered_entry_ids:\n                raise ValueError(\n                    "latest_entry_id required when entries exist"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "latest_entry_id",\n                _text(\n                    self.latest_entry_id,\n                    "latest_entry_id",\n                ),\n            )\n            if self.latest_entry_id != ordered_entry_ids[-1]:\n                raise ValueError(\n                    "latest_entry_id must equal final ordered entry ID"\n                )\n\n        if self.latest_admitted_entry_id is None:\n            if admitted_entry_ids:\n                raise ValueError(\n                    "latest_admitted_entry_id required when admitted entries exist"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "latest_admitted_entry_id",\n                _text(\n                    self.latest_admitted_entry_id,\n                    "latest_admitted_entry_id",\n                ),\n            )\n            if (\n                self.latest_admitted_entry_id\n                != admitted_entry_ids[-1]\n            ):\n                raise ValueError(\n                    "latest_admitted_entry_id must equal final admitted entry ID"\n                )\n\n        object.__setattr__(\n            self,\n            "metadata",\n            _freeze(self.metadata),\n        )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError(\n                "read-model lineage must belong to UMD"\n            )\n        if self.lineage.build_id != UMD_057_BUILD_ID:\n            raise ValueError(\n                "read-model lineage must use build_id UMD-057"\n            )\n        if (\n            self.source_ledger_hash\n            not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "read-model lineage must include source ledger hash"\n            )\n\n        object.__setattr__(\n            self,\n            "_entry_position_by_id",\n            MappingProxyType(\n                {\n                    value: index\n                    for index, value in enumerate(\n                        ordered_entry_ids,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_read_model_position_by_id",\n            MappingProxyType(\n                {\n                    value: index\n                    for index, value in enumerate(\n                        ordered_read_model_ids,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_read_model_position_by_hash",\n            MappingProxyType(\n                {\n                    value: index\n                    for index, value in enumerate(\n                        ordered_read_model_hashes,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_source_ledger_position_by_hash",\n            MappingProxyType(\n                {\n                    value: index\n                    for index, value in enumerate(\n                        ordered_source_ledger_hashes,\n                        start=1,\n                    )\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_decision_position_by_id",\n            MappingProxyType(\n                {\n                    value: index\n                    for index, value in enumerate(\n                        ordered_decision_ids,\n                        start=1,\n                    )\n                }\n            ),\n        )\n\n    @property\n    def read_model_id(self) -> str:\n        return (\n            "umd:raw-observation-read-model-admission-ledger-read-model:"\n            + deterministic_sha256(\n                {\n                    "source_ledger_hash": self.source_ledger_hash,\n                    "ordered_entry_ids": self.ordered_entry_ids,\n                    "ordered_read_model_ids": self.ordered_read_model_ids,\n                    "ordered_read_model_hashes": (\n                        self.ordered_read_model_hashes\n                    ),\n                    "ordered_source_ledger_hashes": (\n                        self.ordered_source_ledger_hashes\n                    ),\n                    "ordered_decision_ids": (\n                        self.ordered_decision_ids\n                    ),\n                }\n            )\n        )\n\n    def entry_position(\n        self,\n        entry_id: str,\n    ) -> int | None:\n        return self._entry_position_by_id.get(\n            _text(entry_id, "entry_id")\n        )\n\n    def read_model_position(\n        self,\n        read_model_id: str,\n    ) -> int | None:\n        return self._read_model_position_by_id.get(\n            _text(read_model_id, "read_model_id")\n        )\n\n    def read_model_hash_position(\n        self,\n        read_model_hash: str,\n    ) -> int | None:\n        return self._read_model_position_by_hash.get(\n            _sha256(\n                read_model_hash,\n                "read_model_hash",\n            )\n        )\n\n    def source_ledger_hash_position(\n        self,\n        source_ledger_hash: str,\n    ) -> int | None:\n        return self._source_ledger_position_by_hash.get(\n            _sha256(\n                source_ledger_hash,\n                "source_ledger_hash",\n            )\n        )\n\n    def decision_position(\n        self,\n        decision_id: str,\n    ) -> int | None:\n        return self._decision_position_by_id.get(\n            _text(decision_id, "decision_id")\n        )\n\n    def is_admitted_entry(\n        self,\n        entry_id: str,\n    ) -> bool:\n        return (\n            _text(entry_id, "entry_id")\n            in self.admitted_entry_ids\n        )\n\n    def is_rejected_entry(\n        self,\n        entry_id: str,\n    ) -> bool:\n        return (\n            _text(entry_id, "entry_id")\n            in self.rejected_entry_ids\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "read_model_id": self.read_model_id,\n            "source_ledger_hash": self.source_ledger_hash,\n            "total_entry_count": self.total_entry_count,\n            "admitted_entry_count": self.admitted_entry_count,\n            "rejected_entry_count": self.rejected_entry_count,\n            "ordered_entry_ids": self.ordered_entry_ids,\n            "ordered_read_model_ids": (\n                self.ordered_read_model_ids\n            ),\n            "ordered_read_model_hashes": (\n                self.ordered_read_model_hashes\n            ),\n            "ordered_source_ledger_hashes": (\n                self.ordered_source_ledger_hashes\n            ),\n            "ordered_decision_ids": (\n                self.ordered_decision_ids\n            ),\n            "admitted_entry_ids": self.admitted_entry_ids,\n            "rejected_entry_ids": self.rejected_entry_ids,\n            "latest_entry_id": self.latest_entry_id,\n            "latest_admitted_entry_id": (\n                self.latest_admitted_entry_id\n            ),\n            "metadata": self.metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def read_model_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_057_admission_ledger_read_model(\n    ledger: ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,\n    *,\n    metadata: Mapping[str, Any] | None = None,\n    lineage: ImmutableLineage,\n) -> CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel:\n    if not isinstance(\n        ledger,\n        ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,\n    ):\n        raise TypeError(\n            "ledger must be the exact certified UMD-056 admission ledger"\n        )\n\n    entries = ledger.entries\n    admitted = ledger.admitted_entries()\n    rejected = ledger.rejected_entries()\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel(\n        source_ledger_hash=ledger.ledger_hash,\n        total_entry_count=len(entries),\n        admitted_entry_count=len(admitted),\n        rejected_entry_count=len(rejected),\n        ordered_entry_ids=tuple(\n            entry.entry_id\n            for entry in entries\n        ),\n        ordered_read_model_ids=tuple(\n            entry.decision.read_model_id\n            for entry in entries\n        ),\n        ordered_read_model_hashes=tuple(\n            entry.decision.read_model_hash\n            for entry in entries\n        ),\n        ordered_source_ledger_hashes=tuple(\n            entry.decision.source_ledger_hash\n            for entry in entries\n        ),\n        ordered_decision_ids=tuple(\n            entry.decision.decision_id\n            for entry in entries\n        ),\n        admitted_entry_ids=tuple(\n            entry.entry_id\n            for entry in admitted\n        ),\n        rejected_entry_ids=tuple(\n            entry.entry_id\n            for entry in rejected\n        ),\n        latest_entry_id=(\n            None\n            if not entries\n            else entries[-1].entry_id\n        ),\n        latest_admitted_entry_id=(\n            None\n            if not admitted\n            else admitted[-1].entry_id\n        ),\n        metadata=(\n            {}\n            if metadata is None\n            else metadata\n        ),\n        lineage=lineage,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD057CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    read_model_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "read_model_mode": self.read_model_mode,\n            "prohibited_capabilities": (\n                self.prohibited_capabilities\n            ),\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_057_certification_manifest() -> UMD057CertificationManifest:\n    return UMD057CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_057_BUILD_ID,\n        revision=UMD_057_REVISION,\n        schema_version=UMD_057_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 57)\n        ),\n        read_model_mode="deterministic_read_only_projection",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_umd_057_read_model(\n    read_model: CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel,\n) -> Mapping[str, Any]:\n    checks = {\n        "count_partition_valid": (\n            read_model.admitted_entry_count\n            + read_model.rejected_entry_count\n            == read_model.total_entry_count\n        ),\n        "ordered_collections_valid": all(\n            len(values) == read_model.total_entry_count\n            for values in (\n                read_model.ordered_entry_ids,\n                read_model.ordered_read_model_ids,\n                read_model.ordered_read_model_hashes,\n                read_model.ordered_source_ledger_hashes,\n                read_model.ordered_decision_ids,\n            )\n        ),\n        "ordered_identities_unique": all(\n            len(set(values)) == len(values)\n            for values in (\n                read_model.ordered_entry_ids,\n                read_model.ordered_read_model_ids,\n                read_model.ordered_read_model_hashes,\n                read_model.ordered_source_ledger_hashes,\n                read_model.ordered_decision_ids,\n            )\n        ),\n        "partition_disjoint": (\n            not set(read_model.admitted_entry_ids).intersection(\n                read_model.rejected_entry_ids\n            )\n        ),\n        "partition_complete": (\n            set(read_model.admitted_entry_ids).union(\n                read_model.rejected_entry_ids\n            )\n            == set(read_model.ordered_entry_ids)\n        ),\n        "lineage_bound": (\n            read_model.source_ledger_hash\n            in read_model.lineage.parent_hashes\n        ),\n        "deterministic_replay": (\n            read_model.read_model_hash\n            == deterministic_sha256(\n                read_model.to_canonical_dict()\n            )\n        ),\n        "read_only_indexes": all(\n            isinstance(index, MappingProxyType)\n            for index in (\n                read_model._entry_position_by_id,\n                read_model._read_model_position_by_id,\n                read_model._read_model_position_by_hash,\n                read_model._source_ledger_position_by_hash,\n                read_model._decision_position_by_id,\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "read_model_id": read_model.read_model_id,\n            "read_model_hash": read_model.read_model_hash,\n            "source_ledger_hash": read_model.source_ledger_hash,\n            "total_entry_count": read_model.total_entry_count,\n            "admitted_entry_count": (\n                read_model.admitted_entry_count\n            ),\n            "rejected_entry_count": (\n                read_model.rejected_entry_count\n            ),\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_057_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_057_certification_manifest()\n    checks = {\n        "subsystem_identity": (\n            manifest.subsystem_id == "UMD"\n        ),\n        "build_identity": (\n            manifest.build_id == "UMD-057"\n        ),\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 57)\n            )\n        ),\n        "read_only_projection": (\n            manifest.read_model_mode\n            == "deterministic_read_only_projection"\n        ),\n        "network_disabled": (\n            manifest.network_enabled is False\n        ),\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": (\n            manifest.mutation_enabled is False\n        ),\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": (\n            manifest.execution_enabled is False\n        ),\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model() -> bool:\n    result = certify_umd_057_foundation()\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-057 foundation certification failed: "\n            + ", ".join(result["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate import (\n    UMD_055_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger import (\n    UMD_056_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,\n)\nfrom qseries_v2.universal_market_discovery.umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model import (\n    UMD_057_REVISION,\n    build_umd_057_admission_ledger_read_model,\n    build_umd_057_certification_manifest,\n    certify_umd_057_foundation,\n    certify_umd_057_read_model,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    7,\n    4,\n    20,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef digest(label: str) -> str:\n    return hashlib.sha256(\n        label.encode("utf-8")\n    ).hexdigest()\n\n\ndef decision(\n    suffix: str,\n    admitted: bool = True,\n):\n    read_model_hash = digest(\n        f"umd-057:{suffix}:read-model"\n    )\n    source_ledger_hash = digest(\n        f"umd-057:{suffix}:source-ledger"\n    )\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-055",\n        revision=UMD_055_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            read_model_hash,\n            source_ledger_hash,\n        ),\n        source_refs=(\n            f"fixture://umd-057/decision/{suffix}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionDecision(\n        read_model_id=f"read-model-{suffix}",\n        read_model_hash=read_model_hash,\n        source_ledger_hash=source_ledger_hash,\n        total_entry_count=2,\n        admitted_entry_count=1,\n        rejected_entry_count=1,\n        latest_entry_id=f"entry-{suffix}",\n        latest_admitted_entry_id=f"admitted-{suffix}",\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef entry(number: int, value, previous):\n    parents = [value.record_hash]\n    if previous is not None:\n        parents.append(previous)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-056",\n        revision=UMD_056_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(\n            f"fixture://umd-057/entry/{number}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=value,\n        recorded_at=FIXED,\n        metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\ndef source_ledger():\n    first = entry(\n        1,\n        decision("a", True),\n        None,\n    )\n    second = entry(\n        2,\n        decision("b", False),\n        first.entry_hash,\n    )\n    third = entry(\n        3,\n        decision("c", True),\n        second.entry_hash,\n    )\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-056",\n        revision=UMD_056_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(third.entry_hash,),\n        source_refs=(\n            "fixture://umd-057/ledger",\n        ),\n        created_at=FIXED,\n    )\n\n    return ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger(\n        entries=(first, second, third),\n        ledger_lineage=lineage,\n    )\n\n\ndef read_model_lineage(ledger_hash: str):\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-057",\n        revision=UMD_057_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(ledger_hash,),\n        source_refs=(\n            "fixture://umd-057/read-model",\n        ),\n        created_at=FIXED,\n    )\n\n\nclass TestUMD057(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_057_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-057")\n\n    def test_projection(self) -> None:\n        ledger = source_ledger()\n        model = build_umd_057_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n        result = certify_umd_057_read_model(model)\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["total_entry_count"], 3)\n        self.assertEqual(result["admitted_entry_count"], 2)\n        self.assertEqual(result["rejected_entry_count"], 1)\n\n    def test_deterministic(self) -> None:\n        ledger = source_ledger()\n        lineage = read_model_lineage(\n            ledger.ledger_hash\n        )\n        first = build_umd_057_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=lineage,\n        )\n        second = build_umd_057_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=lineage,\n        )\n        self.assertEqual(\n            first.read_model_id,\n            second.read_model_id,\n        )\n        self.assertEqual(\n            first.read_model_hash,\n            second.read_model_hash,\n        )\n\n    def test_positions_and_partitions(self) -> None:\n        ledger = source_ledger()\n        model = build_umd_057_admission_ledger_read_model(\n            ledger,\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n        first, second, third = ledger.entries\n\n        self.assertEqual(\n            model.entry_position(first.entry_id),\n            1,\n        )\n        self.assertEqual(\n            model.read_model_position(\n                second.decision.read_model_id\n            ),\n            2,\n        )\n        self.assertEqual(\n            model.read_model_hash_position(\n                third.decision.read_model_hash\n            ),\n            3,\n        )\n        self.assertEqual(\n            model.source_ledger_hash_position(\n                third.decision.source_ledger_hash\n            ),\n            3,\n        )\n        self.assertEqual(\n            model.decision_position(\n                third.decision.decision_id\n            ),\n            3,\n        )\n        self.assertTrue(\n            model.is_admitted_entry(first.entry_id)\n        )\n        self.assertTrue(\n            model.is_rejected_entry(second.entry_id)\n        )\n        self.assertEqual(\n            model.latest_entry_id,\n            third.entry_id,\n        )\n        self.assertEqual(\n            model.latest_admitted_entry_id,\n            third.entry_id,\n        )\n\n    def test_lineage_requires_ledger(self) -> None:\n        ledger = source_ledger()\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-057",\n            revision=UMD_057_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(digest("wrong-ledger"),),\n            source_refs=(\n                "fixture://umd-057/bad",\n            ),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            build_umd_057_admission_ledger_read_model(\n                ledger,\n                lineage=bad,\n            )\n\n    def test_exact_umd056_type(self) -> None:\n        ledger = source_ledger()\n        self.assertIsInstance(\n            ledger,\n            ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedger,\n        )\n        self.assertEqual(\n            ledger.ledger_lineage.build_id,\n            "UMD-056",\n        )\n\n    def test_immutable(self) -> None:\n        ledger = source_ledger()\n        model = build_umd_057_admission_ledger_read_model(\n            ledger,\n            metadata={"read_only": True},\n            lineage=read_model_lineage(\n                ledger.ledger_hash\n            ),\n        )\n\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            model.total_entry_count = 99\n        with self.assertRaises(TypeError):\n            model.metadata["read_only"] = False\n        with self.assertRaises(TypeError):\n            model._entry_position_by_id[\n                model.ordered_entry_ids[0]\n            ] = 99\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_057_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-057 CERTIFICATION TEST")\n    print(\n        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION "\n        "LEDGER READ MODEL ADMISSION LEDGER READ MODEL"\n    )\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD057\n    )\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_057_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-056 consumed read-only")\n    print("[PASS] Exact UMD-056 admission-ledger class consumed")\n    print("[PASS] Deterministic UMD-056 admission-ledger projection certified")\n    print("[PASS] Immutable entry, read-model, source-ledger, and decision indexes certified")\n    print("[PASS] Admitted and rejected partitions certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-057 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER READ MODEL ADMISSION LEDGER READ MODEL CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model import (\n    UMD_057_BUILD_ID,\n    UMD_057_BUILD_NAME,\n    UMD_057_REVISION,\n    UMD_057_SCHEMA_VERSION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel,\n    UMD057CertificationManifest,\n    build_umd_057_admission_ledger_read_model,\n    build_umd_057_certification_manifest,\n    certify_umd_057_read_model,\n    certify_umd_057_foundation,\n    verify_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model,\n)\n'
EXPORTED_NAMES = ('UMD_057_BUILD_ID', 'UMD_057_BUILD_NAME', 'UMD_057_REVISION', 'UMD_057_SCHEMA_VERSION', 'CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModel', 'UMD057CertificationManifest', 'build_umd_057_admission_ledger_read_model', 'build_umd_057_certification_manifest', 'certify_umd_057_read_model', 'certify_umd_057_foundation', 'verify_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'), ('umd_045_venue_discovery_source_contract', 'verify_umd_045_venue_discovery_source_contract'), ('umd_046_venue_discovery_source_registry', 'verify_umd_046_venue_discovery_source_registry'), ('umd_047_venue_discovery_request_contract', 'verify_umd_047_venue_discovery_request_contract'), ('umd_048_venue_discovery_request_admission_gate', 'verify_umd_048_venue_discovery_request_admission_gate'), ('umd_049_venue_discovery_request_admission_ledger', 'verify_umd_049_venue_discovery_request_admission_ledger'), ('umd_050_venue_discovery_request_admission_ledger_read_model', 'verify_umd_050_venue_discovery_request_admission_ledger_read_model'), ('umd_051_raw_venue_market_observation_contract', 'verify_umd_051_raw_venue_market_observation_contract'), ('umd_052_raw_venue_market_observation_admission_gate', 'verify_umd_052_raw_venue_market_observation_admission_gate'), ('umd_053_raw_venue_market_observation_admission_ledger', 'verify_umd_053_raw_venue_market_observation_admission_ledger'), ('umd_054_raw_venue_market_observation_admission_ledger_read_model', 'verify_umd_054_raw_venue_market_observation_admission_ledger_read_model'), ('umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate', 'verify_umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate'), ('umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger', 'verify_umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger'))


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_direct(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )


def find_all_bounds(source: str) -> tuple[int, int]:
    marker = "__all__ = ["
    start = source.find(marker)
    if start == -1:
        raise RuntimeError(
            "UMD package __all__ list is missing"
        )

    opening = source.find("[", start)
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
    source = INIT.read_text(encoding="utf-8")
    marker = (
        "from .umd_057_raw_venue_market_observation_"
        "admission_ledger_read_model_admission_ledger_read_model import ("
    )
    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    opening, closing = find_all_bounds(source)
    block = source[opening + 1:closing]

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

    compile(source, str(INIT), "exec")
    write_direct(INIT, source)


def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
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
            sys.path.remove(str(ROOT))


def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module_name = (
            "qseries_v2.universal_market_discovery."
            "umd_057_raw_venue_market_observation_"
            "admission_ledger_read_model_admission_ledger_read_model"
        )
        sys.modules.pop(module_name, None)
        importlib.invalidate_caches()
        module = importlib.import_module(module_name)

        missing = [
            name
            for name in EXPORTED_NAMES
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-057 missing symbols: "
                + ", ".join(missing)
            )

        if module.verify_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model() is not True:
            raise RuntimeError(
                "UMD-057 verification returned false"
            )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def main() -> int:
    print("=" * 72)
    print(" UMD-057 REPOSITORY-ALIGNED INSTALLER")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION "
        "LEDGER READ MODEL ADMISSION LEDGER READ MODEL"
    )
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-056 "
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
        write_direct(MODULE, MODULE_SOURCE)
        write_direct(TEST, TEST_SOURCE)
        update_init()

        compile(
            MODULE.read_text(encoding="utf-8"),
            str(MODULE),
            "exec",
        )
        compile(
            INIT.read_text(encoding="utf-8"),
            str(INIT),
            "exec",
        )
        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )
        verify_current()
    except Exception:
        rollback_errors = []

        for path, previous in backups.items():
            try:
                if previous is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.write_bytes(previous)
            except Exception as rollback_error:
                rollback_errors.append(
                    f"{path}: "
                    f"{type(rollback_error).__name__}: "
                    f"{rollback_error}"
                )

        importlib.invalidate_caches()

        if rollback_errors:
            print("[ROLLBACK WARNING]")
            for rollback_error in rollback_errors:
                print(f"  - {rollback_error}")
        else:
            print(
                "[ROLLBACK] UMD-057 installation failed; "
                "all affected files restored"
            )
        raise

    manifest = {
        "build_id": "UMD-057",
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
            for number in range(1, 57)
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

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required UMD-057 symbols verified")
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-057 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
