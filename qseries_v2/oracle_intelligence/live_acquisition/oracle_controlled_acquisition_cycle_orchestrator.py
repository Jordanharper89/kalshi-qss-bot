"""
OLA-010
Oracle Controlled Acquisition Cycle Orchestrator

Canonical controlled orchestration boundary for one Oracle live
read-only acquisition cycle.

Architecture:

SOURCE HEALTH / RATE CONTROL
    |
SOURCE CONTROL DECISION
    |
ACQUISITION ALLOWED?
    |
OLA-001 ACQUISITION
    |
OLA-003 DEDUPLICATION
    |
OLA-009 PERSISTENCE ROUTER
    |
OLA-008 APPEND-ONLY LEDGER
    |
CANONICAL ACQUISITION CYCLE RECORD   <- OLA-010

Permanent rules:

- Source-control evidence is required.
- Source identity must remain consistent.
- Blocked source-control decisions never invoke acquisition.
- Acquisition is invoked only when explicitly allowed.
- OLA-001 remains the acquisition runtime.
- Deduplication remains downstream of canonical normalization.
- Duplicate observations are not routed.
- Accepted routing must represent persistence-backed routing.
- Canonical observation counts must reconcile.
- Persistence entry counts must reconcile.
- Caller supplies cycle_started_at.
- Caller supplies cycle_completed_at.
- Caller-controlled timestamps are preserved.
- Cycle records are immutable.
- Cycle records are replayable.
- Cycle records are auditable.
- Cycle records are explainable.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains read-only.
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
from typing import Any, Mapping


from .oracle_live_read_only_acquisition_runtime import (
    AcquisitionBatchRecord,
    OracleLiveReadOnlyAcquisitionRuntime,
    JSONValue,
)

from .oracle_acquisition_source_control_engine import (
    SourceControlDecisionRecord,
)

from .oracle_canonical_observation_persistence_router import (
    OracleCanonicalObservationPersistenceRouter,
)


SCHEMA_VERSION = "OLA-010"
ENGINE_ID = "OLA-010"

ACQUISITION_CYCLE_RECORD_TYPE = (
    "controlled_oracle_acquisition_cycle_record"
)


class AcquisitionCycleContractError(ValueError):
    """Raised when acquisition-cycle contract data is malformed."""


class AcquisitionCycleInvariantError(RuntimeError):
    """Raised when permanent acquisition-cycle invariants are violated."""


class AcquisitionCycleReconciliationError(RuntimeError):
    """Raised when integrated cycle counts or identities do not reconcile."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise AcquisitionCycleContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise AcquisitionCycleContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise AcquisitionCycleContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise AcquisitionCycleContractError(
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
            raise AcquisitionCycleContractError(
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
                raise AcquisitionCycleContractError(
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

    raise AcquisitionCycleContractError(
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
        raise AcquisitionCycleContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise AcquisitionCycleContractError(
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
class ControlledAcquisitionCycleRecord:
    schema_version: str
    engine_id: str
    cycle_id: str
    cycle_status: str
    adapter_id: str
    source_id: str
    cycle_started_at: datetime
    cycle_completed_at: datetime
    source_control_decision_hash: str
    source_control_acquisition_allowed: bool
    acquisition_invoked: bool
    acquisition_batch_id: str | None
    acquisition_batch_hash: str | None
    observation_count: int
    canonical_count: int
    duplicate_count: int
    routed_count: int
    persisted_count: int
    persistence_terminal_chain_hash: str
    persistence_routing_record_count: int
    reason_codes: tuple[str, ...]
    replay_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    audit_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    cycle_hash: str
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
        include_cycle_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "cycle_id": self.cycle_id,
            "cycle_status": self.cycle_status,
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "cycle_started_at": (
                self.cycle_started_at.isoformat()
            ),
            "cycle_completed_at": (
                self.cycle_completed_at.isoformat()
            ),
            "source_control_decision_hash": (
                self.source_control_decision_hash
            ),
            "source_control_acquisition_allowed": (
                self.source_control_acquisition_allowed
            ),
            "acquisition_invoked": self.acquisition_invoked,
            "acquisition_batch_id": self.acquisition_batch_id,
            "acquisition_batch_hash": (
                self.acquisition_batch_hash
            ),
            "observation_count": self.observation_count,
            "canonical_count": self.canonical_count,
            "duplicate_count": self.duplicate_count,
            "routed_count": self.routed_count,
            "persisted_count": self.persisted_count,
            "persistence_terminal_chain_hash": (
                self.persistence_terminal_chain_hash
            ),
            "persistence_routing_record_count": (
                self.persistence_routing_record_count
            ),
            "reason_codes": list(self.reason_codes),
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

        if include_cycle_hash:
            result["cycle_hash"] = self.cycle_hash

        return result


class OracleControlledAcquisitionCycleOrchestrator:
    """
    Coordinates one controlled Oracle acquisition cycle.

    The orchestrator does not implement:
    - source health measurement,
    - rate measurement,
    - source acquisition,
    - normalization,
    - deduplication,
    - persistence.

    Those contracts remain owned by their canonical OLA modules.

    OLA-010 validates and binds the resulting evidence into one immutable
    acquisition-cycle record.
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
        acquisition_runtime: OracleLiveReadOnlyAcquisitionRuntime,
        persistence_router: OracleCanonicalObservationPersistenceRouter,
    ) -> None:
        if not isinstance(
            acquisition_runtime,
            OracleLiveReadOnlyAcquisitionRuntime,
        ):
            raise AcquisitionCycleContractError(
                "acquisition_runtime must be "
                "OracleLiveReadOnlyAcquisitionRuntime"
            )

        if not isinstance(
            persistence_router,
            OracleCanonicalObservationPersistenceRouter,
        ):
            raise AcquisitionCycleContractError(
                "persistence_router must be "
                "OracleCanonicalObservationPersistenceRouter"
            )

        self._acquisition_runtime = acquisition_runtime
        self._persistence_router = persistence_router

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
            raise AcquisitionCycleInvariantError(
                "Oracle acquisition-cycle invariants violated"
            )

        if self._acquisition_runtime.read_only is not True:
            raise AcquisitionCycleInvariantError(
                "acquisition runtime lost read_only invariant"
            )

        if (
            self._acquisition_runtime.execution_allowed
            is not False
        ):
            raise AcquisitionCycleInvariantError(
                "acquisition runtime gained execution capability"
            )

        if self._persistence_router.read_only is not True:
            raise AcquisitionCycleInvariantError(
                "persistence router lost read_only invariant"
            )

        if (
            self._persistence_router.execution_allowed
            is not False
        ):
            raise AcquisitionCycleInvariantError(
                "persistence router gained execution capability"
            )

    @property
    def acquisition_runtime(
        self,
    ) -> OracleLiveReadOnlyAcquisitionRuntime:
        return self._acquisition_runtime

    @property
    def persistence_router(
        self,
    ) -> OracleCanonicalObservationPersistenceRouter:
        return self._persistence_router

    def run_cycle(
        self,
        *,
        adapter_id: str,
        source_control_decision: SourceControlDecisionRecord,
        cycle_started_at: datetime,
        cycle_completed_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> ControlledAcquisitionCycleRecord:
        self._assert_invariants()

        normalized_adapter_id = _require_non_empty_string(
            adapter_id,
            "adapter_id",
        )

        if not isinstance(
            source_control_decision,
            SourceControlDecisionRecord,
        ):
            raise AcquisitionCycleContractError(
                "source_control_decision must be "
                "SourceControlDecisionRecord"
            )

        normalized_cycle_started_at = _require_aware_datetime(
            cycle_started_at,
            "cycle_started_at",
        )

        normalized_cycle_completed_at = _require_aware_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )

        if (
            normalized_cycle_completed_at
            < normalized_cycle_started_at
        ):
            raise AcquisitionCycleContractError(
                "cycle_completed_at cannot be before "
                "cycle_started_at"
            )

        if (
            source_control_decision.evaluated_at
            > normalized_cycle_started_at
        ):
            raise AcquisitionCycleContractError(
                "source-control decision cannot be evaluated after "
                "cycle_started_at"
            )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        cycle_id = "acquisition_cycle." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "controlled_acquisition_cycle_identity",
                "adapter_id": normalized_adapter_id,
                "source_id": source_control_decision.source_id,
                "cycle_started_at": normalized_cycle_started_at,
                "cycle_completed_at": normalized_cycle_completed_at,
                "source_control_decision_hash": (
                    source_control_decision.decision_hash
                ),
                "replay_metadata": _mapping_from_immutable(
                    immutable_replay_metadata
                ),
                "audit_metadata": _mapping_from_immutable(
                    immutable_audit_metadata
                ),
            }
        )

        if not source_control_decision.acquisition_allowed:
            return self._build_cycle_record(
                cycle_id=cycle_id,
                cycle_status="blocked",
                adapter_id=normalized_adapter_id,
                source_control_decision=source_control_decision,
                cycle_started_at=normalized_cycle_started_at,
                cycle_completed_at=normalized_cycle_completed_at,
                acquisition=None,
                acquisition_invoked=False,
                reason_codes=(
                    "source_control_blocked_acquisition",
                    "acquisition_not_invoked",
                    "cycle_blocked_fail_closed",
                ),
                replay_metadata=immutable_replay_metadata,
                audit_metadata=immutable_audit_metadata,
            )

        persistence_count_before = (
            self._persistence_router
            .persistence_ledger
            .entry_count
        )

        routing_count_before = (
            self._persistence_router
            .routing_record_count
        )

        acquisition = self._acquisition_runtime.acquire(
            adapter_id=normalized_adapter_id,
            acquired_at=normalized_cycle_started_at,
            health_evidence=(
                source_control_decision.health_evidence
            ),
            rate_control_evidence=(
                source_control_decision.rate_control_evidence
            ),
            replay_metadata={
                "orchestrator_engine_id": ENGINE_ID,
                "cycle_id": cycle_id,
                "parent_replay_metadata": (
                    _mapping_from_immutable(
                        immutable_replay_metadata
                    )
                ),
            },
            audit_metadata={
                "orchestrator_engine_id": ENGINE_ID,
                "cycle_id": cycle_id,
                "parent_audit_metadata": (
                    _mapping_from_immutable(
                        immutable_audit_metadata
                    )
                ),
            },
        )

        self._reconcile_successful_cycle(
            acquisition=acquisition,
            source_control_decision=source_control_decision,
            persistence_count_before=persistence_count_before,
            routing_count_before=routing_count_before,
        )

        return self._build_cycle_record(
            cycle_id=cycle_id,
            cycle_status="completed",
            adapter_id=normalized_adapter_id,
            source_control_decision=source_control_decision,
            cycle_started_at=normalized_cycle_started_at,
            cycle_completed_at=normalized_cycle_completed_at,
            acquisition=acquisition,
            acquisition_invoked=True,
            reason_codes=(
                "source_control_allowed_acquisition",
                "acquisition_invoked",
                "canonical_observations_reconciled",
                "persistence_routing_reconciled",
                "cycle_completed",
            ),
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
        )

    def _reconcile_successful_cycle(
        self,
        *,
        acquisition: AcquisitionBatchRecord,
        source_control_decision: SourceControlDecisionRecord,
        persistence_count_before: int,
        routing_count_before: int,
    ) -> None:
        if not isinstance(
            acquisition,
            AcquisitionBatchRecord,
        ):
            raise AcquisitionCycleReconciliationError(
                "acquisition runtime returned incompatible record"
            )

        if acquisition.status != "passed":
            raise AcquisitionCycleReconciliationError(
                "acquisition batch status did not pass"
            )

        if (
            acquisition.source_id
            != source_control_decision.source_id
        ):
            raise AcquisitionCycleReconciliationError(
                "source identity mismatch between source control "
                "and acquisition"
            )

        if (
            acquisition.health_evidence.evidence_hash
            != source_control_decision
            .health_evidence
            .evidence_hash
        ):
            raise AcquisitionCycleReconciliationError(
                "health evidence mismatch"
            )

        if (
            acquisition
            .rate_control_evidence
            .evidence_hash
            != source_control_decision
            .rate_control_evidence
            .evidence_hash
        ):
            raise AcquisitionCycleReconciliationError(
                "rate-control evidence mismatch"
            )

        if (
            acquisition.canonical_count
            + acquisition.duplicate_count
            != acquisition.observation_count
        ):
            raise AcquisitionCycleReconciliationError(
                "observation count reconciliation failed"
            )

        if (
            acquisition.routed_count
            != acquisition.canonical_count
        ):
            raise AcquisitionCycleReconciliationError(
                "all non-duplicate canonical observations must route"
            )

        persistence_count_after = (
            self._persistence_router
            .persistence_ledger
            .entry_count
        )

        routing_count_after = (
            self._persistence_router
            .routing_record_count
        )

        persisted_delta = (
            persistence_count_after
            - persistence_count_before
        )

        routing_delta = (
            routing_count_after
            - routing_count_before
        )

        if persisted_delta != acquisition.canonical_count:
            raise AcquisitionCycleReconciliationError(
                "persistence entry delta does not match "
                "canonical_count"
            )

        if routing_delta != acquisition.routed_count:
            raise AcquisitionCycleReconciliationError(
                "persistence routing delta does not match "
                "routed_count"
            )

        for observation_record in acquisition.observations:
            if observation_record.deduplication.duplicate:
                if observation_record.routing is not None:
                    raise AcquisitionCycleReconciliationError(
                        "duplicate observation was routed"
                    )

                continue

            if observation_record.routing is None:
                raise AcquisitionCycleReconciliationError(
                    "canonical observation is missing routing evidence"
                )

            persisted_entry = (
                self._persistence_router
                .persistence_ledger
                .get_entry(
                    observation_id=(
                        observation_record
                        .observation
                        .observation_id
                    )
                )
            )

            if persisted_entry is None:
                raise AcquisitionCycleReconciliationError(
                    "routed canonical observation was not persisted"
                )

            routing_record = (
                self._persistence_router
                .get_routing_record(
                    observation_id=(
                        observation_record
                        .observation
                        .observation_id
                    )
                )
            )

            if routing_record is None:
                raise AcquisitionCycleReconciliationError(
                    "persisted canonical observation lacks "
                    "persistence routing record"
                )

            if (
                routing_record.persistence_entry_id
                != persisted_entry.persistence_entry_id
            ):
                raise AcquisitionCycleReconciliationError(
                    "persistence routing entry identity mismatch"
                )

            if (
                routing_record.persistence_chain_hash
                != persisted_entry.chain_hash
            ):
                raise AcquisitionCycleReconciliationError(
                    "persistence chain identity mismatch"
                )

    def _build_cycle_record(
        self,
        *,
        cycle_id: str,
        cycle_status: str,
        adapter_id: str,
        source_control_decision: SourceControlDecisionRecord,
        cycle_started_at: datetime,
        cycle_completed_at: datetime,
        acquisition: AcquisitionBatchRecord | None,
        acquisition_invoked: bool,
        reason_codes: tuple[str, ...],
        replay_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
        audit_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
    ) -> ControlledAcquisitionCycleRecord:
        persisted_count = (
            0
            if acquisition is None
            else acquisition.canonical_count
        )

        provisional = ControlledAcquisitionCycleRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            cycle_id=cycle_id,
            cycle_status=cycle_status,
            adapter_id=adapter_id,
            source_id=source_control_decision.source_id,
            cycle_started_at=cycle_started_at,
            cycle_completed_at=cycle_completed_at,
            source_control_decision_hash=(
                source_control_decision.decision_hash
            ),
            source_control_acquisition_allowed=(
                source_control_decision.acquisition_allowed
            ),
            acquisition_invoked=acquisition_invoked,
            acquisition_batch_id=(
                None
                if acquisition is None
                else acquisition.acquisition_batch_id
            ),
            acquisition_batch_hash=(
                None
                if acquisition is None
                else acquisition.batch_hash
            ),
            observation_count=(
                0
                if acquisition is None
                else acquisition.observation_count
            ),
            canonical_count=(
                0
                if acquisition is None
                else acquisition.canonical_count
            ),
            duplicate_count=(
                0
                if acquisition is None
                else acquisition.duplicate_count
            ),
            routed_count=(
                0
                if acquisition is None
                else acquisition.routed_count
            ),
            persisted_count=persisted_count,
            persistence_terminal_chain_hash=(
                self._persistence_router
                .persistence_ledger
                .terminal_chain_hash
            ),
            persistence_routing_record_count=(
                self._persistence_router
                .routing_record_count
            ),
            reason_codes=reason_codes,
            replay_metadata=replay_metadata,
            audit_metadata=audit_metadata,
            cycle_hash="",
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

        cycle_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": ACQUISITION_CYCLE_RECORD_TYPE,
                "cycle_record": (
                    provisional.to_canonical_dict(
                        include_cycle_hash=False
                    )
                ),
            }
        )

        return ControlledAcquisitionCycleRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            cycle_id=provisional.cycle_id,
            cycle_status=provisional.cycle_status,
            adapter_id=provisional.adapter_id,
            source_id=provisional.source_id,
            cycle_started_at=provisional.cycle_started_at,
            cycle_completed_at=provisional.cycle_completed_at,
            source_control_decision_hash=(
                provisional.source_control_decision_hash
            ),
            source_control_acquisition_allowed=(
                provisional.source_control_acquisition_allowed
            ),
            acquisition_invoked=provisional.acquisition_invoked,
            acquisition_batch_id=(
                provisional.acquisition_batch_id
            ),
            acquisition_batch_hash=(
                provisional.acquisition_batch_hash
            ),
            observation_count=provisional.observation_count,
            canonical_count=provisional.canonical_count,
            duplicate_count=provisional.duplicate_count,
            routed_count=provisional.routed_count,
            persisted_count=provisional.persisted_count,
            persistence_terminal_chain_hash=(
                provisional.persistence_terminal_chain_hash
            ),
            persistence_routing_record_count=(
                provisional.persistence_routing_record_count
            ),
            reason_codes=provisional.reason_codes,
            replay_metadata=provisional.replay_metadata,
            audit_metadata=provisional.audit_metadata,
            cycle_hash=cycle_hash,
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


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "AcquisitionCycleContractError",
    "AcquisitionCycleInvariantError",
    "AcquisitionCycleReconciliationError",
    "ControlledAcquisitionCycleRecord",
    "OracleControlledAcquisitionCycleOrchestrator",
    "canonical_json",
    "stable_hash",
]
