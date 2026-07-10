from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_oos_runtime_gate import (
    SolanaLaunchDiscoveryOOSRuntimeGate,
)


def test_sld_007_solana_launch_discovery_oos_runtime_gate():
    gate = SolanaLaunchDiscoveryOOSRuntimeGate(
        source_name="sld_007_test_source",
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["snipe_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "SLD-007"
    assert report.gate_id == "oracle.discovery.gate.solana_launch_oos_runtime"
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
    assert report.checks["signing_not_allowed"] is True
    assert report.checks["fund_movement_not_allowed"] is True
    assert report.checks["swap_not_allowed"] is True
    assert report.checks["snipe_not_allowed"] is True
    assert report.checks["solana_launch_market_shape"] is True
    assert report.checks["source_engine_id_solana_launch"] is True
    assert report.checks["immutable_packet_payload"] is True

    first = report.packets[0]
    assert first.payload["validation_required"] is True
    assert first.payload["ranking_required"] is True
    assert first.payload["registry_required"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["signing_allowed"] is False
    assert first.payload["fund_movement_allowed"] is False
    assert first.payload["swap_allowed"] is False
    assert first.payload["snipe_allowed"] is False
    assert first.payload["read_only"] is True
    assert first.audit["oracle_read_only"] is True
    assert first.audit["handoff_target"] == "OOS Opportunity Pipeline"

    d = report.to_dict()
    assert d["schema_version"] == "SLD-007"
    assert d["status"] == "passed"
    assert d["telemetry"]["packets_seen"] == 2
    assert d["telemetry"]["oos_validation_ready"] is True
    assert d["telemetry"]["oos_registry_ready"] is True
    assert d["telemetry"]["oos_ranking_ready"] is True
    assert d["telemetry"]["oos_pipeline_ready"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False
    assert d["telemetry"]["fund_movement_allowed"] is False
    assert d["telemetry"]["swap_allowed"] is False
    assert d["telemetry"]["snipe_allowed"] is False

    print("[PASS] SLD-007 Solana Launch Discovery OOS Runtime Gate")
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
    test_sld_007_solana_launch_discovery_oos_runtime_gate()
