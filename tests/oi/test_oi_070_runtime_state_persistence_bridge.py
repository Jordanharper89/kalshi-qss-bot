from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_runtime_state_store import OracleRuntimeStateStore
from qseries_v2.oracle_intelligence.runtime_state_persistence_bridge import RuntimeStatePersistenceBridge


class FakeCommandCenter:
    def __init__(self):
        self.running = False
        self.cycles = 0

    def status(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime_status": "running" if self.running else "stopped",
            "health": "healthy",
            "cycles": self.cycles,
            "metrics": {"errors": 0},
        }

    def dashboard(self):
        return {
            "status": "ok",
            "read_only": True,
            "runtime": self.status(),
            "last_cycle": {"cycle": self.cycles, "status": "ok"},
        }

    def start_runtime(self):
        self.running = True
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def stop_runtime(self):
        self.running = False
        return {"status": "ok", "read_only": True, "runtime": self.status()}

    def run_once(self, markets=None, **kwargs):
        self.running = True
        self.cycles += 1
        return {
            "status": "ok",
            "read_only": True,
            "result": {"cycle": self.cycles, "markets": len(markets or [])},
        }


def test_oi_070_runtime_state_persistence_bridge():
    test_db = Path("qseries_v2") / "data" / "test_runtime_state_bridge.sqlite3"

    if test_db.exists():
        test_db.unlink()

    store = OracleRuntimeStateStore(test_db)
    center = FakeCommandCenter()
    bridge = RuntimeStatePersistenceBridge(center, store)

    started = bridge.start_and_log()
    assert started["status"] == "ok"
    assert started["event"]["event_type"] == "runtime_started"

    run = bridge.run_once_and_persist(markets=[{"ticker": "STATE-TEST"}])
    assert run["status"] == "ok"
    assert run["event"]["event_type"] == "runtime_cycle_completed"

    full = bridge.persist_full_state()
    assert full["status"] == "ok"

    restore = bridge.restore_summary()
    assert restore["status"] == "ok"
    assert restore["restorable"] is True

    stopped = bridge.stop_and_log()
    assert stopped["status"] == "ok"
    assert stopped["event"]["event_type"] == "runtime_stopped"

    store_status = store.status()
    assert store_status["snapshots"] >= 4
    assert store_status["events"] >= 4

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-070 Runtime State Persistence Bridge")
    print({
        "snapshots": store_status["snapshots"],
        "events": store_status["events"],
        "restorable": restore["restorable"],
    })


if __name__ == "__main__":
    test_oi_070_runtime_state_persistence_bridge()
