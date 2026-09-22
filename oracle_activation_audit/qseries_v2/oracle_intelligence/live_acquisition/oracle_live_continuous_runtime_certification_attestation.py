"""
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
