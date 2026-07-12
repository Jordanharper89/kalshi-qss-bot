"""
OLA-001
Oracle Live Read-Only Acquisition Runtime

Controlled orchestration boundary between approved Oracle source adapters
and canonical Oracle observation routing.

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
PERSISTENCE

Oracle is permanently read-only.

This runtime may:
- invoke approved read-only source adapters,
- collect source observations,
- normalize observation envelopes,
- generate deterministic identities and hashes,
- record deduplication evidence,
- preserve source health and rate-control evidence,
- route canonical observations through an approved read-only router,
- produce immutable replayable acquisition evidence.

This runtime may not:
- authorize trades,
- place orders,
- invoke execution adapters,
- move funds,
- mutate portfolios.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import math
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Protocol,
    Sequence,
)


SCHEMA_VERSION = "OLA-001"
ENGINE_ID = "OLA-001"


class AcquisitionContractError(ValueError):
    """Raised when acquisition contract data is malformed or incompatible."""


class UnapprovedSourceAdapterError(AcquisitionContractError):
    """Raised when a source adapter is not explicitly approved."""


class AcquisitionInvariantError(RuntimeError):
    """Raised when a permanent Oracle acquisition invariant is violated."""


class SourceAdapterFailure(RuntimeError):
    """Raised when an approved source adapter fails closed."""


class CanonicalObservationRouterFailure(RuntimeError):
    """Raised when canonical observation routing fails closed."""


JSONScalar = None | bool | int | float | str
JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise AcquisitionContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise AcquisitionContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AcquisitionContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AcquisitionContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(value: Any) -> JSONValue:
    """
    Convert supported contract values into deterministic JSON-safe values.

    repr() is intentionally never used for contract hashing.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise AcquisitionContractError(
                "non-finite float values are not canonical"
            )

        return json.loads(
            json.dumps(
                value,
                allow_nan=False,
            )
        )

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise AcquisitionContractError(
                "non-finite Decimal values are not canonical"
            )

        return format(value, "f")

    if isinstance(value, datetime):
        normalized = _require_aware_datetime(
            value,
            "canonical datetime",
        )

        return normalized.isoformat()

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        canonical_mapping: dict[str, JSONValue] = {}

        for key in sorted(value.keys()):
            if not isinstance(key, str):
                raise AcquisitionContractError(
                    "canonical mapping keys must be strings"
                )

            canonical_mapping[key] = _canonicalize(value[key])

        return canonical_mapping

    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]

    raise AcquisitionContractError(
        "unsupported canonical value type: "
        f"{type(value).__name__}"
    )


def canonical_json(value: Any) -> str:
    canonical_value = _canonicalize(value)

    return json.dumps(
        canonical_value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(value: Any) -> str:
    payload = canonical_json(value).encode("utf-8")
    return sha256(payload).hexdigest()


def _immutable_mapping(
    value: Mapping[str, Any],
    field_name: str,
) -> tuple[tuple[str, JSONValue], ...]:
    if not isinstance(value, Mapping):
        raise AcquisitionContractError(
            f"{field_name} must be a mapping"
        )

    canonical_value = _canonicalize(value)

    if not isinstance(canonical_value, dict):
        raise AcquisitionContractError(
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


@dataclass(frozen=True, slots=True)
class SourceHealthEvidence:
    source_id: str
    status: str
    checked_at: datetime
    details: tuple[tuple[str, JSONValue], ...]
    evidence_hash: str

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        status: str,
        checked_at: datetime,
        details: Mapping[str, Any],
    ) -> "SourceHealthEvidence":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )
        normalized_status = _require_non_empty_string(
            status,
            "status",
        )
        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )
        immutable_details = _immutable_mapping(
            details,
            "details",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "source_health_evidence",
            "source_id": normalized_source_id,
            "status": normalized_status,
            "checked_at": normalized_checked_at,
            "details": _mapping_from_immutable(
                immutable_details
            ),
        }

        return cls(
            source_id=normalized_source_id,
            status=normalized_status,
            checked_at=normalized_checked_at,
            details=immutable_details,
            evidence_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "checked_at": self.checked_at.isoformat(),
            "details": _mapping_from_immutable(self.details),
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True, slots=True)
class RateControlEvidence:
    source_id: str
    allowed: bool
    checked_at: datetime
    policy_id: str
    details: tuple[tuple[str, JSONValue], ...]
    evidence_hash: str

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        allowed: bool,
        checked_at: datetime,
        policy_id: str,
        details: Mapping[str, Any],
    ) -> "RateControlEvidence":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )

        if not isinstance(allowed, bool):
            raise AcquisitionContractError(
                "allowed must be a bool"
            )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )
        normalized_policy_id = _require_non_empty_string(
            policy_id,
            "policy_id",
        )
        immutable_details = _immutable_mapping(
            details,
            "details",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "rate_control_evidence",
            "source_id": normalized_source_id,
            "allowed": allowed,
            "checked_at": normalized_checked_at,
            "policy_id": normalized_policy_id,
            "details": _mapping_from_immutable(
                immutable_details
            ),
        }

        return cls(
            source_id=normalized_source_id,
            allowed=allowed,
            checked_at=normalized_checked_at,
            policy_id=normalized_policy_id,
            details=immutable_details,
            evidence_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "allowed": self.allowed,
            "checked_at": self.checked_at.isoformat(),
            "policy_id": self.policy_id,
            "details": _mapping_from_immutable(self.details),
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True, slots=True)
class RawSourceObservation:
    """
    Canonical raw adapter return envelope.

    Adapter payload is normalized into immutable canonical JSON-compatible
    evidence before observation identity is generated.
    """

    source_observation_id: str
    observed_at: datetime
    observation_type: str
    payload: tuple[tuple[str, JSONValue], ...]
    provenance: tuple[tuple[str, JSONValue], ...]

    @classmethod
    def create(
        cls,
        *,
        source_observation_id: str,
        observed_at: datetime,
        observation_type: str,
        payload: Mapping[str, Any],
        provenance: Mapping[str, Any],
    ) -> "RawSourceObservation":
        return cls(
            source_observation_id=_require_non_empty_string(
                source_observation_id,
                "source_observation_id",
            ),
            observed_at=_require_aware_datetime(
                observed_at,
                "observed_at",
            ),
            observation_type=_require_non_empty_string(
                observation_type,
                "observation_type",
            ),
            payload=_immutable_mapping(
                payload,
                "payload",
            ),
            provenance=_immutable_mapping(
                provenance,
                "provenance",
            ),
        )

    def payload_dict(self) -> dict[str, JSONValue]:
        return _mapping_from_immutable(self.payload)

    def provenance_dict(self) -> dict[str, JSONValue]:
        return _mapping_from_immutable(self.provenance)


@dataclass(frozen=True, slots=True)
class CanonicalObservation:
    schema_version: str
    observation_id: str
    source_id: str
    source_observation_id: str
    observation_type: str
    observed_at: datetime
    acquired_at: datetime
    acquisition_batch_id: str
    payload: tuple[tuple[str, JSONValue], ...]
    provenance: tuple[tuple[str, JSONValue], ...]
    content_hash: str
    replay_hash: str
    read_only: bool
    execution_allowed: bool

    @classmethod
    def create(
        cls,
        *,
        source_id: str,
        raw_observation: RawSourceObservation,
        acquired_at: datetime,
        acquisition_batch_id: str,
    ) -> "CanonicalObservation":
        normalized_source_id = _require_non_empty_string(
            source_id,
            "source_id",
        )
        normalized_acquired_at = _require_aware_datetime(
            acquired_at,
            "acquired_at",
        )
        normalized_batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        content_payload = {
            "schema_version": SCHEMA_VERSION,
            "source_id": normalized_source_id,
            "source_observation_id": (
                raw_observation.source_observation_id
            ),
            "observation_type": (
                raw_observation.observation_type
            ),
            "observed_at": raw_observation.observed_at,
            "payload": raw_observation.payload_dict(),
            "provenance": raw_observation.provenance_dict(),
        }

        content_hash = stable_hash(content_payload)

        observation_id = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "canonical_observation_identity",
                "source_id": normalized_source_id,
                "source_observation_id": (
                    raw_observation.source_observation_id
                ),
                "content_hash": content_hash,
            }
        )

        replay_payload = {
            "schema_version": SCHEMA_VERSION,
            "observation_id": observation_id,
            "source_id": normalized_source_id,
            "source_observation_id": (
                raw_observation.source_observation_id
            ),
            "observation_type": (
                raw_observation.observation_type
            ),
            "observed_at": raw_observation.observed_at,
            "acquired_at": normalized_acquired_at,
            "acquisition_batch_id": normalized_batch_id,
            "payload": raw_observation.payload_dict(),
            "provenance": raw_observation.provenance_dict(),
            "content_hash": content_hash,
            "read_only": True,
            "execution_allowed": False,
        }

        return cls(
            schema_version=SCHEMA_VERSION,
            observation_id=observation_id,
            source_id=normalized_source_id,
            source_observation_id=(
                raw_observation.source_observation_id
            ),
            observation_type=(
                raw_observation.observation_type
            ),
            observed_at=raw_observation.observed_at,
            acquired_at=normalized_acquired_at,
            acquisition_batch_id=normalized_batch_id,
            payload=raw_observation.payload,
            provenance=raw_observation.provenance,
            content_hash=content_hash,
            replay_hash=stable_hash(replay_payload),
            read_only=True,
            execution_allowed=False,
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "source_observation_id": (
                self.source_observation_id
            ),
            "observation_type": self.observation_type,
            "observed_at": self.observed_at.isoformat(),
            "acquired_at": self.acquired_at.isoformat(),
            "acquisition_batch_id": self.acquisition_batch_id,
            "payload": _mapping_from_immutable(self.payload),
            "provenance": _mapping_from_immutable(
                self.provenance
            ),
            "content_hash": self.content_hash,
            "replay_hash": self.replay_hash,
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
        }


@dataclass(frozen=True, slots=True)
class DeduplicationEvidence:
    observation_id: str
    content_hash: str
    duplicate: bool
    canonical_observation_id: str
    checked_at: datetime
    deduplication_policy_id: str
    evidence_hash: str

    @classmethod
    def create(
        cls,
        *,
        observation: CanonicalObservation,
        duplicate: bool,
        canonical_observation_id: str,
        checked_at: datetime,
        deduplication_policy_id: str,
    ) -> "DeduplicationEvidence":
        if not isinstance(duplicate, bool):
            raise AcquisitionContractError(
                "duplicate must be a bool"
            )

        normalized_canonical_observation_id = (
            _require_non_empty_string(
                canonical_observation_id,
                "canonical_observation_id",
            )
        )

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )
        normalized_policy_id = _require_non_empty_string(
            deduplication_policy_id,
            "deduplication_policy_id",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "deduplication_evidence",
            "observation_id": observation.observation_id,
            "content_hash": observation.content_hash,
            "duplicate": duplicate,
            "canonical_observation_id": (
                normalized_canonical_observation_id
            ),
            "checked_at": normalized_checked_at,
            "deduplication_policy_id": normalized_policy_id,
        }

        return cls(
            observation_id=observation.observation_id,
            content_hash=observation.content_hash,
            duplicate=duplicate,
            canonical_observation_id=(
                normalized_canonical_observation_id
            ),
            checked_at=normalized_checked_at,
            deduplication_policy_id=normalized_policy_id,
            evidence_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "content_hash": self.content_hash,
            "duplicate": self.duplicate,
            "canonical_observation_id": (
                self.canonical_observation_id
            ),
            "checked_at": self.checked_at.isoformat(),
            "deduplication_policy_id": (
                self.deduplication_policy_id
            ),
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True, slots=True)
class ObservationRoutingEvidence:
    observation_id: str
    route_id: str
    routed_at: datetime
    accepted: bool
    metadata: tuple[tuple[str, JSONValue], ...]
    evidence_hash: str

    @classmethod
    def create(
        cls,
        *,
        observation_id: str,
        route_id: str,
        routed_at: datetime,
        accepted: bool,
        metadata: Mapping[str, Any],
    ) -> "ObservationRoutingEvidence":
        normalized_observation_id = _require_non_empty_string(
            observation_id,
            "observation_id",
        )
        normalized_route_id = _require_non_empty_string(
            route_id,
            "route_id",
        )
        normalized_routed_at = _require_aware_datetime(
            routed_at,
            "routed_at",
        )

        if not isinstance(accepted, bool):
            raise AcquisitionContractError(
                "accepted must be a bool"
            )

        immutable_metadata = _immutable_mapping(
            metadata,
            "metadata",
        )

        hash_payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "observation_routing_evidence",
            "observation_id": normalized_observation_id,
            "route_id": normalized_route_id,
            "routed_at": normalized_routed_at,
            "accepted": accepted,
            "metadata": _mapping_from_immutable(
                immutable_metadata
            ),
        }

        return cls(
            observation_id=normalized_observation_id,
            route_id=normalized_route_id,
            routed_at=normalized_routed_at,
            accepted=accepted,
            metadata=immutable_metadata,
            evidence_hash=stable_hash(hash_payload),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "route_id": self.route_id,
            "routed_at": self.routed_at.isoformat(),
            "accepted": self.accepted,
            "metadata": _mapping_from_immutable(
                self.metadata
            ),
            "evidence_hash": self.evidence_hash,
        }


@dataclass(frozen=True, slots=True)
class AcquisitionObservationRecord:
    observation: CanonicalObservation
    deduplication: DeduplicationEvidence
    routing: ObservationRoutingEvidence | None

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "observation": self.observation.to_canonical_dict(),
            "deduplication": (
                self.deduplication.to_canonical_dict()
            ),
            "routing": (
                None
                if self.routing is None
                else self.routing.to_canonical_dict()
            ),
        }


@dataclass(frozen=True, slots=True)
class AcquisitionBatchRecord:
    schema_version: str
    engine_id: str
    acquisition_batch_id: str
    source_id: str
    adapter_id: str
    acquired_at: datetime
    health_evidence: SourceHealthEvidence
    rate_control_evidence: RateControlEvidence
    observations: tuple[AcquisitionObservationRecord, ...]
    observation_count: int
    canonical_count: int
    duplicate_count: int
    routed_count: int
    status: str
    replay_metadata: tuple[tuple[str, JSONValue], ...]
    audit_metadata: tuple[tuple[str, JSONValue], ...]
    batch_hash: str
    read_only: bool
    execution_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    execution_adapter_invocation_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def to_canonical_dict(
        self,
        *,
        include_batch_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "acquisition_batch_id": self.acquisition_batch_id,
            "source_id": self.source_id,
            "adapter_id": self.adapter_id,
            "acquired_at": self.acquired_at.isoformat(),
            "health_evidence": (
                self.health_evidence.to_canonical_dict()
            ),
            "rate_control_evidence": (
                self.rate_control_evidence.to_canonical_dict()
            ),
            "observations": [
                record.to_canonical_dict()
                for record in self.observations
            ],
            "observation_count": self.observation_count,
            "canonical_count": self.canonical_count,
            "duplicate_count": self.duplicate_count,
            "routed_count": self.routed_count,
            "status": self.status,
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
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

        if include_batch_hash:
            result["batch_hash"] = self.batch_hash

        return result


class ApprovedReadOnlySourceAdapter(Protocol):
    adapter_id: str
    source_id: str
    read_only: bool
    execution_allowed: bool

    def acquire(
        self,
        *,
        acquired_at: datetime,
    ) -> Sequence[RawSourceObservation]:
        ...


DeduplicationHook = Callable[
    [CanonicalObservation, datetime],
    DeduplicationEvidence,
]

CanonicalObservationRouter = Callable[
    [CanonicalObservation, datetime],
    ObservationRoutingEvidence,
]


@dataclass(frozen=True, slots=True)
class ApprovedSourceAdapterRegistration:
    adapter_id: str
    source_id: str
    adapter: ApprovedReadOnlySourceAdapter

    @classmethod
    def create(
        cls,
        *,
        adapter: ApprovedReadOnlySourceAdapter,
    ) -> "ApprovedSourceAdapterRegistration":
        adapter_id = _require_non_empty_string(
            getattr(adapter, "adapter_id", None),
            "adapter.adapter_id",
        )
        source_id = _require_non_empty_string(
            getattr(adapter, "source_id", None),
            "adapter.source_id",
        )

        if getattr(adapter, "read_only", None) is not True:
            raise AcquisitionInvariantError(
                "approved Oracle source adapters must be read_only"
            )

        if (
            getattr(adapter, "execution_allowed", None)
            is not False
        ):
            raise AcquisitionInvariantError(
                "approved Oracle source adapters must prohibit execution"
            )

        acquire_method = getattr(adapter, "acquire", None)

        if not callable(acquire_method):
            raise AcquisitionContractError(
                "approved source adapter must provide acquire()"
            )

        return cls(
            adapter_id=adapter_id,
            source_id=source_id,
            adapter=adapter,
        )


class OracleLiveReadOnlyAcquisitionRuntime:
    """
    Controlled Oracle live acquisition boundary.

    Fail-closed principles:
    - only explicitly registered adapters may acquire,
    - adapters must declare read-only and no-execution invariants,
    - unhealthy sources are blocked,
    - rate-denied sources are blocked,
    - malformed observations fail the entire batch,
    - incompatible deduplication evidence fails the batch,
    - rejected or malformed routing evidence fails the batch,
    - duplicate observations are never routed again.
    """

    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True
    execution_allowed = False
    trade_authorization_allowed = False
    order_placement_allowed = False
    execution_adapter_invocation_allowed = False
    funds_moved = False
    portfolio_mutated = False

    def __init__(
        self,
        *,
        approved_adapters: Iterable[
            ApprovedReadOnlySourceAdapter
        ],
        deduplication_hook: DeduplicationHook,
        canonical_observation_router: CanonicalObservationRouter,
        healthy_statuses: Iterable[str] = ("ok", "healthy"),
    ) -> None:
        if not callable(deduplication_hook):
            raise AcquisitionContractError(
                "deduplication_hook must be callable"
            )

        if not callable(canonical_observation_router):
            raise AcquisitionContractError(
                "canonical_observation_router must be callable"
            )

        normalized_healthy_statuses = frozenset(
            _require_non_empty_string(
                status,
                "healthy status",
            )
            for status in healthy_statuses
        )

        if not normalized_healthy_statuses:
            raise AcquisitionContractError(
                "healthy_statuses must not be empty"
            )

        registrations: dict[
            str,
            ApprovedSourceAdapterRegistration,
        ] = {}

        for adapter in approved_adapters:
            registration = (
                ApprovedSourceAdapterRegistration.create(
                    adapter=adapter
                )
            )

            if registration.adapter_id in registrations:
                raise AcquisitionContractError(
                    "duplicate approved adapter_id: "
                    f"{registration.adapter_id}"
                )

            registrations[
                registration.adapter_id
            ] = registration

        if not registrations:
            raise AcquisitionContractError(
                "at least one approved source adapter is required"
            )

        self._registrations = registrations
        self._deduplication_hook = deduplication_hook
        self._canonical_observation_router = (
            canonical_observation_router
        )
        self._healthy_statuses = normalized_healthy_statuses

        self._assert_runtime_invariants()

    def _assert_runtime_invariants(self) -> None:
        invariants = {
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
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
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "execution_adapter_invocation_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        if invariants != expected:
            raise AcquisitionInvariantError(
                "Oracle acquisition no-execution invariants violated"
            )

    @property
    def approved_adapter_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def acquire(
        self,
        *,
        adapter_id: str,
        acquired_at: datetime,
        health_evidence: SourceHealthEvidence,
        rate_control_evidence: RateControlEvidence,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> AcquisitionBatchRecord:
        self._assert_runtime_invariants()

        normalized_adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        )
        normalized_acquired_at = _require_aware_datetime(
            acquired_at,
            "acquired_at",
        )

        registration = self._registrations.get(
            normalized_adapter_id
        )

        if registration is None:
            raise UnapprovedSourceAdapterError(
                "source adapter is not approved: "
                f"{normalized_adapter_id}"
            )

        self._validate_adapter_registration(registration)

        if not isinstance(
            health_evidence,
            SourceHealthEvidence,
        ):
            raise AcquisitionContractError(
                "health_evidence must be SourceHealthEvidence"
            )

        if not isinstance(
            rate_control_evidence,
            RateControlEvidence,
        ):
            raise AcquisitionContractError(
                "rate_control_evidence must be RateControlEvidence"
            )

        self._validate_control_evidence(
            registration=registration,
            acquired_at=normalized_acquired_at,
            health_evidence=health_evidence,
            rate_control_evidence=rate_control_evidence,
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )
        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        acquisition_batch_id = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "acquisition_batch_identity",
                "adapter_id": registration.adapter_id,
                "source_id": registration.source_id,
                "acquired_at": normalized_acquired_at,
                "health_evidence_hash": (
                    health_evidence.evidence_hash
                ),
                "rate_control_evidence_hash": (
                    rate_control_evidence.evidence_hash
                ),
                "replay_metadata": _mapping_from_immutable(
                    immutable_replay_metadata
                ),
                "audit_metadata": _mapping_from_immutable(
                    immutable_audit_metadata
                ),
            }
        )

        try:
            raw_result = registration.adapter.acquire(
                acquired_at=normalized_acquired_at
            )
        except Exception as exc:
            raise SourceAdapterFailure(
                "approved source adapter acquisition failed closed"
            ) from exc

        raw_observations = self._validate_raw_result(
            raw_result
        )

        observation_records: list[
            AcquisitionObservationRecord
        ] = []

        for raw_observation in raw_observations:
            canonical_observation = CanonicalObservation.create(
                source_id=registration.source_id,
                raw_observation=raw_observation,
                acquired_at=normalized_acquired_at,
                acquisition_batch_id=acquisition_batch_id,
            )

            deduplication = self._run_deduplication(
                observation=canonical_observation,
                checked_at=normalized_acquired_at,
            )

            routing: ObservationRoutingEvidence | None = None

            if not deduplication.duplicate:
                routing = self._route_observation(
                    observation=canonical_observation,
                    routed_at=normalized_acquired_at,
                )

            observation_records.append(
                AcquisitionObservationRecord(
                    observation=canonical_observation,
                    deduplication=deduplication,
                    routing=routing,
                )
            )

        immutable_records = tuple(observation_records)

        duplicate_count = sum(
            1
            for record in immutable_records
            if record.deduplication.duplicate
        )

        canonical_count = (
            len(immutable_records) - duplicate_count
        )

        routed_count = sum(
            1
            for record in immutable_records
            if record.routing is not None
            and record.routing.accepted
        )

        if routed_count != canonical_count:
            raise CanonicalObservationRouterFailure(
                "all non-duplicate canonical observations must "
                "produce accepted routing evidence"
            )

        status = "passed"

        provisional_record = AcquisitionBatchRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            acquisition_batch_id=acquisition_batch_id,
            source_id=registration.source_id,
            adapter_id=registration.adapter_id,
            acquired_at=normalized_acquired_at,
            health_evidence=health_evidence,
            rate_control_evidence=rate_control_evidence,
            observations=immutable_records,
            observation_count=len(immutable_records),
            canonical_count=canonical_count,
            duplicate_count=duplicate_count,
            routed_count=routed_count,
            status=status,
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
            batch_hash="",
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

        batch_hash = stable_hash(
            provisional_record.to_canonical_dict(
                include_batch_hash=False
            )
        )

        return AcquisitionBatchRecord(
            schema_version=provisional_record.schema_version,
            engine_id=provisional_record.engine_id,
            acquisition_batch_id=(
                provisional_record.acquisition_batch_id
            ),
            source_id=provisional_record.source_id,
            adapter_id=provisional_record.adapter_id,
            acquired_at=provisional_record.acquired_at,
            health_evidence=(
                provisional_record.health_evidence
            ),
            rate_control_evidence=(
                provisional_record.rate_control_evidence
            ),
            observations=provisional_record.observations,
            observation_count=(
                provisional_record.observation_count
            ),
            canonical_count=provisional_record.canonical_count,
            duplicate_count=provisional_record.duplicate_count,
            routed_count=provisional_record.routed_count,
            status=provisional_record.status,
            replay_metadata=provisional_record.replay_metadata,
            audit_metadata=provisional_record.audit_metadata,
            batch_hash=batch_hash,
            read_only=True,
            execution_allowed=False,
            trade_authorization_allowed=False,
            order_placement_allowed=False,
            execution_adapter_invocation_allowed=False,
            funds_moved=False,
            portfolio_mutated=False,
        )

    def _validate_adapter_registration(
        self,
        registration: ApprovedSourceAdapterRegistration,
    ) -> None:
        current_adapter_id = _require_non_empty_string(
            getattr(
                registration.adapter,
                "adapter_id",
                None,
            ),
            "adapter.adapter_id",
        )

        current_source_id = _require_non_empty_string(
            getattr(
                registration.adapter,
                "source_id",
                None,
            ),
            "adapter.source_id",
        )

        if current_adapter_id != registration.adapter_id:
            raise AcquisitionInvariantError(
                "approved adapter identity changed after registration"
            )

        if current_source_id != registration.source_id:
            raise AcquisitionInvariantError(
                "approved source identity changed after registration"
            )

        if (
            getattr(
                registration.adapter,
                "read_only",
                None,
            )
            is not True
        ):
            raise AcquisitionInvariantError(
                "approved adapter lost read-only invariant"
            )

        if (
            getattr(
                registration.adapter,
                "execution_allowed",
                None,
            )
            is not False
        ):
            raise AcquisitionInvariantError(
                "approved adapter gained execution capability"
            )

    def _validate_control_evidence(
        self,
        *,
        registration: ApprovedSourceAdapterRegistration,
        acquired_at: datetime,
        health_evidence: SourceHealthEvidence,
        rate_control_evidence: RateControlEvidence,
    ) -> None:
        if health_evidence.source_id != registration.source_id:
            raise AcquisitionContractError(
                "health evidence source_id does not match "
                "approved source"
            )

        if (
            rate_control_evidence.source_id
            != registration.source_id
        ):
            raise AcquisitionContractError(
                "rate-control evidence source_id does not match "
                "approved source"
            )

        if health_evidence.checked_at > acquired_at:
            raise AcquisitionContractError(
                "health evidence cannot be from the future "
                "relative to acquired_at"
            )

        if rate_control_evidence.checked_at > acquired_at:
            raise AcquisitionContractError(
                "rate-control evidence cannot be from the future "
                "relative to acquired_at"
            )

        if (
            health_evidence.status
            not in self._healthy_statuses
        ):
            raise SourceAdapterFailure(
                "source health evidence blocked acquisition"
            )

        if not rate_control_evidence.allowed:
            raise SourceAdapterFailure(
                "rate-control evidence blocked acquisition"
            )

    def _validate_raw_result(
        self,
        raw_result: Any,
    ) -> tuple[RawSourceObservation, ...]:
        if isinstance(raw_result, (str, bytes, Mapping)):
            raise AcquisitionContractError(
                "adapter acquire() must return a sequence of "
                "RawSourceObservation records"
            )

        if not isinstance(raw_result, Sequence):
            raise AcquisitionContractError(
                "adapter acquire() must return a sequence"
            )

        observations: list[RawSourceObservation] = []

        for item in raw_result:
            if not isinstance(item, RawSourceObservation):
                raise AcquisitionContractError(
                    "adapter returned a malformed or incompatible "
                    "observation"
                )

            observations.append(item)

        return tuple(observations)

    def _run_deduplication(
        self,
        *,
        observation: CanonicalObservation,
        checked_at: datetime,
    ) -> DeduplicationEvidence:
        try:
            evidence = self._deduplication_hook(
                observation,
                checked_at,
            )
        except Exception as exc:
            raise SourceAdapterFailure(
                "deduplication hook failed closed"
            ) from exc

        if not isinstance(
            evidence,
            DeduplicationEvidence,
        ):
            raise AcquisitionContractError(
                "deduplication hook returned incompatible evidence"
            )

        if evidence.observation_id != observation.observation_id:
            raise AcquisitionContractError(
                "deduplication evidence observation_id mismatch"
            )

        if evidence.content_hash != observation.content_hash:
            raise AcquisitionContractError(
                "deduplication evidence content_hash mismatch"
            )

        if evidence.checked_at != checked_at:
            raise AcquisitionContractError(
                "deduplication evidence checked_at mismatch"
            )

        if (
            not evidence.duplicate
            and evidence.canonical_observation_id
            != observation.observation_id
        ):
            raise AcquisitionContractError(
                "non-duplicate evidence must identify the current "
                "observation as canonical"
            )

        return evidence

    def _route_observation(
        self,
        *,
        observation: CanonicalObservation,
        routed_at: datetime,
    ) -> ObservationRoutingEvidence:
        try:
            evidence = self._canonical_observation_router(
                observation,
                routed_at,
            )
        except Exception as exc:
            raise CanonicalObservationRouterFailure(
                "canonical observation routing failed closed"
            ) from exc

        if not isinstance(
            evidence,
            ObservationRoutingEvidence,
        ):
            raise AcquisitionContractError(
                "canonical observation router returned "
                "incompatible evidence"
            )

        if evidence.observation_id != observation.observation_id:
            raise AcquisitionContractError(
                "routing evidence observation_id mismatch"
            )

        if evidence.routed_at != routed_at:
            raise AcquisitionContractError(
                "routing evidence routed_at mismatch"
            )

        if not evidence.accepted:
            raise CanonicalObservationRouterFailure(
                "canonical observation routing was rejected"
            )

        return evidence


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "AcquisitionContractError",
    "UnapprovedSourceAdapterError",
    "AcquisitionInvariantError",
    "SourceAdapterFailure",
    "CanonicalObservationRouterFailure",
    "SourceHealthEvidence",
    "RateControlEvidence",
    "RawSourceObservation",
    "CanonicalObservation",
    "DeduplicationEvidence",
    "ObservationRoutingEvidence",
    "AcquisitionObservationRecord",
    "AcquisitionBatchRecord",
    "ApprovedReadOnlySourceAdapter",
    "ApprovedSourceAdapterRegistration",
    "OracleLiveReadOnlyAcquisitionRuntime",
    "canonical_json",
    "stable_hash",
]
