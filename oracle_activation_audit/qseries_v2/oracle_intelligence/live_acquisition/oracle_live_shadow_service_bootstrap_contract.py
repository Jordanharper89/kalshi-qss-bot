"""
OLA-022
Oracle Live Shadow Service Bootstrap Contract

Canonical bootstrap boundary for the separately running Oracle live-shadow
service.

Architecture:

EXISTING ORACLE RUNTIME LINEAGE
    |
OEM-013 AUTO DISCOVERY / REGISTRATION
OEM-014 RUNTIME BOOTSTRAP MANAGEMENT
OEM-015 RUNTIME BOOTSTRAP INTEGRATION GATE
    |
OLA-020 SERVICE ISOLATION CONTRACT
    |
OLA-018 READINESS PROVIDER
    |
OLA-019 POLLING POLICY ENGINE
    |
OLA-021 ONE-TICK SCHEDULER
    |
OLA-017 SHADOW ACQUISITION CYCLE BOUNDARY
    |
APPROVED RUNTIME STATE / LOG BOUNDARIES
    |
OLA-022 IMMUTABLE SERVICE BOOTSTRAP RECORD

Purpose:

OLA-022 freezes how a future Oracle live-shadow service runner must be
assembled.

OLA-022 does not start the service.

It does not:
- create a process
- create a thread
- start an infinite loop
- sleep
- call Kalshi
- invoke acquisition
- invoke OLA-017
- invoke OLA-021
- persist observations
- publish intelligence handoffs
- create alerts
- send records to Q Series
- authorize trades
- resolve execution adapters
- invoke execution adapters
- place orders
- move funds
- mutate portfolios

Canonical ownership:

Existing OEM runtime lineage remains historical/runtime architecture
evidence.

OLA-020 is authoritative for Oracle/Q Series process and authority
isolation.

OLA-018 owns live-read readiness evidence.

OLA-019 owns polling eligibility policy.

OLA-021 owns one governed scheduler tick.

OLA-017 owns one PostgreSQL shadow acquisition cycle boundary.

A later service runner may repeatedly call OLA-021, but only after a
passing OLA-022 bootstrap record.

Permanent rules:

- Oracle service identity must match OLA-020.
- Q Series service identity must match OLA-020.
- Separate-process isolation is mandatory.
- Existing Oracle runtime bootstrap lineage must be declared.
- OEM-013, OEM-014, and OEM-015 lineage identities are required.
- OLA-017, OLA-018, OLA-019, OLA-020, and OLA-021 boundaries are required.
- Runtime root is explicit.
- Runtime state directory must be under runtime root.
- Runtime logs directory must be under runtime root.
- State directory role must be runtime/state.
- Logs directory role must be runtime/logs.
- Runtime directories are caller supplied.
- Bootstrap timestamps are caller supplied.
- Bootstrap records are immutable.
- Bootstrap records are deterministic.
- Canonical stable JSON hashing is required.
- repr() is never used.
- Secret-bearing metadata is rejected.
- Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Mapping


from .oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)


SCHEMA_VERSION = "OLA-022"
ENGINE_ID = "OLA-022"

SERVICE_BOOTSTRAP_STATUS_READY = "ready"

ORACLE_SERVICE_ID = "service.oracle.intelligence"

REQUIRED_OEM_RUNTIME_LINEAGE = (
    "OEM-013",
    "OEM-014",
    "OEM-015",
)

REQUIRED_OLA_BOUNDARIES = (
    "OLA-017",
    "OLA-018",
    "OLA-019",
    "OLA-020",
    "OLA-021",
)

REQUIRED_RUNTIME_STATE_ROLE = "runtime/state"
REQUIRED_RUNTIME_LOGS_ROLE = "runtime/logs"

BOOTSTRAP_RECORD_TYPE = (
    "oracle_live_shadow_service_bootstrap_record"
)


class OracleLiveShadowServiceBootstrapContractError(ValueError):
    """Raised when bootstrap contract data is malformed."""


class OracleLiveShadowServiceBootstrapCompatibilityError(
    OracleLiveShadowServiceBootstrapContractError
):
    """Raised when required architecture boundaries are incompatible."""


class OracleLiveShadowServiceBootstrapInvariantError(RuntimeError):
    """Raised when permanent service invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_aware_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


def _canonicalize(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise OracleLiveShadowServiceBootstrapContractError(
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

    if isinstance(value, Path):
        return str(
            value
        )

    if isinstance(value, str):
        return value

    if isinstance(value, Mapping):
        result = {}

        for key in sorted(value):
            if not isinstance(key, str):
                raise OracleLiveShadowServiceBootstrapContractError(
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

    raise OracleLiveShadowServiceBootstrapContractError(
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
) -> tuple[tuple[str, Any], ...]:
    if not isinstance(value, Mapping):
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be a mapping"
        )

    canonical = _canonicalize(
        value
    )

    if not isinstance(canonical, dict):
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must canonicalize to a mapping"
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
        "token",
    }

    result = tuple(
        (
            key,
            canonical[key],
        )
        for key in sorted(canonical)
    )

    for key, _ in result:
        if key.strip().lower() in forbidden_keys:
            raise OracleLiveShadowServiceBootstrapContractError(
                f"{field_name} contains forbidden "
                f"secret-bearing key: {key}"
            )

    return result


def _mapping_from_immutable(
    value: tuple[tuple[str, Any], ...],
) -> dict[str, Any]:
    return {
        key: item
        for key, item in value
    }


def _normalize_path(
    value: Any,
    field_name: str,
) -> Path:
    if isinstance(value, Path):
        path = value

    elif isinstance(value, str):
        normalized = value.strip()

        if not normalized:
            raise OracleLiveShadowServiceBootstrapContractError(
                f"{field_name} must not be empty"
            )

        path = Path(
            normalized
        )

    else:
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be Path or string"
        )

    return Path(
        str(path)
    )


def _path_identity(
    value: Path,
) -> str:
    return value.as_posix()


def _relative_role(
    *,
    runtime_root: Path,
    child_path: Path,
    field_name: str,
) -> str:
    try:
        relative = child_path.relative_to(
            runtime_root
        )

    except ValueError as exc:
        raise OracleLiveShadowServiceBootstrapContractError(
            f"{field_name} must be inside runtime_root"
        ) from exc

    return (
        Path("runtime")
        / relative
    ).as_posix()


@dataclass(frozen=True, slots=True)
class OracleLiveShadowServiceBootstrapRecord:
    schema_version: str
    engine_id: str
    bootstrap_id: str
    bootstrap_status: str
    service_contract_id: str
    service_contract_hash: str
    oracle_service_id: str
    qseries_service_id: str
    separate_process_required: bool
    oracle_execution_authority: bool
    direct_execution_import_allowed: bool
    oem_runtime_lineage: tuple[str, ...]
    required_ola_boundaries: tuple[str, ...]
    ola_017_cycle_boundary_required: bool
    ola_018_readiness_required: bool
    ola_019_polling_policy_required: bool
    ola_020_service_isolation_required: bool
    ola_021_scheduler_tick_required: bool
    runtime_root: str
    runtime_state_directory: str
    runtime_logs_directory: str
    runtime_state_role: str
    runtime_logs_role: str
    bootstrapped_at: datetime
    service_start_allowed: bool
    service_started: bool
    process_created: bool
    thread_created: bool
    loop_started: bool
    sleep_performed: bool
    acquisition_invoked: bool
    scheduler_tick_invoked: bool
    shadow_cycle_invoked: bool
    canonical_handoff_published: bool
    alert_created: bool
    qseries_intake_record_created: bool
    bootstrap_metadata: tuple[
        tuple[str, Any],
        ...
    ]
    bootstrap_hash: str
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
        include_bootstrap_hash: bool = True,
    ) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "bootstrap_id": self.bootstrap_id,
            "bootstrap_status": self.bootstrap_status,
            "service_contract_id": (
                self.service_contract_id
            ),
            "service_contract_hash": (
                self.service_contract_hash
            ),
            "oracle_service_id": self.oracle_service_id,
            "qseries_service_id": self.qseries_service_id,
            "separate_process_required": (
                self.separate_process_required
            ),
            "oracle_execution_authority": (
                self.oracle_execution_authority
            ),
            "direct_execution_import_allowed": (
                self.direct_execution_import_allowed
            ),
            "oem_runtime_lineage": list(
                self.oem_runtime_lineage
            ),
            "required_ola_boundaries": list(
                self.required_ola_boundaries
            ),
            "ola_017_cycle_boundary_required": (
                self.ola_017_cycle_boundary_required
            ),
            "ola_018_readiness_required": (
                self.ola_018_readiness_required
            ),
            "ola_019_polling_policy_required": (
                self.ola_019_polling_policy_required
            ),
            "ola_020_service_isolation_required": (
                self.ola_020_service_isolation_required
            ),
            "ola_021_scheduler_tick_required": (
                self.ola_021_scheduler_tick_required
            ),
            "runtime_root": self.runtime_root,
            "runtime_state_directory": (
                self.runtime_state_directory
            ),
            "runtime_logs_directory": (
                self.runtime_logs_directory
            ),
            "runtime_state_role": self.runtime_state_role,
            "runtime_logs_role": self.runtime_logs_role,
            "bootstrapped_at": self.bootstrapped_at.isoformat(),
            "service_start_allowed": (
                self.service_start_allowed
            ),
            "service_started": self.service_started,
            "process_created": self.process_created,
            "thread_created": self.thread_created,
            "loop_started": self.loop_started,
            "sleep_performed": self.sleep_performed,
            "acquisition_invoked": self.acquisition_invoked,
            "scheduler_tick_invoked": (
                self.scheduler_tick_invoked
            ),
            "shadow_cycle_invoked": (
                self.shadow_cycle_invoked
            ),
            "canonical_handoff_published": (
                self.canonical_handoff_published
            ),
            "alert_created": self.alert_created,
            "qseries_intake_record_created": (
                self.qseries_intake_record_created
            ),
            "bootstrap_metadata": _mapping_from_immutable(
                self.bootstrap_metadata
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

        if include_bootstrap_hash:
            result["bootstrap_hash"] = self.bootstrap_hash

        return result

    def verify_bootstrap_hash(
        self,
    ) -> bool:
        expected = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": BOOTSTRAP_RECORD_TYPE,
                "bootstrap": self.to_canonical_dict(
                    include_bootstrap_hash=False
                ),
            }
        )

        return self.bootstrap_hash == expected


class OracleLiveShadowServiceBootstrapContract:
    """
    Pure deterministic bootstrap contract.

    This class validates and records service composition.

    It never starts the service.
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
        service_contract: OracleQSeriesServiceIsolationContract,
    ) -> None:
        if not isinstance(
            service_contract,
            OracleQSeriesServiceIsolationContract,
        ):
            raise OracleLiveShadowServiceBootstrapContractError(
                "service_contract must be "
                "OracleQSeriesServiceIsolationContract"
            )

        self._service_contract = service_contract

        self._validate_service_contract()

        self._assert_invariants()

    @property
    def service_contract(
        self,
    ) -> OracleQSeriesServiceIsolationContract:
        return self._service_contract

    def _assert_invariants(
        self,
    ) -> None:
        if self.read_only is not True:
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "OLA-022 lost read_only invariant"
            )

        forbidden = {
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

        if any(
            forbidden.values()
        ):
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "OLA-022 gained execution capability"
            )

    def _validate_service_contract(
        self,
    ) -> None:
        contract = self._service_contract

        if contract.oracle_service_id != ORACLE_SERVICE_ID:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "Oracle service identity mismatch"
            )

        if contract.separate_process_required is not True:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "separate Oracle process is required"
            )

        if contract.oracle_execution_authority is not False:
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "Oracle service gained execution authority"
            )

        if (
            contract.direct_execution_import_allowed
            is not False
        ):
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "Oracle service allows direct execution imports"
            )

        if contract.read_only is not True:
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "service-isolation contract lost read_only invariant"
            )

        if contract.execution_allowed is not False:
            raise OracleLiveShadowServiceBootstrapInvariantError(
                "service-isolation contract gained execution capability"
            )

    def bootstrap(
        self,
        *,
        oem_runtime_lineage: tuple[str, ...],
        ola_boundaries: tuple[str, ...],
        runtime_root: Path | str,
        runtime_state_directory: Path | str,
        runtime_logs_directory: Path | str,
        bootstrapped_at: datetime,
        bootstrap_metadata: Mapping[str, Any],
    ) -> OracleLiveShadowServiceBootstrapRecord:
        self._assert_invariants()

        normalized_bootstrapped_at = _require_aware_datetime(
            bootstrapped_at,
            "bootstrapped_at",
        )

        normalized_oem_lineage = tuple(
            _require_non_empty_string(
                item,
                "oem_runtime_lineage item",
            )
            for item in oem_runtime_lineage
        )

        normalized_ola_boundaries = tuple(
            _require_non_empty_string(
                item,
                "ola_boundaries item",
            )
            for item in ola_boundaries
        )

        if normalized_oem_lineage != REQUIRED_OEM_RUNTIME_LINEAGE:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "OEM runtime lineage must be exactly "
                "OEM-013, OEM-014, OEM-015"
            )

        if normalized_ola_boundaries != REQUIRED_OLA_BOUNDARIES:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "OLA service boundaries must be exactly "
                "OLA-017 through OLA-021"
            )

        normalized_runtime_root = _normalize_path(
            runtime_root,
            "runtime_root",
        )

        normalized_state_directory = _normalize_path(
            runtime_state_directory,
            "runtime_state_directory",
        )

        normalized_logs_directory = _normalize_path(
            runtime_logs_directory,
            "runtime_logs_directory",
        )

        state_role = _relative_role(
            runtime_root=normalized_runtime_root,
            child_path=normalized_state_directory,
            field_name="runtime_state_directory",
        )

        logs_role = _relative_role(
            runtime_root=normalized_runtime_root,
            child_path=normalized_logs_directory,
            field_name="runtime_logs_directory",
        )

        if state_role != REQUIRED_RUNTIME_STATE_ROLE:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "runtime state directory role must be runtime/state"
            )

        if logs_role != REQUIRED_RUNTIME_LOGS_ROLE:
            raise OracleLiveShadowServiceBootstrapCompatibilityError(
                "runtime logs directory role must be runtime/logs"
            )

        if normalized_state_directory == normalized_logs_directory:
            raise OracleLiveShadowServiceBootstrapContractError(
                "runtime state and logs directories must differ"
            )

        immutable_metadata = _immutable_mapping(
            bootstrap_metadata,
            "bootstrap_metadata",
        )

        contract = self._service_contract

        bootstrap_id = "oracle_service_bootstrap." + stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "oracle_service_bootstrap_identity",
                "service_contract_hash": contract.contract_hash,
                "oracle_service_id": contract.oracle_service_id,
                "qseries_service_id": contract.qseries_service_id,
                "oem_runtime_lineage": normalized_oem_lineage,
                "ola_boundaries": normalized_ola_boundaries,
                "runtime_root": _path_identity(
                    normalized_runtime_root
                ),
                "runtime_state_directory": _path_identity(
                    normalized_state_directory
                ),
                "runtime_logs_directory": _path_identity(
                    normalized_logs_directory
                ),
                "bootstrapped_at": normalized_bootstrapped_at,
            }
        )

        provisional = OracleLiveShadowServiceBootstrapRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            bootstrap_id=bootstrap_id,
            bootstrap_status=SERVICE_BOOTSTRAP_STATUS_READY,
            service_contract_id=contract.contract_id,
            service_contract_hash=contract.contract_hash,
            oracle_service_id=contract.oracle_service_id,
            qseries_service_id=contract.qseries_service_id,
            separate_process_required=True,
            oracle_execution_authority=False,
            direct_execution_import_allowed=False,
            oem_runtime_lineage=normalized_oem_lineage,
            required_ola_boundaries=normalized_ola_boundaries,
            ola_017_cycle_boundary_required=True,
            ola_018_readiness_required=True,
            ola_019_polling_policy_required=True,
            ola_020_service_isolation_required=True,
            ola_021_scheduler_tick_required=True,
            runtime_root=_path_identity(
                normalized_runtime_root
            ),
            runtime_state_directory=_path_identity(
                normalized_state_directory
            ),
            runtime_logs_directory=_path_identity(
                normalized_logs_directory
            ),
            runtime_state_role=state_role,
            runtime_logs_role=logs_role,
            bootstrapped_at=normalized_bootstrapped_at,
            service_start_allowed=True,
            service_started=False,
            process_created=False,
            thread_created=False,
            loop_started=False,
            sleep_performed=False,
            acquisition_invoked=False,
            scheduler_tick_invoked=False,
            shadow_cycle_invoked=False,
            canonical_handoff_published=False,
            alert_created=False,
            qseries_intake_record_created=False,
            bootstrap_metadata=immutable_metadata,
            bootstrap_hash="",
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

        bootstrap_hash = stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": BOOTSTRAP_RECORD_TYPE,
                "bootstrap": provisional.to_canonical_dict(
                    include_bootstrap_hash=False
                ),
            }
        )

        return OracleLiveShadowServiceBootstrapRecord(
            schema_version=provisional.schema_version,
            engine_id=provisional.engine_id,
            bootstrap_id=provisional.bootstrap_id,
            bootstrap_status=provisional.bootstrap_status,
            service_contract_id=provisional.service_contract_id,
            service_contract_hash=provisional.service_contract_hash,
            oracle_service_id=provisional.oracle_service_id,
            qseries_service_id=provisional.qseries_service_id,
            separate_process_required=True,
            oracle_execution_authority=False,
            direct_execution_import_allowed=False,
            oem_runtime_lineage=provisional.oem_runtime_lineage,
            required_ola_boundaries=(
                provisional.required_ola_boundaries
            ),
            ola_017_cycle_boundary_required=True,
            ola_018_readiness_required=True,
            ola_019_polling_policy_required=True,
            ola_020_service_isolation_required=True,
            ola_021_scheduler_tick_required=True,
            runtime_root=provisional.runtime_root,
            runtime_state_directory=(
                provisional.runtime_state_directory
            ),
            runtime_logs_directory=(
                provisional.runtime_logs_directory
            ),
            runtime_state_role=provisional.runtime_state_role,
            runtime_logs_role=provisional.runtime_logs_role,
            bootstrapped_at=provisional.bootstrapped_at,
            service_start_allowed=True,
            service_started=False,
            process_created=False,
            thread_created=False,
            loop_started=False,
            sleep_performed=False,
            acquisition_invoked=False,
            scheduler_tick_invoked=False,
            shadow_cycle_invoked=False,
            canonical_handoff_published=False,
            alert_created=False,
            qseries_intake_record_created=False,
            bootstrap_metadata=provisional.bootstrap_metadata,
            bootstrap_hash=bootstrap_hash,
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


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "SERVICE_BOOTSTRAP_STATUS_READY",
    "ORACLE_SERVICE_ID",
    "REQUIRED_OEM_RUNTIME_LINEAGE",
    "REQUIRED_OLA_BOUNDARIES",
    "REQUIRED_RUNTIME_STATE_ROLE",
    "REQUIRED_RUNTIME_LOGS_ROLE",
    "OracleLiveShadowServiceBootstrapContractError",
    "OracleLiveShadowServiceBootstrapCompatibilityError",
    "OracleLiveShadowServiceBootstrapInvariantError",
    "OracleLiveShadowServiceBootstrapRecord",
    "OracleLiveShadowServiceBootstrapContract",
    "canonical_json",
    "stable_hash",
]
