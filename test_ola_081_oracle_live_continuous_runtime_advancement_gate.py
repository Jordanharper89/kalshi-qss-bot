from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_continuous_runtime_advancement_gate import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleLiveContinuousRuntimeAdvancementRecord,
    default_process_is_alive,
    evaluate_oracle_live_continuous_runtime_advancement,
)


ROOT = Path(__file__).resolve().parent


def main() -> int:
    print("========================================")
    print(" OLA-081 CORRECTION V3")
    print(" REPOSITORY-ALIGNED LIVE ADVANCEMENT")
    print(" OLA-068 POSTGRESQL PASSIVE MONITOR")
    print("========================================")

    assert SCHEMA_VERSION == "OLA-081"
    assert ENGINE_ID == "OLA-081"

    print(
        "[TEST] Platform process-liveness contract"
    )

    assert default_process_is_alive(
        os.getpid()
    ) is True

    assert default_process_is_alive(
        0
    ) is False

    assert default_process_is_alive(
        -1
    ) is False

    assert default_process_is_alive(
        True
    ) is False

    if os.name == "nt":
        print(
            "[PASS] Windows OpenProcess/GetExitCodeProcess "
            "contract active"
        )
    else:
        print(
            "[PASS] POSIX signal-zero contract active"
        )

    print(
        "[TEST] Validate active OLA-074 runtime lock"
    )
    print(
        "[TEST] Observe canonical OLA-068 PostgreSQL advancement"
    )
    print(
        "[INFO] Observation window: 30 seconds"
    )
    print(
        "[INFO] Runtime state/log changes are supporting evidence"
    )
    print(
        "[INFO] PostgreSQL persistence is canonical advancement"
    )
    print(
        "[INFO] Live Oracle process will not be restarted"
    )

    record = (
        evaluate_oracle_live_continuous_runtime_advancement(
            repository_root=ROOT,
            checked_at=datetime.now(
                timezone.utc
            ),
            observation_window_seconds=30.0,
        )
    )

    assert isinstance(
        record,
        OracleLiveContinuousRuntimeAdvancementRecord,
    )

    assert record.schema_version == "OLA-081"
    assert record.engine_id == "OLA-081"
    assert record.gate_status == "passed"

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
        record.upstream_monitor_schema_version
        == "OLA-068"
    )

    assert record.observation_count_delta > 0
    assert record.latest_sequence_delta > 0

    assert (
        record.postgresql_persistence_advanced
        is True
    )

    assert record.runtime_advancing is True
    assert record.process_remained_alive is True

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
    assert record.qseries_handoff_allowed is False
    assert record.trade_authorization_allowed is False
    assert record.order_placement_allowed is False
    assert record.funds_moved is False
    assert record.portfolio_mutated is False

    assert record.verify_record_hash() is True

    print(
        "[PASS] Active OLA-074 runtime lock verified"
    )
    print(
        f"[PASS] Live Oracle process verified: "
        f"{record.process_id}"
    )
    print(
        f"[PASS] PostgreSQL observations increased by "
        f"{record.observation_count_delta}"
    )
    print(
        f"[PASS] Canonical sequence increased by "
        f"{record.latest_sequence_delta}"
    )

    if record.latest_persisted_at_advanced:
        print(
            "[PASS] Latest persisted timestamp advanced"
        )

    if record.persistence_terminal_sequence_delta > 0:
        print(
            "[PASS] Persistence terminal sequence advanced"
        )

    if record.runtime_log_advanced:
        print(
            "[PASS] Runtime log also advanced"
        )
    else:
        print(
            "[INFO] Runtime log did not need to change "
            "for canonical PASS"
        )

    if record.active_state_advanced:
        print(
            "[PASS] Runtime state file also advanced"
        )
    else:
        print(
            "[INFO] Runtime state file did not need to change "
            "for canonical PASS"
        )

    print(
        "[PASS] OLA-068 passive observation contract preserved"
    )
    print(
        "[PASS] Live Oracle process remained active"
    )
    print(
        "[PASS] OLA-081 evidence record hash verified"
    )
    print(
        "[PASS] Oracle remained read-only"
    )
    print(
        "[PASS] Execution, orders, funds, and "
        "portfolio mutation remained disabled"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
