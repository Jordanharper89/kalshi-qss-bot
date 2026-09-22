from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / "oracle_readiness_recovery_bounded_repeatability_gate.py"
)

TEST_PATH = (
    ROOT
    / "test_ola_080_oracle_readiness_recovery_bounded_repeatability_gate.py"
)


PRODUCTION_SOURCE = r'''"""
OLA-080
Oracle Readiness Recovery Bounded Repeatability Gate

Proves that the complete bounded OLA-079 recovery/full-runner gate can be
repeated deterministically without enabling continuous operation or
introducing execution authority.

OLA-080 does not start the Oracle service.

OLA-080 owns only:

- bounded repetition of a caller-supplied OLA-079 gate callable
- strict success-result validation
- deterministic repetition accounting
- immutable repeatability evidence
- preservation of permanent Oracle safety invariants

Permanent rules:

- Oracle remains read-only.
- Continuous service is not started.
- Alerts remain disabled.
- Q Series handoff remains disabled.
- No execution adapter is resolved.
- No execution adapter is invoked.
- No trade is authorized.
- No order is placed.
- No funds are moved.
- No portfolio is mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "OLA-080"
ENGINE_ID = "OLA-080"

GATE_STATUS_PASSED = "passed"

READ_ONLY = True
CONTINUOUS_SERVICE_STARTED = False
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class OracleReadinessRecoveryBoundedRepeatabilityGateError(
    RuntimeError
):
    """Base OLA-080 failure."""


class OracleReadinessRecoveryBoundedRepeatabilityContractError(
    OracleReadinessRecoveryBoundedRepeatabilityGateError
):
    """Raised when OLA-080 receives malformed contract data."""


class OracleReadinessRecoveryBoundedRepeatabilityFailure(
    OracleReadinessRecoveryBoundedRepeatabilityGateError
):
    """Raised when a bounded OLA-079 repetition fails."""


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise (
            OracleReadinessRecoveryBoundedRepeatabilityContractError(
                f"{field_name} must be a datetime"
            )
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise (
            OracleReadinessRecoveryBoundedRepeatabilityContractError(
                f"{field_name} must be timezone-aware"
            )
        )

    return value


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
    ):
        raise (
            OracleReadinessRecoveryBoundedRepeatabilityContractError(
                f"{field_name} must be a positive int"
            )
        )

    return value


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        (bool, int, float, str),
    ):
        return value

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise (
                    OracleReadinessRecoveryBoundedRepeatabilityContractError(
                        "canonical mapping keys must be strings"
                    )
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(value, (tuple, list)):
        return [
            _canonicalize(item)
            for item in value
        ]

    raise (
        OracleReadinessRecoveryBoundedRepeatabilityContractError(
            "unsupported canonical type: "
            f"{type(value).__name__}"
        )
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


@dataclass(frozen=True)
class OracleReadinessRecoveryBoundedRepeatabilityRecord:
    schema_version: str
    engine_id: str
    gate_status: str

    checked_at: datetime
    evaluated_at: datetime

    requested_repetition_count: int
    completed_repetition_count: int
    successful_repetition_count: int
    failed_repetition_count: int

    result_codes: tuple[int, ...]
    result_hashes: tuple[str, ...]
    deterministic_result_hash: str

    complete_ola079_gate_repeated: bool
    bounded_operation_preserved: bool
    continuous_service_started: bool

    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    metadata: tuple[tuple[str, Any], ...]
    record_hash: str

    def to_canonical_dict(
        self,
        *,
        include_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "gate_status": self.gate_status,
            "checked_at": self.checked_at.isoformat(),
            "evaluated_at": self.evaluated_at.isoformat(),
            "requested_repetition_count": (
                self.requested_repetition_count
            ),
            "completed_repetition_count": (
                self.completed_repetition_count
            ),
            "successful_repetition_count": (
                self.successful_repetition_count
            ),
            "failed_repetition_count": (
                self.failed_repetition_count
            ),
            "result_codes": list(
                self.result_codes
            ),
            "result_hashes": list(
                self.result_hashes
            ),
            "deterministic_result_hash": (
                self.deterministic_result_hash
            ),
            "complete_ola079_gate_repeated": (
                self.complete_ola079_gate_repeated
            ),
            "bounded_operation_preserved": (
                self.bounded_operation_preserved
            ),
            "continuous_service_started": (
                self.continuous_service_started
            ),
            "read_only": self.read_only,
            "execution_allowed": self.execution_allowed,
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
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
            "metadata": [
                [key, value]
                for key, value in self.metadata
            ],
        }

        if include_hash:
            result["record_hash"] = self.record_hash

        return result

    def verify_record_hash(
        self,
    ) -> bool:
        return self.record_hash == stable_hash(
            self.to_canonical_dict(
                include_hash=False
            )
        )


def evaluate_oracle_readiness_recovery_bounded_repeatability(
    *,
    ola079_gate_callable: Callable[[], Any],
    repetition_count: int,
    checked_at: datetime,
    evaluated_at: datetime,
    metadata: Mapping[str, Any] | None = None,
) -> OracleReadinessRecoveryBoundedRepeatabilityRecord:
    if not callable(ola079_gate_callable):
        raise (
            OracleReadinessRecoveryBoundedRepeatabilityContractError(
                "ola079_gate_callable must be callable"
            )
        )

    repetition_count = _require_positive_int(
        repetition_count,
        "repetition_count",
    )

    checked_at = _require_aware_datetime(
        checked_at,
        "checked_at",
    )

    evaluated_at = _require_aware_datetime(
        evaluated_at,
        "evaluated_at",
    )

    if evaluated_at < checked_at:
        raise (
            OracleReadinessRecoveryBoundedRepeatabilityContractError(
                "evaluated_at cannot precede checked_at"
            )
        )

    metadata = dict(
        metadata or {}
    )

    forbidden_metadata_keys = {
        "password",
        "passwd",
        "secret",
        "api_key",
        "private_key",
        "signing_key",
        "token",
        "database_url",
        "connection_string",
        "dsn",
    }

    for key in metadata:
        if not isinstance(key, str):
            raise (
                OracleReadinessRecoveryBoundedRepeatabilityContractError(
                    "metadata keys must be strings"
                )
            )

        if key.strip().lower() in forbidden_metadata_keys:
            raise (
                OracleReadinessRecoveryBoundedRepeatabilityContractError(
                    "secret-bearing metadata is forbidden"
                )
            )

    result_codes: list[int] = []
    result_hashes: list[str] = []

    for repetition_number in range(
        1,
        repetition_count + 1,
    ):
        result = ola079_gate_callable()

        if (
            isinstance(result, bool)
            or not isinstance(result, int)
        ):
            raise (
                OracleReadinessRecoveryBoundedRepeatabilityFailure(
                    "OLA-079 gate callable must return an int exit code"
                )
            )

        result_codes.append(
            result
        )

        result_hashes.append(
            stable_hash(
                {
                    "repetition_number": repetition_number,
                    "result_code": result,
                    "bounded": True,
                    "continuous_service_started": False,
                    "read_only": True,
                    "execution_allowed": False,
                }
            )
        )

        if result != 0:
            raise (
                OracleReadinessRecoveryBoundedRepeatabilityFailure(
                    "OLA-079 bounded repetition failed at "
                    f"repetition {repetition_number} "
                    f"with exit code {result}"
                )
            )

    deterministic_result_hash = stable_hash(
        {
            "result_codes": result_codes,
            "result_hashes": result_hashes,
        }
    )

    immutable_metadata = tuple(
        (
            key,
            _canonicalize(metadata[key]),
        )
        for key in sorted(metadata)
    )

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "gate_status": GATE_STATUS_PASSED,
        "checked_at": checked_at,
        "evaluated_at": evaluated_at,
        "requested_repetition_count": repetition_count,
        "completed_repetition_count": len(
            result_codes
        ),
        "successful_repetition_count": sum(
            1
            for code in result_codes
            if code == 0
        ),
        "failed_repetition_count": sum(
            1
            for code in result_codes
            if code != 0
        ),
        "result_codes": tuple(
            result_codes
        ),
        "result_hashes": tuple(
            result_hashes
        ),
        "deterministic_result_hash": (
            deterministic_result_hash
        ),
        "complete_ola079_gate_repeated": True,
        "bounded_operation_preserved": True,
        "continuous_service_started": (
            CONTINUOUS_SERVICE_STARTED
        ),
        "read_only": READ_ONLY,
        "execution_allowed": EXECUTION_ALLOWED,
        "alerts_allowed": ALERTS_ALLOWED,
        "qseries_handoff_allowed": (
            QSERIES_HANDOFF_ALLOWED
        ),
        "execution_adapter_resolved": (
            EXECUTION_ADAPTER_RESOLVED
        ),
        "execution_adapter_invoked": (
            EXECUTION_ADAPTER_INVOKED
        ),
        "trade_authorization_allowed": (
            TRADE_AUTHORIZATION_ALLOWED
        ),
        "order_placement_allowed": (
            ORDER_PLACEMENT_ALLOWED
        ),
        "funds_moved": FUNDS_MOVED,
        "portfolio_mutated": PORTFOLIO_MUTATED,
        "metadata": immutable_metadata,
    }

    record_hash = stable_hash(
        record_without_hash
    )

    return (
        OracleReadinessRecoveryBoundedRepeatabilityRecord(
            **record_without_hash,
            record_hash=record_hash,
        )
    )
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from pathlib import Path
import runpy

from qseries_v2.oracle_intelligence.live_acquisition.oracle_readiness_recovery_bounded_repeatability_gate import (
    ALERTS_ALLOWED,
    CONTINUOUS_SERVICE_STARTED,
    ENGINE_ID,
    EXECUTION_ALLOWED,
    FUNDS_MOVED,
    ORDER_PLACEMENT_ALLOWED,
    PORTFOLIO_MUTATED,
    QSERIES_HANDOFF_ALLOWED,
    READ_ONLY,
    SCHEMA_VERSION,
    TRADE_AUTHORIZATION_ALLOWED,
    OracleReadinessRecoveryBoundedRepeatabilityContractError,
    OracleReadinessRecoveryBoundedRepeatabilityFailure,
    evaluate_oracle_readiness_recovery_bounded_repeatability,
)


ROOT = Path(__file__).resolve().parent

OLA079_TEST_PATH = (
    ROOT
    / "test_ola_079_oracle_readiness_recovery_full_runner_iteration_gate.py"
)


def run_ola079_gate() -> int:
    namespace = runpy.run_path(
        str(OLA079_TEST_PATH),
        run_name="ola079_bounded_repeatability",
    )

    main_callable = namespace.get(
        "main"
    )

    if not callable(main_callable):
        raise AssertionError(
            "OLA-079 test must expose callable main"
        )

    result = main_callable()

    if result is None:
        return 0

    return result


def main() -> int:
    print("========================================")
    print(" OLA-080 BOUNDED REPEATABILITY GATE")
    print(" COMPLETE OLA-079 RECOVERY/RUNNER GATE")
    print(" CONTINUOUS SERVICE NOT STARTED")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-080"
    assert ENGINE_ID == "OLA-080"
    assert READ_ONLY is True
    assert CONTINUOUS_SERVICE_STARTED is False
    assert EXECUTION_ALLOWED is False
    assert ALERTS_ALLOWED is False
    assert QSERIES_HANDOFF_ALLOWED is False
    assert TRADE_AUTHORIZATION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert FUNDS_MOVED is False
    assert PORTFOLIO_MUTATED is False

    assert OLA079_TEST_PATH.is_file(), (
        "OLA-079 test file is missing"
    )

    production_module = import_module(
        "qseries_v2.oracle_intelligence."
        "live_acquisition."
        "oracle_readiness_recovery_full_runner_iteration_gate"
    )

    assert getattr(
        production_module,
        "SCHEMA_VERSION",
        None,
    ) == "OLA-079"

    checked_at = datetime(
        2026,
        7,
        19,
        15,
        0,
        0,
        tzinfo=timezone.utc,
    )

    evaluated_at = (
        checked_at
        + timedelta(microseconds=1)
    )

    print(
        "[TEST] Repeat complete OLA-079 bounded gate "
        "three times"
    )

    record = (
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=run_ola079_gate,
            repetition_count=3,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
            metadata={
                "gate_role": (
                    "readiness_recovery_bounded_repeatability"
                ),
                "upstream_gate": "OLA-079",
                "continuous_service_requested": False,
            },
        )
    )

    assert record.gate_status == "passed"
    assert record.requested_repetition_count == 3
    assert record.completed_repetition_count == 3
    assert record.successful_repetition_count == 3
    assert record.failed_repetition_count == 0
    assert record.result_codes == (
        0,
        0,
        0,
    )

    assert len(
        record.result_hashes
    ) == 3

    assert len(
        set(record.result_hashes)
    ) == 3

    assert record.complete_ola079_gate_repeated is True
    assert record.bounded_operation_preserved is True
    assert record.continuous_service_started is False

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False
    assert record.execution_adapter_resolved is False
    assert record.execution_adapter_invoked is False
    assert record.trade_authorization_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    assert record.verify_record_hash() is True

    first_canonical = record.to_canonical_dict()
    second_canonical = record.to_canonical_dict()

    assert first_canonical == second_canonical

    print(
        "[PASS] Complete OLA-079 recovery/full-runner "
        "gate repeated three times"
    )
    print(
        "[PASS] Every bounded repetition returned "
        "canonical success"
    )
    print(
        "[PASS] Deterministic repetition evidence "
        "and record hash verified"
    )

    calls = 0

    def failing_gate() -> int:
        nonlocal calls

        calls += 1

        if calls == 2:
            return 1

        return 0

    print(
        "[TEST] Failed bounded repetition rejected"
    )

    try:
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=failing_gate,
            repetition_count=3,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
        )
    except OracleReadinessRecoveryBoundedRepeatabilityFailure:
        pass
    else:
        raise AssertionError(
            "failed OLA-079 repetition was not rejected"
        )

    assert calls == 2

    print(
        "[PASS] Failed bounded repetition rejected"
    )

    print(
        "[TEST] Invalid repetition contract rejected"
    )

    try:
        evaluate_oracle_readiness_recovery_bounded_repeatability(
            ola079_gate_callable=run_ola079_gate,
            repetition_count=0,
            checked_at=checked_at,
            evaluated_at=evaluated_at,
        )
    except OracleReadinessRecoveryBoundedRepeatabilityContractError:
        pass
    else:
        raise AssertionError(
            "invalid repetition count was not rejected"
        )

    print(
        "[PASS] Invalid repetition contract rejected"
    )

    print(
        "[PASS] Continuous Oracle service was not started"
    )
    print(
        "[PASS] Oracle remained read-only; execution "
        "authority remained disabled"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
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
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-080 INSTALLER")
    print(" READINESS RECOVERY REPEATABILITY GATE")
    print(" COMPLETE OLA-079 GATE REPEATED")
    print("========================================")

    write_full_replacement(
        PRODUCTION_PATH,
        PRODUCTION_SOURCE,
    )

    write_full_replacement(
        TEST_PATH,
        TEST_SOURCE,
    )

    print("[OK] Complete OLA-079 gate bound as upstream")
    print("[OK] Three bounded repetitions required")
    print("[OK] Failed repetition rejection preserved")
    print("[OK] Deterministic repetition evidence installed")
    print("[OK] Continuous service remains stopped")
    print("[OK] Oracle remains read-only")
    print(
        "[OK] Execution, orders, funds, and "
        "portfolio mutation disabled"
    )
    print("[DONE] OLA-080 installed")

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )