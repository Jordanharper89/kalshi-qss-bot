
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_contract import (
    LiquidityDiscoveryOpportunity,
    LiquidityDiscoveryResult,
    assert_liquidity_contract_read_only,
    empty_liquidity_discovery_result,
)


def test_liquidity_discovery_contract_empty_result():
    result = empty_liquidity_discovery_result()

    assert result.schema_version == "LQD-001"
    assert result.engine_id == "oracle.discovery.liquidity.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_liquidity_contract_read_only(result) is True


def test_liquidity_discovery_contract_opportunity_hash():
    opportunity = LiquidityDiscoveryOpportunity(
        opportunity_id="liq-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="liquidity_gap",
        direction="thin_liquidity",
        confidence=0.7,
        magnitude=0.4,
        explanation="Test liquidity gap opportunity.",
        evidence={"spread": 0.08, "depth": 100},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "liq-test-001"


def test_liquidity_discovery_contract_result_count():
    opportunity = LiquidityDiscoveryOpportunity(
        opportunity_id="liq-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="liquidity_gap",
        direction="thin_liquidity",
        confidence=0.7,
        magnitude=0.4,
        explanation="Test liquidity gap opportunity.",
        evidence={"spread": 0.08, "depth": 100},
    )

    result = LiquidityDiscoveryResult(
        schema_version="LQD-001",
        engine_id="oracle.discovery.liquidity.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_liquidity_contract_read_only(result) is True


if __name__ == "__main__":
    test_liquidity_discovery_contract_empty_result()
    test_liquidity_discovery_contract_opportunity_hash()
    test_liquidity_discovery_contract_result_count()

    result = empty_liquidity_discovery_result()

    print("[PASS] LQD-001 Liquidity Discovery Contract")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
