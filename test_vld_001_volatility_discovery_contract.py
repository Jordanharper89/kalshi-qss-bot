
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_contract import (
    VolatilityDiscoveryOpportunity,
    VolatilityDiscoveryResult,
    assert_volatility_contract_read_only,
    empty_volatility_discovery_result,
)


def test_volatility_discovery_contract_empty_result():
    result = empty_volatility_discovery_result()

    assert result.schema_version == "VLD-001"
    assert result.engine_id == "oracle.discovery.volatility.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_volatility_contract_read_only(result) is True


def test_volatility_discovery_contract_opportunity_hash():
    opportunity = VolatilityDiscoveryOpportunity(
        opportunity_id="vol-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="volatility_regime_shift",
        regime="expanding",
        confidence=0.75,
        magnitude=0.42,
        explanation="Test volatility regime shift opportunity.",
        evidence={"realized_volatility": 0.31, "baseline_volatility": 0.18},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "vol-test-001"


def test_volatility_discovery_contract_result_count():
    opportunity = VolatilityDiscoveryOpportunity(
        opportunity_id="vol-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="volatility_regime_shift",
        regime="expanding",
        confidence=0.75,
        magnitude=0.42,
        explanation="Test volatility regime shift opportunity.",
        evidence={"realized_volatility": 0.31, "baseline_volatility": 0.18},
    )

    result = VolatilityDiscoveryResult(
        schema_version="VLD-001",
        engine_id="oracle.discovery.volatility.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_volatility_contract_read_only(result) is True


if __name__ == "__main__":
    test_volatility_discovery_contract_empty_result()
    test_volatility_discovery_contract_opportunity_hash()
    test_volatility_discovery_contract_result_count()

    result = empty_volatility_discovery_result()

    print("[PASS] VLD-001 Volatility Discovery Contract")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
