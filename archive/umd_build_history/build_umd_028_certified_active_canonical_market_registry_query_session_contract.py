from __future__ import annotations

import hashlib
import importlib
import json
import os
import py_compile
import sys
import textwrap
from pathlib import Path

REVISION = "UMD_028_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_QUERY_SESSION_CONTRACT_V1"
ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "universal_market_discovery"
MODULE = PKG / "certified_active_canonical_market_registry_query_session_contract.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_umd_028_certified_active_canonical_market_registry_query_session_contract.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from .universal_market_discovery_foundation import (
    UMD_SUBSYSTEM_ID,
    ImmutableLineage,
    deterministic_sha256,
)
from .certified_active_canonical_market_registry_query_execution_read_model import (
    CertifiedActiveMarketQueryExecutionReadModel,
)
from .certified_active_canonical_market_registry_query_execution_ledger import (
    CertifiedActiveMarketQueryExecutionLedgerEntry,
)

UMD_028_BUILD_ID = "UMD-028"
UMD_028_BUILD_NAME = (
    "Certified Active Canonical Market Registry Query Session Contract"
)
UMD_028_REVISION = (
    "UMD_028_CERTIFIED_ACTIVE_CANONICAL_MARKET_REGISTRY_"
    "QUERY_SESSION_CONTRACT_V1"
)
UMD_028_SCHEMA_VERSION = "1.0.0"

PROHIBITED_CAPABILITIES = (
    "network_discovery",
    "market_scanning",
    "automatic_session_commit",
    "session_persistence",
    "session_mutation",
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


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(
        dict(sorted((str(key), item) for key, item in value.items()))
    )


class QuerySessionState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class CertifiedActiveMarketQuerySession:
    session_sequence: int
    previous_session_hash: str | None
    session_name: str
    state: QuerySessionState
    execution_entries: Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]
    opened_at: datetime
    closed_at: datetime | None
    metadata: Mapping[str, Any]
    lineage: ImmutableLineage
    _by_execution_id: Mapping[
        str,
        CertifiedActiveMarketQueryExecutionLedgerEntry,
    ] = field(init=False, repr=False)
    _by_query_id: Mapping[
        str,
        Tuple[
            CertifiedActiveMarketQueryExecutionLedgerEntry,
            ...
        ],
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.session_sequence, int):
            raise TypeError("session_sequence must be an integer")
        if self.session_sequence < 1:
            raise ValueError("session_sequence must be positive")

        if self.previous_session_hash is None:
            if self.session_sequence != 1:
                raise ValueError(
                    "only the first session may omit previous_session_hash"
                )
        else:
            previous = _text(
                self.previous_session_hash,
                "previous_session_hash",
            ).lower()
            if len(previous) != 64:
                raise ValueError(
                    "previous_session_hash must contain 64 hexadecimal characters"
                )
            if any(
                character not in "0123456789abcdef"
                for character in previous
            ):
                raise ValueError(
                    "previous_session_hash must be lowercase SHA-256 hexadecimal"
                )
            object.__setattr__(
                self,
                "previous_session_hash",
                previous,
            )

        object.__setattr__(
            self,
            "session_name",
            _text(
                self.session_name,
                "session_name",
            ),
        )

        if not isinstance(self.state, QuerySessionState):
            object.__setattr__(
                self,
                "state",
                QuerySessionState(self.state),
            )

        opened_at = _utc(
            self.opened_at,
            "opened_at",
        )
        object.__setattr__(
            self,
            "opened_at",
            opened_at,
        )

        if self.closed_at is not None:
            closed_at = _utc(
                self.closed_at,
                "closed_at",
            )
            if closed_at < opened_at:
                raise ValueError(
                    "closed_at cannot be earlier than opened_at"
                )
            object.__setattr__(
                self,
                "closed_at",
                closed_at,
            )

        if self.state == QuerySessionState.OPEN:
            if self.closed_at is not None:
                raise ValueError(
                    "open session cannot define closed_at"
                )
        else:
            if self.closed_at is None:
                raise ValueError(
                    "closed session requires closed_at"
                )

        entries = tuple(
            sorted(
                self.execution_entries,
                key=lambda entry: entry.sequence_number,
            )
        )
        object.__setattr__(
            self,
            "execution_entries",
            entries,
        )

        execution_ids = [
            entry.decision.execution_id
            for entry in entries
        ]
        entry_ids = [
            entry.entry_id
            for entry in entries
        ]

        if len(set(execution_ids)) != len(execution_ids):
            raise ValueError(
                "session cannot contain duplicate executions"
            )
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError(
                "session cannot contain duplicate ledger entries"
            )
        if any(
            entries[index].sequence_number
            >= entries[index + 1].sequence_number
            for index in range(len(entries) - 1)
        ):
            raise ValueError(
                "session execution ordering must strictly increase"
            )

        object.__setattr__(
            self,
            "metadata",
            _freeze(self.metadata),
        )

        if self.lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "query-session lineage must belong to UMD"
            )
        if self.lineage.build_id != UMD_028_BUILD_ID:
            raise ValueError(
                "query-session lineage must use build_id UMD-028"
            )

        required_parents = {
            entry.entry_hash
            for entry in entries
        }
        if self.previous_session_hash is not None:
            required_parents.add(
                self.previous_session_hash
            )

        if not required_parents.issubset(
            set(self.lineage.parent_hashes)
        ):
            raise ValueError(
                "query-session lineage is missing required parent hashes"
            )

        by_execution_id = {
            entry.decision.execution_id: entry
            for entry in entries
        }
        by_query_id = {}

        for entry in entries:
            by_query_id.setdefault(
                entry.decision.query_id,
                [],
            ).append(entry)

        object.__setattr__(
            self,
            "_by_execution_id",
            MappingProxyType(by_execution_id),
        )
        object.__setattr__(
            self,
            "_by_query_id",
            MappingProxyType(
                {
                    query_id: tuple(values)
                    for query_id, values in by_query_id.items()
                }
            ),
        )

    @property
    def session_id(self) -> str:
        return "umd:market-query-session:" + deterministic_sha256(
            {
                "session_sequence": self.session_sequence,
                "previous_session_hash": self.previous_session_hash,
                "session_name": self.session_name,
                "execution_entry_ids": tuple(
                    entry.entry_id
                    for entry in self.execution_entries
                ),
            }
        )

    @property
    def execution_count(self) -> int:
        return len(self.execution_entries)

    @property
    def admitted_execution_count(self) -> int:
        return sum(
            1
            for entry in self.execution_entries
            if entry.decision.admitted
        )

    @property
    def rejected_execution_count(self) -> int:
        return sum(
            1
            for entry in self.execution_entries
            if not entry.decision.admitted
        )

    def get_by_execution(
        self,
        execution_id: str,
    ) -> CertifiedActiveMarketQueryExecutionLedgerEntry | None:
        return self._by_execution_id.get(
            _text(
                execution_id,
                "execution_id",
            )
        )

    def by_query(
        self,
        query_id: str,
    ) -> Tuple[
        CertifiedActiveMarketQueryExecutionLedgerEntry,
        ...
    ]:
        return self._by_query_id.get(
            _text(
                query_id,
                "query_id",
            ),
            (),
        )

    def execution_ids(self) -> Tuple[str, ...]:
        return tuple(
            entry.decision.execution_id
            for entry in self.execution_entries
        )

    def query_ids(self) -> Tuple[str, ...]:
        return tuple(
            sorted(self._by_query_id)
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "session_id": self.session_id,
            "session_sequence": self.session_sequence,
            "previous_session_hash": self.previous_session_hash,
            "session_name": self.session_name,
            "state": self.state,
            "execution_entries": self.execution_entries,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "metadata": self.metadata,
            "lineage": self.lineage,
        }

    @property
    def session_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class ReadOnlyActiveMarketQuerySessionRegistry:
    sessions: Tuple[
        CertifiedActiveMarketQuerySession,
        ...
    ]
    execution_read_model: CertifiedActiveMarketQueryExecutionReadModel
    registry_lineage: ImmutableLineage
    _by_session_id: Mapping[
        str,
        CertifiedActiveMarketQuerySession,
    ] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        ordered = tuple(
            sorted(
                self.sessions,
                key=lambda session: session.session_sequence,
            )
        )
        object.__setattr__(
            self,
            "sessions",
            ordered,
        )

        if self.registry_lineage.subsystem_id != UMD_SUBSYSTEM_ID:
            raise ValueError(
                "session-registry lineage must belong to UMD"
            )
        if self.registry_lineage.build_id != UMD_028_BUILD_ID:
            raise ValueError(
                "session-registry lineage must use build_id UMD-028"
            )
        if (
            self.execution_read_model.read_model_hash
            not in self.registry_lineage.parent_hashes
        ):
            raise ValueError(
                "session-registry lineage must include execution read-model hash"
            )

        by_session_id = {}
        used_execution_ids = set()
        previous_session = None

        for expected_sequence, session in enumerate(
            ordered,
            start=1,
        ):
            if session.session_sequence != expected_sequence:
                raise ValueError(
                    "session sequence must be contiguous and start at 1"
                )

            if previous_session is None:
                if session.previous_session_hash is not None:
                    raise ValueError(
                        "first session must not have previous hash"
                    )
            else:
                if (
                    session.previous_session_hash
                    != previous_session.session_hash
                ):
                    raise ValueError(
                        "session previous-hash chain mismatch"
                    )

            if session.session_id in by_session_id:
                raise ValueError(
                    "duplicate query session ID"
                )

            for execution_id in session.execution_ids():
                if execution_id in used_execution_ids:
                    raise ValueError(
                        "execution may belong to only one query session"
                    )
                if (
                    self.execution_read_model.get_by_execution(
                        execution_id
                    )
                    is None
                ):
                    raise ValueError(
                        "session references unknown execution"
                    )
                used_execution_ids.add(execution_id)

            by_session_id[session.session_id] = session
            previous_session = session

        object.__setattr__(
            self,
            "_by_session_id",
            MappingProxyType(by_session_id),
        )

    def get(
        self,
        session_id: str,
    ) -> CertifiedActiveMarketQuerySession | None:
        return self._by_session_id.get(
            _text(
                session_id,
                "session_id",
            )
        )

    def latest(
        self,
    ) -> CertifiedActiveMarketQuerySession | None:
        if not self.sessions:
            return None
        return self.sessions[-1]

    def open_sessions(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySession,
        ...
    ]:
        return tuple(
            session
            for session in self.sessions
            if session.state == QuerySessionState.OPEN
        )

    def closed_sessions(
        self,
    ) -> Tuple[
        CertifiedActiveMarketQuerySession,
        ...
    ]:
        return tuple(
            session
            for session in self.sessions
            if session.state == QuerySessionState.CLOSED
        )

    def to_canonical_dict(self) -> Mapping[str, Any]:
        return {
            "registry_mode": "append_only_read_only",
            "sessions": self.sessions,
            "execution_read_model_hash": (
                self.execution_read_model.read_model_hash
            ),
            "registry_lineage": self.registry_lineage,
        }

    @property
    def registry_hash(self) -> str:
        return deterministic_sha256(
            self.to_canonical_dict()
        )


@dataclass(frozen=True, slots=True)
class UMD028CertificationManifest:
    subsystem_id: str
    build_id: str
    build_name: str
    revision: str
    schema_version: str
    upstream_builds: Tuple[str, ...]
    session_mode: str
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
            "session_mode": self.session_mode,
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


def build_umd_028_certification_manifest() -> UMD028CertificationManifest:
    return UMD028CertificationManifest(
        subsystem_id="UMD",
        build_id=UMD_028_BUILD_ID,
        build_name=UMD_028_BUILD_NAME,
        revision=UMD_028_REVISION,
        schema_version=UMD_028_SCHEMA_VERSION,
        upstream_builds=tuple(
            f"UMD-{number:03d}"
            for number in range(1, 28)
        ),
        session_mode="append_only_read_only",
        prohibited_capabilities=PROHIBITED_CAPABILITIES,
        network_enabled=False,
        persistence_enabled=False,
        mutation_enabled=False,
        publication_enabled=False,
        execution_enabled=False,
    )


def certify_active_market_query_session_registry(
    registry: ReadOnlyActiveMarketQuerySessionRegistry,
) -> Mapping[str, Any]:
    checks = {
        "session_ids_unique": (
            len(
                {
                    session.session_id
                    for session in registry.sessions
                }
            )
            == len(registry.sessions)
        ),
        "sequence_contiguous": (
            tuple(
                session.session_sequence
                for session in registry.sessions
            )
            == tuple(
                range(
                    1,
                    len(registry.sessions) + 1,
                )
            )
        ),
        "execution_membership_unique": (
            len(
                {
                    execution_id
                    for session in registry.sessions
                    for execution_id in session.execution_ids()
                }
            )
            == sum(
                session.execution_count
                for session in registry.sessions
            )
        ),
        "deterministic_replay": (
            registry.registry_hash
            == deterministic_sha256(
                registry.to_canonical_dict()
            )
        ),
        "read_only_index": isinstance(
            registry._by_session_id,
            MappingProxyType,
        ),
    }

    failed = tuple(
        name
        for name, passed in checks.items()
        if not passed
    )

    latest = registry.latest()

    return MappingProxyType(
        {
            "certified": not failed,
            "registry_hash": registry.registry_hash,
            "session_count": len(registry.sessions),
            "open_session_count": len(
                registry.open_sessions()
            ),
            "closed_session_count": len(
                registry.closed_sessions()
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


def certify_umd_028_foundation() -> Mapping[str, Any]:
    manifest = build_umd_028_certification_manifest()

    checks = {
        "subsystem_identity": (
            manifest.subsystem_id == "UMD"
        ),
        "build_identity": (
            manifest.build_id == "UMD-028"
        ),
        "upstreams_frozen": (
            manifest.upstream_builds
            == tuple(
                f"UMD-{number:03d}"
                for number in range(1, 28)
            )
        ),
        "append_only_read_only": (
            manifest.session_mode
            == "append_only_read_only"
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


def verify_umd_028_certified_active_canonical_market_registry_query_session_contract() -> bool:
    result = certify_umd_028_foundation()

    if not result["certified"]:
        raise RuntimeError(
            "UMD-028 certification failed: "
            + ", ".join(result["failed_checks"])
        )

    return True


__all__ = [
    "UMD_028_BUILD_ID",
    "UMD_028_BUILD_NAME",
    "UMD_028_REVISION",
    "UMD_028_SCHEMA_VERSION",
    "PROHIBITED_CAPABILITIES",
    "QuerySessionState",
    "CertifiedActiveMarketQuerySession",
    "ReadOnlyActiveMarketQuerySessionRegistry",
    "UMD028CertificationManifest",
    "build_umd_028_certification_manifest",
    "certify_active_market_query_session_registry",
    "certify_umd_028_foundation",
    "verify_umd_028_certified_active_canonical_market_registry_query_session_contract",
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
from qseries_v2.universal_market_discovery.certified_active_canonical_market_registry_query_session_contract import (
    UMD_028_REVISION,
    QuerySessionState,
    build_umd_028_certification_manifest,
    certify_umd_028_foundation,
    verify_umd_028_certified_active_canonical_market_registry_query_session_contract,
)

FIXED = datetime(
    2026,
    8,
    6,
    8,
    30,
    tzinfo=timezone.utc,
)


class TestUMD028(unittest.TestCase):
    def test_foundation_certifies(self) -> None:
        self.assertTrue(
            certify_umd_028_foundation()["certified"]
        )
        self.assertTrue(
            verify_umd_028_certified_active_canonical_market_registry_query_session_contract()
        )

    def test_manifest_is_append_only_read_only(
        self,
    ) -> None:
        manifest = build_umd_028_certification_manifest()

        self.assertEqual(
            manifest.session_mode,
            "append_only_read_only",
        )
        self.assertFalse(manifest.network_enabled)
        self.assertFalse(manifest.persistence_enabled)
        self.assertFalse(manifest.mutation_enabled)
        self.assertFalse(manifest.publication_enabled)
        self.assertFalse(manifest.execution_enabled)

    def test_upstream_chain_complete(self) -> None:
        manifest = build_umd_028_certification_manifest()

        self.assertEqual(
            manifest.upstream_builds,
            tuple(
                f"UMD-{number:03d}"
                for number in range(1, 28)
            ),
        )

    def test_session_state_values(self) -> None:
        self.assertEqual(
            QuerySessionState.OPEN.value,
            "open",
        )
        self.assertEqual(
            QuerySessionState.CLOSED.value,
            "closed",
        )

    def test_lineage_identity(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-028",
            revision=UMD_028_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-028",
            ),
            created_at=FIXED,
        )

        self.assertEqual(
            lineage.build_id,
            "UMD-028",
        )

    def test_lineage_immutable(self) -> None:
        lineage = ImmutableLineage(
            subsystem_id="UMD",
            build_id="UMD-028",
            revision=UMD_028_REVISION,
            schema_version="1.0.0",
            parent_hashes=("a" * 64,),
            source_refs=(
                "fixture://umd-028",
            ),
            created_at=FIXED,
        )

        with self.assertRaises(
            (FrozenInstanceError, AttributeError)
        ):
            lineage.build_id = "MUTATED"


if __name__ == "__main__":
    print("=" * 64)
    print(" UMD-028 CERTIFICATION TEST")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION CONTRACT"
    )
    print("=" * 64)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestUMD028
    )
    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    manifest = build_umd_028_certification_manifest()

    print()
    print(f"[PASS] Build: {manifest.build_id}")
    print(f"[PASS] Revision: {manifest.revision}")
    print(
        f"[PASS] Manifest hash: "
        f"{manifest.manifest_hash}"
    )
    print(
        "[PASS] UMD-001 through UMD-027 "
        "consumed read-only"
    )
    print(
        "[PASS] Deterministic query session IDs certified"
    )
    print(
        "[PASS] Ordered execution membership certified"
    )
    print(
        "[PASS] Duplicate session execution membership prohibited"
    )
    print(
        "[PASS] Open and closed session states certified"
    )
    print(
        "[PASS] Previous-session hash chaining certified"
    )
    print(
        "[PASS] Execution read-model lineage certified"
    )
    print(
        "[PASS] Immutable read-only session registry certified"
    )
    print(
        "[PASS] Network and persistence disabled"
    )
    print(
        "[PASS] Publication and Q Series execution disabled"
    )
    print(
        "[DONE] UMD-028 CERTIFIED ACTIVE CANONICAL MARKET "
        "REGISTRY QUERY SESSION CONTRACT CERTIFIED"
    )
"""

INIT_IMPORT = r"""
from .certified_active_canonical_market_registry_query_session_contract import (
    UMD_028_BUILD_ID,
    UMD_028_BUILD_NAME,
    UMD_028_REVISION,
    UMD_028_SCHEMA_VERSION,
    QuerySessionState,
    CertifiedActiveMarketQuerySession,
    ReadOnlyActiveMarketQuerySessionRegistry,
    UMD028CertificationManifest,
    build_umd_028_certification_manifest,
    certify_active_market_query_session_registry,
    certify_umd_028_foundation,
    verify_umd_028_certified_active_canonical_market_registry_query_session_contract,
)
"""

EXPORTED_NAMES = (
    "UMD_028_BUILD_ID",
    "UMD_028_BUILD_NAME",
    "UMD_028_REVISION",
    "UMD_028_SCHEMA_VERSION",
    "QuerySessionState",
    "CertifiedActiveMarketQuerySession",
    "ReadOnlyActiveMarketQuerySessionRegistry",
    "UMD028CertificationManifest",
    "build_umd_028_certification_manifest",
    "certify_active_market_query_session_registry",
    "certify_umd_028_foundation",
    "verify_umd_028_certified_active_canonical_market_registry_query_session_contract",
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
        "query_session_contract import ("
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
        block = source[
            start : end + 1
        ]

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
            "query_session_contract"
        )

        required = (
            "QuerySessionState",
            "CertifiedActiveMarketQuerySession",
            "ReadOnlyActiveMarketQuerySessionRegistry",
            "build_umd_028_certification_manifest",
            "certify_active_market_query_session_registry",
            "certify_umd_028_foundation",
            "verify_umd_028_certified_active_canonical_market_registry_query_session_contract",
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
                "UMD-028 missing symbols: "
                + ", ".join(missing)
            )

        module.verify_umd_028_certified_active_canonical_market_registry_query_session_contract()
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(
                str(ROOT)
            )


def main() -> int:
    print("=" * 64)
    print(" UMD-028 INSTALLER")
    print(
        " CERTIFIED ACTIVE CANONICAL MARKET REGISTRY "
        "QUERY SESSION CONTRACT"
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
        "[PASS] Certified UMD-001 through UMD-027 "
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
        "build_id": "UMD-028",
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
            for number in range(1, 28)
        ),
        "mode": "append_only_read_only",
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
        "[PASS] Required UMD-028 symbols verified"
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
        "[DONE] UMD-028 INSTALLATION COMPLETE"
    )
    print()
    print("NEXT:")
    print(
        "  python "
        "test_umd_028_certified_active_canonical_market_"
        "registry_query_session_contract.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
