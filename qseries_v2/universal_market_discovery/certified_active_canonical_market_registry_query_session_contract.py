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
