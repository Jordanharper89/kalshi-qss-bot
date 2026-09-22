"""
OLA-017
Oracle PostgreSQL Shadow Acquisition Cycle Orchestrator

Production shadow-mode acquisition orchestration boundary.

Architecture:

OLA-002 SOURCE CONTROL
    |
OLA-014 POSTGRESQL BOOTSTRAP EVIDENCE
    |
OLA-016 APPROVED SHADOW SOURCE ADAPTER
    |
OLA-001 LIVE READ-ONLY ACQUISITION
    |
OLA-003 DEDUPLICATION
    |
OLA-015 POSTGRESQL PERSISTENCE ROUTER
    |
OLA-012 POSTGRESQL CANONICAL BACKEND
    |
OLA-017 IMMUTABLE SHADOW CYCLE RECORD

Why OLA-017 exists:

OLA-010 intentionally binds the original OLA-009 in-memory persistence
router and OLA-008 ledger path.

OLA-017 does not patch or weaken OLA-010.

OLA-017 defines the production PostgreSQL shadow-cycle boundary against
the OLA-015 router and OLA-012 backend.

Permanent rules:

- Source-control approval is required.
- PostgreSQL bootstrap evidence is required.
- PostgreSQL bootstrap must be live-write ready.
- Bootstrap backend identity must match OLA-015.
- OLA-016 adapter must remain in shadow mode.
- OLA-016 alerts must remain disabled.
- OLA-016 Q Series intake must remain disabled.
- Blocked source control never invokes acquisition.
- Acquisition is performed only through OLA-001.
- Canonical replay hashing remains owned by OLA-001.
- Deduplication remains owned by the OLA-001 configured hook.
- Production persistence routing remains owned by OLA-015.
- Persistence acceptance requires committed PostgreSQL evidence.
- Routing counts must reconcile.
- Persistence sequence deltas must reconcile.
- PostgreSQL terminal chain state must advance for canonical writes.
- Duplicate-only cycles must not advance PostgreSQL chain state.
- Caller supplies cycle timestamps.
- Cycle records are immutable.
- Cycle records are replayable.
- Cycle records are auditable.
- Cycle records are explainable.
- Shadow mode is mandatory.
- Alerts are disabled.
- Q Series intake is disabled.
- Oracle remains read-only.
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
    AcquisitionBatchRecord,
    JSONValue,
    OracleLiveReadOnlyAcquisitionRuntime,
)

from .oracle_acquisition_source_control_engine import (
    SourceControlDecisionRecord,
)

from .oracle_postgresql_canonical_observation_persistence_backend import (
    BACKEND_ID,
)

from .oracle_postgresql_canonical_observation_persistence_router import (
    OraclePostgreSQLCanonicalObservationPersistenceRouter,
)

from .oracle_postgresql_production_bootstrap_migration_gate import (
    PostgreSQLProductionBootstrapRecord,
)

from .oracle_kalshi_public_market_shadow_source_adapter import (
    ADAPTER_ID as KALSHI_SHADOW_ADAPTER_ID,
    SOURCE_ID as KALSHI_SOURCE_ID,
    OracleKalshiPublicMarketShadowSourceAdapter,
)


SCHEMA_VERSION = "OLA-017"
ENGINE_ID = "OLA-017"

SHADOW_CYCLE_RECORD_TYPE = (
    "oracle_postgresql_shadow_acquisition_cycle_record"
)


class PostgreSQLShadowCycleContractError(ValueError):
    """Raised when shadow-cycle contract data is malformed."""


class PostgreSQLShadowCycleCompatibilityError(
    PostgreSQLShadowCycleContractError
):
    """Raised when integrated shadow components are incompatible."""


class PostgreSQLShadowCycleReconciliationError(RuntimeError):
    """Raised when acquisition and PostgreSQL evidence do not reconcile."""


class PostgreSQLShadowCycleInvariantError(RuntimeError):
    """Raised when permanent shadow-cycle invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostgreSQLShadowCycleContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostgreSQLShadowCycleContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PostgreSQLShadowCycleContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PostgreSQLShadowCycleContractError(
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
            raise PostgreSQLShadowCycleContractError(
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
                raise PostgreSQLShadowCycleContractError(
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

    raise PostgreSQLShadowCycleContractError(
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
        raise PostgreSQLShadowCycleContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise PostgreSQLShadowCycleContractError(
            f"{field_name} must canonicalize to a mapping"
        )

    result = tuple(
        (key, canonical[key])
        for key in sorted(canonical)
    )

    forbidden_keys = {
        "password",
        "passwd",
        "secret",
        "dsn",
        "database_url",
        "connection_string",
        "uri",
    }

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise PostgreSQLShadowCycleContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )

    return result


def _mapping_from_immutable(
    value: tuple[tuple[str, JSONValue], ...],
) -> dict[str, JSONValue]:
    return {
        key: item
        for key, item in value
    }


@dataclass(frozen=True, slots=True)
class PostgreSQLShadowAcquisitionCycleRecord:
    schema_version: str
    engine_id: str
    cycle_id: str
    cycle_status: str
    adapter_id: str
    source_id: str
    backend_id: str
    bootstrap_id: str
    bootstrap_hash: str
    source_control_decision_hash: str
    cycle_started_at: datetime
    cycle_completed_at: datetime
    source_control_acquisition_allowed: bool
    bootstrap_live_write_ready: bool
    shadow_mode: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    acquisition_invoked: bool
    acquisition_batch_id: str | None
    acquisition_batch_hash: str | None
    observation_count: int
    canonical_count: int
    duplicate_count: int
    routed_count: int
    postgresql_routing_record_delta: int
    first_persistence_sequence_number: int | None
    last_persistence_sequence_number: int | None
    prior_terminal_chain_hash: str
    terminal_chain_hash: str
    terminal_chain_advanced: bool
    persistence_reconciled: bool
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
            "backend_id": self.backend_id,
            "bootstrap_id": self.bootstrap_id,
            "bootstrap_hash": self.bootstrap_hash,
            "source_control_decision_hash": (
                self.source_control_decision_hash
            ),
            "cycle_started_at": (
                self.cycle_started_at.isoformat()
            ),
            "cycle_completed_at": (
                self.cycle_completed_at.isoformat()
            ),
            "source_control_acquisition_allowed": (
                self.source_control_acquisition_allowed
            ),
            "bootstrap_live_write_ready": (
                self.bootstrap_live_write_ready
            ),
            "shadow_mode": self.shadow_mode,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
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
            "postgresql_routing_record_delta": (
                self.postgresql_routing_record_delta
            ),
            "first_persistence_sequence_number": (
                self.first_persistence_sequence_number
            ),
            "last_persistence_sequence_number": (
                self.last_persistence_sequence_number
            ),
            "prior_terminal_chain_hash": (
                self.prior_terminal_chain_hash
            ),
            "terminal_chain_hash": self.terminal_chain_hash,
            "terminal_chain_advanced": (
                self.terminal_chain_advanced
            ),
            "persistence_reconciled": (
                self.persistence_reconciled
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


class OraclePostgreSQLShadowAcquisitionCycleOrchestrator:
    """
    Coordinates one controlled PostgreSQL-backed Oracle shadow cycle.

    This class does not replace OLA-010.

    OLA-010 remains the orchestration contract for the original OLA-009
    and OLA-008 in-memory persistence path.

    OLA-017 owns the production PostgreSQL shadow path.
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
        postgresql_router: (
            OraclePostgreSQLCanonicalObservationPersistenceRouter
        ),
        shadow_adapter: OracleKalshiPublicMarketShadowSourceAdapter,
        bootstrap_record: PostgreSQLProductionBootstrapRecord,
    ) -> None:
        if not isinstance(
            acquisition_runtime,
            OracleLiveReadOnlyAcquisitionRuntime,
        ):
            raise PostgreSQLShadowCycleContractError(
                "acquisition_runtime must be "
                "OracleLiveReadOnlyAcquisitionRuntime"
            )

        if not isinstance(
            postgresql_router,
            OraclePostgreSQLCanonicalObservationPersistenceRouter,
        ):
            raise PostgreSQLShadowCycleContractError(
                "postgresql_router must be "
                "OraclePostgreSQLCanonicalObservationPersistenceRouter"
            )

        if not isinstance(
            shadow_adapter,
            OracleKalshiPublicMarketShadowSourceAdapter,
        ):
            raise PostgreSQLShadowCycleContractError(
                "shadow_adapter must be "
                "OracleKalshiPublicMarketShadowSourceAdapter"
            )

        if not isinstance(
            bootstrap_record,
            PostgreSQLProductionBootstrapRecord,
        ):
            raise PostgreSQLShadowCycleContractError(
                "bootstrap_record must be "
                "PostgreSQLProductionBootstrapRecord"
            )

        self._acquisition_runtime = acquisition_runtime
        self._postgresql_router = postgresql_router
        self._shadow_adapter = shadow_adapter
        self._bootstrap_record = bootstrap_record

        self._validate_component_compatibility()

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
            raise PostgreSQLShadowCycleInvariantError(
                "Oracle PostgreSQL shadow-cycle invariants violated"
            )

        if self._acquisition_runtime.read_only is not True:
            raise PostgreSQLShadowCycleInvariantError(
                "acquisition runtime lost read_only invariant"
            )

        if (
            self._acquisition_runtime.execution_allowed
            is not False
        ):
            raise PostgreSQLShadowCycleInvariantError(
                "acquisition runtime gained execution capability"
            )

        if self._postgresql_router.read_only is not True:
            raise PostgreSQLShadowCycleInvariantError(
                "PostgreSQL router lost read_only invariant"
            )

        if (
            self._postgresql_router.execution_allowed
            is not False
        ):
            raise PostgreSQLShadowCycleInvariantError(
                "PostgreSQL router gained execution capability"
            )

        if self._shadow_adapter.read_only is not True:
            raise PostgreSQLShadowCycleInvariantError(
                "shadow adapter lost read_only invariant"
            )

        if self._shadow_adapter.execution_allowed is not False:
            raise PostgreSQLShadowCycleInvariantError(
                "shadow adapter gained execution capability"
            )

        if self._shadow_adapter.shadow_mode is not True:
            raise PostgreSQLShadowCycleInvariantError(
                "Kalshi adapter left shadow mode"
            )

        if self._shadow_adapter.alerts_allowed is not False:
            raise PostgreSQLShadowCycleInvariantError(
                "shadow adapter gained alert capability"
            )

        if (
            self._shadow_adapter.qseries_intake_allowed
            is not False
        ):
            raise PostgreSQLShadowCycleInvariantError(
                "shadow adapter gained Q Series intake capability"
            )

    def _validate_component_compatibility(self) -> None:
        if (
            self._shadow_adapter.adapter_id
            != KALSHI_SHADOW_ADAPTER_ID
        ):
            raise PostgreSQLShadowCycleCompatibilityError(
                "shadow adapter identity is incompatible"
            )

        if self._shadow_adapter.source_id != KALSHI_SOURCE_ID:
            raise PostgreSQLShadowCycleCompatibilityError(
                "shadow source identity is incompatible"
            )

        backend = self._postgresql_router.persistence_backend

        if backend.backend_id != BACKEND_ID:
            raise PostgreSQLShadowCycleCompatibilityError(
                "PostgreSQL router backend identity is incompatible"
            )

        if self._bootstrap_record.bootstrap_status != "passed":
            raise PostgreSQLShadowCycleCompatibilityError(
                "PostgreSQL bootstrap gate has not passed"
            )

        if (
            self._bootstrap_record.live_write_ready
            is not True
        ):
            raise PostgreSQLShadowCycleCompatibilityError(
                "PostgreSQL bootstrap is not live-write ready"
            )

        if (
            self._bootstrap_record.chain_state_compatible
            is not True
        ):
            raise PostgreSQLShadowCycleCompatibilityError(
                "PostgreSQL chain state is incompatible"
            )

        if (
            self._bootstrap_record.backend_id
            != backend.backend_id
        ):
            raise PostgreSQLShadowCycleCompatibilityError(
                "bootstrap and router backend identity mismatch"
            )

        if self._bootstrap_record.read_only is not True:
            raise PostgreSQLShadowCycleCompatibilityError(
                "bootstrap evidence lost read_only invariant"
            )

        if self._bootstrap_record.execution_allowed is not False:
            raise PostgreSQLShadowCycleCompatibilityError(
                "bootstrap evidence gained execution capability"
            )

    @property
    def acquisition_runtime(
        self,
    ) -> OracleLiveReadOnlyAcquisitionRuntime:
        return self._acquisition_runtime

    @property
    def postgresql_router(
        self,
    ) -> OraclePostgreSQLCanonicalObservationPersistenceRouter:
        return self._postgresql_router

    @property
    def shadow_adapter(
        self,
    ) -> OracleKalshiPublicMarketShadowSourceAdapter:
        return self._shadow_adapter

    @property
    def bootstrap_record(
        self,
    ) -> PostgreSQLProductionBootstrapRecord:
        return self._bootstrap_record

    def run_cycle(
        self,
        *,
        source_control_decision: SourceControlDecisionRecord,
        cycle_started_at: datetime,
        cycle_completed_at: datetime,
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> PostgreSQLShadowAcquisitionCycleRecord:
        self._assert_invariants()

        self._validate_component_compatibility()

        if not isinstance(
            source_control_decision,
            SourceControlDecisionRecord,
        ):
            raise PostgreSQLShadowCycleContractError(
                "source_control_decision must be "
                "SourceControlDecisionRecord"
            )

        normalized_started_at = _require_aware_datetime(
            cycle_started_at,
            "cycle_started_at",
        )

        normalized_completed_at = _require_aware_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )

        if normalized_completed_at < normalized_started_at:
            raise PostgreSQLShadowCycleContractError(
                "cycle_completed_at cannot be before "
                "cycle_started_at"
            )

        if (
            source_control_decision.evaluated_at
            > normalized_started_at
        ):
            raise PostgreSQLShadowCycleContractError(
                "source-control decision cannot be evaluated after "
                "cycle_started_at"
            )

        if (
            source_control_decision.source_id
            != self._shadow_adapter.source_id
        ):
            raise PostgreSQLShadowCycleCompatibilityError(
                "source-control source identity mismatch"
            )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        backend = self._postgresql_router.persistence_backend

        prior_terminal_chain_hash = (
            backend.terminal_chain_hash()
        )

        routing_count_before = (
            self._postgresql_router.routing_record_count
        )

        cycle_id = "postgresql_shadow_cycle." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "postgresql_shadow_cycle_identity",
                "adapter_id": self._shadow_adapter.adapter_id,
                "source_id": self._shadow_adapter.source_id,
                "backend_id": backend.backend_id,
                "bootstrap_id": self._bootstrap_record.bootstrap_id,
                "bootstrap_hash": self._bootstrap_record.bootstrap_hash,
                "source_control_decision_hash": (
                    source_control_decision.decision_hash
                ),
                "cycle_started_at": normalized_started_at,
                "cycle_completed_at": normalized_completed_at,
                "replay_metadata": _mapping_from_immutable(
                    immutable_replay_metadata
                ),
                "audit_metadata": _mapping_from_immutable(
                    immutable_audit_metadata
                ),
            }
        )

        if not source_control_decision.acquisition_allowed:
            return self._build_record(
                cycle_id=cycle_id,
                cycle_status="blocked",
                source_control_decision=source_control_decision,
                cycle_started_at=normalized_started_at,
                cycle_completed_at=normalized_completed_at,
                acquisition=None,
                routing_count_before=routing_count_before,
                prior_terminal_chain_hash=(
                    prior_terminal_chain_hash
                ),
                reason_codes=(
                    "source_control_blocked_acquisition",
                    "shadow_acquisition_not_invoked",
                    "postgresql_persistence_not_invoked",
                    "cycle_blocked_fail_closed",
                ),
                replay_metadata=immutable_replay_metadata,
                audit_metadata=immutable_audit_metadata,
            )

        acquisition = self._acquisition_runtime.acquire(
            adapter_id=self._shadow_adapter.adapter_id,
            acquired_at=normalized_started_at,
            health_evidence=(
                source_control_decision.health_evidence
            ),
            rate_control_evidence=(
                source_control_decision.rate_control_evidence
            ),
            replay_metadata={
                "orchestrator_engine_id": ENGINE_ID,
                "cycle_id": cycle_id,
                "shadow_mode": True,
                "alerts_allowed": False,
                "qseries_intake_allowed": False,
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

        self._reconcile_acquisition(
            acquisition=acquisition,
            source_control_decision=source_control_decision,
            routing_count_before=routing_count_before,
            prior_terminal_chain_hash=(
                prior_terminal_chain_hash
            ),
        )

        return self._build_record(
            cycle_id=cycle_id,
            cycle_status="completed",
            source_control_decision=source_control_decision,
            cycle_started_at=normalized_started_at,
            cycle_completed_at=normalized_completed_at,
            acquisition=acquisition,
            routing_count_before=routing_count_before,
            prior_terminal_chain_hash=(
                prior_terminal_chain_hash
            ),
            reason_codes=(
                "source_control_allowed_shadow_acquisition",
                "bootstrap_live_write_ready_verified",
                "shadow_adapter_invariants_verified",
                "ola_001_acquisition_completed",
                "canonical_replay_hashing_owned_by_ola_001",
                "deduplication_reconciled",
                "postgresql_routing_reconciled",
                "postgresql_chain_state_reconciled",
                "alerts_remain_disabled",
                "qseries_intake_remains_disabled",
                "shadow_cycle_completed",
            ),
            replay_metadata=immutable_replay_metadata,
            audit_metadata=immutable_audit_metadata,
        )

    def _reconcile_acquisition(
        self,
        *,
        acquisition: AcquisitionBatchRecord,
        source_control_decision: SourceControlDecisionRecord,
        routing_count_before: int,
        prior_terminal_chain_hash: str,
    ) -> None:
        if not isinstance(
            acquisition,
            AcquisitionBatchRecord,
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "acquisition runtime returned incompatible record"
            )

        if acquisition.status != "passed":
            raise PostgreSQLShadowCycleReconciliationError(
                "acquisition batch status did not pass"
            )

        if acquisition.source_id != self._shadow_adapter.source_id:
            raise PostgreSQLShadowCycleReconciliationError(
                "acquisition source identity mismatch"
            )

        if (
            acquisition.source_id
            != source_control_decision.source_id
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "source-control and acquisition source mismatch"
            )

        if (
            acquisition.health_evidence.evidence_hash
            != source_control_decision.health_evidence.evidence_hash
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "health evidence mismatch"
            )

        if (
            acquisition.rate_control_evidence.evidence_hash
            != source_control_decision
            .rate_control_evidence
            .evidence_hash
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "rate-control evidence mismatch"
            )

        if (
            acquisition.canonical_count
            + acquisition.duplicate_count
            != acquisition.observation_count
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "observation count reconciliation failed"
            )

        if acquisition.routed_count != acquisition.canonical_count:
            raise PostgreSQLShadowCycleReconciliationError(
                "all non-duplicate canonical observations must route"
            )

        routing_count_after = (
            self._postgresql_router.routing_record_count
        )

        routing_delta = (
            routing_count_after
            - routing_count_before
        )

        if routing_delta != acquisition.routed_count:
            raise PostgreSQLShadowCycleReconciliationError(
                "PostgreSQL routing record delta does not match "
                "acquisition routed_count"
            )

        routing_records = (
            self._postgresql_router.routing_records[
                routing_count_before:
                routing_count_after
            ]
        )

        if len(routing_records) != acquisition.canonical_count:
            raise PostgreSQLShadowCycleReconciliationError(
                "PostgreSQL persistence record count does not match "
                "canonical_count"
            )

        canonical_observation_ids = tuple(
            observation_record.observation.observation_id
            for observation_record in acquisition.observations
            if not observation_record.deduplication.duplicate
        )

        routed_observation_ids = tuple(
            record.observation_id
            for record in routing_records
        )

        if (
            routed_observation_ids
            != canonical_observation_ids
        ):
            raise PostgreSQLShadowCycleReconciliationError(
                "PostgreSQL routed observation order or identity "
                "does not match canonical acquisition order"
            )

        for record in routing_records:
            if record.persistence_committed is not True:
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record is not committed"
                )

            if record.persistence_atomic is not True:
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record is not atomic"
                )

            if record.persistence_verified is not True:
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record is not verified"
                )

            if record.routing_accepted is not True:
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record was not accepted"
                )

            if record.read_only is not True:
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record lost read_only invariant"
                )

            false_invariants = {
                "execution_allowed": record.execution_allowed,
                "execution_adapter_resolved": (
                    record.execution_adapter_resolved
                ),
                "execution_adapter_invoked": (
                    record.execution_adapter_invoked
                ),
                "trade_authorization_allowed": (
                    record.trade_authorization_allowed
                ),
                "order_placement_allowed": (
                    record.order_placement_allowed
                ),
                "funds_moved": record.funds_moved,
                "portfolio_mutated": record.portfolio_mutated,
            }

            if any(false_invariants.values()):
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL routing record gained execution "
                    "capability"
                )

        terminal_chain_hash = (
            self._postgresql_router
            .persistence_backend
            .terminal_chain_hash()
        )

        if acquisition.canonical_count > 0:
            if not routing_records:
                raise PostgreSQLShadowCycleReconciliationError(
                    "canonical observations lack PostgreSQL records"
                )

            if (
                routing_records[0].prior_terminal_chain_hash
                != prior_terminal_chain_hash
            ):
                raise PostgreSQLShadowCycleReconciliationError(
                    "first PostgreSQL chain link does not preserve "
                    "prior terminal hash"
                )

            for previous, current in zip(
                routing_records,
                routing_records[1:],
            ):
                if (
                    current.prior_terminal_chain_hash
                    != previous.terminal_chain_hash
                ):
                    raise PostgreSQLShadowCycleReconciliationError(
                        "PostgreSQL routing chain continuity failed"
                    )

            if (
                terminal_chain_hash
                != routing_records[-1].terminal_chain_hash
            ):
                raise PostgreSQLShadowCycleReconciliationError(
                    "PostgreSQL terminal chain state mismatch"
                )

            if terminal_chain_hash == prior_terminal_chain_hash:
                raise PostgreSQLShadowCycleReconciliationError(
                    "canonical writes did not advance PostgreSQL chain"
                )

        else:
            if terminal_chain_hash != prior_terminal_chain_hash:
                raise PostgreSQLShadowCycleReconciliationError(
                    "duplicate-only or empty cycle advanced "
                    "PostgreSQL chain state"
                )

    def _build_record(
        self,
        *,
        cycle_id: str,
        cycle_status: str,
        source_control_decision: SourceControlDecisionRecord,
        cycle_started_at: datetime,
        cycle_completed_at: datetime,
        acquisition: AcquisitionBatchRecord | None,
        routing_count_before: int,
        prior_terminal_chain_hash: str,
        reason_codes: tuple[str, ...],
        replay_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
        audit_metadata: tuple[
            tuple[str, JSONValue],
            ...
        ],
    ) -> PostgreSQLShadowAcquisitionCycleRecord:
        backend = self._postgresql_router.persistence_backend

        terminal_chain_hash = backend.terminal_chain_hash()

        routing_count_after = (
            self._postgresql_router.routing_record_count
        )

        routing_delta = (
            routing_count_after
            - routing_count_before
        )

        new_records = (
            self._postgresql_router.routing_records[
                routing_count_before:
                routing_count_after
            ]
        )

        first_sequence_number = (
            None
            if not new_records
            else new_records[0].persistence_sequence_number
        )

        last_sequence_number = (
            None
            if not new_records
            else new_records[-1].persistence_sequence_number
        )

        terminal_chain_advanced = (
            terminal_chain_hash
            != prior_terminal_chain_hash
        )

        persistence_reconciled = (
            routing_delta
            == (
                0
                if acquisition is None
                else acquisition.canonical_count
            )
        )

        provisional = PostgreSQLShadowAcquisitionCycleRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            cycle_id=cycle_id,
            cycle_status=cycle_status,
            adapter_id=self._shadow_adapter.adapter_id,
            source_id=self._shadow_adapter.source_id,
            backend_id=backend.backend_id,
            bootstrap_id=self._bootstrap_record.bootstrap_id,
            bootstrap_hash=self._bootstrap_record.bootstrap_hash,
            source_control_decision_hash=(
                source_control_decision.decision_hash
            ),
            cycle_started_at=cycle_started_at,
            cycle_completed_at=cycle_completed_at,
            source_control_acquisition_allowed=(
                source_control_decision.acquisition_allowed
            ),
            bootstrap_live_write_ready=(
                self._bootstrap_record.live_write_ready
            ),
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            acquisition_invoked=(
                acquisition is not None
            ),
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
            postgresql_routing_record_delta=(
                routing_delta
            ),
            first_persistence_sequence_number=(
                first_sequence_number
            ),
            last_persistence_sequence_number=(
                last_sequence_number
            ),
            prior_terminal_chain_hash=(
                prior_terminal_chain_hash
            ),
            terminal_chain_hash=terminal_chain_hash,
            terminal_chain_advanced=terminal_chain_advanced,
            persistence_reconciled=persistence_reconciled,
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
                "record_type": SHADOW_CYCLE_RECORD_TYPE,
                "cycle_record": provisional.to_canonical_dict(
                    include_cycle_hash=False
                ),
            }
        )

        return PostgreSQLShadowAcquisitionCycleRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            cycle_id=provisional.cycle_id,
            cycle_status=provisional.cycle_status,
            adapter_id=provisional.adapter_id,
            source_id=provisional.source_id,
            backend_id=provisional.backend_id,
            bootstrap_id=provisional.bootstrap_id,
            bootstrap_hash=provisional.bootstrap_hash,
            source_control_decision_hash=(
                provisional.source_control_decision_hash
            ),
            cycle_started_at=provisional.cycle_started_at,
            cycle_completed_at=provisional.cycle_completed_at,
            source_control_acquisition_allowed=(
                provisional.source_control_acquisition_allowed
            ),
            bootstrap_live_write_ready=True,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
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
            postgresql_routing_record_delta=(
                provisional.postgresql_routing_record_delta
            ),
            first_persistence_sequence_number=(
                provisional.first_persistence_sequence_number
            ),
            last_persistence_sequence_number=(
                provisional.last_persistence_sequence_number
            ),
            prior_terminal_chain_hash=(
                provisional.prior_terminal_chain_hash
            ),
            terminal_chain_hash=(
                provisional.terminal_chain_hash
            ),
            terminal_chain_advanced=(
                provisional.terminal_chain_advanced
            ),
            persistence_reconciled=(
                provisional.persistence_reconciled
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
    "PostgreSQLShadowCycleContractError",
    "PostgreSQLShadowCycleCompatibilityError",
    "PostgreSQLShadowCycleReconciliationError",
    "PostgreSQLShadowCycleInvariantError",
    "PostgreSQLShadowAcquisitionCycleRecord",
    "OraclePostgreSQLShadowAcquisitionCycleOrchestrator",
    "canonical_json",
    "stable_hash",
]
