from __future__ import annotations

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
