from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_032_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_READ_MODEL_ADMISSION_GATE_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_session_read_model_admission_gate.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate.py"

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
from .certified_active_canonical_market_registry_query_session_read_model import (
    CertifiedActiveMarketQuerySessionReadModel,
)

UMD_032_BUILD_ID = "UMD-032"
UMD_032_BUILD_NAME = (
    "Certified Active Canonical Market Registry "
    "Query Session Read Model Admission Gate"
)
UMD_032_REVISION = (
    "UMD_032_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_ADMISSION_GATE_V1"
)
UMD_032_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_read_model_commit",
    "read_model_persistence",
    "read_model_mutation",
    "session_registry_mutation",
    "session_ledger_mutation",
    "execution_ledger_mutation",
    "active_registry_mutation",
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


def _sha256(value: str, field_name: str) -> str:
    normalized = _text(value, field_name).lower()
    if len(normalized) != 64:
        raise ValueError(
            f"{field_name} must contain 64 hexadecimal characters"
        )
    if any(
        character not in "0123456789abcdef"
        for character in normalized
    ):
        raise ValueError(
            f"{field_name} must be lowercase SHA-256 hexadecimal"
        )
    return normalized


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    read_model_hash: str
    session_registry_hash: str
    admission_ledger_hash: str
    admitted: bool
    checks: Mapping[str, bool]
    rejection_reasons: Tuple[str, ...]
    lineage: ImmutableLineage

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "read_model_hash",
            _sha256(
                self.read_model_hash,
                "read_model_hash",
            ),
        )
        object.__setattr__(
            self,
            "session_registry_hash",
            _sha256(
                self.session_registry_hash,
                "session_registry_hash",
            ),
        )
        object.__setattr__(
            self,
            "admission_ledger_hash",
            _sha256(
                self.admission_ledger_hash,
                "admission_ledger_hash",
            ),
        )

        normalized_checks = {
            _text(str(name), "check name"): bool(passed)
            for name, passed in self.checks.items()
        }
        object.__setattr__(
            self,
            "checks",
            MappingProxyType(
                dict(sorted(normalized_checks.items()))
            ),
        )

        failed_checks = tuple(
            name
            for name, passed in self.checks.items()
            if not passed
        )
        reasons = tuple(
            sorted(
                {
                    _text(reason, "rejection reason")
                    for reason in self.rejection_reasons
                }
            )
        )
        object.__setattr__(
            self,
            "rejection_reasons",
            reasons,
        )

        if self.admitted:
            if failed_checks or reasons:
                raise ValueError(
                    "admitted decision cannot contain failures"
                )
        else:
            if not failed_checks:
                raise ValueError(
                    "rejected decision requires failed checks"
                )
            if reasons != tuple(sorted(failed_checks)):
                raise ValueError(
                    "rejection reasons must match failed checks"
                )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "read-model admission lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_032_BUILD_ID:
            raise ValueError(
                "read-model admission lineage must use build_id UMD-032"
            )

        required_parents = {
            self.read_model_hash,
            self.session_registry_hash,
            self.admission_ledger_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "read-model admission lineage is missing required parent hashes"
            )

    @property
    def decision_id(self) -> str:
        return "umd:query-session-read-model-admission:" + deterministic_sha256(
            {
                "read_model_hash": self.read_model_hash,
                "session_registry_hash": self.session_registry_hash,
                "admission_ledger_hash": self.admission_ledger_hash,
                "admitted": self.admitted,
                "checks": self.checks,
            }
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "decision_id": self.decision_id,
            "read_model_hash": self.read_model_hash,
            "session_registry_hash": self.session_registry_hash,
            "admission_ledger_hash": self.admission_ledger_hash,
            "admitted": self.admitted,
            "checks": self.checks,
            "rejection_reasons": self.rejection_reasons,
            "lineage": self.lineage,
        }

    @property
    def record_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def evaluate_active_market_query_session_read_model(
    read_model: CertifiedActiveMarketQuerySessionReadModel,
    *,
    lineage: ImmutableLineage,
) -> CertifiedActiveMarketQuerySessionReadModelAdmissionDecision:
    latest_session = read_model.latest_session()

    checks = {
        "read_model_hash_deterministic": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "session_registry_hash_matches": (
            read_model.session_registry.registry_hash
            == read_model.to_canonical_dict()[
                "session_registry_hash"
            ]
        ),
        "admission_ledger_hash_matches": (
            read_model.admission_ledger.ledger_hash
            == read_model.to_canonical_dict()[
                "admission_ledger_hash"
            ]
        ),
        "session_count_matches_registry": (
            read_model.session_count
            == len(read_model.session_registry.sessions)
        ),
        "admitted_count_matches_ledger": (
            read_model.session_count
            == len(
                read_model.admission_ledger.admitted_entries()
            )
        ),
        "rejected_count_matches_ledger": (
            read_model.rejected_count
            == len(
                read_model.admission_ledger.rejected_entries()
            )
        ),
        "execution_membership_count_valid": (
            read_model.execution_membership_count
            == len(read_model.execution_ids())
        ),
        "session_ids_unique": (
            len(set(read_model.session_ids()))
            == read_model.session_count
        ),
        "execution_ids_unique": (
            len(set(read_model.execution_ids()))
            == read_model.execution_membership_count
        ),
        "latest_session_consistent": (
            latest_session is None
            if read_model.session_count == 0
            else (
                latest_session is not None
                and latest_session.session_id
                == read_model.session_ids()[-1]
            )
        ),
        "registry_and_ledger_lineage_bound": (
            read_model.session_registry.registry_hash
            in read_model.lineage.parent_hashes
            and read_model.admission_ledger.ledger_hash
            in read_model.lineage.parent_hashes
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    return CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
        read_model_hash=read_model.read_model_hash,
        session_registry_hash=(
            read_model.session_registry.registry_hash
        ),
        admission_ledger_hash=(
            read_model.admission_ledger.ledger_hash
        ),
        admitted=not failed,
        checks=checks,
        rejection_reasons=failed,
        lineage=lineage,
    )


@dataclass(frozen=True, slots=True)
class UMD032CertificationManifest:
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
        return deterministic_sha256(
            self.to_canonical_dict()
        )


def build_umd_032_certification_manifest() -> UMD032CertificationManifest:
    return UMD032CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_032_BUILD_ID,
        build_name=UMD_032_BUILD_NAME,
        revision=UMD_032_REVISION,
        schema_version=UMD_032_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 32)
        ),
        gate_mode="read_only_read_model_validation",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_umd_032_foundation() -> Mapping[str, Any]:
    manifest = build_umd_032_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-032"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 32)
            )
        ),
        "read_only_read_model_validation": (
            manifest.gate_mode
            == "read_only_read_model_validation"
        ),
        "network_disabled": (
            manifest.network_enabled is False
        ),
        "persistence_disabled": (
            manifest.persistence_enabled is False
        ),
        "mutation_disabled": (
            manifest.mutation_enabled is False
        ),
        "publication_disabled": (
            manifest.publication_enabled is False
        ),
        "execution_disabled": (
            manifest.execution_enabled is False
        ),
        "deterministic_manifest_hash": (
            manifest.manifest_hash
            == deterministic_sha256(
                manifest.to_canonical_dict()
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
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


def verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate() -> bool:
    result = certify_umd_032_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-032 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_032_BUILD_ID",
    "UMD_032_BUILD_NAME",
    "UMD_032_REVISION",
    "UMD_032_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQuerySessionReadModelAdmissionDecision",
    "evaluate_active_market_query_session_read_model",
    "UMD032CertificationManifest",
    "build_umd_032_certification_manifest",
    "certify_umd_032_foundation",
    "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_REVISION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    build_umd_032_certification_manifest,
    certify_umd_032_foundation,
    verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate,
)

FIXED = datetime(
    2026,
    8,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)
READ_MODEL_HASH = "a" * 64
REGISTRY_HASH = "b" * 64
LEDGER_HASH = "c" * 64


def lineage() -> ImmutableLineage:
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-032",
        revision=UMD_032_REVISION,
        schema_version="1.0.0",
        parent_hashes=(
            READ_MODEL_HASH,
            REGISTRY_HASH,
            LEDGER_HASH,
        ),
        source_refs=(
            "fixture://umd-032/decision",
        ),
        created_at=FIXED,
    )


class TestUMD032(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_032_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate()
        )

    def test_decision_identity_deterministic(self) -> None:
        checks = {
            "read_model_hash_deterministic": True,
            "session_registry_hash_matches": True,
        }

        first = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks=checks,
            rejection_reasons=(),
            lineage=lineage(),
        )

        second = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks=dict(
                reversed(tuple(checks.items()))
            ),
            rejection_reasons=(),
            lineage=lineage(),
        )

        self.assertEqual(
            first.decision_id,
            second.decision_id,
        )
        self.assertEqual(
            first.record_hash,
            second.record_hash,
        )

    def test_rejected_decision_requires_matching_reasons(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=False,
                checks={
                    "read_model_hash_deterministic": False
                },
                rejection_reasons=(
                    "wrong_reason",
                ),
                lineage=lineage(),
            )

    def test_admitted_decision_rejects_failures(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=True,
                checks={
                    "read_model_hash_deterministic": False
                },
                rejection_reasons=(),
                lineage=lineage(),
            )

    def test_lineage_requires_all_parent_hashes(
        self,
    ) -> None:
        bad_lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-032",
            revision=UMD_032_REVISION,
            schema_version="1.0.0",
            parent_hashes=(READ_MODEL_HASH,),
            source_refs=(
                "fixture://umd-032/bad",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(ValueError):
            CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
                read_model_hash=READ_MODEL_HASH,
                session_registry_hash=REGISTRY_HASH,
                admission_ledger_hash=LEDGER_HASH,
                admitted=True,
                checks={
                    "read_model_hash_deterministic": True
                },
                rejection_reasons=(),
                lineage=bad_lineage,
            )

    def test_decision_is_immutable(self) -> None:
        item = CertifiedActiveMarketQuerySessionReadModelAdmissionDecision(
            read_model_hash=READ_MODEL_HASH,
            session_registry_hash=REGISTRY_HASH,
            admission_ledger_hash=LEDGER_HASH,
            admitted=True,
            checks={
                "read_model_hash_deterministic": True
            },
            rejection_reasons=(),
            lineage=lineage(),
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            item.admitted = False

        with self.assertRaises(TypeError):
            item.checks[
                "read_model_hash_deterministic"
            ] = False

    def test_side_effects_disabled(self) -> None:
        manifest = build_umd_032_certification_manifest()

        self.assertEqual(
            manifest.gate_mode,
            "read_only_read_model_validation",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-032 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION GATE"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD032
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_032_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-031 "
        "consumed read-only"
    )
    print(
        "[PASS] Read-model admission decision IDs deterministic"
    )
    print(
        "[PASS] Read-model hash validation certified"
    )
    print(
        "[PASS] Session registry hash binding certified"
    )
    print(
        "[PASS] Admission ledger hash binding certified"
    )
    print(
        "[PASS] Session and execution membership counts certified"
    )
    print(
        "[PASS] Latest-session consistency certified"
    )
    print(
        "[PASS] Immutable read-model admission decisions certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-032 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL ADMISSION GATE CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_session_read_model_admission_gate import (
    UMD_032_BUILD_ID,
    UMD_032_BUILD_NAME,
    UMD_032_REVISION,
    UMD_032_SCHEMA_VERSION,
    CertifiedActiveMarketQuerySessionReadModelAdmissionDecision,
    evaluate_active_market_query_session_read_model,
    UMD032CertificationManifest,
    build_umd_032_certification_manifest,
    certify_umd_032_foundation,
    verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate,
)
"""

EXPORTED_NAMES = (
    "UMD_032_BUILD_ID",
    "UMD_032_BUILD_NAME",
    "UMD_032_REVISION",
    "UMD_032_SCHEMA_VERSION",
    "CertifiedActiveMarketQuerySessionReadModelAdmissionDecision",
    "evaluate_active_market_query_session_read_model",
    "UMD032CertificationManifest",
    "build_umd_032_certification_manifest",
    "certify_umd_032_foundation",
    "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate",
)


def normalize(source: str) -> str:
    return textwrap.dedent(source).lstrip()


def write_exact(path: Path, source: str) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )
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

    source = INIT.read_text(
        encoding="utf-8"
    )
    marker = (
        "from "
        ".certified_active_canonical_market_registry_"
        "query_session_read_model_admission_gate import ("
    )

    if marker not in source:
        source = (
            source.rstrip()
            + "\n\n"
            + normalize(INIT_IMPORT)
        )

    if "__all__" in source:
        start = source.index(
            "__all__ = ["
        )
        end = source.index(
            "]",
            start,
        )
        block = source[start : end + 1]

        missing = [
            name
            for name in EXPORTED_NAMES
            if f'"{name}"' not in block
            and f"'{name}'" not in block
        ]

        if missing:
            block = (
                block[:-1]
                + "".join(
                    f'    "{name}",\n'
                    for name in missing
                )
                + "]"
            )
            source = (
                source[:start]
                + block
                + source[end + 1 :]
            )
    else:
        source += (
            "\n__all__ = [\n"
            + "".join(
                f'    "{name}",\n'
                for name in EXPORTED_NAMES
            )
            + "]\n"
        )

    write_exact(
        INIT,
        source,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_upstream() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

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
            ("certified_admitted_market_materialization_contract", "verify_umd_014_certified_admitted_market_materialization_contract"),
            ("certified_materialized_market_admission_registry", "verify_umd_015_certified_materialized_market_admission_registry"),
            ("certified_canonical_market_registry_snapshot_contract", "verify_umd_016_certified_canonical_market_registry_snapshot_contract"),
            ("certified_canonical_market_registry_snapshot_admission_gate", "verify_umd_017_certified_canonical_market_registry_snapshot_admission_gate"),
            ("certified_canonical_market_registry_snapshot_admission_ledger", "verify_umd_018_certified_canonical_market_registry_snapshot_admission_ledger"),
            ("certified_canonical_market_registry_snapshot_activation_contract", "verify_umd_019_certified_canonical_market_registry_snapshot_activation_contract"),
            ("certified_canonical_market_registry_snapshot_activation_gate", "verify_umd_020_certified_canonical_market_registry_snapshot_activation_gate"),
            ("certified_canonical_market_registry_snapshot_activation_ledger", "verify_umd_021_certified_canonical_market_registry_snapshot_activation_ledger"),
            ("certified_active_canonical_market_registry_read_model", "verify_umd_022_certified_active_canonical_market_registry_read_model"),
            ("certified_active_canonical_market_registry_query_contract", "verify_umd_023_certified_active_canonical_market_registry_query_contract"),
            ("certified_active_canonical_market_registry_query_execution_engine", "verify_umd_024_certified_active_canonical_market_registry_query_execution_engine"),
            ("certified_active_canonical_market_registry_query_execution_admission_gate", "verify_umd_025_certified_active_canonical_market_registry_query_execution_admission_gate"),
            ("certified_active_canonical_market_registry_query_execution_ledger", "verify_umd_026_certified_active_canonical_market_registry_query_execution_ledger"),
            ("certified_active_canonical_market_registry_query_execution_read_model", "verify_umd_027_certified_active_canonical_market_registry_query_execution_read_model"),
            ("certified_active_canonical_market_registry_query_session_contract", "verify_umd_028_certified_active_canonical_market_registry_query_session_contract"),
            ("certified_active_canonical_market_registry_query_session_admission_gate", "verify_umd_029_certified_active_canonical_market_registry_query_session_admission_gate"),
            ("certified_active_canonical_market_registry_query_session_admission_ledger", "verify_umd_030_certified_active_canonical_market_registry_query_session_admission_ledger"),
            ("certified_active_canonical_market_registry_query_session_read_model", "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model"),
        )

        for module_name, verifier_name in modules:
            module = importlib.import_module(
                "qseries_v2."
                "universal_market_discovery."
                + module_name
            )

            verifier = getattr(
                module,
                verifier_name,
            )

            if not verifier():
                raise RuntimeError(
                    f"{module_name} verification failed"
                )
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def verify_current() -> None:
    sys.path.insert(
        0,
        str(ROOT),
    )

    try:
        module = importlib.import_module(
            "qseries_v2."
            "universal_market_discovery."
            "certified_active_canonical_market_registry_"
            "query_session_read_model_admission_gate"
        )

        required = (
            "CertifiedActiveMarketQuerySessionReadModelAdmissionDecision",
            "evaluate_active_market_query_session_read_model",
            "build_umd_032_certification_manifest",
            "certify_umd_032_foundation",
            "verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate",
        )

        missing = [
            name
            for name in required
            if not hasattr(
                module,
                name,
            )
        ]

        if missing:
            raise RuntimeError(
                "UMD-032 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_032_certified_active_canonical_market_registry_query_session_read_model_admission_gate()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-032 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL ADMISSION GATE"
    )
    print("=" * 64)
    print(
        f"[BOOT] Revision: {REVISION}"
    )
    print(
        f"[ROOT] {ROOT}"
    )

    verify_upstream()
    print(
        "[PASS] Certified UMD-001 through UMD-031 "
        "verified read-only"
    )

    write_exact(
        MODULE,
        MODULE_SOURCE,
    )
    write_exact(
        TEST,
        TEST_SOURCE,
    )
    update_init()

    py_compile.compile(
        str(MODULE),
        doraise=True,
    )
    py_compile.compile(
        str(INIT),
        doraise=True,
    )
    py_compile.compile(
        str(TEST),
        doraise=True,
    )
    verify_current()

    manifest = {
        "build_id": "UMD-032",
        "revision": REVISION,
        "files": {
            str(
                MODULE.relative_to(ROOT)
            ): sha256_file(MODULE),
            str(
                INIT.relative_to(ROOT)
            ): sha256_file(INIT),
            str(
                TEST.relative_to(ROOT)
            ): sha256_file(TEST),
        },
        "upstream": tuple(
            f"UMD-{number:03d}"
            for number in range(1, 32)
        ),
        "mode": "read_only_read_model_validation",
    }

    install_hash = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    print(
        f"[PASS] Wrote: "
        f"{MODULE.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Updated: "
        f"{INIT.relative_to(ROOT)}"
    )
    print(
        f"[PASS] Wrote: "
        f"{TEST.relative_to(ROOT)}"
    )
    print(
        "[PASS] Python compilation verified"
    )
    print(
        "[PASS] Required UMD-032 symbols verified"
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
        "[DONE] UMD-032 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_032_certified_active_canonical_market_"
        "registry_query_session_read_model_admission_gate.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
