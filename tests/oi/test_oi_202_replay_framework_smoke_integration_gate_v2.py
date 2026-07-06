from qseries_v2.oracle_intelligence.replay_framework_smoke_integration_gate_v2 import (
    ENGINE_ID,
    ReplayFrameworkSmokeIntegrationGateV2,
    run_replay_framework_smoke_integration_gate_v2,
)


def test_replay_framework_smoke_gate_v2_passes():
    result = ReplayFrameworkSmokeIntegrationGateV2().run()

    assert result.engine_id == ENGINE_ID
    assert result.passed is True
    assert result.status == "passed"
    assert len(result.checks) >= 10
    assert all(check.status == "pass" for check in result.checks)
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True
    assert "OI-201" in result.telemetry["validated_modules"]


def test_wrapper_returns_gate_result():
    result = run_replay_framework_smoke_integration_gate_v2()

    assert result.passed is True
    assert result.telemetry["gate_type"] == "smoke_integration"
    assert result.telemetry["canonical_flow"] == "ranking -> analytics -> intelligence -> certification"


if __name__ == "__main__":
    test_replay_framework_smoke_gate_v2_passes()
    test_wrapper_returns_gate_result()
    print("[PASS] OI-202 Replay Framework Smoke Integration Gate V2")
    print(run_replay_framework_smoke_integration_gate_v2().to_dict())
