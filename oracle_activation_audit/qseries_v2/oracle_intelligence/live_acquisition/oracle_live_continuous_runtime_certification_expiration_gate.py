"""
OLA-085
Oracle Live Continuous Runtime Certification Expiration Gate

Classifies the verified OLA-084 current certification as current,
renewal-due, or expired under an explicit operator policy.

Canonical lineage:

- OLA-074 guarded continuous runtime
- OLA-068 passive PostgreSQL advancement monitor
- OLA-081 live advancement gate
- OLA-082 sustained advancement certification
- OLA-083 durable certification attestation
- OLA-084 current certification status gate
- OLA-085 certification expiration gate

OLA-085 is strictly read-only. It does not contact PostgreSQL, rerun
certification, start or stop Oracle, invoke acquisition, mutate runtime
locks, or write certification evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_current_certification_status_gate import (
    DEFAULT_CURRENT_RELATIVE_PATH,
    OracleLiveContinuousRuntimeCurrentCertificationStatus,
    evaluate_oracle_live_continuous_runtime_current_certification_status,
)


SCHEMA_VERSION = "OLA-085"
ENGINE_ID = "OLA-085"
UPSTREAM_STATUS_SCHEMA_VERSION = "OLA-084"
UPSTREAM_ATTESTATION_SCHEMA_VERSION = "OLA-083"
UPSTREAM_CERTIFICATION_SCHEMA_VERSION = "OLA-082"
UPSTREAM_ADVANCEMENT_SCHEMA_VERSION = "OLA-081"
UPSTREAM_MONITOR_SCHEMA_VERSION = "OLA-068"
UPSTREAM_RUNTIME_SCHEMA_VERSION = "OLA-074"

DEFAULT_EXPIRATION_AGE_SECONDS = 24.0 * 60.0 * 60.0
DEFAULT_RENEWAL_WARNING_SECONDS = 4.0 * 60.0 * 60.0
UPSTREAM_VALIDATION_MAXIMUM_AGE_SECONDS = 100.0 * 365.25 * 24.0 * 60.0 * 60.0

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


class OracleLiveContinuousRuntimeCertificationExpirationError(RuntimeError):
    """Base OLA-085 failure."""


class OracleLiveContinuousRuntimeCertificationExpirationContractError(
    OracleLiveContinuousRuntimeCertificationExpirationError
):
    """Malformed OLA-085 invocation or upstream status."""


class OracleLiveContinuousRuntimeCertificationExpired(
    OracleLiveContinuousRuntimeCertificationExpirationError
):
    """Raised by the strict gate when certification has expired."""


def require_aware_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            f"{field_name} must be timezone-aware"
        )
    return value


def require_positive_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            f"{field_name} must be a positive number"
        )
    normalized = float(value)
    if normalized <= 0.0:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            f"{field_name} must be greater than zero"
        )
    return normalized


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return require_aware_datetime(value, "canonical datetime").isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): canonicalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
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


def validate_upstream_status(
    status: OracleLiveContinuousRuntimeCurrentCertificationStatus,
) -> None:
    if not isinstance(status, OracleLiveContinuousRuntimeCurrentCertificationStatus):
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream status must be an OLA-084 status record"
        )
    if status.schema_version != UPSTREAM_STATUS_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream status schema_version must be OLA-084"
        )
    if status.engine_id != UPSTREAM_STATUS_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream status engine_id must be OLA-084"
        )
    if status.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream OLA-084 status hash is invalid"
        )
    if status.certified is not True or status.certification_fresh is not True:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream OLA-084 status must be certified and validated"
        )
    if status.read_only is not True:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "upstream OLA-084 status must be read-only"
        )
    for field_name in (
        "execution_allowed", "alerts_allowed", "qseries_handoff_allowed",
        "trade_authorization_allowed", "order_placement_allowed", "funds_moved",
        "portfolio_mutated", "postgresql_read_performed", "postgresql_write_performed",
        "runtime_started", "runtime_stopped", "runtime_restarted", "runtime_imported",
        "runtime_invoked", "runtime_lock_mutated", "files_written",
    ):
        if getattr(status, field_name) is not False:
            raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
                f"upstream unsafe field must be false: {field_name}"
            )


@dataclass(frozen=True)
class OracleLiveContinuousRuntimeCertificationExpirationStatus:
    schema_version: str
    engine_id: str
    status: str
    certified: bool
    usable: bool
    renewal_required: bool
    expired: bool
    checked_at: datetime
    certification_published_at: datetime
    certification_age_seconds: float
    expiration_age_seconds: float
    renewal_warning_seconds: float
    renewal_due_at_age_seconds: float
    seconds_until_renewal_due: float
    seconds_until_expiration: float
    attestation_id: str
    attestation_hash: str
    upstream_status_hash: str
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


def evaluate_oracle_live_continuous_runtime_certification_expiration(
    *,
    repository_root: Path,
    checked_at: datetime,
    expiration_age_seconds: float = DEFAULT_EXPIRATION_AGE_SECONDS,
    renewal_warning_seconds: float = DEFAULT_RENEWAL_WARNING_SECONDS,
    current_relative_path: Path = DEFAULT_CURRENT_RELATIVE_PATH,
) -> OracleLiveContinuousRuntimeCertificationExpirationStatus:
    repository_root = Path(repository_root).resolve()
    if not repository_root.is_dir():
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "repository_root must exist"
        )
    checked_at = require_aware_datetime(checked_at, "checked_at")
    expiration_age_seconds = require_positive_number(
        expiration_age_seconds, "expiration_age_seconds"
    )
    renewal_warning_seconds = require_positive_number(
        renewal_warning_seconds, "renewal_warning_seconds"
    )
    if renewal_warning_seconds >= expiration_age_seconds:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "renewal_warning_seconds must be less than expiration_age_seconds"
        )

    upstream_status = evaluate_oracle_live_continuous_runtime_current_certification_status(
        repository_root=repository_root,
        checked_at=checked_at,
        maximum_certification_age_seconds=UPSTREAM_VALIDATION_MAXIMUM_AGE_SECONDS,
        current_relative_path=current_relative_path,
    )
    validate_upstream_status(upstream_status)

    age = float(upstream_status.certification_age_seconds)
    renewal_due_age = expiration_age_seconds - renewal_warning_seconds
    expired = age > expiration_age_seconds
    renewal_required = (not expired) and age >= renewal_due_age
    usable = not expired
    if expired:
        state = "expired"
    elif renewal_required:
        state = "renewal_due"
    else:
        state = "certified_current"

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": state,
        "certified": True,
        "usable": usable,
        "renewal_required": renewal_required,
        "expired": expired,
        "checked_at": checked_at,
        "certification_published_at": upstream_status.certification_published_at,
        "certification_age_seconds": age,
        "expiration_age_seconds": expiration_age_seconds,
        "renewal_warning_seconds": renewal_warning_seconds,
        "renewal_due_at_age_seconds": renewal_due_age,
        "seconds_until_renewal_due": max(0.0, renewal_due_age - age),
        "seconds_until_expiration": max(0.0, expiration_age_seconds - age),
        "attestation_id": upstream_status.attestation_id,
        "attestation_hash": upstream_status.attestation_hash,
        "upstream_status_hash": upstream_status.status_hash,
        "upstream_status_schema_version": upstream_status.schema_version,
        "upstream_attestation_schema_version": upstream_status.upstream_attestation_schema_version,
        "upstream_certification_schema_version": upstream_status.upstream_certification_schema_version,
        "upstream_advancement_schema_version": upstream_status.upstream_advancement_schema_version,
        "upstream_monitor_schema_version": upstream_status.upstream_monitor_schema_version,
        "upstream_runtime_schema_version": upstream_status.upstream_runtime_schema_version,
        "current_file": upstream_status.current_file,
        "immutable_evidence_file": upstream_status.immutable_evidence_file,
        "lineage_verified": upstream_status.lineage_verified,
        "safety_boundary_verified": upstream_status.safety_boundary_verified,
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
    }
    result = OracleLiveContinuousRuntimeCertificationExpirationStatus(
        **record_without_hash,
        status_hash=stable_hash(record_without_hash),
    )
    if result.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationExpirationContractError(
            "constructed OLA-085 status hash is invalid"
        )
    return result


def require_oracle_live_continuous_runtime_certification_unexpired(
    **kwargs: Any,
) -> OracleLiveContinuousRuntimeCertificationExpirationStatus:
    result = evaluate_oracle_live_continuous_runtime_certification_expiration(**kwargs)
    if result.expired:
        raise OracleLiveContinuousRuntimeCertificationExpired(
            "Oracle live continuous runtime certification expired: "
            f"age={result.certification_age_seconds:.3f}s, "
            f"expiration={result.expiration_age_seconds:.3f}s"
        )
    return result
