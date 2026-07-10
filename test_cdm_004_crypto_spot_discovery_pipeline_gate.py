from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_pipeline_gate import (
    CryptoSpotDiscoveryPipelineGate,
)


def test_cdm_004_crypto_spot_discovery_pipeline_gate():
    gate = CryptoSpotDiscoveryPipelineGate(
        source_name="cdm_004_test_source",
        min_edge_percent=0.01,
        min_liquidity=1000,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "CDM-004"
    assert report.gate_id == "oracle.discovery.gate.crypto_spot_pipeline"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.passed_checks >= 20
    assert report.checks["gate_is_read_only"] is True
    assert report.checks["adapter_is_read_only"] is True
    assert report.checks["engine_is_read_only"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["adapter_deterministic_order"] is True
    assert report.checks["engine_replay_deterministic"] is True
    assert report.checks["universal_market_shape"] is True
    assert report.checks["source_engine_id_present"] is True
    assert report.checks["no_execution_fields"] is True
    assert report.checks["immutable_universal_market"] is True

    d = report.to_dict()
    assert d["schema_version"] == "CDM-004"
    assert d["status"] == "passed"
    assert d["telemetry"]["raw_records_seen"] == 3
    assert d["telemetry"]["snapshots_emitted"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["deterministic_replay"] is True

    print("[PASS] CDM-004 Crypto Spot Discovery Pipeline Gate")
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
    test_cdm_004_crypto_spot_discovery_pipeline_gate()
