from __future__ import annotations

from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PRODUCTION_PATH = ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition" / "oracle_live_continuous_runtime_certification_renewal_eligibility_gate.py"
TEST_PATH = ROOT / "test_ola_086_oracle_live_continuous_runtime_certification_renewal_eligibility_gate.py"

PRODUCTION_SOURCE = r'''"""
OLA-086
Oracle Live Continuous Runtime Certification Renewal Eligibility Gate

Consumes the hash-verified OLA-085 expiration state and determines whether
certification renewal is not yet allowed, eligible, or mandatory.

OLA-086 is a decision-only, read-only gate. It never reruns certification,
never starts or stops Oracle, never contacts PostgreSQL, never mutates runtime
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
    OracleLiveContinuousRuntimeCertificationExpirationStatus,
    evaluate_oracle_live_continuous_runtime_certification_expiration,
)
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_current_certification_status_gate import (
    DEFAULT_CURRENT_RELATIVE_PATH,
)

SCHEMA_VERSION = "OLA-086"
ENGINE_ID = "OLA-086"
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


class OracleLiveContinuousRuntimeCertificationRenewalEligibilityError(RuntimeError):
    """Base OLA-086 failure."""


class OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
    OracleLiveContinuousRuntimeCertificationRenewalEligibilityError
):
    """Malformed OLA-086 invocation or upstream OLA-085 status."""


class OracleLiveContinuousRuntimeCertificationRenewalNotEligible(
    OracleLiveContinuousRuntimeCertificationRenewalEligibilityError
):
    """Raised when strict renewal eligibility is requested before the window."""


def require_aware_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            f"{field_name} must be a datetime"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
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
    raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
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


def validate_upstream_expiration_status(
    status: OracleLiveContinuousRuntimeCertificationExpirationStatus,
) -> None:
    if not isinstance(status, OracleLiveContinuousRuntimeCertificationExpirationStatus):
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream status must be an OLA-085 expiration record"
        )
    if status.schema_version != UPSTREAM_EXPIRATION_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream status schema_version must be OLA-085"
        )
    if status.engine_id != UPSTREAM_EXPIRATION_SCHEMA_VERSION:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream status engine_id must be OLA-085"
        )
    if status.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream OLA-085 status hash is invalid"
        )
    if status.status not in {"certified_current", "renewal_due", "expired"}:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream OLA-085 status is unsupported"
        )
    if status.certified is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream OLA-085 status must remain certification-derived"
        )
    if status.lineage_verified is not True or status.safety_boundary_verified is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream OLA-085 lineage and safety boundary must be verified"
        )
    if status.read_only is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "upstream OLA-085 status must be read-only"
        )
    for field_name in (
        "execution_allowed", "alerts_allowed", "qseries_handoff_allowed",
        "trade_authorization_allowed", "order_placement_allowed", "funds_moved",
        "portfolio_mutated", "postgresql_read_performed", "postgresql_write_performed",
        "runtime_started", "runtime_stopped", "runtime_restarted", "runtime_imported",
        "runtime_invoked", "runtime_lock_mutated", "files_written",
    ):
        if getattr(status, field_name) is not False:
            raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
                f"upstream unsafe field must be false: {field_name}"
            )


@dataclass(frozen=True)
class OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus:
    schema_version: str
    engine_id: str
    status: str
    renewal_eligible: bool
    renewal_required: bool
    certification_usable: bool
    certification_expired: bool
    checked_at: datetime
    certification_published_at: datetime
    certification_age_seconds: float
    renewal_due_at_age_seconds: float
    expiration_age_seconds: float
    seconds_until_renewal_due: float
    seconds_until_expiration: float
    attestation_id: str
    attestation_hash: str
    upstream_expiration_status: str
    upstream_expiration_status_hash: str
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


def evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility(
    *,
    repository_root: Path,
    checked_at: datetime,
    expiration_age_seconds: float = DEFAULT_EXPIRATION_AGE_SECONDS,
    renewal_warning_seconds: float = DEFAULT_RENEWAL_WARNING_SECONDS,
    current_relative_path: Path = DEFAULT_CURRENT_RELATIVE_PATH,
) -> OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus:
    repository_root = Path(repository_root).resolve()
    if not repository_root.is_dir():
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "repository_root must exist"
        )
    checked_at = require_aware_datetime(checked_at, "checked_at")

    upstream = evaluate_oracle_live_continuous_runtime_certification_expiration(
        repository_root=repository_root,
        checked_at=checked_at,
        expiration_age_seconds=expiration_age_seconds,
        renewal_warning_seconds=renewal_warning_seconds,
        current_relative_path=current_relative_path,
    )
    validate_upstream_expiration_status(upstream)

    if upstream.status == "certified_current":
        status = "renewal_not_due"
        renewal_eligible = False
        renewal_required = False
    elif upstream.status == "renewal_due":
        status = "renewal_eligible"
        renewal_eligible = True
        renewal_required = False
    else:
        status = "renewal_required"
        renewal_eligible = True
        renewal_required = True

    record_without_hash = {
        "schema_version": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "status": status,
        "renewal_eligible": renewal_eligible,
        "renewal_required": renewal_required,
        "certification_usable": upstream.usable,
        "certification_expired": upstream.expired,
        "checked_at": checked_at,
        "certification_published_at": upstream.certification_published_at,
        "certification_age_seconds": upstream.certification_age_seconds,
        "renewal_due_at_age_seconds": upstream.renewal_due_at_age_seconds,
        "expiration_age_seconds": upstream.expiration_age_seconds,
        "seconds_until_renewal_due": upstream.seconds_until_renewal_due,
        "seconds_until_expiration": upstream.seconds_until_expiration,
        "attestation_id": upstream.attestation_id,
        "attestation_hash": upstream.attestation_hash,
        "upstream_expiration_status": upstream.status,
        "upstream_expiration_status_hash": upstream.status_hash,
        "upstream_expiration_schema_version": UPSTREAM_EXPIRATION_SCHEMA_VERSION,
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
    }
    result = OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus(
        **record_without_hash,
        status_hash=stable_hash(record_without_hash),
    )
    if result.verify_status_hash() is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalEligibilityContractError(
            "constructed OLA-086 status hash is invalid"
        )
    return result


def require_oracle_live_continuous_runtime_certification_renewal_eligible(
    **kwargs: Any,
) -> OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus:
    result = evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility(**kwargs)
    if result.renewal_eligible is not True:
        raise OracleLiveContinuousRuntimeCertificationRenewalNotEligible(
            "Oracle live continuous runtime certification renewal is not yet eligible: "
            f"age={result.certification_age_seconds:.3f}s, "
            f"renewal_due_at={result.renewal_due_at_age_seconds:.3f}s"
        )
    return result
'''

TEST_SOURCE = r'''from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
MODULE_PATH = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition"
    / "oracle_live_continuous_runtime_certification_renewal_eligibility_gate.py"
)


def load_module():
    name = "ola086_test_target"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def make_upstream(module, checked_at, upstream_status):
    upstream_module = __import__(
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_live_continuous_runtime_certification_expiration_gate",
        fromlist=["OracleLiveContinuousRuntimeCertificationExpirationStatus"],
    )
    cls = upstream_module.OracleLiveContinuousRuntimeCertificationExpirationStatus
    age = {"certified_current": 10.0, "renewal_due": 85.0, "expired": 101.0}[upstream_status]
    usable = upstream_status != "expired"
    renewal_required = upstream_status != "certified_current"
    expired = upstream_status == "expired"
    values = {
        "schema_version": "OLA-085", "engine_id": "OLA-085",
        "status": upstream_status, "certified": True, "usable": usable,
        "renewal_required": renewal_required, "expired": expired,
        "checked_at": checked_at,
        "certification_published_at": checked_at - timedelta(seconds=age),
        "certification_age_seconds": age,
        "expiration_age_seconds": 100.0,
        "renewal_warning_seconds": 20.0,
        "renewal_due_at_age_seconds": 80.0,
        "seconds_until_renewal_due": 80.0 - age,
        "seconds_until_expiration": 100.0 - age,
        "attestation_id": "attestation-test", "attestation_hash": "a" * 64,
        "upstream_status_hash": "b" * 64,
        "upstream_status_schema_version": "OLA-084",
        "upstream_attestation_schema_version": "OLA-083",
        "upstream_certification_schema_version": "OLA-082",
        "upstream_advancement_schema_version": "OLA-081",
        "upstream_monitor_schema_version": "OLA-068",
        "upstream_runtime_schema_version": "OLA-074",
        "current_file": "runtime/oracle_live_shadow/certifications/ola083/current.json",
        "immutable_evidence_file": "runtime/oracle_live_shadow/certifications/ola083/evidence/test.json",
        "lineage_verified": True, "safety_boundary_verified": True,
        "read_only": True, "execution_allowed": False, "alerts_allowed": False,
        "qseries_handoff_allowed": False, "trade_authorization_allowed": False,
        "order_placement_allowed": False, "funds_moved": False,
        "portfolio_mutated": False, "postgresql_read_performed": False,
        "postgresql_write_performed": False, "runtime_started": False,
        "runtime_stopped": False, "runtime_restarted": False,
        "runtime_imported": False, "runtime_invoked": False,
        "runtime_lock_mutated": False, "files_written": False,
    }
    return cls(**values, status_hash=upstream_module.stable_hash(values))


def main():
    module = load_module()
    checked_at = datetime(2026, 7, 20, 0, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        expectations = {
            "certified_current": ("renewal_not_due", False, False),
            "renewal_due": ("renewal_eligible", True, False),
            "expired": ("renewal_required", True, True),
        }
        for upstream_status, expected in expectations.items():
            upstream = make_upstream(module, checked_at, upstream_status)
            module.evaluate_oracle_live_continuous_runtime_certification_expiration = (
                lambda **kwargs: upstream
            )
            result = module.evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility(
                repository_root=root,
                checked_at=checked_at,
                expiration_age_seconds=100.0,
                renewal_warning_seconds=20.0,
            )
            assert (result.status, result.renewal_eligible, result.renewal_required) == expected
            assert result.verify_status_hash() is True
            assert result.read_only is True
            assert result.renewal_performed is False
            assert result.certification_evidence_mutated is False
            assert result.postgresql_read_performed is False
            assert result.runtime_invoked is False

        not_due = make_upstream(module, checked_at, "certified_current")
        module.evaluate_oracle_live_continuous_runtime_certification_expiration = lambda **kwargs: not_due
        try:
            module.require_oracle_live_continuous_runtime_certification_renewal_eligible(
                repository_root=root,
                checked_at=checked_at,
                expiration_age_seconds=100.0,
                renewal_warning_seconds=20.0,
            )
        except module.OracleLiveContinuousRuntimeCertificationRenewalNotEligible:
            pass
        else:
            raise AssertionError("strict renewal eligibility gate accepted not-due certification")

        due = make_upstream(module, checked_at, "renewal_due")
        module.evaluate_oracle_live_continuous_runtime_certification_expiration = lambda **kwargs: due
        strict = module.require_oracle_live_continuous_runtime_certification_renewal_eligible(
            repository_root=root,
            checked_at=checked_at,
            expiration_age_seconds=100.0,
            renewal_warning_seconds=20.0,
        )
        assert strict.status == "renewal_eligible"

    print("[PASS] OLA-086 Oracle Live Continuous Runtime Certification Renewal Eligibility Gate")


if __name__ == "__main__":
    main()
'''


def require_actual_ola085_contract() -> None:
    path = ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition" / "oracle_live_continuous_runtime_certification_expiration_gate.py"
    if not path.is_file():
        raise RuntimeError(f"Missing required OLA-085 production module: {path}")
    text = path.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OLA-085"',
        'class OracleLiveContinuousRuntimeCertificationExpirationStatus:',
        'def evaluate_oracle_live_continuous_runtime_certification_expiration(',
        'def verify_status_hash(',
        'DEFAULT_EXPIRATION_AGE_SECONDS',
        'DEFAULT_RENEWAL_WARNING_SECONDS',
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError("Actual OLA-085 contract mismatch; missing: " + ", ".join(missing))


def write_full_replacement(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    print(f"[OK] FULL REPLACEMENT: {path}")


def main() -> None:
    print("========================================")
    print(" OLA-086 INSTALLER")
    print(" CERTIFICATION RENEWAL ELIGIBILITY GATE")
    print(" READ-ONLY HASH-VERIFIED DECISION STATUS")
    print("========================================")
    require_actual_ola085_contract()
    print("[OK] Actual OLA-085 expiration contract verified")
    write_full_replacement(PRODUCTION_PATH, PRODUCTION_SOURCE)
    write_full_replacement(TEST_PATH, TEST_SOURCE)
    py_compile.compile(str(PRODUCTION_PATH), doraise=True)
    py_compile.compile(str(TEST_PATH), doraise=True)
    print("[OK] OLA-086 production and test syntax verified")
    completed = subprocess.run([sys.executable, str(TEST_PATH)], cwd=str(ROOT), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print("[OK] OLA-086 test executed successfully")
    print("[DONE] OLA-086 certification renewal eligibility gate installed")


if __name__ == "__main__":
    main()
