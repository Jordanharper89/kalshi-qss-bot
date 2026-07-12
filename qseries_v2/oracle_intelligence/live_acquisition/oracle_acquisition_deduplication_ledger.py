"""
OLA-003
Oracle Acquisition Deduplication Ledger

Canonical deterministic deduplication evidence boundary for Oracle live
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
DEDUPLICATION                  <- OLA-003
    |
CANONICAL OBSERVATION
    |
ORACLE ROUTING
    |
PERSISTENCE

OLA-001 defines the deduplication hook contract.

OLA-003 provides the canonical implementation of that hook.

This ledger may:
- inspect canonical Oracle observation content hashes,
- retain immutable first-seen canonical identity evidence,
- identify duplicate canonical observations,
- emit OLA-001-compatible DeduplicationEvidence,
- export deterministic replayable ledger snapshots,
- restore deterministic snapshots fail closed,
- preserve audit and replay identity evidence.

This ledger may not:
- acquire source data,
- mutate canonical observations,
- route observations,
- authorize trades,
- place orders,
- invoke execution adapters,
- move funds,
- mutate portfolios.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    DeduplicationEvidence,
    JSONValue,
)


SCHEMA_VERSION = "OLA-003"
ENGINE_ID = "OLA-003"

ENTRY_RECORD_TYPE = (
    "canonical_deduplication_ledger_entry"
)

SNAPSHOT_RECORD_TYPE = (
    "deduplication_ledger_snapshot"
)


class DeduplicationLedgerContractError(ValueError):
    """Raised when ledger contract data is malformed."""


class DeduplicationLedgerInvariantError(RuntimeError):
    """Raised when a permanent ledger invariant is violated."""


class DeduplicationLedgerSnapshotError(
    DeduplicationLedgerContractError
):
    """Raised when deterministic snapshot data is incompatible."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise DeduplicationLedgerContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise DeduplicationLedgerContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise DeduplicationLedgerContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise DeduplicationLedgerContractError(
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
        raise DeduplicationLedgerSnapshotError(
            f"{field_name} must be ISO-8601 datetime text"
        ) from exc

    try:
        return _require_aware_datetime(
            parsed,
            field_name,
        )
    except DeduplicationLedgerContractError as exc:
        raise DeduplicationLedgerSnapshotError(
            str(exc)
        ) from exc


def _canonicalize(value: Any) -> JSONValue:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise DeduplicationLedgerContractError(
                "non-finite float values are not canonical"
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
        canonical_mapping: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise DeduplicationLedgerContractError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(
                value[key]
            )

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise DeduplicationLedgerContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    return sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise DeduplicationLedgerContractError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise DeduplicationLedgerContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    return tuple(
        (key, canonical_value[key])
        for key in sorted(canonical_value)
    )


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


def _require_exact_bool(
    value: Any,
    field_name: str,
    expected: bool,
) -> bool:
    if not isinstance(value, bool):
        raise DeduplicationLedgerSnapshotError(
            f"{field_name} must be a bool"
        )

    if value is not expected:
        raise DeduplicationLedgerSnapshotError(
            f"{field_name} invariant is incompatible"
        )

    return value


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DeduplicationLedgerSnapshotError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise DeduplicationLedgerSnapshotError(
            f"{field_name} must be non-negative"
        )

    return value


@dataclass(frozen=True, slots=True)
class CanonicalDeduplicationLedgerEntry:
    schema_version: str
    content_hash: str
    canonical_observation_id: str
    source_id: str
    observation_type: str
    first_seen_at: datetime
    first_acquisition_batch_id: str
    metadata: tuple[tuple[str, JSONValue], ...]
    entry_hash: str

    @staticmethod
    def build_hash_payload(
        *,
        schema_version: str,
        content_hash: str,
        canonical_observation_id: str,
        source_id: str,
        observation_type: str,
        first_seen_at: datetime,
        first_acquisition_batch_id: str,
        metadata: tuple[tuple[str, JSONValue], ...],
    ) -> dict[str, Any]:
        return {
            "schema_version": schema_version,
            "record_type": ENTRY_RECORD_TYPE,
            "content_hash": content_hash,
            "canonical_observation_id": (
                canonical_observation_id
            ),
            "source_id": source_id,
            "observation_type": observation_type,
            "first_seen_at": first_seen_at,
            "first_acquisition_batch_id": (
                first_acquisition_batch_id
            ),
            "metadata": _mapping_from_immutable(
                metadata
            ),
        }

    @classmethod
    def create(
        cls,
        *,
        observation: CanonicalObservation,
        first_seen_at: datetime,
        metadata: Mapping[str, Any],
    ) -> "CanonicalDeduplicationLedgerEntry":
        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise DeduplicationLedgerContractError(
                "observation must be CanonicalObservation"
            )

        normalized_first_seen_at = _require_aware_datetime(
            first_seen_at,
            "first_seen_at",
        )

        if normalized_first_seen_at < observation.observed_at:
            raise DeduplicationLedgerContractError(
                "first_seen_at cannot be before observed_at"
            )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        hash_payload = cls.build_hash_payload(
            schema_version=SCHEMA_VERSION,
            content_hash=observation.content_hash,
            canonical_observation_id=(
                observation.observation_id
            ),
            source_id=observation.source_id,
            observation_type=observation.observation_type,
            first_seen_at=normalized_first_seen_at,
            first_acquisition_batch_id=(
                observation.acquisition_batch_id
            ),
            metadata=immutable_metadata,
        )

        return cls(
            schema_version=SCHEMA_VERSION,
            content_hash=observation.content_hash,
            canonical_observation_id=(
                observation.observation_id
            ),
            source_id=observation.source_id,
            observation_type=observation.observation_type,
            first_seen_at=normalized_first_seen_at,
            first_acquisition_batch_id=(
                observation.acquisition_batch_id
            ),
            metadata=immutable_metadata,
            entry_hash=stable_hash(hash_payload),
        )

    def calculate_entry_hash(self) -> str:
        return stable_hash(
            self.build_hash_payload(
                schema_version=self.schema_version,
                content_hash=self.content_hash,
                canonical_observation_id=(
                    self.canonical_observation_id
                ),
                source_id=self.source_id,
                observation_type=self.observation_type,
                first_seen_at=self.first_seen_at,
                first_acquisition_batch_id=(
                    self.first_acquisition_batch_id
                ),
                metadata=self.metadata,
            )
        )

    def to_canonical_dict(
        self,
        *,
        include_entry_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "content_hash": self.content_hash,
            "canonical_observation_id": (
                self.canonical_observation_id
            ),
            "source_id": self.source_id,
            "observation_type": self.observation_type,
            "first_seen_at": self.first_seen_at.isoformat(),
            "first_acquisition_batch_id": (
                self.first_acquisition_batch_id
            ),
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
        }

        if include_entry_hash:
            result["entry_hash"] = self.entry_hash

        return result


@dataclass(frozen=True, slots=True)
class DeduplicationLedgerSnapshot:
    schema_version: str
    engine_id: str
    policy_id: str
    snapshot_at: datetime
    entries: tuple[
        CanonicalDeduplicationLedgerEntry,
        ...
    ]
    entry_count: int
    replay_metadata: tuple[tuple[str, JSONValue], ...]
    audit_metadata: tuple[tuple[str, JSONValue], ...]
    snapshot_hash: str
    read_only: bool
    execution_allowed: bool
    acquisition_performed: bool
    routing_performed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @staticmethod
    def build_hash_payload(
        *,
        schema_version: str,
        engine_id: str,
        policy_id: str,
        snapshot_at: datetime,
        entries: tuple[
            CanonicalDeduplicationLedgerEntry,
            ...
        ],
        entry_count: int,
        replay_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
        audit_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
        read_only: bool,
        execution_allowed: bool,
        acquisition_performed: bool,
        routing_performed: bool,
        trade_authorization_allowed: bool,
        order_placement_allowed: bool,
        execution_adapter_invocation_allowed: bool,
        funds_moved: bool,
        portfolio_mutated: bool,
    ) -> dict[str, Any]:
        return {
            "schema_version": schema_version,
            "record_type": SNAPSHOT_RECORD_TYPE,
            "engine_id": engine_id,
            "policy_id": policy_id,
            "snapshot_at": snapshot_at,
            "entries": [
                entry.to_canonical_dict()
                for entry in entries
            ],
            "entry_count": entry_count,
            "replay_metadata": _mapping_from_immutable(
                replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                audit_metadata
            ),
            "read_only": read_only,
            "execution_allowed": execution_allowed,
            "acquisition_performed": acquisition_performed,
            "routing_performed": routing_performed,
            "trade_authorization_allowed": (
                trade_authorization_allowed
            ),
            "order_placement_allowed": (
                order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                execution_adapter_invocation_allowed
            ),
            "funds_moved": funds_moved,
            "portfolio_mutated": portfolio_mutated,
        }

    def calculate_snapshot_hash(self) -> str:
        return stable_hash(
            self.build_hash_payload(
                schema_version=self.schema_version,
                engine_id=self.engine_id,
                policy_id=self.policy_id,
                snapshot_at=self.snapshot_at,
                entries=self.entries,
                entry_count=self.entry_count,
                replay_metadata=self.replay_metadata,
                audit_metadata=self.audit_metadata,
                read_only=self.read_only,
                execution_allowed=self.execution_allowed,
                acquisition_performed=(
                    self.acquisition_performed
                ),
                routing_performed=self.routing_performed,
                trade_authorization_allowed=(
                    self.trade_authorization_allowed
                ),
                order_placement_allowed=(
                    self.order_placement_allowed
                ),
                execution_adapter_invocation_allowed=(
                    self.execution_adapter_invocation_allowed
                ),
                funds_moved=self.funds_moved,
                portfolio_mutated=self.portfolio_mutated,
            )
        )

    def to_canonical_dict(
        self,
        *,
        include_snapshot_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "policy_id": self.policy_id,
            "snapshot_at": self.snapshot_at.isoformat(),
            "entries": [
                entry.to_canonical_dict()
                for entry in self.entries
            ],
            "entry_count": self.entry_count,
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "acquisition_performed": self.acquisition_performed,
            "routing_performed": self.routing_performed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        if include_snapshot_hash:
            result["snapshot_hash"] = self.snapshot_hash

        return result


class OracleAcquisitionDeduplicationLedger:
    """
    Canonical content-hash deduplication implementation for OLA-001.

    The ledger is append-only with respect to canonical first-seen
    observation identities.

    A repeated content hash never replaces or mutates its canonical entry.

    Determinism:
    - caller supplies checked_at,
    - caller supplies snapshot_at,
    - one canonical entry hash payload is used for creation and restore,
    - one canonical snapshot hash payload is used for creation and restore,
    - canonical JSON and SHA-256 are used,
    - repr() is never used.

    Fail closed:
    - only CanonicalObservation input is accepted,
    - malformed timestamps are rejected,
    - conflicting restored content hashes are rejected,
    - incompatible entry hashes are rejected,
    - incompatible snapshot hashes are rejected,
    - policy mismatches are rejected.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True
    execution_allowed = False
    acquisition_performed = False
    routing_performed = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        policy_id: str = "oracle.dedup.content_hash.v1",
        entry_metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self._policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )

        self._entry_metadata = _immutable_mapping(
            (
                {}
                if entry_metadata is None
                else entry_metadata
            ),
            "entry_metadata",
        )

        self._entries_by_content_hash: dict[
            str,
            CanonicalDeduplicationLedgerEntry,
        ] = {}

        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "acquisition_performed": self.acquisition_performed,
            "routing_performed": self.routing_performed,
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                self.execution_adapter_invocation_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": self.portfolio_mutated,
        }

        expected = {
            "read_only": True,
            "execution_allowed": False,
            "acquisition_performed": False,
            "routing_performed": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if actual != expected:
            raise DeduplicationLedgerInvariantError(
                "Oracle deduplication ledger invariants violated"
            )

    @property
    def policy_id(self) -> str:
        return self._policy_id

    @property
    def entry_count(self) -> int:
        return len(self._entries_by_content_hash)

    @property
    def content_hashes(self) -> tuple[str, ...]:
        return tuple(
            sorted(self._entries_by_content_hash)
        )

    def evaluate(
        self,
        observation: CanonicalObservation,
        checked_at: datetime,
    ) -> DeduplicationEvidence:
        """
        OLA-001-compatible deduplication hook.
        """

        self._assert_invariants()

        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise DeduplicationLedgerContractError(
                "observation must be CanonicalObservation"
            )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        if normalized_checked_at < observation.observed_at:
            raise DeduplicationLedgerContractError(
                "checked_at cannot be before observed_at"
            )

        existing = self._entries_by_content_hash.get(
            observation.content_hash
        )

        if existing is None:
            entry = CanonicalDeduplicationLedgerEntry.create(
                observation=observation,
                first_seen_at=normalized_checked_at,
                metadata=_mapping_from_immutable(
                    self._entry_metadata
                ),
            )

            self._entries_by_content_hash[
                observation.content_hash
            ] = entry

            duplicate = False
            canonical_observation_id = (
                observation.observation_id
            )
        else:
            self._validate_existing_entry(
                observation=observation,
                entry=existing,
            )

            duplicate = True

            canonical_observation_id = (
                existing.canonical_observation_id
            )

        return DeduplicationEvidence.create(
            observation=observation,
            duplicate=duplicate,
            canonical_observation_id=(
                canonical_observation_id
            ),
            checked_at=normalized_checked_at,
            deduplication_policy_id=self._policy_id,
        )

    __call__ = evaluate

    def _validate_existing_entry(
        self,
        *,
        observation: CanonicalObservation,
        entry: CanonicalDeduplicationLedgerEntry,
    ) -> None:
        if entry.calculate_entry_hash() != entry.entry_hash:
            raise DeduplicationLedgerInvariantError(
                "existing ledger entry hash is invalid"
            )

        if entry.content_hash != observation.content_hash:
            raise DeduplicationLedgerInvariantError(
                "ledger content-hash index is inconsistent"
            )

        if (
            entry.canonical_observation_id
            != observation.observation_id
        ):
            raise DeduplicationLedgerInvariantError(
                "identical canonical content hash produced "
                "conflicting observation identity"
            )

        if entry.source_id != observation.source_id:
            raise DeduplicationLedgerInvariantError(
                "identical canonical content hash produced "
                "conflicting source identity"
            )

        if (
            entry.observation_type
            != observation.observation_type
        ):
            raise DeduplicationLedgerInvariantError(
                "identical canonical content hash produced "
                "conflicting observation type"
            )

    def get_entry(
        self,
        *,
        content_hash: str,
    ) -> CanonicalDeduplicationLedgerEntry | None:
        normalized_content_hash = _require_non_empty_string(
            content_hash,
            "content_hash",
        )

        entry = self._entries_by_content_hash.get(
            normalized_content_hash
        )

        if entry is not None:
            if entry.calculate_entry_hash() != entry.entry_hash:
                raise DeduplicationLedgerInvariantError(
                    "stored ledger entry hash validation failed"
                )

        return entry

    def export_snapshot(
        self,
        *,
        snapshot_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> DeduplicationLedgerSnapshot:
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

        entries = tuple(
            self._entries_by_content_hash[
                content_hash
            ]
            for content_hash in sorted(
                self._entries_by_content_hash
            )
        )

        for entry in entries:
            if entry.calculate_entry_hash() != entry.entry_hash:
                raise DeduplicationLedgerInvariantError(
                    "entry hash validation failed before snapshot"
                )

            if entry.first_seen_at > normalized_snapshot_at:
                raise DeduplicationLedgerContractError(
                    "snapshot_at cannot be before an entry "
                    "first_seen_at"
                )

        provisional = DeduplicationLedgerSnapshot(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            policy_id=self._policy_id,
            snapshot_at=normalized_snapshot_at,
            entries=entries,
            entry_count=len(entries),
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            snapshot_hash="",
            read_only=True,
            execution_allowed=False,
            acquisition_performed=False,
            routing_performed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        snapshot_hash = (
            provisional.calculate_snapshot_hash()
        )

        return DeduplicationLedgerSnapshot(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            policy_id=provisional.policy_id,
            snapshot_at=provisional.snapshot_at,
            entries=provisional.entries,
            entry_count=provisional.entry_count,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            snapshot_hash=snapshot_hash,
            read_only=True,
            execution_allowed=False,
            acquisition_performed=False,
            routing_performed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    @classmethod
    def restore_snapshot(
        cls,
        *,
        snapshot: DeduplicationLedgerSnapshot,
        entry_metadata: Mapping[str, Any] | None = None,
    ) -> "OracleAcquisitionDeduplicationLedger":
        if not isinstance(
            snapshot,
            DeduplicationLedgerSnapshot,
        ):
            raise DeduplicationLedgerSnapshotError(
                "snapshot must be DeduplicationLedgerSnapshot"
            )

        if snapshot.schema_version != SCHEMA_VERSION:
            raise DeduplicationLedgerSnapshotError(
                "snapshot schema_version is incompatible"
            )

        if snapshot.engine_id != ENGINE_ID:
            raise DeduplicationLedgerSnapshotError(
                "snapshot engine_id is incompatible"
            )

        if snapshot.entry_count != len(snapshot.entries):
            raise DeduplicationLedgerSnapshotError(
                "snapshot entry_count does not match entries"
            )

        if snapshot.read_only is not True:
            raise DeduplicationLedgerSnapshotError(
                "snapshot read_only invariant is incompatible"
            )

        false_invariants = {
            "execution_allowed": snapshot.execution_allowed,
            "acquisition_performed": (
                snapshot.acquisition_performed
            ),
            "routing_performed": snapshot.routing_performed,
            "trade_authorization_allowed": (
                snapshot.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                snapshot.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                snapshot.execution_adapter_invocation_allowed
            ),
            "funds_moved": snapshot.funds_moved,
            "portfolio_mutated": snapshot.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise DeduplicationLedgerSnapshotError(
                "snapshot no-execution invariants are incompatible"
            )

        expected_snapshot_hash = (
            snapshot.calculate_snapshot_hash()
        )

        if expected_snapshot_hash != snapshot.snapshot_hash:
            raise DeduplicationLedgerSnapshotError(
                "snapshot_hash validation failed"
            )

        ledger = cls(
            policy_id=snapshot.policy_id,
            entry_metadata=entry_metadata,
        )

        for entry in snapshot.entries:
            ledger._restore_entry(entry)

        if ledger.entry_count != snapshot.entry_count:
            raise DeduplicationLedgerSnapshotError(
                "restored entry count mismatch"
            )

        return ledger

    def _restore_entry(
        self,
        entry: CanonicalDeduplicationLedgerEntry,
    ) -> None:
        if not isinstance(
            entry,
            CanonicalDeduplicationLedgerEntry,
        ):
            raise DeduplicationLedgerSnapshotError(
                "snapshot contains incompatible entry"
            )

        if entry.schema_version != SCHEMA_VERSION:
            raise DeduplicationLedgerSnapshotError(
                "entry schema_version is incompatible"
            )

        expected_entry_hash = entry.calculate_entry_hash()

        if expected_entry_hash != entry.entry_hash:
            raise DeduplicationLedgerSnapshotError(
                "entry_hash validation failed"
            )

        existing = self._entries_by_content_hash.get(
            entry.content_hash
        )

        if existing is not None:
            if existing != entry:
                raise DeduplicationLedgerSnapshotError(
                    "snapshot contains conflicting duplicate "
                    "content hash"
                )

            raise DeduplicationLedgerSnapshotError(
                "snapshot contains duplicate content hash"
            )

        self._entries_by_content_hash[
            entry.content_hash
        ] = entry

    @classmethod
    def restore_canonical_dict(
        cls,
        *,
        snapshot_data: Mapping[str, Any],
        entry_metadata: Mapping[str, Any] | None = None,
    ) -> "OracleAcquisitionDeduplicationLedger":
        if not isinstance(snapshot_data, Mapping):
            raise DeduplicationLedgerSnapshotError(
                "snapshot_data must be a mapping"
            )

        required_fields = {
            "schema_version",
            "engine_id",
            "policy_id",
            "snapshot_at",
            "entries",
            "entry_count",
            "replay_metadata",
            "audit_metadata",
            "snapshot_hash",
            "read_only",
            "execution_allowed",
            "acquisition_performed",
            "routing_performed",
            "trade_authorization_allowed",
            "order_placement_allowed",
            "execution_adapter_invocation_allowed",
            "funds_moved",
            "portfolio_mutated",
        }

        if set(snapshot_data.keys()) != required_fields:
            raise DeduplicationLedgerSnapshotError(
                "snapshot_data fields are incompatible"
            )

        entries_data = snapshot_data["entries"]

        if not isinstance(entries_data, list):
            raise DeduplicationLedgerSnapshotError(
                "snapshot entries must be a list"
            )

        entries: list[
            CanonicalDeduplicationLedgerEntry
        ] = []

        for entry_data in entries_data:
            entries.append(
                cls._entry_from_canonical_dict(
                    entry_data
                )
            )

        snapshot = DeduplicationLedgerSnapshot(
            schema_version=_require_non_empty_string(
                snapshot_data["schema_version"],
                "schema_version",
            ),
            engine_id=_require_non_empty_string(
                snapshot_data["engine_id"],
                "engine_id",
            ),
            policy_id=_require_non_empty_string(
                snapshot_data["policy_id"],
                "policy_id",
            ),
            snapshot_at=_parse_aware_datetime(
                snapshot_data["snapshot_at"],
                "snapshot_at",
            ),
            entries=tuple(entries),
            entry_count=_require_non_negative_int(
                snapshot_data["entry_count"],
                "entry_count",
            ),
            replay_metadata=_immutable_mapping(
                snapshot_data["replay_metadata"],
                "replay_metadata",
            ),
            audit_metadata=_immutable_mapping(
                snapshot_data["audit_metadata"],
                "audit_metadata",
            ),
            snapshot_hash=_require_non_empty_string(
                snapshot_data["snapshot_hash"],
                "snapshot_hash",
            ),
            read_only=_require_exact_bool(
                snapshot_data["read_only"],
                "read_only",
                True,
            ),
            execution_allowed=_require_exact_bool(
                snapshot_data["execution_allowed"],
                "execution_allowed",
                False,
            ),
            acquisition_performed=_require_exact_bool(
                snapshot_data["acquisition_performed"],
                "acquisition_performed",
                False,
            ),
            routing_performed=_require_exact_bool(
                snapshot_data["routing_performed"],
                "routing_performed",
                False,
            ),
            trade_authorization_allowed=(
                _require_exact_bool(
                    snapshot_data[
                        "trade_authorization_allowed"
                    ],
                    "trade_authorization_allowed",
                    False,
                )
            ),
            order_placement_allowed=_require_exact_bool(
                snapshot_data["order_placement_allowed"],
                "order_placement_allowed",
                False,
            ),
            execution_adapter_invocation_allowed=(
                _require_exact_bool(
                    snapshot_data[
                        "execution_adapter_invocation_allowed"
                    ],
                    "execution_adapter_invocation_allowed",
                    False,
                )
            ),
            funds_moved=_require_exact_bool(
                snapshot_data["funds_moved"],
                "funds_moved",
                False,
            ),
            portfolio_mutated=_require_exact_bool(
                snapshot_data["portfolio_mutated"],
                "portfolio_mutated",
                False,
            ),
        )

        return cls.restore_snapshot(
            snapshot=snapshot,
            entry_metadata=entry_metadata,
        )

    @staticmethod
    def _entry_from_canonical_dict(
        entry_data: Any,
    ) -> CanonicalDeduplicationLedgerEntry:
        if not isinstance(entry_data, Mapping):
            raise DeduplicationLedgerSnapshotError(
                "snapshot entry must be a mapping"
            )

        required_fields = {
            "schema_version",
            "content_hash",
            "canonical_observation_id",
            "source_id",
            "observation_type",
            "first_seen_at",
            "first_acquisition_batch_id",
            "metadata",
            "entry_hash",
        }

        if set(entry_data.keys()) != required_fields:
            raise DeduplicationLedgerSnapshotError(
                "snapshot entry fields are incompatible"
            )

        return CanonicalDeduplicationLedgerEntry(
            schema_version=_require_non_empty_string(
                entry_data["schema_version"],
                "entry.schema_version",
            ),
            content_hash=_require_non_empty_string(
                entry_data["content_hash"],
                "entry.content_hash",
            ),
            canonical_observation_id=(
                _require_non_empty_string(
                    entry_data["canonical_observation_id"],
                    "entry.canonical_observation_id",
                )
            ),
            source_id=_require_non_empty_string(
                entry_data["source_id"],
                "entry.source_id",
            ),
            observation_type=_require_non_empty_string(
                entry_data["observation_type"],
                "entry.observation_type",
            ),
            first_seen_at=_parse_aware_datetime(
                entry_data["first_seen_at"],
                "entry.first_seen_at",
            ),
            first_acquisition_batch_id=(
                _require_non_empty_string(
                    entry_data[
                        "first_acquisition_batch_id"
                    ],
                    "entry.first_acquisition_batch_id",
                )
            ),
            metadata=_immutable_mapping(
                entry_data["metadata"],
                "entry.metadata",
            ),
            entry_hash=_require_non_empty_string(
                entry_data["entry_hash"],
                "entry.entry_hash",
            ),
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENTRY_RECORD_TYPE",
    "SNAPSHOT_RECORD_TYPE",
    "DeduplicationLedgerContractError",
    "DeduplicationLedgerInvariantError",
    "DeduplicationLedgerSnapshotError",
    "CanonicalDeduplicationLedgerEntry",
    "DeduplicationLedgerSnapshot",
    "OracleAcquisitionDeduplicationLedger",
    "canonical_json",
    "stable_hash",
]
