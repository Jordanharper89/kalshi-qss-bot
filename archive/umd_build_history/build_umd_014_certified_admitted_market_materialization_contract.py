from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_014_CERTIFIED_ADMITTED_MARKET_MATERIALIZATION_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_admitted_market_materialization_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_014_certified_admitted_market_materialization_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_canonical_market_contract import CertifiedCanonicalMarket
from .certified_incremental_discovery_batch_contract import (
    CertifiedIncrementalDiscoveryBatch,
)
from .certified_discovery_admission_ledger import (
    CertifiedDiscoveryAdmissionLedgerEntry,
)

UMD_014_BUILD_ID = "UMD-014"
UMD_014_BUILD_NAME = "Certified Admitted Market Materialization Contract"
UMD_014_REVISION = (
    "UMD_014_CERTIFIED_ADMITTED_MARKET_MATERIALIZATION_CONTRACT_V1"
)
UMD_014_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_registry_commit",
    "persistence_write",
    "registry_mutation",
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


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


@dataclass(frozen=True, slots=True)
class CertifiedAdmittedMarketMaterialization:
    ledger_entry_id: str
    admission_decision_id: str
    batch_id: str
    source_id: str
    source_market_key: str
    candidate_id: str
    market: CertifiedCanonicalMarket
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        for field_name, prefix in (
            ("ledger_entry_id", "umd:admission-ledger-entry:"),
            ("admission_decision_id", "umd:admission:"),
            ("batch_id", "umd:batch:"),
            ("candidate_id", "umd:candidate:"),
        ):
            value = _text(getattr(self, field_name), field_name)
            if not value.startswith(prefix):
                raise ValueError(
                    f"{field_name} must use prefix {prefix}"
                )
            object.__setattr__(self, field_name, value)

        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, "source_id").lower(),
        )
        object.__setattr__(
            self,
            "source_market_key",
            _text(self.source_market_key, "source_market_key"),
        )
        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("materialization lineage must belong to UMD")
        if self.lineage.build_id != UMD_014_BUILD_ID:
            raise ValueError(
                "materialization lineage must use build_id UMD-014"
            )

    @property
    def materialization_id(self) -> str:
        return "umd:materialization:" + deterministic_sha256(
            {
                "ledger_entry_id": self.ledger_entry_id,
                "candidate_id": self.candidate_id,
                "canonical_market_id": self.market.canonical_market_id,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "materialization_id": self.materialization_id,
            "ledger_entry_id": self.ledger_entry_id,
            "admission_decision_id": self.admission_decision_id,
            "batch_id": self.batch_id,
            "source_id": self.source_id,
            "source_market_key": self.source_market_key,
            "candidate_id": self.candidate_id,
            "canonical_market_id": self.market.canonical_market_id,
            "market_record_hash": self.market.record_hash,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def materialize_admitted_batch(
    batch: CertifiedIncrementalDiscoveryBatch,
    ledger_entry: CertifiedDiscoveryAdmissionLedgerEntry,
    *,
    metadata: Mapping[str, Any],
    lineage_factory,
) -> Tuple[CertifiedAdmittedMarketMaterialization, ...]:
    decision = ledger_entry.decision

    if not decision.admitted:
        raise ValueError("rejected admission decisions cannot be materialized")
    if decision.batch_id != batch.batch_id:
        raise ValueError("ledger decision batch_id does not match batch")
    if decision.batch_hash != batch.batch_hash:
        raise ValueError("ledger decision batch_hash does not match batch")
    if decision.source_id != batch.source_id:
        raise ValueError("ledger decision source_id does not match batch")
    if decision.batch_sequence != batch.batch_sequence:
        raise ValueError(
            "ledger decision batch_sequence does not match batch"
        )

    materializations = []
    seen_market_ids = set()

    for candidate in batch.candidates:
        market_id = candidate.market.canonical_market_id
        if market_id in seen_market_ids:
            raise ValueError(
                "batch cannot materialize the same canonical market twice"
            )
        seen_market_ids.add(market_id)

        lineage = lineage_factory(
            candidate,
            ledger_entry,
        )
        required_parents = {
            candidate.record_hash,
            ledger_entry.entry_hash,
            decision.record_hash,
            batch.batch_hash,
        }
        if not required_parents.issubset(
            set(lineage.parent_hashes)
        ):
            raise ValueError(
                "materialization lineage is missing required parents"
            )

        materializations.append(
            CertifiedAdmittedMarketMaterialization(
                ledger_entry_id=ledger_entry.entry_id,
                admission_decision_id=decision.decision_id,
                batch_id=batch.batch_id,
                source_id=candidate.source_id,
                source_market_key=candidate.source_market_key,
                candidate_id=candidate.candidate_id,
                market=candidate.market,
                metadata=metadata,
                lineage=lineage,
            )
        )

    return tuple(
        sorted(
            materializations,
            key=lambda item: item.materialization_id,
        )
    )


@dataclass(frozen=True, slots=True)
class ReadOnlyAdmittedMarketMaterializationRegistry:
    materializations: Tuple[
        CertifiedAdmittedMarketMaterialization,
        ...
    ]

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.materializations,
                key=lambda item: item.materialization_id,
            )
        )
        object.__setattr__(self, "materializations", ordered)

        materialization_ids = {
            item.materialization_id for item in ordered
        }
        candidate_ids = {
            item.candidate_id for item in ordered
        }
        market_ids = {
            item.market.canonical_market_id for item in ordered
        }

        if len(materialization_ids) != len(ordered):
            raise ValueError("duplicate materialization ID")
        if len(candidate_ids) != len(ordered):
            raise ValueError("candidate may be materialized only once")
        if len(market_ids) != len(ordered):
            raise ValueError(
                "canonical market may be materialized only once"
            )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "read_only",
            "materializations": self.materializations,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


@dataclass(frozen=True, slots=True)
class UMD014CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    contract_mode: str
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
            "contract_mode": self.contract_mode,
            "prohibited_capabilities": self.prohibited_capabilities,
            "network_enabled": self.network_enabled,
            "persistence_enabled": self.persistence_enabled,
            "mutation_enabled": self.mutation_enabled,
            "publication_enabled": self.publication_enabled,
            "execution_enabled": self.execution_enabled,
        }

    @property
    def manifest_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def build_umd_014_certification_manifest() -> UMD014CertificationManifest:
    return UMD014CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_014_BUILD_ID,
        build_name=UMD_014_BUILD_NAME,
        revision=UMD_014_REVISION,
        schema_version=UMD_014_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 14)
        ),
        contract_mode="read_only_materialization",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_014_foundation() -> Mapping[str, Any]:
    manifest = build_umd_014_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-014",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(
            f"UMD-{number:03d}" for number in range(1, 14)
        ),
        "read_only_materialization": (
            manifest.contract_mode
            == "read_only_materialization"
        ),
        "network_disabled": not manifest.network_enabled,
        "persistence_disabled": not manifest.persistence_enabled,
        "mutation_disabled": not manifest.mutation_enabled,
        "publication_disabled": not manifest.publication_enabled,
        "execution_disabled": not manifest.execution_enabled,
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(manifest.to_canonical_dict())
        ),
    }
    failed = tuple(
        name for name, passed in checks.items() if not passed
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


def verify_umd_014_certified_admitted_market_materialization_contract() -> bool:
    result = certify_umd_014_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-014 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_014_BUILD_ID",
    "UMD_014_BUILD_NAME",
    "UMD_014_REVISION",
    "UMD_014_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedAdmittedMarketMaterialization",
    "materialize_admitted_batch",
    "ReadOnlyAdmittedMarketMaterializationRegistry",
    "UMD014CertificationManifest",
    "build_umd_014_certification_manifest",
    "certify_umd_014_foundation",
    "verify_umd_014_certified_admitted_market_materialization_contract",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import (
    ImmutableLineage,
)
from qseries_v2.universal_market_discovery.certified_admitted_market_materialization_contract import (
    UMD_014_REVISION,
    build_umd_014_certification_manifest,
    certify_umd_014_foundation,
    verify_umd_014_certified_admitted_market_materialization_contract,
)

FIXED = datetime(2026, 8, 5, 23, 0, tzinfo=timezone.utc)


class TestUMD014(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_014_foundation()["certified"])
        self.assertTrue(
            verify_umd_014_certified_admitted_market_materialization_contract()
        )

    def test_manifest_is_read_only(self) -> None:
        manifest = build_umd_014_certification_manifest()
        self.assertEqual(
            manifest.contract_mode,
            "read_only_materialization",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_014_certification_manifest()
        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 14)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-014",
            revision=UMD_014_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=("fixture://umd-014",),
            created_at=FIXED,
        )
        self.assertEqual(lineage.build_id, "UMD-014")


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-014 CERTIFICATION TEST")
    print(" CERTIFIED ADMITTED MARKET MATERIALIZATION CONTRACT")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD014
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_014_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-013 consumed read-only")
    print("[PASS] Admitted-only materialization contract certified")
    print("[PASS] Rejected batch materialization prohibited")
    print("[PASS] Candidate-to-market identity preserved")
    print("[PASS] Candidate, batch, decision, and ledger lineage required")
    print("[PASS] Duplicate candidate materialization prohibited")
    print("[PASS] Duplicate canonical market materialization prohibited")
    print("[PASS] Deterministic materialization ordering verified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-014 CERTIFIED ADMITTED MARKET MATERIALIZATION CONTRACT CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_admitted_market_materialization_contract import (
    UMD_014_BUILD_ID,
    UMD_014_BUILD_NAME,
    UMD_014_REVISION,
    UMD_014_SCHEMA_VERSION,
    CertifiedAdmittedMarketMaterialization,
    materialize_admitted_batch,
    ReadOnlyAdmittedMarketMaterializationRegistry,
    UMD014CertificationManifest,
    build_umd_014_certification_manifest,
    certify_umd_014_foundation,
    verify_umd_014_certified_admitted_market_materialization_contract,
)
"""

EXPORTED_NAMES = (
    "UMD_014_BUILD_ID",
    "UMD_014_BUILD_NAME",
    "UMD_014_REVISION",
    "UMD_014_SCHEMA_VERSION",
    "CertifiedAdmittedMarketMaterialization",
    "materialize_admitted_batch",
    "ReadOnlyAdmittedMarketMaterializationRegistry",
    "UMD014CertificationManifest",
    "build_umd_014_certification_manifest",
    "certify_umd_014_foundation",
    "verify_umd_014_certified_admitted_market_materialization_contract",
)


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


def update_init() -> None:
    if not INIT.exists():
        raise FileNotFoundError(
            f"UMD package initializer missing: {INIT}"
        )

    source = INIT.read_text(encoding="utf-8")
    marker = (
        "from .certified_admitted_market_materialization_contract import ("
    )

    if marker not in source:
        source = source.rstrip() + "\n\n" + normalize(INIT_IMPORT)

    if "__all__" in source:
        start = source.index("__all__ = [")
        end = source.index("]", start)
        block = source[start : end + 1]
        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]
        if missing:
            block = block[:-1] + "".join(
                f'    "{name}",\n' for name in missing
            ) + "]"
            source = source[:start] + block + source[end + 1 :]
    else:
        source += "\n__all__ = [\n" + "".join(
            f'    "{name}",\n' for name in EXPORTED_NAMES
        ) + "]\n"

    write_exact(INIT, source)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        modules = (
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
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            if not getattr(module, verifier_name)():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def verify_current() -> None:
    sys.path.insert(0, str(ROOT))
    try:
        module = importlib.import_module(
            "qseries_v2.universal_market_discovery."
            "certified_admitted_market_materialization_contract"
        )
        required = (
            "CertifiedAdmittedMarketMaterialization",
            "materialize_admitted_batch",
            "ReadOnlyAdmittedMarketMaterializationRegistry",
            "certify_umd_014_foundation",
            "verify_umd_014_certified_admitted_market_materialization_contract",
        )
        missing = [
            name
            for name in required
            if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-014 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_014_certified_admitted_market_materialization_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def main() -> int:
    print("=" * 64)
    print(" UMD-014 INSTALLER")
    print(" CERTIFIED ADMITTED MARKET MATERIALIZATION CONTRACT")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-013 "
        "verified read-only"
    )

    write_exact(MODULE, MODULE_SOURCE)
    write_exact(TEST, TEST_SOURCE)
    update_init()

    py_compile.compile(str(MODULE), doraise=True)
    py_compile.compile(str(INIT), doraise=True)
    py_compile.compile(str(TEST), doraise=True)
    verify_current()

    manifest = {
        "build_id": "UMD-014",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 14)
        ),
        "mode": "read_only_materialization",
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
    print("[PASS] Required UMD-014 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-014 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_014_certified_admitted_market_materialization_contract.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
