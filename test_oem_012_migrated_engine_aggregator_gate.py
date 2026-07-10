from qseries_v2.integration.oem_012_migrated_engine_aggregator_gate import (
    GATE_ID,
    MigratedEngineAggregatorGate,
    run_gate,
)


def test_oem_012_gate_runs():
    result = run_gate()

    assert result.gate_id == GATE_ID
    assert result.status == "pass"
    assert result.engine_count == 7
    assert result.passed_count == 7
    assert result.failed_count == 0


def test_oem_012_predictions_are_aggregated():
    result = run_gate()

    assert result.total_signals >= 7
    assert result.total_predictions >= 7
    assert len(result.predictions) >= 7


def test_oem_012_all_engines_are_read_only():
    result = run_gate()

    for item in result.engine_results:
        assert item["status"] == "pass"
        assert item["read_only"] is True


def test_oem_012_gate_class_shape():
    gate = MigratedEngineAggregatorGate()
    result = gate.run()

    assert gate.read_only is True
    assert result.telemetry["read_only"] is True
    assert result.telemetry["aggregation_mode"] == "migrated_oem_engine_prediction_collection"


if __name__ == "__main__":
    test_oem_012_gate_runs()
    test_oem_012_predictions_are_aggregated()
    test_oem_012_all_engines_are_read_only()
    test_oem_012_gate_class_shape()

    result = run_gate()

    print("[PASS] OEM-012 Migrated Engine Aggregator Gate")
    print(
        {
            "gate_id": result.gate_id,
            "status": result.status,
            "engine_count": result.engine_count,
            "passed_count": result.passed_count,
            "failed_count": result.failed_count,
            "total_signals": result.total_signals,
            "total_predictions": result.total_predictions,
        }
    )
