from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Mapping


SCHEMA_VERSION = "OLA-066"
ENGINE_ID = "OLA-066"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False


class OracleLiveShadowOperatorHealthAttestationError(
    RuntimeError
):
    pass


class OracleLiveShadowOperatorHealthAttestationBlocked(
    OracleLiveShadowOperatorHealthAttestationError
):
    pass


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "observed_at must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "observed_at must be timezone-aware"
        )

    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(
            dict(payload),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "health evidence is not serializable"
        ) from exc

    return hashlib.sha256(encoded).hexdigest()


def _require_bool(
    payload: Mapping[str, Any],
    field_name: str,
) -> bool:
    value = payload.get(field_name)

    if not isinstance(value, bool):
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            f"{field_name} must be boolean"
        )

    return value


def _optional_age(
    payload: Mapping[str, Any],
    field_name: str,
) -> float | None:
    value = payload.get(field_name)

    if value is None:
        return None

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
    ):
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            f"{field_name} must be numeric or None"
        )

    normalized = float(value)

    if normalized < 0:
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            f"{field_name} cannot be negative"
        )

    return normalized


def _optional_pid(
    payload: Mapping[str, Any],
) -> int | None:
    value = payload.get("pid")

    if value is None:
        return None

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
    ):
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "pid must be a positive integer or None"
        )

    return value


@dataclass(frozen=True, slots=True)
class OracleLiveShadowOperatorHealthAttestationRecord:
    schema_version: str
    engine_id: str
    observed_at: str
    operator_status: str
    health_status: str
    pid: int | None
    process_alive: bool
    runtime_fresh: bool
    state_age_seconds: float | None
    newest_log_age_seconds: float | None
    stale_seconds: int
    healthy: bool
    degraded: bool
    stopped: bool
    fail_closed: bool
    evidence_hash: str
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "schema version mismatch"
            )

        if self.engine_id != ENGINE_ID:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "engine id mismatch"
            )

        if self.operator_status not in {
            "RUNNING",
            "DEGRADED",
            "STOPPED",
        }:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "unsupported operator status"
            )

        if self.health_status not in {
            "HEALTHY",
            "DEGRADED",
            "STOPPED",
        }:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "unsupported health status"
            )

        if len(self.evidence_hash) != 64:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "invalid evidence hash"
            )

        try:
            int(self.evidence_hash, 16)
        except ValueError as exc:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "invalid evidence hash"
            ) from exc

        classifications = (
            self.healthy,
            self.degraded,
            self.stopped,
        )

        if sum(value is True for value in classifications) != 1:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "exactly one health classification is required"
            )

        if self.healthy:
            if not (
                self.operator_status == "RUNNING"
                and self.health_status == "HEALTHY"
                and self.process_alive
                and self.runtime_fresh
                and not self.fail_closed
            ):
                raise OracleLiveShadowOperatorHealthAttestationBlocked(
                    "healthy record is inconsistent"
                )

        if self.degraded:
            if not (
                self.operator_status == "DEGRADED"
                and self.health_status == "DEGRADED"
                and self.process_alive
                and not self.runtime_fresh
                and self.fail_closed
            ):
                raise OracleLiveShadowOperatorHealthAttestationBlocked(
                    "degraded record is inconsistent"
                )

        if self.stopped:
            if not (
                self.operator_status == "STOPPED"
                and self.health_status == "STOPPED"
                and not self.process_alive
                and not self.runtime_fresh
                and self.fail_closed
            ):
                raise OracleLiveShadowOperatorHealthAttestationBlocked(
                    "stopped record is inconsistent"
                )

        if self.read_only is not True:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "OLA-066 must remain read-only"
            )

        forbidden = (
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if any(value is True for value in forbidden):
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "OLA-066 authority boundary violated"
            )

    def to_dict(self) -> Mapping[str, Any]:
        return MappingProxyType(asdict(self))


class OracleLiveShadowOperatorHealthAttestor:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        status_provider: Callable[..., Mapping[str, Any]],
    ) -> None:
        if not callable(status_provider):
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "status provider must be callable"
            )

        self._status_provider = status_provider

    def attest(
        self,
        *,
        observed_at: datetime,
        stale_seconds: int = 120,
    ) -> OracleLiveShadowOperatorHealthAttestationRecord:
        if (
            isinstance(stale_seconds, bool)
            or not isinstance(stale_seconds, int)
            or stale_seconds < 1
        ):
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "stale_seconds must be positive"
            )

        observed_at_value = _timestamp(observed_at)

        try:
            raw_payload = self._status_provider(
                stale_seconds=stale_seconds
            )
        except BaseException as exc:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "operator status provider failed closed"
            ) from exc

        if not isinstance(raw_payload, Mapping):
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "operator status provider must return a mapping"
            )

        payload = dict(raw_payload)

        operator_status = payload.get("status")

        if operator_status not in {
            "RUNNING",
            "DEGRADED",
            "STOPPED",
        }:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "unsupported operator status"
            )

        process_alive = _require_bool(
            payload,
            "process_alive",
        )

        runtime_fresh = _require_bool(
            payload,
            "runtime_fresh",
        )

        operator_read_only = _require_bool(
            payload,
            "read_only",
        )

        operator_execution_allowed = _require_bool(
            payload,
            "execution_allowed",
        )

        if operator_read_only is not True:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "operator read-only guarantee is absent"
            )

        if operator_execution_allowed is not False:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "operator execution authority is enabled"
            )

        pid = _optional_pid(payload)

        state_age_seconds = _optional_age(
            payload,
            "state_age_seconds",
        )

        newest_log_age_seconds = _optional_age(
            payload,
            "newest_log_age_seconds",
        )

        if process_alive and pid is None:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "live operator requires a PID"
            )

        if not process_alive and runtime_fresh:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "stopped process cannot have fresh runtime evidence"
            )

        if process_alive and runtime_fresh:
            expected_status = "RUNNING"
            health_status = "HEALTHY"
            healthy = True
            degraded = False
            stopped = False
            fail_closed = False
        elif process_alive:
            expected_status = "DEGRADED"
            health_status = "DEGRADED"
            healthy = False
            degraded = True
            stopped = False
            fail_closed = True
        else:
            expected_status = "STOPPED"
            health_status = "STOPPED"
            healthy = False
            degraded = False
            stopped = True
            fail_closed = True

        if operator_status != expected_status:
            raise OracleLiveShadowOperatorHealthAttestationBlocked(
                "operator status conflicts with runtime evidence"
            )

        evidence = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "observed_at": observed_at_value,
            "operator_status": operator_status,
            "health_status": health_status,
            "pid": pid,
            "process_alive": process_alive,
            "runtime_fresh": runtime_fresh,
            "state_age_seconds": state_age_seconds,
            "newest_log_age_seconds": newest_log_age_seconds,
            "stale_seconds": stale_seconds,
            "healthy": healthy,
            "degraded": degraded,
            "stopped": stopped,
            "fail_closed": fail_closed,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "execution_adapter_resolved": False,
            "execution_adapter_invoked": False,
            "trade_authorization_allowed": False,
            "order_placement_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }

        return OracleLiveShadowOperatorHealthAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            observed_at=observed_at_value,
            operator_status=operator_status,
            health_status=health_status,
            pid=pid,
            process_alive=process_alive,
            runtime_fresh=runtime_fresh,
            state_age_seconds=state_age_seconds,
            newest_log_age_seconds=newest_log_age_seconds,
            stale_seconds=stale_seconds,
            healthy=healthy,
            degraded=degraded,
            stopped=stopped,
            fail_closed=fail_closed,
            evidence_hash=_canonical_hash(evidence),
        )


def build_production_operator_health_attestor(
) -> OracleLiveShadowOperatorHealthAttestor:
    try:
        import oracle_live_shadow_operator as operator
    except ImportError as exc:
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "OLA-064 operator module is unavailable"
        ) from exc

    status_provider = getattr(
        operator,
        "_status_payload",
        None,
    )

    if not callable(status_provider):
        raise OracleLiveShadowOperatorHealthAttestationBlocked(
            "OLA-064 status provider is unavailable"
        )

    return OracleLiveShadowOperatorHealthAttestor(
        status_provider=status_provider
    )


__all__ = [
    "ALERTS_ALLOWED",
    "ENGINE_ID",
    "EXECUTION_ALLOWED",
    "QSERIES_HANDOFF_ALLOWED",
    "READ_ONLY",
    "SCHEMA_VERSION",
    "OracleLiveShadowOperatorHealthAttestationBlocked",
    "OracleLiveShadowOperatorHealthAttestationError",
    "OracleLiveShadowOperatorHealthAttestationRecord",
    "OracleLiveShadowOperatorHealthAttestor",
    "build_production_operator_health_attestor",
]
