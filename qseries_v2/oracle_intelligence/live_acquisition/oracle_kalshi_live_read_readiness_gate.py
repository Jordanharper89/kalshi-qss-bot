"""
OLA-018
Oracle Kalshi Live Read Readiness Gate

FINAL PROVEN OLA-002 CONTRACT REWRITE

Architecture:

ONE KALSHI PUBLIC GET /markets
    |
OLA-016 SOURCE HEALTH PROBE
    |
SOURCE HEALTH OBSERVATION
    |
RATE WINDOW OBSERVATION
    |
OLA-002 SOURCE CONTROL ENGINE
    |
AUTHORITATIVE SourceControlDecisionRecord
    |
DECISION acquisition_allowed
DECISION reason_codes
HEALTH EVIDENCE identity/hash
RATE EVIDENCE identity/hash
    |
OLA-018 READINESS RECORD
    |
OLA-017 SHADOW CYCLE ENTRY ELIGIBLE

Proven OLA-002 contract consumed by OLA-018:

SourceControlDecisionRecord:
- source_id
- acquisition_allowed
- reason_codes
- decision_hash
- health_evidence
- rate_control_evidence
- read_only
- execution_allowed
- trade_authorization_allowed
- order_placement_allowed
- execution_adapter_invocation_allowed
- funds_moved
- portfolio_mutated

Child evidence records:
- source_id
- evidence_hash

OLA-018 does not inspect any other child evidence fields.

Permanent rules:

- One public source-health GET per readiness evaluation.
- OLA-016 validates the public source response contract.
- OLA-002 is authoritative for acquisition permission.
- OLA-002 reason codes explain health and rate approval.
- Child evidence hashes preserve canonical provenance.
- Shadow mode is mandatory.
- Alerts remain disabled.
- Q Series intake remains disabled.
- Continuous polling is not started.
- adapter.acquire() is not called.
- Canonical observations are not created.
- Deduplication is not mutated.
- PostgreSQL persistence is not invoked.
- No alert record is created.
- No Q Series intake record is created.
- Caller supplies deterministic timestamps.
- Caller supplies measured latency evidence.
- Canonical stable hashing is used.
- repr() is never used.
- Oracle remains permanently read-only.
- No execution adapter is resolved or invoked.
- No trade authorization exists.
- No order is placed.
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
    JSONValue,
)

from .oracle_acquisition_source_control_engine import (
    OracleAcquisitionSourceControlEngine,
    RateWindowObservation,
    SourceControlDecisionRecord,
    SourceHealthObservation,
)

from .oracle_kalshi_public_market_shadow_source_adapter import (
    ADAPTER_ID,
    ALERTS_ALLOWED,
    MARKETS_PATH,
    PRODUCTION_BASE_URL,
    Q_SERIES_INTAKE_ALLOWED,
    SHADOW_MODE,
    SOURCE_ID,
    OracleKalshiPublicMarketShadowSourceAdapter,
)


SCHEMA_VERSION = "OLA-018"
ENGINE_ID = "OLA-018"

READINESS_RECORD_TYPE = (
    "oracle_kalshi_live_read_readiness_record"
)

HEALTH_APPROVAL_REASON_CODES = frozenset(
    {
        "source_reachable",
        "latency_within_policy",
        "consecutive_failures_within_policy",
    }
)

RATE_APPROVAL_REASON_CODES = frozenset(
    {
        "rate_usage_within_limit",
        "rate_reserve_preserved",
    }
)

FINAL_APPROVAL_REASON_CODE = "acquisition_allowed"


class KalshiLiveReadReadinessContractError(ValueError):
    """Raised when readiness contract data is malformed."""


class KalshiLiveReadReadinessFailure(RuntimeError):
    """Raised when live-read readiness fails closed."""


class KalshiLiveReadReadinessInvariantError(RuntimeError):
    """Raised when permanent readiness invariants are violated."""


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise KalshiLiveReadReadinessContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise KalshiLiveReadReadinessContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise KalshiLiveReadReadinessContractError(
            f"{field_name} must be an int"
        )

    if value < 0:
        raise KalshiLiveReadReadinessContractError(
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
            raise KalshiLiveReadReadinessContractError(
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
                raise KalshiLiveReadReadinessContractError(
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

    raise KalshiLiveReadReadinessContractError(
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
        raise KalshiLiveReadReadinessContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(value)

    if not isinstance(canonical, dict):
        raise KalshiLiveReadReadinessContractError(
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
        "api_key",
        "private_key",
        "signing_key",
        "dsn",
        "database_url",
        "connection_string",
        "uri",
    }

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise KalshiLiveReadReadinessContractError(
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
class KalshiLiveReadReadinessRecord:
    schema_version: str
    engine_id: str
    readiness_id: str
    readiness_status: str
    adapter_id: str
    source_id: str
    source_base_url: str
    source_endpoint: str
    http_method: str
    checked_at: datetime
    evaluated_at: datetime
    public_endpoint: bool
    authentication_used: bool
    live_get_request_count: int
    source_contract_valid: bool
    source_probe_health_status: str
    source_reachable: bool
    source_latency_ms: int
    source_health_evidence_hash: str
    rate_control_evidence_hash: str
    source_control_decision_hash: str
    source_control_reason_codes: tuple[str, ...]
    health_policy_evidence_present: bool
    rate_policy_evidence_present: bool
    source_control_acquisition_allowed: bool
    shadow_mode: bool
    alerts_allowed: bool
    qseries_intake_allowed: bool
    live_shadow_cycle_entry_ready: bool
    continuous_polling_started: bool
    acquisition_performed: bool
    canonical_observation_created: bool
    persistence_invoked: bool
    alert_created: bool
    qseries_intake_record_created: bool
    reason_codes: tuple[str, ...]
    readiness_metadata: tuple[
        tuple[str, JSONValue],
        ...
    ]
    readiness_hash: str
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
        include_readiness_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "readiness_id": self.readiness_id,
            "readiness_status": self.readiness_status,
            "adapter_id": self.adapter_id,
            "source_id": self.source_id,
            "source_base_url": self.source_base_url,
            "source_endpoint": self.source_endpoint,
            "http_method": self.http_method,
            "checked_at": self.checked_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat(),
            "public_endpoint": self.public_endpoint,
            "authentication_used": self.authentication_used,
            "live_get_request_count": self.live_get_request_count,
            "source_contract_valid": self.source_contract_valid,
            "source_probe_health_status": (
                self.source_probe_health_status
            ),
            "source_reachable": self.source_reachable,
            "source_latency_ms": self.source_latency_ms,
            "source_health_evidence_hash": (
                self.source_health_evidence_hash
            ),
            "rate_control_evidence_hash": (
                self.rate_control_evidence_hash
            ),
            "source_control_decision_hash": (
                self.source_control_decision_hash
            ),
            "source_control_reason_codes": list(
                self.source_control_reason_codes
            ),
            "health_policy_evidence_present": (
                self.health_policy_evidence_present
            ),
            "rate_policy_evidence_present": (
                self.rate_policy_evidence_present
            ),
            "source_control_acquisition_allowed": (
                self.source_control_acquisition_allowed
            ),
            "shadow_mode": self.shadow_mode,
            "alerts_allowed": self.alerts_allowed,
            "qseries_intake_allowed": (
                self.qseries_intake_allowed
            ),
            "live_shadow_cycle_entry_ready": (
                self.live_shadow_cycle_entry_ready
            ),
            "continuous_polling_started": (
                self.continuous_polling_started
            ),
            "acquisition_performed": self.acquisition_performed,
            "canonical_observation_created": (
                self.canonical_observation_created
            ),
            "persistence_invoked": self.persistence_invoked,
            "alert_created": self.alert_created,
            "qseries_intake_record_created": (
                self.qseries_intake_record_created
            ),
            "reason_codes": list(self.reason_codes),
            "readiness_metadata": _mapping_from_immutable(
                self.readiness_metadata
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

        if include_readiness_hash:
            result["readiness_hash"] = self.readiness_hash

        return result


class OracleKalshiLiveReadReadinessGate:
    """
    Execute one OLA-016 source-health probe and consume only the proven
    SourceControlDecisionRecord boundary from OLA-002.
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
        shadow_adapter: OracleKalshiPublicMarketShadowSourceAdapter,
        source_control_engine: OracleAcquisitionSourceControlEngine,
    ) -> None:
        if not isinstance(
            shadow_adapter,
            OracleKalshiPublicMarketShadowSourceAdapter,
        ):
            raise KalshiLiveReadReadinessContractError(
                "shadow_adapter must be "
                "OracleKalshiPublicMarketShadowSourceAdapter"
            )

        if not isinstance(
            source_control_engine,
            OracleAcquisitionSourceControlEngine,
        ):
            raise KalshiLiveReadReadinessContractError(
                "source_control_engine must be "
                "OracleAcquisitionSourceControlEngine"
            )

        self._shadow_adapter = shadow_adapter
        self._source_control_engine = source_control_engine

        self._validate_adapter_boundary()
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
            raise KalshiLiveReadReadinessInvariantError(
                "Kalshi live-read readiness invariants violated"
            )

    def _validate_adapter_boundary(self) -> None:
        if self._shadow_adapter.adapter_id != ADAPTER_ID:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi shadow adapter identity mismatch"
            )

        if self._shadow_adapter.source_id != SOURCE_ID:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi source identity mismatch"
            )

        if self._shadow_adapter.read_only is not True:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi adapter lost read_only invariant"
            )

        if self._shadow_adapter.execution_allowed is not False:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi adapter gained execution capability"
            )

        if self._shadow_adapter.shadow_mode is not SHADOW_MODE:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi adapter is not in shadow mode"
            )

        if self._shadow_adapter.alerts_allowed is not ALERTS_ALLOWED:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi alert boundary is incompatible"
            )

        if (
            self._shadow_adapter.qseries_intake_allowed
            is not Q_SERIES_INTAKE_ALLOWED
        ):
            raise KalshiLiveReadReadinessFailure(
                "Kalshi Q Series intake boundary is incompatible"
            )

    def evaluate(
        self,
        *,
        checked_at: datetime,
        evaluated_at: datetime,
        measured_latency_ms: int,
        consecutive_failures: int,
        rate_window_observation: RateWindowObservation,
        readiness_metadata: Mapping[str, Any],
        replay_metadata: Mapping[str, Any],
        audit_metadata: Mapping[str, Any],
    ) -> KalshiLiveReadReadinessRecord:
        self._assert_invariants()
        self._validate_adapter_boundary()

        normalized_checked_at = _require_aware_datetime(
            checked_at,
            "checked_at",
        )

        normalized_evaluated_at = _require_aware_datetime(
            evaluated_at,
            "evaluated_at",
        )

        if normalized_evaluated_at < normalized_checked_at:
            raise KalshiLiveReadReadinessContractError(
                "evaluated_at cannot be before checked_at"
            )

        normalized_latency_ms = _require_non_negative_int(
            measured_latency_ms,
            "measured_latency_ms",
        )

        normalized_consecutive_failures = (
            _require_non_negative_int(
                consecutive_failures,
                "consecutive_failures",
            )
        )

        if not isinstance(
            rate_window_observation,
            RateWindowObservation,
        ):
            raise KalshiLiveReadReadinessContractError(
                "rate_window_observation must be "
                "RateWindowObservation"
            )

        if rate_window_observation.source_id != SOURCE_ID:
            raise KalshiLiveReadReadinessContractError(
                "rate-window source identity mismatch"
            )

        immutable_readiness_metadata = _immutable_mapping(
            readiness_metadata,
            "readiness_metadata",
        )

        immutable_replay_metadata = _immutable_mapping(
            replay_metadata,
            "replay_metadata",
        )

        immutable_audit_metadata = _immutable_mapping(
            audit_metadata,
            "audit_metadata",
        )

        source_health = self._shadow_adapter.probe_health(
            checked_at=normalized_checked_at
        )

        self._validate_source_health_evidence(
            source_health
        )

        health_observation = SourceHealthObservation.create(
            source_id=SOURCE_ID,
            checked_at=normalized_checked_at,
            reachable=source_health.reachable,
            consecutive_failures=(
                normalized_consecutive_failures
            ),
            latency_ms=(
                normalized_latency_ms
                if source_health.reachable
                else None
            ),
            metadata={
                "readiness_engine_id": ENGINE_ID,
                "adapter_id": ADAPTER_ID,
                "source_health_evidence_hash": (
                    source_health.evidence_hash
                ),
                "source_probe_health_status": (
                    source_health.health_status
                ),
                "public_endpoint": True,
                "authentication_used": False,
                "http_method": "GET",
                "endpoint_path": MARKETS_PATH,
                "shadow_mode": True,
            },
        )

        decision = self._source_control_engine.evaluate(
            health_observation=health_observation,
            rate_observation=rate_window_observation,
            evaluated_at=normalized_evaluated_at,
            replay_metadata={
                "readiness_engine_id": ENGINE_ID,
                "source_health_evidence_hash": (
                    source_health.evidence_hash
                ),
                "parent_replay_metadata": (
                    _mapping_from_immutable(
                        immutable_replay_metadata
                    )
                ),
            },
            audit_metadata={
                "readiness_engine_id": ENGINE_ID,
                "source_health_evidence_hash": (
                    source_health.evidence_hash
                ),
                "parent_audit_metadata": (
                    _mapping_from_immutable(
                        immutable_audit_metadata
                    )
                ),
            },
        )

        (
            source_control_reason_codes,
            health_policy_evidence_present,
            rate_policy_evidence_present,
        ) = self._validate_source_control_decision(
            decision=decision,
        )

        if source_health.health_status != "healthy":
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 source probe is not healthy"
            )

        if source_health.reachable is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 source probe is not reachable"
            )

        if decision.acquisition_allowed is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 blocked live shadow cycle entry"
            )

        readiness_id = "kalshi_live_readiness." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "kalshi_live_readiness_identity",
                "adapter_id": ADAPTER_ID,
                "source_id": SOURCE_ID,
                "ola_016_source_health_evidence_hash": (
                    source_health.evidence_hash
                ),
                "ola_002_health_evidence_hash": (
                    decision.health_evidence.evidence_hash
                ),
                "ola_002_rate_control_evidence_hash": (
                    decision.rate_control_evidence.evidence_hash
                ),
                "source_control_decision_hash": (
                    decision.decision_hash
                ),
                "checked_at": normalized_checked_at,
                "evaluated_at": normalized_evaluated_at,
            }
        )

        reason_codes = (
            "one_live_public_get_completed",
            "kalshi_public_market_contract_valid",
            "kalshi_source_probe_healthy",
            "ola_002_authoritative_decision_consumed",
            "ola_002_health_evidence_hash_preserved",
            "ola_002_rate_evidence_hash_preserved",
            "ola_002_health_policy_approval_explained",
            "ola_002_rate_policy_approval_explained",
            "ola_002_acquisition_allowed",
            "shadow_mode_verified",
            "alerts_remain_disabled",
            "qseries_intake_remains_disabled",
            "continuous_polling_not_started",
            "live_acquisition_not_performed",
            "postgresql_persistence_not_invoked",
            "live_shadow_cycle_entry_ready",
        )

        provisional = KalshiLiveReadReadinessRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            readiness_id=readiness_id,
            readiness_status="passed",
            adapter_id=ADAPTER_ID,
            source_id=SOURCE_ID,
            source_base_url=PRODUCTION_BASE_URL,
            source_endpoint=MARKETS_PATH,
            http_method="GET",
            checked_at=normalized_checked_at,
            evaluated_at=normalized_evaluated_at,
            public_endpoint=True,
            authentication_used=False,
            live_get_request_count=1,
            source_contract_valid=True,
            source_probe_health_status=(
                source_health.health_status
            ),
            source_reachable=True,
            source_latency_ms=normalized_latency_ms,
            source_health_evidence_hash=(
                decision.health_evidence.evidence_hash
            ),
            rate_control_evidence_hash=(
                decision.rate_control_evidence.evidence_hash
            ),
            source_control_decision_hash=(
                decision.decision_hash
            ),
            source_control_reason_codes=(
                source_control_reason_codes
            ),
            health_policy_evidence_present=(
                health_policy_evidence_present
            ),
            rate_policy_evidence_present=(
                rate_policy_evidence_present
            ),
            source_control_acquisition_allowed=True,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            live_shadow_cycle_entry_ready=True,
            continuous_polling_started=False,
            acquisition_performed=False,
            canonical_observation_created=False,
            persistence_invoked=False,
            alert_created=False,
            qseries_intake_record_created=False,
            reason_codes=reason_codes,
            readiness_metadata=immutable_readiness_metadata,
            readiness_hash="",
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

        readiness_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": READINESS_RECORD_TYPE,
                "readiness_record": (
                    provisional.to_canonical_dict(
                        include_readiness_hash=False
                    )
                ),
            }
        )

        return KalshiLiveReadReadinessRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            readiness_id=provisional.readiness_id,
            readiness_status=provisional.readiness_status,
            adapter_id=provisional.adapter_id,
            source_id=provisional.source_id,
            source_base_url=provisional.source_base_url,
            source_endpoint=provisional.source_endpoint,
            http_method=provisional.http_method,
            checked_at=provisional.checked_at,
            evaluated_at=provisional.evaluated_at,
            public_endpoint=True,
            authentication_used=False,
            live_get_request_count=1,
            source_contract_valid=True,
            source_probe_health_status=(
                provisional.source_probe_health_status
            ),
            source_reachable=True,
            source_latency_ms=provisional.source_latency_ms,
            source_health_evidence_hash=(
                provisional.source_health_evidence_hash
            ),
            rate_control_evidence_hash=(
                provisional.rate_control_evidence_hash
            ),
            source_control_decision_hash=(
                provisional.source_control_decision_hash
            ),
            source_control_reason_codes=(
                provisional.source_control_reason_codes
            ),
            health_policy_evidence_present=True,
            rate_policy_evidence_present=True,
            source_control_acquisition_allowed=True,
            shadow_mode=True,
            alerts_allowed=False,
            qseries_intake_allowed=False,
            live_shadow_cycle_entry_ready=True,
            continuous_polling_started=False,
            acquisition_performed=False,
            canonical_observation_created=False,
            persistence_invoked=False,
            alert_created=False,
            qseries_intake_record_created=False,
            reason_codes=provisional.reason_codes,
            readiness_metadata=provisional.readiness_metadata,
            readiness_hash=readiness_hash,
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

    @staticmethod
    def _validate_source_health_evidence(
        source_health,
    ) -> None:
        if source_health.adapter_id != ADAPTER_ID:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 source-health adapter identity mismatch"
            )

        if source_health.source_id != SOURCE_ID:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 source-health source identity mismatch"
            )

        if source_health.public_endpoint is not True:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi public endpoint evidence is incompatible"
            )

        if source_health.authentication_used is not False:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi readiness probe used authentication"
            )

        if source_health.http_method != "GET":
            raise KalshiLiveReadReadinessFailure(
                "Kalshi readiness probe did not use GET"
            )

        if source_health.endpoint_path != MARKETS_PATH:
            raise KalshiLiveReadReadinessFailure(
                "Kalshi readiness endpoint mismatch"
            )

        if source_health.shadow_mode is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 health evidence left shadow mode"
            )

        if source_health.alerts_allowed is not False:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 health evidence gained alert capability"
            )

        if source_health.qseries_intake_allowed is not False:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 health evidence gained Q Series intake"
            )

        if source_health.read_only is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 health evidence lost read_only invariant"
            )

        if source_health.execution_allowed is not False:
            raise KalshiLiveReadReadinessFailure(
                "OLA-016 health evidence gained execution capability"
            )

    @staticmethod
    def _validate_source_control_decision(
        *,
        decision: SourceControlDecisionRecord,
    ) -> tuple[
        tuple[str, ...],
        bool,
        bool,
    ]:
        if not isinstance(
            decision,
            SourceControlDecisionRecord,
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 returned incompatible source-control evidence"
            )

        if decision.source_id != SOURCE_ID:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 source identity mismatch"
            )

        if (
            decision.health_evidence.source_id
            != SOURCE_ID
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 health evidence source identity mismatch"
            )

        if (
            decision.rate_control_evidence.source_id
            != SOURCE_ID
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 rate evidence source identity mismatch"
            )

        health_evidence_hash = (
            decision.health_evidence.evidence_hash
        )

        rate_evidence_hash = (
            decision.rate_control_evidence.evidence_hash
        )

        if (
            not isinstance(health_evidence_hash, str)
            or not health_evidence_hash
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 health evidence hash is missing"
            )

        if (
            not isinstance(rate_evidence_hash, str)
            or not rate_evidence_hash
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 rate evidence hash is missing"
            )

        if (
            not isinstance(decision.decision_hash, str)
            or not decision.decision_hash
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision hash is missing"
            )

        reason_codes = tuple(
            decision.reason_codes
        )

        reason_code_set = set(
            reason_codes
        )

        health_policy_evidence_present = (
            HEALTH_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        rate_policy_evidence_present = (
            RATE_APPROVAL_REASON_CODES
            .issubset(reason_code_set)
        )

        if not health_policy_evidence_present:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks health approval reasons"
            )

        if not rate_policy_evidence_present:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks rate approval reasons"
            )

        if (
            FINAL_APPROVAL_REASON_CODE
            not in reason_code_set
        ):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lacks final acquisition approval"
            )

        if decision.acquisition_allowed is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 blocked acquisition"
            )

        if decision.read_only is not True:
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision lost read_only invariant"
            )

        false_invariants = {
            "execution_allowed": decision.execution_allowed,
            "trade_authorization_allowed": (
                decision.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                decision.order_placement_allowed
            ),
            "execution_adapter_invocation_allowed": (
                decision.execution_adapter_invocation_allowed
            ),
            "funds_moved": decision.funds_moved,
            "portfolio_mutated": decision.portfolio_mutated,
        }

        if any(false_invariants.values()):
            raise KalshiLiveReadReadinessFailure(
                "OLA-002 decision gained execution capability"
            )

        return (
            reason_codes,
            health_policy_evidence_present,
            rate_policy_evidence_present,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "HEALTH_APPROVAL_REASON_CODES",
    "RATE_APPROVAL_REASON_CODES",
    "FINAL_APPROVAL_REASON_CODE",
    "KalshiLiveReadReadinessContractError",
    "KalshiLiveReadReadinessFailure",
    "KalshiLiveReadReadinessInvariantError",
    "KalshiLiveReadReadinessRecord",
    "OracleKalshiLiveReadReadinessGate",
    "canonical_json",
    "stable_hash",
]
