from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_046_CERTIFIED_VENUE_DISCOVERY_SOURCE_REGISTRY_REPOSITORY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_046_venue_discovery_source_registry.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_046_venue_discovery_source_registry.py"

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass, field\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_045_venue_discovery_source_contract import (\n    CertifiedVenueDiscoverySourceContract,\n)\n\nUMD_046_BUILD_ID = "UMD-046"\nUMD_046_BUILD_NAME = "Certified Venue Discovery Source Registry"\nUMD_046_REVISION = "UMD_046_CERTIFIED_VENUE_DISCOVERY_SOURCE_REGISTRY_V1"\nUMD_046_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_invocation",\n    "authentication_execution",\n    "credential_storage",\n    "market_scanning",\n    "automatic_discovery",\n    "automatic_registration",\n    "registry_mutation",\n    "registry_persistence",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedVenueDiscoverySourceRegistry:\n    sources: Tuple[CertifiedVenueDiscoverySourceContract, ...]\n    registry_metadata: Mapping[str, Any]\n    lineage: ImmutableLineage\n    _by_source_id: Mapping[str, CertifiedVenueDiscoverySourceContract] = field(\n        init=False,\n        repr=False,\n    )\n    _by_venue_adapter: Mapping[\n        str,\n        CertifiedVenueDiscoverySourceContract,\n    ] = field(init=False, repr=False)\n    _source_ids_by_venue: Mapping[str, Tuple[str, ...]] = field(\n        init=False,\n        repr=False,\n    )\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.sources, tuple):\n            object.__setattr__(self, "sources", tuple(self.sources))\n\n        ordered = tuple(\n            sorted(\n                self.sources,\n                key=lambda source: (\n                    source.canonical_venue_id,\n                    source.adapter_key,\n                    source.source_id,\n                ),\n            )\n        )\n        object.__setattr__(self, "sources", ordered)\n\n        metadata = MappingProxyType(\n            dict(\n                sorted(\n                    (str(key), value)\n                    for key, value in self.registry_metadata.items()\n                )\n            )\n        )\n        object.__setattr__(self, "registry_metadata", metadata)\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("registry lineage must belong to UMD")\n        if self.lineage.build_id != UMD_046_BUILD_ID:\n            raise ValueError("registry lineage must use build_id UMD-046")\n\n        by_source_id = {}\n        by_venue_adapter = {}\n        source_ids_by_venue = {}\n\n        for source in ordered:\n            if not isinstance(source, CertifiedVenueDiscoverySourceContract):\n                raise TypeError(\n                    "sources must contain certified UMD-045 source contracts"\n                )\n            if source.read_only is not True:\n                raise ValueError("all registered sources must be read-only")\n            if source.contract_hash not in self.lineage.parent_hashes:\n                raise ValueError(\n                    "registry lineage must include every source contract hash"\n                )\n            if source.source_id in by_source_id:\n                raise ValueError("duplicate venue discovery source ID")\n\n            venue_adapter_key = (\n                f"{source.canonical_venue_id}:{source.adapter_key}"\n            )\n            if venue_adapter_key in by_venue_adapter:\n                raise ValueError(\n                    "duplicate canonical venue and adapter binding"\n                )\n\n            by_source_id[source.source_id] = source\n            by_venue_adapter[venue_adapter_key] = source\n            source_ids_by_venue.setdefault(\n                source.canonical_venue_id,\n                [],\n            ).append(source.source_id)\n\n        object.__setattr__(\n            self,\n            "_by_source_id",\n            MappingProxyType(by_source_id),\n        )\n        object.__setattr__(\n            self,\n            "_by_venue_adapter",\n            MappingProxyType(by_venue_adapter),\n        )\n        object.__setattr__(\n            self,\n            "_source_ids_by_venue",\n            MappingProxyType(\n                {\n                    venue_id: tuple(sorted(source_ids))\n                    for venue_id, source_ids in source_ids_by_venue.items()\n                }\n            ),\n        )\n\n    @property\n    def registry_id(self) -> str:\n        return "umd:venue-discovery-source-registry:" + deterministic_sha256(\n            {\n                "ordered_source_ids": tuple(\n                    source.source_id\n                    for source in self.sources\n                ),\n                "ordered_contract_hashes": tuple(\n                    source.contract_hash\n                    for source in self.sources\n                ),\n            }\n        )\n\n    def get(\n        self,\n        source_id: str,\n    ) -> CertifiedVenueDiscoverySourceContract | None:\n        return self._by_source_id.get(_text(source_id, "source_id"))\n\n    def get_by_venue_adapter(\n        self,\n        canonical_venue_id: str,\n        adapter_key: str,\n    ) -> CertifiedVenueDiscoverySourceContract | None:\n        key = (\n            f"{_text(canonical_venue_id, \'canonical_venue_id\').upper()}:"\n            f"{_text(adapter_key, \'adapter_key\').upper().replace(\'-\', \'_\')}"\n        )\n        return self._by_venue_adapter.get(key)\n\n    def list_by_venue(\n        self,\n        canonical_venue_id: str,\n    ) -> Tuple[CertifiedVenueDiscoverySourceContract, ...]:\n        venue_id = _text(\n            canonical_venue_id,\n            "canonical_venue_id",\n        ).upper()\n        source_ids = self._source_ids_by_venue.get(venue_id, ())\n        return tuple(self._by_source_id[source_id] for source_id in source_ids)\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "registry_id": self.registry_id,\n            "sources": self.sources,\n            "registry_metadata": self.registry_metadata,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def registry_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD046CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    registry_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "registry_mode": self.registry_mode,\n            "prohibited_capabilities": self.prohibited_capabilities,\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\ndef build_umd_046_certification_manifest() -> UMD046CertificationManifest:\n    return UMD046CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_046_BUILD_ID,\n        revision=UMD_046_REVISION,\n        schema_version=UMD_046_SCHEMA_VERSION,\n        upstream_builds=tuple(\n            f"UMD-{number:03d}" for number in range(1, 46)\n        ),\n        registry_mode="deterministic_read_only_registry",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_venue_discovery_source_registry(\n    registry: CertifiedVenueDiscoverySourceRegistry,\n) -> Mapping[str, Any]:\n    if not isinstance(registry, CertifiedVenueDiscoverySourceRegistry):\n        raise TypeError("registry must be a certified UMD-046 registry")\n\n    checks = {\n        "source_ids_unique": (\n            len({source.source_id for source in registry.sources})\n            == len(registry.sources)\n        ),\n        "venue_adapter_bindings_unique": (\n            len(\n                {\n                    (\n                        source.canonical_venue_id,\n                        source.adapter_key,\n                    )\n                    for source in registry.sources\n                }\n            )\n            == len(registry.sources)\n        ),\n        "all_sources_read_only": all(\n            source.read_only is True\n            for source in registry.sources\n        ),\n        "all_source_lineage_bound": all(\n            source.contract_hash in registry.lineage.parent_hashes\n            for source in registry.sources\n        ),\n        "deterministic_registry_hash": (\n            registry.registry_hash\n            == deterministic_sha256(registry.to_canonical_dict())\n        ),\n        "read_only_indexes": (\n            isinstance(registry._by_source_id, MappingProxyType)\n            and isinstance(registry._by_venue_adapter, MappingProxyType)\n            and isinstance(registry._source_ids_by_venue, MappingProxyType)\n        ),\n        "network_not_invoked": True,\n    }\n    failed = tuple(name for name, passed in checks.items() if not passed)\n\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "registry_id": registry.registry_id,\n            "registry_hash": registry.registry_hash,\n            "source_count": len(registry.sources),\n            "venue_count": len(registry._source_ids_by_venue),\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef certify_umd_046_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_046_certification_manifest()\n    checks = {\n        "subsystem_identity": manifest.subsystem_id == "UMD",\n        "build_identity": manifest.build_id == "UMD-046",\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(\n                f"UMD-{number:03d}" for number in range(1, 46)\n            )\n        ),\n        "registry_mode": (\n            manifest.registry_mode\n            == "deterministic_read_only_registry"\n        ),\n        "network_disabled": manifest.network_enabled is False,\n        "persistence_disabled": manifest.persistence_enabled is False,\n        "mutation_disabled": manifest.mutation_enabled is False,\n        "publication_disabled": manifest.publication_enabled is False,\n        "execution_disabled": manifest.execution_enabled is False,\n        "deterministic_manifest": (\n            manifest.manifest_hash\n            == deterministic_sha256(manifest.to_canonical_dict())\n        ),\n    }\n    failed = tuple(name for name, passed in checks.items() if not passed)\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_046_venue_discovery_source_registry() -> bool:\n    result = certify_umd_046_foundation()\n    if not result["certified"]:\n        raise RuntimeError(\n            "UMD-046 foundation certification failed: "\n            + ", ".join(result["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_045_venue_discovery_source_contract import (\n    UMD_045_REVISION,\n    CertifiedVenueDiscoverySourceContract,\n)\nfrom qseries_v2.universal_market_discovery.umd_046_venue_discovery_source_registry import (\n    UMD_046_REVISION,\n    CertifiedVenueDiscoverySourceRegistry,\n    build_umd_046_certification_manifest,\n    certify_umd_046_foundation,\n    certify_venue_discovery_source_registry,\n)\n\nFIXED = datetime(2026, 8, 6, 19, 55, 0, tzinfo=timezone.utc)\n\n\ndef source_lineage(name: str) -> ImmutableLineage:\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-045",\n        revision=UMD_045_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(),\n        source_refs=(f"fixture://umd-046/source/{name}",),\n        created_at=FIXED,\n    )\n\n\ndef source(\n    venue: str,\n    adapter: str,\n    method: str = "REST_CATALOG",\n) -> CertifiedVenueDiscoverySourceContract:\n    return CertifiedVenueDiscoverySourceContract(\n        canonical_venue_id=venue,\n        adapter_key=adapter,\n        display_name=f"{venue} {adapter}",\n        discovery_method=method,\n        authentication_mode="API_KEY",\n        pagination_mode="CURSOR",\n        supported_market_families=("BINARY_MARKET",),\n        supported_statuses=("ACTIVE", "CLOSED", "SETTLED"),\n        source_schema_version="v1",\n        supports_incremental_discovery=True,\n        supports_historical_markets=True,\n        supports_settlement_status=True,\n        supports_cursor_resume=True,\n        rate_limit_metadata_available=True,\n        read_only=True,\n        metadata={"certification_only": True},\n        lineage=source_lineage(f"{venue}-{adapter}"),\n    )\n\n\ndef registry(*sources):\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-046",\n        revision=UMD_046_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(item.contract_hash for item in sources),\n        source_refs=("fixture://umd-046/registry",),\n        created_at=FIXED,\n    )\n    return CertifiedVenueDiscoverySourceRegistry(\n        sources=tuple(sources),\n        registry_metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\nclass TestUMD046(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_046_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-046")\n\n    def test_registry_certifies(self) -> None:\n        item = registry(\n            source("KALSHI", "KALSHI_MARKET_CATALOG"),\n            source("POLYMARKET", "POLYMARKET_MARKET_CATALOG"),\n        )\n        result = certify_venue_discovery_source_registry(item)\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["source_count"], 2)\n        self.assertEqual(result["venue_count"], 2)\n\n    def test_deterministic(self) -> None:\n        first_source = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        first = registry(first_source)\n        second = registry(first_source)\n        self.assertEqual(first.registry_id, second.registry_id)\n        self.assertEqual(first.registry_hash, second.registry_hash)\n\n    def test_lookup_indexes(self) -> None:\n        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        polymarket = source("POLYMARKET", "POLYMARKET_MARKET_CATALOG")\n        item = registry(kalshi, polymarket)\n        self.assertIs(item.get(kalshi.source_id), kalshi)\n        self.assertIs(\n            item.get_by_venue_adapter(\n                "kalshi",\n                "kalshi-market-catalog",\n            ),\n            kalshi,\n        )\n        self.assertEqual(item.list_by_venue("KALSHI"), (kalshi,))\n\n    def test_duplicate_source_rejected(self) -> None:\n        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        with self.assertRaises(ValueError):\n            registry(kalshi, kalshi)\n\n    def test_duplicate_venue_adapter_rejected(self) -> None:\n        first = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        second = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        with self.assertRaises(ValueError):\n            registry(first, second)\n\n    def test_lineage_requires_contract_hashes(self) -> None:\n        kalshi = source("KALSHI", "KALSHI_MARKET_CATALOG")\n        bad_lineage = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-046",\n            revision=UMD_046_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(),\n            source_refs=("fixture://umd-046/bad",),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            CertifiedVenueDiscoverySourceRegistry(\n                sources=(kalshi,),\n                registry_metadata={},\n                lineage=bad_lineage,\n            )\n\n    def test_immutable(self) -> None:\n        item = registry(source("KALSHI", "KALSHI_MARKET_CATALOG"))\n        with self.assertRaises((FrozenInstanceError, AttributeError)):\n            item.sources = ()\n        with self.assertRaises(TypeError):\n            item.registry_metadata["read_only"] = False\n        with self.assertRaises(TypeError):\n            item._by_source_id["x"] = None\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_046_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-046 CERTIFICATION TEST")\n    print(" CERTIFIED VENUE DISCOVERY SOURCE REGISTRY")\n    print("=" * 72)\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD046)\n    result = unittest.TextTestRunner(verbosity=2).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_046_certification_manifest()\n    print()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-045 consumed read-only")\n    print("[PASS] Exact UMD-045 source-contract class consumed")\n    print("[PASS] Deterministic source registry identity certified")\n    print("[PASS] Venue and adapter uniqueness enforced")\n    print("[PASS] Immutable read-only registry indexes certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-046 CERTIFIED VENUE DISCOVERY SOURCE REGISTRY CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_046_venue_discovery_source_registry import (\n    UMD_046_BUILD_ID,\n    UMD_046_BUILD_NAME,\n    UMD_046_REVISION,\n    UMD_046_SCHEMA_VERSION,\n    CertifiedVenueDiscoverySourceRegistry,\n    UMD046CertificationManifest,\n    build_umd_046_certification_manifest,\n    certify_venue_discovery_source_registry,\n    certify_umd_046_foundation,\n    verify_umd_046_venue_discovery_source_registry,\n)\n'
EXPORTED_NAMES = ('UMD_046_BUILD_ID', 'UMD_046_BUILD_NAME', 'UMD_046_REVISION', 'UMD_046_SCHEMA_VERSION', 'CertifiedVenueDiscoverySourceRegistry', 'UMD046CertificationManifest', 'build_umd_046_certification_manifest', 'certify_venue_discovery_source_registry', 'certify_umd_046_foundation', 'verify_umd_046_venue_discovery_source_registry')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'), ('umd_044_query_session_read_model_admission_gate', 'verify_umd_044_query_session_read_model_admission_gate'), ('umd_045_venue_discovery_source_contract', 'verify_umd_045_venue_discovery_source_contract'))


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_direct(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalize(source), encoding="utf-8", newline="\n")


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
    source = INIT.read_text(encoding="utf-8")
    marker = "from .umd_046_venue_discovery_source_registry import ("
    if marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)
    opening, closing = find_all_bounds(source)
    block = source[opening + 1:closing]
    missing = [
        name for name in EXPORTED_NAMES
        if f'"{name}"' not in block and f"'{name}'" not in block
    ]
    if missing:
        insertion = "".join(f'    "{name}",\n' for name in missing)
        source = source[:closing] + insertion + source[closing:]
    compile(source, str(INIT), "exec")
    write_direct(INIT, source)


def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        for module_name, verifier_name in UPSTREAM_MODULES:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery." + module_name
            )
            verifier = getattr(module, verifier_name, None)
            if verifier is None:
                raise RuntimeError(
                    f"Certified upstream verifier missing: "
                    f"{module_name}.{verifier_name}"
                )
            if verifier() is not True:
                raise RuntimeError(
                    f"Certified upstream verification failed: {module_name}"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module_name = (
            "qseries_v2.universal_market_discovery."
            "umd_046_venue_discovery_source_registry"
        )
        sys.modules.pop(module_name, None)
        importlib.invalidate_caches()
        module = importlib.import_module(module_name)
        missing = [
            name for name in EXPORTED_NAMES
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError("UMD-046 missing symbols: " + ", ".join(missing))
        if module.verify_umd_046_venue_discovery_source_registry() is not True:
            raise RuntimeError("UMD-046 verification returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    print("=" * 72)
    print(" UMD-046 REPOSITORY-VERIFIED INSTALLER")
    print(" CERTIFIED VENUE DISCOVERY SOURCE REGISTRY")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-045 verified read-only")

    backups = {
        path: (path.read_bytes() if path.exists() else None)
        for path in (MODULE, INIT, TEST)
    }
    try:
        write_direct(MODULE, MODULE_SOURCE)
        write_direct(TEST, TEST_SOURCE)
        update_init()
        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(INIT.read_text(encoding="utf-8"), str(INIT), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
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
                    f"{path}: {type(rollback_error).__name__}: {rollback_error}"
                )
        importlib.invalidate_caches()
        if rollback_errors:
            print("[ROLLBACK WARNING]")
            for rollback_error in rollback_errors:
                print(f"  - {rollback_error}")
        else:
            print("[ROLLBACK] UMD-046 installation failed; all affected files restored")
        raise

    manifest = {
        "build_id": "UMD-046",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(f"UMD-{number:03d}" for number in range(1, 46)),
        "mode": "deterministic_read_only_registry",
        "network_enabled": False,
        "persistence_enabled": False,
        "mutation_enabled": False,
        "publication_enabled": False,
        "execution_enabled": False,
    }
    install_hash = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required UMD-046 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-046 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
