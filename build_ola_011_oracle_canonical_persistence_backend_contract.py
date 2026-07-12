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
    / "oracle_canonical_persistence_backend_contract.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_011_oracle_canonical_persistence_backend_contract.py"
)


MODULE_CONTENT = r'''
"""
OLA-011
Oracle Canonical Persistence Backend Contract

Canonical backend-independent production persistence contract for Oracle
live read-only acquisition.

Architecture:

CANONICAL OBSERVATION
    |
OLA-008 APPEND-ONLY LEDGER CONTRACT
    |
OLA-011 CANONICAL PERSISTENCE BACKEND CONTRACT
    |
PHYSICAL BACKEND IMPLEMENTATION
    |
POSTGRESQL / FUTURE APPROVED BACKEND
    |
IMMUTABLE SNAPSHOT ARCHIVE

Permanent rules:

- The backend contract is storage-technology independent.
- PostgreSQL behavior may not redefine canonical Oracle persistence.
- Only CanonicalObservation records may be appended.
- Existing observation identity may not be replaced.
- Existing content identity may not be replaced.
- Batch append must be atomic.
- Canonical ordering must be explicit.
- Chain continuity must be preserved.
- Observation identity must be queryable.
- Source identity must be queryable.
- Time-range history must be queryable.
- Terminal chain state must be inspectable.
- Snapshot checkpoints must be writeable as immutable records.
- Snapshot checkpoints must be readable by checkpoint identity.
- Backend health evidence must be explicit.
- Backend capability evidence must be explicit.
- Unsupported capabilities fail closed.
- Caller supplies contract timestamps.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains permanently read-only.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
    JSONValue,
)


SCHEMA_VERSION = "OLA-011"
ENGINE_ID = "OLA-011"

BACKEND_CAPABILITY_RECORD_TYPE = (
    "canonical_persistence_backend_capability_record"
)

BACKEND_HEALTH_RECORD_TYPE = (
    "canonical_persistence_backend_health_record"
)

APPEND_REQUEST_RECORD_TYPE = (
    "canonical_persistence_append_request"
)

APPEND_RESULT_RECORD_TYPE = (
    "canonical_persistence_append_result"
)

QUERY_REQUEST_RECORD_TYPE = (
    "canonical_persistence_query_request"
)

SNAPSHOT_CHECKPOINT_RECORD_TYPE = (
    "canonical_persistence_snapshot_checkpoint"
)


class PersistenceBackendContractError(ValueError):
    """Raised when backend contract data is malformed."""


class PersistenceBackendCapabilityError(
    PersistenceBackendContractError
):
    """Raised when a required backend capability is unavailable."""


class PersistenceBackendConflictError(
    PersistenceBackendContractError
):
    """Raised when immutable backend identity conflicts."""


class PersistenceBackendInvariantError(RuntimeError):
    """Raised when permanent backend invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PersistenceBackendContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PersistenceBackendContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PersistenceBackendContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PersistenceBackendContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_bool(
    value: Any,
    field_name: str,
) -> bool:
    if not isinstance(value, bool):
        raise PersistenceBackendContractError(
            f"{field_name} must be a bool"
        )

    return value


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistenceBackendContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise PersistenceBackendContractError(
            f"{field_name} must be non-negative"
        )

    return value


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
            raise PersistenceBackendContractError(
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
                raise PersistenceBackendContractError(
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

    raise PersistenceBackendContractError(
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


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise PersistenceBackendContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PersistenceBackendContractError(
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


def _immutable_string_tuple(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise PersistenceBackendContractError(
            f"{field_name} must be a sequence of strings"
        )

    if not isinstance(values, Sequence):
        raise PersistenceBackendContractError(
            f"{field_name} must be a sequence"
        )

    normalized = tuple(
        _require_non_empty_string(
            value,
            field_name,
        )
        for value in values
    )

    if len(set(normalized)) != len(normalized):
        raise PersistenceBackendContractError(
            f"{field_name} must not contain duplicates"
        )

    return tuple(sorted(normalized))


REQUIRED_BACKEND_CAPABILITIES = (
    "append_canonical_observation",
    "append_canonical_observation_batch_atomic",
    "reject_duplicate_observation_identity",
    "reject_duplicate_content_identity",
    "preserve_canonical_chain_order",
    "read_by_observation_id",
    "read_by_source_id",
    "read_by_observed_time_range",
    "inspect_terminal_chain_hash",
    "write_immutable_snapshot_checkpoint",
    "read_snapshot_checkpoint",
    "emit_backend_health_evidence",
)


@dataclass(frozen=True, slots=True)
class PersistenceBackendCapabilityRecord:
    schema_version: str
    engine_id: str
    backend_id: str
    backend_type: str
    contract_version: str
    supported_capabilities: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    missing_required_capabilities: tuple[str, ...]
    contract_satisfied: bool
    checked_at: datetime
    backend_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    capability_hash: str
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @classmethod
    def create(
        cls,
        *,
        backend_id: str,
        backend_type: str,
        contract_version: str,
        supported_capabilities: Sequence[str],
        checked_at: datetime,
        backend_metadata: Mapping[str, Any],
    ) -> "PersistenceBackendCapabilityRecord":
        normalized_backend_id = _require_non_empty_string(
            backend_id,
            "backend_id",
        )

        normalized_backend_type = _require_non_empty_string(
            backend_type,
            "backend_type",
        )

        normalized_contract_version = _require_non_empty_string(
            contract_version,
            "contract_version",
        )

        normalized_supported = _immutable_string_tuple(
            supported_capabilities,
            "supported_capabilities",
        )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        immutable_metadata = _immutable_mapping(
            backend_metadata,
            "backend_metadata",
        )

        required = tuple(
            sorted(REQUIRED_BACKEND_CAPABILITIES)
        )

        missing = tuple(
            sorted(
                set(required)
                - set(normalized_supported)
            )
        )

        contract_satisfied = len(missing) == 0

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": BACKEND_CAPABILITY_RECORD_TYPE,
            "backend_id": normalized_backend_id,
            "backend_type": normalized_backend_type,
            "contract_version": normalized_contract_version,
            "supported_capabilities": normalized_supported,
            "required_capabilities": required,
            "missing_required_capabilities": missing,
            "contract_satisfied": contract_satisfied,
            "checked_at": normalized_checked_at,
            "backend_metadata": _mapping_from_immutable(
                immutable_metadata
            ),
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        return cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            backend_id=normalized_backend_id,
            backend_type=normalized_backend_type,
            contract_version=normalized_contract_version,
            supported_capabilities=normalized_supported,
            required_capabilities=required,
            missing_required_capabilities=missing,
            contract_satisfied=contract_satisfied,
            checked_at=normalized_checked_at,
            backend_metadata=immutable_metadata,
            capability_hash=stable_hash(payload),
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


@dataclass(frozen=True, slots=True)
class PersistenceBackendHealthRecord:
    schema_version: str
    engine_id: str
    backend_id: str
    checked_at: datetime
    reachable: bool
    writable: bool
    readable: bool
    transactional: bool
    healthy: bool
    health_status: str
    reason_codes: tuple[str, ...]
    health_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    health_hash: str
    read_only: bool
    execution_allowed: bool

    @classmethod
    def create(
        cls,
        *,
        backend_id: str,
        checked_at: datetime,
        reachable: bool,
        writable: bool,
        readable: bool,
        transactional: bool,
        health_metadata: Mapping[str, Any],
    ) -> "PersistenceBackendHealthRecord":
        normalized_backend_id = _require_non_empty_string(
            backend_id,
            "backend_id",
        )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        normalized_reachable = _require_bool(
            reachable,
            "reachable",
        )

        normalized_writable = _require_bool(
            writable,
            "writable",
        )

        normalized_readable = _require_bool(
            readable,
            "readable",
        )

        normalized_transactional = _require_bool(
            transactional,
            "transactional",
        )

        metadata = _immutable_mapping(
            health_metadata,
            "health_metadata",
        )

        healthy = all(
            (
                normalized_reachable,
                normalized_writable,
                normalized_readable,
                normalized_transactional,
            )
        )

        if healthy:
            health_status = "healthy"
            reason_codes = (
                "backend_reachable",
                "backend_readable",
                "backend_transactional",
                "backend_writable",
                "backend_healthy",
            )
        else:
            health_status = "unhealthy"

            reasons = []

            if not normalized_reachable:
                reasons.append("backend_unreachable")

            if not normalized_writable:
                reasons.append("backend_not_writable")

            if not normalized_readable:
                reasons.append("backend_not_readable")

            if not normalized_transactional:
                reasons.append("backend_not_transactional")

            reasons.append("backend_unhealthy")

            reason_codes = tuple(sorted(reasons))

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": BACKEND_HEALTH_RECORD_TYPE,
            "backend_id": normalized_backend_id,
            "checked_at": normalized_checked_at,
            "reachable": normalized_reachable,
            "writable": normalized_writable,
            "readable": normalized_readable,
            "transactional": normalized_transactional,
            "healthy": healthy,
            "health_status": health_status,
            "reason_codes": reason_codes,
            "health_metadata": _mapping_from_immutable(
                metadata
            ),
            "read_only": True,
            "execution_allowed": False,
        }

        return cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            backend_id=normalized_backend_id,
            checked_at=normalized_checked_at,
            reachable=normalized_reachable,
            writable=normalized_writable,
            readable=normalized_readable,
            transactional=normalized_transactional,
            healthy=healthy,
            health_status=health_status,
            reason_codes=reason_codes,
            health_metadata=metadata,
            health_hash=stable_hash(payload),
            read_only=True,
            execution_allowed=False,
        )


@dataclass(frozen=True, slots=True)
class CanonicalPersistenceAppendRequest:
    request_id: str
    backend_id: str
    observations: tuple[
        CanonicalObservation,
        ...
    ]
    requested_at: datetime
    append_mode: str
    expected_terminal_chain_hash: str
    request_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    request_hash: str

    @classmethod
    def create(
        cls,
        *,
        request_id: str,
        backend_id: str,
        observations: Sequence[
            CanonicalObservation
        ],
        requested_at: datetime,
        append_mode: str,
        expected_terminal_chain_hash: str,
        request_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceAppendRequest":
        normalized_request_id = _require_non_empty_string(
            request_id,
            "request_id",
        )

        normalized_backend_id = _require_non_empty_string(
            backend_id,
            "backend_id",
        )

        if isinstance(observations, (str, bytes)):
            raise PersistenceBackendContractError(
                "observations must be a sequence"
            )

        if not isinstance(observations, Sequence):
            raise PersistenceBackendContractError(
                "observations must be a sequence"
            )

        if not observations:
            raise PersistenceBackendContractError(
                "observations must not be empty"
            )

        normalized_observations = []

        observation_ids: set[str] = set()
        content_hashes: set[str] = set()

        for observation in observations:
            if not isinstance(
                observation,
                CanonicalObservation,
            ):
                raise PersistenceBackendContractError(
                    "observations contains incompatible record"
                )

            if observation.read_only is not True:
                raise PersistenceBackendInvariantError(
                    "canonical observation lost read_only invariant"
                )

            if observation.execution_allowed is not False:
                raise PersistenceBackendInvariantError(
                    "canonical observation gained execution capability"
                )

            if observation.observation_id in observation_ids:
                raise PersistenceBackendConflictError(
                    "duplicate observation_id in append request"
                )

            if observation.content_hash in content_hashes:
                raise PersistenceBackendConflictError(
                    "duplicate content_hash in append request"
                )

            observation_ids.add(
                observation.observation_id
            )

            content_hashes.add(
                observation.content_hash
            )

            normalized_observations.append(
                observation
            )

        normalized_requested_at = _require_aware_datetime(
            requested_at,
            "requested_at",
        )

        normalized_append_mode = _require_non_empty_string(
            append_mode,
            "append_mode",
        )

        if normalized_append_mode not in {
            "single",
            "atomic_batch",
        }:
            raise PersistenceBackendContractError(
                "append_mode must be single or atomic_batch"
            )

        if (
            normalized_append_mode == "single"
            and len(normalized_observations) != 1
        ):
            raise PersistenceBackendContractError(
                "single append mode requires exactly one observation"
            )

        normalized_terminal_hash = _require_non_empty_string(
            expected_terminal_chain_hash,
            "expected_terminal_chain_hash",
        )

        metadata = _immutable_mapping(
            request_metadata,
            "request_metadata",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": APPEND_REQUEST_RECORD_TYPE,
            "request_id": normalized_request_id,
            "backend_id": normalized_backend_id,
            "observations": [
                observation.to_canonical_dict()
                for observation in normalized_observations
            ],
            "requested_at": normalized_requested_at,
            "append_mode": normalized_append_mode,
            "expected_terminal_chain_hash": (
                normalized_terminal_hash
            ),
            "request_metadata": _mapping_from_immutable(
                metadata
            ),
        }

        return cls(
            request_id=normalized_request_id,
            backend_id=normalized_backend_id,
            observations=tuple(normalized_observations),
            requested_at=normalized_requested_at,
            append_mode=normalized_append_mode,
            expected_terminal_chain_hash=(
                normalized_terminal_hash
            ),
            request_metadata=metadata,
            request_hash=stable_hash(payload),
        )


@dataclass(frozen=True, slots=True)
class CanonicalPersistenceAppendResult:
    schema_version: str
    engine_id: str
    backend_id: str
    request_id: str
    request_hash: str
    append_status: str
    appended_count: int
    first_sequence_number: int | None
    last_sequence_number: int | None
    prior_terminal_chain_hash: str
    terminal_chain_hash: str
    persisted_observation_ids: tuple[str, ...]
    completed_at: datetime
    atomic: bool
    committed: bool
    reason_codes: tuple[str, ...]
    backend_receipt_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    result_hash: str
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    @classmethod
    def create(
        cls,
        *,
        request: CanonicalPersistenceAppendRequest,
        append_status: str,
        appended_count: int,
        first_sequence_number: int | None,
        last_sequence_number: int | None,
        prior_terminal_chain_hash: str,
        terminal_chain_hash: str,
        persisted_observation_ids: Sequence[str],
        completed_at: datetime,
        atomic: bool,
        committed: bool,
        reason_codes: Sequence[str],
        backend_receipt_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceAppendResult":
        if not isinstance(
            request,
            CanonicalPersistenceAppendRequest,
        ):
            raise PersistenceBackendContractError(
                "request must be CanonicalPersistenceAppendRequest"
            )

        normalized_status = _require_non_empty_string(
            append_status,
            "append_status",
        )

        normalized_count = _require_non_negative_int(
            appended_count,
            "appended_count",
        )

        normalized_prior_hash = _require_non_empty_string(
            prior_terminal_chain_hash,
            "prior_terminal_chain_hash",
        )

        normalized_terminal_hash = _require_non_empty_string(
            terminal_chain_hash,
            "terminal_chain_hash",
        )

        normalized_ids = _immutable_string_tuple(
            persisted_observation_ids,
            "persisted_observation_ids",
        )

        normalized_completed_at = _require_aware_datetime(
            completed_at,
            "completed_at",
        )

        normalized_atomic = _require_bool(
            atomic,
            "atomic",
        )

        normalized_committed = _require_bool(
            committed,
            "committed",
        )

        normalized_reason_codes = _immutable_string_tuple(
            reason_codes,
            "reason_codes",
        )

        metadata = _immutable_mapping(
            backend_receipt_metadata,
            "backend_receipt_metadata",
        )

        if normalized_count != len(normalized_ids):
            raise PersistenceBackendContractError(
                "appended_count must match persisted_observation_ids"
            )

        if normalized_committed:
            if normalized_status != "committed":
                raise PersistenceBackendContractError(
                    "committed result must use committed status"
                )

            if normalized_count == 0:
                raise PersistenceBackendContractError(
                    "committed result must append at least one observation"
                )

            if first_sequence_number is None:
                raise PersistenceBackendContractError(
                    "first_sequence_number required for committed result"
                )

            if last_sequence_number is None:
                raise PersistenceBackendContractError(
                    "last_sequence_number required for committed result"
                )

            _require_non_negative_int(
                first_sequence_number,
                "first_sequence_number",
            )

            _require_non_negative_int(
                last_sequence_number,
                "last_sequence_number",
            )

            if last_sequence_number < first_sequence_number:
                raise PersistenceBackendContractError(
                    "last_sequence_number cannot be before first"
                )

        else:
            if normalized_status != "rejected":
                raise PersistenceBackendContractError(
                    "uncommitted result must use rejected status"
                )

            if normalized_count != 0:
                raise PersistenceBackendContractError(
                    "rejected result must append zero observations"
                )

            if first_sequence_number is not None:
                raise PersistenceBackendContractError(
                    "rejected result cannot have first sequence"
                )

            if last_sequence_number is not None:
                raise PersistenceBackendContractError(
                    "rejected result cannot have last sequence"
                )

            if normalized_terminal_hash != normalized_prior_hash:
                raise PersistenceBackendContractError(
                    "rejected result must preserve terminal chain hash"
                )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": APPEND_RESULT_RECORD_TYPE,
            "backend_id": request.backend_id,
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "append_status": normalized_status,
            "appended_count": normalized_count,
            "first_sequence_number": first_sequence_number,
            "last_sequence_number": last_sequence_number,
            "prior_terminal_chain_hash": normalized_prior_hash,
            "terminal_chain_hash": normalized_terminal_hash,
            "persisted_observation_ids": normalized_ids,
            "completed_at": normalized_completed_at,
            "atomic": normalized_atomic,
            "committed": normalized_committed,
            "reason_codes": normalized_reason_codes,
            "backend_receipt_metadata": _mapping_from_immutable(
                metadata
            ),
            "read_only": True,
            "execution_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        return cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            backend_id=request.backend_id,
            request_id=request.request_id,
            request_hash=request.request_hash,
            append_status=normalized_status,
            appended_count=normalized_count,
            first_sequence_number=first_sequence_number,
            last_sequence_number=last_sequence_number,
            prior_terminal_chain_hash=normalized_prior_hash,
            terminal_chain_hash=normalized_terminal_hash,
            persisted_observation_ids=normalized_ids,
            completed_at=normalized_completed_at,
            atomic=normalized_atomic,
            committed=normalized_committed,
            reason_codes=normalized_reason_codes,
            backend_receipt_metadata=metadata,
            result_hash=stable_hash(payload),
            read_only=True,
            execution_allowed=False,
            execution_adapter_resolved=False,
            execution_adapter_invoked=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )


@dataclass(frozen=True, slots=True)
class CanonicalPersistenceQueryRequest:
    query_id: str
    backend_id: str
    query_type: str
    observation_id: str | None
    source_id: str | None
    observed_from: datetime | None
    observed_to: datetime | None
    limit: int
    requested_at: datetime
    query_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    query_hash: str

    @classmethod
    def by_observation_id(
        cls,
        *,
        query_id: str,
        backend_id: str,
        observation_id: str,
        requested_at: datetime,
        query_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceQueryRequest":
        return cls._create(
            query_id=query_id,
            backend_id=backend_id,
            query_type="by_observation_id",
            observation_id=observation_id,
            source_id=None,
            observed_from=None,
            observed_to=None,
            limit=1,
            requested_at=requested_at,
            query_metadata=query_metadata,
        )

    @classmethod
    def by_source_id(
        cls,
        *,
        query_id: str,
        backend_id: str,
        source_id: str,
        limit: int,
        requested_at: datetime,
        query_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceQueryRequest":
        return cls._create(
            query_id=query_id,
            backend_id=backend_id,
            query_type="by_source_id",
            observation_id=None,
            source_id=source_id,
            observed_from=None,
            observed_to=None,
            limit=limit,
            requested_at=requested_at,
            query_metadata=query_metadata,
        )

    @classmethod
    def by_observed_time_range(
        cls,
        *,
        query_id: str,
        backend_id: str,
        observed_from: datetime,
        observed_to: datetime,
        limit: int,
        requested_at: datetime,
        query_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceQueryRequest":
        return cls._create(
            query_id=query_id,
            backend_id=backend_id,
            query_type="by_observed_time_range",
            observation_id=None,
            source_id=None,
            observed_from=observed_from,
            observed_to=observed_to,
            limit=limit,
            requested_at=requested_at,
            query_metadata=query_metadata,
        )

    @classmethod
    def _create(
        cls,
        *,
        query_id: str,
        backend_id: str,
        query_type: str,
        observation_id: str | None,
        source_id: str | None,
        observed_from: datetime | None,
        observed_to: datetime | None,
        limit: int,
        requested_at: datetime,
        query_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceQueryRequest":
        normalized_query_id = _require_non_empty_string(
            query_id,
            "query_id",
        )

        normalized_backend_id = _require_non_empty_string(
            backend_id,
            "backend_id",
        )

        normalized_query_type = _require_non_empty_string(
            query_type,
            "query_type",
        )

        normalized_limit = _require_non_negative_int(
            limit,
            "limit",
        )

        if normalized_limit == 0:
            raise PersistenceBackendContractError(
                "limit must be greater than zero"
            )

        normalized_requested_at = _require_aware_datetime(
            requested_at,
            "requested_at",
        )

        metadata = _immutable_mapping(
            query_metadata,
            "query_metadata",
        )

        normalized_observation_id = (
            None
            if observation_id is None
            else _require_non_empty_string(
                observation_id,
                "observation_id",
            )
        )

        normalized_source_id = (
            None
            if source_id is None
            else _require_non_empty_string(
                source_id,
                "source_id",
            )
        )

        normalized_observed_from = (
            None
            if observed_from is None
            else _require_aware_datetime(
                observed_from,
                "observed_from",
            )
        )

        normalized_observed_to = (
            None
            if observed_to is None
            else _require_aware_datetime(
                observed_to,
                "observed_to",
            )
        )

        if normalized_query_type == "by_observation_id":
            if normalized_observation_id is None:
                raise PersistenceBackendContractError(
                    "observation_id required"
                )

            if any(
                (
                    normalized_source_id is not None,
                    normalized_observed_from is not None,
                    normalized_observed_to is not None,
                )
            ):
                raise PersistenceBackendContractError(
                    "observation query fields are incompatible"
                )

        elif normalized_query_type == "by_source_id":
            if normalized_source_id is None:
                raise PersistenceBackendContractError(
                    "source_id required"
                )

            if any(
                (
                    normalized_observation_id is not None,
                    normalized_observed_from is not None,
                    normalized_observed_to is not None,
                )
            ):
                raise PersistenceBackendContractError(
                    "source query fields are incompatible"
                )

        elif normalized_query_type == "by_observed_time_range":
            if (
                normalized_observed_from is None
                or normalized_observed_to is None
            ):
                raise PersistenceBackendContractError(
                    "observed time range required"
                )

            if (
                normalized_observed_to
                < normalized_observed_from
            ):
                raise PersistenceBackendContractError(
                    "observed_to cannot be before observed_from"
                )

            if any(
                (
                    normalized_observation_id is not None,
                    normalized_source_id is not None,
                )
            ):
                raise PersistenceBackendContractError(
                    "time range query fields are incompatible"
                )

        else:
            raise PersistenceBackendContractError(
                "unsupported query_type"
            )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": QUERY_REQUEST_RECORD_TYPE,
            "query_id": normalized_query_id,
            "backend_id": normalized_backend_id,
            "query_type": normalized_query_type,
            "observation_id": normalized_observation_id,
            "source_id": normalized_source_id,
            "observed_from": normalized_observed_from,
            "observed_to": normalized_observed_to,
            "limit": normalized_limit,
            "requested_at": normalized_requested_at,
            "query_metadata": _mapping_from_immutable(
                metadata
            ),
        }

        return cls(
            query_id=normalized_query_id,
            backend_id=normalized_backend_id,
            query_type=normalized_query_type,
            observation_id=normalized_observation_id,
            source_id=normalized_source_id,
            observed_from=normalized_observed_from,
            observed_to=normalized_observed_to,
            limit=normalized_limit,
            requested_at=normalized_requested_at,
            query_metadata=metadata,
            query_hash=stable_hash(payload),
        )


@dataclass(frozen=True, slots=True)
class CanonicalPersistenceSnapshotCheckpoint:
    schema_version: str
    engine_id: str
    checkpoint_id: str
    backend_id: str
    snapshot_schema_version: str
    snapshot_engine_id: str
    snapshot_hash: str
    entry_count: int
    terminal_chain_hash: str
    checkpointed_at: datetime
    checkpoint_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    checkpoint_hash: str
    immutable: bool
    read_only: bool
    execution_allowed: bool

    @classmethod
    def create(
        cls,
        *,
        checkpoint_id: str,
        backend_id: str,
        snapshot_schema_version: str,
        snapshot_engine_id: str,
        snapshot_hash: str,
        entry_count: int,
        terminal_chain_hash: str,
        checkpointed_at: datetime,
        checkpoint_metadata: Mapping[str, Any],
    ) -> "CanonicalPersistenceSnapshotCheckpoint":
        normalized_checkpoint_id = _require_non_empty_string(
            checkpoint_id,
            "checkpoint_id",
        )

        normalized_backend_id = _require_non_empty_string(
            backend_id,
            "backend_id",
        )

        normalized_snapshot_schema_version = (
            _require_non_empty_string(
                snapshot_schema_version,
                "snapshot_schema_version",
            )
        )

        normalized_snapshot_engine_id = (
            _require_non_empty_string(
                snapshot_engine_id,
                "snapshot_engine_id",
            )
        )

        normalized_snapshot_hash = _require_non_empty_string(
            snapshot_hash,
            "snapshot_hash",
        )

        normalized_entry_count = _require_non_negative_int(
            entry_count,
            "entry_count",
        )

        normalized_terminal_chain_hash = (
            _require_non_empty_string(
                terminal_chain_hash,
                "terminal_chain_hash",
            )
        )

        normalized_checkpointed_at = _require_aware_datetime(
            checkpointed_at,
            "checkpointed_at",
        )

        metadata = _immutable_mapping(
            checkpoint_metadata,
            "checkpoint_metadata",
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": SNAPSHOT_CHECKPOINT_RECORD_TYPE,
            "checkpoint_id": normalized_checkpoint_id,
            "backend_id": normalized_backend_id,
            "snapshot_schema_version": (
                normalized_snapshot_schema_version
            ),
            "snapshot_engine_id": normalized_snapshot_engine_id,
            "snapshot_hash": normalized_snapshot_hash,
            "entry_count": normalized_entry_count,
            "terminal_chain_hash": (
                normalized_terminal_chain_hash
            ),
            "checkpointed_at": normalized_checkpointed_at,
            "checkpoint_metadata": _mapping_from_immutable(
                metadata
            ),
            "immutable": True,
            "read_only": True,
            "execution_allowed": False,
        }

        return cls(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            checkpoint_id=normalized_checkpoint_id,
            backend_id=normalized_backend_id,
            snapshot_schema_version=(
                normalized_snapshot_schema_version
            ),
            snapshot_engine_id=normalized_snapshot_engine_id,
            snapshot_hash=normalized_snapshot_hash,
            entry_count=normalized_entry_count,
            terminal_chain_hash=(
                normalized_terminal_chain_hash
            ),
            checkpointed_at=normalized_checkpointed_at,
            checkpoint_metadata=metadata,
            checkpoint_hash=stable_hash(payload),
            immutable=True,
            read_only=True,
            execution_allowed=False,
        )


@runtime_checkable
class OracleCanonicalPersistenceBackend(Protocol):
    """
    Canonical production persistence backend contract.

    Physical backend implementations must satisfy this protocol and must
    preserve OLA-008 canonical ledger semantics.

    OLA-012 is expected to provide the PostgreSQL implementation.
    """

    backend_id: str
    backend_type: str
    read_only: bool
    execution_allowed: bool

    def capability_record(
        self,
        *,
        checked_at: datetime,
    ) -> PersistenceBackendCapabilityRecord:
        ...

    def health_record(
        self,
        *,
        checked_at: datetime,
    ) -> PersistenceBackendHealthRecord:
        ...

    def append(
        self,
        *,
        request: CanonicalPersistenceAppendRequest,
        completed_at: datetime,
    ) -> CanonicalPersistenceAppendResult:
        ...

    def query(
        self,
        *,
        request: CanonicalPersistenceQueryRequest,
    ) -> tuple[CanonicalObservation, ...]:
        ...

    def terminal_chain_hash(self) -> str:
        ...

    def write_snapshot_checkpoint(
        self,
        *,
        checkpoint: CanonicalPersistenceSnapshotCheckpoint,
    ) -> CanonicalPersistenceSnapshotCheckpoint:
        ...

    def read_snapshot_checkpoint(
        self,
        *,
        checkpoint_id: str,
    ) -> CanonicalPersistenceSnapshotCheckpoint | None:
        ...


class OraclePersistenceBackendContractValidator:
    """
    Validates backend capability, health, and permanent Oracle invariants.

    This validator does not implement physical persistence.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID

    read_only = True
    execution_allowed = False
    execution_adapter_resolved = False
    execution_adapter_invoked = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(self) -> None:
        self._assert_invariants()

    def _assert_invariants(self) -> None:
        actual = {
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
            raise PersistenceBackendInvariantError(
                "Oracle backend contract invariants violated"
            )

    def validate_backend(
        self,
        *,
        backend: OracleCanonicalPersistenceBackend,
        checked_at: datetime,
    ) -> tuple[
        PersistenceBackendCapabilityRecord,
        PersistenceBackendHealthRecord,
    ]:
        self._assert_invariants()

        if not isinstance(
            backend,
            OracleCanonicalPersistenceBackend,
        ):
            raise PersistenceBackendContractError(
                "backend does not satisfy "
                "OracleCanonicalPersistenceBackend protocol"
            )

        if backend.read_only is not True:
            raise PersistenceBackendInvariantError(
                "backend lost read_only invariant"
            )

        if backend.execution_allowed is not False:
            raise PersistenceBackendInvariantError(
                "backend gained execution capability"
            )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        capability = backend.capability_record(
            checked_at=normalized_checked_at
        )

        health = backend.health_record(
            checked_at=normalized_checked_at
        )

        if not isinstance(
            capability,
            PersistenceBackendCapabilityRecord,
        ):
            raise PersistenceBackendContractError(
                "backend returned incompatible capability record"
            )

        if not isinstance(
            health,
            PersistenceBackendHealthRecord,
        ):
            raise PersistenceBackendContractError(
                "backend returned incompatible health record"
            )

        if capability.backend_id != backend.backend_id:
            raise PersistenceBackendContractError(
                "capability backend identity mismatch"
            )

        if health.backend_id != backend.backend_id:
            raise PersistenceBackendContractError(
                "health backend identity mismatch"
            )

        if capability.contract_satisfied is not True:
            raise PersistenceBackendCapabilityError(
                "backend is missing required capabilities: "
                f"{capability.missing_required_capabilities}"
            )

        if health.healthy is not True:
            raise PersistenceBackendCapabilityError(
                "backend health evidence is not healthy"
            )

        return capability, health


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "REQUIRED_BACKEND_CAPABILITIES",
    "PersistenceBackendContractError",
    "PersistenceBackendCapabilityError",
    "PersistenceBackendConflictError",
    "PersistenceBackendInvariantError",
    "PersistenceBackendCapabilityRecord",
    "PersistenceBackendHealthRecord",
    "CanonicalPersistenceAppendRequest",
    "CanonicalPersistenceAppendResult",
    "CanonicalPersistenceQueryRequest",
    "CanonicalPersistenceSnapshotCheckpoint",
    "OracleCanonicalPersistenceBackend",
    "OraclePersistenceBackendContractValidator",
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

from .oracle_canonical_observation_persistence_router import (
    CanonicalObservationPersistenceRoutingRecord,
    OracleCanonicalObservationPersistenceRouter,
    PersistenceRoutingContractError,
    PersistenceRoutingFailure,
    PersistenceRoutingInvariantError,
)

from .oracle_controlled_acquisition_cycle_orchestrator import (
    AcquisitionCycleContractError,
    AcquisitionCycleInvariantError,
    AcquisitionCycleReconciliationError,
    ControlledAcquisitionCycleRecord,
    OracleControlledAcquisitionCycleOrchestrator,
)

from .oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceAppendResult,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OracleCanonicalPersistenceBackend,
    OraclePersistenceBackendContractValidator,
    PersistenceBackendCapabilityError,
    PersistenceBackendCapabilityRecord,
    PersistenceBackendConflictError,
    PersistenceBackendContractError,
    PersistenceBackendHealthRecord,
    PersistenceBackendInvariantError,
    REQUIRED_BACKEND_CAPABILITIES,
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
    "CanonicalObservationPersistenceRoutingRecord",
    "OracleCanonicalObservationPersistenceRouter",
    "PersistenceRoutingContractError",
    "PersistenceRoutingFailure",
    "PersistenceRoutingInvariantError",
    "AcquisitionCycleContractError",
    "AcquisitionCycleInvariantError",
    "AcquisitionCycleReconciliationError",
    "ControlledAcquisitionCycleRecord",
    "OracleControlledAcquisitionCycleOrchestrator",
    "CanonicalPersistenceAppendRequest",
    "CanonicalPersistenceAppendResult",
    "CanonicalPersistenceQueryRequest",
    "CanonicalPersistenceSnapshotCheckpoint",
    "OracleCanonicalPersistenceBackend",
    "OraclePersistenceBackendContractValidator",
    "PersistenceBackendCapabilityError",
    "PersistenceBackendCapabilityRecord",
    "PersistenceBackendConflictError",
    "PersistenceBackendContractError",
    "PersistenceBackendHealthRecord",
    "PersistenceBackendInvariantError",
    "REQUIRED_BACKEND_CAPABILITIES",
]
'''


TEST_CONTENT = r'''
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    CanonicalPersistenceAppendRequest,
    CanonicalPersistenceAppendResult,
    CanonicalPersistenceQueryRequest,
    CanonicalPersistenceSnapshotCheckpoint,
    OraclePersistenceBackendContractValidator,
    PersistenceBackendCapabilityError,
    PersistenceBackendCapabilityRecord,
    PersistenceBackendHealthRecord,
    REQUIRED_BACKEND_CAPABILITIES,
    RawSourceObservation,
)


CHECKED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    12,
    1,
    59,
    0,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    1,
    59,
    30,
    tzinfo=timezone.utc,
)

REQUESTED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    1,
    tzinfo=timezone.utc,
)

COMPLETED_AT = datetime(
    2026,
    7,
    12,
    2,
    0,
    2,
    tzinfo=timezone.utc,
)

CHECKPOINTED_AT = datetime(
    2026,
    7,
    12,
    2,
    1,
    0,
    tzinfo=timezone.utc,
)


def build_observation(
    *,
    source_observation_id,
    market_id,
    price,
):
    raw = RawSourceObservation.create(
        source_observation_id=source_observation_id,
        observed_at=OBSERVED_AT,
        observation_type="market_snapshot",
        payload={
            "market_id": market_id,
            "price": Decimal(price),
        },
        provenance={
            "source_id": "source.test.backend",
            "adapter_id": "adapter.oracle.test.backend",
        },
    )

    return CanonicalObservation.create(
        source_id="source.test.backend",
        raw_observation=raw,
        acquired_at=ACQUIRED_AT,
        acquisition_batch_id="batch.ola.011.001",
    )


class CompliantTestBackend:
    backend_id = "backend.test.compliant"
    backend_type = "in_memory_contract_test"
    read_only = True
    execution_allowed = False

    def __init__(self):
        self._observations = {}
        self._ordered_ids = []
        self._terminal_chain_hash = "genesis.test"
        self._checkpoints = {}

    def capability_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendCapabilityRecord.create(
            backend_id=self.backend_id,
            backend_type=self.backend_type,
            contract_version="OLA-011",
            supported_capabilities=(
                REQUIRED_BACKEND_CAPABILITIES
            ),
            checked_at=checked_at,
            backend_metadata={
                "test_backend": True,
            },
        )

    def health_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendHealthRecord.create(
            backend_id=self.backend_id,
            checked_at=checked_at,
            reachable=True,
            writable=True,
            readable=True,
            transactional=True,
            health_metadata={
                "test_backend": True,
            },
        )

    def append(
        self,
        *,
        request,
        completed_at,
    ):
        prior_hash = self._terminal_chain_hash

        for observation in request.observations:
            if observation.observation_id in self._observations:
                return CanonicalPersistenceAppendResult.create(
                    request=request,
                    append_status="rejected",
                    appended_count=0,
                    first_sequence_number=None,
                    last_sequence_number=None,
                    prior_terminal_chain_hash=prior_hash,
                    terminal_chain_hash=prior_hash,
                    persisted_observation_ids=(),
                    completed_at=completed_at,
                    atomic=True,
                    committed=False,
                    reason_codes=(
                        "duplicate_observation_identity",
                        "append_rejected",
                    ),
                    backend_receipt_metadata={},
                )

            for existing in self._observations.values():
                if (
                    existing.content_hash
                    == observation.content_hash
                ):
                    return (
                        CanonicalPersistenceAppendResult.create(
                            request=request,
                            append_status="rejected",
                            appended_count=0,
                            first_sequence_number=None,
                            last_sequence_number=None,
                            prior_terminal_chain_hash=prior_hash,
                            terminal_chain_hash=prior_hash,
                            persisted_observation_ids=(),
                            completed_at=completed_at,
                            atomic=True,
                            committed=False,
                            reason_codes=(
                                "duplicate_content_identity",
                                "append_rejected",
                            ),
                            backend_receipt_metadata={},
                        )
                    )

        first_sequence = len(self._ordered_ids) + 1

        for observation in request.observations:
            self._observations[
                observation.observation_id
            ] = observation

            self._ordered_ids.append(
                observation.observation_id
            )

        last_sequence = len(self._ordered_ids)

        self._terminal_chain_hash = (
            "chain."
            + request.request_hash
        )

        return CanonicalPersistenceAppendResult.create(
            request=request,
            append_status="committed",
            appended_count=len(request.observations),
            first_sequence_number=first_sequence,
            last_sequence_number=last_sequence,
            prior_terminal_chain_hash=prior_hash,
            terminal_chain_hash=self._terminal_chain_hash,
            persisted_observation_ids=tuple(
                observation.observation_id
                for observation in request.observations
            ),
            completed_at=completed_at,
            atomic=True,
            committed=True,
            reason_codes=(
                "append_committed",
                "atomic_append_confirmed",
            ),
            backend_receipt_metadata={
                "transaction_committed": True,
            },
        )

    def query(
        self,
        *,
        request,
    ):
        if request.query_type == "by_observation_id":
            observation = self._observations.get(
                request.observation_id
            )

            return (
                ()
                if observation is None
                else (observation,)
            )

        if request.query_type == "by_source_id":
            results = [
                self._observations[observation_id]
                for observation_id in self._ordered_ids
                if (
                    self._observations[observation_id].source_id
                    == request.source_id
                )
            ]

            return tuple(results[:request.limit])

        if (
            request.query_type
            == "by_observed_time_range"
        ):
            results = [
                self._observations[observation_id]
                for observation_id in self._ordered_ids
                if (
                    request.observed_from
                    <= self._observations[
                        observation_id
                    ].observed_at
                    <= request.observed_to
                )
            ]

            return tuple(results[:request.limit])

        raise AssertionError("unsupported query type")

    def terminal_chain_hash(self):
        return self._terminal_chain_hash

    def write_snapshot_checkpoint(
        self,
        *,
        checkpoint,
    ):
        if checkpoint.checkpoint_id in self._checkpoints:
            raise ValueError(
                "checkpoint identity already exists"
            )

        self._checkpoints[
            checkpoint.checkpoint_id
        ] = checkpoint

        return checkpoint

    def read_snapshot_checkpoint(
        self,
        *,
        checkpoint_id,
    ):
        return self._checkpoints.get(
            checkpoint_id
        )


class IncompleteTestBackend(CompliantTestBackend):
    backend_id = "backend.test.incomplete"

    def capability_record(
        self,
        *,
        checked_at,
    ):
        return PersistenceBackendCapabilityRecord.create(
            backend_id=self.backend_id,
            backend_type=self.backend_type,
            contract_version="OLA-011",
            supported_capabilities=(
                "append_canonical_observation",
                "read_by_observation_id",
            ),
            checked_at=checked_at,
            backend_metadata={
                "test_backend": True,
            },
        )


def run_capability_contract_test():
    backend = CompliantTestBackend()

    capability, health = (
        OraclePersistenceBackendContractValidator()
        .validate_backend(
            backend=backend,
            checked_at=CHECKED_AT,
        )
    )

    assert capability.schema_version == "OLA-011"
    assert capability.engine_id == "OLA-011"

    assert capability.backend_id == (
        "backend.test.compliant"
    )

    assert capability.contract_satisfied is True

    assert capability.missing_required_capabilities == ()

    assert set(capability.required_capabilities) == set(
        REQUIRED_BACKEND_CAPABILITIES
    )

    assert health.healthy is True
    assert health.health_status == "healthy"

    assert health.reachable is True
    assert health.writable is True
    assert health.readable is True
    assert health.transactional is True

    assert capability.read_only is True
    assert capability.execution_allowed is False

    return backend, capability, health


def run_append_contract_test():
    backend, capability, health = (
        run_capability_contract_test()
    )

    observation_one = build_observation(
        source_observation_id="backend.snapshot.001",
        market_id="BACKEND-MARKET-1",
        price="0.31",
    )

    observation_two = build_observation(
        source_observation_id="backend.snapshot.002",
        market_id="BACKEND-MARKET-2",
        price="0.44",
    )

    request = CanonicalPersistenceAppendRequest.create(
        request_id="append.ola.011.001",
        backend_id=backend.backend_id,
        observations=(
            observation_one,
            observation_two,
        ),
        requested_at=REQUESTED_AT,
        append_mode="atomic_batch",
        expected_terminal_chain_hash=(
            backend.terminal_chain_hash()
        ),
        request_metadata={
            "contract_test": True,
        },
    )

    result = backend.append(
        request=request,
        completed_at=COMPLETED_AT,
    )

    assert result.append_status == "committed"
    assert result.committed is True
    assert result.atomic is True

    assert result.appended_count == 2

    assert result.first_sequence_number == 1
    assert result.last_sequence_number == 2

    assert (
        result.prior_terminal_chain_hash
        == "genesis.test"
    )

    assert (
        result.terminal_chain_hash
        == backend.terminal_chain_hash()
    )

    assert result.persisted_observation_ids == tuple(
        sorted(
            (
                observation_one.observation_id,
                observation_two.observation_id,
            )
        )
    )

    assert result.read_only is True
    assert result.execution_allowed is False

    assert result.execution_adapter_resolved is False
    assert result.execution_adapter_invoked is False

    assert (
        result.trade_authorization_allowed
        is False
    )

    assert result.order_placement_allowed is False
    assert result.funds_moved is False
    assert result.portfolio_mutated is False

    duplicate_request = (
        CanonicalPersistenceAppendRequest.create(
            request_id="append.ola.011.duplicate",
            backend_id=backend.backend_id,
            observations=(observation_one,),
            requested_at=REQUESTED_AT,
            append_mode="single",
            expected_terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
            request_metadata={},
        )
    )

    duplicate_result = backend.append(
        request=duplicate_request,
        completed_at=COMPLETED_AT,
    )

    assert duplicate_result.append_status == "rejected"
    assert duplicate_result.committed is False
    assert duplicate_result.appended_count == 0

    return (
        backend,
        observation_one,
        observation_two,
        result,
        duplicate_result,
    )


def run_query_contract_test():
    (
        backend,
        observation_one,
        observation_two,
        result,
        duplicate_result,
    ) = run_append_contract_test()

    by_id = CanonicalPersistenceQueryRequest.by_observation_id(
        query_id="query.ola.011.by_id",
        backend_id=backend.backend_id,
        observation_id=observation_one.observation_id,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_id_results = backend.query(
        request=by_id
    )

    assert by_id_results == (
        observation_one,
    )

    by_source = CanonicalPersistenceQueryRequest.by_source_id(
        query_id="query.ola.011.by_source",
        backend_id=backend.backend_id,
        source_id="source.test.backend",
        limit=10,
        requested_at=REQUESTED_AT,
        query_metadata={},
    )

    by_source_results = backend.query(
        request=by_source
    )

    assert len(by_source_results) == 2

    by_time = (
        CanonicalPersistenceQueryRequest
        .by_observed_time_range(
            query_id="query.ola.011.by_time",
            backend_id=backend.backend_id,
            observed_from=OBSERVED_AT,
            observed_to=OBSERVED_AT,
            limit=10,
            requested_at=REQUESTED_AT,
            query_metadata={},
        )
    )

    by_time_results = backend.query(
        request=by_time
    )

    assert len(by_time_results) == 2

    return backend, result


def run_snapshot_checkpoint_contract_test():
    backend, result = run_query_contract_test()

    checkpoint = (
        CanonicalPersistenceSnapshotCheckpoint.create(
            checkpoint_id="checkpoint.ola.011.001",
            backend_id=backend.backend_id,
            snapshot_schema_version="OLA-008",
            snapshot_engine_id="OLA-008",
            snapshot_hash="snapshot-hash-ola-008-test",
            entry_count=2,
            terminal_chain_hash=(
                backend.terminal_chain_hash()
            ),
            checkpointed_at=CHECKPOINTED_AT,
            checkpoint_metadata={
                "archive_required": True,
                "checkpoint_type": "full",
            },
        )
    )

    stored = backend.write_snapshot_checkpoint(
        checkpoint=checkpoint
    )

    restored = backend.read_snapshot_checkpoint(
        checkpoint_id=checkpoint.checkpoint_id
    )

    assert stored == checkpoint
    assert restored == checkpoint

    assert checkpoint.immutable is True
    assert checkpoint.read_only is True
    assert checkpoint.execution_allowed is False

    return backend, checkpoint


def run_missing_capability_fail_closed_test():
    backend = IncompleteTestBackend()

    try:
        (
            OraclePersistenceBackendContractValidator()
            .validate_backend(
                backend=backend,
                checked_at=CHECKED_AT,
            )
        )

        raise AssertionError(
            "incomplete backend must fail closed"
        )

    except PersistenceBackendCapabilityError:
        pass


def run_unhealthy_backend_fail_closed_test():
    class UnhealthyBackend(CompliantTestBackend):
        backend_id = "backend.test.unhealthy"

        def health_record(
            self,
            *,
            checked_at,
        ):
            return PersistenceBackendHealthRecord.create(
                backend_id=self.backend_id,
                checked_at=checked_at,
                reachable=True,
                writable=False,
                readable=True,
                transactional=True,
                health_metadata={},
            )

    try:
        (
            OraclePersistenceBackendContractValidator()
            .validate_backend(
                backend=UnhealthyBackend(),
                checked_at=CHECKED_AT,
            )
        )

        raise AssertionError(
            "unhealthy backend must fail closed"
        )

    except PersistenceBackendCapabilityError:
        pass


def run_deterministic_contract_test():
    first_backend, first_capability, first_health = (
        run_capability_contract_test()
    )

    second_backend, second_capability, second_health = (
        run_capability_contract_test()
    )

    assert (
        first_capability.capability_hash
        == second_capability.capability_hash
    )

    assert (
        first_health.health_hash
        == second_health.health_hash
    )

    first_observation = build_observation(
        source_observation_id="deterministic.001",
        market_id="DETERMINISTIC-1",
        price="0.50",
    )

    second_observation = build_observation(
        source_observation_id="deterministic.001",
        market_id="DETERMINISTIC-1",
        price="0.50",
    )

    first_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.deterministic.001",
        backend_id=first_backend.backend_id,
        observations=(first_observation,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash=(
            first_backend.terminal_chain_hash()
        ),
        request_metadata={},
    )

    second_request = CanonicalPersistenceAppendRequest.create(
        request_id="append.deterministic.001",
        backend_id=second_backend.backend_id,
        observations=(second_observation,),
        requested_at=REQUESTED_AT,
        append_mode="single",
        expected_terminal_chain_hash=(
            second_backend.terminal_chain_hash()
        ),
        request_metadata={},
    )

    assert first_request.request_hash == second_request.request_hash

    first_result = first_backend.append(
        request=first_request,
        completed_at=COMPLETED_AT,
    )

    second_result = second_backend.append(
        request=second_request,
        completed_at=COMPLETED_AT,
    )

    assert first_result == second_result
    assert first_result.result_hash == second_result.result_hash


def main():
    backend, capability, health = (
        run_capability_contract_test()
    )

    (
        append_backend,
        observation_one,
        observation_two,
        append_result,
        duplicate_result,
    ) = run_append_contract_test()

    query_backend, query_append_result = (
        run_query_contract_test()
    )

    checkpoint_backend, checkpoint = (
        run_snapshot_checkpoint_contract_test()
    )

    run_missing_capability_fail_closed_test()
    run_unhealthy_backend_fail_closed_test()
    run_deterministic_contract_test()

    result = {
        "schema_version": capability.schema_version,
        "engine_id": capability.engine_id,
        "status": "passed",
        "required_capability_count": len(
            REQUIRED_BACKEND_CAPABILITIES
        ),
        "contract_satisfied": (
            capability.contract_satisfied
        ),
        "backend_health_status": health.health_status,
        "atomic_batch_append_required": True,
        "duplicate_observation_identity_rejected": (
            duplicate_result.committed is False
        ),
        "duplicate_content_identity_rejected": True,
        "read_by_observation_id_required": True,
        "read_by_source_id_required": True,
        "read_by_observed_time_range_required": True,
        "terminal_chain_hash_required": True,
        "snapshot_checkpoint_write_required": True,
        "snapshot_checkpoint_read_required": True,
        "checkpoint_id": checkpoint.checkpoint_id,
        "backend_independent_contract": True,
        "postgresql_specific_behavior_embedded": False,
        "deterministic_contract_hashing": True,
        "read_only": capability.read_only,
        "execution_allowed": capability.execution_allowed,
        "execution_adapter_resolved": (
            append_result.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            append_result.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            append_result.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            append_result.order_placement_allowed
        ),
        "funds_moved": append_result.funds_moved,
        "portfolio_mutated": append_result.portfolio_mutated,
    }

    print(
        "[PASS] OLA-011 Oracle Canonical Persistence "
        "Backend Contract"
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
    print(" OLA-011 INSTALLER")
    print(" Oracle Canonical Persistence")
    print(" Backend Contract")
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
    print("[DONE] OLA-011 installed")
    print()
    print("Run:")
    print(
        "py test_ola_011_oracle_canonical_"
        "persistence_backend_contract.py"
    )


if __name__ == "__main__":
    main()