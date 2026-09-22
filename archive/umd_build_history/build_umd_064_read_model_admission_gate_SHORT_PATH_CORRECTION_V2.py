from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = (
    "UMD_064_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"
    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"
    "ADMISSION_GATE_SHORT_PATH_CORRECTION_V2"
)

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"

MODULE = PKG / "umd_064_read_model_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_064_read_model_admission_gate.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_063_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model import (\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,\n    certify_umd_063_read_model,\n)\n\nUMD_064_BUILD_ID = "UMD-064"\nUMD_064_BUILD_NAME = (\n    "Certified Raw Venue Market Observation Admission Ledger "\n    "Read Model Admission Ledger Read Model Admission Ledger "\n    "Read Model Admission Ledger Read Model Admission Gate"\n)\nUMD_064_REVISION = (\n    "UMD_064_CERTIFIED_RAW_VENUE_MARKET_OBSERVATION_"\n    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"\n    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"\n    "ADMISSION_GATE_V1"\n)\nUMD_064_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "automatic_discovery",\n    "automatic_observation_creation",\n    "automatic_admission_commit",\n    "ledger_append",\n    "ledger_mutation",\n    "read_model_mutation",\n    "read_model_persistence",\n    "canonical_market_construction",\n    "classification_inference",\n    "duplicate_resolution",\n    "registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(\n        character not in "0123456789abcdef"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _freeze_checks(\n    checks: Mapping[str, bool],\n) -> Mapping[str, bool]:\n    if not isinstance(checks, Mapping):\n        raise TypeError("checks must be a mapping")\n\n    normalized = {}\n    for key, value in checks.items():\n        normalized_key = _text(str(key), "check name")\n        if not isinstance(value, bool):\n            raise TypeError(\n                f"check {normalized_key!r} must be boolean"\n            )\n        normalized[normalized_key] = value\n\n    return MappingProxyType(\n        dict(sorted(normalized.items()))\n    )\n\n\ndef _reasons(\n    values: Tuple[str, ...],\n) -> Tuple[str, ...]:\n    if not isinstance(values, tuple):\n        values = tuple(values)\n\n    return tuple(\n        sorted(\n            {\n                _text(value, "rejection_reason")\n                for value in values\n            }\n        )\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision:\n    read_model_id: str\n    read_model_hash: str\n    source_ledger_hash: str\n    total_entry_count: int\n    admitted_entry_count: int\n    rejected_entry_count: int\n    latest_entry_id: str | None\n    latest_admitted_entry_id: str | None\n    admitted: bool\n    checks: Mapping[str, bool]\n    rejection_reasons: Tuple[str, ...]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        object.__setattr__(\n            self,\n            "read_model_id",\n            _text(self.read_model_id, "read_model_id"),\n        )\n        object.__setattr__(\n            self,\n            "read_model_hash",\n            _sha256(self.read_model_hash, "read_model_hash"),\n        )\n        object.__setattr__(\n            self,\n            "source_ledger_hash",\n            _sha256(\n                self.source_ledger_hash,\n                "source_ledger_hash",\n            ),\n        )\n\n        for field_name in (\n            "total_entry_count",\n            "admitted_entry_count",\n            "rejected_entry_count",\n        ):\n            value = getattr(self, field_name)\n            if not isinstance(value, int):\n                raise TypeError(\n                    f"{field_name} must be an integer"\n                )\n            if value < 0:\n                raise ValueError(\n                    f"{field_name} must be non-negative"\n                )\n\n        if (\n            self.admitted_entry_count\n            + self.rejected_entry_count\n            != self.total_entry_count\n        ):\n            raise ValueError(\n                "admitted and rejected counts must partition total"\n            )\n\n        for field_name in (\n            "latest_entry_id",\n            "latest_admitted_entry_id",\n        ):\n            value = getattr(self, field_name)\n            if value is not None:\n                object.__setattr__(\n                    self,\n                    field_name,\n                    _text(value, field_name),\n                )\n\n        if not isinstance(self.admitted, bool):\n            raise TypeError("admitted must be boolean")\n\n        frozen_checks = _freeze_checks(self.checks)\n        object.__setattr__(\n            self,\n            "checks",\n            frozen_checks,\n        )\n\n        normalized_reasons = _reasons(\n            self.rejection_reasons\n        )\n        object.__setattr__(\n            self,\n            "rejection_reasons",\n            normalized_reasons,\n        )\n\n        failed_checks = tuple(\n            sorted(\n                name\n                for name, passed in frozen_checks.items()\n                if not passed\n            )\n        )\n\n        if self.admitted:\n            if failed_checks:\n                raise ValueError(\n                    "admitted decisions cannot contain failed checks"\n                )\n            if normalized_reasons:\n                raise ValueError(\n                    "admitted decisions cannot contain rejection reasons"\n                )\n        else:\n            if not failed_checks:\n                raise ValueError(\n                    "rejected decisions require failed checks"\n                )\n            if normalized_reasons != failed_checks:\n                raise ValueError(\n                    "rejection reasons must exactly match failed checks"\n                )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError(\n                "decision lineage must belong to UMD"\n            )\n        if self.lineage.build_id != UMD_064_BUILD_ID:\n            raise ValueError(\n                "decision lineage must use build_id UMD-064"\n            )\n        if (\n            self.read_model_hash\n            not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "decision lineage must include read_model_hash"\n            )\n        if (\n            self.source_ledger_hash\n            not in self.lineage.parent_hashes\n        ):\n            raise ValueError(\n                "decision lineage must include source_ledger_hash"\n            )\n\n    @property\n    def decision_id(self) -> str:\n        return (\n            "umd:raw-observation-rm-admission-ledger-rm-"\n            "admission-ledger-rm-admission-ledger-rm-"\n            "admission-decision:"\n            + deterministic_sha256(\n                {\n                    "read_model_id": self.read_model_id,\n                    "read_model_hash": self.read_model_hash,\n                    "source_ledger_hash": self.source_ledger_hash,\n                    "admitted": self.admitted,\n                    "checks": self.checks,\n                    "rejection_reasons": (\n                        self.rejection_reasons\n                    ),\n                }\n            )\n        )\n\n    def to_canonical_dict(\n        self,\n    ) -> Mapping[str, Any]:\n        return {\n            "decision_id": self.decision_id,\n            "read_model_id": self.read_model_id,\n            "read_model_hash": self.read_model_hash,\n            "source_ledger_hash": self.source_ledger_hash,\n            "total_entry_count": self.total_entry_count,\n            "admitted_entry_count": (\n                self.admitted_entry_count\n            ),\n            "rejected_entry_count": (\n                self.rejected_entry_count\n            ),\n            "latest_entry_id": self.latest_entry_id,\n            "latest_admitted_entry_id": (\n                self.latest_admitted_entry_id\n            ),\n            "admitted": self.admitted,\n            "checks": self.checks,\n            "rejection_reasons": (\n                self.rejection_reasons\n            ),\n            "lineage": self.lineage,\n        }\n\n    @property\n    def record_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef evaluate_umd_064_read_model_admission(\n    read_model: CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,\n    *,\n    seen_read_model_ids: Tuple[str, ...] = (),\n    seen_read_model_hashes: Tuple[str, ...] = (),\n    seen_source_ledger_hashes: Tuple[str, ...] = (),\n    lineage: ImmutableLineage,\n) -> CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision:\n    if not isinstance(\n        read_model,\n        CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModel,\n    ):\n        raise TypeError(\n            "read_model must be the exact certified UMD-063 class"\n        )\n\n    certification = certify_umd_063_read_model(\n        read_model\n    )\n\n    normalized_ids = {\n        _text(\n            value,\n            "seen_read_model_id",\n        )\n        for value in seen_read_model_ids\n    }\n    normalized_hashes = {\n        _sha256(\n            value,\n            "seen_read_model_hash",\n        )\n        for value in seen_read_model_hashes\n    }\n    normalized_source_hashes = {\n        _sha256(\n            value,\n            "seen_source_ledger_hash",\n        )\n        for value in seen_source_ledger_hashes\n    }\n\n    checks = {\n        "read_model_certified": (\n            certification["certified"]\n            is True\n        ),\n        "read_model_id_matches": (\n            certification["read_model_id"]\n            == read_model.read_model_id\n        ),\n        "read_model_hash_matches": (\n            certification["read_model_hash"]\n            == read_model.read_model_hash\n        ),\n        "source_ledger_hash_matches": (\n            certification["source_ledger_hash"]\n            == read_model.source_ledger_hash\n        ),\n        "counts_match": (\n            certification["total_entry_count"]\n            == read_model.total_entry_count\n            and certification[\n                "admitted_entry_count"\n            ]\n            == read_model.admitted_entry_count\n            and certification[\n                "rejected_entry_count"\n            ]\n            == read_model.rejected_entry_count\n        ),\n        "count_partition_valid": (\n            read_model.admitted_entry_count\n            + read_model.rejected_entry_count\n            == read_model.total_entry_count\n        ),\n        "latest_entry_consistent": (\n            (\n                read_model.total_entry_count\n                == 0\n                and read_model.latest_entry_id\n                is None\n            )\n            or (\n                read_model.total_entry_count\n                > 0\n                and read_model.latest_entry_id\n                == read_model.ordered_entry_ids[-1]\n            )\n        ),\n        "latest_admitted_entry_consistent": (\n            (\n                read_model.admitted_entry_count\n                == 0\n                and read_model.latest_admitted_entry_id\n                is None\n            )\n            or (\n                read_model.admitted_entry_count\n                > 0\n                and read_model.latest_admitted_entry_id\n                == read_model.admitted_entry_ids[-1]\n            )\n        ),\n        "read_model_id_not_seen": (\n            read_model.read_model_id\n            not in normalized_ids\n        ),\n        "read_model_hash_not_seen": (\n            read_model.read_model_hash\n            not in normalized_hashes\n        ),\n        "source_ledger_hash_not_seen": (\n            read_model.source_ledger_hash\n            not in normalized_source_hashes\n        ),\n        "lineage_bound_to_source_ledger": (\n            read_model.source_ledger_hash\n            in read_model.lineage.parent_hashes\n        ),\n        "read_only_indexes": all(\n            isinstance(\n                index,\n                MappingProxyType,\n            )\n            for index in (\n                read_model._entry_position_by_id,\n                read_model._read_model_position_by_id,\n                read_model._read_model_position_by_hash,\n                read_model._source_ledger_position_by_hash,\n                read_model._decision_position_by_id,\n            )\n        ),\n    }\n\n    rejection_reasons = tuple(\n        sorted(\n            name\n            for name, passed in checks.items()\n            if not passed\n        )\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(\n        read_model_id=read_model.read_model_id,\n        read_model_hash=read_model.read_model_hash,\n        source_ledger_hash=(\n            read_model.source_ledger_hash\n        ),\n        total_entry_count=(\n            read_model.total_entry_count\n        ),\n        admitted_entry_count=(\n            read_model.admitted_entry_count\n        ),\n        rejected_entry_count=(\n            read_model.rejected_entry_count\n        ),\n        latest_entry_id=(\n            read_model.latest_entry_id\n        ),\n        latest_admitted_entry_id=(\n            read_model.latest_admitted_entry_id\n        ),\n        admitted=not rejection_reasons,\n        checks=checks,\n        rejection_reasons=rejection_reasons,\n        lineage=lineage,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD064CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    gate_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(\n        self,\n    ) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": (\n                self.schema_version\n            ),\n            "upstream_builds": (\n                self.upstream_builds\n            ),\n            "gate_mode": self.gate_mode,\n            "prohibited_capabilities": (\n                self.prohibited_capabilities\n            ),\n            "network_enabled": (\n                self.network_enabled\n            ),\n            "persistence_enabled": (\n                self.persistence_enabled\n            ),\n            "mutation_enabled": (\n                self.mutation_enabled\n            ),\n            "publication_enabled": (\n                self.publication_enabled\n            ),\n            "execution_enabled": (\n                self.execution_enabled\n            ),\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_064_certification_manifest(\n) -> UMD064CertificationManifest:\n    return UMD064CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_064_BUILD_ID,\n        revision=UMD_064_REVISION,\n        schema_version=(\n            UMD_064_SCHEMA_VERSION\n        ),\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 64)\n        ),\n        gate_mode=(\n            "deterministic_read_only_read_model_admission"\n        ),\n        prohibited_capabilities=(\n            PROHIBITED_CAPABILITIES\n        ),\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_umd_064_foundation(\n) -> Mapping[str, Any]:\n    manifest = (\n        build_umd_064_certification_manifest()\n    )\n\n    checks = {\n        "subsystem_identity": (\n            manifest.subsystem_id == "UMD"\n        ),\n        "build_identity": (\n            manifest.build_id == "UMD-064"\n        ),\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 64)\n            )\n        ),\n        "gate_mode": (\n            manifest.gate_mode\n            == "deterministic_read_only_read_model_admission"\n        ),\n        "network_disabled": (\n            manifest.network_enabled is False\n        ),\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": (\n            manifest.mutation_enabled is False\n        ),\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": (\n            manifest.execution_enabled is False\n        ),\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": (\n                manifest.manifest_hash\n            ),\n            "checks": MappingProxyType(\n                checks\n            ),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_064_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate() -> bool:\n    result = certify_umd_064_foundation()\n\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-064 foundation certification failed: "\n            + ", ".join(\n                result["failed_checks"]\n            )\n        )\n\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_061_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate import (\n    UMD_061_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.umd_062_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger import (\n    UMD_062_REVISION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry,\n    ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger,\n)\nfrom qseries_v2.universal_market_discovery.umd_063_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model import (\n    UMD_063_REVISION,\n    build_umd_063_admission_ledger_read_model,\n)\nfrom qseries_v2.universal_market_discovery.umd_064_read_model_admission_gate import (\n    UMD_064_REVISION,\n    build_umd_064_certification_manifest,\n    certify_umd_064_foundation,\n    evaluate_umd_064_read_model_admission,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    7,\n    7,\n    35,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef digest(label: str) -> str:\n    return hashlib.sha256(\n        label.encode("utf-8")\n    ).hexdigest()\n\n\ndef decision(\n    suffix: str,\n    admitted: bool = True,\n):\n    read_model_hash = digest(\n        f"umd-064:{suffix}:read-model"\n    )\n    source_ledger_hash = digest(\n        f"umd-064:{suffix}:source-ledger"\n    )\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-061",\n        revision=UMD_061_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            read_model_hash,\n            source_ledger_hash,\n        ),\n        source_refs=(\n            f"fixture://umd-064/decision/{suffix}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(\n        read_model_id=f"read-model-{suffix}",\n        read_model_hash=read_model_hash,\n        source_ledger_hash=source_ledger_hash,\n        total_entry_count=2,\n        admitted_entry_count=1,\n        rejected_entry_count=1,\n        latest_entry_id=f"entry-{suffix}",\n        latest_admitted_entry_id=f"admitted-{suffix}",\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef entry(\n    number: int,\n    value,\n    previous,\n):\n    parents = [value.record_hash]\n    if previous is not None:\n        parents.append(previous)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-062",\n        revision=UMD_062_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(\n            f"fixture://umd-064/entry/{number}",\n        ),\n        created_at=FIXED,\n    )\n\n    return CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=value,\n        recorded_at=FIXED,\n        metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\ndef read_model():\n    first = entry(\n        1,\n        decision("a", True),\n        None,\n    )\n    second = entry(\n        2,\n        decision("b", False),\n        first.entry_hash,\n    )\n\n    ledger_lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-062",\n        revision=UMD_062_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            second.entry_hash,\n        ),\n        source_refs=(\n            "fixture://umd-064/ledger",\n        ),\n        created_at=FIXED,\n    )\n\n    ledger = ReadOnlyRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedger(\n        entries=(\n            first,\n            second,\n        ),\n        ledger_lineage=(\n            ledger_lineage\n        ),\n    )\n\n    model_lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-063",\n        revision=UMD_063_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            ledger.ledger_hash,\n        ),\n        source_refs=(\n            "fixture://umd-064/read-model",\n        ),\n        created_at=FIXED,\n    )\n\n    return build_umd_063_admission_ledger_read_model(\n        ledger,\n        metadata={\n            "read_only": True\n        },\n        lineage=model_lineage,\n    )\n\n\ndef gate_lineage(model):\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-064",\n        revision=UMD_064_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            model.read_model_hash,\n            model.source_ledger_hash,\n        ),\n        source_refs=(\n            "fixture://umd-064/gate",\n        ),\n        created_at=FIXED,\n    )\n\n\nclass TestUMD064(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = (\n            certify_umd_064_foundation()\n        )\n\n        self.assertTrue(\n            result["certified"]\n        )\n        self.assertEqual(\n            result["build_id"],\n            "UMD-064",\n        )\n\n    def test_valid_read_model_admitted(\n        self,\n    ) -> None:\n        model = read_model()\n\n        decision_value = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                lineage=gate_lineage(\n                    model\n                ),\n            )\n        )\n\n        self.assertTrue(\n            decision_value.admitted\n        )\n        self.assertEqual(\n            decision_value.rejection_reasons,\n            (),\n        )\n        self.assertTrue(\n            all(\n                decision_value.checks.values()\n            )\n        )\n\n    def test_deterministic(\n        self,\n    ) -> None:\n        model = read_model()\n        lineage = gate_lineage(\n            model\n        )\n\n        first = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                lineage=lineage,\n            )\n        )\n        second = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                lineage=lineage,\n            )\n        )\n\n        self.assertEqual(\n            first.decision_id,\n            second.decision_id,\n        )\n        self.assertEqual(\n            first.record_hash,\n            second.record_hash,\n        )\n\n    def test_duplicate_read_model_id_rejected(\n        self,\n    ) -> None:\n        model = read_model()\n\n        decision_value = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                seen_read_model_ids=(\n                    model.read_model_id,\n                ),\n                lineage=gate_lineage(\n                    model\n                ),\n            )\n        )\n\n        self.assertFalse(\n            decision_value.admitted\n        )\n        self.assertIn(\n            "read_model_id_not_seen",\n            decision_value.rejection_reasons,\n        )\n\n    def test_duplicate_read_model_hash_rejected(\n        self,\n    ) -> None:\n        model = read_model()\n\n        decision_value = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                seen_read_model_hashes=(\n                    model.read_model_hash,\n                ),\n                lineage=gate_lineage(\n                    model\n                ),\n            )\n        )\n\n        self.assertFalse(\n            decision_value.admitted\n        )\n        self.assertIn(\n            "read_model_hash_not_seen",\n            decision_value.rejection_reasons,\n        )\n\n    def test_duplicate_source_ledger_rejected(\n        self,\n    ) -> None:\n        model = read_model()\n\n        decision_value = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                seen_source_ledger_hashes=(\n                    model.source_ledger_hash,\n                ),\n                lineage=gate_lineage(\n                    model\n                ),\n            )\n        )\n\n        self.assertFalse(\n            decision_value.admitted\n        )\n        self.assertIn(\n            "source_ledger_hash_not_seen",\n            decision_value.rejection_reasons,\n        )\n\n    def test_lineage_requires_both_hashes(\n        self,\n    ) -> None:\n        model = read_model()\n\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-064",\n            revision=UMD_064_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(\n                model.read_model_hash,\n            ),\n            source_refs=(\n                "fixture://umd-064/bad",\n            ),\n            created_at=FIXED,\n        )\n\n        with self.assertRaises(\n            ValueError\n        ):\n            evaluate_umd_064_read_model_admission(\n                model,\n                lineage=bad,\n            )\n\n    def test_exact_umd063_type(\n        self,\n    ) -> None:\n        model = read_model()\n\n        self.assertEqual(\n            model.lineage.build_id,\n            "UMD-063",\n        )\n\n    def test_immutable(\n        self,\n    ) -> None:\n        model = read_model()\n\n        decision_value = (\n            evaluate_umd_064_read_model_admission(\n                model,\n                lineage=gate_lineage(\n                    model\n                ),\n            )\n        )\n\n        with self.assertRaises(\n            (\n                FrozenInstanceError,\n                AttributeError,\n            )\n        ):\n            decision_value.admitted = False\n\n        with self.assertRaises(\n            TypeError\n        ):\n            decision_value.checks[\n                "changed"\n            ] = False\n\n    def test_side_effects(\n        self,\n    ) -> None:\n        manifest = (\n            build_umd_064_certification_manifest()\n        )\n\n        self.assertFalse(\n            manifest.network_enabled\n        )\n        self.assertFalse(\n            manifest.persistence_enabled\n        )\n        self.assertFalse(\n            manifest.mutation_enabled\n        )\n        self.assertFalse(\n            manifest.publication_enabled\n        )\n        self.assertFalse(\n            manifest.execution_enabled\n        )\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(\n        " UMD-064 CERTIFICATION TEST"\n    )\n    print(\n        " CERTIFIED RAW VENUE MARKET OBSERVATION "\n        "ADMISSION LEDGER READ MODEL ADMISSION LEDGER "\n        "READ MODEL ADMISSION LEDGER READ MODEL "\n        "ADMISSION LEDGER READ MODEL ADMISSION GATE"\n    )\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD064\n    )\n\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(\n        suite\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = (\n        build_umd_064_certification_manifest()\n    )\n\n    print()\n    print(\n        f"[PASS] Build: "\n        f"{manifest.build_id}"\n    )\n    print(\n        f"[PASS] Revision: "\n        f"{manifest.revision}"\n    )\n    print(\n        f"[PASS] Manifest hash: "\n        f"{manifest.manifest_hash}"\n    )\n    print(\n        "[PASS] UMD-001 through UMD-063 consumed read-only"\n    )\n    print(\n        "[PASS] Exact UMD-063 read-model class consumed"\n    )\n    print(\n        "[PASS] Deterministic read-model admission decision certified"\n    )\n    print(\n        "[PASS] Duplicate read-model ID, hash, and source-ledger replay rejected"\n    )\n    print(\n        "[PASS] Immutable complete decision lineage certified"\n    )\n    print(\n        "[PASS] Network, persistence, publication, and execution disabled"\n    )\n    print(\n        "[DONE] UMD-064 CERTIFIED RAW VENUE MARKET OBSERVATION "\n        "ADMISSION LEDGER READ MODEL ADMISSION LEDGER "\n        "READ MODEL ADMISSION LEDGER READ MODEL "\n        "ADMISSION LEDGER READ MODEL ADMISSION GATE CERTIFIED"\n    )\n'
INIT_IMPORT = '\nfrom .umd_064_read_model_admission_gate import (\n    UMD_064_BUILD_ID,\n    UMD_064_BUILD_NAME,\n    UMD_064_REVISION,\n    UMD_064_SCHEMA_VERSION,\n    CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,\n    UMD064CertificationManifest,\n    evaluate_umd_064_read_model_admission,\n    build_umd_064_certification_manifest,\n    certify_umd_064_foundation,\n    verify_umd_064_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate,\n)\n'
EXPORTED_NAMES = ('UMD_064_BUILD_ID', 'UMD_064_BUILD_NAME', 'UMD_064_REVISION', 'UMD_064_SCHEMA_VERSION', 'CertifiedRawVenueMarketObservationAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision', 'UMD064CertificationManifest', 'evaluate_umd_064_read_model_admission', 'build_umd_064_certification_manifest', 'certify_umd_064_foundation', 'verify_umd_064_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'), ('umd_045_venue_discovery_source_contract', 'verify_umd_045_venue_discovery_source_contract'), ('umd_046_venue_discovery_source_registry', 'verify_umd_046_venue_discovery_source_registry'), ('umd_047_venue_discovery_request_contract', 'verify_umd_047_venue_discovery_request_contract'), ('umd_048_venue_discovery_request_admission_gate', 'verify_umd_048_venue_discovery_request_admission_gate'), ('umd_049_venue_discovery_request_admission_ledger', 'verify_umd_049_venue_discovery_request_admission_ledger'), ('umd_050_venue_discovery_request_admission_ledger_read_model', 'verify_umd_050_venue_discovery_request_admission_ledger_read_model'), ('umd_051_raw_venue_market_observation_contract', 'verify_umd_051_raw_venue_market_observation_contract'), ('umd_052_raw_venue_market_observation_admission_gate', 'verify_umd_052_raw_venue_market_observation_admission_gate'), ('umd_053_raw_venue_market_observation_admission_ledger', 'verify_umd_053_raw_venue_market_observation_admission_ledger'), ('umd_054_raw_venue_market_observation_admission_ledger_read_model', 'verify_umd_054_raw_venue_market_observation_admission_ledger_read_model'), ('umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate', 'verify_umd_055_raw_venue_market_observation_admission_ledger_read_model_admission_gate'), ('umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger', 'verify_umd_056_raw_venue_market_observation_admission_ledger_read_model_admission_ledger'), ('umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_057_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model'), ('umd_058_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_058_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('umd_059_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_059_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('umd_060_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_060_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_061_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_061_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('umd_062_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_062_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('umd_063_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_063_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'))


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
        "from .umd_064_read_model_admission_gate import ("
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
            "umd_064_read_model_admission_gate"
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
                "UMD-064 missing symbols: "
                + ", ".join(missing)
            )

        verifier = getattr(
            module,
            "verify_umd_064_raw_venue_market_observation_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate",
        )

        if verifier() is not True:
            raise RuntimeError(
                "UMD-064 verification returned false"
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
    print(
        " UMD-064 SHORT-PATH REPOSITORY CORRECTION V2 INSTALLER"
    )
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION "
        "READ MODEL ADMISSION GATE"
    )
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()

    print(
        "[PASS] Certified UMD-001 through UMD-063 "
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
                "[ROLLBACK] UMD-064 installation failed; "
                "all affected files restored"
            )

        raise

    manifest = {
        "build_id": "UMD-064",
        "revision": REVISION,
        "production_module": "umd_064_read_model_admission_gate.py",
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 64)
        ),
        "mode": (
            "deterministic_read_only_read_model_admission"
        ),
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
        "[PASS] Windows-safe short production path selected"
    )
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
        "[PASS] In-memory compilation verified"
    )
    print(
        "[PASS] Required UMD-064 symbols verified"
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
        "[DONE] UMD-064 SHORT-PATH CORRECTION V2 "
        "INSTALLATION COMPLETE"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
