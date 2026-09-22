from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_current_certification_status_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeCurrentCertificationStatus,
    evaluate_oracle_live_continuous_runtime_current_certification_status,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-084")
    print(" CURRENT RUNTIME CERTIFICATION STATUS")
    print(" FAST HASH-VERIFIED OPERATOR GATE")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-084"
    assert ENGINE_ID == "OLA-084"

    print(
        "[TEST] Load OLA-083 current certification"
    )

    print(
        "[TEST] Verify immutable evidence match"
    )

    print(
        "[TEST] Verify certification freshness"
    )

    print(
        "[INFO] No 60-second recertification will run"
    )

    print(
        "[INFO] No PostgreSQL connection will be opened"
    )

    print(
        "[INFO] Oracle runtime will not be touched"
    )

    checked_at = datetime.now(
        timezone.utc
    )

    record = (
        evaluate_oracle_live_continuous_runtime_current_certification_status(
            repository_root=ROOT,
            checked_at=checked_at,
            maximum_certification_age_seconds=(
                24.0
                * 60.0
                * 60.0
            ),
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeCurrentCertificationStatus,
    )

    assert record.schema_version == "OLA-084"
    assert record.engine_id == "OLA-084"

    assert (
        record.status
        == "certified_current"
    )

    assert record.certified is True

    assert (
        record.certification_fresh
        is True
    )

    assert (
        record.certification_age_seconds
        >= 0.0
    )

    assert (
        record.certification_age_seconds
        <= record.maximum_certification_age_seconds
    )

    assert record.attestation_id.startswith(
        "ola083-"
    )

    assert record.attestation_hash

    assert record.process_id > 0

    assert (
        record.runtime_mode
        == "continuous_live_shadow"
    )

    assert (
        record.launcher
        == "run_oracle_live_shadow_"
        "CONTINUOUS_GUARDED.py"
    )

    assert (
        record.upstream_attestation_schema_version
        == "OLA-083"
    )

    assert (
        record.upstream_certification_schema_version
        == "OLA-082"
    )

    assert (
        record.upstream_advancement_schema_version
        == "OLA-081"
    )

    assert (
        record.upstream_monitor_schema_version
        == "OLA-068"
    )

    assert (
        record.upstream_runtime_schema_version
        == "OLA-074"
    )

    assert record.checkpoint_count >= 2

    assert (
        record.total_observation_count_delta
        > 0
    )

    assert (
        record.total_latest_sequence_delta
        > 0
    )

    assert (
        record.current_hash_verified
        is True
    )

    assert (
        record.immutable_hash_verified
        is True
    )

    assert (
        record.current_matches_immutable
        is True
    )

    assert (
        record.lineage_verified
        is True
    )

    assert (
        record.safety_boundary_verified
        is True
    )

    assert record.read_only is True

    assert (
        record.execution_allowed
        is False
    )

    assert record.alerts_allowed is False

    assert (
        record.qseries_handoff_allowed
        is False
    )

    assert (
        record.trade_authorization_allowed
        is False
    )

    assert (
        record.order_placement_allowed
        is False
    )

    assert record.funds_moved is False

    assert (
        record.portfolio_mutated
        is False
    )

    assert (
        record.postgresql_read_performed
        is False
    )

    assert (
        record.postgresql_write_performed
        is False
    )

    assert record.runtime_started is False
    assert record.runtime_stopped is False

    assert (
        record.runtime_restarted
        is False
    )

    assert (
        record.runtime_imported
        is False
    )

    assert (
        record.runtime_invoked
        is False
    )

    assert (
        record.runtime_lock_mutated
        is False
    )

    assert record.files_written is False

    assert (
        record.verify_status_hash()
        is True
    )

    print(
        "[PASS] Current certification is valid"
    )

    print(
        f"[PASS] Certified process: "
        f"{record.process_id}"
    )

    print(
        f"[PASS] Attestation: "
        f"{record.attestation_id}"
    )

    print(
        f"[PASS] Certification age: "
        f"{record.certification_age_seconds:.3f} seconds"
    )

    print(
        f"[PASS] Certified observation increase: "
        f"{record.total_observation_count_delta}"
    )

    print(
        f"[PASS] Certified sequence increase: "
        f"{record.total_latest_sequence_delta}"
    )

    print(
        f"[PASS] Current file: "
        f"{record.current_file}"
    )

    print(
        f"[PASS] Immutable evidence: "
        f"{record.immutable_evidence_file}"
    )

    print(
        "[PASS] Current attestation hash verified"
    )

    print(
        "[PASS] Immutable evidence hash verified"
    )

    print(
        "[PASS] Current and immutable evidence match"
    )

    print(
        "[PASS] OLA-074 through OLA-083 lineage verified"
    )

    print(
        "[PASS] Oracle safety boundary verified"
    )

    print(
        "[PASS] No PostgreSQL or runtime access performed"
    )

    print(
        "[PASS] OLA-084 current certification status gate"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
