from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_oos_runtime_gate import (
    PredictionMarketDiscoveryOOSRuntimeGate,
)


def test_odm_007_prediction_market_discovery_oos_runtime_gate():
    gate = PredictionMarketDiscoveryOOSRuntimeGate(
        source_name="odm_007_test_source",
        min_edge=0.02,
        min_liquidity=100,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "ODM-007"
    assert report.gate_id == "oracle.discovery.gate.prediction_market_oos_runtime"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True
    assert len(report.packets) == 2

    assert report.checks["gate_is_read_only"] is True
    assert report.checks["pipeline_bridge_is_read_only"] is True
    assert report.checks["deterministic_replay"] is True
    assert report.checks["all_packets_validation_required"] is True
    assert report.checks["all_packets_ranking_required"] is True
    assert report.checks["all_packets_registry_required"] is True
    assert report.checks["execution_not_allowed"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "ODM-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] ODM-007 Prediction Market Discovery OOS Runtime Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "packets": len(d["packets"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_odm_007_prediction_market_discovery_oos_runtime_gate()
