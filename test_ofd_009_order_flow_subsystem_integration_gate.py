
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_subsystem_integration_gate import (
    OrderFlowSubsystemIntegrationGate,
    run_order_flow_subsystem_integration_gate,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 85,
        "ask_size": 15,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2500,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXTEST-NO",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 15,
        "ask_size": 85,
        "bid_price": 0.55,
        "ask_price": 0.58,
        "last_price": 0.56,
        "volume": 2100,
        "open_interest": 6500,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_order_flow_subsystem_integration_gate_accepts_full_chain():
    gate = OrderFlowSubsystemIntegrationGate()
    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name="order_flow.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    assert result.schema_version == "OFD-009"
    assert result.engine_id == "oracle.discovery.order_flow.subsystem_integration_gate"
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count == 2
    assert result.integration_hash
    assert all(result.checks.values())
    assert result.audit["subsystem"] == "order_flow_discovery"
    assert result.audit["ledger_validation"]["accepted"] is True


def test_order_flow_subsystem_integration_gate_is_replayable_and_order_independent():
    r1 = run_order_flow_subsystem_integration_gate(
        RAW,
        source_name="order_flow.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_order_flow_subsystem_integration_gate(
        list(reversed(RAW)),
        source_name="order_flow.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.integration_hash == r2.integration_hash
    assert r1.discovery_result_hash == r2.discovery_result_hash
    assert r1.pipeline_hash == r2.pipeline_hash
    assert r1.replay_ledger_hash == r2.replay_ledger_hash


def test_order_flow_subsystem_integration_gate_accepts_empty_chain():
    result = run_order_flow_subsystem_integration_gate(
        [],
        source_name="order_flow.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow", "fold": "empty"},
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values())


def test_order_flow_subsystem_integration_gate_rejects_execution_context():
    result = run_order_flow_subsystem_integration_gate(
        RAW,
        source_name="order_flow.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["oos_accepted"] is False
    assert result.read_only is True


if __name__ == "__main__":
    test_order_flow_subsystem_integration_gate_accepts_full_chain()
    test_order_flow_subsystem_integration_gate_is_replayable_and_order_independent()
    test_order_flow_subsystem_integration_gate_accepts_empty_chain()
    test_order_flow_subsystem_integration_gate_rejects_execution_context()

    result = run_order_flow_subsystem_integration_gate(
        [],
        source_name="order_flow.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    print("[PASS] OFD-009 Order Flow Subsystem Integration Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
