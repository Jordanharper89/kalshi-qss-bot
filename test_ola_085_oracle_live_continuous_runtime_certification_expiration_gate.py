from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
MODULE_PATH = (
    ROOT / "qseries_v2" / "oracle_intelligence" / "live_acquisition"
    / "oracle_live_continuous_runtime_certification_expiration_gate.py"
)


def load_module():
    name = "ola085_test_target"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def make_upstream(module, checked_at, age_seconds):
    upstream_module = __import__(
        "qseries_v2.oracle_intelligence.live_acquisition."
        "oracle_live_continuous_runtime_current_certification_status_gate",
        fromlist=["OracleLiveContinuousRuntimeCurrentCertificationStatus"],
    )
    cls = upstream_module.OracleLiveContinuousRuntimeCurrentCertificationStatus
    published_at = checked_at - timedelta(seconds=age_seconds)
    values = {
        "schema_version": "OLA-084", "engine_id": "OLA-084",
        "status": "certified_current", "certified": True,
        "certification_fresh": True, "checked_at": checked_at,
        "certification_published_at": published_at,
        "certification_age_seconds": float(age_seconds),
        "maximum_certification_age_seconds": module.UPSTREAM_VALIDATION_MAXIMUM_AGE_SECONDS,
        "attestation_id": "attestation-test", "attestation_hash": "a" * 64,
        "process_id": 1234, "runtime_mode": "continuous_live_shadow",
        "launcher": "run_oracle_live_shadow_CONTINUOUS_GUARDED.py",
        "upstream_attestation_schema_version": "OLA-083",
        "upstream_certification_schema_version": "OLA-082",
        "upstream_advancement_schema_version": "OLA-081",
        "upstream_monitor_schema_version": "OLA-068",
        "upstream_runtime_schema_version": "OLA-074",
        "checkpoint_count": 3, "total_observation_count_delta": 15,
        "total_latest_sequence_delta": 15,
        "total_persistence_terminal_sequence_delta": 0,
        "current_file": "runtime/oracle_live_shadow/certifications/ola083/current.json",
        "immutable_evidence_file": "runtime/oracle_live_shadow/certifications/ola083/evidence/test.json",
        "current_hash_verified": True, "immutable_hash_verified": True,
        "current_matches_immutable": True, "lineage_verified": True,
        "safety_boundary_verified": True, "read_only": True,
        "execution_allowed": False, "alerts_allowed": False,
        "qseries_handoff_allowed": False, "trade_authorization_allowed": False,
        "order_placement_allowed": False, "funds_moved": False,
        "portfolio_mutated": False, "postgresql_read_performed": False,
        "postgresql_write_performed": False, "runtime_started": False,
        "runtime_stopped": False, "runtime_restarted": False,
        "runtime_imported": False, "runtime_invoked": False,
        "runtime_lock_mutated": False, "files_written": False,
    }
    return cls(**values, status_hash=upstream_module.stable_hash(values))


def run_case(module, root, checked_at, age, expected):
    upstream = make_upstream(module, checked_at, age)
    module.evaluate_oracle_live_continuous_runtime_current_certification_status = (
        lambda **kwargs: upstream
    )
    result = module.evaluate_oracle_live_continuous_runtime_certification_expiration(
        repository_root=root,
        checked_at=checked_at,
        expiration_age_seconds=100.0,
        renewal_warning_seconds=20.0,
    )
    assert result.status == expected
    assert result.verify_status_hash() is True
    assert result.read_only is True
    assert result.postgresql_read_performed is False
    assert result.postgresql_write_performed is False
    assert result.runtime_invoked is False
    assert result.files_written is False
    return result


def main():
    module = load_module()
    checked_at = datetime(2026, 7, 19, 18, 0, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        current = run_case(module, root, checked_at, 10.0, "certified_current")
        assert current.usable is True and current.renewal_required is False
        due = run_case(module, root, checked_at, 85.0, "renewal_due")
        assert due.usable is True and due.renewal_required is True
        expired = run_case(module, root, checked_at, 101.0, "expired")
        assert expired.usable is False and expired.expired is True
        try:
            module.require_oracle_live_continuous_runtime_certification_unexpired(
                repository_root=root,
                checked_at=checked_at,
                expiration_age_seconds=100.0,
                renewal_warning_seconds=20.0,
            )
        except module.OracleLiveContinuousRuntimeCertificationExpired:
            pass
        else:
            raise AssertionError("strict gate did not reject expired certification")
        try:
            module.evaluate_oracle_live_continuous_runtime_certification_expiration(
                repository_root=root,
                checked_at=checked_at,
                expiration_age_seconds=100.0,
                renewal_warning_seconds=100.0,
            )
        except module.OracleLiveContinuousRuntimeCertificationExpirationContractError:
            pass
        else:
            raise AssertionError("invalid policy was accepted")
    print("[PASS] OLA-085 Oracle Live Continuous Runtime Certification Expiration Gate")


if __name__ == "__main__":
    main()
