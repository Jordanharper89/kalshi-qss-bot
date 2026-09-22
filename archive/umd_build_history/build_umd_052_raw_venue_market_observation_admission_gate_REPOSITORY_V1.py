from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = (
    "UMD_052_CERTIFIED_RAW_VENUE_MARKET_"
    "OBSERVATION_ADMISSION_GATE_REPOSITORY_V1"
)
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_052_raw_venue_market_observation_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_052_raw_venue_market_observation_admission_gate.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_051_raw_venue_market_observation_contract import (\n    CertifiedRawVenueMarketObservation,\n    certify_raw_venue_market_observation,\n)\n\nUMD_052_BUILD_ID = "UMD-052"\nUMD_052_BUILD_NAME = (\n    "Certified Raw Venue Market Observation Admission Gate"\n)\nUMD_052_REVISION = (\n    "UMD_052_CERTIFIED_RAW_VENUE_MARKET_"\n    "OBSERVATION_ADMISSION_GATE_V1"\n)\nUMD_052_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "automatic_discovery",\n    "automatic_observation_creation",\n    "automatic_admission_commit",\n    "ledger_append",\n    "canonical_market_construction",\n    "classification_inference",\n    "duplicate_resolution",\n    "observation_persistence",\n    "registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(\n            f"{field_name} must contain 64 hexadecimal characters"\n        )\n    if any(\n        character not in "0123456789abcdef"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must be lowercase SHA-256 hexadecimal"\n        )\n    return normalized\n\n\ndef _normalized_text_tuple(\n    values: Tuple[str, ...],\n    field_name: str,\n) -> Tuple[str, ...]:\n    if not isinstance(values, tuple):\n        values = tuple(values)\n    return tuple(\n        sorted(\n            {\n                _text(value, field_name)\n                for value in values\n            }\n        )\n    )\n\n\ndef _normalized_hash_tuple(\n    values: Tuple[str, ...],\n    field_name: str,\n) -> Tuple[str, ...]:\n    if not isinstance(values, tuple):\n        values = tuple(values)\n    return tuple(\n        sorted(\n            {\n                _sha256(value, field_name)\n                for value in values\n            }\n        )\n    )\n\n\ndef _freeze_checks(\n    checks: Mapping[str, bool],\n) -> Mapping[str, bool]:\n    if not isinstance(checks, Mapping):\n        raise TypeError("checks must be a mapping")\n    normalized = {}\n    for key, value in checks.items():\n        normalized_key = _text(str(key), "check name")\n        if not isinstance(value, bool):\n            raise TypeError(\n                f"check {normalized_key!r} must be boolean"\n            )\n        normalized[normalized_key] = value\n    return MappingProxyType(dict(sorted(normalized.items())))\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedRawVenueMarketObservationAdmissionDecision:\n    observation_id: str\n    observation_hash: str\n    request_id: str\n    request_hash: str\n    admission_decision_id: str\n    admission_decision_record_hash: str\n    source_id: str\n    source_contract_hash: str\n    source_registry_hash: str\n    raw_payload_hash: str\n    canonical_venue_id: str\n    adapter_key: str\n    venue_market_id: str\n    retrieval_sequence: int\n    admitted: bool\n    checks: Mapping[str, bool]\n    rejection_reasons: Tuple[str, ...]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        for field_name in (\n            "observation_id",\n            "request_id",\n            "admission_decision_id",\n            "source_id",\n            "canonical_venue_id",\n            "adapter_key",\n            "venue_market_id",\n        ):\n            object.__setattr__(\n                self,\n                field_name,\n                _text(\n                    getattr(self, field_name),\n                    field_name,\n                ),\n            )\n\n        for field_name in (\n            "observation_hash",\n            "request_hash",\n            "admission_decision_record_hash",\n            "source_contract_hash",\n            "source_registry_hash",\n            "raw_payload_hash",\n        ):\n            object.__setattr__(\n                self,\n                field_name,\n                _sha256(\n                    getattr(self, field_name),\n                    field_name,\n                ),\n            )\n\n        if not isinstance(self.retrieval_sequence, int):\n            raise TypeError(\n                "retrieval_sequence must be an integer"\n            )\n        if self.retrieval_sequence < 1:\n            raise ValueError(\n                "retrieval_sequence must be positive"\n            )\n        if not isinstance(self.admitted, bool):\n            raise TypeError("admitted must be boolean")\n\n        frozen_checks = _freeze_checks(self.checks)\n        object.__setattr__(\n            self,\n            "checks",\n            frozen_checks,\n        )\n        normalized_reasons = _normalized_text_tuple(\n            self.rejection_reasons,\n            "rejection_reason",\n        )\n        object.__setattr__(\n            self,\n            "rejection_reasons",\n            normalized_reasons,\n        )\n\n        failed_checks = tuple(\n            sorted(\n                name\n                for name, passed in frozen_checks.items()\n                if not passed\n            )\n        )\n        if self.admitted:\n            if failed_checks:\n                raise ValueError(\n                    "admitted decisions cannot contain failed checks"\n                )\n            if normalized_reasons:\n                raise ValueError(\n                    "admitted decisions cannot contain rejection reasons"\n                )\n        else:\n            if not failed_checks:\n                raise ValueError(\n                    "rejected decisions require at least one failed check"\n                )\n            if normalized_reasons != failed_checks:\n                raise ValueError(\n                    "rejection reasons must exactly match failed checks"\n                )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError(\n                "decision lineage must belong to UMD"\n            )\n        if self.lineage.build_id != UMD_052_BUILD_ID:\n            raise ValueError(\n                "decision lineage must use build_id UMD-052"\n            )\n\n        required_parent_hashes = {\n            self.observation_hash,\n            self.request_hash,\n            self.admission_decision_record_hash,\n            self.source_contract_hash,\n            self.source_registry_hash,\n            self.raw_payload_hash,\n        }\n        if not required_parent_hashes.issubset(\n            set(self.lineage.parent_hashes)\n        ):\n            raise ValueError(\n                "decision lineage must include observation, request, "\n                "request-decision, source-contract, source-registry, "\n                "and raw-payload hashes"\n            )\n\n    @property\n    def decision_id(self) -> str:\n        return (\n            "umd:raw-venue-market-observation-admission-decision:"\n            + deterministic_sha256(\n                {\n                    "observation_id": self.observation_id,\n                    "observation_hash": self.observation_hash,\n                    "admitted": self.admitted,\n                    "checks": self.checks,\n                    "rejection_reasons": self.rejection_reasons,\n                }\n            )\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "decision_id": self.decision_id,\n            "observation_id": self.observation_id,\n            "observation_hash": self.observation_hash,\n            "request_id": self.request_id,\n            "request_hash": self.request_hash,\n            "admission_decision_id": (\n                self.admission_decision_id\n            ),\n            "admission_decision_record_hash": (\n                self.admission_decision_record_hash\n            ),\n            "source_id": self.source_id,\n            "source_contract_hash": self.source_contract_hash,\n            "source_registry_hash": self.source_registry_hash,\n            "raw_payload_hash": self.raw_payload_hash,\n            "canonical_venue_id": self.canonical_venue_id,\n            "adapter_key": self.adapter_key,\n            "venue_market_id": self.venue_market_id,\n            "retrieval_sequence": self.retrieval_sequence,\n            "admitted": self.admitted,\n            "checks": self.checks,\n            "rejection_reasons": self.rejection_reasons,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def record_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef evaluate_raw_venue_market_observation_admission(\n    observation: CertifiedRawVenueMarketObservation,\n    *,\n    seen_observation_ids: Tuple[str, ...] = (),\n    seen_observation_hashes: Tuple[str, ...] = (),\n    seen_source_market_retrieval_keys: Tuple[str, ...] = (),\n    lineage: ImmutableLineage,\n) -> CertifiedRawVenueMarketObservationAdmissionDecision:\n    if not isinstance(\n        observation,\n        CertifiedRawVenueMarketObservation,\n    ):\n        raise TypeError(\n            "observation must be the certified UMD-051 raw observation"\n        )\n\n    certification = certify_raw_venue_market_observation(\n        observation\n    )\n    normalized_ids = set(\n        _normalized_text_tuple(\n            seen_observation_ids,\n            "seen_observation_id",\n        )\n    )\n    normalized_hashes = set(\n        _normalized_hash_tuple(\n            seen_observation_hashes,\n            "seen_observation_hash",\n        )\n    )\n    normalized_retrieval_keys = set(\n        _normalized_text_tuple(\n            seen_source_market_retrieval_keys,\n            "seen_source_market_retrieval_key",\n        )\n    )\n\n    retrieval_key = (\n        f"{observation.source_id}|"\n        f"{observation.venue_market_id}|"\n        f"{observation.retrieval_sequence}"\n    )\n\n    checks = {\n        "observation_contract_certified": (\n            certification["certified"] is True\n        ),\n        "observation_hash_matches_contract": (\n            certification["observation_hash"]\n            == observation.observation_hash\n        ),\n        "observation_identity_matches_contract": (\n            certification["observation_id"]\n            == observation.observation_id\n        ),\n        "raw_payload_hash_matches": (\n            observation.raw_payload_hash\n            == deterministic_sha256(\n                observation.raw_payload\n            )\n        ),\n        "observation_read_only": (\n            observation.read_only is True\n        ),\n        "source_emission_time_valid": (\n            observation.source_emitted_at is None\n            or observation.source_emitted_at\n            <= observation.observed_at\n        ),\n        "observation_id_not_seen": (\n            observation.observation_id\n            not in normalized_ids\n        ),\n        "observation_hash_not_seen": (\n            observation.observation_hash\n            not in normalized_hashes\n        ),\n        "source_market_retrieval_not_seen": (\n            retrieval_key\n            not in normalized_retrieval_keys\n        ),\n        "lineage_build_valid": (\n            observation.lineage.build_id == "UMD-051"\n        ),\n    }\n    rejection_reasons = tuple(\n        sorted(\n            name\n            for name, passed in checks.items()\n            if not passed\n        )\n    )\n    admitted = not rejection_reasons\n\n    return CertifiedRawVenueMarketObservationAdmissionDecision(\n        observation_id=observation.observation_id,\n        observation_hash=observation.observation_hash,\n        request_id=observation.request_id,\n        request_hash=observation.request_hash,\n        admission_decision_id=(\n            observation.admission_decision_id\n        ),\n        admission_decision_record_hash=(\n            observation.admission_decision_record_hash\n        ),\n        source_id=observation.source_id,\n        source_contract_hash=(\n            observation.source_contract_hash\n        ),\n        source_registry_hash=(\n            observation.source_registry_hash\n        ),\n        raw_payload_hash=observation.raw_payload_hash,\n        canonical_venue_id=observation.canonical_venue_id,\n        adapter_key=observation.adapter_key,\n        venue_market_id=observation.venue_market_id,\n        retrieval_sequence=observation.retrieval_sequence,\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=rejection_reasons,\n        lineage=lineage,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD052CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    gate_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "gate_mode": self.gate_mode,\n            "prohibited_capabilities": (\n                self.prohibited_capabilities\n            ),\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_052_certification_manifest() -> UMD052CertificationManifest:\n    return UMD052CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_052_BUILD_ID,\n        revision=UMD_052_REVISION,\n        schema_version=UMD_052_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 52)\n        ),\n        gate_mode=(\n            "deterministic_read_only_raw_observation_admission"\n        ),\n        prohibited_capabilities=(\n            PROHIBITED_CAPABILITIES\n        ),\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_umd_052_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_052_certification_manifest()\n    checks = {\n        "subsystem_identity": (\n            manifest.subsystem_id == "UMD"\n        ),\n        "build_identity": (\n            manifest.build_id == "UMD-052"\n        ),\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 52)\n            )\n        ),\n        "gate_mode": (\n            manifest.gate_mode\n            == "deterministic_read_only_raw_observation_admission"\n        ),\n        "network_disabled": (\n            manifest.network_enabled is False\n        ),\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": (\n            manifest.mutation_enabled is False\n        ),\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": (\n            manifest.execution_enabled is False\n        ),\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_052_raw_venue_market_observation_admission_gate() -> bool:\n    result = certify_umd_052_foundation()\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-052 foundation certification failed: "\n            + ", ".join(result["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom qseries_v2.universal_market_discovery.umd_047_venue_discovery_request_contract import (\n    UMD_047_REVISION,\n    CertifiedVenueDiscoveryRequestContract,\n)\nfrom qseries_v2.universal_market_discovery.umd_048_venue_discovery_request_admission_gate import (\n    UMD_048_REVISION,\n    CertifiedVenueDiscoveryRequestAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.umd_051_raw_venue_market_observation_contract import (\n    UMD_051_REVISION,\n    build_raw_venue_market_observation,\n)\nfrom qseries_v2.universal_market_discovery.umd_052_raw_venue_market_observation_admission_gate import (\n    UMD_052_REVISION,\n    build_umd_052_certification_manifest,\n    certify_umd_052_foundation,\n    evaluate_raw_venue_market_observation_admission,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    7,\n    2,\n    5,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef digest(label: str) -> str:\n    return hashlib.sha256(\n        label.encode("utf-8")\n    ).hexdigest()\n\n\ndef request():\n    source_contract_hash = digest(\n        "umd-052:source-contract"\n    )\n    source_registry_hash = digest(\n        "umd-052:source-registry"\n    )\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-047",\n        revision=UMD_047_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            source_contract_hash,\n            source_registry_hash,\n        ),\n        source_refs=("fixture://umd-052/request",),\n        created_at=FIXED,\n    )\n    return CertifiedVenueDiscoveryRequestContract(\n        source_id="source-kalshi",\n        source_contract_hash=source_contract_hash,\n        source_registry_hash=source_registry_hash,\n        canonical_venue_id="KALSHI",\n        adapter_key="KALSHI_MARKET_CATALOG",\n        discovery_scope="ACTIVE_ONLY",\n        requested_statuses=("ACTIVE",),\n        requested_market_families=("BINARY_MARKET",),\n        window_start=None,\n        window_end=None,\n        pagination_cursor=None,\n        page_size=100,\n        requested_at=FIXED,\n        request_schema_version="v1",\n        read_only=True,\n        metadata={"certification_only": True},\n        lineage=lineage,\n    )\n\n\ndef request_decision(item):\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-048",\n        revision=UMD_048_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            item.request_hash,\n            item.source_contract_hash,\n            item.source_registry_hash,\n        ),\n        source_refs=(\n            "fixture://umd-052/request-decision",\n        ),\n        created_at=FIXED,\n    )\n    return CertifiedVenueDiscoveryRequestAdmissionDecision(\n        request_id=item.request_id,\n        request_hash=item.request_hash,\n        source_id=item.source_id,\n        source_contract_hash=(\n            item.source_contract_hash\n        ),\n        source_registry_hash=(\n            item.source_registry_hash\n        ),\n        admitted=True,\n        checks={"request_certified": True},\n        rejection_reasons=(),\n        lineage=lineage,\n    )\n\n\ndef observation():\n    item = request()\n    gate = request_decision(item)\n    payload = {\n        "ticker": "KXBTC-26AUG07-T100000",\n        "title": "Will Bitcoin exceed 100000?",\n        "status": "active",\n        "yes_bid": 41,\n        "yes_ask": 43,\n    }\n    payload_hash = deterministic_sha256(payload)\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-051",\n        revision=UMD_051_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            item.request_hash,\n            gate.record_hash,\n            item.source_contract_hash,\n            item.source_registry_hash,\n            payload_hash,\n        ),\n        source_refs=(\n            "fixture://umd-052/observation",\n        ),\n        created_at=FIXED,\n    )\n    return build_raw_venue_market_observation(\n        item,\n        gate,\n        venue_market_id="KXBTC-26AUG07-T100000",\n        venue_event_id="KXBTC",\n        source_record_type="MARKET",\n        raw_title="Will Bitcoin exceed 100000?",\n        raw_status="active",\n        raw_market_family="binary",\n        source_schema_version="kalshi-v1",\n        raw_payload=payload,\n        retrieval_sequence=1,\n        observed_at=FIXED,\n        source_emitted_at=FIXED,\n        metadata={"network_enabled": False},\n        lineage=lineage,\n    )\n\n\ndef gate_lineage(item):\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-052",\n        revision=UMD_052_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            item.observation_hash,\n            item.request_hash,\n            item.admission_decision_record_hash,\n            item.source_contract_hash,\n            item.source_registry_hash,\n            item.raw_payload_hash,\n        ),\n        source_refs=(\n            "fixture://umd-052/gate",\n        ),\n        created_at=FIXED,\n    )\n\n\nclass TestUMD052(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_052_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-052")\n\n    def test_valid_observation_admitted(self) -> None:\n        item = observation()\n        decision = evaluate_raw_venue_market_observation_admission(\n            item,\n            lineage=gate_lineage(item),\n        )\n        self.assertTrue(decision.admitted)\n        self.assertEqual(decision.rejection_reasons, ())\n        self.assertTrue(all(decision.checks.values()))\n\n    def test_deterministic(self) -> None:\n        item = observation()\n        lineage = gate_lineage(item)\n        first = evaluate_raw_venue_market_observation_admission(\n            item,\n            lineage=lineage,\n        )\n        second = evaluate_raw_venue_market_observation_admission(\n            item,\n            lineage=lineage,\n        )\n        self.assertEqual(first.decision_id, second.decision_id)\n        self.assertEqual(first.record_hash, second.record_hash)\n\n    def test_duplicate_observation_id_rejected(self) -> None:\n        item = observation()\n        decision = evaluate_raw_venue_market_observation_admission(\n            item,\n            seen_observation_ids=(item.observation_id,),\n            lineage=gate_lineage(item),\n        )\n        self.assertFalse(decision.admitted)\n        self.assertIn(\n            "observation_id_not_seen",\n            decision.rejection_reasons,\n        )\n\n    def test_duplicate_observation_hash_rejected(self) -> None:\n        item = observation()\n        decision = evaluate_raw_venue_market_observation_admission(\n            item,\n            seen_observation_hashes=(\n                item.observation_hash,\n            ),\n            lineage=gate_lineage(item),\n        )\n        self.assertFalse(decision.admitted)\n        self.assertIn(\n            "observation_hash_not_seen",\n            decision.rejection_reasons,\n        )\n\n    def test_duplicate_retrieval_rejected(self) -> None:\n        item = observation()\n        key = (\n            f"{item.source_id}|"\n            f"{item.venue_market_id}|"\n            f"{item.retrieval_sequence}"\n        )\n        decision = evaluate_raw_venue_market_observation_admission(\n            item,\n            seen_source_market_retrieval_keys=(key,),\n            lineage=gate_lineage(item),\n        )\n        self.assertFalse(decision.admitted)\n        self.assertIn(\n            "source_market_retrieval_not_seen",\n            decision.rejection_reasons,\n        )\n\n    def test_lineage_requires_all_hashes(self) -> None:\n        item = observation()\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-052",\n            revision=UMD_052_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(\n                item.observation_hash,\n            ),\n            source_refs=(\n                "fixture://umd-052/bad",\n            ),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            evaluate_raw_venue_market_observation_admission(\n                item,\n                lineage=bad,\n            )\n\n    def test_immutable(self) -> None:\n        item = observation()\n        decision = evaluate_raw_venue_market_observation_admission(\n            item,\n            lineage=gate_lineage(item),\n        )\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            decision.admitted = False\n        with self.assertRaises(TypeError):\n            decision.checks["changed"] = False\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_052_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-052 CERTIFICATION TEST")\n    print(\n        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION GATE"\n    )\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD052\n    )\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_052_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-051 consumed read-only")\n    print("[PASS] Exact UMD-051 raw-observation class consumed")\n    print("[PASS] Deterministic observation-admission decision certified")\n    print("[PASS] Duplicate observation ID, hash, and retrieval replay rejected")\n    print("[PASS] Immutable complete decision lineage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-052 CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION GATE CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_052_raw_venue_market_observation_admission_gate import (\n    UMD_052_BUILD_ID,\n    UMD_052_BUILD_NAME,\n    UMD_052_REVISION,\n    UMD_052_SCHEMA_VERSION,\n    CertifiedRawVenueMarketObservationAdmissionDecision,\n    UMD052CertificationManifest,\n    evaluate_raw_venue_market_observation_admission,\n    build_umd_052_certification_manifest,\n    certify_umd_052_foundation,\n    verify_umd_052_raw_venue_market_observation_admission_gate,\n)\n'
EXPORTED_NAMES = ('UMD_052_BUILD_ID', 'UMD_052_BUILD_NAME', 'UMD_052_REVISION', 'UMD_052_SCHEMA_VERSION', 'CertifiedRawVenueMarketObservationAdmissionDecision', 'UMD052CertificationManifest', 'evaluate_raw_venue_market_observation_admission', 'build_umd_052_certification_manifest', 'certify_umd_052_foundation', 'verify_umd_052_raw_venue_market_observation_admission_gate')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'), ('umd_045_venue_discovery_source_contract', 'verify_umd_045_venue_discovery_source_contract'), ('umd_046_venue_discovery_source_registry', 'verify_umd_046_venue_discovery_source_registry'), ('umd_047_venue_discovery_request_contract', 'verify_umd_047_venue_discovery_request_contract'), ('umd_048_venue_discovery_request_admission_gate', 'verify_umd_048_venue_discovery_request_admission_gate'), ('umd_049_venue_discovery_request_admission_ledger', 'verify_umd_049_venue_discovery_request_admission_ledger'), ('umd_050_venue_discovery_request_admission_ledger_read_model', 'verify_umd_050_venue_discovery_request_admission_ledger_read_model'), ('umd_051_raw_venue_market_observation_contract', 'verify_umd_051_raw_venue_market_observation_contract'))


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
        "from .umd_052_raw_venue_market_"
        "observation_admission_gate import ("
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
            "umd_052_raw_venue_market_observation_admission_gate"
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
                "UMD-052 missing symbols: "
                + ", ".join(missing)
            )

        if module.verify_umd_052_raw_venue_market_observation_admission_gate() is not True:
            raise RuntimeError(
                "UMD-052 verification returned false"
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
    print(" UMD-052 REPOSITORY-VERIFIED INSTALLER")
    print(
        " CERTIFIED RAW VENUE MARKET OBSERVATION ADMISSION GATE"
    )
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-051 "
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
                "[ROLLBACK] UMD-052 installation failed; "
                "all affected files restored"
            )
        raise

    manifest = {
        "build_id": "UMD-052",
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
            for number in range(1, 52)
        ),
        "mode": (
            "deterministic_read_only_raw_observation_admission"
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

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required UMD-052 symbols verified")
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-052 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
