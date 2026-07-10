from qseries_v2.integration.oem_010_oracle_engine_migration_integration_gate import (
    EXPECTED_ADAPTERS,
    GATE_ID,
    OracleEngineMigrationIntegrationGate,
    run_gate,
)


def test_oem_010_gate_runs():
    result = run_gate()

    assert result.gate_id == GATE_ID
    assert result.required_count == len(EXPECTED_ADAPTERS)
    assert result.status == "pass"
    assert result.failed_count == 0
    assert result.passed_count == len(EXPECTED_ADAPTERS)


def test_oem_010_all_required_adapters_are_read_only():
    result = run_gate()

    for check in result.checks:
        if check["status"] == "pass":
            assert check["read_only"] is True


def test_oem_010_all_required_adapters_emit_signals_and_predictions():
    result = run_gate()

    required_engine_ids = {spec["engine_id"] for spec in EXPECTED_ADAPTERS}
    checks = [check for check in result.checks if check["engine_id"] in required_engine_ids]

    assert len(checks) == len(EXPECTED_ADAPTERS)

    for check in checks:
        assert check["status"] == "pass"
        assert check["signal_count"] >= 1
        assert check["prediction_count"] >= 1


def test_oem_010_gate_class_shape():
    gate = OracleEngineMigrationIntegrationGate()
    result = gate.run()

    assert gate.read_only is True
    assert result.telemetry["read_only"] is True
    assert result.telemetry["expected_required_adapters"] == len(EXPECTED_ADAPTERS)


if __name__ == "__main__":
    test_oem_010_gate_runs()
    test_oem_010_all_required_adapters_are_read_only()
    test_oem_010_all_required_adapters_emit_signals_and_predictions()
    test_oem_010_gate_class_shape()

    result = run_gate()

    print("[PASS] OEM-010 Oracle Engine Migration Integration Gate")
    print(
        {
            "gate_id": result.gate_id,
            "status": result.status,
            "required_count": result.required_count,
            "passed_count": result.passed_count,
            "failed_count": result.failed_count,
            "optional_loaded_count": result.optional_loaded_count,
        }
    )
