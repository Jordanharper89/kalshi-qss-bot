"""
OLA-088
Oracle Live Continuous Runtime Certification Renewal Invocation Readiness Gate

Consumes the hash-verified OLA-087 renewal authorization status and determines
whether a later renewal executor may be invoked.

OLA-088 is readiness-decision only. It never performs renewal, never imports or
invokes the Oracle runtime, never contacts PostgreSQL, never mutates runtime
locks, and never writes or replaces certification evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_expiration_gate import (
    DEFAULT_EXPIRATION_AGE_SECONDS,
    DEFAULT_RENEWAL_WARNING_SECONDS,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_renewal_authorization_gate import (
    OracleLiveContinuousRuntimeCertificationRenewalAuthorizationStatus,
    evaluate_oracle_live_continuous_runtime_certification_renewal_authorization,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_current_certification_status_gate import (
    DEFAULT_CURRENT_RELATIVE_PATH,
)

SCHEMA_VERSION = "OLA-088"
ENGINE_ID = "OLA-088"
UPSTREAM_AUTHORIZATION_SCHEMA_VERSION = "OLA-087"
UPSTREAM_RENEWAL_SCHEMA_VERSION = "OLA-086"
UPSTREAM_EXPIRATION_SCHEMA_VERSION = "OLA-085"
UPSTREAM_STATUS_SCHEMA_VERSION = "OLA-084"
UPSTREAM_ATTESTATION_SCHEMA_VERSION = "OLA-083"
UPSTREAM_CERTIFICATION_SCHEMA_VERSION = "OLA-082"
UPSTREAM_ADVANCEMENT_SCHEMA_VERSION = "OLA-081"
UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_RUNTIME_SCHEMA_VERSION = "OLA-074"

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
RENEWAL_PERFORMED = False
CERTIFICATION_EVIDENCE_MUTATED = False
RENEWAL_EXECUTOR_IMPORTED = False
RENEWAL_EXECUTOR_INVOKED = False


class OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessError(RuntimeError):
    """Base OLA-088 failure."""


class OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
    OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessError
):
    """Malformed OLA-088 invocation or upstream OLA-087 status."""


class OracleLiveContinuousRuntimeCertificationRenewalInvocationNotReady(
    OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessError
):
    """Raised when strict readiness is requested without authorization."""


def require_aware_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            f"{field_name} must be timezone-aware"
        )
    return value


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return require_aware_datetime(value, "canonical datetime").isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): canonicalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
        f"unsupported canonical value type: {type(value).__name__}"
    )


def stable_hash(value: Any) -> str:
    import json

    payload = json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def validate_upstream_authorization_status(
    status: OracleLiveContinuousRuntimeCertificationRenewalAuthorizationStatus,
) -> None:
    if not isinstance(status, OracleLiveContinuousRuntimeCertificationRenewalAuthorizationStatus):
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream status must be an OLA-087 renewal authorization record"
        )
    if status.schema_version != UPSTREAM_AUTHORIZATION_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream status schema_version must be OLA-087"
        )
    if status.engine_id != UPSTREAM_AUTHORIZATION_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream status engine_id must be OLA-087"
        )
    if status.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 status hash is invalid"
        )
    supported = {
        "renewal_not_permitted",
        "renewal_eligible_awaiting_authorization",
        "renewal_eligible_authorized",
        "renewal_required_awaiting_authorization",
        "renewal_required_authorized",
    }
    if status.status not in supported:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 status is unsupported"
        )
    expected_authorized = status.status in {
        "renewal_eligible_authorized", "renewal_required_authorized"
    }
    if status.renewal_authorized is not expected_authorized:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 authorization flag contradicts status"
        )
    if status.operator_authorization_present is not expected_authorized:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 operator authorization presence contradicts status"
        )
    if expected_authorized:
        if not status.operator_authorization_id:
            raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
                "authorized upstream status requires operator authorization identity"
            )
        require_aware_datetime(status.authorized_at, "upstream authorized_at")
    else:
        if status.operator_authorization_id != "" or status.authorized_at is not None:
            raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
                "unauthorized upstream status contains authorization evidence"
            )
    if status.lineage_verified is not True or status.safety_boundary_verified is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 lineage and safety boundary must be verified"
        )
    if status.read_only is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "upstream OLA-087 status must be read-only"
        )
    for field_name in (
        "execution_allowed", "alerts_allowed", "qseries_handoff_allowed",
        "trade_authorization_allowed", "order_placement_allowed", "funds_moved",
        "portfolio_mutated", "postgresql_read_performed", "postgresql_write_performed",
        "runtime_started", "runtime_stopped", "runtime_restarted", "runtime_imported",
        "runtime_invoked", "runtime_lock_mutated", "files_written", "renewal_performed",
        "certification_evidence_mutated",
    ):
        if getattr(status, field_name) is not False:
            raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
                f"upstream unsafe field must be false: {field_name}"
            )


@dataclass(frozen=True)
class OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus:
    schema_version: str
    engine_id: str
    status: str
    renewal_invocation_ready: bool
    renewal_eligible: bool
    renewal_required: bool
    renewal_authorized: bool
    operator_authorization_id: str
    authorized_at: datetime | None
    checked_at: datetime
    certification_usable: bool
    certification_expired: bool
    certification_published_at: datetime
    certification_age_seconds: float
    renewal_due_at_age_seconds: float
    expiration_age_seconds: float
    seconds_until_renewal_due: float
    seconds_until_expiration: float
    attestation_id: str
    attestation_hash: str
    upstream_authorization_status: str
    upstream_authorization_status_hash: str
    upstream_authorization_schema_version: str
    upstream_renewal_schema_version: str
    upstream_expiration_schema_version: str
    upstream_status_schema_version: str
    upstream_attestation_schema_version: str
    upstream_certification_schema_version: str
    upstream_advancement_schema_version: str
    upstream_monitor_schema_version: str
    upstream_runtime_schema_version: str
    current_file: str
    immutable_evidence_file: str
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
    renewal_performed: bool
    certification_evidence_mutated: bool
    renewal_executor_imported: bool
    renewal_executor_invoked: bool
    status_hash: str

    def to_canonical_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        result = {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
            if field_name != "status_hash"
        }
        if include_hash:
            result["status_hash"] = self.status_hash
        return result

    def verify_status_hash(self) -> bool:
        return self.status_hash == stable_hash(self.to_canonical_dict(include_hash=False))


def evaluate_oracle_live_continuous_runtime_certification_renewal_invocation_readiness(
    *,
    repository_root: Path,
    checked_at: datetime,
    operator_authorized: bool = False,
    operator_authorization_id: str = "",
    authorized_at: datetime | None = None,
    expiration_age_seconds: float = DEFAULT_EXPIRATION_AGE_SECONDS,
    renewal_warning_seconds: float = DEFAULT_RENEWAL_WARNING_SECONDS,
    current_relative_path: Path = DEFAULT_CURRENT_RELATIVE_PATH,
) -> OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus:
    repository_root = Path(repository_root).resolve()
    if not repository_root.is_dir():
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "repository_root must exist"
        )
    checked_at = require_aware_datetime(checked_at, "checked_at")

    upstream = evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
        repository_root=repository_root,
        checked_at=checked_at,
        operator_authorized=operator_authorized,
        operator_authorization_id=operator_authorization_id,
        authorized_at=authorized_at,
        expiration_age_seconds=expiration_age_seconds,
        renewal_warning_seconds=renewal_warning_seconds,
        current_relative_path=current_relative_path,
    )
    validate_upstream_authorization_status(upstream)

    renewal_invocation_ready = upstream.renewal_authorized is True
    if renewal_invocation_ready:
        status = "renewal_required_invocation_ready" if upstream.renewal_required else "renewal_eligible_invocation_ready"
    elif upstream.status == "renewal_not_permitted":
        status = "renewal_invocation_prohibited"
    elif upstream.renewal_required:
        status = "renewal_required_invocation_blocked"
    else:
        status = "renewal_eligible_invocation_blocked"

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "renewal_invocation_ready": renewal_invocation_ready,
        "renewal_eligible": upstream.renewal_eligible,
        "renewal_required": upstream.renewal_required,
        "renewal_authorized": upstream.renewal_authorized,
        "operator_authorization_id": upstream.operator_authorization_id,
        "authorized_at": upstream.authorized_at,
        "checked_at": checked_at,
        "certification_usable": upstream.certification_usable,
        "certification_expired": upstream.certification_expired,
        "certification_published_at": upstream.certification_published_at,
        "certification_age_seconds": upstream.certification_age_seconds,
        "renewal_due_at_age_seconds": upstream.renewal_due_at_age_seconds,
        "expiration_age_seconds": upstream.expiration_age_seconds,
        "seconds_until_renewal_due": upstream.seconds_until_renewal_due,
        "seconds_until_expiration": upstream.seconds_until_expiration,
        "attestation_id": upstream.attestation_id,
        "attestation_hash": upstream.attestation_hash,
        "upstream_authorization_status": upstream.status,
        "upstream_authorization_status_hash": upstream.status_hash,
        "upstream_authorization_schema_version": UPSTREAM_AUTHORIZATION_SCHEMA_VERSION,
        "upstream_renewal_schema_version": upstream.upstream_renewal_schema_version,
        "upstream_expiration_schema_version": upstream.upstream_expiration_schema_version,
        "upstream_status_schema_version": upstream.upstream_status_schema_version,
        "upstream_attestation_schema_version": upstream.upstream_attestation_schema_version,
        "upstream_certification_schema_version": upstream.upstream_certification_schema_version,
        "upstream_advancement_schema_version": upstream.upstream_advancement_schema_version,
        "upstream_monitor_schema_version": upstream.upstream_monitor_schema_version,
        "upstream_runtime_schema_version": upstream.upstream_runtime_schema_version,
        "current_file": upstream.current_file,
        "immutable_evidence_file": upstream.immutable_evidence_file,
        "lineage_verified": upstream.lineage_verified,
        "safety_boundary_verified": upstream.safety_boundary_verified,
        "read_only": READ_ONLY,
        "execution_allowed": EXECUTION_ALLOWED,
        "alerts_allowed": ALERTS_ALLOWED,
        "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
        "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
        "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
        "funds_moved": FUNDS_MOVED,
        "portfolio_mutated": PORTFOLIO_MUTATED,
        "postgresql_read_performed": POSTGRESQL_READ_PERFORMED,
        "postgresql_write_performed": POSTGRESQL_WRITE_PERFORMED,
        "runtime_started": RUNTIME_STARTED,
        "runtime_stopped": RUNTIME_STOPPED,
        "runtime_restarted": RUNTIME_RESTARTED,
        "runtime_imported": RUNTIME_IMPORTED,
        "runtime_invoked": RUNTIME_INVOKED,
        "runtime_lock_mutated": RUNTIME_LOCK_MUTATED,
        "files_written": FILES_WRITTEN,
        "renewal_performed": RENEWAL_PERFORMED,
        "certification_evidence_mutated": CERTIFICATION_EVIDENCE_MUTATED,
        "renewal_executor_imported": RENEWAL_EXECUTOR_IMPORTED,
        "renewal_executor_invoked": RENEWAL_EXECUTOR_INVOKED,
    }
    result = OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus(
        **record_without_hash,
        status_hash=stable_hash(record_without_hash),
    )
    if result.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessContractError(
            "constructed OLA-088 status hash is invalid"
        )
    return result


def require_oracle_live_continuous_runtime_certification_renewal_invocation_ready(
    **kwargs: Any,
) -> OracleLiveContinuousRuntimeCertificationRenewalInvocationReadinessStatus:
    result = evaluate_oracle_live_continuous_runtime_certification_renewal_invocation_readiness(**kwargs)
    if result.renewal_invocation_ready is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalInvocationNotReady(
            "Oracle live continuous runtime certification renewal invocation is not ready: "
            f"status={result.status}"
        )
    return result
