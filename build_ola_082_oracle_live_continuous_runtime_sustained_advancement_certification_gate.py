from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent

PRODUCTION_PATH = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
    / (
        "oracle_live_continuous_runtime_"
        "sustained_advancement_certification_gate.py"
    )
)

TEST_PATH = (
    ROOT
    / (
        "test_ola_082_oracle_live_continuous_runtime_"
        "sustained_advancement_certification_gate.py"
    )
)


PRODUCTION_SOURCE = r'''"""
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
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_sustained_advancement_certification_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    evaluate_oracle_live_continuous_runtime_sustained_advancement,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-082")
    print(" SUSTAINED CONTINUOUS ADVANCEMENT")
    print(" TWO CONSECUTIVE OLA-081 CHECKPOINTS")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-082"
    assert ENGINE_ID == "OLA-082"

    print(
        "[TEST] Observe the active OLA-074 runtime only"
    )

    print(
        "[TEST] Require two consecutive "
        "OLA-081 advancement passes"
    )

    print(
        "[INFO] 30 seconds per checkpoint"
    )

    print(
        "[INFO] 60 seconds total canonical observation"
    )

    print(
        "[INFO] The live Oracle process "
        "will not be restarted"
    )

    record = (
        evaluate_oracle_live_continuous_runtime_sustained_advancement(
            repository_root=ROOT,
            checked_at=datetime.now(
                timezone.utc
            ),
            checkpoint_count=2,
            observation_window_seconds=30.0,
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    )

    assert record.schema_version == "OLA-082"
    assert record.engine_id == "OLA-082"

    assert (
        record.certification_status
        == "certified"
    )

    assert record.process_id > 0

    assert (
        record.runtime_mode
        == "continuous_live_shadow"
    )

    assert (
        record.launcher
        == "run_oracle_live_shadow_"
        "CONTINUOUS_GUARDED.py"
    )

    assert (
        record.upstream_gate_schema_version
        == "OLA-081"
    )

    assert (
        record.upstream_monitor_schema_version
        == "OLA-068"
    )

    assert (
        record.upstream_lock_schema_version
        == "OLA-074"
    )

    assert record.checkpoint_count == 2

    assert (
        record.observation_window_seconds_per_checkpoint
        == 30.0
    )

    assert (
        record.total_observation_window_seconds
        == 60.0
    )

    assert (
        len(
            record.checkpoint_record_hashes
        )
        == 2
    )

    assert (
        len(
            set(
                record.checkpoint_record_hashes
            )
        )
        == 2
    )

    assert (
        record.total_observation_count_delta
        > 0
    )

    assert (
        record.total_latest_sequence_delta
        > 0
    )

    assert (
        record.all_checkpoints_advanced
        is True
    )

    assert (
        record.same_process_all_checkpoints
        is True
    )

    assert (
        record.process_remained_alive
        is True
    )

    assert (
        record.existing_runtime_observed_only
        is True
    )

    assert (
        record.acquisition_cycle_invoked
        is False
    )

    assert record.scheduler_invoked is False
    assert record.runner_invoked is False

    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False

    assert (
        record.qseries_handoff_allowed
        is False
    )

    assert (
        record.trade_authorization_allowed
        is False
    )

    assert (
        record.order_placement_allowed
        is False
    )

    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    assert (
        record.verify_record_hash()
        is True
    )

    print(
        f"[PASS] Same live process certified: "
        f"{record.process_id}"
    )

    print(
        f"[PASS] Consecutive advancement checkpoints: "
        f"{record.checkpoint_count}"
    )

    print(
        f"[PASS] PostgreSQL observations increased by "
        f"{record.total_observation_count_delta}"
    )

    print(
        f"[PASS] Canonical sequence increased by "
        f"{record.total_latest_sequence_delta}"
    )

    print(
        "[PASS] OLA-081 record hashes verified"
    )

    print(
        "[PASS] OLA-068 passive monitoring preserved"
    )

    print(
        "[PASS] OLA-074 runtime identity remained stable"
    )

    print(
        "[PASS] Oracle remained read-only"
    )

    print(
        "[PASS] No execution, orders, funds, "
        "or portfolio mutation"
    )

    print(
        "[PASS] OLA-082 sustained continuous "
        "runtime certification"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
'''


def write_complete_file(
    path: Path,
    source: str,
) -> None:
    compile(
        source,
        str(path),
        "exec",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name + ".ola082.tmp"
    )

    temporary_path.write_text(
        source,
        encoding="utf-8",
        newline="\n",
    )

    installed_source = (
        temporary_path.read_text(
            encoding="utf-8"
        )
    )

    compile(
        installed_source,
        str(path),
        "exec",
    )

    temporary_path.replace(
        path
    )

    print(
        f"[OK] FULL REPLACEMENT: {path}"
    )


def main() -> int:
    print("========================================")
    print(" OLA-082 INSTALLER")
    print(" SUSTAINED CONTINUOUS ADVANCEMENT")
    print(" SAME-PROCESS CERTIFICATION GATE")
    print("========================================")

    upstream_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / (
            "oracle_live_continuous_runtime_"
            "advancement_gate.py"
        )
    )

    upstream_test_path = (
        ROOT
        / (
            "test_ola_081_oracle_live_continuous_"
            "runtime_advancement_gate.py"
        )
    )

    launcher_path = (
        ROOT
        / (
            "run_oracle_live_shadow_"
            "CONTINUOUS_GUARDED.py"
        )
    )

    for required_path in (
        upstream_path,
        upstream_test_path,
        launcher_path,
    ):
        if not required_path.is_file():
            raise FileNotFoundError(
                "Required repository file is missing: "
                f"{required_path}"
            )

    upstream_source = (
        upstream_path.read_text(
            encoding="utf-8"
        )
    )

    required_upstream_tokens = (
        'SCHEMA_VERSION = "OLA-081"',
        (
            'UPSTREAM_MONITOR_SCHEMA_VERSION '
            '= "OLA-068"'
        ),
        (
            'UPSTREAM_LOCK_SCHEMA_VERSION '
            '= "OLA-074"'
        ),
        (
            "class "
            "OracleLiveContinuousRuntimeAdvancementRecord:"
        ),
        (
            "def "
            "evaluate_oracle_live_continuous_"
            "runtime_advancement("
        ),
        "postgresql_persistence_advanced",
        "existing_runtime_observed_only",
        "process_remained_alive",
        "verify_record_hash",
    )

    for token in required_upstream_tokens:
        if token not in upstream_source:
            raise RuntimeError(
                "Actual OLA-081 contract is missing "
                f"required token: {token}"
            )

    launcher_source = (
        launcher_path.read_text(
            encoding="utf-8"
        )
    )

    required_launcher_tokens = (
        'SCHEMA_VERSION = "OLA-074"',
        '"runtime_mode": (',
        '"continuous_live_shadow"',
        '"read_only": True',
        '"execution_allowed": False',
        '"order_placement_allowed": False',
    )

    for token in required_launcher_tokens:
        if token not in launcher_source:
            raise RuntimeError(
                "Actual OLA-074 launcher is missing "
                f"required token: {token}"
            )

    write_complete_file(
        PRODUCTION_PATH,
        PRODUCTION_SOURCE,
    )

    write_complete_file(
        TEST_PATH,
        TEST_SOURCE,
    )

    installed_production = (
        PRODUCTION_PATH.read_text(
            encoding="utf-8"
        )
    )

    installed_test = (
        TEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    required_installed_tokens = (
        'SCHEMA_VERSION = "OLA-082"',
        (
            'UPSTREAM_GATE_SCHEMA_VERSION '
            '= "OLA-081"'
        ),
        (
            "checkpoint_count must be "
            "at least 2"
        ),
        (
            "OracleLiveContinuousRuntime"
            "IdentityChanged"
        ),
        "same_process_all_checkpoints",
        "checkpoint_record_hashes",
        "existing_runtime_observed_only",
        "acquisition_cycle_invoked",
    )

    for token in required_installed_tokens:
        if token not in installed_production:
            raise RuntimeError(
                "Installed OLA-082 production file "
                f"is missing token: {token}"
            )

    forbidden_tokens = (
        "subprocess",
        "Popen",
        "psycopg",
        "os.kill",
        "LOCK_FILE.unlink",
        "_acquire_runtime_lock",
        "_release_runtime_lock",
    )

    for token in forbidden_tokens:
        if token in installed_production:
            raise RuntimeError(
                "Installed OLA-082 contains forbidden "
                f"runtime action: {token}"
            )

    if (
        "checkpoint_count=2"
        not in installed_test
    ):
        raise RuntimeError(
            "Installed OLA-082 test does not "
            "require two checkpoints"
        )

    print(
        "[OK] Actual OLA-081 V3 contract verified"
    )

    print(
        "[OK] Actual OLA-068 passive monitor "
        "lineage verified"
    )

    print(
        "[OK] Actual OLA-074 guarded launcher "
        "contract verified"
    )

    print(
        "[OK] Two consecutive advancement "
        "checkpoints installed"
    )

    print(
        "[OK] Same-process identity enforcement installed"
    )

    print(
        "[OK] Upstream record-hash validation installed"
    )

    print(
        "[OK] Aggregate PostgreSQL advancement "
        "evidence installed"
    )

    print(
        "[OK] No runtime start, stop, restart, "
        "or lock mutation installed"
    )

    print(
        "[OK] Oracle read-only boundary preserved"
    )

    print(
        "\n[DONE] OLA-082 sustained advancement "
        "certification gate installed"
    )

    print("\nRun:")

    print(
        "py test_ola_082_oracle_live_continuous_"
        "runtime_sustained_advancement_"
        "certification_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )