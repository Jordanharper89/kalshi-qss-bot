
from qseries_v2.oracle_intelligence.social_intelligence_discovery_model.social_intelligence_subsystem_integration_gate import (
    SocialIntelligenceSubsystemIntegrationGate,
)


def test_sid_009_social_intelligence_subsystem_integration_gate():
    gate = SocialIntelligenceSubsystemIntegrationGate(source_name="sid_009_test_source", min_social_score=0.55)

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["position_sizing_allowed"] is False
    assert caps["broker_connectivity_allowed"] is False
    assert caps["posting_allowed"] is False
    assert caps["dm_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "SID-009"
    assert report.gate_id == "oracle.discovery.gate.social_intelligence_subsystem_integration"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.checks["contract_schema_ok"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["engine_runtime_schema_ok"] is True
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
    assert report.checks["posting_not_allowed"] is True
    assert report.checks["dm_not_allowed"] is True
    assert report.checks["deterministic_replay_fingerprint"] is True
    assert report.checks["immutable_registry_payload"] is True
    assert report.checks["immutable_pipeline_payload"] is True
    assert report.checks["immutable_replay_summary"] is True
    assert report.checks["read_only_telemetry_all"] is True

    d = report.to_dict()
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["registry_records_emitted"] == 2
    assert d["telemetry"]["pipeline_packets_emitted"] == 2
    assert d["telemetry"]["oos_packets_emitted"] == 2
    assert d["telemetry"]["replay_entries_emitted"] == 2
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["posting_allowed"] is False
    assert d["telemetry"]["dm_allowed"] is False
    assert d["telemetry"]["replay_match"] is True

    print("[PASS] SID-009 Social Intelligence Subsystem Integration Gate")
    print({
        "schema_version": d["schema_version"],
        "gate_id": d["gate_id"],
        "status": d["status"],
        "passed_checks": d["passed_checks"],
        "failed_checks": d["failed_checks"],
        "opportunities": d["telemetry"]["opportunities_emitted"],
        "packets": d["telemetry"]["pipeline_packets_emitted"],
        "replay_match": d["telemetry"]["replay_match"],
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_sid_009_social_intelligence_subsystem_integration_gate()
