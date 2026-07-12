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
    / "oracle_canonical_observation_persistence_router.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_009_oracle_canonical_observation_persistence_router.py"
)


MODULE_CONTENT = r'''
"""
OLA-009
Oracle Canonical Observation Persistence Router

Canonical read-only bridge between the OLA-001 canonical observation
routing contract and the OLA-008 append-only persistence ledger.

Architecture:

OLA-001 ACQUISITION
    |
CANONICAL OBSERVATION
    |
OLA-003 DEDUPLICATION
    |
OLA-009 PERSISTENCE ROUTER
    |
OLA-008 APPEND-ONLY PERSISTENCE LEDGER
    |
OLA-001 ROUTING EVIDENCE

Permanent rules:

- Only CanonicalObservation records may be routed.
- routed_at is caller supplied by OLA-001.
- Persistence occurs before accepted routing evidence is emitted.
- Successful persistence entry identity is preserved.
- Persistence sequence identity is preserved.
- Persistence chain identity is preserved.
- Observation identity is preserved.
- Source identity is preserved.
- Content hash is preserved.
- Replay hash is preserved.
- Duplicate persistence conflicts fail closed.
- Persistence failures fail closed.
- Routing evidence is accepted only after validated persistence.
- No alternate non-persistent success path exists.
- No default persistence backend exists.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade authorization exists.
- No orders are placed.
- No funds are moved.
- No portfolio is mutated.
- Canonical stable hashing is used.
- repr() is never used.
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
    JSONValue,
    ObservationRoutingEvidence,
)

from .oracle_canonical_observation_persistence_ledger import (
    CanonicalObservationPersistenceEntry,
    ObservationPersistenceConflictError,
    ObservationPersistenceContractError,
    ObservationPersistenceInvariantError,
    OracleCanonicalObservationPersistenceLedger,
)


SCHEMA_VERSION = "OLA-009"
ENGINE_ID = "OLA-009"

PERSISTENCE_ROUTING_RECORD_TYPE = (
    "canonical_observation_persistence_routing_record"
)


class PersistenceRoutingContractError(ValueError):
    """Raised when persistence routing contract data is malformed."""


class PersistenceRoutingFailure(RuntimeError):
    """Raised when canonical persistence routing fails closed."""


class PersistenceRoutingInvariantError(RuntimeError):
    """Raised when permanent persistence routing invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PersistenceRoutingContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PersistenceRoutingContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PersistenceRoutingContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PersistenceRoutingContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


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
            raise PersistenceRoutingContractError(
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
                raise PersistenceRoutingContractError(
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

    raise PersistenceRoutingContractError(
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
        raise PersistenceRoutingContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PersistenceRoutingContractError(
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
class CanonicalObservationPersistenceRoutingRecord:
    schema_version: str
    engine_id: str
    route_id: str
    observation_id: str
    source_id: str
    acquisition_batch_id: str
    content_hash: str
    observation_replay_hash: str
    routed_at: datetime
    persistence_entry_id: str
    persistence_sequence_number: int
    persistence_entry_hash: str
    persistence_chain_hash: str
    persistence_previous_chain_hash: str
    persistence_verified: bool
    routing_accepted: bool
    persistence_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    routing_record_hash: str
    immutable: bool
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

    def to_canonical_dict(
        self,
        *,
        include_routing_record_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "route_id": self.route_id,
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "acquisition_batch_id": (
                self.acquisition_batch_id
            ),
            "content_hash": self.content_hash,
            "observation_replay_hash": (
                self.observation_replay_hash
            ),
            "routed_at": self.routed_at.isoformat(),
            "persistence_entry_id": (
                self.persistence_entry_id
            ),
            "persistence_sequence_number": (
                self.persistence_sequence_number
            ),
            "persistence_entry_hash": (
                self.persistence_entry_hash
            ),
            "persistence_chain_hash": (
                self.persistence_chain_hash
            ),
            "persistence_previous_chain_hash": (
                self.persistence_previous_chain_hash
            ),
            "persistence_verified": self.persistence_verified,
            "routing_accepted": self.routing_accepted,
            "persistence_metadata": _mapping_from_immutable(
                self.persistence_metadata
            ),
            "replay_metadata": _mapping_from_immutable(
                self.replay_metadata
            ),
            "audit_metadata": _mapping_from_immutable(
                self.audit_metadata
            ),
            "immutable": self.immutable,
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

        if include_routing_record_hash:
            result["routing_record_hash"] = (
                self.routing_record_hash
            )

        return result


class OracleCanonicalObservationPersistenceRouter:
    """
    OLA-001-compatible canonical observation router backed by OLA-008.

    Usage:

        ledger = OracleCanonicalObservationPersistenceLedger()

        router = OracleCanonicalObservationPersistenceRouter(
            persistence_ledger=ledger,
            route_id="oracle.persistence.router.v1",
            persistence_metadata={...},
            replay_metadata={...},
            audit_metadata={...},
        )

        runtime = OracleLiveReadOnlyAcquisitionRuntime(
            ...,
            canonical_observation_router=router,
        )

    The router is callable and matches the OLA-001 router hook contract:

        router(
            observation: CanonicalObservation,
            routed_at: datetime,
        ) -> ObservationRoutingEvidence

    A routing result is accepted only after OLA-008 persistence succeeds
    and the appended persistence entry is independently validated.
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

    def __init__(
        self,
        *,
        persistence_ledger: (
            OracleCanonicalObservationPersistenceLedger
        ),
        route_id: str,
        persistence_metadata: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> None:
        if not isinstance(
            persistence_ledger,
            OracleCanonicalObservationPersistenceLedger,
        ):
            raise PersistenceRoutingContractError(
                "persistence_ledger must be "
                "OracleCanonicalObservationPersistenceLedger"
            )

        self._persistence_ledger = persistence_ledger

        self._route_id = _require_non_empty_string(
            route_id,
            "route_id",
        )

        self._persistence_metadata = _immutable_mapping(
            persistence_metadata,
            "persistence_metadata",
        )

        self._replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        self._audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        self._routing_records: list[
            CanonicalObservationPersistenceRoutingRecord
        ] = []

        self._routing_records_by_observation_id: dict[
            str,
            CanonicalObservationPersistenceRoutingRecord,
        ] = {}

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
            raise PersistenceRoutingInvariantError(
                "Oracle persistence router invariants violated"
            )

        if self._persistence_ledger.read_only is not True:
            raise PersistenceRoutingInvariantError(
                "persistence ledger lost read_only invariant"
            )

        if (
            self._persistence_ledger.execution_allowed
            is not False
        ):
            raise PersistenceRoutingInvariantError(
                "persistence ledger gained execution capability"
            )

    @property
    def route_id(self) -> str:
        return self._route_id

    @property
    def persistence_ledger(
        self,
    ) -> OracleCanonicalObservationPersistenceLedger:
        return self._persistence_ledger

    @property
    def routing_record_count(self) -> int:
        return len(self._routing_records)

    @property
    def routing_records(
        self,
    ) -> tuple[
        CanonicalObservationPersistenceRoutingRecord,
        ...
    ]:
        return tuple(self._routing_records)

    def route(
        self,
        observation: CanonicalObservation,
        routed_at: datetime,
    ) -> ObservationRoutingEvidence:
        self._assert_invariants()

        if not isinstance(
            observation,
            CanonicalObservation,
        ):
            raise PersistenceRoutingContractError(
                "observation must be CanonicalObservation"
            )

        normalized_routed_at = _require_aware_datetime(
            routed_at,
            "routed_at",
        )

        if normalized_routed_at < observation.acquired_at:
            raise PersistenceRoutingContractError(
                "routed_at cannot be before acquired_at"
            )

        if (
            observation.observation_id
            in self._routing_records_by_observation_id
        ):
            raise PersistenceRoutingFailure(
                "observation_id has already been routed "
                "through persistence router"
            )

        try:
            entry = self._persistence_ledger.append(
                observation=observation,
                persisted_at=normalized_routed_at,
                persistence_metadata=(
                    _mapping_from_immutable(
                        self._persistence_metadata
                    )
                ),
            )
        except (
            ObservationPersistenceConflictError,
            ObservationPersistenceContractError,
            ObservationPersistenceInvariantError,
        ) as exc:
            raise PersistenceRoutingFailure(
                "canonical observation persistence failed closed"
            ) from exc

        self._validate_persistence_entry(
            observation=observation,
            entry=entry,
            routed_at=normalized_routed_at,
        )

        routing_record = self._build_routing_record(
            observation=observation,
            entry=entry,
            routed_at=normalized_routed_at,
        )

        self._routing_records.append(
            routing_record
        )

        self._routing_records_by_observation_id[
            observation.observation_id
        ] = routing_record

        return ObservationRoutingEvidence.create(
            observation_id=observation.observation_id,
            route_id=self._route_id,
            routed_at=normalized_routed_at,
            accepted=True,
            metadata={
                "router_engine_id": ENGINE_ID,
                "routing_record_hash": (
                    routing_record.routing_record_hash
                ),
                "persistence_verified": True,
                "persistence_entry_id": (
                    entry.persistence_entry_id
                ),
                "persistence_sequence_number": (
                    entry.sequence_number
                ),
                "persistence_entry_hash": (
                    entry.entry_hash
                ),
                "persistence_chain_hash": (
                    entry.chain_hash
                ),
                "persistence_previous_chain_hash": (
                    entry.previous_chain_hash
                ),
                "observation_content_hash": (
                    observation.content_hash
                ),
                "observation_replay_hash": (
                    observation.replay_hash
                ),
                "destination": (
                    "oracle.canonical.persistence"
                ),
            },
        )

    __call__ = route

    @staticmethod
    def _validate_persistence_entry(
        *,
        observation: CanonicalObservation,
        entry: CanonicalObservationPersistenceEntry,
        routed_at: datetime,
    ) -> None:
        if not isinstance(
            entry,
            CanonicalObservationPersistenceEntry,
        ):
            raise PersistenceRoutingFailure(
                "persistence ledger returned incompatible entry"
            )

        if entry.observation_id != observation.observation_id:
            raise PersistenceRoutingFailure(
                "persisted observation identity mismatch"
            )

        if entry.source_id != observation.source_id:
            raise PersistenceRoutingFailure(
                "persisted source identity mismatch"
            )

        if (
            entry.source_observation_id
            != observation.source_observation_id
        ):
            raise PersistenceRoutingFailure(
                "persisted source observation identity mismatch"
            )

        if (
            entry.acquisition_batch_id
            != observation.acquisition_batch_id
        ):
            raise PersistenceRoutingFailure(
                "persisted acquisition batch identity mismatch"
            )

        if entry.content_hash != observation.content_hash:
            raise PersistenceRoutingFailure(
                "persisted content hash mismatch"
            )

        if (
            entry.observation_replay_hash
            != observation.replay_hash
        ):
            raise PersistenceRoutingFailure(
                "persisted replay hash mismatch"
            )

        if entry.persisted_at != routed_at:
            raise PersistenceRoutingFailure(
                "persisted_at does not match routed_at"
            )

        if entry.calculate_entry_hash() != entry.entry_hash:
            raise PersistenceRoutingFailure(
                "persistence entry hash validation failed"
            )

        if entry.calculate_chain_hash() != entry.chain_hash:
            raise PersistenceRoutingFailure(
                "persistence chain hash validation failed"
            )

        if entry.read_only is not True:
            raise PersistenceRoutingFailure(
                "persistence entry lost read_only invariant"
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
            raise PersistenceRoutingFailure(
                "persistence entry gained execution capability"
            )

    def _build_routing_record(
        self,
        *,
        observation: CanonicalObservation,
        entry: CanonicalObservationPersistenceEntry,
        routed_at: datetime,
    ) -> CanonicalObservationPersistenceRoutingRecord:
        provisional = (
            CanonicalObservationPersistenceRoutingRecord(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                route_id=self._route_id,
                observation_id=observation.observation_id,
                source_id=observation.source_id,
                acquisition_batch_id=(
                    observation.acquisition_batch_id
                ),
                content_hash=observation.content_hash,
                observation_replay_hash=(
                    observation.replay_hash
                ),
                routed_at=routed_at,
                persistence_entry_id=(
                    entry.persistence_entry_id
                ),
                persistence_sequence_number=(
                    entry.sequence_number
                ),
                persistence_entry_hash=entry.entry_hash,
                persistence_chain_hash=entry.chain_hash,
                persistence_previous_chain_hash=(
                    entry.previous_chain_hash
                ),
                persistence_verified=True,
                routing_accepted=True,
                persistence_metadata=(
                    self._persistence_metadata
                ),
                replay_metadata=self._replay_metadata,
                audit_metadata=self._audit_metadata,
                routing_record_hash="",
                immutable=True,
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
        )

        routing_record_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": (
                    PERSISTENCE_ROUTING_RECORD_TYPE
                ),
                "routing_record": (
                    provisional.to_canonical_dict(
                        include_routing_record_hash=False
                    )
                ),
            }
        )

        return CanonicalObservationPersistenceRoutingRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            route_id=provisional.route_id,
            observation_id=provisional.observation_id,
            source_id=provisional.source_id,
            acquisition_batch_id=(
                provisional.acquisition_batch_id
            ),
            content_hash=provisional.content_hash,
            observation_replay_hash=(
                provisional.observation_replay_hash
            ),
            routed_at=provisional.routed_at,
            persistence_entry_id=(
                provisional.persistence_entry_id
            ),
            persistence_sequence_number=(
                provisional.persistence_sequence_number
            ),
            persistence_entry_hash=(
                provisional.persistence_entry_hash
            ),
            persistence_chain_hash=(
                provisional.persistence_chain_hash
            ),
            persistence_previous_chain_hash=(
                provisional.persistence_previous_chain_hash
            ),
            persistence_verified=True,
            routing_accepted=True,
            persistence_metadata=(
                provisional.persistence_metadata
            ),
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            routing_record_hash=routing_record_hash,
            immutable=True,
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

    def get_routing_record(
        self,
        *,
        observation_id: str,
    ) -> CanonicalObservationPersistenceRoutingRecord | None:
        normalized_observation_id = _require_non_empty_string(
            observation_id,
            "observation_id",
        )

        return self._routing_records_by_observation_id.get(
            normalized_observation_id
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "PersistenceRoutingContractError",
    "PersistenceRoutingFailure",
    "PersistenceRoutingInvariantError",
    "CanonicalObservationPersistenceRoutingRecord",
    "OracleCanonicalObservationPersistenceRouter",
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
]
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    CanonicalObservation,
    OracleCanonicalObservationPersistenceLedger,
    OracleCanonicalObservationPersistenceRouter,
    PersistenceRoutingContractError,
    PersistenceRoutingFailure,
    RawSourceObservation,
)


OBSERVED_AT_ONE = datetime(
    2026,
    7,
    12,
    0,
    0,
    0,
    tzinfo=timezone.utc,
)

OBSERVED_AT_TWO = datetime(
    2026,
    7,
    12,
    0,
    0,
    5,
    tzinfo=timezone.utc,
)

ACQUIRED_AT = datetime(
    2026,
    7,
    12,
    0,
    1,
    0,
    tzinfo=timezone.utc,
)

ROUTED_AT_ONE = datetime(
    2026,
    7,
    12,
    0,
    1,
    1,
    tzinfo=timezone.utc,
)

ROUTED_AT_TWO = datetime(
    2026,
    7,
    12,
    0,
    1,
    2,
    tzinfo=timezone.utc,
)


def build_observation_one():
    raw = RawSourceObservation.create(
        source_observation_id="kalshi.route.snapshot.001",
        observed_at=OBSERVED_AT_ONE,
        observation_type="market_snapshot",
        payload={
            "source_market_id": "KXBTC-TEST-001",
            "share_side": "yes",
            "share_price": Decimal("0.31"),
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
        acquisition_batch_id="batch.ola.009.001",
    )


def build_observation_two():
    raw = RawSourceObservation.create(
        source_observation_id="coinbase.route.snapshot.001",
        observed_at=OBSERVED_AT_TWO,
        observation_type="asset_snapshot",
        payload={
            "symbol": "BTC-USD",
            "price": Decimal("117420"),
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
        acquisition_batch_id="batch.ola.009.001",
    )


def build_router():
    ledger = OracleCanonicalObservationPersistenceLedger()

    router = OracleCanonicalObservationPersistenceRouter(
        persistence_ledger=ledger,
        route_id="oracle.canonical.persistence.router.v1",
        persistence_metadata={
            "persistence_policy_id": (
                "oracle.persistence.canonical.v1"
            ),
            "retention_required": True,
        },
        replay_metadata={
            "replay_source": "persistence_router",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-009",
            "operator": "automated_runtime",
        },
    )

    return router, ledger


def run_primary_routing_test():
    router, ledger = build_router()

    observation_one = build_observation_one()
    observation_two = build_observation_two()

    first_evidence = router.route(
        observation_one,
        ROUTED_AT_ONE,
    )

    second_evidence = router(
        observation_two,
        ROUTED_AT_TWO,
    )

    assert first_evidence.accepted is True
    assert second_evidence.accepted is True

    assert first_evidence.route_id == (
        "oracle.canonical.persistence.router.v1"
    )

    assert second_evidence.route_id == (
        "oracle.canonical.persistence.router.v1"
    )

    assert (
        first_evidence.observation_id
        == observation_one.observation_id
    )

    assert (
        second_evidence.observation_id
        == observation_two.observation_id
    )

    assert first_evidence.routed_at == ROUTED_AT_ONE
    assert second_evidence.routed_at == ROUTED_AT_TWO

    assert ledger.entry_count == 2
    assert router.routing_record_count == 2

    first_entry = ledger.get_entry(
        observation_id=observation_one.observation_id
    )

    second_entry = ledger.get_entry(
        observation_id=observation_two.observation_id
    )

    assert first_entry is not None
    assert second_entry is not None

    assert first_entry.persisted_at == ROUTED_AT_ONE
    assert second_entry.persisted_at == ROUTED_AT_TWO

    assert (
        second_entry.previous_chain_hash
        == first_entry.chain_hash
    )

    first_record = router.get_routing_record(
        observation_id=observation_one.observation_id
    )

    second_record = router.get_routing_record(
        observation_id=observation_two.observation_id
    )

    assert first_record is not None
    assert second_record is not None

    assert first_record.schema_version == "OLA-009"
    assert first_record.engine_id == "OLA-009"

    assert first_record.persistence_verified is True
    assert first_record.routing_accepted is True

    assert (
        first_record.persistence_entry_id
        == first_entry.persistence_entry_id
    )

    assert (
        first_record.persistence_sequence_number
        == first_entry.sequence_number
    )

    assert (
        first_record.persistence_entry_hash
        == first_entry.entry_hash
    )

    assert (
        first_record.persistence_chain_hash
        == first_entry.chain_hash
    )

    assert (
        first_record.persistence_previous_chain_hash
        == first_entry.previous_chain_hash
    )

    assert (
        first_record.observation_id
        == observation_one.observation_id
    )

    assert (
        first_record.source_id
        == observation_one.source_id
    )

    assert (
        first_record.acquisition_batch_id
        == observation_one.acquisition_batch_id
    )

    assert (
        first_record.content_hash
        == observation_one.content_hash
    )

    assert (
        first_record.observation_replay_hash
        == observation_one.replay_hash
    )

    assert first_record.immutable is True
    assert first_record.replayable is True
    assert first_record.auditable is True
    assert first_record.explainable is True

    assert first_record.read_only is True
    assert first_record.execution_allowed is False

    assert (
        first_record.execution_adapter_resolved
        is False
    )

    assert (
        first_record.execution_adapter_invoked
        is False
    )

    assert (
        first_record.trade_authorization_allowed
        is False
    )

    assert (
        first_record.order_placement_allowed
        is False
    )

    assert first_record.funds_moved is False
    assert first_record.portfolio_mutated is False

    try:
        first_record.routing_accepted = False

        raise AssertionError(
            "persistence routing record must be immutable"
        )

    except FrozenInstanceError:
        pass

    first_metadata = dict(first_evidence.metadata)

    assert (
        first_metadata["persistence_verified"]
        is True
    )

    assert (
        first_metadata["persistence_entry_id"]
        == first_entry.persistence_entry_id
    )

    assert (
        first_metadata["persistence_sequence_number"]
        == 1
    )

    assert (
        first_metadata["persistence_chain_hash"]
        == first_entry.chain_hash
    )

    assert (
        first_metadata["observation_content_hash"]
        == observation_one.content_hash
    )

    assert (
        first_metadata["observation_replay_hash"]
        == observation_one.replay_hash
    )

    return (
        router,
        ledger,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    )


def run_deterministic_replay_test():
    first_router, first_ledger = build_router()

    second_router, second_ledger = build_router()

    first_observation_one = build_observation_one()
    first_observation_two = build_observation_two()

    second_observation_one = build_observation_one()
    second_observation_two = build_observation_two()

    first_evidence_one = first_router(
        first_observation_one,
        ROUTED_AT_ONE,
    )

    first_evidence_two = first_router(
        first_observation_two,
        ROUTED_AT_TWO,
    )

    second_evidence_one = second_router(
        second_observation_one,
        ROUTED_AT_ONE,
    )

    second_evidence_two = second_router(
        second_observation_two,
        ROUTED_AT_TWO,
    )

    assert first_evidence_one == second_evidence_one
    assert first_evidence_two == second_evidence_two

    assert (
        first_ledger.terminal_chain_hash
        == second_ledger.terminal_chain_hash
    )

    assert (
        first_router.routing_records
        == second_router.routing_records
    )

    return first_router


def run_duplicate_route_fail_closed_test():
    router, ledger = build_router()

    observation = build_observation_one()

    router(
        observation,
        ROUTED_AT_ONE,
    )

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "duplicate routing must fail closed"
        )

    except PersistenceRoutingFailure:
        pass

    assert ledger.entry_count == 1
    assert router.routing_record_count == 1


def run_external_persistence_conflict_test():
    router, ledger = build_router()

    observation = build_observation_one()

    ledger.append(
        observation=observation,
        persisted_at=ROUTED_AT_ONE,
        persistence_metadata={
            "external_test": True,
        },
    )

    try:
        router(
            observation,
            ROUTED_AT_TWO,
        )

        raise AssertionError(
            "pre-persisted observation must fail routing closed"
        )

    except PersistenceRoutingFailure:
        pass

    assert ledger.entry_count == 1
    assert router.routing_record_count == 0


def run_timestamp_fail_closed_test():
    router, ledger = build_router()

    observation = build_observation_one()

    try:
        router(
            observation,
            datetime(
                2026,
                7,
                12,
                0,
                1,
                1,
            ),
        )

        raise AssertionError(
            "naive routed_at must fail closed"
        )

    except PersistenceRoutingContractError:
        pass

    assert ledger.entry_count == 0
    assert router.routing_record_count == 0

    try:
        router(
            observation,
            OBSERVED_AT_ONE,
        )

        raise AssertionError(
            "routing before acquired_at must fail closed"
        )

    except PersistenceRoutingContractError:
        pass

    assert ledger.entry_count == 0
    assert router.routing_record_count == 0


def main():
    (
        router,
        ledger,
        first_evidence,
        second_evidence,
        first_record,
        second_record,
    ) = run_primary_routing_test()

    replay_router = run_deterministic_replay_test()

    run_duplicate_route_fail_closed_test()
    run_external_persistence_conflict_test()
    run_timestamp_fail_closed_test()

    result = {
        "schema_version": first_record.schema_version,
        "engine_id": first_record.engine_id,
        "status": "passed",
        "route_id": router.route_id,
        "routing_record_count": (
            router.routing_record_count
        ),
        "persistence_entry_count": ledger.entry_count,
        "first_routing_accepted": (
            first_evidence.accepted
        ),
        "second_routing_accepted": (
            second_evidence.accepted
        ),
        "persistence_before_acceptance": True,
        "persistence_verified": (
            first_record.persistence_verified
        ),
        "observation_identity_preserved": True,
        "source_identity_preserved": True,
        "acquisition_batch_identity_preserved": True,
        "content_hash_preserved": True,
        "observation_replay_hash_preserved": True,
        "persistence_sequence_preserved": True,
        "persistence_chain_preserved": True,
        "duplicate_route_blocked": True,
        "external_persistence_conflict_blocked": True,
        "deterministic_replay_valid": (
            replay_router.routing_record_count == 2
        ),
        "read_only": first_record.read_only,
        "execution_allowed": first_record.execution_allowed,
        "execution_adapter_resolved": (
            first_record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            first_record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            first_record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            first_record.order_placement_allowed
        ),
        "funds_moved": first_record.funds_moved,
        "portfolio_mutated": first_record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-009 Oracle Canonical Observation "
        "Persistence Router"
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
    print(" OLA-009 INSTALLER")
    print(" Oracle Canonical Observation")
    print(" Persistence Router")
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
    print("[DONE] OLA-009 installed")
    print()
    print("Run:")
    print(
        "py test_ola_009_oracle_canonical_"
        "observation_persistence_router.py"
    )


if __name__ == "__main__":
    main()