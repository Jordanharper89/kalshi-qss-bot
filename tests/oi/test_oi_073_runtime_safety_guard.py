from qseries_v2.oracle_intelligence.runtime_safety_guard import runtime_safety_guard


def test_oi_073_runtime_safety_guard():
    safe = runtime_safety_guard.validate_command(
        "run_once",
        {"markets": [{"ticker": "SAFE-TEST"}]},
    )

    assert safe["status"] == "ok"
    assert safe["allowed"] is True
    assert safe["decision"] == "allow"

    bad_command = runtime_safety_guard.validate_command(
        "execute_trade",
        {"ticker": "BAD-TEST"},
    )

    assert bad_command["status"] == "blocked"
    assert bad_command["allowed"] is False
    assert bad_command["decision"] == "block"

    bad_output = runtime_safety_guard.validate_runtime_output({
        "status": "ok",
        "api": {"execution_enabled": True},
        "signals": {"actionable": True},
    })

    assert bad_output["status"] == "blocked"
    assert bad_output["allowed"] is False
    assert len(bad_output["violations"]) >= 2

    guarded = runtime_safety_guard.guarded_command_result(
        command="dashboard",
        payload={},
        result={
            "status": "ok",
            "read_only": True,
            "api": {"execution_enabled": False},
            "signals": {"actionable": False},
        },
    )

    assert guarded["status"] == "ok"
    assert guarded["allowed"] is True
    assert guarded["result"] is not None

    status = runtime_safety_guard.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-073 Runtime Safety Guard")
    print({
        "safe_allowed": safe["allowed"],
        "bad_command": bad_command["decision"],
        "bad_output_violations": len(bad_output["violations"]),
    })


if __name__ == "__main__":
    test_oi_073_runtime_safety_guard()
