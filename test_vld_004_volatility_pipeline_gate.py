
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_engine import (
    discover_volatility_opportunities,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_gate import (
    VolatilityPipelineGate,
    validate_volatility_discovery_result,
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
    }
]


def test_volatility_pipeline_gate_accepts_valid_result():
    result = discover_volatility_opportunities(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = VolatilityPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "VLD-004"
    assert gated.engine_id == "oracle.discovery.volatility.pipeline_gate"
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert gated.discovery_result_hash == result.result_hash
    assert gated.opportunity_count == result.opportunity_count
    assert gated.gate_hash
    assert all(gated.checks.values())


def test_volatility_pipeline_gate_accepts_empty_valid_result():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_volatility_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert all(gated.checks.values())


def test_volatility_pipeline_gate_is_replayable():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated1 = validate_volatility_discovery_result(result)
    gated2 = validate_volatility_discovery_result(result)

    assert gated1.gate_hash == gated2.gate_hash


if __name__ == "__main__":
    test_volatility_pipeline_gate_accepts_valid_result()
    test_volatility_pipeline_gate_accepts_empty_valid_result()
    test_volatility_pipeline_gate_is_replayable()

    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_volatility_discovery_result(result)

    print("[PASS] VLD-004 Volatility Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "read_only": gated.read_only,
        }
    )
