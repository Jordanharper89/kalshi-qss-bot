from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_runtime_state_store import OracleRuntimeStateStore
from qseries_v2.oracle_intelligence.runtime_recovery_manager import RuntimeRecoveryManager


def test_oi_071_runtime_recovery_manager():
    test_db = Path("qseries_v2") / "data" / "test_runtime_recovery.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OracleRuntimeStateStore(test_db)
    manager = RuntimeRecoveryManager(store)

    cold = manager.recovery_plan()
    assert cold["status"] == "ok"
    assert cold["read_only"] is True
    assert cold["recovery_plan"]["recommended_action"] == "cold_start"

    store.save_snapshot(
        snapshot_type="runtime_status",
        source_module="test_oi_071",
        payload={
            "runtime_status": "running",
            "health": "healthy",
            "cycles": 5,
            "metrics": {"errors": 0},
        },
    )

    store.save_snapshot(
        snapshot_type="command_center_dashboard",
        source_module="test_oi_071",
        payload={
            "last_cycle": {"cycle": 5, "status": "ok"},
        },
    )

    store.log_event(
        event_type="runtime_cycle_completed",
        severity="info",
        source_module="test_oi_071",
        payload={"cycle": 5},
    )

    plan = manager.recovery_plan()
    assert plan["status"] == "ok"
    assert plan["restorable"] is True
    assert plan["recovery_plan"]["safe_to_resume"] is True

    summary = manager.recover_summary()
    assert summary["status"] == "ok"
    assert summary["health"] == "healthy"
    assert summary["cycles"] == 5

    event = manager.log_recovery_attempt(True, {"mode": "test"})
    assert event["status"] == "ok"
    assert event["event_type"] == "runtime_recovery_attempt"

    status = manager.status()
    assert status["status"] == "ok"

    print("[PASS] OI-071 Runtime Recovery Manager")
    print({
        "recommended_action": plan["recovery_plan"]["recommended_action"],
        "warnings": plan["recovery_plan"]["warnings"],
        "summary": summary,
    })


if __name__ == "__main__":
    test_oi_071_runtime_recovery_manager()
