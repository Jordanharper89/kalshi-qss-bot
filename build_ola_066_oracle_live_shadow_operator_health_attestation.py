from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_live_shadow_operator_health_attestation.py"
)

TEST_FILE = (
    ROOT
    / "test_ola_066_oracle_live_shadow_operator_health_attestation.py"
)

PACKAGE_INIT = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "__init__.py"
)


MODULE_SOURCE = r'''from __future__ import annotations

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
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    OracleLiveShadowOperatorHealthAttestationBlocked,
    OracleLiveShadowOperatorHealthAttestor,
)


OBSERVED_AT = datetime(
    2026,
    7,
    17,
    20,
    0,
    0,
    tzinfo=timezone.utc,
)


def expect_blocked(callable_object) -> None:
    try:
        callable_object()
    except OracleLiveShadowOperatorHealthAttestationBlocked:
        return

    raise AssertionError(
        "expected OLA-066 to fail closed"
    )


def main() -> int:
    def healthy_provider(*, stale_seconds):
        assert stale_seconds == 120

        return {
            "status": "RUNNING",
            "pid": 12345,
            "process_alive": True,
            "runtime_fresh": True,
            "state_age_seconds": 3.0,
            "newest_log_age_seconds": 2.0,
            "read_only": True,
            "execution_allowed": False,
        }

    attestor = OracleLiveShadowOperatorHealthAttestor(
        status_provider=healthy_provider
    )

    first = attestor.attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    second = attestor.attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert first == second
    assert first.operator_status == "RUNNING"
    assert first.health_status == "HEALTHY"
    assert first.healthy is True
    assert first.degraded is False
    assert first.stopped is False
    assert first.fail_closed is False
    assert first.read_only is True
    assert first.execution_allowed is False
    assert first.alerts_allowed is False
    assert first.qseries_handoff_allowed is False
    assert first.execution_adapter_resolved is False
    assert first.execution_adapter_invoked is False
    assert first.trade_authorization_allowed is False
    assert first.order_placement_allowed is False
    assert first.funds_moved is False
    assert first.portfolio_mutated is False
    assert first.evidence_hash == second.evidence_hash

    immutable_payload = first.to_dict()

    try:
        immutable_payload["healthy"] = False
    except TypeError:
        pass
    else:
        raise AssertionError(
            "health projection must be immutable"
        )

    degraded = OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": "DEGRADED",
            "pid": 12346,
            "process_alive": True,
            "runtime_fresh": False,
            "state_age_seconds": 150.0,
            "newest_log_age_seconds": 151.0,
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert degraded.degraded is True
    assert degraded.fail_closed is True

    stopped = OracleLiveShadowOperatorHealthAttestor(
        status_provider=lambda **_: {
            "status": "STOPPED",
            "pid": None,
            "process_alive": False,
            "runtime_fresh": False,
            "state_age_seconds": None,
            "newest_log_age_seconds": None,
            "read_only": True,
            "execution_allowed": False,
        }
    ).attest(
        observed_at=OBSERVED_AT,
        stale_seconds=120,
    )

    assert stopped.stopped is True
    assert stopped.fail_closed is True

    expect_blocked(
        lambda: attestor.attest(
            observed_at=datetime(
                2026,
                7,
                17,
                20,
                0,
                0,
            )
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": 12345,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": False,
                "execution_allowed": False,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": 12345,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": True,
                "execution_allowed": True,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    expect_blocked(
        lambda: OracleLiveShadowOperatorHealthAttestor(
            status_provider=lambda **_: {
                "status": "RUNNING",
                "pid": None,
                "process_alive": True,
                "runtime_fresh": True,
                "state_age_seconds": 1.0,
                "newest_log_age_seconds": 1.0,
                "read_only": True,
                "execution_allowed": False,
            }
        ).attest(
            observed_at=OBSERVED_AT
        )
    )

    print(
        "[PASS] OLA-066 Oracle Live Shadow "
        "Operator Health Attestation"
    )

    print(
        {
            "schema_version": "OLA-066",
            "engine_id": "OLA-066",
            "status": "passed",
            "ola064_status_provider_consumed": True,
            "invalid_brittle_marker_checks_removed": True,
            "healthy_attestation": True,
            "degraded_fail_closed": True,
            "stopped_fail_closed": True,
            "deterministic_evidence_hash": True,
            "immutable_record": True,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "funds_moved": False,
            "portfolio_mutated": False,
        }
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


EXPORT_BLOCK = '''
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_operator_health_attestation import (
    OracleLiveShadowOperatorHealthAttestationBlocked,
    OracleLiveShadowOperatorHealthAttestationError,
    OracleLiveShadowOperatorHealthAttestationRecord,
    OracleLiveShadowOperatorHealthAttestor,
    build_production_operator_health_attestor,
)
'''


def write_full_replacement(
    path: Path,
    source: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    print(f"[OK] FULL REPLACEMENT: {path}")


def update_package_exports() -> None:
    PACKAGE_INIT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if PACKAGE_INIT.exists():
        source = PACKAGE_INIT.read_text(
            encoding="utf-8"
        )
    else:
        source = ""

    marker = (
        "oracle_live_shadow_operator_health_attestation import"
    )

    if marker in source:
        print(
            f"[OK] PACKAGE EXPORT ALREADY PRESENT: "
            f"{PACKAGE_INIT}"
        )
        return

    updated = source.rstrip()

    if updated:
        updated += "\n\n"

    updated += EXPORT_BLOCK.strip() + "\n"

    PACKAGE_INIT.write_text(
        updated,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[OK] UPDATED PACKAGE EXPORTS: {PACKAGE_INIT}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-066 PRODUCTION CORRECTION")
    print(" ORACLE LIVE SHADOW OPERATOR")
    print(" HEALTH ATTESTATION")
    print("========================================")

    operator_file = (
        ROOT
        / "oracle_live_shadow_operator.py"
    )

    if not operator_file.exists():
        raise SystemExit(
            "[ERROR] Missing OLA-064 operator file: "
            f"{operator_file}"
        )

    operator_source = operator_file.read_text(
        encoding="utf-8"
    )

    required_markers = (
        'SCHEMA_VERSION = "OLA-064"',
        'ENGINE_ID = "OLA-064"',
        "def _status_payload(",
    )

    missing = [
        marker
        for marker in required_markers
        if marker not in operator_source
    ]

    if missing:
        raise SystemExit(
            "[ERROR] OLA-064 operator contract is "
            f"incomplete. Missing: {missing}"
        )

    write_full_replacement(
        MODULE,
        MODULE_SOURCE,
    )

    write_full_replacement(
        TEST_FILE,
        TEST_SOURCE,
    )

    update_package_exports()

    compile(
        MODULE.read_text(encoding="utf-8"),
        str(MODULE),
        "exec",
    )

    compile(
        TEST_FILE.read_text(encoding="utf-8"),
        str(TEST_FILE),
        "exec",
    )

    compile(
        PACKAGE_INIT.read_text(encoding="utf-8"),
        str(PACKAGE_INIT),
        "exec",
    )

    print("")
    print(
        "[DONE] OLA-066 corrected existing installer "
        "and production files installed"
    )
    print("")
    print("Run:")
    print(
        "py test_ola_066_oracle_live_shadow_"
        "operator_health_attestation.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())