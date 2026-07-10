from qseries_v2.integration.oem_015_runtime_bootstrap_integration_gate import (
    GATE_ID,
    RuntimeBootstrapIntegrationGate,
    run_gate,
)


def test_oem_015_gate_runs():
    result = run_gate()

    assert result.gate_id == GATE_ID
    assert result.status == "pass"
    assert result.check_count == 5
    assert result.passed_count == 5
    assert result.failed_count == 0


def test_oem_015_all_checks_pass():
    result = run_gate()

    for check in result.checks:
        assert check["status"] == "pass"
        assert check["error"] is None


def test_oem_015_gate_is_read_only():
    gate = RuntimeBootstrapIntegrationGate()
    result = gate.run()

    assert gate.read_only is True
    assert result.telemetry["read_only"] is True


def test_oem_015_bootstrap_checkpoint_details():
    result = run_gate()

    detail_map = {check["check_id"]: check["details"] for check in result.checks}

    assert detail_map["registry_bridge"]["loaded_engines"] == 7
    assert detail_map["migrated_engine_aggregator_gate"]["total_predictions"] >= 7
    assert detail_map["runtime_bootstrap_manager"]["runtime_status"] == "ready"
    assert detail_map["duplicate_protection"]["second_duplicates"] == 7
    assert detail_map["registered_prediction_readiness"]["prediction_count"] >= 7


if __name__ == "__main__":
    test_oem_015_gate_runs()
    test_oem_015_all_checks_pass()
    test_oem_015_gate_is_read_only()
    test_oem_015_bootstrap_checkpoint_details()

    result = run_gate()

    print("[PASS] OEM-015 Runtime Bootstrap Integration Gate")
    print(
        {
            "gate_id": result.gate_id,
            "status": result.status,
            "check_count": result.check_count,
            "passed_count": result.passed_count,
            "failed_count": result.failed_count,
            "read_only": result.telemetry["read_only"],
        }
    )
