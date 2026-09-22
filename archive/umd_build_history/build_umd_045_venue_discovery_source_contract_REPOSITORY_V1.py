from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_045_CERTIFIED_VENUE_DISCOVERY_SOURCE_CONTRACT_REPOSITORY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_045_venue_discovery_source_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_045_venue_discovery_source_contract.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\n\nUMD_045_BUILD_ID = "UMD-045"\nUMD_045_BUILD_NAME = "Certified Venue Discovery Source Contract"\nUMD_045_REVISION = (\n    "UMD_045_CERTIFIED_VENUE_DISCOVERY_SOURCE_CONTRACT_V1"\n)\nUMD_045_SCHEMA_VERSION = "1.0.0"\n\nALLOWED_DISCOVERY_METHODS = (\n    "REST_CATALOG",\n    "GRAPHQL_CATALOG",\n    "WEBSOCKET_CATALOG",\n    "FILE_CATALOG",\n    "DATABASE_CATALOG",\n    "MANUAL_IMPORT",\n)\n\nALLOWED_AUTHENTICATION_MODES = (\n    "NONE",\n    "API_KEY",\n    "BEARER_TOKEN",\n    "OAUTH2",\n    "SIGNED_REQUEST",\n    "SESSION_COOKIE",\n)\n\nALLOWED_PAGINATION_MODES = (\n    "NONE",\n    "OFFSET",\n    "PAGE_NUMBER",\n    "CURSOR",\n    "TOKEN",\n    "TIME_WINDOW",\n)\n\nALLOWED_MARKET_STATUS_CAPABILITIES = (\n    "ACTIVE",\n    "INACTIVE",\n    "CLOSED",\n    "SETTLED",\n    "CANCELLED",\n    "ARCHIVED",\n)\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "credential_resolution",\n    "market_scanning",\n    "continuous_runtime",\n    "automatic_discovery",\n    "automatic_admission",\n    "registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _token(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).upper().replace("-", "_")\n    if not all(\n        character.isalnum() or character == "_"\n        for character in normalized\n    ):\n        raise ValueError(\n            f"{field_name} must contain only letters, numbers, and underscores"\n        )\n    return normalized\n\n\ndef _sorted_unique_tokens(\n    values: Tuple[str, ...],\n    field_name: str,\n) -> Tuple[str, ...]:\n    if not isinstance(values, tuple):\n        values = tuple(values)\n    normalized = tuple(\n        sorted(\n            {\n                _token(value, field_name)\n                for value in values\n            }\n        )\n    )\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:\n    if not isinstance(value, Mapping):\n        raise TypeError("metadata must be a mapping")\n    return MappingProxyType(\n        dict(\n            sorted(\n                (str(key), item)\n                for key, item in value.items()\n            )\n        )\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedVenueDiscoverySourceContract:\n    canonical_venue_id: str\n    adapter_key: str\n    display_name: str\n    discovery_method: str\n    authentication_mode: str\n    pagination_mode: str\n    supported_market_families: Tuple[str, ...]\n    supported_statuses: Tuple[str, ...]\n    source_schema_version: str\n    supports_incremental_discovery: bool\n    supports_historical_markets: bool\n    supports_settlement_status: bool\n    supports_cursor_resume: bool\n    rate_limit_metadata_available: bool\n    read_only: bool\n    metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        object.__setattr__(\n            self,\n            "canonical_venue_id",\n            _token(self.canonical_venue_id, "canonical_venue_id"),\n        )\n        object.__setattr__(\n            self,\n            "adapter_key",\n            _token(self.adapter_key, "adapter_key"),\n        )\n        object.__setattr__(\n            self,\n            "display_name",\n            _text(self.display_name, "display_name"),\n        )\n\n        discovery_method = _token(\n            self.discovery_method,\n            "discovery_method",\n        )\n        if discovery_method not in ALLOWED_DISCOVERY_METHODS:\n            raise ValueError(\n                "discovery_method is not certified"\n            )\n        object.__setattr__(\n            self,\n            "discovery_method",\n            discovery_method,\n        )\n\n        authentication_mode = _token(\n            self.authentication_mode,\n            "authentication_mode",\n        )\n        if authentication_mode not in ALLOWED_AUTHENTICATION_MODES:\n            raise ValueError(\n                "authentication_mode is not certified"\n            )\n        object.__setattr__(\n            self,\n            "authentication_mode",\n            authentication_mode,\n        )\n\n        pagination_mode = _token(\n            self.pagination_mode,\n            "pagination_mode",\n        )\n        if pagination_mode not in ALLOWED_PAGINATION_MODES:\n            raise ValueError(\n                "pagination_mode is not certified"\n            )\n        object.__setattr__(\n            self,\n            "pagination_mode",\n            pagination_mode,\n        )\n\n        object.__setattr__(\n            self,\n            "supported_market_families",\n            _sorted_unique_tokens(\n                self.supported_market_families,\n                "supported_market_family",\n            ),\n        )\n\n        statuses = _sorted_unique_tokens(\n            self.supported_statuses,\n            "supported_status",\n        )\n        unknown_statuses = tuple(\n            status\n            for status in statuses\n            if status not in ALLOWED_MARKET_STATUS_CAPABILITIES\n        )\n        if unknown_statuses:\n            raise ValueError(\n                "unsupported market statuses: "\n                + ", ".join(unknown_statuses)\n            )\n        object.__setattr__(\n            self,\n            "supported_statuses",\n            statuses,\n        )\n\n        object.__setattr__(\n            self,\n            "source_schema_version",\n            _text(\n                self.source_schema_version,\n                "source_schema_version",\n            ),\n        )\n\n        for field_name in (\n            "supports_incremental_discovery",\n            "supports_historical_markets",\n            "supports_settlement_status",\n            "supports_cursor_resume",\n            "rate_limit_metadata_available",\n            "read_only",\n        ):\n            if not isinstance(getattr(self, field_name), bool):\n                raise TypeError(f"{field_name} must be boolean")\n\n        if self.read_only is not True:\n            raise ValueError(\n                "venue discovery source contracts must be read-only"\n            )\n\n        if (\n            self.supports_cursor_resume\n            and self.pagination_mode not in ("CURSOR", "TOKEN")\n        ):\n            raise ValueError(\n                "cursor resume requires CURSOR or TOKEN pagination"\n            )\n\n        object.__setattr__(\n            self,\n            "metadata",\n            _freeze(self.metadata),\n        )\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError(\n                "source-contract lineage must belong to UMD"\n            )\n        if self.lineage.build_id != UMD_045_BUILD_ID:\n            raise ValueError(\n                "source-contract lineage must use build_id UMD-045"\n            )\n\n    @property\n    def source_id(self) -> str:\n        return "umd:venue-discovery-source:" + deterministic_sha256(\n            {\n                "canonical_venue_id": self.canonical_venue_id,\n                "adapter_key": self.adapter_key,\n                "discovery_method": self.discovery_method,\n                "source_schema_version": self.source_schema_version,\n            }\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "source_id": self.source_id,\n            "canonical_venue_id": self.canonical_venue_id,\n            "adapter_key": self.adapter_key,\n            "display_name": self.display_name,\n            "discovery_method": self.discovery_method,\n            "authentication_mode": self.authentication_mode,\n            "pagination_mode": self.pagination_mode,\n            "supported_market_families": (\n                self.supported_market_families\n            ),\n            "supported_statuses": self.supported_statuses,\n            "source_schema_version": self.source_schema_version,\n            "supports_incremental_discovery": (\n                self.supports_incremental_discovery\n            ),\n            "supports_historical_markets": (\n                self.supports_historical_markets\n            ),\n            "supports_settlement_status": (\n                self.supports_settlement_status\n            ),\n            "supports_cursor_resume": self.supports_cursor_resume,\n            "rate_limit_metadata_available": (\n                self.rate_limit_metadata_available\n            ),\n            "read_only": self.read_only,\n            "metadata": self.metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def contract_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD045CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    contract_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "contract_mode": self.contract_mode,\n            "prohibited_capabilities": self.prohibited_capabilities,\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(\n            self.to_canonical_dict()\n        )\n\n\ndef build_umd_045_certification_manifest() -> UMD045CertificationManifest:\n    return UMD045CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_045_BUILD_ID,\n        revision=UMD_045_REVISION,\n        schema_version=UMD_045_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}"\n            for number in range(1, 45)\n        ),\n        contract_mode="deterministic_read_only_source_definition",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_venue_discovery_source_contract(\n    source: CertifiedVenueDiscoverySourceContract,\n) -> Mapping[str, Any]:\n    if not isinstance(\n        source,\n        CertifiedVenueDiscoverySourceContract,\n    ):\n        raise TypeError(\n            "source must be a certified UMD-045 source contract"\n        )\n\n    checks = {\n        "source_identity_deterministic": (\n            source.source_id\n            == "umd:venue-discovery-source:"\n            + deterministic_sha256(\n                {\n                    "canonical_venue_id": source.canonical_venue_id,\n                    "adapter_key": source.adapter_key,\n                    "discovery_method": source.discovery_method,\n                    "source_schema_version": (\n                        source.source_schema_version\n                    ),\n                }\n            )\n        ),\n        "contract_hash_deterministic": (\n            source.contract_hash\n            == deterministic_sha256(\n                source.to_canonical_dict()\n            )\n        ),\n        "read_only_required": source.read_only is True,\n        "market_families_present": (\n            bool(source.supported_market_families)\n        ),\n        "statuses_present": bool(source.supported_statuses),\n        "lineage_build_valid": (\n            source.lineage.build_id == UMD_045_BUILD_ID\n        ),\n        "network_not_invoked": True,\n    }\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "source_id": source.source_id,\n            "contract_hash": source.contract_hash,\n            "canonical_venue_id": source.canonical_venue_id,\n            "adapter_key": source.adapter_key,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_045_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_045_certification_manifest()\n    checks = {\n        "subsystem_identity": manifest.subsystem_id == "UMD",\n        "build_identity": manifest.build_id == "UMD-045",\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}"\n                for number in range(1, 45)\n            )\n        ),\n        "source_contract_mode": (\n            manifest.contract_mode\n            == "deterministic_read_only_source_definition"\n        ),\n        "network_disabled": manifest.network_enabled is False,\n        "persistence_disabled": (\n            manifest.persistence_enabled is False\n        ),\n        "mutation_disabled": manifest.mutation_enabled is False,\n        "publication_disabled": (\n            manifest.publication_enabled is False\n        ),\n        "execution_disabled": manifest.execution_enabled is False,\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(\n                manifest.to_canonical_dict()\n            )\n        ),\n    }\n    failed = tuple(\n        name\n        for name, passed in checks.items()\n        if not passed\n    )\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_045_venue_discovery_source_contract() -> bool:\n    result = certify_umd_045_foundation()\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-045 foundation certification failed: "\n            + ", ".join(result["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_045_venue_discovery_source_contract import (\n    UMD_045_REVISION,\n    CertifiedVenueDiscoverySourceContract,\n    build_umd_045_certification_manifest,\n    certify_umd_045_foundation,\n    certify_venue_discovery_source_contract,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    6,\n    19,\n    45,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef lineage() -> ImmutableLineage:\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-045",\n        revision=UMD_045_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(),\n        source_refs=(\n            "fixture://umd-045/source-contract",\n        ),\n        created_at=FIXED,\n    )\n\n\ndef source_contract() -> CertifiedVenueDiscoverySourceContract:\n    return CertifiedVenueDiscoverySourceContract(\n        canonical_venue_id="KALSHI",\n        adapter_key="KALSHI_MARKET_CATALOG",\n        display_name="Kalshi Market Catalog",\n        discovery_method="REST_CATALOG",\n        authentication_mode="API_KEY",\n        pagination_mode="CURSOR",\n        supported_market_families=(\n            "EVENT_CONTRACT",\n            "BINARY_MARKET",\n        ),\n        supported_statuses=(\n            "ACTIVE",\n            "CLOSED",\n            "SETTLED",\n        ),\n        source_schema_version="kalshi-market-catalog-v1",\n        supports_incremental_discovery=True,\n        supports_historical_markets=True,\n        supports_settlement_status=True,\n        supports_cursor_resume=True,\n        rate_limit_metadata_available=True,\n        read_only=True,\n        metadata={\n            "network_enabled": False,\n            "certification_only": True,\n        },\n        lineage=lineage(),\n    )\n\n\nclass TestUMD045(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_045_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-045")\n\n    def test_contract_certifies(self) -> None:\n        source = source_contract()\n        result = certify_venue_discovery_source_contract(source)\n        self.assertTrue(result["certified"])\n        self.assertEqual(\n            result["canonical_venue_id"],\n            "KALSHI",\n        )\n\n    def test_deterministic_identity(self) -> None:\n        first = source_contract()\n        second = source_contract()\n        self.assertEqual(first.source_id, second.source_id)\n        self.assertEqual(\n            first.contract_hash,\n            second.contract_hash,\n        )\n\n    def test_normalization(self) -> None:\n        source = CertifiedVenueDiscoverySourceContract(\n            canonical_venue_id="kalshi",\n            adapter_key="kalshi-market-catalog",\n            display_name="  Kalshi   Market Catalog ",\n            discovery_method="rest-catalog",\n            authentication_mode="api-key",\n            pagination_mode="cursor",\n            supported_market_families=(\n                "binary-market",\n                "event-contract",\n                "binary-market",\n            ),\n            supported_statuses=(\n                "settled",\n                "active",\n                "closed",\n            ),\n            source_schema_version="v1",\n            supports_incremental_discovery=True,\n            supports_historical_markets=True,\n            supports_settlement_status=True,\n            supports_cursor_resume=True,\n            rate_limit_metadata_available=True,\n            read_only=True,\n            metadata={},\n            lineage=lineage(),\n        )\n        self.assertEqual(source.canonical_venue_id, "KALSHI")\n        self.assertEqual(\n            source.supported_market_families,\n            ("BINARY_MARKET", "EVENT_CONTRACT"),\n        )\n        self.assertEqual(\n            source.supported_statuses,\n            ("ACTIVE", "CLOSED", "SETTLED"),\n        )\n\n    def test_cursor_resume_requires_cursor_mode(self) -> None:\n        with self.assertRaises(ValueError):\n            CertifiedVenueDiscoverySourceContract(\n                canonical_venue_id="TEST",\n                adapter_key="TEST_SOURCE",\n                display_name="Test Source",\n                discovery_method="REST_CATALOG",\n                authentication_mode="NONE",\n                pagination_mode="OFFSET",\n                supported_market_families=(\n                    "BINARY_MARKET",\n                ),\n                supported_statuses=("ACTIVE",),\n                source_schema_version="v1",\n                supports_incremental_discovery=True,\n                supports_historical_markets=False,\n                supports_settlement_status=False,\n                supports_cursor_resume=True,\n                rate_limit_metadata_available=False,\n                read_only=True,\n                metadata={},\n                lineage=lineage(),\n            )\n\n    def test_read_only_required(self) -> None:\n        with self.assertRaises(ValueError):\n            CertifiedVenueDiscoverySourceContract(\n                canonical_venue_id="TEST",\n                adapter_key="TEST_SOURCE",\n                display_name="Test Source",\n                discovery_method="FILE_CATALOG",\n                authentication_mode="NONE",\n                pagination_mode="NONE",\n                supported_market_families=(\n                    "BINARY_MARKET",\n                ),\n                supported_statuses=("ACTIVE",),\n                source_schema_version="v1",\n                supports_incremental_discovery=False,\n                supports_historical_markets=False,\n                supports_settlement_status=False,\n                supports_cursor_resume=False,\n                rate_limit_metadata_available=False,\n                read_only=False,\n                metadata={},\n                lineage=lineage(),\n            )\n\n    def test_immutable(self) -> None:\n        source = source_contract()\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            source.display_name = "Changed"\n        with self.assertRaises(TypeError):\n            source.metadata["network_enabled"] = True\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_045_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-045 CERTIFICATION TEST")\n    print(" CERTIFIED VENUE DISCOVERY SOURCE CONTRACT")\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD045\n    )\n    result = unittest.TextTestRunner(\n        verbosity=2\n    ).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_045_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-044 consumed read-only")\n    print("[PASS] Deterministic venue discovery source identity certified")\n    print("[PASS] Supported families and statuses normalized")\n    print("[PASS] Authentication and pagination capabilities certified")\n    print("[PASS] Read-only source definition enforced")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-045 CERTIFIED VENUE DISCOVERY SOURCE CONTRACT CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_045_venue_discovery_source_contract import (\n    UMD_045_BUILD_ID,\n    UMD_045_BUILD_NAME,\n    UMD_045_REVISION,\n    UMD_045_SCHEMA_VERSION,\n    ALLOWED_DISCOVERY_METHODS,\n    ALLOWED_AUTHENTICATION_MODES,\n    ALLOWED_PAGINATION_MODES,\n    ALLOWED_MARKET_STATUS_CAPABILITIES,\n    CertifiedVenueDiscoverySourceContract,\n    UMD045CertificationManifest,\n    build_umd_045_certification_manifest,\n    certify_venue_discovery_source_contract,\n    certify_umd_045_foundation,\n    verify_umd_045_venue_discovery_source_contract,\n)\n'
EXPORTED_NAMES = ('UMD_045_BUILD_ID', 'UMD_045_BUILD_NAME', 'UMD_045_REVISION', 'UMD_045_SCHEMA_VERSION', 'ALLOWED_DISCOVERY_METHODS', 'ALLOWED_AUTHENTICATION_MODES', 'ALLOWED_PAGINATION_MODES', 'ALLOWED_MARKET_STATUS_CAPABILITIES', 'CertifiedVenueDiscoverySourceContract', 'UMD045CertificationManifest', 'build_umd_045_certification_manifest', 'certify_venue_discovery_source_contract', 'certify_umd_045_foundation', 'verify_umd_045_venue_discovery_source_contract')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'))


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
        "from .umd_045_venue_discovery_source_contract import ("
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
            "umd_045_venue_discovery_source_contract"
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
                "UMD-045 missing symbols: "
                + ", ".join(missing)
            )

        if module.verify_umd_045_venue_discovery_source_contract() is not True:
            raise RuntimeError(
                "UMD-045 verification returned false"
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
    print(" UMD-045 REPOSITORY-VERIFIED INSTALLER")
    print(" CERTIFIED VENUE DISCOVERY SOURCE CONTRACT")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-044 "
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
                "[ROLLBACK] UMD-045 installation failed; "
                "all affected files restored"
            )
        raise

    manifest = {
        "build_id": "UMD-045",
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
            for number in range(1, 45)
        ),
        "mode": "deterministic_read_only_source_definition",
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
    print("[PASS] Required UMD-045 symbols verified")
    print(
        f"[PASS] Deterministic install hash: "
        f"{install_hash}"
    )
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-045 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
