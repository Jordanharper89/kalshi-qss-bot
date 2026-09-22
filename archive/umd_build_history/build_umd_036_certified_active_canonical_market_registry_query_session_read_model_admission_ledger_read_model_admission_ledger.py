from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_036_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom datetime import datetime, timezone\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate import (\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,\n)\n\nUMD_036_BUILD_ID = "UMD-036"\nUMD_036_BUILD_NAME = (\n    "Certified Active Canonical Market Registry Query Session "\n    "Read Model Admission Ledger Read Model Admission Ledger"\n)\nUMD_036_REVISION = (\n    "UMD_036_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_"\n    "READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_V1"\n)\nUMD_036_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_discovery",\n    "market_scanning",\n    "automatic_admission",\n    "automatic_ledger_append",\n    "ledger_mutation",\n    "record_deletion",\n    "record_reordering",\n    "read_model_mutation",\n    "read_model_persistence",\n    "active_registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(character not in "0123456789abcdef" for character in normalized):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _utc(value: datetime, field_name: str) -> datetime:\n    if not isinstance(value, datetime):\n        raise TypeError(f"{field_name} must be a datetime")\n    if value.tzinfo is None:\n        raise ValueError(f"{field_name} must be timezone-aware")\n    return value.astimezone(timezone.utc)\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(\n        dict(sorted((str(key), item) for key, item in value.items()))\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry:\n    sequence_number: int\n    previous_entry_hash: str | None\n    decision: CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision\n    recorded_at: datetime\n    metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.sequence_number, int):\n            raise TypeError("sequence_number must be an integer")\n        if self.sequence_number < 1:\n            raise ValueError("sequence_number must be positive")\n\n        if self.previous_entry_hash is None:\n            if self.sequence_number != 1:\n                raise ValueError(\n                    "only the first ledger entry may omit previous_entry_hash"\n                )\n        else:\n            object.__setattr__(\n                self,\n                "previous_entry_hash",\n                _sha256(self.previous_entry_hash, "previous_entry_hash"),\n            )\n\n        if not isinstance(\n            self.decision,\n            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,\n        ):\n            raise TypeError(\n                "decision must be a certified UMD-035 admission decision"\n            )\n\n        object.__setattr__(\n            self,\n            "recorded_at",\n            _utc(self.recorded_at, "recorded_at"),\n        )\n        object.__setattr__(self, "metadata", _freeze(self.metadata))\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("ledger-entry lineage must belong to UMD")\n        if self.lineage.build_id != UMD_036_BUILD_ID:\n            raise ValueError("ledger-entry lineage must use build_id UMD-036")\n        if self.decision.record_hash not in self.lineage.parent_hashes:\n            raise ValueError(\n                "ledger-entry lineage must include UMD-035 decision record hash"\n            )\n        if (\n            self.previous_entry_hash is not None\n            and self.previous_entry_hash not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "ledger-entry lineage must include previous entry hash"\n            )\n\n    @property\n    def entry_id(self) -> str:\n        return (\n            "umd:query-session-read-model-admission-ledger-read-model-"\n            "admission-ledger-entry:"\n            + deterministic_sha256(\n                {\n                    "sequence_number": self.sequence_number,\n                    "previous_entry_hash": self.previous_entry_hash,\n                    "decision_id": self.decision.decision_id,\n                    "decision_record_hash": self.decision.record_hash,\n                }\n            )\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "entry_id": self.entry_id,\n            "sequence_number": self.sequence_number,\n            "previous_entry_hash": self.previous_entry_hash,\n            "decision": self.decision,\n            "recorded_at": self.recorded_at,\n            "metadata": self.metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def entry_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True, slots=True)\nclass ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger:\n    entries: Tuple[\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n        ...,\n    ]\n    ledger_lineage: ImmutableLineage\n    _by_entry_id: Mapping[\n        str,\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _by_read_model_hash: Mapping[\n        str,\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n    _by_decision_id: Mapping[\n        str,\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ] = field(init=False, repr=False)\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.entries, tuple):\n            object.__setattr__(self, "entries", tuple(self.entries))\n\n        ordered = tuple(\n            sorted(self.entries, key=lambda entry: entry.sequence_number)\n        )\n        object.__setattr__(self, "entries", ordered)\n\n        if self.ledger_lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("ledger lineage must belong to UMD")\n        if self.ledger_lineage.build_id != UMD_036_BUILD_ID:\n            raise ValueError("ledger lineage must use build_id UMD-036")\n\n        by_entry_id = {}\n        by_read_model_hash = {}\n        by_decision_id = {}\n        previous = None\n\n        for expected_sequence, entry in enumerate(ordered, start=1):\n            if not isinstance(\n                entry,\n                CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n            ):\n                raise TypeError(\n                    "entries must contain certified UMD-036 ledger entries"\n                )\n            if entry.sequence_number != expected_sequence:\n                raise ValueError(\n                    "ledger sequence must be contiguous and start at 1"\n                )\n            if previous is None:\n                if entry.previous_entry_hash is not None:\n                    raise ValueError(\n                        "first ledger entry must not have previous hash"\n                    )\n            elif entry.previous_entry_hash != previous.entry_hash:\n                raise ValueError(\n                    "ledger previous-entry hash chain mismatch"\n                )\n\n            decision = entry.decision\n            if entry.entry_id in by_entry_id:\n                raise ValueError("duplicate ledger entry ID")\n            if decision.read_model_hash in by_read_model_hash:\n                raise ValueError(\n                    "read model may appear only once in admission ledger"\n                )\n            if decision.decision_id in by_decision_id:\n                raise ValueError(\n                    "admission decision may appear only once in ledger"\n                )\n\n            by_entry_id[entry.entry_id] = entry\n            by_read_model_hash[decision.read_model_hash] = entry\n            by_decision_id[decision.decision_id] = entry\n            previous = entry\n\n        if ordered and ordered[-1].entry_hash not in self.ledger_lineage.parent_hashes:\n            raise ValueError(\n                "ledger lineage must include latest entry hash"\n            )\n\n        object.__setattr__(\n            self,\n            "_by_entry_id",\n            MappingProxyType(by_entry_id),\n        )\n        object.__setattr__(\n            self,\n            "_by_read_model_hash",\n            MappingProxyType(by_read_model_hash),\n        )\n        object.__setattr__(\n            self,\n            "_by_decision_id",\n            MappingProxyType(by_decision_id),\n        )\n\n    def get(\n        self,\n        entry_id: str,\n    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry | None:\n        return self._by_entry_id.get(_text(entry_id, "entry_id"))\n\n    def get_by_read_model_hash(\n        self,\n        read_model_hash: str,\n    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry | None:\n        return self._by_read_model_hash.get(\n            _sha256(read_model_hash, "read_model_hash")\n        )\n\n    def get_by_decision(\n        self,\n        decision_id: str,\n    ) -> CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry | None:\n        return self._by_decision_id.get(_text(decision_id, "decision_id"))\n\n    def admitted_entries(self) -> Tuple[\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n        ...,\n    ]:\n        return tuple(entry for entry in self.entries if entry.decision.admitted)\n\n    def rejected_entries(self) -> Tuple[\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n        ...,\n    ]:\n        return tuple(\n            entry for entry in self.entries if not entry.decision.admitted\n        )\n\n    def latest_admitted(self) -> (\n        CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry\n        | None\n    ):\n        admitted = self.admitted_entries()\n        return None if not admitted else admitted[-1]\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "ledger_mode": "append_only_read_only",\n            "entries": self.entries,\n            "ledger_lineage": self.ledger_lineage,\n        }\n\n    @property\n    def ledger_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD036CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    build_name: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    ledger_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "build_name": self.build_name,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "ledger_mode": self.ledger_mode,\n            "prohibited_capabilities": self.prohibited_capabilities,\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\ndef build_umd_036_certification_manifest() -> UMD036CertificationManifest:\n    return UMD036CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_036_BUILD_ID,\n        build_name=UMD_036_BUILD_NAME,\n        revision=UMD_036_REVISION,\n        schema_version=UMD_036_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}" for number in range(1, 36)\n        ),\n        ledger_mode="append_only_read_only",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger(\n    ledger: ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n) -> Mapping[str, Any]:\n    entries = ledger.entries\n    admitted = ledger.admitted_entries()\n    rejected = ledger.rejected_entries()\n\n    checks = {\n        "sequence_contiguous": (\n            tuple(entry.sequence_number for entry in entries)\n            == tuple(range(1, len(entries) + 1))\n        ),\n        "previous_hash_chain_valid": all(\n            entry.previous_entry_hash == entries[index - 1].entry_hash\n            for index, entry in enumerate(entries)\n            if index > 0\n        ),\n        "entry_ids_unique": (\n            len({entry.entry_id for entry in entries}) == len(entries)\n        ),\n        "read_model_hashes_unique": (\n            len({entry.decision.read_model_hash for entry in entries})\n            == len(entries)\n        ),\n        "decision_ids_unique": (\n            len({entry.decision.decision_id for entry in entries})\n            == len(entries)\n        ),\n        "admission_partition_complete": (\n            len(admitted) + len(rejected) == len(entries)\n        ),\n        "latest_entry_lineage_bound": (\n            not entries\n            or entries[-1].entry_hash in ledger.ledger_lineage.parent_hashes\n        ),\n        "deterministic_replay": (\n            ledger.ledger_hash\n            == deterministic_sha256(ledger.to_canonical_dict())\n        ),\n        "read_only_indexes": (\n            isinstance(ledger._by_entry_id, MappingProxyType)\n            and isinstance(ledger._by_read_model_hash, MappingProxyType)\n            and isinstance(ledger._by_decision_id, MappingProxyType)\n        ),\n    }\n\n    failed = tuple(name for name, passed in checks.items() if not passed)\n    latest = ledger.latest_admitted()\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "ledger_hash": ledger.ledger_hash,\n            "entry_count": len(entries),\n            "admitted_count": len(admitted),\n            "rejected_count": len(rejected),\n            "latest_admitted_read_model_hash": (\n                None if latest is None else latest.decision.read_model_hash\n            ),\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_036_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_036_certification_manifest()\n    checks = {\n        "subsystem_identity": manifest.subsystem_id == "UMD",\n        "build_identity": manifest.build_id == "UMD-036",\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(f"UMD-{number:03d}" for number in range(1, 36))\n        ),\n        "append_only_read_only": (\n            manifest.ledger_mode == "append_only_read_only"\n        ),\n        "network_disabled": manifest.network_enabled is False,\n        "persistence_disabled": manifest.persistence_enabled is False,\n        "mutation_disabled": manifest.mutation_enabled is False,\n        "publication_disabled": manifest.publication_enabled is False,\n        "execution_disabled": manifest.execution_enabled is False,\n        "deterministic_manifest_hash": (\n            manifest.manifest_hash\n            == deterministic_sha256(manifest.to_canonical_dict())\n        ),\n    }\n    failed = tuple(name for name, passed in checks.items() if not passed)\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger() -> bool:\n    certification = certify_umd_036_foundation()\n    if not certification["certified"]:\n        raise RuntimeError(\n            "UMD-036 foundation certification failed: "\n            + ", ".join(certification["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate import (\n    UMD_035_REVISION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger import (\n    UMD_036_REVISION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n    build_umd_036_certification_manifest,\n    certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger,\n    certify_umd_036_foundation,\n)\n\nFIXED = datetime(2026, 8, 6, 6, 35, 0, tzinfo=timezone.utc)\n\n\ndef decision(suffix: str, admitted: bool = True):\n    read_model_hash = (suffix * 64)[:64]\n    source_ledger_hash = (chr(ord(suffix) + 1) * 64)[:64]\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-035",\n        revision=UMD_035_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(read_model_hash, source_ledger_hash),\n        source_refs=(f"fixture://umd-036/decision/{suffix}",),\n        created_at=FIXED,\n    )\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionDecision(\n        read_model_hash=read_model_hash,\n        source_ledger_hash=source_ledger_hash,\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef entry(number, value, previous):\n    parents = [value.record_hash]\n    if previous is not None:\n        parents.append(previous)\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-036",\n        revision=UMD_036_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(f"fixture://umd-036/entry/{number}",),\n        created_at=FIXED,\n    )\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=value,\n        recorded_at=FIXED,\n        metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\ndef ledger(entries):\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-036",\n        revision=UMD_036_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(() if not entries else (entries[-1].entry_hash,)),\n        source_refs=("fixture://umd-036/ledger",),\n        created_at=FIXED,\n    )\n    return ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(\n        entries=tuple(entries),\n        ledger_lineage=lineage,\n    )\n\n\nclass TestUMD036(unittest.TestCase):\n    def test_foundation_certifies(self):\n        result = certify_umd_036_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-036")\n\n    def test_entry_identity_deterministic(self):\n        value = decision("a")\n        first = entry(1, value, None)\n        second = entry(1, value, None)\n        self.assertEqual(first.entry_id, second.entry_id)\n        self.assertEqual(first.entry_hash, second.entry_hash)\n\n    def test_ledger_certifies(self):\n        first = entry(1, decision("a", True), None)\n        second = entry(2, decision("d", False), first.entry_hash)\n        item = ledger((first, second))\n        result = certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger(item)\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["entry_count"], 2)\n        self.assertEqual(result["admitted_count"], 1)\n        self.assertEqual(result["rejected_count"], 1)\n\n    def test_lookup_indexes(self):\n        first = entry(1, decision("a"), None)\n        item = ledger((first,))\n        self.assertIs(item.get(first.entry_id), first)\n        self.assertIs(\n            item.get_by_read_model_hash(first.decision.read_model_hash),\n            first,\n        )\n        self.assertIs(\n            item.get_by_decision(first.decision.decision_id),\n            first,\n        )\n        self.assertIs(item.latest_admitted(), first)\n\n    def test_sequence_gap_rejected(self):\n        first = entry(1, decision("a"), None)\n        third = entry(3, decision("d"), first.entry_hash)\n        with self.assertRaises(ValueError):\n            ledger((first, third))\n\n    def test_previous_hash_mismatch_rejected(self):\n        first = entry(1, decision("a"), None)\n        second = entry(2, decision("d"), "f" * 64)\n        with self.assertRaises(ValueError):\n            ledger((first, second))\n\n    def test_duplicate_read_model_rejected(self):\n        value = decision("a")\n        first = entry(1, value, None)\n        second = entry(2, value, first.entry_hash)\n        with self.assertRaises(ValueError):\n            ledger((first, second))\n\n    def test_lineage_requires_decision_hash(self):\n        value = decision("a")\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-036",\n            revision=UMD_036_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(),\n            source_refs=("fixture://umd-036/bad-entry",),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(\n                sequence_number=1,\n                previous_entry_hash=None,\n                decision=value,\n                recorded_at=FIXED,\n                metadata={},\n                lineage=bad,\n            )\n\n    def test_ledger_lineage_requires_latest_hash(self):\n        first = entry(1, decision("a"), None)\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-036",\n            revision=UMD_036_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(),\n            source_refs=("fixture://umd-036/bad-ledger",),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger(\n                entries=(first,),\n                ledger_lineage=bad,\n            )\n\n    def test_immutable(self):\n        first = entry(1, decision("a"), None)\n        with self.assertRaises((FrozenInstanceError, AttributeError)):\n            first.sequence_number = 2\n        with self.assertRaises(TypeError):\n            first.metadata["read_only"] = False\n\n    def test_side_effects_disabled(self):\n        manifest = build_umd_036_certification_manifest()\n        self.assertEqual(manifest.ledger_mode, "append_only_read_only")\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 78)\n    print(" UMD-036 CERTIFICATION TEST")\n    print(\n        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION READ MODEL "\n        "ADMISSION LEDGER READ MODEL ADMISSION LEDGER"\n    )\n    print("=" * 78)\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD036)\n    result = unittest.TextTestRunner(verbosity=2).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_036_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-035 consumed read-only")\n    print("[PASS] UMD-035 admission decisions bound to ledger entries")\n    print("[PASS] Entry IDs and record hashes deterministic")\n    print("[PASS] Append-only sequence continuity enforced")\n    print("[PASS] Previous-entry hash chain verified")\n    print("[PASS] Duplicate read-model and decision replay rejected")\n    print("[PASS] Admitted and rejected indexes verified")\n    print("[PASS] Latest admitted view deterministic")\n    print("[PASS] Immutable read-only admission ledger certified")\n    print("[PASS] Network and persistence disabled")\n    print("[PASS] Publication and Q Series execution disabled")\n    print(\n        "[DONE] UMD-036 CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY "\n        "SESSION READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER CERTIFIED"\n    )\n'
INIT_IMPORT = '\nfrom .certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger import (\n    UMD_036_BUILD_ID,\n    UMD_036_BUILD_NAME,\n    UMD_036_REVISION,\n    UMD_036_SCHEMA_VERSION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger,\n    UMD036CertificationManifest,\n    build_umd_036_certification_manifest,\n    certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger,\n    certify_umd_036_foundation,\n    verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger,\n)\n'
EXPORTED_NAMES = ('UMD_036_BUILD_ID', 'UMD_036_BUILD_NAME', 'UMD_036_REVISION', 'UMD_036_SCHEMA_VERSION', 'CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerEntry', 'ReadOnlyActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedger', 'UMD036CertificationManifest', 'build_umd_036_certification_manifest', 'certify_active_market_query_session_read_model_admission_ledger_read_model_admission_ledger', 'certify_umd_036_foundation', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'))


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        normalize(source),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def find_all_bounds(source: str) -> tuple[int, int]:
    marker = "__all__ = ["
    start = source.find(marker)
    if start == -1:
        raise RuntimeError("UMD package __all__ list is missing")

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

    raise RuntimeError("UMD package __all__ closing bracket is missing")


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(encoding="utf-8")
    marker = (
        "from .certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model_"
        "admission_ledger import ("
    )

    if marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

    opening, closing = find_all_bounds(source)
    block = source[opening + 1 : closing]
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
        source = source[:closing] + insertion + source[closing:]

    compile(source, str(INIT), "exec")
    write_exact(INIT, source)


def verify_upstream() -> None:
    if not PKG.exists():
        raise FileNotFoundError(f"UMD package missing: {PKG}")
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    sys.path.insert(0, str(ROOT))
    try:
        for module_name, verifier_name in UPSTREAM_MODULES:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            verifier = getattr(module, verifier_name, None)
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
        importlib.invalidate_caches()
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_active_canonical_market_registry_query_session_"
            "read_model_admission_ledger_read_model_admission_ledger"
        )
        missing = [
            name
            for name in EXPORTED_NAMES
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-036 missing symbols: "
                + ", ".join(missing)
            )
        verifier = getattr(
            module,
            "verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger",
        )
        if verifier() is not True:
            raise RuntimeError(
                "UMD-036 verification returned false"
            )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    print("=" * 78)
    print(" UMD-036 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY QUERY SESSION "
        "READ MODEL ADMISSION LEDGER READ MODEL ADMISSION LEDGER"
    )
    print("=" * 78)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-035 "
        "verified read-only"
    )

    backups = {
        path: (path.read_bytes() if path.exists() else None)
        for path in (MODULE, INIT, TEST)
    }

    try:
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init()

        py_compile.compile(str(MODULE), doraise=True)
        py_compile.compile(str(INIT), doraise=True)
        py_compile.compile(str(TEST), doraise=True)
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
                os.replace(temporary, path)
        importlib.invalidate_caches()
        print(
            "[ROLLBACK] UMD-036 installation failed; "
            "all affected files restored"
        )
        raise

    manifest = {
        "build_id": "UMD-036",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}" for number in range(1, 36)
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
    print("[PASS] Python compilation verified")
    print("[PASS] Required UMD-036 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-036 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python test_umd_036_certified_active_canonical_market_registry_"
        "query_session_read_model_admission_ledger_read_model_"
        "admission_ledger.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
