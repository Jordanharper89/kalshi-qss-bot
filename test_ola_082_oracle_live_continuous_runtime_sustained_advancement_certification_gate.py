from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_sustained_advancement_certification_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    evaluate_oracle_live_continuous_runtime_sustained_advancement,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-082")
    print(" SUSTAINED CONTINUOUS ADVANCEMENT")
    print(" TWO CONSECUTIVE OLA-081 CHECKPOINTS")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-082"
    assert ENGINE_ID == "OLA-082"

    print(
        "[TEST] Observe the active OLA-074 runtime only"
    )

    print(
        "[TEST] Require two consecutive "
        "OLA-081 advancement passes"
    )

    print(
        "[INFO] 30 seconds per checkpoint"
    )

    print(
        "[INFO] 60 seconds total canonical observation"
    )

    print(
        "[INFO] The live Oracle process "
        "will not be restarted"
    )

    record = (
        evaluate_oracle_live_continuous_runtime_sustained_advancement(
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
        OracleLiveContinuousRuntimeSustainedAdvancementRecord,
    )

    assert record.schema_version == "OLA-082"
    assert record.engine_id == "OLA-082"

    assert (
        record.certification_status
        == "certified"
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
        record.upstream_gate_schema_version
        == "OLA-081"
    )

    assert (
        record.upstream_monitor_schema_version
        == "OLA-068"
    )

    assert (
        record.upstream_lock_schema_version
        == "OLA-074"
    )

    assert record.checkpoint_count == 2

    assert (
        record.observation_window_seconds_per_checkpoint
        == 30.0
    )

    assert (
        record.total_observation_window_seconds
        == 60.0
    )

    assert (
        len(
            record.checkpoint_record_hashes
        )
        == 2
    )

    assert (
        len(
            set(
                record.checkpoint_record_hashes
            )
        )
        == 2
    )

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
        record.verify_record_hash()
        is True
    )

    print(
        f"[PASS] Same live process certified: "
        f"{record.process_id}"
    )

    print(
        f"[PASS] Consecutive advancement checkpoints: "
        f"{record.checkpoint_count}"
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
        "[PASS] OLA-081 record hashes verified"
    )

    print(
        "[PASS] OLA-068 passive monitoring preserved"
    )

    print(
        "[PASS] OLA-074 runtime identity remained stable"
    )

    print(
        "[PASS] Oracle remained read-only"
    )

    print(
        "[PASS] No execution, orders, funds, "
        "or portfolio mutation"
    )

    print(
        "[PASS] OLA-082 sustained continuous "
        "runtime certification"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
