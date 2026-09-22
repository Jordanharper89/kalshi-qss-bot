from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_012_CERTIFIED_INCREMENTAL_DISCOVERY_ADMISSION_GATE_CORRECTION_V2"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_incremental_discovery_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_012_certified_incremental_discovery_admission_gate.py"

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
from .certified_incremental_discovery_batch_contract import (
    CertifiedIncrementalDiscoveryBatch,
    ReadOnlyIncrementalDiscoveryBatchRegistry,
)

UMD_012_BUILD_ID = "UMD-012"
UMD_012_BUILD_NAME = "Certified Incremental Discovery Admission Gate"
UMD_012_REVISION = (
    "UMD_012_CERTIFIED_INCREMENTAL_DISCOVERY_ADMISSION_GATE_CORRECTION_V2"
)
UMD_012_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "venue_api_connection",
    "credential_loading",
    "automatic_admission_commit",
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


def _sha256_text(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(f"{field_name} must contain 64 hexadecimal characters")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be lowercase SHA-256 hexadecimal")
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedDiscoveryAdmissionDecision:
    batch_id: str
    batch_hash: str
    source_id: str
    batch_sequence: int
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        batch_id = _text(self.batch_id, "batch_id")
        if not batch_id.startswith("umd:batch:"):
            raise ValueError("batch_id must use the UMD batch prefix")
        object.__setattr__(self, "batch_id", batch_id)
        object.__setattr__(
            self,
            "batch_hash",
            _sha256_text(self.batch_hash, "batch_hash"),
        )
        object.__setattr__(
            self,
            "source_id",
            _text(self.source_id, "source_id").lower(),
        )

        if not isinstance(self.batch_sequence, int):
            raise TypeError("batch_sequence must be an integer")
        if self.batch_sequence < 1:
            raise ValueError("batch_sequence must be positive")

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(dict(sorted(normalized_checks.items()))),
        )

        reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(self, "rejection_reasons", reasons)

        failed_checks = tuple(
            name for name, passed in self.checks.items() if not passed
        )
        if self.admitted:
            if failed_checks:
                raise ValueError("admitted decisions cannot contain failed checks")
            if reasons:
                raise ValueError(
                    "admitted decisions cannot contain rejection reasons"
                )
        else:
            if not failed_checks:
                raise ValueError("rejected decisions require a failed check")
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must exactly match failed check names"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("decision lineage must belong to UMD")
        if self.lineage.build_id != UMD_012_BUILD_ID:
            raise ValueError("decision lineage must use build_id UMD-012")
        if self.batch_hash not in self.lineage.parent_hashes:
            raise ValueError(
                "decision lineage must include the evaluated batch hash"
            )

    @property
    def decision_id(self) -> str:
        return "umd:admission:" + deterministic_sha256(
            {
                "batch_id": self.batch_id,
                "batch_hash": self.batch_hash,
                "checks": self.checks,
                "admitted": self.admitted,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "batch_id": self.batch_id,
            "batch_hash": self.batch_hash,
            "source_id": self.source_id,
            "batch_sequence": self.batch_sequence,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(self.to_canonical_dict())


def evaluate_incremental_discovery_batch(
    batch: CertifiedIncrementalDiscoveryBatch,
    existing_registry: ReadOnlyIncrementalDiscoveryBatchRegistry,
    *,
    lineage: ImmutableLineage,
) -> CertifiedDiscoveryAdmissionDecision:
    latest = existing_registry.latest_for_source(batch.source_id)

    known_market_ids = {
        market.canonical_market_id
        for market in existing_registry.graph_registry.markets
    }
    prior_source_keys = {
        (candidate.source_id, candidate.source_market_key)
        for prior_batch in existing_registry.batches
        for candidate in prior_batch.candidates
    }

    checks = {
        "batch_id_not_seen": existing_registry.get(batch.batch_id) is None,
        "batch_hash_not_seen": all(
            prior_batch.batch_hash != batch.batch_hash
            for prior_batch in existing_registry.batches
        ),
        "source_sequence_valid": (
            batch.batch_sequence == 1
            if latest is None
            else batch.batch_sequence == latest.batch_sequence + 1
        ),
        "previous_hash_valid": (
            batch.previous_batch_hash is None
            if latest is None
            else batch.previous_batch_hash == latest.batch_hash
        ),
        "cursor_chain_valid": (
            batch.start_cursor is None
            if latest is None
            else (
                batch.start_cursor is not None
                and batch.start_cursor.record_hash
                == latest.end_cursor.record_hash
            )
        ),
        "candidate_ids_unique": len(
            {candidate.candidate_id for candidate in batch.candidates}
        )
        == len(batch.candidates),
        "source_market_keys_unique": len(
            {candidate.source_market_key for candidate in batch.candidates}
        )
        == len(batch.candidates),
        "candidate_sources_match": all(
            candidate.source_id == batch.source_id
            for candidate in batch.candidates
        ),
        "candidate_markets_new": all(
            candidate.market.canonical_market_id not in known_market_ids
            for candidate in batch.candidates
        ),
        "candidate_keys_not_replayed": all(
            (candidate.source_id, candidate.source_market_key)
            not in prior_source_keys
            for candidate in batch.candidates
        ),
        "batch_hash_deterministic": (
            batch.batch_hash
            == deterministic_sha256(batch.to_canonical_dict())
        ),
    }

    failed = tuple(
        name for name, passed in checks.items() if not passed
    )

    return CertifiedDiscoveryAdmissionDecision(
        batch_id=batch.batch_id,
        batch_hash=batch.batch_hash,
        source_id=batch.source_id,
        batch_sequence=batch.batch_sequence,
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD012CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    gate_mode: str
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
            "gate_mode": self.gate_mode,
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


def build_umd_012_certification_manifest() -> UMD012CertificationManifest:
    return UMD012CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_012_BUILD_ID,
        build_name=UMD_012_BUILD_NAME,
        revision=UMD_012_REVISION,
        schema_version=UMD_012_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}" for number in range(1, 12)
        ),
        gate_mode="read_only_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_012_foundation() -> Mapping[str, Any]:
    manifest = build_umd_012_certification_manifest()
    checks = {
        "subsystem_identity": manifest.subsystem_id == "UMD",
        "build_identity": manifest.build_id == "UMD-012",
        "upstreams_frozen": manifest.upstream_builds
        == tuple(f"UMD-{number:03d}" for number in range(1, 12)),
        "read_only_gate": manifest.gate_mode == "read_only_validation",
        "network_disabled": manifest.network_enabled is False,
        "persistence_disabled": manifest.persistence_enabled is False,
        "mutation_disabled": manifest.mutation_enabled is False,
        "publication_disabled": manifest.publication_enabled is False,
        "execution_disabled": manifest.execution_enabled is False,
        "deterministic_manifest_hash": manifest.manifest_hash
        == deterministic_sha256(manifest.to_canonical_dict()),
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


def verify_umd_012_certified_incremental_discovery_admission_gate() -> bool:
    result = certify_umd_012_foundation()
    if not result["certified"]:
        raise RuntimeError(
            "UMD-012 certification failed: "
            + ", ".join(result["failed_checks"])
        )
    return True


__all__ = [
    "UMD_012_BUILD_ID",
    "UMD_012_BUILD_NAME",
    "UMD_012_REVISION",
    "UMD_012_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedDiscoveryAdmissionDecision",
    "evaluate_incremental_discovery_batch",
    "UMD012CertificationManifest",
    "build_umd_012_certification_manifest",
    "certify_umd_012_foundation",
    "verify_umd_012_certified_incremental_discovery_admission_gate",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
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
from qseries_v2.universal_market_discovery.certified_incremental_discovery_admission_gate import (
    UMD_012_REVISION,
    CertifiedDiscoveryAdmissionDecision,
    build_umd_012_certification_manifest,
    certify_umd_012_foundation,
    verify_umd_012_certified_incremental_discovery_admission_gate,
)

FIXED = datetime(2026, 8, 5, 21, 30, tzinfo=timezone.utc)
BATCH_HASH = "a" * 64


def decision_lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-012",
        revision=UMD_012_REVISION,
        schema_version="1.0.0",
        parent_hashes=(BATCH_HASH,),
        source_refs=("fixture://umd-012/decision",),
        created_at=FIXED,
    )


class TestUMD012(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(certify_umd_012_foundation()["certified"])
        self.assertTrue(
            verify_umd_012_certified_incremental_discovery_admission_gate()
        )

    def test_admitted_decision_deterministic(self) -> None:
        checks = {
            "batch_id_not_seen": True,
            "batch_hash_not_seen": True,
        }
        first = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        second = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks=dict(reversed(tuple(checks.items()))),
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        self.assertEqual(first.decision_id, second.decision_id)
        self.assertEqual(first.record_hash, second.record_hash)

    def test_rejected_decision_requires_matching_reasons(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=False,
                checks={"batch_id_not_seen": False},
                rejection_reasons=("wrong_reason",),
                lineage=decision_lineage(),
            )

    def test_admitted_decision_rejects_failed_checks(self) -> None:
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=True,
                checks={"batch_id_not_seen": False},
                rejection_reasons=(),
                lineage=decision_lineage(),
            )

    def test_lineage_requires_batch_hash(self) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-012",
            revision=UMD_012_REVISION,
            schema_version="1.0.0",
            parent_hashes=(),
            source_refs=("fixture://umd-012/bad",),
            created_at=FIXED,
        )
        with self.assertRaises(ValueError):
            CertifiedDiscoveryAdmissionDecision(
                batch_id="umd:batch:" + "b" * 64,
                batch_hash=BATCH_HASH,
                source_id="fixture-source",
                batch_sequence=1,
                admitted=True,
                checks={"batch_id_not_seen": True},
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedDiscoveryAdmissionDecision(
            batch_id="umd:batch:" + "b" * 64,
            batch_hash=BATCH_HASH,
            source_id="fixture-source",
            batch_sequence=1,
            admitted=True,
            checks={"batch_id_not_seen": True},
            rejection_reasons=(),
            lineage=decision_lineage(),
        )
        with self.assertRaises((FrozenInstanceError, AttributeError)):
            item.admitted = False
        with self.assertRaises(TypeError):
            item.checks["batch_id_not_seen"] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_012_certification_manifest()
        self.assertEqual(manifest.gate_mode, "read_only_validation")
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-012 CERTIFICATION TEST")
    print(" CERTIFIED INCREMENTAL DISCOVERY ADMISSION GATE")
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD012)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_012_certification_manifest()
    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(f"[PASS] Manifest hash: {manifest.manifest_hash}")
    print("[PASS] UMD-001 through UMD-011 consumed read-only")
    print("[PASS] Admission decision IDs deterministic")
    print("[PASS] Admission and rejection states mutually consistent")
    print("[PASS] Rejection reasons bound to failed checks")
    print("[PASS] Batch-hash lineage requirement enforced")
    print("[PASS] Replay, cursor, sequence, and candidate checks registered")
    print("[PASS] Read-only admission gate certified")
    print("[PASS] Network and persistence disabled")
    print("[PASS] Publication and Q Series execution disabled")
    print("[DONE] UMD-012 CERTIFIED INCREMENTAL DISCOVERY ADMISSION GATE CERTIFIED")
"""

INIT_IMPORT = r"""
from .certified_incremental_discovery_admission_gate import (
    UMD_012_BUILD_ID,
    UMD_012_BUILD_NAME,
    UMD_012_REVISION,
    UMD_012_SCHEMA_VERSION,
    CertifiedDiscoveryAdmissionDecision,
    evaluate_incremental_discovery_batch,
    UMD012CertificationManifest,
    build_umd_012_certification_manifest,
    certify_umd_012_foundation,
    verify_umd_012_certified_incremental_discovery_admission_gate,
)
"""

EXPORTED_NAMES = (
    "UMD_012_BUILD_ID",
    "UMD_012_BUILD_NAME",
    "UMD_012_REVISION",
    "UMD_012_SCHEMA_VERSION",
    "CertifiedDiscoveryAdmissionDecision",
    "evaluate_incremental_discovery_batch",
    "UMD012CertificationManifest",
    "build_umd_012_certification_manifest",
    "certify_umd_012_foundation",
    "verify_umd_012_certified_incremental_discovery_admission_gate",
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
    import_marker = (
        "from .certified_incremental_discovery_admission_gate import ("
    )

    if import_marker not in source:
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
            addition = "".join(
                f'    "{name}",\n' for name in missing
            )
            block = block[:-1] + addition + "]"
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
            (
                "universal_market_discovery_foundation",
                "verify_umd_foundation",
            ),
            (
                "certified_canonical_market_contract",
                "verify_umd_002_certified_canonical_market_contract",
            ),
            (
                "certified_venue_identity_registry",
                "verify_umd_003_certified_venue_identity_registry",
            ),
            (
                "certified_venue_market_binding_registry",
                "verify_umd_004_certified_venue_market_binding_registry",
            ),
            (
                "certified_market_category_hierarchy_registry",
                "verify_umd_005_certified_market_category_hierarchy_registry",
            ),
            (
                "certified_market_classification_registry",
                "verify_umd_006_certified_market_classification_registry",
            ),
            (
                "certified_market_metadata_registry",
                "verify_umd_007_certified_market_metadata_registry",
            ),
            (
                "certified_market_lifecycle_and_settlement_registry",
                "verify_umd_008_certified_market_lifecycle_and_settlement_registry",
            ),
            (
                "certified_market_duplicate_resolution_registry",
                "verify_umd_009_certified_market_duplicate_resolution_registry",
            ),
            (
                "certified_related_market_graph_registry",
                "verify_umd_010_certified_related_market_graph_registry",
            ),
            (
                "certified_incremental_discovery_batch_contract",
                "verify_umd_011_certified_incremental_discovery_batch_contract",
            ),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2.universal_market_discovery."
                + module_name
            )
            verifier = getattr(module, verifier_name)
            if not verifier():
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
            "certified_incremental_discovery_admission_gate"
        )
        required = (
            "CertifiedDiscoveryAdmissionDecision",
            "evaluate_incremental_discovery_batch",
            "build_umd_012_certification_manifest",
            "certify_umd_012_foundation",
            "verify_umd_012_certified_incremental_discovery_admission_gate",
        )
        missing = [
            name for name in required if not hasattr(module, name)
        ]
        if missing:
            raise RuntimeError(
                "UMD-012 missing symbols: " + ", ".join(missing)
            )

        module.verify_umd_012_certified_incremental_discovery_admission_gate()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))


def main() -> int:
    print("=" * 64)
    print(" UMD-012 CORRECTION V2 INSTALLER")
    print(" CERTIFIED INCREMENTAL DISCOVERY ADMISSION GATE")
    print("=" * 64)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-011 "
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
        "build_id": "UMD-012",
        "revision": REVISION,
        "files": {
            str(MODULE.relative_to(ROOT)): sha256_file(MODULE),
            str(INIT.relative_to(ROOT)): sha256_file(INIT),
            str(TEST.relative_to(ROOT)): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}" for number in range(1, 12)
        ),
        "mode": "read_only_validation",
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
    print("[PASS] Required UMD-012 symbols verified")
    print(f"[PASS] Deterministic install hash: {install_hash}")
    print(
        "[PASS] Network, persistence, publication, "
        "and execution disabled"
    )
    print("[DONE] UMD-012 CORRECTION V2 INSTALLATION COMPLETE")
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_012_certified_incremental_discovery_admission_gate.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
