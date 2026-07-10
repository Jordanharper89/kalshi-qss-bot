
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_subsystem_integration_gate import (
    LiquiditySubsystemIntegrationGate,
    run_liquidity_subsystem_integration_gate,
)


RAW = [
    {
        "market_id": "KXTHIN",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.40,
        "ask_price": 0.48,
        "bid_depth": 100,
        "ask_depth": 50,
        "volume_24h": 12000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXDEEP",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.49,
        "ask_price": 0.50,
        "bid_depth": 5000,
        "ask_depth": 5200,
        "volume_24h": 50000,
        "open_interest": 100000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_liquidity_subsystem_integration_gate_accepts_full_chain():
    gate = LiquiditySubsystemIntegrationGate()
    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name="liquidity.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    assert result.schema_version == "LQD-009"
    assert result.engine_id == "oracle.discovery.liquidity.subsystem_integration_gate"
    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 2
    assert result.integration_hash
    assert all(result.checks.values()), result.checks
    assert result.audit["subsystem"] == "liquidity_discovery"
    assert result.audit["ledger_validation"]["accepted"] is True


def test_liquidity_subsystem_integration_gate_is_replayable_and_order_independent():
    r1 = run_liquidity_subsystem_integration_gate(
        RAW,
        source_name="liquidity.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_liquidity_subsystem_integration_gate(
        list(reversed(RAW)),
        source_name="liquidity.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.integration_hash == r2.integration_hash
    assert r1.discovery_result_hash == r2.discovery_result_hash
    assert r1.pipeline_hash == r2.pipeline_hash
    assert r1.replay_ledger_hash == r2.replay_ledger_hash


def test_liquidity_subsystem_integration_gate_accepts_empty_chain():
    result = run_liquidity_subsystem_integration_gate(
        [],
        source_name="liquidity.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow", "fold": "empty"},
    )

    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values()), result.checks


def test_liquidity_subsystem_integration_gate_rejects_execution_context():
    result = run_liquidity_subsystem_integration_gate(
        RAW,
        source_name="liquidity.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["oos_accepted"] is False
    assert result.read_only is True


if __name__ == "__main__":
    test_liquidity_subsystem_integration_gate_accepts_full_chain()
    test_liquidity_subsystem_integration_gate_is_replayable_and_order_independent()
    test_liquidity_subsystem_integration_gate_accepts_empty_chain()
    test_liquidity_subsystem_integration_gate_rejects_execution_context()

    result = run_liquidity_subsystem_integration_gate(
        [],
        source_name="liquidity.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    print("[PASS] LQD-009 Liquidity Subsystem Integration Gate")
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
