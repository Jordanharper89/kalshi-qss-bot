
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_subsystem_integration_gate import (
    VolatilitySubsystemIntegrationGate,
    run_volatility_subsystem_integration_gate,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXVOL-CONTRACT",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.10,
        "implied_volatility": 0.24,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_subsystem_integration_gate_accepts_full_chain():
    gate = VolatilitySubsystemIntegrationGate()
    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    assert result.schema_version == "VLD-009"
    assert result.engine_id == "oracle.discovery.volatility.subsystem_integration_gate"
    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.integration_hash
    assert all(result.checks.values()), result.checks
    assert result.audit["subsystem"] == "volatility_discovery"
    assert result.audit["ledger_validation"]["accepted"] is True


def test_volatility_subsystem_integration_gate_is_replayable_and_order_independent():
    r1 = run_volatility_subsystem_integration_gate(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_volatility_subsystem_integration_gate(
        list(reversed(RAW)),
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.integration_hash == r2.integration_hash
    assert r1.discovery_result_hash == r2.discovery_result_hash
    assert r1.pipeline_hash == r2.pipeline_hash
    assert r1.replay_ledger_hash == r2.replay_ledger_hash


def test_volatility_subsystem_integration_gate_accepts_empty_chain():
    result = run_volatility_subsystem_integration_gate(
        [],
        source_name="volatility.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow", "fold": "empty"},
    )

    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values()), result.checks


def test_volatility_subsystem_integration_gate_rejects_execution_context():
    result = run_volatility_subsystem_integration_gate(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["oos_accepted"] is False
    assert result.read_only is True


if __name__ == "__main__":
    test_volatility_subsystem_integration_gate_accepts_full_chain()
    test_volatility_subsystem_integration_gate_is_replayable_and_order_independent()
    test_volatility_subsystem_integration_gate_accepts_empty_chain()
    test_volatility_subsystem_integration_gate_rejects_execution_context()

    result = run_volatility_subsystem_integration_gate(
        [],
        source_name="volatility.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    print("[PASS] VLD-009 Volatility Subsystem Integration Gate")
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
