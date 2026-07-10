from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_pipeline_gate import (
    PredictionMarketDiscoveryPipelineGate,
)


def test_odm_004_prediction_market_discovery_pipeline_gate():
    gate = PredictionMarketDiscoveryPipelineGate(
        source_name="odm_004_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "ODM-004"
    assert report.gate_id == "oracle.discovery.gate.prediction_market_pipeline"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.passed_checks >= 20
    assert report.checks["gate_is_read_only"] is True
    assert report.checks["adapter_is_read_only"] is True
    assert report.checks["adapter_deterministic_order"] is True
    assert report.checks["engine_replay_deterministic"] is True
    assert report.checks["universal_market_shape"] is True
    assert report.checks["immutable_market_output"] is True
    assert report.checks["no_execution_fields"] is True

    d = report.to_dict()
    assert d["schema_version"] == "ODM-004"
    assert d["status"] == "passed"
    assert d["telemetry"]["raw_records_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["deterministic_replay"] is True

    print("[PASS] ODM-004 Prediction Market Discovery Pipeline Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "opportunities": d["telemetry"]["opportunities_emitted"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_odm_004_prediction_market_discovery_pipeline_gate()
