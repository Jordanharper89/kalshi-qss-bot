from qseries_v2.oracle_intelligence.runtime_recovery_bridge import RuntimeRecoveryBridge


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
        }

    def start_runtime(self):
        self.running = True
        return {
            "status": "ok",
            "read_only": True,
            "runtime": self.status(),
        }

    def run_once(self, markets=None):
        self.cycles += 1
        return {
            "status": "ok",
            "read_only": True,
            "result": {
                "cycle": self.cycles,
                "markets": len(markets or []),
            },
        }


class FakeRecoveryManager:
    def __init__(self):
        self.logged = []

    def status(self):
        return {"status": "ok"}

    def recovery_plan(self):
        return {
            "status": "ok",
            "read_only": True,
            "restorable": True,
            "recovery_plan": {
                "recommended_action": "resume_with_validation",
                "safe_to_resume": True,
                "warnings": ["last_event_not_clean_shutdown"],
                "steps": ["Run validation cycle."],
            },
        }

    def recover_summary(self):
        return {
            "status": "ok",
            "read_only": True,
            "recommended_action": "resume_with_validation",
            "warnings": ["last_event_not_clean_shutdown"],
        }

    def log_recovery_attempt(self, success, details=None):
        event = {
            "status": "ok",
            "read_only": True,
            "event_type": "runtime_recovery_attempt",
            "success": success,
            "details": details or {},
        }
        self.logged.append(event)
        return event


def test_oi_072_runtime_recovery_bridge():
    center = FakeCommandCenter()
    recovery = FakeRecoveryManager()
    bridge = RuntimeRecoveryBridge(center, recovery)

    check = bridge.startup_check()
    assert check["status"] == "ok"
    assert check["startup_action"] == "resume_with_validation"
    assert check["safe_to_resume"] is True

    result = bridge.recover_and_start(
        validation_cycle=True,
        markets=[{"ticker": "RECOVERY-TEST"}],
    )

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["startup_action"] == "resume_with_validation"
    assert result["validation"]["status"] == "ok"
    assert result["recovery_event"]["event_type"] == "runtime_recovery_attempt"

    last = bridge.last_recovery()
    assert last["last_recovery"]["status"] == "ok"

    summary = bridge.recovery_summary()
    assert summary["status"] == "ok"
    assert summary["command_center"]["runtime_status"] == "running"

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["has_last_recovery"] is True

    print("[PASS] OI-072 Runtime Recovery Bridge")
    print({
        "startup_action": result["startup_action"],
        "validation_cycle": result["validation"]["result"]["cycle"],
        "warnings": check["warnings"],
    })


if __name__ == "__main__":
    test_oi_072_runtime_recovery_bridge()
