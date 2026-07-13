from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parent

PACKAGE_DIR = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition"
)

MODULE_PATH = (
    PACKAGE_DIR
    / "oracle_live_shadow_service_bootstrap_contract.py"
)

PACKAGE_INIT_PATH = PACKAGE_DIR / "__init__.py"

TEST_PATH = (
    ROOT
    / "test_ola_022_oracle_live_shadow_service_bootstrap_contract.py"
)


MODULE_CONTENT = r'''
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
'''


TEST_CONTENT = r'''
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path


from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_shadow_service_bootstrap_contract import (
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    OracleLiveShadowServiceBootstrapCompatibilityError,
    OracleLiveShadowServiceBootstrapContract,
    OracleLiveShadowServiceBootstrapContractError,
)

from qseries_v2.oracle_intelligence.live_acquisition.oracle_service_isolation_canonical_intelligence_handoff_contract import (
    OracleQSeriesServiceIsolationContract,
)


BOOTSTRAPPED_AT = datetime(
    2026,
    7,
    12,
    18,
    0,
    0,
    tzinfo=timezone.utc,
)

RUNTIME_ROOT = Path(
    "C:/qseries/runtime"
)

RUNTIME_STATE = (
    RUNTIME_ROOT
    / "state"
)

RUNTIME_LOGS = (
    RUNTIME_ROOT
    / "logs"
)


def build_service_contract():
    return OracleQSeriesServiceIsolationContract.create(
        contract_id=(
            "oracle.qseries.service_isolation.v1"
        ),
        oracle_service_id=(
            "service.oracle.intelligence"
        ),
        qseries_service_id=(
            "service.qseries.execution"
        ),
        contract_metadata={
            "environment": "production",
            "oracle_process": "separate",
            "qseries_process": "separate",
        },
    )


def build_bootstrap_contract():
    return OracleLiveShadowServiceBootstrapContract(
        service_contract=build_service_contract()
    )


def build_bootstrap_record():
    return build_bootstrap_contract().bootstrap(
        oem_runtime_lineage=(
            REQUIRED_OEM_RUNTIME_LINEAGE
        ),
        ola_boundaries=(
            REQUIRED_OLA_BOUNDARIES
        ),
        runtime_root=RUNTIME_ROOT,
        runtime_state_directory=RUNTIME_STATE,
        runtime_logs_directory=RUNTIME_LOGS,
        bootstrapped_at=BOOTSTRAPPED_AT,
        bootstrap_metadata={
            "environment": "production",
            "service_mode": "live_shadow",
            "runtime_owner": "oracle",
            "runner_status": "not_started",
        },
    )


def run_bootstrap_contract_test():
    contract = build_bootstrap_contract()

    assert contract.schema_version == "OLA-022"

    assert contract.engine_id == "OLA-022"

    assert contract.read_only is True

    assert contract.execution_allowed is False

    assert contract.execution_adapter_resolved is False

    assert contract.execution_adapter_invoked is False

    assert contract.trade_authorization_allowed is False

    assert contract.order_placement_allowed is False

    assert contract.funds_moved is False

    assert contract.portfolio_mutated is False

    assert (
        contract.service_contract.oracle_service_id
        == "service.oracle.intelligence"
    )

    assert (
        contract.service_contract.qseries_service_id
        == "service.qseries.execution"
    )

    assert (
        contract.service_contract.separate_process_required
        is True
    )

    return contract


def run_bootstrap_record_test():
    record = build_bootstrap_record()

    assert record.schema_version == "OLA-022"

    assert record.engine_id == "OLA-022"

    assert record.bootstrap_status == "ready"

    assert record.bootstrap_id.startswith(
        "oracle_service_bootstrap."
    )

    assert record.oracle_service_id == (
        "service.oracle.intelligence"
    )

    assert record.qseries_service_id == (
        "service.qseries.execution"
    )

    assert record.separate_process_required is True

    assert record.oracle_execution_authority is False

    assert (
        record.direct_execution_import_allowed
        is False
    )

    assert record.oem_runtime_lineage == (
        "OEM-013",
        "OEM-014",
        "OEM-015",
    )

    assert record.required_ola_boundaries == (
        "OLA-017",
        "OLA-018",
        "OLA-019",
        "OLA-020",
        "OLA-021",
    )

    assert (
        record.ola_017_cycle_boundary_required
        is True
    )

    assert record.ola_018_readiness_required is True

    assert (
        record.ola_019_polling_policy_required
        is True
    )

    assert (
        record.ola_020_service_isolation_required
        is True
    )

    assert (
        record.ola_021_scheduler_tick_required
        is True
    )

    assert record.runtime_root == (
        "C:/qseries/runtime"
    )

    assert record.runtime_state_directory == (
        "C:/qseries/runtime/state"
    )

    assert record.runtime_logs_directory == (
        "C:/qseries/runtime/logs"
    )

    assert record.runtime_state_role == "runtime/state"

    assert record.runtime_logs_role == "runtime/logs"

    assert record.bootstrapped_at == BOOTSTRAPPED_AT

    assert record.service_start_allowed is True

    assert record.service_started is False

    assert record.process_created is False

    assert record.thread_created is False

    assert record.loop_started is False

    assert record.sleep_performed is False

    assert record.acquisition_invoked is False

    assert record.scheduler_tick_invoked is False

    assert record.shadow_cycle_invoked is False

    assert record.canonical_handoff_published is False

    assert record.alert_created is False

    assert record.qseries_intake_record_created is False

    assert record.immutable is True

    assert record.replayable is True

    assert record.auditable is True

    assert record.explainable is True

    assert record.read_only is True

    assert record.execution_allowed is False

    assert record.execution_adapter_resolved is False

    assert record.execution_adapter_invoked is False

    assert record.trade_authorization_allowed is False

    assert record.order_placement_allowed is False

    assert record.funds_moved is False

    assert record.portfolio_mutated is False

    assert len(record.bootstrap_hash) == 64

    assert record.verify_bootstrap_hash() is True

    try:
        record.service_started = True

        raise AssertionError(
            "bootstrap record must be immutable"
        )

    except FrozenInstanceError:
        pass

    return record


def run_deterministic_replay_test():
    first = build_bootstrap_record()

    second = build_bootstrap_record()

    assert first == second

    assert first.bootstrap_id == second.bootstrap_id

    assert first.bootstrap_hash == second.bootstrap_hash

    assert first.verify_bootstrap_hash() is True

    assert second.verify_bootstrap_hash() is True


def run_lineage_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=(
                "OEM-014",
                "OEM-015",
            ),
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "incomplete OEM lineage must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=(
                REQUIRED_OEM_RUNTIME_LINEAGE
            ),
            ola_boundaries=(
                "OLA-017",
                "OLA-018",
                "OLA-020",
                "OLA-021",
            ),
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "missing OLA-019 boundary must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass


def run_runtime_path_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=(
                Path("C:/outside/state")
            ),
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "state path outside runtime root must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=(
                RUNTIME_ROOT
                / "data"
            ),
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "wrong runtime state role must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=(
                RUNTIME_ROOT
                / "cache"
            ),
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={},
        )

        raise AssertionError(
            "wrong runtime logs role must fail closed"
        )

    except OracleLiveShadowServiceBootstrapCompatibilityError:
        pass


def run_contract_fail_closed_tests():
    contract = build_bootstrap_contract()

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=datetime(
                2026,
                7,
                12,
                18,
                0,
                0,
            ),
            bootstrap_metadata={},
        )

        raise AssertionError(
            "naive bootstrap timestamp must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass

    try:
        contract.bootstrap(
            oem_runtime_lineage=REQUIRED_OEM_RUNTIME_LINEAGE,
            ola_boundaries=REQUIRED_OLA_BOUNDARIES,
            runtime_root=RUNTIME_ROOT,
            runtime_state_directory=RUNTIME_STATE,
            runtime_logs_directory=RUNTIME_LOGS,
            bootstrapped_at=BOOTSTRAPPED_AT,
            bootstrap_metadata={
                "api_key": "must-not-enter-bootstrap"
            },
        )

        raise AssertionError(
            "secret metadata must fail closed"
        )

    except OracleLiveShadowServiceBootstrapContractError:
        pass


def main():
    bootstrap_contract = run_bootstrap_contract_test()

    record = run_bootstrap_record_test()

    run_deterministic_replay_test()

    run_lineage_fail_closed_tests()

    run_runtime_path_fail_closed_tests()

    run_contract_fail_closed_tests()

    result = {
        "schema_version": record.schema_version,
        "engine_id": record.engine_id,
        "status": "passed",
        "bootstrap_status": record.bootstrap_status,
        "oracle_service_id": record.oracle_service_id,
        "qseries_service_id": record.qseries_service_id,
        "separate_process_required": (
            record.separate_process_required
        ),
        "oracle_execution_authority": (
            record.oracle_execution_authority
        ),
        "direct_execution_import_allowed": (
            record.direct_execution_import_allowed
        ),
        "oem_013_lineage_required": (
            "OEM-013" in record.oem_runtime_lineage
        ),
        "oem_014_lineage_required": (
            "OEM-014" in record.oem_runtime_lineage
        ),
        "oem_015_lineage_required": (
            "OEM-015" in record.oem_runtime_lineage
        ),
        "ola_017_cycle_boundary_required": (
            record.ola_017_cycle_boundary_required
        ),
        "ola_018_readiness_required": (
            record.ola_018_readiness_required
        ),
        "ola_019_polling_policy_required": (
            record.ola_019_polling_policy_required
        ),
        "ola_020_service_isolation_required": (
            record.ola_020_service_isolation_required
        ),
        "ola_021_scheduler_tick_required": (
            record.ola_021_scheduler_tick_required
        ),
        "runtime_state_role": record.runtime_state_role,
        "runtime_logs_role": record.runtime_logs_role,
        "runtime_state_inside_runtime_root": True,
        "runtime_logs_inside_runtime_root": True,
        "wrong_state_role_blocked": True,
        "wrong_logs_role_blocked": True,
        "incomplete_oem_lineage_blocked": True,
        "missing_ola_boundary_blocked": True,
        "deterministic_bootstrap_hashing": True,
        "service_start_allowed": (
            record.service_start_allowed
        ),
        "service_started": record.service_started,
        "process_created": record.process_created,
        "thread_created": record.thread_created,
        "loop_started": record.loop_started,
        "sleep_performed": record.sleep_performed,
        "acquisition_invoked": (
            record.acquisition_invoked
        ),
        "scheduler_tick_invoked": (
            record.scheduler_tick_invoked
        ),
        "shadow_cycle_invoked": (
            record.shadow_cycle_invoked
        ),
        "canonical_handoff_published": (
            record.canonical_handoff_published
        ),
        "alert_created": record.alert_created,
        "qseries_intake_record_created": (
            record.qseries_intake_record_created
        ),
        "read_only": bootstrap_contract.read_only,
        "execution_allowed": record.execution_allowed,
        "execution_adapter_resolved": (
            record.execution_adapter_resolved
        ),
        "execution_adapter_invoked": (
            record.execution_adapter_invoked
        ),
        "trade_authorization_allowed": (
            record.trade_authorization_allowed
        ),
        "order_placement_allowed": (
            record.order_placement_allowed
        ),
        "funds_moved": record.funds_moved,
        "portfolio_mutated": record.portfolio_mutated,
    }

    print(
        "[PASS] OLA-022 Oracle Live Shadow Service "
        "Bootstrap Contract"
    )

    print(result)


if __name__ == "__main__":
    main()
'''


EXPORT_BLOCK = r'''

from .oracle_live_shadow_service_bootstrap_contract import (
    ORACLE_SERVICE_ID as LIVE_SHADOW_ORACLE_SERVICE_ID,
    REQUIRED_OEM_RUNTIME_LINEAGE,
    REQUIRED_OLA_BOUNDARIES,
    REQUIRED_RUNTIME_LOGS_ROLE,
    REQUIRED_RUNTIME_STATE_ROLE,
    SERVICE_BOOTSTRAP_STATUS_READY,
    OracleLiveShadowServiceBootstrapCompatibilityError,
    OracleLiveShadowServiceBootstrapContract,
    OracleLiveShadowServiceBootstrapContractError,
    OracleLiveShadowServiceBootstrapInvariantError,
    OracleLiveShadowServiceBootstrapRecord,
)
'''


EXPORT_NAMES = [
    "LIVE_SHADOW_ORACLE_SERVICE_ID",
    "REQUIRED_OEM_RUNTIME_LINEAGE",
    "REQUIRED_OLA_BOUNDARIES",
    "REQUIRED_RUNTIME_LOGS_ROLE",
    "REQUIRED_RUNTIME_STATE_ROLE",
    "SERVICE_BOOTSTRAP_STATUS_READY",
    "OracleLiveShadowServiceBootstrapCompatibilityError",
    "OracleLiveShadowServiceBootstrapContract",
    "OracleLiveShadowServiceBootstrapContractError",
    "OracleLiveShadowServiceBootstrapInvariantError",
    "OracleLiveShadowServiceBootstrapRecord",
]


def write_file(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        textwrap.dedent(content).lstrip(),
        encoding="utf-8",
    )

    print(f"[OK] Wrote {path}")


def update_package_exports() -> None:
    existing = PACKAGE_INIT_PATH.read_text(
        encoding="utf-8"
    )

    import_marker = (
        "from .oracle_live_shadow_service_bootstrap_"
        "contract import"
    )

    updated = existing

    if import_marker not in updated:
        updated = (
            updated.rstrip()
            + "\n"
            + textwrap.dedent(EXPORT_BLOCK)
        )

    all_start = updated.find("__all__ = [")

    if all_start == -1:
        raise RuntimeError(
            "__init__.py does not contain __all__"
        )

    closing_index = updated.find(
        "]",
        all_start,
    )

    if closing_index == -1:
        raise RuntimeError(
            "__init__.py does not contain "
            "__all__ closing bracket"
        )

    for name in EXPORT_NAMES:
        export_line = f'    "{name}",'

        if export_line in updated[
            all_start:closing_index
        ]:
            continue

        updated = (
            updated[:closing_index]
            + export_line
            + "\n"
            + updated[closing_index:]
        )

        closing_index += len(
            export_line
        ) + 1

    PACKAGE_INIT_PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print(
        f"[OK] Updated {PACKAGE_INIT_PATH}"
    )


def main() -> None:
    print("========================================")
    print(" OLA-022 INSTALLER")
    print(" Oracle Live Shadow Service")
    print(" Bootstrap Contract")
    print("========================================")

    write_file(
        MODULE_PATH,
        MODULE_CONTENT,
    )

    write_file(
        TEST_PATH,
        TEST_CONTENT,
    )

    update_package_exports()

    print()
    print("[DONE] OLA-022 installed")
    print()
    print("Run:")
    print(
        "py test_ola_022_oracle_live_shadow_service_"
        "bootstrap_contract.py"
    )


if __name__ == "__main__":
    main()