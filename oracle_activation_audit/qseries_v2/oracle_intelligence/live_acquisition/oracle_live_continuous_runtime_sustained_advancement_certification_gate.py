"""
OLA-082
Oracle Live Continuous Runtime Sustained Advancement Certification Gate

Requires multiple consecutive OLA-081 advancement passes from the same
already-running OLA-074 guarded continuous Oracle process.

The gate is strictly observational. It does not start, stop, restart,
import, or invoke the live runtime.

OLA-081 remains the canonical per-window advancement gate.
OLA-068 remains the canonical PostgreSQL advancement monitor.
OLA-074 remains the canonical guarded continuous runtime owner.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
from typing import Any, Callable, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_advancement_gate import (
    OracleLiveContinuousRuntimeAdvancementRecord,
    evaluate_oracle_live_continuous_runtime_advancement,
)


SCHEMA_VERSION = "OLA-082"
ENGINE_ID = "OLA-082"

UPSTREAM_GATE_SCHEMA_VERSION = "OLA-081"
UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_LOCK_SCHEMA_VERSION = "OLA-074"

EXPECTED_RUNTIME_MODE = (
    "continuous_live_shadow"
)

EXPECTED_LAUNCHER = (
    "run_oracle_live_shadow_"
    "CONTINUOUS_GUARDED.py"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

DEFAULT_CHECKPOINT_COUNT = 2

DEFAULT_OBSERVATION_WINDOW_SECONDS = (
    30.0
)


class OracleLiveContinuousRuntimeSustainedAdvancementError(
    RuntimeError
):
    """Base OLA-082 failure."""


class OracleLiveContinuousRuntimeSustainedAdvancementContractError(
    OracleLiveContinuousRuntimeSustainedAdvancementError
):
    """Malformed invocation or upstream record contract."""


class OracleLiveContinuousRuntimeIdentityChanged(
    OracleLiveContinuousRuntimeSustainedAdvancementError
):
    """The observed OLA-074 process changed between checkpoints."""


class OracleLiveContinuousRuntimeSustainedAdvancementFailed(
    OracleLiveContinuousRuntimeSustainedAdvancementError
):
    """A required OLA-081 advancement checkpoint failed."""


def _utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"{field_name} must be a datetime"
            )
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"{field_name} must be timezone-aware"
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
        (
            bool,
            int,
            float,
            str,
        ),
    ):
        return value

    if isinstance(
        value,
        datetime,
    ):
        return _require_aware_datetime(
            value,
            "canonical datetime",
        ).isoformat()

    if isinstance(
        value,
        Path,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        Mapping,
    ):
        result: dict[str, Any] = {}

        for key in sorted(
            value
        ):
            if not isinstance(
                key,
                str,
            ):
                raise (
                    OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                        "canonical mapping keys must be strings"
                    )
                )

            result[key] = _canonicalize(
                value[key]
            )

        return result

    if isinstance(
        value,
        (
            tuple,
            list,
        ),
    ):
        return [
            _canonicalize(
                item
            )
            for item in value
        ]

    raise (
        OracleLiveContinuousRuntimeSustainedAdvancementContractError(
            "unsupported canonical type: "
            f"{type(value).__name__}"
        )
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        _canonicalize(
            value
        ),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        allow_nan=False,
    )


def stable_hash(
    value: Any,
) -> str:
    return sha256(
        canonical_json(
            value
        ).encode(
            "utf-8"
        )
    ).hexdigest()


def _require_positive_int(
    value: Any,
    field_name: str,
) -> int:
    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
        or value < 1
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"{field_name} must be a positive int"
            )
        )

    return value


def _require_positive_number(
    value: Any,
    field_name: str,
) -> float:
    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            (
                int,
                float,
            ),
        )
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"{field_name} must be a positive number"
            )
        )

    normalized = float(
        value
    )

    if normalized <= 0.0:
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"{field_name} must be greater than zero"
            )
        )

    return normalized


def _validate_upstream_record(
    record: OracleLiveContinuousRuntimeAdvancementRecord,
    checkpoint_number: int,
) -> None:
    if not isinstance(
        record,
        OracleLiveContinuousRuntimeAdvancementRecord,
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "returned the wrong record type"
            )
        )

    if (
        record.schema_version
        != UPSTREAM_GATE_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "schema must be OLA-081"
            )
        )

    if (
        record.engine_id
        != UPSTREAM_GATE_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "engine must be OLA-081"
            )
        )

    if record.gate_status != "passed":
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementFailed(
                f"checkpoint {checkpoint_number} did not pass"
            )
        )

    if (
        record.runtime_mode
        != EXPECTED_RUNTIME_MODE
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "runtime mode mismatch"
            )
        )

    if (
        record.launcher
        != EXPECTED_LAUNCHER
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "launcher mismatch"
            )
        )

    if (
        record.upstream_monitor_schema_version
        != UPSTREAM_MONITOR_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "upstream monitor mismatch"
            )
        )

    if record.process_id < 1:
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "process_id must be positive"
            )
        )

    if (
        record.observation_count_delta <= 0
        or record.latest_sequence_delta <= 0
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementFailed(
                f"checkpoint {checkpoint_number} "
                "did not prove PostgreSQL advancement"
            )
        )

    if (
        record.postgresql_persistence_advanced
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementFailed(
                f"checkpoint {checkpoint_number} "
                "PostgreSQL did not advance"
            )
        )

    if (
        record.runtime_advancing is not True
        or record.process_remained_alive is not True
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementFailed(
                f"checkpoint {checkpoint_number} "
                "runtime did not remain advancing and alive"
            )
        )

    if (
        record.existing_runtime_observed_only
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "was not observational"
            )
        )

    if (
        record.acquisition_cycle_invoked
        is not False
        or record.scheduler_invoked
        is not False
        or record.runner_invoked
        is not False
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "invoked runtime machinery"
            )
        )

    for field_name, expected in (
        (
            "read_only",
            True,
        ),
        (
            "execution_allowed",
            False,
        ),
        (
            "alerts_allowed",
            False,
        ),
        (
            "qseries_handoff_allowed",
            False,
        ),
        (
            "trade_authorization_allowed",
            False,
        ),
        (
            "order_placement_allowed",
            False,
        ),
        (
            "funds_moved",
            False,
        ),
        (
            "portfolio_mutated",
            False,
        ),
    ):
        if (
            getattr(
                record,
                field_name,
            )
            is not expected
        ):
            raise (
                OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                    f"checkpoint {checkpoint_number} "
                    f"safety field {field_name} mismatch"
                )
            )

    if (
        record.verify_record_hash()
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                f"checkpoint {checkpoint_number} "
                "record hash is invalid"
            )
        )


@dataclass(
    frozen=True
)
class OracleLiveContinuousRuntimeSustainedAdvancementRecord:
    schema_version: str
    engine_id: str
    certification_status: str

    checked_at: datetime
    completed_at: datetime

    process_id: int
    runtime_mode: str
    launcher: str

    upstream_gate_schema_version: str
    upstream_monitor_schema_version: str
    upstream_lock_schema_version: str

    checkpoint_count: int

    observation_window_seconds_per_checkpoint: float
    total_observation_window_seconds: float

    checkpoint_record_hashes: tuple[
        str,
        ...,
    ]

    total_observation_count_delta: int
    total_latest_sequence_delta: int
    total_persistence_terminal_sequence_delta: int

    all_checkpoints_advanced: bool
    same_process_all_checkpoints: bool
    process_remained_alive: bool

    existing_runtime_observed_only: bool
    acquisition_cycle_invoked: bool
    scheduler_invoked: bool
    runner_invoked: bool

    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    record_hash: str

    def to_canonical_dict(
        self,
        *,
        include_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": (
                self.engine_id
            ),
            "certification_status": (
                self.certification_status
            ),
            "checked_at": (
                self.checked_at
            ),
            "completed_at": (
                self.completed_at
            ),
            "process_id": (
                self.process_id
            ),
            "runtime_mode": (
                self.runtime_mode
            ),
            "launcher": (
                self.launcher
            ),
            "upstream_gate_schema_version": (
                self.upstream_gate_schema_version
            ),
            "upstream_monitor_schema_version": (
                self.upstream_monitor_schema_version
            ),
            "upstream_lock_schema_version": (
                self.upstream_lock_schema_version
            ),
            "checkpoint_count": (
                self.checkpoint_count
            ),
            "observation_window_seconds_per_checkpoint": (
                self.observation_window_seconds_per_checkpoint
            ),
            "total_observation_window_seconds": (
                self.total_observation_window_seconds
            ),
            "checkpoint_record_hashes": (
                self.checkpoint_record_hashes
            ),
            "total_observation_count_delta": (
                self.total_observation_count_delta
            ),
            "total_latest_sequence_delta": (
                self.total_latest_sequence_delta
            ),
            "total_persistence_terminal_sequence_delta": (
                self.total_persistence_terminal_sequence_delta
            ),
            "all_checkpoints_advanced": (
                self.all_checkpoints_advanced
            ),
            "same_process_all_checkpoints": (
                self.same_process_all_checkpoints
            ),
            "process_remained_alive": (
                self.process_remained_alive
            ),
            "existing_runtime_observed_only": (
                self.existing_runtime_observed_only
            ),
            "acquisition_cycle_invoked": (
                self.acquisition_cycle_invoked
            ),
            "scheduler_invoked": (
                self.scheduler_invoked
            ),
            "runner_invoked": (
                self.runner_invoked
            ),
            "read_only": (
                self.read_only
            ),
            "execution_allowed": (
                self.execution_allowed
            ),
            "alerts_allowed": (
                self.alerts_allowed
            ),
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": (
                self.funds_moved
            ),
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
        }

        if include_hash:
            result["record_hash"] = (
                self.record_hash
            )

        return result

    def verify_record_hash(
        self,
    ) -> bool:
        return (
            self.record_hash
            == stable_hash(
                self.to_canonical_dict(
                    include_hash=False
                )
            )
        )


def evaluate_oracle_live_continuous_runtime_sustained_advancement(
    *,
    repository_root: Path,
    checked_at: datetime,
    checkpoint_count: int = (
        DEFAULT_CHECKPOINT_COUNT
    ),
    observation_window_seconds: float = (
        DEFAULT_OBSERVATION_WINDOW_SECONDS
    ),
    advancement_evaluator: Callable[
        ...,
        OracleLiveContinuousRuntimeAdvancementRecord,
    ] = (
        evaluate_oracle_live_continuous_runtime_advancement
    ),
) -> OracleLiveContinuousRuntimeSustainedAdvancementRecord:
    repository_root = Path(
        repository_root
    ).resolve()

    if not repository_root.is_dir():
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                "repository_root must exist"
            )
        )

    checked_at = _require_aware_datetime(
        checked_at,
        "checked_at",
    )

    checkpoint_count = _require_positive_int(
        checkpoint_count,
        "checkpoint_count",
    )

    if checkpoint_count < 2:
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                "checkpoint_count must be at least 2"
            )
        )

    observation_window_seconds = (
        _require_positive_number(
            observation_window_seconds,
            "observation_window_seconds",
        )
    )

    if not callable(
        advancement_evaluator
    ):
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                "advancement_evaluator must be callable"
            )
        )

    records: list[
        OracleLiveContinuousRuntimeAdvancementRecord
    ] = []

    expected_process_id: int | None = (
        None
    )

    for checkpoint_number in range(
        1,
        checkpoint_count + 1,
    ):
        checkpoint_checked_at = (
            _utc_now()
        )

        record = advancement_evaluator(
            repository_root=repository_root,
            checked_at=checkpoint_checked_at,
            observation_window_seconds=(
                observation_window_seconds
            ),
        )

        _validate_upstream_record(
            record,
            checkpoint_number,
        )

        if expected_process_id is None:
            expected_process_id = (
                record.process_id
            )

        elif (
            record.process_id
            != expected_process_id
        ):
            raise (
                OracleLiveContinuousRuntimeIdentityChanged(
                    "OLA-074 process changed between "
                    "sustained advancement checkpoints"
                )
            )

        if (
            records
            and record.checked_at
            < records[-1].completed_at
        ):
            raise (
                OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                    "checkpoint chronology overlaps "
                    "or moves backward"
                )
            )

        records.append(
            record
        )

    if expected_process_id is None:
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                "no advancement checkpoints were collected"
            )
        )

    completed_at = _utc_now()

    if completed_at < checked_at:
        raise (
            OracleLiveContinuousRuntimeSustainedAdvancementContractError(
                "completed_at cannot precede checked_at"
            )
        )

    record_without_hash = {
        "schema_version": (
            SCHEMA_VERSION
        ),
        "engine_id": (
            ENGINE_ID
        ),
        "certification_status": (
            "certified"
        ),
        "checked_at": (
            checked_at
        ),
        "completed_at": (
            completed_at
        ),
        "process_id": (
            expected_process_id
        ),
        "runtime_mode": (
            EXPECTED_RUNTIME_MODE
        ),
        "launcher": (
            EXPECTED_LAUNCHER
        ),
        "upstream_gate_schema_version": (
            UPSTREAM_GATE_SCHEMA_VERSION
        ),
        "upstream_monitor_schema_version": (
            UPSTREAM_MONITOR_SCHEMA_VERSION
        ),
        "upstream_lock_schema_version": (
            UPSTREAM_LOCK_SCHEMA_VERSION
        ),
        "checkpoint_count": (
            checkpoint_count
        ),
        "observation_window_seconds_per_checkpoint": (
            observation_window_seconds
        ),
        "total_observation_window_seconds": (
            checkpoint_count
            * observation_window_seconds
        ),
        "checkpoint_record_hashes": tuple(
            record.record_hash
            for record in records
        ),
        "total_observation_count_delta": sum(
            record.observation_count_delta
            for record in records
        ),
        "total_latest_sequence_delta": sum(
            record.latest_sequence_delta
            for record in records
        ),
        "total_persistence_terminal_sequence_delta": sum(
            (
                record
                .persistence_terminal_sequence_delta
            )
            for record in records
        ),
        "all_checkpoints_advanced": (
            True
        ),
        "same_process_all_checkpoints": (
            True
        ),
        "process_remained_alive": (
            True
        ),
        "existing_runtime_observed_only": (
            True
        ),
        "acquisition_cycle_invoked": (
            False
        ),
        "scheduler_invoked": (
            False
        ),
        "runner_invoked": (
            False
        ),
        "read_only": (
            READ_ONLY
        ),
        "execution_allowed": (
            EXECUTION_ALLOWED
        ),
        "alerts_allowed": (
            ALERTS_ALLOWED
        ),
        "qseries_handoff_allowed": (
            QSERIES_HANDOFF_ALLOWED
        ),
        "trade_authorization_allowed": (
            TRADE_AUTHORIZATION_ALLOWED
        ),
        "order_placement_allowed": (
            ORDER_PLACEMENT_ALLOWED
        ),
        "funds_moved": (
            FUNDS_MOVED
        ),
        "portfolio_mutated": (
            PORTFOLIO_MUTATED
        ),
    }

    return (
        OracleLiveContinuousRuntimeSustainedAdvancementRecord(
            **record_without_hash,
            record_hash=stable_hash(
                record_without_hash
            ),
        )
    )
