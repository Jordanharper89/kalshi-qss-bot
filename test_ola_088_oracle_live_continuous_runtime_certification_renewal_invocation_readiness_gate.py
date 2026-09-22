from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
MODULE_PATH = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition"
    / "oracle_live_continuous_runtime_certification_renewal_invocation_readiness_gate.py"
)


def load_module():
    name = "ola088_test_target"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def make_upstream(checked_at, status):
    upstream_module = __import__(
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_live_continuous_runtime_certification_renewal_authorization_gate",
        fromlist=["OracleLiveContinuousRuntimeCertificationRenewalAuthorizationStatus"],
    )
    cls = upstream_module.OracleLiveContinuousRuntimeCertificationRenewalAuthorizationStatus
    mapping = {
        "renewal_not_permitted": (False, False, False, False, "", None, True, False, 10.0),
        "renewal_eligible_awaiting_authorization": (True, False, False, False, "", None, True, False, 85.0),
        "renewal_eligible_authorized": (True, False, True, True, "operator-test", checked_at - timedelta(seconds=1), True, False, 85.0),
        "renewal_required_awaiting_authorization": (True, True, False, False, "", None, False, True, 101.0),
        "renewal_required_authorized": (True, True, True, True, "operator-test", checked_at - timedelta(seconds=1), False, True, 101.0),
    }
    eligible, required, authorized, present, auth_id, authorized_at, usable, expired, age = mapping[status]
    values = {
        "schema_version": "OLA-087", "engine_id": "OLA-087", "status": status,
        "renewal_eligible": eligible, "renewal_required": required,
        "renewal_authorized": authorized, "operator_authorization_present": present,
        "operator_authorization_id": auth_id, "authorized_at": authorized_at,
        "checked_at": checked_at, "certification_usable": usable,
        "certification_expired": expired,
        "certification_published_at": checked_at - timedelta(seconds=age),
        "certification_age_seconds": age, "renewal_due_at_age_seconds": 80.0,
        "expiration_age_seconds": 100.0, "seconds_until_renewal_due": 80.0 - age,
        "seconds_until_expiration": 100.0 - age,
        "attestation_id": "attestation-test", "attestation_hash": "a" * 64,
        "upstream_renewal_status": "renewal_required" if required else ("renewal_eligible" if eligible else "renewal_not_due"),
        "upstream_renewal_status_hash": "b" * 64,
        "upstream_renewal_schema_version": "OLA-086",
        "upstream_expiration_schema_version": "OLA-085",
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
        "renewal_performed": False, "certification_evidence_mutated": False,
    }
    return cls(**values, status_hash=upstream_module.stable_hash(values))


def main():
    module = load_module()
    checked_at = datetime(2026, 7, 20, 2, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        cases = {
            "renewal_not_permitted": ("renewal_invocation_prohibited", False),
            "renewal_eligible_awaiting_authorization": ("renewal_eligible_invocation_blocked", False),
            "renewal_eligible_authorized": ("renewal_eligible_invocation_ready", True),
            "renewal_required_awaiting_authorization": ("renewal_required_invocation_blocked", False),
            "renewal_required_authorized": ("renewal_required_invocation_ready", True),
        }
        for upstream_status, (expected_status, expected_ready) in cases.items():
            upstream = make_upstream(checked_at, upstream_status)
            module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization = lambda _upstream=upstream, **kwargs: _upstream
            result = module.evaluate_oracle_live_continuous_runtime_certification_renewal_invocation_readiness(
                repository_root=root, checked_at=checked_at
            )
            assert result.status == expected_status
            assert result.renewal_invocation_ready is expected_ready
            assert result.verify_status_hash() is True
            assert result.renewal_performed is False
            assert result.renewal_executor_imported is False
            assert result.renewal_executor_invoked is False
            assert result.certification_evidence_mutated is False
            assert result.postgresql_read_performed is False
            assert result.runtime_invoked is False

        blocked = make_upstream(checked_at, "renewal_required_awaiting_authorization")
        module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization = lambda **kwargs: blocked
        try:
            module.require_oracle_live_continuous_runtime_certification_renewal_invocation_ready(
                repository_root=root, checked_at=checked_at
            )
        except module.OracleLiveContinuousRuntimeCertificationRenewalInvocationNotReady:
            pass
        else:
            raise AssertionError("blocked renewal invocation was accepted")

        ready = make_upstream(checked_at, "renewal_required_authorized")
        module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization = lambda **kwargs: ready
        accepted = module.require_oracle_live_continuous_runtime_certification_renewal_invocation_ready(
            repository_root=root, checked_at=checked_at
        )
        assert accepted.renewal_invocation_ready is True
        assert accepted.status == "renewal_required_invocation_ready"

    print("[PASS] OLA-088 Oracle Live Continuous Runtime Certification Renewal Invocation Readiness Gate")


if __name__ == "__main__":
    main()
