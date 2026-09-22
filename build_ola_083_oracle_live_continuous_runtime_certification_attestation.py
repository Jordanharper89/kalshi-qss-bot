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
        "certification_attestation.py"
    )
)

TEST_PATH = (
    ROOT
    / (
        "test_ola_083_oracle_live_continuous_runtime_"
        "certification_attestation.py"
    )
)


PRODUCTION_SOURCE = r'''"""
OLA-083
Oracle Live Continuous Runtime Certification Attestation

Publishes durable, immutable, hash-verified evidence after the canonical
OLA-082 sustained runtime certification gate passes.

Production lineage:

- OLA-074 owns the guarded continuous runtime.
- OLA-068 passively observes PostgreSQL advancement.
- OLA-081 certifies one advancement window.
- OLA-082 certifies consecutive advancement windows from one process.
- OLA-083 publishes durable certification evidence.

This module does not start, stop, restart, import, or invoke the live
runtime. It does not mutate the runtime lock or PostgreSQL.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_sustained_advancement_certification_gate import (
    OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    evaluate_oracle_live_continuous_runtime_sustained_advancement,
)


SCHEMA_VERSION = "OLA-083"
ENGINE_ID = "OLA-083"

UPSTREAM_CERTIFICATION_SCHEMA_VERSION = "OLA-082"
UPSTREAM_ADVANCEMENT_SCHEMA_VERSION = "OLA-081"
UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_RUNTIME_SCHEMA_VERSION = "OLA-074"

EXPECTED_RUNTIME_MODE = "continuous_live_shadow"

EXPECTED_LAUNCHER = (
    "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
)

DEFAULT_CHECKPOINT_COUNT = 2

DEFAULT_OBSERVATION_WINDOW_SECONDS = 30.0

DEFAULT_RELATIVE_EVIDENCE_DIRECTORY = (
    Path("runtime")
    / "oracle_live_shadow"
    / "certifications"
    / "ola083"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False
POSTGRESQL_WRITE_PERFORMED = False
RUNTIME_STARTED = False
RUNTIME_STOPPED = False
RUNTIME_RESTARTED = False
RUNTIME_LOCK_MUTATED = False


class OracleLiveContinuousRuntimeCertificationAttestationError(
    RuntimeError
):
    """Base OLA-083 failure."""


class OracleLiveContinuousRuntimeCertificationAttestationContractError(
    OracleLiveContinuousRuntimeCertificationAttestationError
):
    """Malformed OLA-083 invocation or upstream evidence."""


class OracleLiveContinuousRuntimeCertificationPublicationError(
    OracleLiveContinuousRuntimeCertificationAttestationError
):
    """Durable certification publication failed."""


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(
        value,
        datetime,
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                f"{field_name} must be a datetime"
            )
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                f"{field_name} must be timezone-aware"
            )
        )

    return value


def canonicalize(
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
        return require_aware_datetime(
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
                    OracleLiveContinuousRuntimeCertificationAttestationContractError(
                        "canonical mapping keys must be strings"
                    )
                )

            result[key] = canonicalize(
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
            canonicalize(
                item
            )
            for item in value
        ]

    raise (
        OracleLiveContinuousRuntimeCertificationAttestationContractError(
            "unsupported canonical type: "
            f"{type(value).__name__}"
        )
    )


def canonical_json(
    value: Any,
) -> str:
    return json.dumps(
        canonicalize(
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


def require_positive_int(
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
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                f"{field_name} must be a positive int"
            )
        )

    return value


def require_positive_number(
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
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                f"{field_name} must be a positive number"
            )
        )

    normalized = float(
        value
    )

    if normalized <= 0.0:
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                f"{field_name} must be greater than zero"
            )
        )

    return normalized


def validate_upstream_certification(
    record: OracleLiveContinuousRuntimeSustainedAdvancementRecord,
) -> None:
    if not isinstance(
        record,
        OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream certification returned the wrong record type"
            )
        )

    if (
        record.schema_version
        != UPSTREAM_CERTIFICATION_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream certification schema must be OLA-082"
            )
        )

    if (
        record.engine_id
        != UPSTREAM_CERTIFICATION_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream certification engine must be OLA-082"
            )
        )

    if (
        record.certification_status
        != "certified"
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream runtime was not certified"
            )
        )

    if record.process_id < 1:
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream process_id must be positive"
            )
        )

    if (
        record.runtime_mode
        != EXPECTED_RUNTIME_MODE
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream runtime mode mismatch"
            )
        )

    if (
        record.launcher
        != EXPECTED_LAUNCHER
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream launcher mismatch"
            )
        )

    if (
        record.upstream_gate_schema_version
        != UPSTREAM_ADVANCEMENT_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream advancement schema mismatch"
            )
        )

    if (
        record.upstream_monitor_schema_version
        != UPSTREAM_MONITOR_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream passive monitor schema mismatch"
            )
        )

    if (
        record.upstream_lock_schema_version
        != UPSTREAM_RUNTIME_SCHEMA_VERSION
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream runtime schema mismatch"
            )
        )

    if record.checkpoint_count < 2:
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream certification requires at least two checkpoints"
            )
        )

    if (
        len(
            record.checkpoint_record_hashes
        )
        != record.checkpoint_count
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream checkpoint hash count mismatch"
            )
        )

    if (
        len(
            set(
                record.checkpoint_record_hashes
            )
        )
        != record.checkpoint_count
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream checkpoint hashes must be unique"
            )
        )

    if (
        record.total_observation_count_delta
        <= 0
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream observation count did not advance"
            )
        )

    if (
        record.total_latest_sequence_delta
        <= 0
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream canonical sequence did not advance"
            )
        )

    required_true_fields = (
        "all_checkpoints_advanced",
        "same_process_all_checkpoints",
        "process_remained_alive",
        "existing_runtime_observed_only",
        "read_only",
    )

    for field_name in required_true_fields:
        if (
            getattr(
                record,
                field_name,
            )
            is not True
        ):
            raise (
                OracleLiveContinuousRuntimeCertificationAttestationContractError(
                    "upstream safety field must be true: "
                    f"{field_name}"
                )
            )

    required_false_fields = (
        "acquisition_cycle_invoked",
        "scheduler_invoked",
        "runner_invoked",
        "execution_allowed",
        "alerts_allowed",
        "qseries_handoff_allowed",
        "trade_authorization_allowed",
        "order_placement_allowed",
        "funds_moved",
        "portfolio_mutated",
    )

    for field_name in required_false_fields:
        if (
            getattr(
                record,
                field_name,
            )
            is not False
        ):
            raise (
                OracleLiveContinuousRuntimeCertificationAttestationContractError(
                    "upstream safety field must be false: "
                    f"{field_name}"
                )
            )

    if (
        record.verify_record_hash()
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "upstream OLA-082 record hash is invalid"
            )
        )


@dataclass(
    frozen=True
)
class OracleLiveContinuousRuntimeCertificationAttestation:
    schema_version: str
    engine_id: str
    attestation_status: str

    attestation_id: str

    checked_at: datetime
    published_at: datetime

    process_id: int
    runtime_mode: str
    launcher: str

    upstream_certification_schema_version: str
    upstream_advancement_schema_version: str
    upstream_monitor_schema_version: str
    upstream_runtime_schema_version: str

    upstream_certification_record_hash: str
    checkpoint_record_hashes: tuple[
        str,
        ...,
    ]

    checkpoint_count: int
    observation_window_seconds_per_checkpoint: float
    total_observation_window_seconds: float

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

    evidence_file: str
    current_file: str

    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    postgresql_write_performed: bool
    runtime_started: bool
    runtime_stopped: bool
    runtime_restarted: bool
    runtime_lock_mutated: bool

    attestation_hash: str

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
            "attestation_status": (
                self.attestation_status
            ),
            "attestation_id": (
                self.attestation_id
            ),
            "checked_at": (
                self.checked_at
            ),
            "published_at": (
                self.published_at
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
            "upstream_certification_schema_version": (
                self.upstream_certification_schema_version
            ),
            "upstream_advancement_schema_version": (
                self.upstream_advancement_schema_version
            ),
            "upstream_monitor_schema_version": (
                self.upstream_monitor_schema_version
            ),
            "upstream_runtime_schema_version": (
                self.upstream_runtime_schema_version
            ),
            "upstream_certification_record_hash": (
                self.upstream_certification_record_hash
            ),
            "checkpoint_record_hashes": (
                self.checkpoint_record_hashes
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
            "evidence_file": (
                self.evidence_file
            ),
            "current_file": (
                self.current_file
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
            "postgresql_write_performed": (
                self.postgresql_write_performed
            ),
            "runtime_started": (
                self.runtime_started
            ),
            "runtime_stopped": (
                self.runtime_stopped
            ),
            "runtime_restarted": (
                self.runtime_restarted
            ),
            "runtime_lock_mutated": (
                self.runtime_lock_mutated
            ),
        }

        if include_hash:
            result["attestation_hash"] = (
                self.attestation_hash
            )

        return result

    def verify_attestation_hash(
        self,
    ) -> bool:
        return (
            self.attestation_hash
            == stable_hash(
                self.to_canonical_dict(
                    include_hash=False
                )
            )
        )


def atomic_write_json(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    path = Path(
        path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.name
        + "."
        + uuid4().hex
        + ".tmp"
    )

    serialized = (
        json.dumps(
            canonicalize(
                payload
            ),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as handle:
            handle.write(
                serialized
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

        temporary_path.replace(
            path
        )

    except Exception as exc:
        try:
            if temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            pass

        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "failed to publish certification file: "
                f"{path}"
            )
        ) from exc


def load_and_verify_attestation_file(
    path: Path,
) -> dict[str, Any]:
    path = Path(
        path
    )

    if not path.is_file():
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                f"attestation file not found: {path}"
            )
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
    ) as exc:
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                f"attestation file is invalid JSON: {path}"
            )
        ) from exc

    if not isinstance(
        payload,
        dict,
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "attestation file must contain a JSON object"
            )
        )

    recorded_hash = payload.get(
        "attestation_hash"
    )

    if not isinstance(
        recorded_hash,
        str,
    ) or not recorded_hash:
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "attestation_hash is missing"
            )
        )

    payload_without_hash = dict(
        payload
    )

    payload_without_hash.pop(
        "attestation_hash",
        None,
    )

    expected_hash = stable_hash(
        payload_without_hash
    )

    if (
        recorded_hash
        != expected_hash
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "attestation file hash verification failed"
            )
        )

    return payload


def publish_oracle_live_continuous_runtime_certification_attestation(
    *,
    repository_root: Path,
    checked_at: datetime,
    checkpoint_count: int = (
        DEFAULT_CHECKPOINT_COUNT
    ),
    observation_window_seconds: float = (
        DEFAULT_OBSERVATION_WINDOW_SECONDS
    ),
    evidence_directory: Path | None = None,
    certification_evaluator: Callable[
        ...,
        OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    ] = (
        evaluate_oracle_live_continuous_runtime_sustained_advancement
    ),
) -> OracleLiveContinuousRuntimeCertificationAttestation:
    repository_root = Path(
        repository_root
    ).resolve()

    if not repository_root.is_dir():
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "repository_root must exist"
            )
        )

    checked_at = require_aware_datetime(
        checked_at,
        "checked_at",
    )

    checkpoint_count = require_positive_int(
        checkpoint_count,
        "checkpoint_count",
    )

    if checkpoint_count < 2:
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "checkpoint_count must be at least 2"
            )
        )

    observation_window_seconds = (
        require_positive_number(
            observation_window_seconds,
            "observation_window_seconds",
        )
    )

    if not callable(
        certification_evaluator
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "certification_evaluator must be callable"
            )
        )

    if evidence_directory is None:
        resolved_evidence_directory = (
            repository_root
            / DEFAULT_RELATIVE_EVIDENCE_DIRECTORY
        )
    else:
        resolved_evidence_directory = Path(
            evidence_directory
        )

        if not resolved_evidence_directory.is_absolute():
            resolved_evidence_directory = (
                repository_root
                / resolved_evidence_directory
            )

    resolved_evidence_directory = (
        resolved_evidence_directory.resolve()
    )

    upstream_record = certification_evaluator(
        repository_root=repository_root,
        checked_at=checked_at,
        checkpoint_count=checkpoint_count,
        observation_window_seconds=(
            observation_window_seconds
        ),
    )

    validate_upstream_certification(
        upstream_record
    )

    published_at = utc_now()

    if (
        published_at
        < checked_at
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationAttestationContractError(
                "published_at cannot precede checked_at"
            )
        )

    attestation_id = (
        "ola083-"
        + published_at.strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        + "-"
        + upstream_record.record_hash[:16]
    )

    evidence_path = (
        resolved_evidence_directory
        / f"{attestation_id}.json"
    )

    current_path = (
        resolved_evidence_directory
        / "current.json"
    )

    relative_evidence_path = str(
        evidence_path.relative_to(
            repository_root
        )
    )

    relative_current_path = str(
        current_path.relative_to(
            repository_root
        )
    )

    record_without_hash = {
        "schema_version": (
            SCHEMA_VERSION
        ),
        "engine_id": (
            ENGINE_ID
        ),
        "attestation_status": (
            "certified"
        ),
        "attestation_id": (
            attestation_id
        ),
        "checked_at": (
            checked_at
        ),
        "published_at": (
            published_at
        ),
        "process_id": (
            upstream_record.process_id
        ),
        "runtime_mode": (
            upstream_record.runtime_mode
        ),
        "launcher": (
            upstream_record.launcher
        ),
        "upstream_certification_schema_version": (
            upstream_record.schema_version
        ),
        "upstream_advancement_schema_version": (
            upstream_record.upstream_gate_schema_version
        ),
        "upstream_monitor_schema_version": (
            upstream_record.upstream_monitor_schema_version
        ),
        "upstream_runtime_schema_version": (
            upstream_record.upstream_lock_schema_version
        ),
        "upstream_certification_record_hash": (
            upstream_record.record_hash
        ),
        "checkpoint_record_hashes": (
            upstream_record.checkpoint_record_hashes
        ),
        "checkpoint_count": (
            upstream_record.checkpoint_count
        ),
        "observation_window_seconds_per_checkpoint": (
            upstream_record.observation_window_seconds_per_checkpoint
        ),
        "total_observation_window_seconds": (
            upstream_record.total_observation_window_seconds
        ),
        "total_observation_count_delta": (
            upstream_record.total_observation_count_delta
        ),
        "total_latest_sequence_delta": (
            upstream_record.total_latest_sequence_delta
        ),
        "total_persistence_terminal_sequence_delta": (
            upstream_record.total_persistence_terminal_sequence_delta
        ),
        "all_checkpoints_advanced": (
            upstream_record.all_checkpoints_advanced
        ),
        "same_process_all_checkpoints": (
            upstream_record.same_process_all_checkpoints
        ),
        "process_remained_alive": (
            upstream_record.process_remained_alive
        ),
        "existing_runtime_observed_only": (
            upstream_record.existing_runtime_observed_only
        ),
        "acquisition_cycle_invoked": (
            upstream_record.acquisition_cycle_invoked
        ),
        "scheduler_invoked": (
            upstream_record.scheduler_invoked
        ),
        "runner_invoked": (
            upstream_record.runner_invoked
        ),
        "evidence_file": (
            relative_evidence_path
        ),
        "current_file": (
            relative_current_path
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
        "postgresql_write_performed": (
            POSTGRESQL_WRITE_PERFORMED
        ),
        "runtime_started": (
            RUNTIME_STARTED
        ),
        "runtime_stopped": (
            RUNTIME_STOPPED
        ),
        "runtime_restarted": (
            RUNTIME_RESTARTED
        ),
        "runtime_lock_mutated": (
            RUNTIME_LOCK_MUTATED
        ),
    }

    attestation = (
        OracleLiveContinuousRuntimeCertificationAttestation(
            **record_without_hash,
            attestation_hash=stable_hash(
                record_without_hash
            ),
        )
    )

    if (
        attestation.verify_attestation_hash()
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "constructed attestation hash is invalid"
            )
        )

    payload = (
        attestation.to_canonical_dict(
            include_hash=True
        )
    )

    atomic_write_json(
        evidence_path,
        payload,
    )

    verified_evidence = (
        load_and_verify_attestation_file(
            evidence_path
        )
    )

    if (
        verified_evidence.get(
            "attestation_hash"
        )
        != attestation.attestation_hash
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "immutable evidence hash mismatch"
            )
        )

    atomic_write_json(
        current_path,
        payload,
    )

    verified_current = (
        load_and_verify_attestation_file(
            current_path
        )
    )

    if (
        verified_current.get(
            "attestation_id"
        )
        != attestation.attestation_id
    ):
        raise (
            OracleLiveContinuousRuntimeCertificationPublicationError(
                "current certification pointer mismatch"
            )
        )

    return attestation
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_attestation import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeCertificationAttestation,
    load_and_verify_attestation_file,
    publish_oracle_live_continuous_runtime_certification_attestation,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-083")
    print(" DURABLE RUNTIME CERTIFICATION")
    print(" IMMUTABLE + CURRENT ATTESTATION")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-083"
    assert ENGINE_ID == "OLA-083"

    print(
        "[TEST] Run canonical OLA-082 certification"
    )

    print(
        "[INFO] Two OLA-081 checkpoints"
    )

    print(
        "[INFO] 30 seconds per checkpoint"
    )

    print(
        "[INFO] Existing OLA-074 runtime only"
    )

    print(
        "[INFO] Oracle will not be restarted"
    )

    record = (
        publish_oracle_live_continuous_runtime_certification_attestation(
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
        OracleLiveContinuousRuntimeCertificationAttestation,
    )

    assert record.schema_version == "OLA-083"
    assert record.engine_id == "OLA-083"

    assert (
        record.attestation_status
        == "certified"
    )

    assert record.attestation_id.startswith(
        "ola083-"
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
        record.upstream_certification_schema_version
        == "OLA-082"
    )

    assert (
        record.upstream_advancement_schema_version
        == "OLA-081"
    )

    assert (
        record.upstream_monitor_schema_version
        == "OLA-068"
    )

    assert (
        record.upstream_runtime_schema_version
        == "OLA-074"
    )

    assert record.checkpoint_count == 2

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
        record.postgresql_write_performed
        is False
    )

    assert record.runtime_started is False
    assert record.runtime_stopped is False
    assert record.runtime_restarted is False

    assert (
        record.runtime_lock_mutated
        is False
    )

    assert (
        record.verify_attestation_hash()
        is True
    )

    evidence_path = (
        ROOT
        / record.evidence_file
    )

    current_path = (
        ROOT
        / record.current_file
    )

    assert evidence_path.is_file()
    assert current_path.is_file()

    assert evidence_path != current_path

    evidence_payload = (
        load_and_verify_attestation_file(
            evidence_path
        )
    )

    current_payload = (
        load_and_verify_attestation_file(
            current_path
        )
    )

    assert (
        evidence_payload
        == current_payload
    )

    assert (
        evidence_payload[
            "attestation_id"
        ]
        == record.attestation_id
    )

    assert (
        evidence_payload[
            "attestation_hash"
        ]
        == record.attestation_hash
    )

    parsed_current = json.loads(
        current_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        parsed_current[
            "schema_version"
        ]
        == "OLA-083"
    )

    print(
        f"[PASS] Same live process certified: "
        f"{record.process_id}"
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
        f"[PASS] Immutable evidence: "
        f"{record.evidence_file}"
    )

    print(
        f"[PASS] Current certification: "
        f"{record.current_file}"
    )

    print(
        "[PASS] Attestation hash verified"
    )

    print(
        "[PASS] Immutable and current evidence match"
    )

    print(
        "[PASS] Existing runtime observed only"
    )

    print(
        "[PASS] No runtime or lock mutation"
    )

    print(
        "[PASS] No PostgreSQL writes by OLA-083"
    )

    print(
        "[PASS] Oracle remained read-only"
    )

    print(
        "[PASS] OLA-083 durable runtime "
        "certification attestation"
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
        path.name + ".ola083.tmp"
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


def require_file(
    path: Path,
) -> None:
    if not path.is_file():
        raise FileNotFoundError(
            "Required repository file is missing: "
            f"{path}"
        )


def require_tokens(
    source: str,
    tokens: tuple[str, ...],
    description: str,
) -> None:
    for token in tokens:
        if token not in source:
            raise RuntimeError(
                f"{description} is missing token: "
                f"{token}"
            )


def forbid_tokens(
    source: str,
    tokens: tuple[str, ...],
    description: str,
) -> None:
    for token in tokens:
        if token in source:
            raise RuntimeError(
                f"{description} contains forbidden token: "
                f"{token}"
            )


def main() -> int:
    print("========================================")
    print(" OLA-083 INSTALLER")
    print(" DURABLE RUNTIME CERTIFICATION")
    print(" IMMUTABLE + CURRENT ATTESTATION")
    print("========================================")

    upstream_production_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / (
            "oracle_live_continuous_runtime_"
            "sustained_advancement_certification_gate.py"
        )
    )

    upstream_test_path = (
        ROOT
        / (
            "test_ola_082_oracle_live_continuous_runtime_"
            "sustained_advancement_certification_gate.py"
        )
    )

    advancement_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / (
            "oracle_live_continuous_runtime_"
            "advancement_gate.py"
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
        upstream_production_path,
        upstream_test_path,
        advancement_path,
        launcher_path,
    ):
        require_file(
            required_path
        )

    upstream_source = (
        upstream_production_path.read_text(
            encoding="utf-8"
        )
    )

    require_tokens(
        upstream_source,
        (
            'SCHEMA_VERSION = "OLA-082"',
            (
                'UPSTREAM_GATE_SCHEMA_VERSION '
                '= "OLA-081"'
            ),
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
                "OracleLiveContinuousRuntime"
                "SustainedAdvancementRecord:"
            ),
            (
                "def evaluate_oracle_live_continuous_"
                "runtime_sustained_advancement("
            ),
            "checkpoint_record_hashes",
            "same_process_all_checkpoints",
            "verify_record_hash",
        ),
        "Actual OLA-082 production contract",
    )

    advancement_source = (
        advancement_path.read_text(
            encoding="utf-8"
        )
    )

    require_tokens(
        advancement_source,
        (
            'SCHEMA_VERSION = "OLA-081"',
            (
                'UPSTREAM_MONITOR_SCHEMA_VERSION '
                '= "OLA-068"'
            ),
            (
                'UPSTREAM_LOCK_SCHEMA_VERSION '
                '= "OLA-074"'
            ),
            "postgresql_persistence_advanced",
            "existing_runtime_observed_only",
        ),
        "Actual OLA-081 production contract",
    )

    launcher_source = (
        launcher_path.read_text(
            encoding="utf-8"
        )
    )

    require_tokens(
        launcher_source,
        (
            'SCHEMA_VERSION = "OLA-074"',
            '"continuous_live_shadow"',
            '"read_only": True',
            '"execution_allowed": False',
            '"order_placement_allowed": False',
        ),
        "Actual OLA-074 guarded launcher",
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

    require_tokens(
        installed_production,
        (
            'SCHEMA_VERSION = "OLA-083"',
            (
                'UPSTREAM_CERTIFICATION_SCHEMA_VERSION '
                '= "OLA-082"'
            ),
            (
                "class "
                "OracleLiveContinuousRuntime"
                "CertificationAttestation:"
            ),
            (
                "def publish_oracle_live_continuous_"
                "runtime_certification_attestation("
            ),
            "atomic_write_json",
            "load_and_verify_attestation_file",
            "attestation_hash",
            "upstream_certification_record_hash",
            "runtime_lock_mutated",
            "postgresql_write_performed",
        ),
        "Installed OLA-083 production file",
    )

    require_tokens(
        installed_test,
        (
            "checkpoint_count=2",
            "observation_window_seconds=30.0",
            "evidence_payload",
            "current_payload",
            "verify_attestation_hash",
        ),
        "Installed OLA-083 test",
    )

    forbid_tokens(
        installed_production,
        (
            "subprocess",
            "Popen",
            "os.kill",
            "psycopg",
            "psycopg2",
            "_acquire_runtime_lock",
            "_release_runtime_lock",
            "LOCK_FILE.unlink",
        ),
        "Installed OLA-083 production file",
    )

    print(
        "[OK] Actual OLA-082 certification "
        "contract verified"
    )

    print(
        "[OK] Actual OLA-081 advancement "
        "contract verified"
    )

    print(
        "[OK] Actual OLA-068 monitor lineage verified"
    )

    print(
        "[OK] Actual OLA-074 guarded runtime "
        "contract verified"
    )

    print(
        "[OK] Immutable certification file installed"
    )

    print(
        "[OK] Atomic current certification "
        "publication installed"
    )

    print(
        "[OK] Attestation hash verification installed"
    )

    print(
        "[OK] Upstream certification hash "
        "lineage installed"
    )

    print(
        "[OK] No runtime start, stop, restart, "
        "or lock mutation installed"
    )

    print(
        "[OK] No PostgreSQL writes installed"
    )

    print(
        "[OK] Oracle read-only boundary preserved"
    )

    print(
        "\n[DONE] OLA-083 durable runtime "
        "certification attestation installed"
    )

    print("\nRun:")

    print(
        "python "
        "test_ola_083_oracle_live_continuous_"
        "runtime_certification_attestation.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )