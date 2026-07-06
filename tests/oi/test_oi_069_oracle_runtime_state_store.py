from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_runtime_state_store import OracleRuntimeStateStore


def test_oi_069_oracle_runtime_state_store():
    test_db = Path("qseries_v2") / "data" / "test_oracle_runtime_state.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OracleRuntimeStateStore(test_db)

    snap = store.save_snapshot(
        snapshot_type="runtime_status",
        source_module="test_oi_069",
        payload={
            "status": "running",
            "health": "healthy",
            "metrics": {"cycles": 1},
        },
    )

    assert snap["status"] == "ok"
    assert snap["snapshot_type"] == "runtime_status"

    dash = store.save_snapshot(
        snapshot_type="command_center_dashboard",
        source_module="test_oi_069",
        payload={
            "runtime": {"status": "running"},
            "last_cycle": {"status": "ok"},
        },
    )

    assert dash["status"] == "ok"

    event = store.log_event(
        event_type="runtime_started",
        severity="info",
        source_module="test_oi_069",
        payload={"message": "runtime started"},
    )

    assert event["status"] == "ok"

    latest = store.latest_snapshot("runtime_status")
    assert latest is not None
    assert latest["payload"]["status"] == "running"

    events = store.list_events(event_type="runtime_started")
    assert len(events) == 1
    assert events[0]["severity"] == "info"

    restore = store.restore_runtime_summary()
    assert restore["status"] == "ok"
    assert restore["restorable"] is True
    assert restore["latest_runtime"] is not None
    assert restore["latest_dashboard"] is not None

    status = store.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["snapshots"] == 2
    assert status["events"] == 1

    print("[PASS] OI-069 Oracle Runtime State Store")
    print(status)


if __name__ == "__main__":
    test_oi_069_oracle_runtime_state_store()
