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
        "current_certification_status_gate.py"
    )
)

TEST_PATH = (
    ROOT
    / (
        "test_ola_084_oracle_live_continuous_runtime_"
        "current_certification_status_gate.py"
    )
)


PRODUCTION_SOURCE = r'''"""
OLA-084
Oracle Live Continuous Runtime Current Certification Status Gate

Provides an immediate operator-facing certification status by validating
the durable OLA-083 current attestation and its immutable evidence file.

Canonical lineage:

- OLA-074 guarded continuous runtime
- OLA-068 passive PostgreSQL advancement monitor
- OLA-081 live advancement gate
- OLA-082 sustained advancement certification
- OLA-083 durable certification attestation
- OLA-084 current certification status gate

OLA-084 does not rerun OLA-082, contact PostgreSQL, start or stop Oracle,
invoke acquisition, or mutate the OLA-074 runtime lock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_attestation import (
    load_and_verify_attestation_file,
)


SCHEMA_VERSION = "OLA-084"
ENGINE_ID = "OLA-084"

UPSTREAM_ATTESTATION_SCHEMA_VERSION = "OLA-083"
UPSTREAM_CERTIFICATION_SCHEMA_VERSION = "OLA-082"
UPSTREAM_ADVANCEMENT_SCHEMA_VERSION = "OLA-081"
UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_RUNTIME_SCHEMA_VERSION = "OLA-074"

EXPECTED_RUNTIME_MODE = "continuous_live_shadow"

EXPECTED_LAUNCHER = (
    "run_oracle_live_shadow_CONTINUOUS_GUARDED.py"
)

DEFAULT_CURRENT_RELATIVE_PATH = (
    Path("runtime")
    / "oracle_live_shadow"
    / "certifications"
    / "ola083"
    / "current.json"
)

DEFAULT_MAXIMUM_CERTIFICATION_AGE_SECONDS = (
    24.0
    * 60.0
    * 60.0
)

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

POSTGRESQL_READ_PERFORMED = False
POSTGRESQL_WRITE_PERFORMED = False

RUNTIME_STARTED = False
RUNTIME_STOPPED = False
RUNTIME_RESTARTED = False
RUNTIME_IMPORTED = False
RUNTIME_INVOKED = False
RUNTIME_LOCK_MUTATED = False

FILES_WRITTEN = False


class OracleLiveContinuousRuntimeCurrentCertificationStatusError(
    RuntimeError
):
    """Base OLA-084 failure."""


class OracleLiveContinuousRuntimeCurrentCertificationContractError(
    OracleLiveContinuousRuntimeCurrentCertificationStatusError
):
    """Malformed invocation or certification contract."""


class OracleLiveContinuousRuntimeCurrentCertificationMissing(
    OracleLiveContinuousRuntimeCurrentCertificationStatusError
):
    """No current OLA-083 certification exists."""


class OracleLiveContinuousRuntimeCurrentCertificationExpired(
    OracleLiveContinuousRuntimeCurrentCertificationStatusError
):
    """The current certification is older than policy permits."""


class OracleLiveContinuousRuntimeCurrentCertificationMismatch(
    OracleLiveContinuousRuntimeCurrentCertificationStatusError
):
    """Current and immutable OLA-083 evidence do not match."""


class OracleLiveContinuousRuntimeCurrentCertificationUnsafe(
    OracleLiveContinuousRuntimeCurrentCertificationStatusError
):
    """The current certification violates Oracle safety boundaries."""


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
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be a datetime"
            )
        )

    if (
        value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be timezone-aware"
            )
        )

    return value


def parse_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(
        value,
        str,
    ) or not value.strip():
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be a non-empty datetime string"
            )
        )

    normalized = value.strip()

    if normalized.endswith(
        "Z"
    ):
        normalized = (
            normalized[:-1]
            + "+00:00"
        )

    try:
        parsed = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} is not valid ISO-8601"
            )
        ) from exc

    return require_aware_datetime(
        parsed,
        field_name,
    )


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
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be a positive number"
            )
        )

    normalized = float(
        value
    )

    if normalized <= 0.0:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be greater than zero"
            )
        )

    return normalized


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
                    OracleLiveContinuousRuntimeCurrentCertificationContractError(
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
        OracleLiveContinuousRuntimeCurrentCertificationContractError(
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


def require_string(
    payload: Mapping[str, Any],
    field_name: str,
) -> str:
    value = payload.get(
        field_name
    )

    if not isinstance(
        value,
        str,
    ) or not value.strip():
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be a non-empty string"
            )
        )

    return value.strip()


def require_positive_int_field(
    payload: Mapping[str, Any],
    field_name: str,
) -> int:
    value = payload.get(
        field_name
    )

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
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} must be a positive int"
            )
        )

    return value


def require_boolean_field(
    payload: Mapping[str, Any],
    field_name: str,
    expected: bool,
) -> None:
    value = payload.get(
        field_name
    )

    if value is not expected:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationUnsafe(
                f"{field_name} must be {expected}"
            )
        )


def resolve_repository_file(
    *,
    repository_root: Path,
    recorded_path: str,
    field_name: str,
) -> Path:
    candidate = Path(
        recorded_path
    )

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (
            repository_root
            / candidate
        ).resolve()

    try:
        resolved.relative_to(
            repository_root
        )
    except ValueError as exc:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                f"{field_name} escapes repository_root"
            )
        ) from exc

    return resolved


def validate_attestation_contract(
    payload: Mapping[str, Any],
) -> None:
    expected_strings = {
        "schema_version": (
            UPSTREAM_ATTESTATION_SCHEMA_VERSION
        ),
        "engine_id": (
            UPSTREAM_ATTESTATION_SCHEMA_VERSION
        ),
        "attestation_status": (
            "certified"
        ),
        "runtime_mode": (
            EXPECTED_RUNTIME_MODE
        ),
        "launcher": (
            EXPECTED_LAUNCHER
        ),
        "upstream_certification_schema_version": (
            UPSTREAM_CERTIFICATION_SCHEMA_VERSION
        ),
        "upstream_advancement_schema_version": (
            UPSTREAM_ADVANCEMENT_SCHEMA_VERSION
        ),
        "upstream_monitor_schema_version": (
            UPSTREAM_MONITOR_SCHEMA_VERSION
        ),
        "upstream_runtime_schema_version": (
            UPSTREAM_RUNTIME_SCHEMA_VERSION
        ),
    }

    for field_name, expected in (
        expected_strings.items()
    ):
        actual = require_string(
            payload,
            field_name,
        )

        if actual != expected:
            raise (
                OracleLiveContinuousRuntimeCurrentCertificationContractError(
                    f"{field_name} must be {expected}"
                )
            )

    attestation_id = require_string(
        payload,
        "attestation_id",
    )

    if not attestation_id.startswith(
        "ola083-"
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "attestation_id must begin with ola083-"
            )
        )

    require_string(
        payload,
        "attestation_hash",
    )

    require_string(
        payload,
        "upstream_certification_record_hash",
    )

    process_id = require_positive_int_field(
        payload,
        "process_id",
    )

    if process_id < 1:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "process_id must be positive"
            )
        )

    checkpoint_count = (
        require_positive_int_field(
            payload,
            "checkpoint_count",
        )
    )

    if checkpoint_count < 2:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "checkpoint_count must be at least 2"
            )
        )

    checkpoint_hashes = payload.get(
        "checkpoint_record_hashes"
    )

    if not isinstance(
        checkpoint_hashes,
        list,
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "checkpoint_record_hashes must be a list"
            )
        )

    if (
        len(
            checkpoint_hashes
        )
        != checkpoint_count
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "checkpoint hash count mismatch"
            )
        )

    normalized_hashes: list[str] = []

    for checkpoint_hash in checkpoint_hashes:
        if not isinstance(
            checkpoint_hash,
            str,
        ) or not checkpoint_hash:
            raise (
                OracleLiveContinuousRuntimeCurrentCertificationContractError(
                    "checkpoint hashes must be non-empty strings"
                )
            )

        normalized_hashes.append(
            checkpoint_hash
        )

    if (
        len(
            set(
                normalized_hashes
            )
        )
        != checkpoint_count
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "checkpoint hashes must be unique"
            )
        )

    for field_name in (
        "total_observation_count_delta",
        "total_latest_sequence_delta",
    ):
        require_positive_int_field(
            payload,
            field_name,
        )

    require_boolean_field(
        payload,
        "all_checkpoints_advanced",
        True,
    )

    require_boolean_field(
        payload,
        "same_process_all_checkpoints",
        True,
    )

    require_boolean_field(
        payload,
        "process_remained_alive",
        True,
    )

    require_boolean_field(
        payload,
        "existing_runtime_observed_only",
        True,
    )

    require_boolean_field(
        payload,
        "read_only",
        True,
    )

    for field_name in (
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
        "postgresql_write_performed",
        "runtime_started",
        "runtime_stopped",
        "runtime_restarted",
        "runtime_lock_mutated",
    ):
        require_boolean_field(
            payload,
            field_name,
            False,
        )


@dataclass(
    frozen=True
)
class OracleLiveContinuousRuntimeCurrentCertificationStatus:
    schema_version: str
    engine_id: str

    status: str
    certified: bool
    certification_fresh: bool

    checked_at: datetime
    certification_published_at: datetime
    certification_age_seconds: float
    maximum_certification_age_seconds: float

    attestation_id: str
    attestation_hash: str

    process_id: int
    runtime_mode: str
    launcher: str

    upstream_attestation_schema_version: str
    upstream_certification_schema_version: str
    upstream_advancement_schema_version: str
    upstream_monitor_schema_version: str
    upstream_runtime_schema_version: str

    checkpoint_count: int
    total_observation_count_delta: int
    total_latest_sequence_delta: int
    total_persistence_terminal_sequence_delta: int

    current_file: str
    immutable_evidence_file: str

    current_hash_verified: bool
    immutable_hash_verified: bool
    current_matches_immutable: bool
    lineage_verified: bool
    safety_boundary_verified: bool

    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    postgresql_read_performed: bool
    postgresql_write_performed: bool

    runtime_started: bool
    runtime_stopped: bool
    runtime_restarted: bool
    runtime_imported: bool
    runtime_invoked: bool
    runtime_lock_mutated: bool

    files_written: bool

    status_hash: str

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
            "status": (
                self.status
            ),
            "certified": (
                self.certified
            ),
            "certification_fresh": (
                self.certification_fresh
            ),
            "checked_at": (
                self.checked_at
            ),
            "certification_published_at": (
                self.certification_published_at
            ),
            "certification_age_seconds": (
                self.certification_age_seconds
            ),
            "maximum_certification_age_seconds": (
                self.maximum_certification_age_seconds
            ),
            "attestation_id": (
                self.attestation_id
            ),
            "attestation_hash": (
                self.attestation_hash
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
            "upstream_attestation_schema_version": (
                self.upstream_attestation_schema_version
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
            "checkpoint_count": (
                self.checkpoint_count
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
            "current_file": (
                self.current_file
            ),
            "immutable_evidence_file": (
                self.immutable_evidence_file
            ),
            "current_hash_verified": (
                self.current_hash_verified
            ),
            "immutable_hash_verified": (
                self.immutable_hash_verified
            ),
            "current_matches_immutable": (
                self.current_matches_immutable
            ),
            "lineage_verified": (
                self.lineage_verified
            ),
            "safety_boundary_verified": (
                self.safety_boundary_verified
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
            "postgresql_read_performed": (
                self.postgresql_read_performed
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
            "runtime_imported": (
                self.runtime_imported
            ),
            "runtime_invoked": (
                self.runtime_invoked
            ),
            "runtime_lock_mutated": (
                self.runtime_lock_mutated
            ),
            "files_written": (
                self.files_written
            ),
        }

        if include_hash:
            result["status_hash"] = (
                self.status_hash
            )

        return result

    def verify_status_hash(
        self,
    ) -> bool:
        return (
            self.status_hash
            == stable_hash(
                self.to_canonical_dict(
                    include_hash=False
                )
            )
        )


def evaluate_oracle_live_continuous_runtime_current_certification_status(
    *,
    repository_root: Path,
    checked_at: datetime,
    maximum_certification_age_seconds: float = (
        DEFAULT_MAXIMUM_CERTIFICATION_AGE_SECONDS
    ),
    current_relative_path: Path = (
        DEFAULT_CURRENT_RELATIVE_PATH
    ),
) -> OracleLiveContinuousRuntimeCurrentCertificationStatus:
    repository_root = Path(
        repository_root
    ).resolve()

    if not repository_root.is_dir():
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "repository_root must exist"
            )
        )

    checked_at = require_aware_datetime(
        checked_at,
        "checked_at",
    )

    maximum_certification_age_seconds = (
        require_positive_number(
            maximum_certification_age_seconds,
            "maximum_certification_age_seconds",
        )
    )

    current_relative_path = Path(
        current_relative_path
    )

    if current_relative_path.is_absolute():
        current_path = (
            current_relative_path.resolve()
        )
    else:
        current_path = (
            repository_root
            / current_relative_path
        ).resolve()

    try:
        current_path.relative_to(
            repository_root
        )
    except ValueError as exc:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "current certification path escapes repository_root"
            )
        ) from exc

    if not current_path.is_file():
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationMissing(
                "current OLA-083 certification not found: "
                f"{current_path}"
            )
        )

    current_payload = (
        load_and_verify_attestation_file(
            current_path
        )
    )

    validate_attestation_contract(
        current_payload
    )

    recorded_current_file = (
        require_string(
            current_payload,
            "current_file",
        )
    )

    recorded_evidence_file = (
        require_string(
            current_payload,
            "evidence_file",
        )
    )

    recorded_current_path = (
        resolve_repository_file(
            repository_root=repository_root,
            recorded_path=recorded_current_file,
            field_name="current_file",
        )
    )

    evidence_path = (
        resolve_repository_file(
            repository_root=repository_root,
            recorded_path=recorded_evidence_file,
            field_name="evidence_file",
        )
    )

    if (
        recorded_current_path
        != current_path
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationMismatch(
                "recorded current_file does not match the file evaluated"
            )
        )

    if not evidence_path.is_file():
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationMissing(
                "immutable OLA-083 evidence not found: "
                f"{evidence_path}"
            )
        )

    immutable_payload = (
        load_and_verify_attestation_file(
            evidence_path
        )
    )

    validate_attestation_contract(
        immutable_payload
    )

    if (
        current_payload
        != immutable_payload
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationMismatch(
                "current certification does not match immutable evidence"
            )
        )

    published_at = (
        parse_aware_datetime(
            current_payload.get(
                "published_at"
            ),
            "published_at",
        )
    )

    if checked_at < published_at:
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "checked_at cannot precede certification published_at"
            )
        )

    certification_age_seconds = max(
        0.0,
        (
            checked_at
            - published_at
        ).total_seconds(),
    )

    if (
        certification_age_seconds
        > maximum_certification_age_seconds
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationExpired(
                "current certification expired: "
                f"age={certification_age_seconds:.3f}s, "
                "maximum="
                f"{maximum_certification_age_seconds:.3f}s"
            )
        )

    process_id = require_positive_int_field(
        current_payload,
        "process_id",
    )

    checkpoint_count = (
        require_positive_int_field(
            current_payload,
            "checkpoint_count",
        )
    )

    total_observation_count_delta = (
        require_positive_int_field(
            current_payload,
            "total_observation_count_delta",
        )
    )

    total_latest_sequence_delta = (
        require_positive_int_field(
            current_payload,
            "total_latest_sequence_delta",
        )
    )

    persistence_delta_value = (
        current_payload.get(
            "total_persistence_terminal_sequence_delta"
        )
    )

    if (
        isinstance(
            persistence_delta_value,
            bool,
        )
        or not isinstance(
            persistence_delta_value,
            int,
        )
        or persistence_delta_value < 0
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "total_persistence_terminal_sequence_delta "
                "must be a non-negative int"
            )
        )

    record_without_hash = {
        "schema_version": (
            SCHEMA_VERSION
        ),
        "engine_id": (
            ENGINE_ID
        ),
        "status": (
            "certified_current"
        ),
        "certified": (
            True
        ),
        "certification_fresh": (
            True
        ),
        "checked_at": (
            checked_at
        ),
        "certification_published_at": (
            published_at
        ),
        "certification_age_seconds": (
            certification_age_seconds
        ),
        "maximum_certification_age_seconds": (
            maximum_certification_age_seconds
        ),
        "attestation_id": (
            require_string(
                current_payload,
                "attestation_id",
            )
        ),
        "attestation_hash": (
            require_string(
                current_payload,
                "attestation_hash",
            )
        ),
        "process_id": (
            process_id
        ),
        "runtime_mode": (
            require_string(
                current_payload,
                "runtime_mode",
            )
        ),
        "launcher": (
            require_string(
                current_payload,
                "launcher",
            )
        ),
        "upstream_attestation_schema_version": (
            require_string(
                current_payload,
                "schema_version",
            )
        ),
        "upstream_certification_schema_version": (
            require_string(
                current_payload,
                "upstream_certification_schema_version",
            )
        ),
        "upstream_advancement_schema_version": (
            require_string(
                current_payload,
                "upstream_advancement_schema_version",
            )
        ),
        "upstream_monitor_schema_version": (
            require_string(
                current_payload,
                "upstream_monitor_schema_version",
            )
        ),
        "upstream_runtime_schema_version": (
            require_string(
                current_payload,
                "upstream_runtime_schema_version",
            )
        ),
        "checkpoint_count": (
            checkpoint_count
        ),
        "total_observation_count_delta": (
            total_observation_count_delta
        ),
        "total_latest_sequence_delta": (
            total_latest_sequence_delta
        ),
        "total_persistence_terminal_sequence_delta": (
            persistence_delta_value
        ),
        "current_file": str(
            current_path.relative_to(
                repository_root
            )
        ),
        "immutable_evidence_file": str(
            evidence_path.relative_to(
                repository_root
            )
        ),
        "current_hash_verified": (
            True
        ),
        "immutable_hash_verified": (
            True
        ),
        "current_matches_immutable": (
            True
        ),
        "lineage_verified": (
            True
        ),
        "safety_boundary_verified": (
            True
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
        "postgresql_read_performed": (
            POSTGRESQL_READ_PERFORMED
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
        "runtime_imported": (
            RUNTIME_IMPORTED
        ),
        "runtime_invoked": (
            RUNTIME_INVOKED
        ),
        "runtime_lock_mutated": (
            RUNTIME_LOCK_MUTATED
        ),
        "files_written": (
            FILES_WRITTEN
        ),
    }

    status_record = (
        OracleLiveContinuousRuntimeCurrentCertificationStatus(
            **record_without_hash,
            status_hash=stable_hash(
                record_without_hash
            ),
        )
    )

    if (
        status_record.verify_status_hash()
        is not True
    ):
        raise (
            OracleLiveContinuousRuntimeCurrentCertificationContractError(
                "constructed OLA-084 status hash is invalid"
            )
        )

    return status_record
'''


TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_current_certification_status_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeCurrentCertificationStatus,
    evaluate_oracle_live_continuous_runtime_current_certification_status,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-084")
    print(" CURRENT RUNTIME CERTIFICATION STATUS")
    print(" FAST HASH-VERIFIED OPERATOR GATE")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-084"
    assert ENGINE_ID == "OLA-084"

    print(
        "[TEST] Load OLA-083 current certification"
    )

    print(
        "[TEST] Verify immutable evidence match"
    )

    print(
        "[TEST] Verify certification freshness"
    )

    print(
        "[INFO] No 60-second recertification will run"
    )

    print(
        "[INFO] No PostgreSQL connection will be opened"
    )

    print(
        "[INFO] Oracle runtime will not be touched"
    )

    checked_at = datetime.now(
        timezone.utc
    )

    record = (
        evaluate_oracle_live_continuous_runtime_current_certification_status(
            repository_root=ROOT,
            checked_at=checked_at,
            maximum_certification_age_seconds=(
                24.0
                * 60.0
                * 60.0
            ),
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeCurrentCertificationStatus,
    )

    assert record.schema_version == "OLA-084"
    assert record.engine_id == "OLA-084"

    assert (
        record.status
        == "certified_current"
    )

    assert record.certified is True

    assert (
        record.certification_fresh
        is True
    )

    assert (
        record.certification_age_seconds
        >= 0.0
    )

    assert (
        record.certification_age_seconds
        <= record.maximum_certification_age_seconds
    )

    assert record.attestation_id.startswith(
        "ola083-"
    )

    assert record.attestation_hash

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
        record.upstream_attestation_schema_version
        == "OLA-083"
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

    assert record.checkpoint_count >= 2

    assert (
        record.total_observation_count_delta
        > 0
    )

    assert (
        record.total_latest_sequence_delta
        > 0
    )

    assert (
        record.current_hash_verified
        is True
    )

    assert (
        record.immutable_hash_verified
        is True
    )

    assert (
        record.current_matches_immutable
        is True
    )

    assert (
        record.lineage_verified
        is True
    )

    assert (
        record.safety_boundary_verified
        is True
    )

    assert record.read_only is True

    assert (
        record.execution_allowed
        is False
    )

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

    assert (
        record.portfolio_mutated
        is False
    )

    assert (
        record.postgresql_read_performed
        is False
    )

    assert (
        record.postgresql_write_performed
        is False
    )

    assert record.runtime_started is False
    assert record.runtime_stopped is False

    assert (
        record.runtime_restarted
        is False
    )

    assert (
        record.runtime_imported
        is False
    )

    assert (
        record.runtime_invoked
        is False
    )

    assert (
        record.runtime_lock_mutated
        is False
    )

    assert record.files_written is False

    assert (
        record.verify_status_hash()
        is True
    )

    print(
        "[PASS] Current certification is valid"
    )

    print(
        f"[PASS] Certified process: "
        f"{record.process_id}"
    )

    print(
        f"[PASS] Attestation: "
        f"{record.attestation_id}"
    )

    print(
        f"[PASS] Certification age: "
        f"{record.certification_age_seconds:.3f} seconds"
    )

    print(
        f"[PASS] Certified observation increase: "
        f"{record.total_observation_count_delta}"
    )

    print(
        f"[PASS] Certified sequence increase: "
        f"{record.total_latest_sequence_delta}"
    )

    print(
        f"[PASS] Current file: "
        f"{record.current_file}"
    )

    print(
        f"[PASS] Immutable evidence: "
        f"{record.immutable_evidence_file}"
    )

    print(
        "[PASS] Current attestation hash verified"
    )

    print(
        "[PASS] Immutable evidence hash verified"
    )

    print(
        "[PASS] Current and immutable evidence match"
    )

    print(
        "[PASS] OLA-074 through OLA-083 lineage verified"
    )

    print(
        "[PASS] Oracle safety boundary verified"
    )

    print(
        "[PASS] No PostgreSQL or runtime access performed"
    )

    print(
        "[PASS] OLA-084 current certification status gate"
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
        path.name + ".ola084.tmp"
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
    print(" OLA-084 INSTALLER")
    print(" CURRENT RUNTIME CERTIFICATION STATUS")
    print(" FAST HASH-VERIFIED OPERATOR GATE")
    print("========================================")

    upstream_production_path = (
        ROOT
        / "qseries_v2"
        / "oracle_intelligence"
        / "live_acquisition"
        / (
            "oracle_live_continuous_runtime_"
            "certification_attestation.py"
        )
    )

    upstream_test_path = (
        ROOT
        / (
            "test_ola_083_oracle_live_continuous_runtime_"
            "certification_attestation.py"
        )
    )

    current_attestation_path = (
        ROOT
        / "runtime"
        / "oracle_live_shadow"
        / "certifications"
        / "ola083"
        / "current.json"
    )

    require_file(
        upstream_production_path
    )

    require_file(
        upstream_test_path
    )

    require_file(
        current_attestation_path
    )

    upstream_source = (
        upstream_production_path.read_text(
            encoding="utf-8"
        )
    )

    require_tokens(
        upstream_source,
        (
            'SCHEMA_VERSION = "OLA-083"',
            (
                'UPSTREAM_CERTIFICATION_SCHEMA_VERSION '
                '= "OLA-082"'
            ),
            (
                'UPSTREAM_ADVANCEMENT_SCHEMA_VERSION '
                '= "OLA-081"'
            ),
            (
                'UPSTREAM_MONITOR_SCHEMA_VERSION '
                '= "OLA-068"'
            ),
            (
                'UPSTREAM_RUNTIME_SCHEMA_VERSION '
                '= "OLA-074"'
            ),
            (
                "def load_and_verify_attestation_file("
            ),
            "attestation_hash",
            "evidence_file",
            "current_file",
            "runtime_lock_mutated",
            "postgresql_write_performed",
        ),
        "Actual OLA-083 production contract",
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
            'SCHEMA_VERSION = "OLA-084"',
            (
                'UPSTREAM_ATTESTATION_SCHEMA_VERSION '
                '= "OLA-083"'
            ),
            (
                "class OracleLiveContinuousRuntime"
                "CurrentCertificationStatus:"
            ),
            (
                "def evaluate_oracle_live_continuous_"
                "runtime_current_certification_status("
            ),
            "current_matches_immutable",
            "certification_age_seconds",
            "maximum_certification_age_seconds",
            "verify_status_hash",
            "runtime_imported",
            "files_written",
        ),
        "Installed OLA-084 production file",
    )

    require_tokens(
        installed_test,
        (
            "maximum_certification_age_seconds=(",
            "current_hash_verified",
            "immutable_hash_verified",
            "current_matches_immutable",
            "verify_status_hash",
        ),
        "Installed OLA-084 test",
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
            "urlopen",
            "requests.",
        ),
        "Installed OLA-084 production file",
    )

    print(
        "[OK] Actual OLA-083 attestation "
        "contract verified"
    )

    print(
        "[OK] Existing OLA-083 current "
        "certification verified present"
    )

    print(
        "[OK] Current attestation hash gate installed"
    )

    print(
        "[OK] Immutable evidence hash gate installed"
    )

    print(
        "[OK] Current-to-immutable equality gate installed"
    )

    print(
        "[OK] Certification freshness policy installed"
    )

    print(
        "[OK] Complete OLA-074 through OLA-083 "
        "lineage validation installed"
    )

    print(
        "[OK] Oracle safety boundary validation installed"
    )

    print(
        "[OK] No PostgreSQL access installed"
    )

    print(
        "[OK] No runtime or lock access installed"
    )

    print(
        "[OK] No file writes installed"
    )

    print(
        "\n[DONE] OLA-084 current runtime "
        "certification status gate installed"
    )

    print("\nRun:")

    print(
        "python "
        "test_ola_084_oracle_live_continuous_"
        "runtime_current_certification_status_gate.py"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )