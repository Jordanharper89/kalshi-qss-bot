from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_subsystem_integration_gate import (
    CryptoSpotDiscoverySubsystemIntegrationGate,
)


def test_cdm_009_crypto_spot_discovery_subsystem_integration_gate():
    gate = CryptoSpotDiscoverySubsystemIntegrationGate(
        source_name="cdm_009_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["swap_allowed"] is False
    assert caps["order_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "CDM-009"
    assert report.gate_id == "oracle.discovery.gate.crypto_spot_subsystem_integration"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.checks["contract_schema_ok"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["pipeline_gate_schema_ok"] is True
    assert report.checks["registry_bridge_schema_ok"] is True
    assert report.checks["pipeline_bridge_schema_ok"] is True
    assert report.checks["oos_gate_schema_ok"] is True
    assert report.checks["replay_ledger_schema_ok"] is True

    assert report.checks["opportunities_emitted"] is True
    assert report.checks["registry_records_emitted"] is True
    assert report.checks["pipeline_packets_emitted"] is True
    assert report.checks["oos_packets_emitted"] is True
    assert report.checks["replay_entries_emitted"] is True

    assert report.checks["execution_not_allowed"] is True
    assert report.checks["swap_not_allowed"] is True
    assert report.checks["order_not_allowed"] is True
    assert report.checks["deterministic_replay_fingerprint"] is True
    assert report.checks["immutable_registry_payload"] is True
    assert report.checks["immutable_pipeline_payload"] is True
    assert report.checks["immutable_replay_summary"] is True
    assert report.checks["read_only_telemetry_all"] is True

    d = report.to_dict()
    assert d["schema_version"] == "CDM-009"
    assert d["status"] == "passed"
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["registry_records_emitted"] == 2
    assert d["telemetry"]["pipeline_packets_emitted"] == 2
    assert d["telemetry"]["oos_packets_emitted"] == 2
    assert d["telemetry"]["replay_entries_emitted"] == 2
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["swap_allowed"] is False
    assert d["telemetry"]["order_allowed"] is False
    assert d["telemetry"]["replay_match"] is True
    assert d["read_only"] is True

    print("[PASS] CDM-009 Crypto Spot Discovery Subsystem Integration Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "opportunities": d["telemetry"]["opportunities_emitted"],
            "packets": d["telemetry"]["pipeline_packets_emitted"],
            "replay_match": d["telemetry"]["replay_match"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_cdm_009_crypto_spot_discovery_subsystem_integration_gate()
