from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_certification_attestation import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeCertificationAttestation,
    load_and_verify_attestation_file,
    publish_oracle_live_continuous_runtime_certification_attestation,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-083")
    print(" DURABLE RUNTIME CERTIFICATION")
    print(" IMMUTABLE + CURRENT ATTESTATION")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-083"
    assert ENGINE_ID == "OLA-083"

    print(
        "[TEST] Run canonical OLA-082 certification"
    )

    print(
        "[INFO] Two OLA-081 checkpoints"
    )

    print(
        "[INFO] 30 seconds per checkpoint"
    )

    print(
        "[INFO] Existing OLA-074 runtime only"
    )

    print(
        "[INFO] Oracle will not be restarted"
    )

    record = (
        publish_oracle_live_continuous_runtime_certification_attestation(
            repository_root=ROOT,
            checked_at=datetime.now(
                timezone.utc
            ),
            checkpoint_count=2,
            observation_window_seconds=30.0,
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeCertificationAttestation,
    )

    assert record.schema_version == "OLA-083"
    assert record.engine_id == "OLA-083"

    assert (
        record.attestation_status
        == "certified"
    )

    assert record.attestation_id.startswith(
        "ola083-"
    )

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

    assert record.checkpoint_count == 2

    assert (
        record.total_observation_count_delta
        > 0
    )

    assert (
        record.total_latest_sequence_delta
        > 0
    )

    assert (
        record.all_checkpoints_advanced
        is True
    )

    assert (
        record.same_process_all_checkpoints
        is True
    )

    assert (
        record.process_remained_alive
        is True
    )

    assert (
        record.existing_runtime_observed_only
        is True
    )

    assert (
        record.acquisition_cycle_invoked
        is False
    )

    assert record.scheduler_invoked is False
    assert record.runner_invoked is False

    assert record.read_only is True
    assert record.execution_allowed is False
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
    assert record.portfolio_mutated is False

    assert (
        record.postgresql_write_performed
        is False
    )

    assert record.runtime_started is False
    assert record.runtime_stopped is False
    assert record.runtime_restarted is False

    assert (
        record.runtime_lock_mutated
        is False
    )

    assert (
        record.verify_attestation_hash()
        is True
    )

    evidence_path = (
        ROOT
        / record.evidence_file
    )

    current_path = (
        ROOT
        / record.current_file
    )

    assert evidence_path.is_file()
    assert current_path.is_file()

    assert evidence_path != current_path

    evidence_payload = (
        load_and_verify_attestation_file(
            evidence_path
        )
    )

    current_payload = (
        load_and_verify_attestation_file(
            current_path
        )
    )

    assert (
        evidence_payload
        == current_payload
    )

    assert (
        evidence_payload[
            "attestation_id"
        ]
        == record.attestation_id
    )

    assert (
        evidence_payload[
            "attestation_hash"
        ]
        == record.attestation_hash
    )

    parsed_current = json.loads(
        current_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        parsed_current[
            "schema_version"
        ]
        == "OLA-083"
    )

    print(
        f"[PASS] Same live process certified: "
        f"{record.process_id}"
    )

    print(
        f"[PASS] PostgreSQL observations increased by "
        f"{record.total_observation_count_delta}"
    )

    print(
        f"[PASS] Canonical sequence increased by "
        f"{record.total_latest_sequence_delta}"
    )

    print(
        f"[PASS] Immutable evidence: "
        f"{record.evidence_file}"
    )

    print(
        f"[PASS] Current certification: "
        f"{record.current_file}"
    )

    print(
        "[PASS] Attestation hash verified"
    )

    print(
        "[PASS] Immutable and current evidence match"
    )

    print(
        "[PASS] Existing runtime observed only"
    )

    print(
        "[PASS] No runtime or lock mutation"
    )

    print(
        "[PASS] No PostgreSQL writes by OLA-083"
    )

    print(
        "[PASS] Oracle remained read-only"
    )

    print(
        "[PASS] OLA-083 durable runtime "
        "certification attestation"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
