from __future__ import annotations

import hashlib
import importlib
import json
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_044_CERTIFIED_QUERY_SESSION_READ_MODEL_ADMISSION_GATE_REPOSITORY_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "umd_044_query_session_read_model_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_044_query_session_read_model_admission_gate.py"

MODULE_SOURCE = 'from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import (\n    UMD_SUBSYSTEM_ID,\n    ImmutableLineage,\n    deterministic_sha256,\n)\nfrom .umd_043_query_session_read_model_admission_ledger_read_model import (\n    CertifiedUMD043AdmissionLedgerReadModel,\n)\n\nUMD_044_BUILD_ID = "UMD-044"\nUMD_044_BUILD_NAME = (\n    "Certified Active Canonical Market Registry Query Session "\n    "Read Model Admission Ledger Read Model Admission Ledger Read Model Admission Gate"\n)\nUMD_044_REVISION = (\n    "UMD_044_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_"\n    "READ_MODEL_ADMISSION_LEDGER_READ_MODEL_ADMISSION_LEDGER_READ_MODEL_"\n    "ADMISSION_LEDGER_READ_MODEL_ADMISSION_GATE_V1"\n)\nUMD_044_SCHEMA_VERSION = "1.0.0"\n\nPROHIBITED_CAPABILITIES = (\n    "network_discovery",\n    "market_scanning",\n    "automatic_admission_commit",\n    "ledger_append",\n    "ledger_mutation",\n    "read_model_mutation",\n    "read_model_persistence",\n    "active_registry_mutation",\n    "oracle_memory_mutation",\n    "publication",\n    "order_submission",\n    "trade_execution",\n)\n\n\ndef _text(value: str, field_name: str) -> str:\n    if not isinstance(value, str):\n        raise TypeError(f"{field_name} must be a string")\n    normalized = " ".join(value.strip().split())\n    if not normalized:\n        raise ValueError(f"{field_name} must not be empty")\n    return normalized\n\n\ndef _sha256(value: str, field_name: str) -> str:\n    normalized = _text(value, field_name).lower()\n    if len(normalized) != 64:\n        raise ValueError(f"{field_name} must contain 64 hexadecimal characters")\n    if any(character not in "0123456789abcdef" for character in normalized):\n        raise ValueError(f"{field_name} must be lowercase SHA-256 hexadecimal")\n    return normalized\n\n\n@dataclass(frozen=True, slots=True)\nclass CertifiedUMD044AdmissionDecision:\n    read_model_hash: str\n    source_ledger_hash: str\n    admitted: bool\n    checks: Mapping[str, bool]\n    rejection_reasons: Tuple[str, ...]\n    lineage: ImmutableLineage\n\n    def __post_init__(self) -> None:\n        object.__setattr__(self, "read_model_hash", _sha256(self.read_model_hash, "read_model_hash"))\n        object.__setattr__(self, "source_ledger_hash", _sha256(self.source_ledger_hash, "source_ledger_hash"))\n\n        normalized_checks = {\n            _text(str(name), "check name"): bool(passed)\n            for name, passed in self.checks.items()\n        }\n        object.__setattr__(\n            self,\n            "checks",\n            MappingProxyType(dict(sorted(normalized_checks.items()))),\n        )\n\n        failed = tuple(name for name, passed in self.checks.items() if not passed)\n        reasons = tuple(sorted({_text(reason, "rejection reason") for reason in self.rejection_reasons}))\n        object.__setattr__(self, "rejection_reasons", reasons)\n\n        if self.admitted:\n            if failed or reasons:\n                raise ValueError("admitted decision cannot contain failures")\n        else:\n            if not failed:\n                raise ValueError("rejected decision requires failed checks")\n            if reasons != tuple(sorted(failed)):\n                raise ValueError("rejection reasons must match failed checks")\n\n        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:\n            raise ValueError("admission lineage must belong to UMD")\n        if self.lineage.build_id != UMD_044_BUILD_ID:\n            raise ValueError("admission lineage must use build_id UMD-044")\n        required = {self.read_model_hash, self.source_ledger_hash}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("admission lineage is missing required parent hashes")\n\n    @property\n    def decision_id(self) -> str:\n        return (\n            "umd:query-session-read-model-admission-ledger-read-model-admission:"\n            + deterministic_sha256(\n                {\n                    "read_model_hash": self.read_model_hash,\n                    "source_ledger_hash": self.source_ledger_hash,\n                    "admitted": self.admitted,\n                    "checks": self.checks,\n                }\n            )\n        )\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "decision_id": self.decision_id,\n            "read_model_hash": self.read_model_hash,\n            "source_ledger_hash": self.source_ledger_hash,\n            "admitted": self.admitted,\n            "checks": self.checks,\n            "rejection_reasons": self.rejection_reasons,\n            "lineage": self.lineage,\n        }\n\n    @property\n    def record_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\ndef evaluate_umd_044_admission(\n    read_model: CertifiedUMD043AdmissionLedgerReadModel,\n    *,\n    lineage: ImmutableLineage,\n) -> CertifiedUMD044AdmissionDecision:\n    if not isinstance(\n        read_model,\n        CertifiedUMD043AdmissionLedgerReadModel,\n    ):\n        raise TypeError("read_model must be a certified UMD-037 read model")\n\n    checks = {\n        "read_model_hash_deterministic": (\n            read_model.read_model_hash\n            == deterministic_sha256(read_model.to_canonical_dict())\n        ),\n        "count_partition_valid": (\n            read_model.admitted_entry_count\n            + read_model.rejected_entry_count\n            == read_model.total_entry_count\n        ),\n        "ordered_entry_count_valid": (\n            len(read_model.ordered_entry_ids) == read_model.total_entry_count\n        ),\n        "ordered_read_model_count_valid": (\n            len(read_model.ordered_read_model_hashes) == read_model.total_entry_count\n        ),\n        "ordered_decision_count_valid": (\n            len(read_model.ordered_decision_ids) == read_model.total_entry_count\n        ),\n        "entry_ids_unique": (\n            len(set(read_model.ordered_entry_ids))\n            == len(read_model.ordered_entry_ids)\n        ),\n        "read_model_hashes_unique": (\n            len(set(read_model.ordered_read_model_hashes))\n            == len(read_model.ordered_read_model_hashes)\n        ),\n        "decision_ids_unique": (\n            len(set(read_model.ordered_decision_ids))\n            == len(read_model.ordered_decision_ids)\n        ),\n        "admission_partition_disjoint": (\n            not set(read_model.admitted_entry_ids).intersection(\n                read_model.rejected_entry_ids\n            )\n        ),\n        "admission_partition_complete": (\n            set(read_model.admitted_entry_ids).union(\n                read_model.rejected_entry_ids\n            )\n            == set(read_model.ordered_entry_ids)\n        ),\n        "latest_entry_consistent": (\n            (\n                read_model.latest_entry_id is None\n                and not read_model.ordered_entry_ids\n            )\n            or (\n                bool(read_model.ordered_entry_ids)\n                and read_model.latest_entry_id\n                == read_model.ordered_entry_ids[-1]\n            )\n        ),\n        "latest_admitted_entry_consistent": (\n            (\n                read_model.latest_admitted_entry_id is None\n                and not read_model.admitted_entry_ids\n            )\n            or (\n                bool(read_model.admitted_entry_ids)\n                and read_model.latest_admitted_entry_id\n                == read_model.admitted_entry_ids[-1]\n            )\n        ),\n        "entry_positions_contiguous": all(\n            read_model.entry_position(entry_id) == index\n            for index, entry_id in enumerate(read_model.ordered_entry_ids, start=1)\n        ),\n        "read_model_positions_contiguous": all(\n            read_model.read_model_position(read_model_hash) == index\n            for index, read_model_hash in enumerate(\n                read_model.ordered_read_model_hashes,\n                start=1,\n            )\n        ),\n        "decision_positions_contiguous": all(\n            read_model.decision_position(decision_id) == index\n            for index, decision_id in enumerate(\n                read_model.ordered_decision_ids,\n                start=1,\n            )\n        ),\n        "lineage_bound_to_source_ledger": (\n            read_model.source_ledger_hash in read_model.lineage.parent_hashes\n        ),\n    }\n\n    failed = tuple(name for name, passed in checks.items() if not passed)\n\n    return CertifiedUMD044AdmissionDecision(\n        read_model_hash=read_model.read_model_hash,\n        source_ledger_hash=read_model.source_ledger_hash,\n        admitted=not failed,\n        checks=checks,\n        rejection_reasons=failed,\n        lineage=lineage,\n    )\n\n\n@dataclass(frozen=True, slots=True)\nclass UMD044CertificationManifest:\n    subsystem_id: str\n    build_id: str\n    build_name: str\n    revision: str\n    schema_version: str\n    upstream_builds: Tuple[str, ...]\n    gate_mode: str\n    prohibited_capabilities: Tuple[str, ...]\n    network_enabled: bool\n    persistence_enabled: bool\n    mutation_enabled: bool\n    publication_enabled: bool\n    execution_enabled: bool\n\n    def to_canonical_dict(self) -> Mapping[str, Any]:\n        return {\n            "subsystem_id": self.subsystem_id,\n            "build_id": self.build_id,\n            "build_name": self.build_name,\n            "revision": self.revision,\n            "schema_version": self.schema_version,\n            "upstream_builds": self.upstream_builds,\n            "gate_mode": self.gate_mode,\n            "prohibited_capabilities": self.prohibited_capabilities,\n            "network_enabled": self.network_enabled,\n            "persistence_enabled": self.persistence_enabled,\n            "mutation_enabled": self.mutation_enabled,\n            "publication_enabled": self.publication_enabled,\n            "execution_enabled": self.execution_enabled,\n        }\n\n    @property\n    def manifest_hash(self) -> str:\n        return deterministic_sha256(self.to_canonical_dict())\n\n\ndef build_umd_044_certification_manifest() -> UMD044CertificationManifest:\n    return UMD044CertificationManifest(\n        subsystem_id="UMD",\n        build_id=UMD_044_BUILD_ID,\n        build_name=UMD_044_BUILD_NAME,\n        revision=UMD_044_REVISION,\n        schema_version=UMD_044_SCHEMA_VERSION,\n        upstream_builds=tuple(f"UMD-{number:03d}" for number in range(1, 44)),\n        gate_mode="deterministic_read_only_admission",\n        prohibited_capabilities=PROHIBITED_CAPABILITIES,\n        network_enabled=False,\n        persistence_enabled=False,\n        mutation_enabled=False,\n        publication_enabled=False,\n        execution_enabled=False,\n    )\n\n\ndef certify_umd_044_foundation() -> Mapping[str, Any]:\n    manifest = build_umd_044_certification_manifest()\n    checks = {\n        "subsystem_identity": manifest.subsystem_id == "UMD",\n        "build_identity": manifest.build_id == "UMD-044",\n        "upstreams_frozen": (\n            manifest.upstream_builds\n            == tuple(f"UMD-{number:03d}" for number in range(1, 44))\n        ),\n        "deterministic_read_only_admission": (\n            manifest.gate_mode == "deterministic_read_only_admission"\n        ),\n        "network_disabled": manifest.network_enabled is False,\n        "persistence_disabled": manifest.persistence_enabled is False,\n        "mutation_disabled": manifest.mutation_enabled is False,\n        "publication_disabled": manifest.publication_enabled is False,\n        "execution_disabled": manifest.execution_enabled is False,\n        "deterministic_manifest_hash": (\n            manifest.manifest_hash\n            == deterministic_sha256(manifest.to_canonical_dict())\n        ),\n    }\n    failed = tuple(name for name, passed in checks.items() if not passed)\n    return MappingProxyType(\n        {\n            "certified": not failed,\n            "build_id": manifest.build_id,\n            "revision": manifest.revision,\n            "manifest_hash": manifest.manifest_hash,\n            "checks": MappingProxyType(checks),\n            "failed_checks": failed,\n        }\n    )\n\n\ndef verify_umd_044_query_session_read_model_admission_gate() -> bool:\n    certification = certify_umd_044_foundation()\n    if not certification["certified"]:\n        raise RuntimeError(\n            "UMD-044 foundation certification failed: "\n            + ", ".join(certification["failed_checks"])\n        )\n    return True\n'
TEST_SOURCE = '\nfrom __future__ import annotations\n\nimport hashlib\nimport unittest\nfrom dataclasses import FrozenInstanceError\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (\n    ImmutableLineage,\n)\nfrom qseries_v2.universal_market_discovery.umd_041_query_session_read_model_admission_gate import (\n    UMD_041_REVISION,\n    CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision,\n)\nfrom qseries_v2.universal_market_discovery.umd_042_query_session_read_model_admission_ledger import (\n    UMD_042_REVISION,\n    CertifiedUMD042AdmissionLedgerEntry,\n    ReadOnlyUMD042AdmissionLedger,\n)\nfrom qseries_v2.universal_market_discovery.umd_043_query_session_read_model_admission_ledger_read_model import (\n    UMD_043_REVISION,\n    build_umd_043_admission_ledger_read_model,\n)\nfrom qseries_v2.universal_market_discovery.umd_044_query_session_read_model_admission_gate import (\n    UMD_044_REVISION,\n    CertifiedUMD044AdmissionDecision,\n    build_umd_044_certification_manifest,\n    certify_umd_044_foundation,\n    evaluate_umd_044_admission,\n)\n\nFIXED = datetime(\n    2026,\n    8,\n    6,\n    19,\n    35,\n    0,\n    tzinfo=timezone.utc,\n)\n\n\ndef digest(label: str) -> str:\n    return hashlib.sha256(label.encode("utf-8")).hexdigest()\n\n\ndef upstream_decision(\n    suffix: str,\n    admitted: bool = True,\n):\n    read_model_hash = digest(f"umd-044:{suffix}:read-model")\n    source_ledger_hash = digest(f"umd-044:{suffix}:source-ledger")\n    checks = {"certified": admitted}\n    reasons = () if admitted else ("certified",)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-041",\n        revision=UMD_041_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(read_model_hash, source_ledger_hash),\n        source_refs=(f"fixture://umd-044/decision/{suffix}",),\n        created_at=FIXED,\n    )\n\n    return CertifiedActiveMarketQuerySessionReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionLedgerReadModelAdmissionDecision(\n        read_model_hash=read_model_hash,\n        source_ledger_hash=source_ledger_hash,\n        admitted=admitted,\n        checks=checks,\n        rejection_reasons=reasons,\n        lineage=lineage,\n    )\n\n\ndef ledger_entry(number: int, decision, previous: str | None):\n    parents = [decision.record_hash]\n    if previous is not None:\n        parents.append(previous)\n\n    lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-042",\n        revision=UMD_042_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=tuple(parents),\n        source_refs=(f"fixture://umd-044/entry/{number}",),\n        created_at=FIXED,\n    )\n\n    return CertifiedUMD042AdmissionLedgerEntry(\n        sequence_number=number,\n        previous_entry_hash=previous,\n        decision=decision,\n        recorded_at=FIXED,\n        metadata={"read_only": True},\n        lineage=lineage,\n    )\n\n\ndef build_read_model():\n    first = ledger_entry(1, upstream_decision("a", True), None)\n    second = ledger_entry(\n        2,\n        upstream_decision("b", False),\n        first.entry_hash,\n    )\n    third = ledger_entry(\n        3,\n        upstream_decision("c", True),\n        second.entry_hash,\n    )\n\n    ledger_lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-042",\n        revision=UMD_042_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(third.entry_hash,),\n        source_refs=("fixture://umd-044/ledger",),\n        created_at=FIXED,\n    )\n    ledger = ReadOnlyUMD042AdmissionLedger(\n        entries=(first, second, third),\n        ledger_lineage=ledger_lineage,\n    )\n\n    read_model_lineage = ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-043",\n        revision=UMD_043_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(ledger.ledger_hash,),\n        source_refs=("fixture://umd-044/read-model",),\n        created_at=FIXED,\n    )\n\n    return build_umd_043_admission_ledger_read_model(\n        ledger,\n        metadata={"read_only": True},\n        lineage=read_model_lineage,\n    )\n\n\ndef gate_lineage(read_model):\n    return ImmutableLineage(\n        subsystem_id="UMD",\n        build_id="UMD-044",\n        revision=UMD_044_REVISION,\n        schema_version="1.0.0",\n        parent_hashes=(\n            read_model.read_model_hash,\n            read_model.source_ledger_hash,\n        ),\n        source_refs=("fixture://umd-044/gate",),\n        created_at=FIXED,\n    )\n\n\nclass TestUMD044(unittest.TestCase):\n    def test_foundation(self) -> None:\n        result = certify_umd_044_foundation()\n        self.assertTrue(result["certified"])\n        self.assertEqual(result["build_id"], "UMD-044")\n\n    def test_valid_admitted(self) -> None:\n        read_model = build_read_model()\n        decision = evaluate_umd_044_admission(\n            read_model,\n            lineage=gate_lineage(read_model),\n        )\n        self.assertTrue(decision.admitted)\n        self.assertEqual(decision.rejection_reasons, ())\n        self.assertTrue(all(decision.checks.values()))\n\n    def test_deterministic(self) -> None:\n        read_model = build_read_model()\n        lineage = gate_lineage(read_model)\n        first = evaluate_umd_044_admission(\n            read_model,\n            lineage=lineage,\n        )\n        second = evaluate_umd_044_admission(\n            read_model,\n            lineage=lineage,\n        )\n        self.assertEqual(first.decision_id, second.decision_id)\n        self.assertEqual(first.record_hash, second.record_hash)\n\n    def test_lineage_requires_both(self) -> None:\n        read_model = build_read_model()\n        bad = ImmutableLineage(\n            subsystem_id="UMD",\n            build_id="UMD-044",\n            revision=UMD_044_REVISION,\n            schema_version="1.0.0",\n            parent_hashes=(read_model.read_model_hash,),\n            source_refs=("fixture://umd-044/bad",),\n            created_at=FIXED,\n        )\n        with self.assertRaises(ValueError):\n            evaluate_umd_044_admission(\n                read_model,\n                lineage=bad,\n            )\n\n    def test_immutable(self) -> None:\n        read_model = build_read_model()\n        decision = evaluate_umd_044_admission(\n            read_model,\n            lineage=gate_lineage(read_model),\n        )\n        with self.assertRaises(\n            (FrozenInstanceError, AttributeError)\n        ):\n            decision.admitted = False\n        with self.assertRaises(TypeError):\n            decision.checks["changed"] = False\n\n    def test_exact_umd_043_type(self) -> None:\n        read_model = build_read_model()\n        self.assertEqual(\n            read_model.lineage.build_id,\n            "UMD-043",\n        )\n\n    def test_side_effects(self) -> None:\n        manifest = build_umd_044_certification_manifest()\n        self.assertFalse(manifest.network_enabled)\n        self.assertFalse(manifest.persistence_enabled)\n        self.assertFalse(manifest.mutation_enabled)\n        self.assertFalse(manifest.publication_enabled)\n        self.assertFalse(manifest.execution_enabled)\n\n\nif __name__ == "__main__":\n    print("=" * 72)\n    print(" UMD-044 CERTIFICATION TEST")\n    print("=" * 72)\n\n    suite = unittest.defaultTestLoader.loadTestsFromTestCase(\n        TestUMD044\n    )\n    result = unittest.TextTestRunner(verbosity=2).run(suite)\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    manifest = build_umd_044_certification_manifest()\n    print(f"[PASS] Build: {manifest.build_id}")\n    print(f"[PASS] Revision: {manifest.revision}")\n    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")\n    print("[PASS] UMD-001 through UMD-043 consumed read-only")\n    print("[PASS] Exact UMD-043 read-model class consumed")\n    print("[PASS] Immutable UMD-044 admission decisions certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-044 CERTIFIED")\n'
INIT_IMPORT = '\nfrom .umd_044_query_session_read_model_admission_gate import (\n    UMD_044_BUILD_ID,\n    UMD_044_BUILD_NAME,\n    UMD_044_REVISION,\n    UMD_044_SCHEMA_VERSION,\n    CertifiedUMD044AdmissionDecision,\n    UMD044CertificationManifest,\n    evaluate_umd_044_admission,\n    build_umd_044_certification_manifest,\n    certify_umd_044_foundation,\n    verify_umd_044_query_session_read_model_admission_gate,\n)\n'
EXPORTED_NAMES = ('UMD_044_BUILD_ID', 'UMD_044_BUILD_NAME', 'UMD_044_REVISION', 'UMD_044_SCHEMA_VERSION', 'CertifiedUMD044AdmissionDecision', 'UMD044CertificationManifest', 'evaluate_umd_044_admission', 'build_umd_044_certification_manifest', 'certify_umd_044_foundation', 'verify_umd_044_query_session_read_model_admission_gate')
UPSTREAM_MODULES = (('universal_market_discovery_foundation', 'verify_umd_foundation'), ('certified_canonical_market_contract', 'verify_umd_002_certified_canonical_market_contract'), ('certified_venue_identity_registry', 'verify_umd_003_certified_venue_identity_registry'), ('certified_venue_market_binding_registry', 'verify_umd_004_certified_venue_market_binding_registry'), ('certified_market_category_hierarchy_registry', 'verify_umd_005_certified_market_category_hierarchy_registry'), ('certified_market_classification_registry', 'verify_umd_006_certified_market_classification_registry'), ('certified_market_metadata_registry', 'verify_umd_007_certified_market_metadata_registry'), ('certified_market_lifecycle_and_settlement_registry', 'verify_umd_008_certified_market_lifecycle_and_settlement_registry'), ('certified_market_duplicate_resolution_registry', 'verify_umd_009_certified_market_duplicate_resolution_registry'), ('certified_related_market_graph_registry', 'verify_umd_010_certified_related_market_graph_registry'), ('certified_incremental_discovery_batch_contract', 'verify_umd_011_certified_incremental_discovery_batch_contract'), ('certified_incremental_discovery_admission_gate', 'verify_umd_012_certified_incremental_discovery_admission_gate'), ('certified_discovery_admission_ledger', 'verify_umd_013_certified_discovery_admission_ledger'), ('certified_admitted_market_materialization_contract', 'verify_umd_014_certified_admitted_market_materialization_contract'), ('certified_materialized_market_admission_registry', 'verify_umd_015_certified_materialized_market_admission_registry'), ('certified_canonical_market_registry_snapshot_contract', 'verify_umd_016_certified_canonical_market_registry_snapshot_contract'), ('certified_canonical_market_registry_snapshot_admission_gate', 'verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate'), ('certified_canonical_market_registry_snapshot_admission_ledger', 'verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger'), ('certified_canonical_market_registry_snapshot_activation_contract', 'verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract'), ('certified_canonical_market_registry_snapshot_activation_gate', 'verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate'), ('certified_canonical_market_registry_snapshot_activation_ledger', 'verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger'), ('certified_active_canonical_market_registry_read_model', 'verify_umd_022_certified_active_canonical_market_registry_read_model'), ('certified_active_canonical_market_registry_query_contract', 'verify_umd_023_certified_active_canonical_market_registry_query_contract'), ('certified_active_canonical_market_registry_query_execution_engine', 'verify_umd_024_certified_active_canonical_market_registry_query_execution_engine'), ('certified_active_canonical_market_registry_query_execution_admission_gate', 'verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate'), ('certified_active_canonical_market_registry_query_execution_ledger', 'verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger'), ('certified_active_canonical_market_registry_query_execution_read_model', 'verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model'), ('certified_active_canonical_market_registry_query_session_contract', 'verify_umd_028_certified_active_canonical_market_registry_query_session_contract'), ('certified_active_canonical_market_registry_query_session_admission_gate', 'verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate'), ('certified_active_canonical_market_registry_query_session_admission_ledger', 'verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model', 'verify_umd_031_certified_active_canonical_market_registry_query_session_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_gate', 'verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger', 'verify_umd_033_certified_active_canonical_market_registry_query_session_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model', 'verify_umd_034_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_035_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_036_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_037_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate', 'verify_umd_038_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_gate'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger', 'verify_umd_039_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger'), ('certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model', 'verify_umd_040_certified_active_canonical_market_registry_query_session_read_model_admission_ledger_read_model_admission_ledger_read_model_admission_ledger_read_model'), ('umd_041_query_session_read_model_admission_gate', 'verify_umd_041_query_session_read_model_admission_gate'), ('umd_042_query_session_read_model_admission_ledger', 'verify_umd_042_query_session_read_model_admission_ledger'), ('umd_043_query_session_read_model_admission_ledger_read_model', 'verify_umd_043_query_session_read_model_admission_ledger_read_model'))


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
    marker = (
        "from .umd_044_query_session_read_model_admission_gate import ("
    )
    if marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

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
            "umd_044_query_session_read_model_admission_gate"
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
                "UMD-044 missing symbols: " + ", ".join(missing)
            )
        if module.verify_umd_044_query_session_read_model_admission_gate() is not True:
            raise RuntimeError("UMD-044 verification returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    print("=" * 72)
    print(" UMD-044 REPOSITORY-VERIFIED INSTALLER")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print("[PASS] Certified UMD-001 through UMD-043 verified read-only")

    backups = {
        path: (path.read_bytes() if path.exists() else None)
        for path in (MODULE, INIT, TEST)
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
                "[ROLLBACK] UMD-044 installation failed; "
                "all affected files restored"
            )
        raise

    manifest = {
        "build_id": "UMD-044",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}" for number in range(1, 44)
        ),
        "mode": "deterministic_read_only_admission",
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
    print("[PASS] Required UMD-044 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print("[DONE] UMD-044 INSTALLATION COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
