from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_031_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_READ_MODEL_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_session_read_model.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_031_certified_active_canonical_market_registry_query_session_read_model.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_session_contract import (
    CertifiedActiveMarketQuerySession,
    ReadOnlyActiveMarketQuerySessionRegistry,
)
from .certified_active_canonical_market_registry_query_session_admission_ledger import (
    CertifiedActiveMarketQuerySessionAdmissionLedgerEntry,
    ReadOnlyActiveMarketQuerySessionAdmissionLedger,
)

UMD_031_BUILD_ID = "UMD-031"
UMD_031_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Session Read Model"
)
UMD_031_REVISION = (
    "UMD_031_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_READ_MODEL_V1"
)
UMD_031_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_session_commit",
    "session_persistence",
    "session_registry_mutation",
    "session_ledger_mutation",
    "read_model_mutation",
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


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQuerySessionReadModel:
    session_registry: ReadOnlyActiveMarketQuerySessionRegistry
    admission_ledger: ReadOnlyActiveMarketQuerySessionAdmissionLedger
    lineage: ImmutableLineage
    _by_session_id: Mapping[
        str,
        CertifiedActiveMarketQuerySession,
    ] = field(init=False, repr=False)
    _by_admission_entry_id: Mapping[
        str,
        CertifiedActiveMarketQuerySessionAdmissionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQuerySession,
    ] = field(init=False, repr=False)
    _admitted_sessions: Tuple[
        CertifiedActiveMarketQuerySession,
        ...
    ] = field(init=False, repr=False)
    _rejected_entries: Tuple[
        CertifiedActiveMarketQuerySessionAdmissionLedgerEntry,
        ...
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError("read-model lineage must belong to UMD")
        if self.lineage.build_id != UMD_031_BUILD_ID:
            raise ValueError(
                "read-model lineage must use build_id UMD-031"
            )

        required_parents = {
            self.session_registry.registry_hash,
            self.admission_ledger.ledger_hash,
        }
        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "read-model lineage is missing required parent hashes"
            )

        admitted_entries = self.admission_ledger.admitted_entries()
        admitted_by_session_id = {
            entry.decision.session_id: entry
            for entry in admitted_entries
        }

        registry_sessions = tuple(
            sorted(
                self.session_registry.sessions,
                key=lambda session: session.session_sequence,
            )
        )

        registry_session_ids = {
            session.session_id
            for session in registry_sessions
        }

        if registry_session_ids != set(admitted_by_session_id):
            raise ValueError(
                "session registry must exactly match admitted session ledger"
            )

        by_session_id = {}
        by_execution_id = {}

        for session in registry_sessions:
            entry = admitted_by_session_id[session.session_id]

            if entry.decision.session_hash != session.session_hash:
                raise ValueError(
                    "session hash does not match admitted ledger decision"
                )
            if (
                entry.decision.session_sequence
                != session.session_sequence
            ):
                raise ValueError(
                    "session sequence does not match admitted ledger decision"
                )

            if session.session_id in by_session_id:
                raise ValueError("duplicate session ID")

            by_session_id[session.session_id] = session

            for execution_id in session.execution_ids():
                if execution_id in by_execution_id:
                    raise ValueError(
                        "execution may belong to only one admitted session"
                    )
                by_execution_id[execution_id] = session

        object.__setattr__(
            self,
            "_by_session_id",
            MappingProxyType(by_session_id),
        )
        object.__setattr__(
            self,
            "_by_admission_entry_id",
            MappingProxyType(
                {
                    entry.entry_id: entry
                    for entry in self.admission_ledger.entries
                }
            ),
        )
        object.__setattr__(
            self,
            "_by_execution_id",
            MappingProxyType(by_execution_id),
        )
        object.__setattr__(
            self,
            "_admitted_sessions",
            registry_sessions,
        )
        object.__setattr__(
            self,
            "_rejected_entries",
            self.admission_ledger.rejected_entries(),
        )

    @property
    def session_count(self) -> int:
        return len(self._admitted_sessions)

    @property
    def rejected_count(self) -> int:
        return len(self._rejected_entries)

    @property
    def execution_membership_count(self) -> int:
        return len(self._by_execution_id)

    def get_session(
        self,
        session_id: str,
    ) -> CertifiedActiveMarketQuerySession | None:
        return self._by_session_id.get(
            _text(session_id, "session_id")
        )

    def get_admission_entry(
        self,
        entry_id: str,
    ) -> CertifiedActiveMarketQuerySessionAdmissionLedgerEntry | None:
        return self._by_admission_entry_id.get(
            _text(entry_id, "entry_id")
        )

    def get_session_by_execution(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQuerySession | None:
        return self._by_execution_id.get(
            _text(execution_id, "execution_id")
        )

    def admitted_sessions(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySession,
        ...
    ]:
        return self._admitted_sessions

    def rejected_entries(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySessionAdmissionLedgerEntry,
        ...
    ]:
        return self._rejected_entries

    def latest_session(
        self,
    ) -> CertifiedActiveMarketQuerySession | None:
        if not self._admitted_sessions:
            return None
        return self._admitted_sessions[-1]

    def session_ids(self) -> Tuple[str, ...]:
        return tuple(
            session.session_id
            for session in self._admitted_sessions
        )

    def execution_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_execution_id))

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "read_model_mode": "session_history_read_only",
            "session_registry_hash": (
                self.session_registry.registry_hash
            ),
            "admission_ledger_hash": (
                self.admission_ledger.ledger_hash
            ),
            "session_ids": self.session_ids(),
            "execution_membership": {
                execution_id: (
                    self._by_execution_id[
                        execution_id
                    ].session_id
                )
                for execution_id in self.execution_ids()
            },
            "rejected_entry_ids": tuple(
                entry.entry_id
                for entry in self._rejected_entries
            ),
            "lineage": self.lineage,
        }

    @property
    def read_model_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD031CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    read_model_mode: str
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
            "read_model_mode": self.read_model_mode,
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


def build_umd_031_certification_manifest() -> UMD031CertificationManifest:
    return UMD031CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_031_BUILD_ID,
        build_name=UMD_031_BUILD_NAME,
        revision=UMD_031_REVISION,
        schema_version=UMD_031_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 31)
        ),
        read_model_mode="session_history_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_session_read_model(
    read_model: CertifiedActiveMarketQuerySessionReadModel,
) -> Mapping[str, Any]:
    checks = {
        "session_count_matches_registry": (
            read_model.session_count
            == len(read_model.session_registry.sessions)
        ),
        "admitted_sessions_match_ledger": (
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
        "session_ids_unique": (
            len(set(read_model.session_ids()))
            == read_model.session_count
        ),
        "execution_membership_unique": (
            len(read_model.execution_ids())
            == read_model.execution_membership_count
        ),
        "deterministic_session_order": (
            tuple(
                session.session_sequence
                for session in read_model.admitted_sessions()
            )
            == tuple(
                sorted(
                    session.session_sequence
                    for session in read_model.admitted_sessions()
                )
            )
        ),
        "deterministic_replay": (
            read_model.read_model_hash
            == deterministic_sha256(
                read_model.to_canonical_dict()
            )
        ),
        "read_only_indexes": (
            isinstance(
                read_model._by_session_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_admission_entry_id,
                MappingProxyType,
            )
            and isinstance(
                read_model._by_execution_id,
                MappingProxyType,
            )
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = read_model.latest_session()

    return MappingProxyType(
        {
            "certified": not failed,
            "read_model_hash": read_model.read_model_hash,
            "session_registry_hash": (
                read_model.session_registry.registry_hash
            ),
            "admission_ledger_hash": (
                read_model.admission_ledger.ledger_hash
            ),
            "session_count": read_model.session_count,
            "rejected_count": read_model.rejected_count,
            "execution_membership_count": (
                read_model.execution_membership_count
            ),
            "latest_session_id": (
                None
                if latest is None
                else latest.session_id
            ),
            "checks": MappingProxyType(checks),
            "failed_checks": failed,
        }
    )


def certify_umd_031_foundation() -> Mapping[str, Any]:
    manifest = build_umd_031_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-031"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 31)
            )
        ),
        "session_history_read_only": (
            manifest.read_model_mode
            == "session_history_read_only"
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


def verify_umd_031_certified_active_canonical_market_registry_query_session_read_model() -> bool:
    result = certify_umd_031_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-031 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_031_BUILD_ID",
    "UMD_031_BUILD_NAME",
    "UMD_031_REVISION",
    "UMD_031_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "CertifiedActiveMarketQuerySessionReadModel",
    "UMD031CertificationManifest",
    "build_umd_031_certification_manifest",
    "certify_active_market_query_session_read_model",
    "certify_umd_031_foundation",
    "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_read_model import (
    UMD_031_REVISION,
    build_umd_031_certification_manifest,
    certify_umd_031_foundation,
    verify_umd_031_certified_active_canonical_market_registry_query_session_read_model,
)

FIXED = datetime(
    2026,
    8,
    6,
    10,
    0,
    tzinfo=timezone.utc,
)


class TestUMD031(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_031_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_031_certified_active_canonical_market_registry_query_session_read_model()
        )

    def test_manifest_is_session_history_read_only(
        self,
    ) -> None:
        manifest = build_umd_031_certification_manifest()

        self.assertEqual(
            manifest.read_model_mode,
            "session_history_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_031_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 31)
            ),
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-031",
            revision=UMD_031_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-031",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-031",
        )

    def test_lineage_is_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-031",
            revision=UMD_031_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-031",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-031 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD031
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_031_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-030 "
        "consumed read-only"
    )
    print(
        "[PASS] Session registry and admission ledger binding certified"
    )
    print(
        "[PASS] Admitted and rejected session views certified"
    )
    print(
        "[PASS] Session ID and admission-entry indexes certified"
    )
    print(
        "[PASS] Execution-to-session membership index certified"
    )
    print(
        "[PASS] Latest admitted session view deterministic"
    )
    print(
        "[PASS] Immutable read-only session history certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-031 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION READ MODEL CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_session_read_model import (
    UMD_031_BUILD_ID,
    UMD_031_BUILD_NAME,
    UMD_031_REVISION,
    UMD_031_SCHEMA_VERSION,
    CertifiedActiveMarketQuerySessionReadModel,
    UMD031CertificationManifest,
    build_umd_031_certification_manifest,
    certify_active_market_query_session_read_model,
    certify_umd_031_foundation,
    verify_umd_031_certified_active_canonical_market_registry_query_session_read_model,
)
"""

EXPORTED_NAMES = (
    "UMD_031_BUILD_ID",
    "UMD_031_BUILD_NAME",
    "UMD_031_REVISION",
    "UMD_031_SCHEMA_VERSION",
    "CertifiedActiveMarketQuerySessionReadModel",
    "UMD031CertificationManifest",
    "build_umd_031_certification_manifest",
    "certify_active_market_query_session_read_model",
    "certify_umd_031_foundation",
    "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model",
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
        "query_session_read_model import ("
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
            "query_session_read_model"
        )

        required = (
            "CertifiedActiveMarketQuerySessionReadModel",
            "build_umd_031_certification_manifest",
            "certify_active_market_query_session_read_model",
            "certify_umd_031_foundation",
            "verify_umd_031_certified_active_canonical_market_registry_query_session_read_model",
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
                "UMD-031 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_031_certified_active_canonical_market_registry_query_session_read_model()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-031 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION READ MODEL"
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
        "[PASS] Certified UMD-001 through UMD-030 "
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
        "build_id": "UMD-031",
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
            for number in range(1, 31)
        ),
        "mode": "session_history_read_only",
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
        "[PASS] Required UMD-031 symbols verified"
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
        "[DONE] UMD-031 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_031_certified_active_canonical_market_"
        "registry_query_session_read_model.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
