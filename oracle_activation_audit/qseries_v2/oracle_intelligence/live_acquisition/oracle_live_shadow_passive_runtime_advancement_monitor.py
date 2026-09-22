from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Protocol


SCHEMA_VERSION = "OLA-068"
ENGINE_ID = "OLA-068"

READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PassiveRuntimeMonitorError(RuntimeError):
    """Base OLA-068 runtime-monitor failure."""


class PassiveRuntimeConfigurationError(
    PassiveRuntimeMonitorError
):
    """Raised when passive-monitor configuration is invalid."""


class PassiveRuntimeObservationError(
    PassiveRuntimeMonitorError
):
    """Raised when passive observation cannot be completed."""


class PassiveRuntimeInvariantError(
    PassiveRuntimeMonitorError
):
    """Raised when an OLA-068 invariant is violated."""


class RuntimeSnapshotProbe(Protocol):
    def __call__(self) -> "OraclePassiveRuntimeSnapshot":
        ...


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_aware_datetime(
    value: datetime,
    name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PassiveRuntimeInvariantError(
            f"{name} must be a datetime."
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PassiveRuntimeInvariantError(
            f"{name} must be timezone-aware."
        )

    return value.astimezone(timezone.utc)


def _freeze_mapping(
    payload: Mapping[str, Any],
) -> Mapping[str, Any]:
    return MappingProxyType(dict(payload))


def _normalize_for_hash(value: Any) -> Any:
    """
    Convert immutable and structured values into deterministic
    JSON-compatible primitives before hashing.

    The original OLA-068 implementation passed MappingProxyType
    directly to json.dumps(). Because json.dumps() does not treat
    MappingProxyType as a normal dictionary, default=str converted
    the entire mapping into a string. Tests hashed a regular dict,
    producing a different digest.

    This function guarantees that dict and MappingProxyType values
    produce the exact same canonical hash.
    """
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_for_hash(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _normalize_for_hash(item)
            for item in value
        ]

    if isinstance(value, datetime):
        return _require_aware_datetime(
            value,
            "hash_datetime",
        ).isoformat()

    if isinstance(value, Path):
        return str(value)

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def _canonical_json_bytes(
    payload: Mapping[str, Any],
) -> bytes:
    normalized = _normalize_for_hash(payload)

    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_hex(
    payload: Mapping[str, Any],
) -> str:
    return hashlib.sha256(
        _canonical_json_bytes(payload)
    ).hexdigest()


def _safe_int(
    value: Any,
    name: str,
) -> int:
    try:
        converted = int(value)
    except (TypeError, ValueError) as exc:
        raise PassiveRuntimeObservationError(
            f"{name} must be integer-compatible."
        ) from exc

    if converted < 0:
        raise PassiveRuntimeObservationError(
            f"{name} cannot be negative."
        )

    return converted


def _file_sha256(path: Path) -> Optional[str]:
    if not path.exists() or not path.is_file():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _newest_json_file(
    root: Path,
) -> Optional[Path]:
    if not root.exists() or not root.is_dir():
        return None

    candidates = [
        path
        for path in root.rglob("*.json")
        if path.is_file()
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: path.stat().st_mtime_ns,
    )


def _load_environment_file(
    environment_file: Path,
) -> None:
    if not environment_file.exists():
        return

    for raw_line in environment_file.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _resolve_database_url() -> str:
    candidates = (
        "DATABASE_URL",
        "POSTGRES_URL",
        "POSTGRESQL_URL",
        "ORACLE_DATABASE_URL",
    )

    for key in candidates:
        value = os.getenv(key)

        if value and value.strip():
            return value.strip()

    raise PassiveRuntimeConfigurationError(
        "No PostgreSQL URL was found in the environment."
    )


def _connect_postgresql(
    database_url: str,
) -> Any:
    try:
        import psycopg  # type: ignore

        return psycopg.connect(database_url)
    except ImportError:
        pass

    try:
        import psycopg2  # type: ignore

        return psycopg2.connect(database_url)
    except ImportError as exc:
        raise PassiveRuntimeConfigurationError(
            "Neither psycopg nor psycopg2 is installed."
        ) from exc


def _query_postgresql_state(
    database_url: str,
) -> Mapping[str, Any]:
    connection = _connect_postgresql(database_url)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS observation_count,
                    COALESCE(MAX(sequence_number), 0)
                        AS latest_sequence_number,
                    MAX(persisted_at) AS latest_persisted_at
                FROM oracle_canonical_observations
                """
            )

            row = cursor.fetchone()

            if row is None:
                raise PassiveRuntimeObservationError(
                    "PostgreSQL observation query returned no row."
                )

            observation_count = _safe_int(
                row[0],
                "observation_count",
            )

            latest_sequence_number = _safe_int(
                row[1],
                "latest_sequence_number",
            )

            latest_persisted_at = row[2]

            if latest_persisted_at is not None:
                latest_persisted_at = (
                    _require_aware_datetime(
                        latest_persisted_at,
                        "latest_persisted_at",
                    )
                )

            persistence_terminal_sequence = (
                latest_sequence_number
            )

            try:
                cursor.execute(
                    """
                    SELECT
                        COALESCE(
                            MAX(terminal_sequence_number),
                            0
                        )
                    FROM oracle_canonical_persistence_state
                    """
                )

                persistence_row = cursor.fetchone()

                if persistence_row is not None:
                    persistence_terminal_sequence = (
                        _safe_int(
                            persistence_row[0],
                            (
                                "persistence_terminal_"
                                "sequence"
                            ),
                        )
                    )
            except Exception:
                try:
                    connection.rollback()
                except Exception:
                    pass

                persistence_terminal_sequence = (
                    latest_sequence_number
                )

            return _freeze_mapping(
                {
                    "observation_count": (
                        observation_count
                    ),
                    "latest_sequence_number": (
                        latest_sequence_number
                    ),
                    "latest_persisted_at": (
                        latest_persisted_at
                    ),
                    "persistence_terminal_sequence": (
                        persistence_terminal_sequence
                    ),
                }
            )
    finally:
        connection.close()


@dataclass(frozen=True)
class OraclePassiveRuntimeSnapshot:
    schema_version: str
    engine_id: str
    captured_at: datetime
    observation_count: int
    latest_sequence_number: int
    latest_persisted_at: Optional[datetime]
    persistence_terminal_sequence: int
    newest_runtime_log_path: Optional[str]
    newest_runtime_log_modified_at: Optional[datetime]
    newest_runtime_log_size_bytes: Optional[int]
    newest_runtime_log_sha256: Optional[str]
    active_state_path: Optional[str]
    active_state_modified_at: Optional[datetime]
    active_state_size_bytes: Optional[int]
    active_state_sha256: Optional[str]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    snapshot_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PassiveRuntimeInvariantError(
                "Unexpected snapshot schema version."
            )

        if self.engine_id != ENGINE_ID:
            raise PassiveRuntimeInvariantError(
                "Unexpected snapshot engine ID."
            )

        _require_aware_datetime(
            self.captured_at,
            "captured_at",
        )

        if self.latest_persisted_at is not None:
            _require_aware_datetime(
                self.latest_persisted_at,
                "latest_persisted_at",
            )

        if (
            self.newest_runtime_log_modified_at
            is not None
        ):
            _require_aware_datetime(
                self.newest_runtime_log_modified_at,
                "newest_runtime_log_modified_at",
            )

        if self.active_state_modified_at is not None:
            _require_aware_datetime(
                self.active_state_modified_at,
                "active_state_modified_at",
            )

        for field_name in (
            "observation_count",
            "latest_sequence_number",
            "persistence_terminal_sequence",
        ):
            if getattr(self, field_name) < 0:
                raise PassiveRuntimeInvariantError(
                    f"{field_name} cannot be negative."
                )

        if self.read_only is not True:
            raise PassiveRuntimeInvariantError(
                "OLA-068 must remain read-only."
            )

        for field_name in (
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "trade_authorization_allowed",
            "order_placement_allowed",
            "funds_moved",
            "portfolio_mutated",
        ):
            if getattr(self, field_name) is not False:
                raise PassiveRuntimeInvariantError(
                    f"{field_name} must remain false."
                )

        expected_hash = _sha256_hex(
            self.to_payload(include_hash=False)
        )

        if self.snapshot_hash != expected_hash:
            raise PassiveRuntimeInvariantError(
                "Snapshot hash verification failed."
            )

    def to_payload(
        self,
        *,
        include_hash: bool = True,
    ) -> Mapping[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "captured_at": (
                self.captured_at.isoformat()
            ),
            "observation_count": (
                self.observation_count
            ),
            "latest_sequence_number": (
                self.latest_sequence_number
            ),
            "latest_persisted_at": (
                self.latest_persisted_at.isoformat()
                if self.latest_persisted_at is not None
                else None
            ),
            "persistence_terminal_sequence": (
                self.persistence_terminal_sequence
            ),
            "newest_runtime_log_path": (
                self.newest_runtime_log_path
            ),
            "newest_runtime_log_modified_at": (
                self.newest_runtime_log_modified_at
                .isoformat()
                if self.newest_runtime_log_modified_at
                is not None
                else None
            ),
            "newest_runtime_log_size_bytes": (
                self.newest_runtime_log_size_bytes
            ),
            "newest_runtime_log_sha256": (
                self.newest_runtime_log_sha256
            ),
            "active_state_path": (
                self.active_state_path
            ),
            "active_state_modified_at": (
                self.active_state_modified_at
                .isoformat()
                if self.active_state_modified_at
                is not None
                else None
            ),
            "active_state_size_bytes": (
                self.active_state_size_bytes
            ),
            "active_state_sha256": (
                self.active_state_sha256
            ),
            "read_only": self.read_only,
            "execution_allowed": (
                self.execution_allowed
            ),
            "alerts_allowed": self.alerts_allowed,
            "qseries_handoff_allowed": (
                self.qseries_handoff_allowed
            ),
            "trade_authorization_allowed": (
                self.trade_authorization_allowed
            ),
            "order_placement_allowed": (
                self.order_placement_allowed
            ),
            "funds_moved": self.funds_moved,
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
        }

        if include_hash:
            payload["snapshot_hash"] = (
                self.snapshot_hash
            )

        return _freeze_mapping(payload)


@dataclass(frozen=True)
class OraclePassiveRuntimeAdvancementRecord:
    schema_version: str
    engine_id: str
    status: str
    evaluated_at: datetime
    observation_window_seconds: float
    before_snapshot_hash: str
    after_snapshot_hash: str
    observation_count_delta: int
    latest_sequence_delta: int
    persistence_terminal_sequence_delta: int
    latest_persisted_at_advanced: bool
    runtime_log_advanced: bool
    active_state_advanced: bool
    postgresql_persistence_advanced: bool
    runtime_advancing: bool
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
    evidence_hash: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PassiveRuntimeInvariantError(
                "Unexpected advancement schema version."
            )

        if self.engine_id != ENGINE_ID:
            raise PassiveRuntimeInvariantError(
                "Unexpected advancement engine ID."
            )

        if self.status not in {
            "advancing",
            "not_advancing",
        }:
            raise PassiveRuntimeInvariantError(
                "Unexpected advancement status."
            )

        _require_aware_datetime(
            self.evaluated_at,
            "evaluated_at",
        )

        if self.observation_window_seconds < 0:
            raise PassiveRuntimeInvariantError(
                "Observation window cannot be negative."
            )

        if (
            self.existing_runtime_observed_only
            is not True
        ):
            raise PassiveRuntimeInvariantError(
                "OLA-068 must observe only the "
                "existing runtime."
            )

        if self.read_only is not True:
            raise PassiveRuntimeInvariantError(
                "OLA-068 must remain read-only."
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
        ):
            if getattr(self, field_name) is not False:
                raise PassiveRuntimeInvariantError(
                    f"{field_name} must remain false."
                )

        if self.runtime_advancing:
            if self.status != "advancing":
                raise PassiveRuntimeInvariantError(
                    "Advancing runtime must use "
                    "advancing status."
                )

            if (
                self.postgresql_persistence_advanced
                is not True
            ):
                raise PassiveRuntimeInvariantError(
                    "Runtime advancement requires "
                    "PostgreSQL advancement."
                )
        else:
            if self.status != "not_advancing":
                raise PassiveRuntimeInvariantError(
                    "Inactive runtime must use "
                    "not_advancing status."
                )

        expected_hash = _sha256_hex(
            self.to_payload(include_hash=False)
        )

        if self.evidence_hash != expected_hash:
            raise PassiveRuntimeInvariantError(
                "Advancement evidence hash "
                "verification failed."
            )

    def to_payload(
        self,
        *,
        include_hash: bool = True,
    ) -> Mapping[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "evaluated_at": (
                self.evaluated_at.isoformat()
            ),
            "observation_window_seconds": (
                self.observation_window_seconds
            ),
            "before_snapshot_hash": (
                self.before_snapshot_hash
            ),
            "after_snapshot_hash": (
                self.after_snapshot_hash
            ),
            "observation_count_delta": (
                self.observation_count_delta
            ),
            "latest_sequence_delta": (
                self.latest_sequence_delta
            ),
            "persistence_terminal_sequence_delta": (
                self.persistence_terminal_sequence_delta
            ),
            "latest_persisted_at_advanced": (
                self.latest_persisted_at_advanced
            ),
            "runtime_log_advanced": (
                self.runtime_log_advanced
            ),
            "active_state_advanced": (
                self.active_state_advanced
            ),
            "postgresql_persistence_advanced": (
                self.postgresql_persistence_advanced
            ),
            "runtime_advancing": (
                self.runtime_advancing
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
            "read_only": self.read_only,
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
            "funds_moved": self.funds_moved,
            "portfolio_mutated": (
                self.portfolio_mutated
            ),
        }

        if include_hash:
            payload["evidence_hash"] = (
                self.evidence_hash
            )

        return _freeze_mapping(payload)


def build_passive_runtime_snapshot(
    *,
    repository_root: Path,
    captured_at: Optional[datetime] = None,
    database_url: Optional[str] = None,
) -> OraclePassiveRuntimeSnapshot:
    root = Path(repository_root).resolve()

    if not root.exists() or not root.is_dir():
        raise PassiveRuntimeConfigurationError(
            "Repository root does not exist."
        )

    _load_environment_file(root / ".env")

    resolved_database_url = (
        database_url.strip()
        if database_url and database_url.strip()
        else _resolve_database_url()
    )

    database_state = _query_postgresql_state(
        resolved_database_url
    )

    newest_log = _newest_json_file(
        root / "logs"
    )

    active_state = (
        root
        / "state"
        / "current.json"
    )

    newest_log_path: Optional[str] = None
    newest_log_modified_at: Optional[datetime] = None
    newest_log_size_bytes: Optional[int] = None
    newest_log_sha256: Optional[str] = None

    if newest_log is not None:
        stat = newest_log.stat()

        newest_log_path = str(newest_log)
        newest_log_modified_at = datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        )
        newest_log_size_bytes = stat.st_size
        newest_log_sha256 = _file_sha256(newest_log)

    active_state_path: Optional[str] = None
    active_state_modified_at: Optional[datetime] = None
    active_state_size_bytes: Optional[int] = None
    active_state_sha256: Optional[str] = None

    if active_state.exists() and active_state.is_file():
        stat = active_state.stat()

        active_state_path = str(active_state)
        active_state_modified_at = datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        )
        active_state_size_bytes = stat.st_size
        active_state_sha256 = _file_sha256(active_state)

    normalized_captured_at = _require_aware_datetime(
        captured_at or _utc_now(),
        "captured_at",
    )

    latest_persisted_at = database_state[
        "latest_persisted_at"
    ]

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "captured_at": (
            normalized_captured_at.isoformat()
        ),
        "observation_count": database_state[
            "observation_count"
        ],
        "latest_sequence_number": database_state[
            "latest_sequence_number"
        ],
        "latest_persisted_at": (
            latest_persisted_at.isoformat()
            if latest_persisted_at is not None
            else None
        ),
        "persistence_terminal_sequence": (
            database_state[
                "persistence_terminal_sequence"
            ]
        ),
        "newest_runtime_log_path": (
            newest_log_path
        ),
        "newest_runtime_log_modified_at": (
            newest_log_modified_at.isoformat()
            if newest_log_modified_at is not None
            else None
        ),
        "newest_runtime_log_size_bytes": (
            newest_log_size_bytes
        ),
        "newest_runtime_log_sha256": (
            newest_log_sha256
        ),
        "active_state_path": active_state_path,
        "active_state_modified_at": (
            active_state_modified_at.isoformat()
            if active_state_modified_at is not None
            else None
        ),
        "active_state_size_bytes": (
            active_state_size_bytes
        ),
        "active_state_sha256": (
            active_state_sha256
        ),
        "read_only": READ_ONLY,
        "execution_allowed": EXECUTION_ALLOWED,
        "alerts_allowed": ALERTS_ALLOWED,
        "qseries_handoff_allowed": (
            QSERIES_HANDOFF_ALLOWED
        ),
        "trade_authorization_allowed": (
            TRADE_AUTHORIZATION_ALLOWED
        ),
        "order_placement_allowed": (
            ORDER_PLACEMENT_ALLOWED
        ),
        "funds_moved": FUNDS_MOVED,
        "portfolio_mutated": PORTFOLIO_MUTATED,
    }

    return OraclePassiveRuntimeSnapshot(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        captured_at=normalized_captured_at,
        observation_count=database_state[
            "observation_count"
        ],
        latest_sequence_number=database_state[
            "latest_sequence_number"
        ],
        latest_persisted_at=latest_persisted_at,
        persistence_terminal_sequence=(
            database_state[
                "persistence_terminal_sequence"
            ]
        ),
        newest_runtime_log_path=newest_log_path,
        newest_runtime_log_modified_at=(
            newest_log_modified_at
        ),
        newest_runtime_log_size_bytes=(
            newest_log_size_bytes
        ),
        newest_runtime_log_sha256=(
            newest_log_sha256
        ),
        active_state_path=active_state_path,
        active_state_modified_at=(
            active_state_modified_at
        ),
        active_state_size_bytes=(
            active_state_size_bytes
        ),
        active_state_sha256=active_state_sha256,
        read_only=READ_ONLY,
        execution_allowed=EXECUTION_ALLOWED,
        alerts_allowed=ALERTS_ALLOWED,
        qseries_handoff_allowed=(
            QSERIES_HANDOFF_ALLOWED
        ),
        trade_authorization_allowed=(
            TRADE_AUTHORIZATION_ALLOWED
        ),
        order_placement_allowed=(
            ORDER_PLACEMENT_ALLOWED
        ),
        funds_moved=FUNDS_MOVED,
        portfolio_mutated=PORTFOLIO_MUTATED,
        snapshot_hash=_sha256_hex(payload),
    )


def compare_passive_runtime_snapshots(
    *,
    before: OraclePassiveRuntimeSnapshot,
    after: OraclePassiveRuntimeSnapshot,
    observation_window_seconds: float,
    evaluated_at: Optional[datetime] = None,
) -> OraclePassiveRuntimeAdvancementRecord:
    if not isinstance(
        before,
        OraclePassiveRuntimeSnapshot,
    ):
        raise PassiveRuntimeInvariantError(
            "before must be an OLA-068 snapshot."
        )

    if not isinstance(
        after,
        OraclePassiveRuntimeSnapshot,
    ):
        raise PassiveRuntimeInvariantError(
            "after must be an OLA-068 snapshot."
        )

    if observation_window_seconds < 0:
        raise PassiveRuntimeConfigurationError(
            "Observation window cannot be negative."
        )

    observation_count_delta = (
        after.observation_count
        - before.observation_count
    )

    latest_sequence_delta = (
        after.latest_sequence_number
        - before.latest_sequence_number
    )

    persistence_terminal_sequence_delta = (
        after.persistence_terminal_sequence
        - before.persistence_terminal_sequence
    )

    latest_persisted_at_advanced = (
        after.latest_persisted_at is not None
        and (
            before.latest_persisted_at is None
            or after.latest_persisted_at
            > before.latest_persisted_at
        )
    )

    runtime_log_advanced = (
        after.newest_runtime_log_path
        != before.newest_runtime_log_path
        or after.newest_runtime_log_modified_at
        != before.newest_runtime_log_modified_at
        or after.newest_runtime_log_sha256
        != before.newest_runtime_log_sha256
    )

    active_state_advanced = (
        after.active_state_modified_at
        != before.active_state_modified_at
        or after.active_state_sha256
        != before.active_state_sha256
    )

    postgresql_persistence_advanced = (
        observation_count_delta > 0
        and latest_sequence_delta > 0
        and persistence_terminal_sequence_delta > 0
        and latest_persisted_at_advanced
    )

    # Canonical continuous-runtime advancement is established by
    # PostgreSQL persistence. The guarded continuous process persists
    # canonical observations every cycle without necessarily rewriting
    # the historical launch log or state/current.json.
    #
    # Runtime-log and active-state movement remain captured as supporting
    # evidence, but neither filesystem artifact is mandatory.
    runtime_advancing = (
        postgresql_persistence_advanced
    )

    status = (
        "advancing"
        if runtime_advancing
        else "not_advancing"
    )

    normalized_evaluated_at = (
        _require_aware_datetime(
            evaluated_at or _utc_now(),
            "evaluated_at",
        )
    )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "evaluated_at": (
            normalized_evaluated_at.isoformat()
        ),
        "observation_window_seconds": float(
            observation_window_seconds
        ),
        "before_snapshot_hash": (
            before.snapshot_hash
        ),
        "after_snapshot_hash": (
            after.snapshot_hash
        ),
        "observation_count_delta": (
            observation_count_delta
        ),
        "latest_sequence_delta": (
            latest_sequence_delta
        ),
        "persistence_terminal_sequence_delta": (
            persistence_terminal_sequence_delta
        ),
        "latest_persisted_at_advanced": (
            latest_persisted_at_advanced
        ),
        "runtime_log_advanced": (
            runtime_log_advanced
        ),
        "active_state_advanced": (
            active_state_advanced
        ),
        "postgresql_persistence_advanced": (
            postgresql_persistence_advanced
        ),
        "runtime_advancing": runtime_advancing,
        "existing_runtime_observed_only": True,
        "acquisition_cycle_invoked": False,
        "scheduler_invoked": False,
        "runner_invoked": False,
        "read_only": READ_ONLY,
        "execution_allowed": EXECUTION_ALLOWED,
        "alerts_allowed": ALERTS_ALLOWED,
        "qseries_handoff_allowed": (
            QSERIES_HANDOFF_ALLOWED
        ),
        "trade_authorization_allowed": (
            TRADE_AUTHORIZATION_ALLOWED
        ),
        "order_placement_allowed": (
            ORDER_PLACEMENT_ALLOWED
        ),
        "funds_moved": FUNDS_MOVED,
        "portfolio_mutated": PORTFOLIO_MUTATED,
    }

    return OraclePassiveRuntimeAdvancementRecord(
        schema_version=SCHEMA_VERSION,
        engine_id=ENGINE_ID,
        status=status,
        evaluated_at=normalized_evaluated_at,
        observation_window_seconds=float(
            observation_window_seconds
        ),
        before_snapshot_hash=(
            before.snapshot_hash
        ),
        after_snapshot_hash=after.snapshot_hash,
        observation_count_delta=(
            observation_count_delta
        ),
        latest_sequence_delta=latest_sequence_delta,
        persistence_terminal_sequence_delta=(
            persistence_terminal_sequence_delta
        ),
        latest_persisted_at_advanced=(
            latest_persisted_at_advanced
        ),
        runtime_log_advanced=runtime_log_advanced,
        active_state_advanced=active_state_advanced,
        postgresql_persistence_advanced=(
            postgresql_persistence_advanced
        ),
        runtime_advancing=runtime_advancing,
        existing_runtime_observed_only=True,
        acquisition_cycle_invoked=False,
        scheduler_invoked=False,
        runner_invoked=False,
        read_only=READ_ONLY,
        execution_allowed=EXECUTION_ALLOWED,
        alerts_allowed=ALERTS_ALLOWED,
        qseries_handoff_allowed=(
            QSERIES_HANDOFF_ALLOWED
        ),
        trade_authorization_allowed=(
            TRADE_AUTHORIZATION_ALLOWED
        ),
        order_placement_allowed=(
            ORDER_PLACEMENT_ALLOWED
        ),
        funds_moved=FUNDS_MOVED,
        portfolio_mutated=PORTFOLIO_MUTATED,
        evidence_hash=_sha256_hex(payload),
    )


def monitor_existing_runtime(
    *,
    snapshot_probe: RuntimeSnapshotProbe,
    observation_window_seconds: float = 30.0,
    sleeper: Callable[[float], None] = time.sleep,
    evaluated_at_factory: Callable[
        [],
        datetime,
    ] = _utc_now,
) -> OraclePassiveRuntimeAdvancementRecord:
    if not callable(snapshot_probe):
        raise PassiveRuntimeConfigurationError(
            "snapshot_probe must be callable."
        )

    if observation_window_seconds < 0:
        raise PassiveRuntimeConfigurationError(
            "Observation window cannot be negative."
        )

    if not callable(sleeper):
        raise PassiveRuntimeConfigurationError(
            "sleeper must be callable."
        )

    before = snapshot_probe()

    if not isinstance(
        before,
        OraclePassiveRuntimeSnapshot,
    ):
        raise PassiveRuntimeObservationError(
            "snapshot_probe returned an invalid "
            "BEFORE snapshot."
        )

    sleeper(float(observation_window_seconds))

    after = snapshot_probe()

    if not isinstance(
        after,
        OraclePassiveRuntimeSnapshot,
    ):
        raise PassiveRuntimeObservationError(
            "snapshot_probe returned an invalid "
            "AFTER snapshot."
        )

    return compare_passive_runtime_snapshots(
        before=before,
        after=after,
        observation_window_seconds=(
            observation_window_seconds
        ),
        evaluated_at=evaluated_at_factory(),
    )


def build_repository_snapshot_probe(
    *,
    repository_root: Path,
    database_url: Optional[str] = None,
) -> RuntimeSnapshotProbe:
    root = Path(repository_root).resolve()

    def probe() -> OraclePassiveRuntimeSnapshot:
        return build_passive_runtime_snapshot(
            repository_root=root,
            database_url=database_url,
        )

    return probe


def run_repository_passive_monitor(
    *,
    repository_root: Path,
    observation_window_seconds: float = 30.0,
    database_url: Optional[str] = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> OraclePassiveRuntimeAdvancementRecord:
    probe = build_repository_snapshot_probe(
        repository_root=repository_root,
        database_url=database_url,
    )

    return monitor_existing_runtime(
        snapshot_probe=probe,
        observation_window_seconds=(
            observation_window_seconds
        ),
        sleeper=sleeper,
    )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "ALERTS_ALLOWED",
    "QSERIES_HANDOFF_ALLOWED",
    "TRADE_AUTHORIZATION_ALLOWED",
    "ORDER_PLACEMENT_ALLOWED",
    "FUNDS_MOVED",
    "PORTFOLIO_MUTATED",
    "PassiveRuntimeMonitorError",
    "PassiveRuntimeConfigurationError",
    "PassiveRuntimeObservationError",
    "PassiveRuntimeInvariantError",
    "RuntimeSnapshotProbe",
    "OraclePassiveRuntimeSnapshot",
    "OraclePassiveRuntimeAdvancementRecord",
    "build_passive_runtime_snapshot",
    "compare_passive_runtime_snapshots",
    "monitor_existing_runtime",
    "build_repository_snapshot_probe",
    "run_repository_passive_monitor",
]
