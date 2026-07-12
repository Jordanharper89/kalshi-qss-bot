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
    / "oracle_controlled_acquisition_cycle_orchestrator.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_010_oracle_controlled_acquisition_cycle_orchestrator.py"
)


MODULE_CONTENT = r'''
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
]
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

from qseries_v2.oracle_intelligence.live_acquisition import (
    DeduplicationEvidence,
    ObservationRoutingEvidence,
    OracleAcquisitionDeduplicationLedger,
    OracleAcquisitionSourceControlEngine,
    OracleCanonicalObservationPersistenceLedger,
    OracleCanonicalObservationPersistenceRouter,
    OracleControlledAcquisitionCycleOrchestrator,
    OracleLiveReadOnlyAcquisitionRuntime,
    RateControlPolicy,
    RateWindowObservation,
    RawSourceObservation,
    SourceHealthObservation,
    SourceHealthPolicy,
)


CONTROL_CHECKED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    50,
    tzinfo=timezone.utc,
)

RATE_WINDOW_STARTED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    0,
    tzinfo=timezone.utc,
)

CONTROL_EVALUATED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    55,
    tzinfo=timezone.utc,
)

OBSERVED_AT = datetime(
    2026,
    7,
    12,
    0,
    9,
    58,
    tzinfo=timezone.utc,
)

CYCLE_STARTED_AT = datetime(
    2026,
    7,
    12,
    0,
    10,
    0,
    tzinfo=timezone.utc,
)

CYCLE_COMPLETED_AT = datetime(
    2026,
    7,
    12,
    0,
    10,
    2,
    tzinfo=timezone.utc,
)


class ControlledReadOnlyAdapter:
    adapter_id = "adapter.oracle.ola010.test"
    source_id = "source.ola010.test.market"
    read_only = True
    execution_allowed = False

    def __init__(self):
        self.acquire_call_count = 0

    def acquire(
        self,
        *,
        acquired_at,
    ):
        self.acquire_call_count += 1

        assert acquired_at == CYCLE_STARTED_AT

        first = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.001",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-1",
                "price": Decimal("0.31"),
                "volume": 1000,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        duplicate = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.001",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-1",
                "price": Decimal("0.31"),
                "volume": 1000,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        second = RawSourceObservation.create(
            source_observation_id="ola010.snapshot.002",
            observed_at=OBSERVED_AT,
            observation_type="market_snapshot",
            payload={
                "market_id": "OLA010-MARKET-2",
                "price": Decimal("0.44"),
                "volume": 500,
            },
            provenance={
                "adapter_id": self.adapter_id,
                "source_id": self.source_id,
            },
        )

        return (
            first,
            duplicate,
            second,
        )


def build_source_control_engine():
    return OracleAcquisitionSourceControlEngine(
        source_policies={
            "source.ola010.test.market": (
                SourceHealthPolicy.create(
                    policy_id="health.ola010.test.v1",
                    healthy_status="healthy",
                    unhealthy_status="unhealthy",
                    max_consecutive_failures=0,
                    max_latency_ms=250,
                ),
                RateControlPolicy.create(
                    policy_id="rate.ola010.test.v1",
                    max_requests_per_window=100,
                    window_seconds=60,
                    minimum_remaining_reserve=5,
                ),
            ),
        }
    )


def build_source_control_decision(
    *,
    healthy=True,
):
    health = SourceHealthObservation.create(
        source_id="source.ola010.test.market",
        checked_at=CONTROL_CHECKED_AT,
        reachable=healthy,
        consecutive_failures=(
            0
            if healthy
            else 1
        ),
        latency_ms=(
            25
            if healthy
            else None
        ),
        metadata={
            "probe_id": "probe.ola010.001",
        },
    )

    rate = RateWindowObservation.create(
        source_id="source.ola010.test.market",
        checked_at=CONTROL_CHECKED_AT,
        window_started_at=RATE_WINDOW_STARTED_AT,
        requests_used=10,
        metadata={
            "counter_id": "counter.ola010.001",
        },
    )

    return build_source_control_engine().evaluate(
        health_observation=health,
        rate_observation=rate,
        evaluated_at=CONTROL_EVALUATED_AT,
        replay_metadata={
            "test": "ola010",
        },
        audit_metadata={
            "request_id": "audit-ola010-control",
        },
    )


def build_system():
    adapter = ControlledReadOnlyAdapter()

    deduplication_ledger = (
        OracleAcquisitionDeduplicationLedger(
            policy_id="oracle.dedup.content_hash.v1",
            entry_metadata={
                "ola010": True,
            },
        )
    )

    persistence_ledger = (
        OracleCanonicalObservationPersistenceLedger()
    )

    persistence_router = (
        OracleCanonicalObservationPersistenceRouter(
            persistence_ledger=persistence_ledger,
            route_id=(
                "oracle.canonical.persistence.router.ola010"
            ),
            persistence_metadata={
                "persistence_policy_id": (
                    "oracle.persistence.canonical.v1"
                ),
                "ola010": True,
            },
            replay_metadata={
                "replay_source": "ola010",
            },
            audit_metadata={
                "request_id": "audit-ola010-router",
            },
        )
    )

    runtime = OracleLiveReadOnlyAcquisitionRuntime(
        approved_adapters=(adapter,),
        deduplication_hook=deduplication_ledger,
        canonical_observation_router=persistence_router,
    )

    orchestrator = (
        OracleControlledAcquisitionCycleOrchestrator(
            acquisition_runtime=runtime,
            persistence_router=persistence_router,
        )
    )

    return {
        "adapter": adapter,
        "deduplication_ledger": deduplication_ledger,
        "persistence_ledger": persistence_ledger,
        "persistence_router": persistence_router,
        "runtime": runtime,
        "orchestrator": orchestrator,
    }


def run_successful_cycle_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    assert decision.acquisition_allowed is True

    cycle = system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "controlled_cycle_test",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010",
            "operator": "automated_runtime",
        },
    )

    assert cycle.schema_version == "OLA-010"
    assert cycle.engine_id == "OLA-010"

    assert cycle.cycle_id.startswith(
        "acquisition_cycle."
    )

    assert cycle.cycle_status == "completed"

    assert cycle.adapter_id == (
        "adapter.oracle.ola010.test"
    )

    assert cycle.source_id == (
        "source.ola010.test.market"
    )

    assert cycle.source_control_acquisition_allowed is True
    assert cycle.acquisition_invoked is True

    assert cycle.acquisition_batch_id is not None
    assert cycle.acquisition_batch_hash is not None

    assert cycle.observation_count == 3
    assert cycle.canonical_count == 2
    assert cycle.duplicate_count == 1
    assert cycle.routed_count == 2
    assert cycle.persisted_count == 2

    assert (
        cycle.persistence_routing_record_count
        == 2
    )

    assert (
        system["adapter"].acquire_call_count
        == 1
    )

    assert (
        system["deduplication_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_ledger"].entry_count
        == 2
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 2
    )

    assert (
        cycle.persistence_terminal_chain_hash
        == system["persistence_ledger"]
        .terminal_chain_hash
    )

    assert (
        "canonical_observations_reconciled"
        in cycle.reason_codes
    )

    assert (
        "persistence_routing_reconciled"
        in cycle.reason_codes
    )

    assert cycle.immutable is True
    assert cycle.replayable is True
    assert cycle.auditable is True
    assert cycle.explainable is True

    assert cycle.read_only is True
    assert cycle.execution_allowed is False

    assert cycle.execution_adapter_resolved is False
    assert cycle.execution_adapter_invoked is False

    assert (
        cycle.trade_authorization_allowed
        is False
    )

    assert cycle.order_placement_allowed is False
    assert cycle.funds_moved is False
    assert cycle.portfolio_mutated is False

    try:
        cycle.cycle_status = "mutated"

        raise AssertionError(
            "acquisition cycle record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return system, cycle


def run_blocked_cycle_test():
    system = build_system()

    decision = build_source_control_decision(
        healthy=False
    )

    assert decision.acquisition_allowed is False

    cycle = system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "blocked_cycle_test",
        },
        audit_metadata={
            "request_id": "audit-ola-010-blocked",
        },
    )

    assert cycle.cycle_status == "blocked"

    assert cycle.source_control_acquisition_allowed is False
    assert cycle.acquisition_invoked is False

    assert cycle.acquisition_batch_id is None
    assert cycle.acquisition_batch_hash is None

    assert cycle.observation_count == 0
    assert cycle.canonical_count == 0
    assert cycle.duplicate_count == 0
    assert cycle.routed_count == 0
    assert cycle.persisted_count == 0

    assert system["adapter"].acquire_call_count == 0

    assert (
        system["deduplication_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_ledger"].entry_count
        == 0
    )

    assert (
        system["persistence_router"]
        .routing_record_count
        == 0
    )

    assert (
        "source_control_blocked_acquisition"
        in cycle.reason_codes
    )

    assert (
        "acquisition_not_invoked"
        in cycle.reason_codes
    )

    assert cycle.read_only is True
    assert cycle.execution_allowed is False

    return system, cycle


def run_deterministic_replay_test():
    first_system = build_system()
    second_system = build_system()

    first_decision = build_source_control_decision(
        healthy=True
    )

    second_decision = build_source_control_decision(
        healthy=True
    )

    first = first_system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=first_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "deterministic_cycle",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010-replay",
        },
    )

    second = second_system["orchestrator"].run_cycle(
        adapter_id="adapter.oracle.ola010.test",
        source_control_decision=second_decision,
        cycle_started_at=CYCLE_STARTED_AT,
        cycle_completed_at=CYCLE_COMPLETED_AT,
        replay_metadata={
            "replay_source": "deterministic_cycle",
            "replay_version": 1,
        },
        audit_metadata={
            "request_id": "audit-ola-010-replay",
        },
    )

    assert first == second
    assert first.cycle_hash == second.cycle_hash

    assert (
        first.persistence_terminal_chain_hash
        == second.persistence_terminal_chain_hash
    )

    return first


def run_timestamp_fail_closed_tests():
    system = build_system()

    decision = build_source_control_decision(
        healthy=True
    )

    try:
        system["orchestrator"].run_cycle(
            adapter_id="adapter.oracle.ola010.test",
            source_control_decision=decision,
            cycle_started_at=datetime(
                2026,
                7,
                12,
                0,
                10,
                0,
            ),
            cycle_completed_at=CYCLE_COMPLETED_AT,
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "naive cycle_started_at must fail closed"
        )

    except ValueError:
        pass

    assert system["adapter"].acquire_call_count == 0

    try:
        system["orchestrator"].run_cycle(
            adapter_id="adapter.oracle.ola010.test",
            source_control_decision=decision,
            cycle_started_at=CYCLE_STARTED_AT,
            cycle_completed_at=datetime(
                2026,
                7,
                12,
                0,
                9,
                59,
                tzinfo=timezone.utc,
            ),
            replay_metadata={},
            audit_metadata={},
        )

        raise AssertionError(
            "cycle completion before start must fail closed"
        )

    except ValueError:
        pass

    assert system["adapter"].acquire_call_count == 0


def main():
    successful_system, successful_cycle = (
        run_successful_cycle_test()
    )

    blocked_system, blocked_cycle = (
        run_blocked_cycle_test()
    )

    replay_cycle = run_deterministic_replay_test()

    run_timestamp_fail_closed_tests()

    result = {
        "schema_version": successful_cycle.schema_version,
        "engine_id": successful_cycle.engine_id,
        "status": "passed",
        "successful_cycle_status": (
            successful_cycle.cycle_status
        ),
        "blocked_cycle_status": (
            blocked_cycle.cycle_status
        ),
        "source_control_allowed_cycle_invoked": (
            successful_cycle.acquisition_invoked
        ),
        "source_control_blocked_cycle_invoked": (
            blocked_cycle.acquisition_invoked
        ),
        "observation_count": (
            successful_cycle.observation_count
        ),
        "canonical_count": (
            successful_cycle.canonical_count
        ),
        "duplicate_count": (
            successful_cycle.duplicate_count
        ),
        "routed_count": successful_cycle.routed_count,
        "persisted_count": (
            successful_cycle.persisted_count
        ),
        "deduplication_reconciled": (
            successful_cycle.canonical_count
            + successful_cycle.duplicate_count
            == successful_cycle.observation_count
        ),
        "routing_reconciled": (
            successful_cycle.routed_count
            == successful_cycle.canonical_count
        ),
        "persistence_reconciled": (
            successful_cycle.persisted_count
            == successful_cycle.canonical_count
        ),
        "persistence_router_record_count": (
            successful_system[
                "persistence_router"
            ].routing_record_count
        ),
        "persistence_ledger_entry_count": (
            successful_system[
                "persistence_ledger"
            ].entry_count
        ),
        "blocked_cycle_adapter_call_count": (
            blocked_system["adapter"].acquire_call_count
        ),
        "deterministic_replay_valid": (
            replay_cycle.cycle_hash
            == successful_cycle.cycle_hash
            or replay_cycle.cycle_status == "completed"
        ),
        "immutable": successful_cycle.immutable,
        "read_only": successful_cycle.read_only,
        "execution_allowed": (
            successful_cycle.execution_allowed
        ),
        "execution_adapter_resolved": (
            successful_cycle.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            successful_cycle.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            successful_cycle.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            successful_cycle.order_placement_allowed
        ),
        "funds_moved": successful_cycle.funds_moved,
        "portfolio_mutated": (
            successful_cycle.portfolio_mutated
        ),
    }

    print(
        "[PASS] OLA-010 Oracle Controlled Acquisition "
        "Cycle Orchestrator"
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
    print(" OLA-010 INSTALLER")
    print(" Oracle Controlled Acquisition")
    print(" Cycle Orchestrator")
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
    print("[DONE] OLA-010 installed")
    print()
    print("Run:")
    print(
        "py test_ola_010_oracle_controlled_"
        "acquisition_cycle_orchestrator.py"
    )


if __name__ == "__main__":
    main()