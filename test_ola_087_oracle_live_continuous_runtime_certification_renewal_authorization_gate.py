from __future__ import annotations

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
MODULE_PATH = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition"
    / "oracle_live_continuous_runtime_certification_renewal_authorization_gate.py"
)


def load_module():
    name = "ola087_test_target"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def make_upstream(checked_at, upstream_status):
    upstream_module = __import__(
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_live_continuous_runtime_certification_renewal_eligibility_gate",
        fromlist=["OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus"],
    )
    cls = upstream_module.OracleLiveContinuousRuntimeCertificationRenewalEligibilityStatus
    mapping = {
        "renewal_not_due": (False, False, True, False, 10.0, "certified_current"),
        "renewal_eligible": (True, False, True, False, 85.0, "renewal_due"),
        "renewal_required": (True, True, False, True, 101.0, "expired"),
    }
    eligible, required, usable, expired, age, expiration_status = mapping[upstream_status]
    values = {
        "schema_version": "OLA-086", "engine_id": "OLA-086",
        "status": upstream_status, "renewal_eligible": eligible,
        "renewal_required": required, "certification_usable": usable,
        "certification_expired": expired, "checked_at": checked_at,
        "certification_published_at": checked_at - timedelta(seconds=age),
        "certification_age_seconds": age, "renewal_due_at_age_seconds": 80.0,
        "expiration_age_seconds": 100.0, "seconds_until_renewal_due": 80.0 - age,
        "seconds_until_expiration": 100.0 - age,
        "attestation_id": "attestation-test", "attestation_hash": "a" * 64,
        "upstream_expiration_status": expiration_status,
        "upstream_expiration_status_hash": "b" * 64,
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
    checked_at = datetime(2026, 7, 20, 1, 0, tzinfo=timezone.utc)
    authorized_at = checked_at - timedelta(seconds=1)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        not_due = make_upstream(checked_at, "renewal_not_due")
        module.evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility = lambda **kwargs: not_due
        result = module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
            repository_root=root, checked_at=checked_at
        )
        assert result.status == "renewal_not_permitted"
        assert result.renewal_authorized is False
        try:
            module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
                repository_root=root, checked_at=checked_at, operator_authorized=True,
                operator_authorization_id="operator-test", authorized_at=authorized_at,
            )
        except module.OracleLiveContinuousRuntimeCertificationRenewalAuthorizationContractError:
            pass
        else:
            raise AssertionError("premature authorization was accepted")

        eligible = make_upstream(checked_at, "renewal_eligible")
        module.evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility = lambda **kwargs: eligible
        awaiting = module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
            repository_root=root, checked_at=checked_at
        )
        assert awaiting.status == "renewal_eligible_awaiting_authorization"
        assert awaiting.renewal_authorized is False
        authorized = module.require_oracle_live_continuous_runtime_certification_renewal_authorized(
            repository_root=root, checked_at=checked_at, operator_authorized=True,
            operator_authorization_id="operator-test", authorized_at=authorized_at,
        )
        assert authorized.status == "renewal_eligible_authorized"
        assert authorized.renewal_authorized is True
        assert authorized.verify_status_hash() is True

        required = make_upstream(checked_at, "renewal_required")
        module.evaluate_oracle_live_continuous_runtime_certification_renewal_eligibility = lambda **kwargs: required
        required_waiting = module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
            repository_root=root, checked_at=checked_at
        )
        assert required_waiting.status == "renewal_required_awaiting_authorization"
        required_authorized = module.require_oracle_live_continuous_runtime_certification_renewal_authorized(
            repository_root=root, checked_at=checked_at, operator_authorized=True,
            operator_authorization_id="operator-test", authorized_at=authorized_at,
        )
        assert required_authorized.status == "renewal_required_authorized"
        assert required_authorized.renewal_required is True
        assert required_authorized.renewal_performed is False
        assert required_authorized.certification_evidence_mutated is False
        assert required_authorized.postgresql_read_performed is False
        assert required_authorized.runtime_invoked is False

        try:
            module.evaluate_oracle_live_continuous_runtime_certification_renewal_authorization(
                repository_root=root, checked_at=checked_at, operator_authorized=True,
                operator_authorization_id="", authorized_at=authorized_at,
            )
        except module.OracleLiveContinuousRuntimeCertificationRenewalAuthorizationContractError:
            pass
        else:
            raise AssertionError("authorization without identity was accepted")

    print("[PASS] OLA-087 Oracle Live Continuous Runtime Certification Renewal Authorization Gate")


if __name__ == "__main__":
    main()
