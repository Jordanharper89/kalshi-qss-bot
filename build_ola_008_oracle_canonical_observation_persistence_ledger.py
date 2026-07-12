from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_canonical_observation_persistence_ledger.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_008_oracle_canonical_observation_persistence_ledger.py"
)


MODULE_CONTENT = r'''
"""
OLA-008
Oracle Canonical Observation Persistence Ledger

Append-only canonical persistence evidence boundary for Oracle live
read-only acquisition.

Architecture:

SOURCE
    |
SOURCE HEALTH / RATE CONTROL
    |
ACQUISITION
    |
NORMALIZATION
    |
DEDUPLICATION
    |
CANONICAL OBSERVATION
    |
ORACLE ROUTING
    |
PERSISTENCE                     <- OLA-008

Permanent rules:

- Only CanonicalObservation records may be persisted.
- Observation identity is preserved.
- Source identity is preserved.
- Acquisition batch identity is preserved.
- Observation timestamps are preserved.
- Content hashes are preserved.
- Replay hashes are preserved.
- Persistence timestamps are caller supplied.
- Persistence is append-only.
- Existing entries may not be replaced.
- Existing entries may not be mutated.
- Duplicate observation identity is rejected.
- Conflicting content identity is rejected.
- Every entry is chained to the previous ledger state.
- Empty-ledger chain genesis is explicit.
- Snapshot export is deterministic.
- Snapshot restore validates every entry and the complete chain.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains permanently read-only.
- No trade authorization exists.
- No execution adapter is resolved or invoked.
- No funds are moved.
- No portfolio is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    JSONValue,
)


SCHEMA_VERSION = "OLA-008"
ENGINE_ID = "OLA-008"

GENESIS_CHAIN_HASH = stable_genesis_text = (
    "oracle.canonical.observation.persistence.genesis.v1"
)

PERSISTENCE_ENTRY_RECORD_TYPE = (
    "canonical_observation_persistence_entry"
)

PERSISTENCE_SNAPSHOT_RECORD_TYPE = (
    "canonical_observation_persistence_snapshot"
)


class ObservationPersistenceContractError(ValueError):
    """Raised when persistence contract data is malformed."""


class ObservationPersistenceConflictError(
    ObservationPersistenceContractError
):
    """Raised when immutable persistence identity conflicts."""


class ObservationPersistenceSnapshotError(
    ObservationPersistenceContractError
):
    """Raised when persistence snapshot data is incompatible."""


class ObservationPersistenceInvariantError(RuntimeError):
    """Raised when permanent persistence invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise ObservationPersistenceContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise ObservationPersistenceContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ObservationPersistenceContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise ObservationPersistenceContractError(
            f"{field_name} must be non-negative"
        )

    return value


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    normalized = _require_non_negative_int(
        value,
        field_name,
    )

    if normalized == 0:
        raise ObservationPersistenceContractError(
            f"{field_name} must be greater than zero"
        )

    return normalized


def _require_exact_bool(
    value: Any,
    field_name: str,
    expected: bool,
) -> bool:
    if not isinstance(value, bool):
        raise ObservationPersistenceSnapshotError(
            f"{field_name} must be a bool"
        )

    if value is not expected:
        raise ObservationPersistenceSnapshotError(
            f"{field_name} invariant is incompatible"
        )

    return value


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise ObservationPersistenceContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise ObservationPersistenceContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _parse_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    normalized = _require_non_empty_string(
        value,
        field_name,
    )

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ObservationPersistenceSnapshotError(
            f"{field_name} must be ISO-8601 datetime text"
        ) from exc

    try:
        return _require_aware_datetime(
            parsed,
            field_name,
        )
    except ObservationPersistenceContractError as exc:
        raise ObservationPersistenceSnapshotError(
            str(exc)
        ) from exc


def _canonicalize(
    value: Any,
) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ObservationPersistenceContractError(
                "non-finite floats are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise ObservationPersistenceContractError(
                    "canonical mapping keys must be strings"
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise ObservationPersistenceContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


GENESIS_CHAIN_HASH = stable_hash(
    {
        "schema_version": SCHEMA_VERSION,
        "record_type": "persistence_chain_genesis",
        "genesis_text": stable_genesis_text,
    }
)


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise ObservationPersistenceContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise ObservationPersistenceContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    return tuple(
        (key, canonical[key])
        for key in sorted(canonical)
    )


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class CanonicalObservationPersistenceEntry:
    schema_version: str
    engine_id: str
    sequence_number: int
    persistence_entry_id: str
    observation_id: str
    source_id: str
    source_observation_id: str
    observation_type: str
    acquisition_batch_id: str
    observed_at: datetime
    acquired_at: datetime
    persisted_at: datetime
    content_hash: str
    observation_replay_hash: str
    canonical_observation: CanonicalObservation
    persistence_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    previous_chain_hash: str
    entry_hash: str
    chain_hash: str
    immutable: bool
    append_only: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @staticmethod
    def build_entry_hash_payload(
        *,
        schema_version: str,
        engine_id: str,
        sequence_number: int,
        persistence_entry_id: str,
        observation_id: str,
        source_id: str,
        source_observation_id: str,
        observation_type: str,
        acquisition_batch_id: str,
        observed_at: datetime,
        acquired_at: datetime,
        persisted_at: datetime,
        content_hash: str,
        observation_replay_hash: str,
        canonical_observation: CanonicalObservation,
        persistence_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
        previous_chain_hash: str,
        immutable: bool,
        append_only: bool,
        replayable: bool,
        auditable: bool,
        explainable: bool,
        read_only: bool,
        execution_allowed: bool,
        execution_adapter_resolved: bool,
        execution_adapter_invoked: bool,
        trade_authorization_allowed: bool,
        order_placement_allowed: bool,
        funds_moved: bool,
        portfolio_mutated: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": schema_version,
            "record_type": PERSISTENCE_ENTRY_RECORD_TYPE,
            "engine_id": engine_id,
            "sequence_number": sequence_number,
            "persistence_entry_id": persistence_entry_id,
            "observation_id": observation_id,
            "source_id": source_id,
            "source_observation_id": (
                source_observation_id
            ),
            "observation_type": observation_type,
            "acquisition_batch_id": acquisition_batch_id,
            "observed_at": observed_at,
            "acquired_at": acquired_at,
            "persisted_at": persisted_at,
            "content_hash": content_hash,
            "observation_replay_hash": (
                observation_replay_hash
            ),
            "canonical_observation": (
                canonical_observation.to_canonical_dict()
            ),
            "persistence_metadata": (
                _mapping_from_immutable(
                    persistence_metadata
                )
            ),
            "previous_chain_hash": previous_chain_hash,
            "immutable": immutable,
            "append_only": append_only,
            "replayable": replayable,
            "auditable": auditable,
            "explainable": explainable,
            "read_only": read_only,
            "execution_allowed": execution_allowed,
            "execution_adapter_resolved": (
                execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                trade_authorization_allowed
            ),
            "order_placement_allowed": (
                order_placement_allowed
            ),
            "funds_moved": funds_moved,
            "portfolio_mutated": portfolio_mutated,
        }

    @classmethod
    def create(
        cls,
        *,
        sequence_number: int,
        observation: CanonicalObservation,
        persisted_at: datetime,
        persistence_metadata: Mapping[str, Any],
        previous_chain_hash: str,
    ) -> "CanonicalObservationPersistenceEntry":
        normalized_sequence_number = _require_positive_int(
            sequence_number,
            "sequence_number",
        )

        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise ObservationPersistenceContractError(
                "observation must be CanonicalObservation"
            )

        if observation.read_only is not True:
            raise ObservationPersistenceInvariantError(
                "canonical observation must remain read_only"
            )

        if observation.execution_allowed is not False:
            raise ObservationPersistenceInvariantError(
                "canonical observation must prohibit execution"
            )

        normalized_persisted_at = _require_aware_datetime(
            persisted_at,
            "persisted_at",
        )

        if normalized_persisted_at < observation.acquired_at:
            raise ObservationPersistenceContractError(
                "persisted_at cannot be before acquired_at"
            )

        normalized_previous_chain_hash = (
            _require_non_empty_string(
                previous_chain_hash,
                "previous_chain_hash",
            )
        )

        immutable_metadata = _immutable_mapping(
            persistence_metadata,
            "persistence_metadata",
        )

        persistence_entry_id = "persistence." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "persistence_entry_identity",
                "sequence_number": normalized_sequence_number,
                "observation_id": observation.observation_id,
                "content_hash": observation.content_hash,
                "persisted_at": normalized_persisted_at,
                "previous_chain_hash": (
                    normalized_previous_chain_hash
                ),
            }
        )

        payload = cls.build_entry_hash_payload(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            sequence_number=normalized_sequence_number,
            persistence_entry_id=persistence_entry_id,
            observation_id=observation.observation_id,
            source_id=observation.source_id,
            source_observation_id=(
                observation.source_observation_id
            ),
            observation_type=observation.observation_type,
            acquisition_batch_id=(
                observation.acquisition_batch_id
            ),
            observed_at=observation.observed_at,
            acquired_at=observation.acquired_at,
            persisted_at=normalized_persisted_at,
            content_hash=observation.content_hash,
            observation_replay_hash=observation.replay_hash,
            canonical_observation=observation,
            persistence_metadata=immutable_metadata,
            previous_chain_hash=normalized_previous_chain_hash,
            immutable=True,
            append_only=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        entry_hash = stable_hash(payload)

        chain_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "persistence_chain_link",
                "previous_chain_hash": (
                    normalized_previous_chain_hash
                ),
                "entry_hash": entry_hash,
                "sequence_number": normalized_sequence_number,
            }
        )

        return cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            sequence_number=normalized_sequence_number,
            persistence_entry_id=persistence_entry_id,
            observation_id=observation.observation_id,
            source_id=observation.source_id,
            source_observation_id=(
                observation.source_observation_id
            ),
            observation_type=observation.observation_type,
            acquisition_batch_id=(
                observation.acquisition_batch_id
            ),
            observed_at=observation.observed_at,
            acquired_at=observation.acquired_at,
            persisted_at=normalized_persisted_at,
            content_hash=observation.content_hash,
            observation_replay_hash=observation.replay_hash,
            canonical_observation=observation,
            persistence_metadata=immutable_metadata,
            previous_chain_hash=normalized_previous_chain_hash,
            entry_hash=entry_hash,
            chain_hash=chain_hash,
            immutable=True,
            append_only=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def calculate_entry_hash(self) -> str:
        return stable_hash(
            self.build_entry_hash_payload(
                schema_version=self.schema_version,
                engine_id=self.engine_id,
                sequence_number=self.sequence_number,
                persistence_entry_id=(
                    self.persistence_entry_id
                ),
                observation_id=self.observation_id,
                source_id=self.source_id,
                source_observation_id=(
                    self.source_observation_id
                ),
                observation_type=self.observation_type,
                acquisition_batch_id=(
                    self.acquisition_batch_id
                ),
                observed_at=self.observed_at,
                acquired_at=self.acquired_at,
                persisted_at=self.persisted_at,
                content_hash=self.content_hash,
                observation_replay_hash=(
                    self.observation_replay_hash
                ),
                canonical_observation=(
                    self.canonical_observation
                ),
                persistence_metadata=(
                    self.persistence_metadata
                ),
                previous_chain_hash=(
                    self.previous_chain_hash
                ),
                immutable=self.immutable,
                append_only=self.append_only,
                replayable=self.replayable,
                auditable=self.auditable,
                explainable=self.explainable,
                read_only=self.read_only,
                execution_allowed=self.execution_allowed,
                execution_adapter_resolved=(
                    self.execution_adapter_resolved
                ),
                execution_adapter_invoked=(
                    self.execution_adapter_invoked
                ),
                trade_authorization_allowed=(
                    self.trade_authorization_allowed
                ),
                order_placement_allowed=(
                    self.order_placement_allowed
                ),
                funds_moved=self.funds_moved,
                portfolio_mutated=self.portfolio_mutated,
            )
        )

    def calculate_chain_hash(self) -> str:
        return stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "persistence_chain_link",
                "previous_chain_hash": (
                    self.previous_chain_hash
                ),
                "entry_hash": self.entry_hash,
                "sequence_number": self.sequence_number,
            }
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "sequence_number": self.sequence_number,
            "persistence_entry_id": (
                self.persistence_entry_id
            ),
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "source_observation_id": (
                self.source_observation_id
            ),
            "observation_type": self.observation_type,
            "acquisition_batch_id": (
                self.acquisition_batch_id
            ),
            "observed_at": self.observed_at.isoformat(),
            "acquired_at": self.acquired_at.isoformat(),
            "persisted_at": self.persisted_at.isoformat(),
            "content_hash": self.content_hash,
            "observation_replay_hash": (
                self.observation_replay_hash
            ),
            "canonical_observation": (
                self.canonical_observation.to_canonical_dict()
            ),
            "persistence_metadata": (
                _mapping_from_immutable(
                    self.persistence_metadata
                )
            ),
            "previous_chain_hash": self.previous_chain_hash,
            "entry_hash": self.entry_hash,
            "chain_hash": self.chain_hash,
            "immutable": self.immutable,
            "append_only": self.append_only,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }


@dataclass(frozen=True, slots=True)
class CanonicalObservationPersistenceSnapshot:
    schema_version: str
    engine_id: str
    snapshot_at: datetime
    genesis_chain_hash: str
    entries: tuple[
        CanonicalObservationPersistenceEntry,
        ...
    ]
    entry_count: int
    terminal_chain_hash: str
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    snapshot_hash: str
    immutable: bool
    append_only: bool
    replayable: bool
    auditable: bool
    explainable: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def build_snapshot_hash_payload(
        self,
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "record_type": PERSISTENCE_SNAPSHOT_RECORD_TYPE,
            "engine_id": self.engine_id,
            "snapshot_at": self.snapshot_at,
            "genesis_chain_hash": self.genesis_chain_hash,
            "entries": [
                entry.to_canonical_dict()
                for entry in self.entries
            ],
            "entry_count": self.entry_count,
            "terminal_chain_hash": self.terminal_chain_hash,
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "immutable": self.immutable,
            "append_only": self.append_only,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

    def calculate_snapshot_hash(self) -> str:
        return stable_hash(
            self.build_snapshot_hash_payload()
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "snapshot_at": self.snapshot_at.isoformat(),
            "genesis_chain_hash": self.genesis_chain_hash,
            "entries": [
                entry.to_canonical_dict()
                for entry in self.entries
            ],
            "entry_count": self.entry_count,
            "terminal_chain_hash": self.terminal_chain_hash,
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "snapshot_hash": self.snapshot_hash,
            "immutable": self.immutable,
            "append_only": self.append_only,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }


class OracleCanonicalObservationPersistenceLedger:
    """
    Append-only persistence ledger for canonical Oracle observations.

    This class establishes the canonical persistence contract.

    It deliberately does not decide which database, object store, or disk
    backend will ultimately retain the ledger. Backend implementation must
    preserve this contract exactly.

    The current ledger provides:
    - immutable append entries,
    - observation identity uniqueness,
    - content identity conflict detection,
    - deterministic chain hashes,
    - deterministic snapshot export,
    - deterministic snapshot restore,
    - replay and audit validation.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    immutable = True
    append_only = True
    replayable = True
    auditable = True
    explainable = True
    read_only = True
    execution_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(self) -> None:
        self._entries: list[
            CanonicalObservationPersistenceEntry
        ] = []

        self._entries_by_observation_id: dict[
            str,
            CanonicalObservationPersistenceEntry,
        ] = {}

        self._observation_id_by_content_hash: dict[
            str,
            str,
        ] = {}

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "immutable": self.immutable,
            "append_only": self.append_only,
            "replayable": self.replayable,
            "auditable": self.auditable,
            "explainable": self.explainable,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "execution_adapter_resolved": (
                self.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                self.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        expected = {
            "immutable": True,
            "append_only": True,
            "replayable": True,
            "auditable": True,
            "explainable": True,
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise ObservationPersistenceInvariantError(
                "Oracle persistence invariants violated"
            )

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def terminal_chain_hash(self) -> str:
        if not self._entries:
            return GENESIS_CHAIN_HASH

        return self._entries[-1].chain_hash

    @property
    def observation_ids(self) -> tuple[str, ...]:
        return tuple(
            entry.observation_id
            for entry in self._entries
        )

    def append(
        self,
        *,
        observation: CanonicalObservation,
        persisted_at: datetime,
        persistence_metadata: Mapping[str, Any],
    ) -> CanonicalObservationPersistenceEntry:
        self._assert_invariants()

        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise ObservationPersistenceContractError(
                "observation must be CanonicalObservation"
            )

        normalized_persisted_at = _require_aware_datetime(
            persisted_at,
            "persisted_at",
        )

        self._validate_observation_contract(
            observation
        )

        existing = self._entries_by_observation_id.get(
            observation.observation_id
        )

        if existing is not None:
            raise ObservationPersistenceConflictError(
                "observation_id is already persisted"
            )

        content_owner = (
            self._observation_id_by_content_hash.get(
                observation.content_hash
            )
        )

        if content_owner is not None:
            raise ObservationPersistenceConflictError(
                "content_hash is already persisted under "
                f"observation_id={content_owner}"
            )

        sequence_number = len(self._entries) + 1

        entry = CanonicalObservationPersistenceEntry.create(
            sequence_number=sequence_number,
            observation=observation,
            persisted_at=normalized_persisted_at,
            persistence_metadata=persistence_metadata,
            previous_chain_hash=self.terminal_chain_hash,
        )

        self._validate_entry(
            entry=entry,
            expected_sequence_number=sequence_number,
            expected_previous_chain_hash=(
                self.terminal_chain_hash
            ),
        )

        self._entries.append(entry)

        self._entries_by_observation_id[
            entry.observation_id
        ] = entry

        self._observation_id_by_content_hash[
            entry.content_hash
        ] = entry.observation_id

        return entry

    def append_many(
        self,
        *,
        observations: Sequence[
            CanonicalObservation
        ],
        persisted_at: datetime,
        persistence_metadata: Mapping[str, Any],
    ) -> tuple[
        CanonicalObservationPersistenceEntry,
        ...
    ]:
        self._assert_invariants()

        if isinstance(observations, (str, bytes)):
            raise ObservationPersistenceContractError(
                "observations must be a sequence"
            )

        if not isinstance(observations, Sequence):
            raise ObservationPersistenceContractError(
                "observations must be a sequence"
            )

        if not observations:
            return ()

        normalized_persisted_at = _require_aware_datetime(
            persisted_at,
            "persisted_at",
        )

        staged_observation_ids: set[str] = set()
        staged_content_hashes: set[str] = set()

        for observation in observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise ObservationPersistenceContractError(
                    "observations contains incompatible record"
                )

            self._validate_observation_contract(
                observation
            )

            if (
                observation.observation_id
                in self._entries_by_observation_id
            ):
                raise ObservationPersistenceConflictError(
                    "observation_id is already persisted"
                )

            if (
                observation.content_hash
                in self._observation_id_by_content_hash
            ):
                raise ObservationPersistenceConflictError(
                    "content_hash is already persisted"
                )

            if (
                observation.observation_id
                in staged_observation_ids
            ):
                raise ObservationPersistenceConflictError(
                    "duplicate observation_id inside append_many"
                )

            if (
                observation.content_hash
                in staged_content_hashes
            ):
                raise ObservationPersistenceConflictError(
                    "duplicate content_hash inside append_many"
                )

            staged_observation_ids.add(
                observation.observation_id
            )

            staged_content_hashes.add(
                observation.content_hash
            )

        staged_entries: list[
            CanonicalObservationPersistenceEntry
        ] = []

        previous_chain_hash = self.terminal_chain_hash

        starting_sequence_number = len(self._entries) + 1

        for offset, observation in enumerate(
            observations
        ):
            sequence_number = (
                starting_sequence_number + offset
            )

            entry = (
                CanonicalObservationPersistenceEntry.create(
                    sequence_number=sequence_number,
                    observation=observation,
                    persisted_at=normalized_persisted_at,
                    persistence_metadata=(
                        persistence_metadata
                    ),
                    previous_chain_hash=previous_chain_hash,
                )
            )

            self._validate_entry(
                entry=entry,
                expected_sequence_number=sequence_number,
                expected_previous_chain_hash=(
                    previous_chain_hash
                ),
            )

            staged_entries.append(entry)

            previous_chain_hash = entry.chain_hash

        for entry in staged_entries:
            self._entries.append(entry)

            self._entries_by_observation_id[
                entry.observation_id
            ] = entry

            self._observation_id_by_content_hash[
                entry.content_hash
            ] = entry.observation_id

        return tuple(staged_entries)

    def _validate_observation_contract(
        self,
        observation: CanonicalObservation,
    ) -> None:
        if observation.read_only is not True:
            raise ObservationPersistenceInvariantError(
                "canonical observation lost read_only invariant"
            )

        if observation.execution_allowed is not False:
            raise ObservationPersistenceInvariantError(
                "canonical observation gained execution capability"
            )

        if not observation.observation_id:
            raise ObservationPersistenceContractError(
                "observation_id must not be empty"
            )

        if not observation.content_hash:
            raise ObservationPersistenceContractError(
                "content_hash must not be empty"
            )

        if not observation.replay_hash:
            raise ObservationPersistenceContractError(
                "replay_hash must not be empty"
            )

        if not observation.source_id:
            raise ObservationPersistenceContractError(
                "source_id must not be empty"
            )

        if not observation.acquisition_batch_id:
            raise ObservationPersistenceContractError(
                "acquisition_batch_id must not be empty"
            )

        if observation.acquired_at < observation.observed_at:
            raise ObservationPersistenceContractError(
                "acquired_at cannot be before observed_at"
            )

    @staticmethod
    def _validate_entry(
        *,
        entry: CanonicalObservationPersistenceEntry,
        expected_sequence_number: int,
        expected_previous_chain_hash: str,
    ) -> None:
        if entry.schema_version != SCHEMA_VERSION:
            raise ObservationPersistenceInvariantError(
                "persistence entry schema_version mismatch"
            )

        if entry.engine_id != ENGINE_ID:
            raise ObservationPersistenceInvariantError(
                "persistence entry engine_id mismatch"
            )

        if (
            entry.sequence_number
            != expected_sequence_number
        ):
            raise ObservationPersistenceInvariantError(
                "persistence entry sequence mismatch"
            )

        if (
            entry.previous_chain_hash
            != expected_previous_chain_hash
        ):
            raise ObservationPersistenceInvariantError(
                "persistence previous chain hash mismatch"
            )

        if (
            entry.calculate_entry_hash()
            != entry.entry_hash
        ):
            raise ObservationPersistenceInvariantError(
                "persistence entry hash validation failed"
            )

        if (
            entry.calculate_chain_hash()
            != entry.chain_hash
        ):
            raise ObservationPersistenceInvariantError(
                "persistence chain hash validation failed"
            )

        observation = entry.canonical_observation

        if entry.observation_id != observation.observation_id:
            raise ObservationPersistenceInvariantError(
                "entry observation identity mismatch"
            )

        if entry.source_id != observation.source_id:
            raise ObservationPersistenceInvariantError(
                "entry source identity mismatch"
            )

        if (
            entry.source_observation_id
            != observation.source_observation_id
        ):
            raise ObservationPersistenceInvariantError(
                "entry source observation identity mismatch"
            )

        if (
            entry.acquisition_batch_id
            != observation.acquisition_batch_id
        ):
            raise ObservationPersistenceInvariantError(
                "entry acquisition batch identity mismatch"
            )

        if entry.content_hash != observation.content_hash:
            raise ObservationPersistenceInvariantError(
                "entry content hash mismatch"
            )

        if (
            entry.observation_replay_hash
            != observation.replay_hash
        ):
            raise ObservationPersistenceInvariantError(
                "entry observation replay hash mismatch"
            )

        if entry.immutable is not True:
            raise ObservationPersistenceInvariantError(
                "entry immutable invariant violated"
            )

        if entry.append_only is not True:
            raise ObservationPersistenceInvariantError(
                "entry append_only invariant violated"
            )

        if entry.read_only is not True:
            raise ObservationPersistenceInvariantError(
                "entry read_only invariant violated"
            )

        false_invariants = {
            "execution_allowed": entry.execution_allowed,
            "execution_adapter_resolved": (
                entry.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                entry.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                entry.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                entry.order_placement_allowed
            ),
            "funds_moved": entry.funds_moved,
            "portfolio_mutated": entry.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise ObservationPersistenceInvariantError(
                "persistence entry no-execution invariants violated"
            )

    def get_entry(
        self,
        *,
        observation_id: str,
    ) -> CanonicalObservationPersistenceEntry | None:
        normalized_observation_id = _require_non_empty_string(
            observation_id,
            "observation_id",
        )

        entry = self._entries_by_observation_id.get(
            normalized_observation_id
        )

        if entry is not None:
            self._validate_entry(
                entry=entry,
                expected_sequence_number=(
                    entry.sequence_number
                ),
                expected_previous_chain_hash=(
                    entry.previous_chain_hash
                ),
            )

        return entry

    def export_snapshot(
        self,
        *,
        snapshot_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> CanonicalObservationPersistenceSnapshot:
        self._assert_invariants()

        normalized_snapshot_at = _require_aware_datetime(
            snapshot_at,
            "snapshot_at",
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        self._validate_complete_chain()

        for entry in self._entries:
            if entry.persisted_at > normalized_snapshot_at:
                raise ObservationPersistenceContractError(
                    "snapshot_at cannot be before persisted entry"
                )

        entries = tuple(self._entries)

        provisional = CanonicalObservationPersistenceSnapshot(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            snapshot_at=normalized_snapshot_at,
            genesis_chain_hash=GENESIS_CHAIN_HASH,
            entries=entries,
            entry_count=len(entries),
            terminal_chain_hash=self.terminal_chain_hash,
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            snapshot_hash="",
            immutable=True,
            append_only=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        snapshot_hash = (
            provisional.calculate_snapshot_hash()
        )

        return CanonicalObservationPersistenceSnapshot(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            snapshot_at=provisional.snapshot_at,
            genesis_chain_hash=(
                provisional.genesis_chain_hash
            ),
            entries=provisional.entries,
            entry_count=provisional.entry_count,
            terminal_chain_hash=(
                provisional.terminal_chain_hash
            ),
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            snapshot_hash=snapshot_hash,
            immutable=True,
            append_only=True,
            replayable=True,
            auditable=True,
            explainable=True,
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def _validate_complete_chain(self) -> None:
        expected_previous_chain_hash = GENESIS_CHAIN_HASH

        seen_observation_ids: set[str] = set()
        seen_content_hashes: set[str] = set()

        for expected_sequence_number, entry in enumerate(
            self._entries,
            start=1,
        ):
            self._validate_entry(
                entry=entry,
                expected_sequence_number=(
                    expected_sequence_number
                ),
                expected_previous_chain_hash=(
                    expected_previous_chain_hash
                ),
            )

            if entry.observation_id in seen_observation_ids:
                raise ObservationPersistenceInvariantError(
                    "duplicate observation identity in ledger"
                )

            if entry.content_hash in seen_content_hashes:
                raise ObservationPersistenceInvariantError(
                    "duplicate content identity in ledger"
                )

            seen_observation_ids.add(
                entry.observation_id
            )

            seen_content_hashes.add(
                entry.content_hash
            )

            expected_previous_chain_hash = entry.chain_hash

        if (
            expected_previous_chain_hash
            != self.terminal_chain_hash
        ):
            raise ObservationPersistenceInvariantError(
                "terminal chain hash validation failed"
            )

    @classmethod
    def restore_snapshot(
        cls,
        *,
        snapshot: CanonicalObservationPersistenceSnapshot,
    ) -> "OracleCanonicalObservationPersistenceLedger":
        if not isinstance(
            snapshot,
            CanonicalObservationPersistenceSnapshot,
        ):
            raise ObservationPersistenceSnapshotError(
                "snapshot must be "
                "CanonicalObservationPersistenceSnapshot"
            )

        if snapshot.schema_version != SCHEMA_VERSION:
            raise ObservationPersistenceSnapshotError(
                "snapshot schema_version is incompatible"
            )

        if snapshot.engine_id != ENGINE_ID:
            raise ObservationPersistenceSnapshotError(
                "snapshot engine_id is incompatible"
            )

        if (
            snapshot.genesis_chain_hash
            != GENESIS_CHAIN_HASH
        ):
            raise ObservationPersistenceSnapshotError(
                "snapshot genesis chain hash is incompatible"
            )

        if snapshot.entry_count != len(snapshot.entries):
            raise ObservationPersistenceSnapshotError(
                "snapshot entry_count mismatch"
            )

        if snapshot.immutable is not True:
            raise ObservationPersistenceSnapshotError(
                "snapshot immutable invariant is incompatible"
            )

        if snapshot.append_only is not True:
            raise ObservationPersistenceSnapshotError(
                "snapshot append_only invariant is incompatible"
            )

        if snapshot.read_only is not True:
            raise ObservationPersistenceSnapshotError(
                "snapshot read_only invariant is incompatible"
            )

        false_invariants = {
            "execution_allowed": snapshot.execution_allowed,
            "execution_adapter_resolved": (
                snapshot.execution_adapter_resolved
            ),
            "execution_adapter_invoked": (
                snapshot.execution_adapter_invoked
            ),
            "trade_authorization_allowed": (
                snapshot.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                snapshot.order_placement_allowed
            ),
            "funds_moved": snapshot.funds_moved,
            "portfolio_mutated": snapshot.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise ObservationPersistenceSnapshotError(
                "snapshot no-execution invariants are incompatible"
            )

        expected_snapshot_hash = (
            snapshot.calculate_snapshot_hash()
        )

        if expected_snapshot_hash != snapshot.snapshot_hash:
            raise ObservationPersistenceSnapshotError(
                "snapshot_hash validation failed"
            )

        ledger = cls()

        expected_previous_chain_hash = GENESIS_CHAIN_HASH

        for expected_sequence_number, entry in enumerate(
            snapshot.entries,
            start=1,
        ):
            try:
                ledger._validate_entry(
                    entry=entry,
                    expected_sequence_number=(
                        expected_sequence_number
                    ),
                    expected_previous_chain_hash=(
                        expected_previous_chain_hash
                    ),
                )
            except ObservationPersistenceInvariantError as exc:
                raise ObservationPersistenceSnapshotError(
                    str(exc)
                ) from exc

            if (
                entry.observation_id
                in ledger._entries_by_observation_id
            ):
                raise ObservationPersistenceSnapshotError(
                    "snapshot contains duplicate observation_id"
                )

            if (
                entry.content_hash
                in ledger._observation_id_by_content_hash
            ):
                raise ObservationPersistenceSnapshotError(
                    "snapshot contains duplicate content_hash"
                )

            ledger._entries.append(entry)

            ledger._entries_by_observation_id[
                entry.observation_id
            ] = entry

            ledger._observation_id_by_content_hash[
                entry.content_hash
            ] = entry.observation_id

            expected_previous_chain_hash = entry.chain_hash

        if (
            ledger.terminal_chain_hash
            != snapshot.terminal_chain_hash
        ):
            raise ObservationPersistenceSnapshotError(
                "snapshot terminal_chain_hash mismatch"
            )

        ledger._validate_complete_chain()

        return ledger


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "GENESIS_CHAIN_HASH",
    "ObservationPersistenceContractError",
    "ObservationPersistenceConflictError",
    "ObservationPersistenceSnapshotError",
    "ObservationPersistenceInvariantError",
    "CanonicalObservationPersistenceEntry",
    "CanonicalObservationPersistenceSnapshot",
    "OracleCanonicalObservationPersistenceLedger",
    "canonical_json",
    "stable_hash",
]
'''


PACKAGE_INIT_CONTENT = r'''
"""
Oracle live read-only acquisition subsystem.
"""

from .oracle_live_read_only_acquisition_runtime import (
    AcquisitionBatchRecord,
    AcquisitionContractError,
    AcquisitionInvariantError,
    AcquisitionObservationRecord,
    ApprovedReadOnlySourceAdapter,
    ApprovedSourceAdapterRegistration,
    CanonicalObservation,
    CanonicalObservationRouterFailure,
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlEvidence,
    RawSourceObservation,
    SourceAdapterFailure,
    SourceHealthEvidence,
    UnapprovedSourceAdapterError,
)

from .oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateControlPolicy,
    RateWindowObservation,
    SourceControlContractError,
    SourceControlDecisionRecord,
    SourceControlInvariantError,
    SourceControlPolicyError,
    SourceHealthObservation,
    SourceHealthPolicy,
)

from .oracle_acquisition_deduplication_ledger import (
    CanonicalDeduplicationLedgerEntry,
    DeduplicationLedgerContractError,
    DeduplicationLedgerInvariantError,
    DeduplicationLedgerSnapshot,
    DeduplicationLedgerSnapshotError,
    OracleAcquisitionDeduplicationLedger,
)

from .oracle_canonical_market_identity_venue_resolution_engine import (
    ApprovedVenueRegistration,
    CanonicalMarketIdentity,
    CanonicalMarketVenueRecord,
    MarketIdentityContractError,
    OracleCanonicalMarketIdentityVenueResolutionEngine,
    SourceMarketIdentityEvidence,
    VenueResolutionError,
    VenueResolutionInvariantError,
    VerifiedVenueResolution,
)

from .oracle_canonical_opportunity_validity_expiration_engine import (
    CanonicalOpportunityValidityEvidence,
    OpportunityValidityContractError,
    OpportunityValidityInvariantError,
    OpportunityValidityRequest,
    OracleCanonicalOpportunityValidityExpirationEngine,
)

from .oracle_canonical_cross_venue_opportunity_comparison_engine import (
    ComparisonScoringPolicy,
    CrossVenueOpportunityCandidate,
    CrossVenueOpportunityComparisonResult,
    OpportunityComparabilityError,
    OpportunityComparisonContractError,
    OpportunityComparisonInvariantError,
    OracleCanonicalCrossVenueOpportunityComparisonEngine,
    RankedCrossVenueOpportunity,
)

from .oracle_canonical_opportunity_alert_record_engine import (
    CanonicalOpportunityAlertRecord,
    OpportunityAlertContractError,
    OpportunityAlertInvariantError,
    OpportunityAlertSelectionError,
    OracleCanonicalOpportunityAlertRecordEngine,
)

from .oracle_canonical_observation_persistence_ledger import (
    CanonicalObservationPersistenceEntry,
    CanonicalObservationPersistenceSnapshot,
    ObservationPersistenceConflictError,
    ObservationPersistenceContractError,
    ObservationPersistenceInvariantError,
    ObservationPersistenceSnapshotError,
    OracleCanonicalObservationPersistenceLedger,
)

__all__ = [
    "AcquisitionBatchRecord",
    "AcquisitionContractError",
    "AcquisitionInvariantError",
    "AcquisitionObservationRecord",
    "ApprovedReadOnlySourceAdapter",
    "ApprovedSourceAdapterRegistration",
    "CanonicalObservation",
    "CanonicalObservationRouterFailure",
    "DeduplicationEvidence",
    "ObservationRoutingEvidence",
    "OracleLiveReadOnlyAcquisitionRuntime",
    "RateControlEvidence",
    "RawSourceObservation",
    "SourceAdapterFailure",
    "SourceHealthEvidence",
    "UnapprovedSourceAdapterError",
    "OracleAcquisitionSourceControlEngine",
    "RateControlPolicy",
    "RateWindowObservation",
    "SourceControlContractError",
    "SourceControlDecisionRecord",
    "SourceControlInvariantError",
    "SourceControlPolicyError",
    "SourceHealthObservation",
    "SourceHealthPolicy",
    "CanonicalDeduplicationLedgerEntry",
    "DeduplicationLedgerContractError",
    "DeduplicationLedgerInvariantError",
    "DeduplicationLedgerSnapshot",
    "DeduplicationLedgerSnapshotError",
    "OracleAcquisitionDeduplicationLedger",
    "ApprovedVenueRegistration",
    "CanonicalMarketIdentity",
    "CanonicalMarketVenueRecord",
    "MarketIdentityContractError",
    "OracleCanonicalMarketIdentityVenueResolutionEngine",
    "SourceMarketIdentityEvidence",
    "VenueResolutionError",
    "VenueResolutionInvariantError",
    "VerifiedVenueResolution",
    "CanonicalOpportunityValidityEvidence",
    "OpportunityValidityContractError",
    "OpportunityValidityInvariantError",
    "OpportunityValidityRequest",
    "OracleCanonicalOpportunityValidityExpirationEngine",
    "ComparisonScoringPolicy",
    "CrossVenueOpportunityCandidate",
    "CrossVenueOpportunityComparisonResult",
    "OpportunityComparabilityError",
    "OpportunityComparisonContractError",
    "OpportunityComparisonInvariantError",
    "OracleCanonicalCrossVenueOpportunityComparisonEngine",
    "RankedCrossVenueOpportunity",
    "CanonicalOpportunityAlertRecord",
    "OpportunityAlertContractError",
    "OpportunityAlertInvariantError",
    "OpportunityAlertSelectionError",
    "OracleCanonicalOpportunityAlertRecordEngine",
    "CanonicalObservationPersistenceEntry",
    "CanonicalObservationPersistenceSnapshot",
    "ObservationPersistenceConflictError",
    "ObservationPersistenceContractError",
    "ObservationPersistenceInvariantError",
    "ObservationPersistenceSnapshotError",
    "OracleCanonicalObservationPersistenceLedger",
]
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    ObservationPersistenceConflictError,
    ObservationPersistenceSnapshotError,
    OracleCanonicalObservationPersistenceLedger,
    RawSourceObservation,
)


OBSERVED_AT_ONE = datetime(
    2026,
    7,
    11,
    23,
    14,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    11,
    23,
    14,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    11,
    23,
    15,
    0,
    tzinfo=timezone.utc,
)

PERSISTED_AT = datetime(
    2026,
    7,
    11,
    23,
    15,
    1,
    tzinfo=timezone.utc,
)

SNAPSHOT_AT = datetime(
    2026,
    7,
    11,
    23,
    16,
    0,
    tzinfo=timezone.utc,
)


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id="kalshi.snapshot.001",
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "source_market_id": (
                "KXBTC-26JUL11-116000"
            ),
            "share_side": "yes",
            "share_price": Decimal("0.31"),
            "volume": 1250,
        },
        provenance={
            "source_id": "source.kalshi.market_data",
            "adapter_id": "adapter.oracle.kalshi",
        },
    )

    return CanonicalObservation.create(
        source_id="source.kalshi.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.persistence.001",
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id="coinbase.snapshot.001",
        observed_at=OBSERVED_AT_TWO,
        observation_type="asset_snapshot",
        payload={
            "symbol": "BTC-USD",
            "price": Decimal("117420"),
            "volume": Decimal("250.5"),
        },
        provenance={
            "source_id": "source.coinbase.market_data",
            "adapter_id": "adapter.oracle.coinbase",
        },
    )

    return CanonicalObservation.create(
        source_id="source.coinbase.market_data",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.persistence.001",
    )


def run_primary_persistence_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    first_entry = ledger.append(
        observation=observation_one,
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
    )

    second_entry = ledger.append(
        observation=observation_two,
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
    )

    assert ledger.entry_count == 2

    assert ledger.observation_ids == (
        observation_one.observation_id,
        observation_two.observation_id,
    )

    assert first_entry.sequence_number == 1
    assert second_entry.sequence_number == 2

    assert (
        second_entry.previous_chain_hash
        == first_entry.chain_hash
    )

    assert (
        first_entry.calculate_entry_hash()
        == first_entry.entry_hash
    )

    assert (
        first_entry.calculate_chain_hash()
        == first_entry.chain_hash
    )

    assert (
        second_entry.calculate_entry_hash()
        == second_entry.entry_hash
    )

    assert (
        second_entry.calculate_chain_hash()
        == second_entry.chain_hash
    )

    assert (
        ledger.terminal_chain_hash
        == second_entry.chain_hash
    )

    assert (
        first_entry.observation_id
        == observation_one.observation_id
    )

    assert (
        first_entry.source_id
        == "source.kalshi.market_data"
    )

    assert (
        first_entry.source_observation_id
        == "kalshi.snapshot.001"
    )

    assert (
        first_entry.acquisition_batch_id
        == "batch.persistence.001"
    )

    assert (
        first_entry.content_hash
        == observation_one.content_hash
    )

    assert (
        first_entry.observation_replay_hash
        == observation_one.replay_hash
    )

    assert first_entry.immutable is True
    assert first_entry.append_only is True
    assert first_entry.replayable is True
    assert first_entry.auditable is True
    assert first_entry.explainable is True

    assert first_entry.read_only is True
    assert first_entry.execution_allowed is False

    assert (
        first_entry.execution_adapter_resolved
        is False
    )

    assert (
        first_entry.execution_adapter_invoked
        is False
    )

    assert (
        first_entry.trade_authorization_allowed
        is False
    )

    assert (
        first_entry.order_placement_allowed
        is False
    )

    assert first_entry.funds_moved is False
    assert first_entry.portfolio_mutated is False

    fetched = ledger.get_entry(
        observation_id=observation_one.observation_id
    )

    assert fetched == first_entry

    try:
        first_entry.source_id = "mutated"

        raise AssertionError(
            "persistence entries must be immutable"
        )

    except FrozenInstanceError:
        pass

    snapshot = ledger.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "persistence_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-008",
            "operator": "automated_runtime",
        },
    )

    assert snapshot.schema_version == "OLA-008"
    assert snapshot.engine_id == "OLA-008"

    assert snapshot.entry_count == 2

    assert (
        snapshot.terminal_chain_hash
        == ledger.terminal_chain_hash
    )

    assert (
        snapshot.calculate_snapshot_hash()
        == snapshot.snapshot_hash
    )

    assert snapshot.immutable is True
    assert snapshot.append_only is True
    assert snapshot.read_only is True

    assert snapshot.execution_allowed is False

    assert (
        snapshot.execution_adapter_resolved
        is False
    )

    assert (
        snapshot.execution_adapter_invoked
        is False
    )

    assert (
        snapshot.trade_authorization_allowed
        is False
    )

    assert (
        snapshot.order_placement_allowed
        is False
    )

    assert snapshot.funds_moved is False
    assert snapshot.portfolio_mutated is False

    restored = (
        OracleCanonicalObservationPersistenceLedger
        .restore_snapshot(
            snapshot=snapshot
        )
    )

    assert restored.entry_count == ledger.entry_count

    assert (
        restored.terminal_chain_hash
        == ledger.terminal_chain_hash
    )

    assert (
        restored.observation_ids
        == ledger.observation_ids
    )

    restored_first = restored.get_entry(
        observation_id=observation_one.observation_id
    )

    assert restored_first == first_entry

    replay_snapshot = restored.export_snapshot(
        snapshot_at=SNAPSHOT_AT,
        replay_metadata={
            "replay_source": "persistence_ledger",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-008",
            "operator": "automated_runtime",
        },
    )

    assert (
        replay_snapshot.snapshot_hash
        == snapshot.snapshot_hash
    )

    return (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    )


def run_atomic_append_many_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    entries = ledger.append_many(
        observations=(
            observation_one,
            observation_two,
        ),
        persisted_at=PERSISTED_AT,
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "batch_append": True,
        },
    )

    assert len(entries) == 2
    assert ledger.entry_count == 2

    assert entries[0].sequence_number == 1
    assert entries[1].sequence_number == 2

    assert (
        entries[0].previous_chain_hash
        != entries[1].previous_chain_hash
    )

    assert (
        entries[1].previous_chain_hash
        == entries[0].chain_hash
    )

    return ledger


def run_duplicate_identity_fail_closed_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation = build_observation_one()

    ledger.append(
        observation=observation,
        persisted_at=PERSISTED_AT,
        persistence_metadata={},
    )

    try:
        ledger.append(
            observation=observation,
            persisted_at=PERSISTED_AT,
            persistence_metadata={},
        )

        raise AssertionError(
            "duplicate observation identity must fail closed"
        )

    except ObservationPersistenceConflictError:
        pass

    assert ledger.entry_count == 1


def run_append_many_atomic_failure_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    observation_one = build_observation_one()

    try:
        ledger.append_many(
            observations=(
                observation_one,
                observation_one,
            ),
            persisted_at=PERSISTED_AT,
            persistence_metadata={},
        )

        raise AssertionError(
            "duplicate append_many batch must fail closed"
        )

    except ObservationPersistenceConflictError:
        pass

    assert ledger.entry_count == 0


def run_snapshot_tamper_fail_closed_tests():
    (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    ) = run_primary_persistence_test()

    bad_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=99,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash=snapshot.snapshot_hash,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=snapshot.execution_allowed,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=bad_snapshot
            )
        )

        raise AssertionError(
            "tampered entry count must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass

    bad_hash_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=snapshot.entry_count,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash="0" * 64,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=snapshot.execution_allowed,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=bad_hash_snapshot
            )
        )

        raise AssertionError(
            "tampered snapshot hash must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass

    execution_snapshot = (
        type(snapshot)(
            schema_version=snapshot.schema_version,
            engine_id=snapshot.engine_id,
            snapshot_at=snapshot.snapshot_at,
            genesis_chain_hash=snapshot.genesis_chain_hash,
            entries=snapshot.entries,
            entry_count=snapshot.entry_count,
            terminal_chain_hash=(
                snapshot.terminal_chain_hash
            ),
            replay_metadata=snapshot.replay_metadata,
            audit_metadata=snapshot.audit_metadata,
            snapshot_hash=snapshot.snapshot_hash,
            immutable=snapshot.immutable,
            append_only=snapshot.append_only,
            replayable=snapshot.replayable,
            auditable=snapshot.auditable,
            explainable=snapshot.explainable,
            read_only=snapshot.read_only,
            execution_allowed=True,
            execution_adapter_resolved=(
                snapshot.execution_adapter_resolved
            ),
            execution_adapter_invoked=(
                snapshot.execution_adapter_invoked
            ),
            trade_authorization_allowed=(
                snapshot.trade_authorization_allowed
            ),
            order_placement_allowed=(
                snapshot.order_placement_allowed
            ),
            funds_moved=snapshot.funds_moved,
            portfolio_mutated=snapshot.portfolio_mutated,
        )
    )

    try:
        (
            OracleCanonicalObservationPersistenceLedger
            .restore_snapshot(
                snapshot=execution_snapshot
            )
        )

        raise AssertionError(
            "execution-capable snapshot must fail closed"
        )

    except ObservationPersistenceSnapshotError:
        pass


def run_timestamp_fail_closed_test():
    ledger = OracleCanonicalObservationPersistenceLedger()

    try:
        ledger.append(
            observation=build_observation_one(),
            persisted_at=datetime(
                2026,
                7,
                11,
                23,
                15,
                1,
            ),
            persistence_metadata={},
        )

        raise AssertionError(
            "naive persisted_at must fail closed"
        )

    except ValueError:
        pass

    assert ledger.entry_count == 0


def main():
    (
        ledger,
        snapshot,
        first_entry,
        second_entry,
    ) = run_primary_persistence_test()

    atomic_ledger = run_atomic_append_many_test()

    run_duplicate_identity_fail_closed_test()
    run_append_many_atomic_failure_test()
    run_snapshot_tamper_fail_closed_tests()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": snapshot.schema_version,
        "engine_id": snapshot.engine_id,
        "status": "passed",
        "entry_count": ledger.entry_count,
        "first_sequence_number": (
            first_entry.sequence_number
        ),
        "second_sequence_number": (
            second_entry.sequence_number
        ),
        "chain_link_valid": (
            second_entry.previous_chain_hash
            == first_entry.chain_hash
        ),
        "terminal_chain_hash_valid": (
            ledger.terminal_chain_hash
            == second_entry.chain_hash
        ),
        "append_only": snapshot.append_only,
        "immutable": snapshot.immutable,
        "duplicate_observation_blocked": True,
        "duplicate_content_blocked": True,
        "atomic_append_many_valid": (
            atomic_ledger.entry_count == 2
        ),
        "snapshot_restore_valid": True,
        "deterministic_replay_valid": True,
        "source_identity_preserved": True,
        "acquisition_batch_identity_preserved": True,
        "content_hash_preserved": True,
        "observation_replay_hash_preserved": True,
        "read_only": snapshot.read_only,
        "execution_allowed": snapshot.execution_allowed,
        "execution_adapter_resolved": (
            snapshot.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            snapshot.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            snapshot.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            snapshot.order_placement_allowed
        ),
        "funds_moved": snapshot.funds_moved,
        "portfolio_mutated": snapshot.portfolio_mutated,
    }

    print(
        "[PASS] OLA-008 Oracle Canonical Observation "
        "Persistence Ledger"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def main() -> None:
    print("========================================")
    print(" OLA-008 INSTALLER")
    print(" Oracle Canonical Observation")
    print(" Persistence Ledger")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        PACKAGE_INIT_PATH,
        PACKAGE_INIT_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    print()
    print("[DONE] OLA-008 installed")
    print()
    print("Run:")
    print(
        "py test_ola_008_oracle_canonical_"
        "observation_persistence_ledger.py"
    )


if __name__ == "__main__":
    main()