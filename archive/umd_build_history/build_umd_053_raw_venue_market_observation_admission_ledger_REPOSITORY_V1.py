from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = (
    "UMD_053_CERTIFIED_RAW_VENUE_MARKET_"
    "OBSERVATION_ADMISSION_LEDGER_REPOSITORY_V1"
)
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_053_raw_venue_market_observation_admission_ledger.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_053_raw_venue_market_observation_admission_ledger.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom datetime import datetime, timezone\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_052_raw_venue_market_observation_admission_gate import (\n    CertifiedRawVenueMarketObservationAdmissionDecision,\n)\n\nUMD_053_BUILD_ID = "UMD-053"\nUMD_053_BUILD_NAME = (\n    "Certified Raw Venue Market Observation Admission Ledger"\n)\nUMD_053_REVISION = (\n    "UMD_053_CERTIFIED_RAW_VENUE_MARKET_"\n    "OBSERVATION_ADMISSION_LEDGER_V1"\n)\nUMD_053_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "automatic_discovery",\n    "automatic_observation_creation",\n    "automatic_admission",\n    "automatic_append",\n    "ledger_mutation",\n    "record_deletion",\n    "record_reordering",\n    "observation_persistence",\n    "registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(\n        character not in "0123456789abcdef"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _utc(value: datetime, field_name: str) -> datetime:\n    if not isinstance(value, datetime):\n        raise TypeError(f"{field_name} must be a datetime")\n    if value.tzinfo is None:\n        raise ValueError(f"{field_name} must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(\n        dict(\n            sorted(\n                (str(key), item)\n                for key, item in value.items()\n            )\n        )\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedRawVenueMarketObservationAdmissionLedgerEntry:\n    sequence_number: int\n    previous_entry_hash: str | None\n    decision: CertifiedRawVenueMarketObservationAdmissionDecision\n    recorded_at: datetime\n    metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.sequence_number, int):\n            raise TypeError("sequence_number must be an integer")\n        if self.sequence_number < 1:\n            raise ValueError("sequence_number must be positive")\n\n        if self.previous_entry_hash is None:\n            if self.sequence_number != 1:\n                raise ValueError(\n                    "only the first entry may omit previous_entry_hash"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "previous_entry_hash",\n                _sha256(\n                    self.previous_entry_hash,\n                    "previous_entry_hash",\n                ),\n            )\n\n        if not isinstance(\n            self.decision,\n            CertifiedRawVenueMarketObservationAdmissionDecision,\n        ):\n            raise TypeError(\n                "decision must be a certified UMD-052 admission decision"\n            )\n\n        object.__setattr__(\n            self,\n            "recorded_at",\n            _utc(self.recorded_at, "recorded_at"),\n        )\n        object.__setattr__(\n            self,\n            "metadata",\n            _freeze(self.metadata),\n        )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("entry lineage must belong to UMD")\n        if self.lineage.build_id != UMD_053_BUILD_ID:\n            raise ValueError(\n                "entry lineage must use build_id UMD-053"\n            )\n        if self.decision.record_hash not in self.lineage.parent_hashes:\n            raise ValueError(\n                "entry lineage must include UMD-052 decision record hash"\n            )\n        if (\n            self.previous_entry_hash is not None\n            and self.previous_entry_hash not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "entry lineage must include previous_entry_hash"\n            )\n\n    @property\n    def entry_id(self) -> str:\n        return (\n            "umd:raw-venue-market-observation-admission-ledger-entry:"\n            + deterministic_sha256(\n                {\n                    "sequence_number": self.sequence_number,\n                    "previous_entry_hash": self.previous_entry_hash,\n                    "decision_id": self.decision.decision_id,\n                    "decision_record_hash": self.decision.record_hash,\n                }\n            )\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "entry_id": self.entry_id,\n            "sequence_number": self.sequence_number,\n            "previous_entry_hash": self.previous_entry_hash,\n            "decision": self.decision,\n            "recorded_at": self.recorded_at,\n            "metadata": self.metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def entry_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\n@dataclass(frozen=True, slots=True)\nclass ReadOnlyRawVenueMarketObservationAdmissionLedger:\n    entries: Tuple[\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n        ...,\n    ]\n    ledger_lineage: ImmutableLineage\n    _by_entry_id: Mapping[\n        str,\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _by_observation_id: Mapping[\n        str,\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _by_observation_hash: Mapping[\n        str,\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _by_decision_id: Mapping[\n        str,\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _entry_ids_by_source_id: Mapping[\n        str,\n        Tuple[str, ...],\n    ] = field(init=False, repr=False)\n    _entry_ids_by_venue_market_id: Mapping[\n        str,\n        Tuple[str, ...],\n    ] = field(init=False, repr=False)\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.entries, tuple):\n            object.__setattr__(\n                self,\n                "entries",\n                tuple(self.entries),\n            )\n\n        ordered = tuple(\n            sorted(\n                self.entries,\n                key=lambda entry: entry.sequence_number,\n            )\n        )\n        object.__setattr__(self, "entries", ordered)\n\n        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("ledger lineage must belong to UMD")\n        if self.ledger_lineage.build_id != UMD_053_BUILD_ID:\n            raise ValueError(\n                "ledger lineage must use build_id UMD-053"\n            )\n\n        by_entry_id = {}\n        by_observation_id = {}\n        by_observation_hash = {}\n        by_decision_id = {}\n        entry_ids_by_source_id = {}\n        entry_ids_by_venue_market_id = {}\n        previous = None\n\n        for expected_sequence, entry in enumerate(\n            ordered,\n            start=1,\n        ):\n            if not isinstance(\n                entry,\n                CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n            ):\n                raise TypeError(\n                    "entries must contain certified UMD-053 entries"\n                )\n            if entry.sequence_number != expected_sequence:\n                raise ValueError(\n                    "sequence must be contiguous and begin at 1"\n                )\n\n            if previous is None:\n                if entry.previous_entry_hash is not None:\n                    raise ValueError(\n                        "first entry must not have previous_entry_hash"\n                    )\n            elif entry.previous_entry_hash != previous.entry_hash:\n                raise ValueError(\n                    "previous-entry hash chain mismatch"\n                )\n\n            if entry.entry_id in by_entry_id:\n                raise ValueError("duplicate ledger entry ID")\n            if entry.decision.observation_id in by_observation_id:\n                raise ValueError("duplicate observation ID replay")\n            if entry.decision.observation_hash in by_observation_hash:\n                raise ValueError("duplicate observation hash replay")\n            if entry.decision.decision_id in by_decision_id:\n                raise ValueError("duplicate decision replay")\n\n            by_entry_id[entry.entry_id] = entry\n            by_observation_id[\n                entry.decision.observation_id\n            ] = entry\n            by_observation_hash[\n                entry.decision.observation_hash\n            ] = entry\n            by_decision_id[\n                entry.decision.decision_id\n            ] = entry\n            entry_ids_by_source_id.setdefault(\n                entry.decision.source_id,\n                [],\n            ).append(entry.entry_id)\n            entry_ids_by_venue_market_id.setdefault(\n                entry.decision.venue_market_id,\n                [],\n            ).append(entry.entry_id)\n            previous = entry\n\n        if (\n            ordered\n            and ordered[-1].entry_hash\n            not in self.ledger_lineage.parent_hashes\n        ):\n            raise ValueError(\n                "ledger lineage must include latest entry hash"\n            )\n\n        object.__setattr__(\n            self,\n            "_by_entry_id",\n            MappingProxyType(by_entry_id),\n        )\n        object.__setattr__(\n            self,\n            "_by_observation_id",\n            MappingProxyType(by_observation_id),\n        )\n        object.__setattr__(\n            self,\n            "_by_observation_hash",\n            MappingProxyType(by_observation_hash),\n        )\n        object.__setattr__(\n            self,\n            "_by_decision_id",\n            MappingProxyType(by_decision_id),\n        )\n        object.__setattr__(\n            self,\n            "_entry_ids_by_source_id",\n            MappingProxyType(\n                {\n                    source_id: tuple(entry_ids)\n                    for source_id, entry_ids\n                    in entry_ids_by_source_id.items()\n                }\n            ),\n        )\n        object.__setattr__(\n            self,\n            "_entry_ids_by_venue_market_id",\n            MappingProxyType(\n                {\n                    venue_market_id: tuple(entry_ids)\n                    for venue_market_id, entry_ids\n                    in entry_ids_by_venue_market_id.items()\n                }\n            ),\n        )\n\n    def get(\n        self,\n        entry_id: str,\n    ) -> CertifiedRawVenueMarketObservationAdmissionLedgerEntry | None:\n        return self._by_entry_id.get(\n            _text(entry_id, "entry_id")\n        )\n\n    def get_by_observation_id(\n        self,\n        observation_id: str,\n    ) -> CertifiedRawVenueMarketObservationAdmissionLedgerEntry | None:\n        return self._by_observation_id.get(\n            _text(observation_id, "observation_id")\n        )\n\n    def get_by_observation_hash(\n        self,\n        observation_hash: str,\n    ) -> CertifiedRawVenueMarketObservationAdmissionLedgerEntry | None:\n        return self._by_observation_hash.get(\n            _sha256(\n                observation_hash,\n                "observation_hash",\n            )\n        )\n\n    def get_by_decision_id(\n        self,\n        decision_id: str,\n    ) -> CertifiedRawVenueMarketObservationAdmissionLedgerEntry | None:\n        return self._by_decision_id.get(\n            _text(decision_id, "decision_id")\n        )\n\n    def list_by_source_id(\n        self,\n        source_id: str,\n    ) -> Tuple[\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n        ...,\n    ]:\n        normalized = _text(source_id, "source_id")\n        entry_ids = self._entry_ids_by_source_id.get(\n            normalized,\n            (),\n        )\n        return tuple(\n            self._by_entry_id[entry_id]\n            for entry_id in entry_ids\n        )\n\n    def list_by_venue_market_id(\n        self,\n        venue_market_id: str,\n    ) -> Tuple[\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n        ...,\n    ]:\n        normalized = _text(\n            venue_market_id,\n            "venue_market_id",\n        )\n        entry_ids = self._entry_ids_by_venue_market_id.get(\n            normalized,\n            (),\n        )\n        return tuple(\n            self._by_entry_id[entry_id]\n            for entry_id in entry_ids\n        )\n\n    def admitted_entries(\n        self,\n    ) -> Tuple[\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n        ...,\n    ]:\n        return tuple(\n            entry\n            for entry in self.entries\n            if entry.decision.admitted\n        )\n\n    def rejected_entries(\n        self,\n    ) -> Tuple[\n        CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n        ...,\n    ]:\n        return tuple(\n            entry\n            for entry in self.entries\n            if not entry.decision.admitted\n        )\n\n    def latest_admitted(\n        self,\n    ) -> CertifiedRawVenueMarketObservationAdmissionLedgerEntry | None:\n        admitted = self.admitted_entries()\n        return None if not admitted else admitted[-1]\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "ledger_mode": "append_only_read_only",\n            "entries": self.entries,\n            "ledger_lineage": self.ledger_lineage,\n        }\n\n    @property\n    def ledger_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD053CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    ledger_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "ledger_mode": self.ledger_mode,\n            "prohibited_capabilities": self.prohibited_capabilities,\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_053_certification_manifest() -> UMD053CertificationManifest:\n    return UMD053CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_053_BUILD_ID,\n        revision=UMD_053_REVISION,\n        schema_version=UMD_053_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 53)\n        ),\n        ledger_mode="append_only_read_only",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_raw_venue_market_observation_admission_ledger(\n    ledger: ReadOnlyRawVenueMarketObservationAdmissionLedger,\n) -> Mapping[str, Any]:\n    if not isinstance(\n        ledger,\n        ReadOnlyRawVenueMarketObservationAdmissionLedger,\n    ):\n        raise TypeError(\n            "ledger must be a certified UMD-053 ledger"\n        )\n\n    admitted = ledger.admitted_entries()\n    rejected = ledger.rejected_entries()\n    checks = {\n        "sequence_contiguous": (\n            tuple(\n                entry.sequence_number\n                for entry in ledger.entries\n            )\n            == tuple(\n                range(1, len(ledger.entries) + 1)\n            )\n        ),\n        "previous_hash_chain_valid": all(\n            entry.previous_entry_hash\n            == ledger.entries[index - 1].entry_hash\n            for index, entry in enumerate(ledger.entries)\n            if index > 0\n        ),\n        "entry_ids_unique": (\n            len({entry.entry_id for entry in ledger.entries})\n            == len(ledger.entries)\n        ),\n        "observation_ids_unique": (\n            len(\n                {\n                    entry.decision.observation_id\n                    for entry in ledger.entries\n                }\n            )\n            == len(ledger.entries)\n        ),\n        "observation_hashes_unique": (\n            len(\n                {\n                    entry.decision.observation_hash\n                    for entry in ledger.entries\n                }\n            )\n            == len(ledger.entries)\n        ),\n        "decision_ids_unique": (\n            len(\n                {\n                    entry.decision.decision_id\n                    for entry in ledger.entries\n                }\n            )\n            == len(ledger.entries)\n        ),\n        "partition_complete": (\n            len(admitted)\n            + len(rejected)\n            == len(ledger.entries)\n        ),\n        "latest_lineage_bound": (\n            not ledger.entries\n            or ledger.entries[-1].entry_hash\n            in ledger.ledger_lineage.parent_hashes\n        ),\n        "deterministic_replay": (\n            ledger.ledger_hash\n            == deterministic_sha256(\n                ledger.to_canonical_dict()\n            )\n        ),\n        "read_only_indexes": all(\n            isinstance(index, MappingProxyType)\n            for index in (\n                ledger._by_entry_id,\n                ledger._by_observation_id,\n                ledger._by_observation_hash,\n                ledger._by_decision_id,\n                ledger._entry_ids_by_source_id,\n                ledger._entry_ids_by_venue_market_id,\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "ledger_hash": ledger.ledger_hash,\n            "entry_count": len(ledger.entries),\n            "admitted_count": len(admitted),\n            "rejected_count": len(rejected),\n            "source_count": len(\n                ledger._entry_ids_by_source_id\n            ),\n            "venue_market_count": len(\n                ledger._entry_ids_by_venue_market_id\n            ),\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_053_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_053_certification_manifest()\n    checks = {\n        "subsystem_identity": (\n            manifest.subsystem_id == "UMD"\n        ),\n        "build_identity": (\n            manifest.build_id == "UMD-053"\n        ),\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 53)\n            )\n        ),\n        "append_only_read_only": (\n            manifest.ledger_mode\n            == "append_only_read_only"\n        ),\n        "network_disabled": (\n            manifest.network_enabled is False\n        ),\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": (\n            manifest.mutation_enabled is False\n        ),\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": (\n            manifest.execution_enabled is False\n        ),\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_053_raw_venue_market_observation_admission_ledger() -> bool:\n    result = certify_umd_053_foundation()\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-053 foundation certification failed: "\n            + ", ".join(result["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_052_raw_venue_market_observation_admission_gate import (\n    UMD_052_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.umd_053_raw_venue_market_observation_admission_ledger import (\n    UMD_053_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ReadOnlyRawVenueMarketObservationAdmissionLedger,\n    build_umd_053_certification_manifest,\n    certify_raw_venue_market_observation_admission_ledger,\n    certify_umd_053_foundation,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    7,\n    2,\n    35,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef digest(label: str) -> str:\n    return hashlib.sha256(\n        label.encode("utf-8")\n    ).hexdigest()\n\n\ndef decision(\n    suffix: str,\n    admitted: bool = True,\n    source_id: str = "SOURCE-A",\n    venue_market_id: str = "MARKET-A",\n):\n    observation_hash = digest(\n        f"umd-053:{suffix}:observation"\n    )\n    request_hash = digest(\n        f"umd-053:{suffix}:request"\n    )\n    request_decision_hash = digest(\n        f"umd-053:{suffix}:request-decision"\n    )\n    source_contract_hash = digest(\n        f"umd-053:{suffix}:source-contract"\n    )\n    source_registry_hash = digest(\n        f"umd-053:{suffix}:source-registry"\n    )\n    raw_payload_hash = digest(\n        f"umd-053:{suffix}:raw-payload"\n    )\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-052",\n        revision=UMD_052_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            observation_hash,\n            request_hash,\n            request_decision_hash,\n            source_contract_hash,\n            source_registry_hash,\n            raw_payload_hash,\n        ),\n        source_refs=(\n            f"fixture://umd-053/decision/{suffix}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionDecision(\n        observation_id=f"observation-{suffix}",\n        observation_hash=observation_hash,\n        request_id=f"request-{suffix}",\n        request_hash=request_hash,\n        admission_decision_id=f"request-decision-{suffix}",\n        admission_decision_record_hash=request_decision_hash,\n        source_id=source_id,\n        source_contract_hash=source_contract_hash,\n        source_registry_hash=source_registry_hash,\n        raw_payload_hash=raw_payload_hash,\n        canonical_venue_id="KALSHI",\n        adapter_key="KALSHI_MARKET_CATALOG",\n        venue_market_id=venue_market_id,\n        retrieval_sequence=1,\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef entry(number: int, value, previous: str | None):\n    parents = [value.record_hash]\n    if previous is not None:\n        parents.append(previous)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-053",\n        revision=UMD_053_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(\n            f"fixture://umd-053/entry/{number}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=value,\n        recorded_at=FIXED,\n        metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\ndef ledger(entries):\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-053",\n        revision=UMD_053_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            ()\n            if not entries\n            else (entries[-1].entry_hash,)\n        ),\n        source_refs=(\n            "fixture://umd-053/ledger",\n        ),\n        created_at=FIXED,\n    )\n    return ReadOnlyRawVenueMarketObservationAdmissionLedger(\n        entries=tuple(entries),\n        ledger_lineage=lineage,\n    )\n\n\nclass TestUMD053(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_053_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-053")\n\n    def test_ledger_certifies(self) -> None:\n        first = entry(\n            1,\n            decision("a", True, "SOURCE-A", "MARKET-A"),\n            None,\n        )\n        second = entry(\n            2,\n            decision("b", False, "SOURCE-B", "MARKET-B"),\n            first.entry_hash,\n        )\n        item = ledger((first, second))\n        result = (\n            certify_raw_venue_market_observation_admission_ledger(\n                item\n            )\n        )\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["entry_count"], 2)\n        self.assertEqual(result["admitted_count"], 1)\n        self.assertEqual(result["rejected_count"], 1)\n        self.assertEqual(result["source_count"], 2)\n        self.assertEqual(result["venue_market_count"], 2)\n\n    def test_deterministic(self) -> None:\n        value = decision("a")\n        first = entry(1, value, None)\n        second = entry(1, value, None)\n        self.assertEqual(first.entry_id, second.entry_id)\n        self.assertEqual(first.entry_hash, second.entry_hash)\n\n    def test_sequence_gap_rejected(self) -> None:\n        first = entry(1, decision("a"), None)\n        second = entry(\n            3,\n            decision("b"),\n            first.entry_hash,\n        )\n        with self.assertRaises(ValueError):\n            ledger((first, second))\n\n    def test_hash_chain_rejected(self) -> None:\n        first = entry(1, decision("a"), None)\n        second = entry(\n            2,\n            decision("b"),\n            digest("wrong"),\n        )\n        with self.assertRaises(ValueError):\n            ledger((first, second))\n\n    def test_duplicate_observation_rejected(self) -> None:\n        value = decision("a")\n        first = entry(1, value, None)\n        second = entry(\n            2,\n            value,\n            first.entry_hash,\n        )\n        with self.assertRaises(ValueError):\n            ledger((first, second))\n\n    def test_lookup_indexes(self) -> None:\n        first = entry(\n            1,\n            decision(\n                "a",\n                True,\n                "SOURCE-A",\n                "MARKET-A",\n            ),\n            None,\n        )\n        second = entry(\n            2,\n            decision(\n                "b",\n                False,\n                "SOURCE-A",\n                "MARKET-A",\n            ),\n            first.entry_hash,\n        )\n        item = ledger((first, second))\n\n        self.assertIs(item.get(first.entry_id), first)\n        self.assertIs(\n            item.get_by_observation_id(\n                first.decision.observation_id\n            ),\n            first,\n        )\n        self.assertIs(\n            item.get_by_observation_hash(\n                first.decision.observation_hash\n            ),\n            first,\n        )\n        self.assertIs(\n            item.get_by_decision_id(\n                first.decision.decision_id\n            ),\n            first,\n        )\n        self.assertEqual(\n            item.list_by_source_id("SOURCE-A"),\n            (first, second),\n        )\n        self.assertEqual(\n            item.list_by_venue_market_id("MARKET-A"),\n            (first, second),\n        )\n        self.assertIs(item.latest_admitted(), first)\n\n    def test_lineage_requires_latest_hash(self) -> None:\n        first = entry(1, decision("a"), None)\n        bad_lineage = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-053",\n            revision=UMD_053_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(),\n            source_refs=(\n                "fixture://umd-053/bad-ledger",\n            ),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            ReadOnlyRawVenueMarketObservationAdmissionLedger(\n                entries=(first,),\n                ledger_lineage=bad_lineage,\n            )\n\n    def test_immutable(self) -> None:\n        first = entry(1, decision("a"), None)\n        item = ledger((first,))\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            first.sequence_number = 2\n        with self.assertRaises(TypeError):\n            first.metadata["read_only"] = False\n        with self.assertRaises(TypeError):\n            item._by_observation_id["changed"] = first\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_053_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-053 CERTIFICATION TEST")\n    print(\n        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER"\n    )\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD053\n    )\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_053_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-052 consumed read-only")\n    print("[PASS] Exact UMD-052 observation-admission decision consumed")\n    print("[PASS] Append-only sequence and previous-entry hash chain certified")\n    print("[PASS] Duplicate observation and decision replay rejected")\n    print("[PASS] Immutable observation, source, and venue-market indexes certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-053 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_053_raw_venue_market_observation_admission_ledger import (\n    UMD_053_BUILD_ID,\n    UMD_053_BUILD_NAME,\n    UMD_053_REVISION,\n    UMD_053_SCHEMA_VERSION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerEntry,\n    ReadOnlyRawVenueMarketObservationAdmissionLedger,\n    UMD053CertificationManifest,\n    build_umd_053_certification_manifest,\n    certify_raw_venue_market_observation_admission_ledger,\n    certify_umd_053_foundation,\n    verify_umd_053_raw_venue_market_observation_admission_ledger,\n)\n'
EXPORTED_NAMES = ('UMD_053_BUILD_ID', 'UMD_053_BUILD_NAME', 'UMD_053_REVISION', 'UMD_053_SCHEMA_VERSION', 'CertifiedRawVenueMarketObservationAdmissionLedgerEntry', 'ReadOnlyRawVenueMarketObservationAdmissionLedger', 'UMD053CertificationManifest', 'build_umd_053_certification_manifest', 'certify_raw_venue_market_observation_admission_ledger', 'certify_umd_053_foundation', 'verify_umd_053_raw_venue_market_observation_admission_ledger')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'), ('umd_045_venue_discovery_source_contract', 'verify_umd_045_venue_discovery_source_contract'), ('umd_046_venue_discovery_source_registry', 'verify_umd_046_venue_discovery_source_registry'), ('umd_047_venue_discovery_request_contract', 'verify_umd_047_venue_discovery_request_contract'), ('umd_048_venue_discovery_request_admission_gate', 'verify_umd_048_venue_discovery_request_admission_gate'), ('umd_049_venue_discovery_request_admission_ledger', 'verify_umd_049_venue_discovery_request_admission_ledger'), ('umd_050_venue_discovery_request_admission_ledger_read_model', 'verify_umd_050_venue_discovery_request_admission_ledger_read_model'), ('umd_051_raw_venue_market_observation_contract', 'verify_umd_051_raw_venue_market_observation_contract'), ('umd_052_raw_venue_market_observation_admission_gate', 'verify_umd_052_raw_venue_market_observation_admission_gate'))


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_direct(path: Path, source: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
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
        "from .umd_053_raw_venue_market_"
        "observation_admission_ledger import ("
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
            "umd_053_raw_venue_market_observation_admission_ledger"
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
                "UMD-053 missing symbols: "
                + ", ".join(missing)
            )

        if module.verify_umd_053_raw_venue_market_observation_admission_ledger() is not True:
            raise RuntimeError(
                "UMD-053 verification returned false"
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
    print(" UMD-053 REPOSITORY-VERIFIED INSTALLER")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION LEDGER"
    )
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-052 "
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
                "[ROLLBACK] UMD-053 installation failed; "
                "all affected files restored"
            )
        raise

    manifest = {
        "build_id": "UMD-053",
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
            for number in range(1, 53)
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

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required UMD-053 symbols verified")
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-053 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
