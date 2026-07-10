
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_contract import (
    CorrelationDiscoveryOpportunity,
    CorrelationDiscoveryResult,
    assert_correlation_contract_read_only,
    empty_correlation_discovery_result,
)


def test_correlation_discovery_contract_empty_result():
    result = empty_correlation_discovery_result()

    assert result.schema_version == "CRD-001"
    assert result.engine_id == "oracle.discovery.correlation.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_correlation_contract_read_only(result) is True


def test_correlation_discovery_contract_opportunity_hash():
    opportunity = CorrelationDiscoveryOpportunity(
        opportunity_id="corr-test-001",
        primary_market_id="KXTEST-A",
        related_market_id="KXTEST-B",
        venue="kalshi",
        signal_type="correlation_break",
        relationship="positive_correlation_breakdown",
        confidence=0.72,
        magnitude=0.41,
        explanation="Test correlation breakdown opportunity.",
        evidence={"correlation": 0.82, "recent_correlation": 0.21},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "corr-test-001"


def test_correlation_discovery_contract_result_count():
    opportunity = CorrelationDiscoveryOpportunity(
        opportunity_id="corr-test-001",
        primary_market_id="KXTEST-A",
        related_market_id="KXTEST-B",
        venue="kalshi",
        signal_type="correlation_break",
        relationship="positive_correlation_breakdown",
        confidence=0.72,
        magnitude=0.41,
        explanation="Test correlation breakdown opportunity.",
        evidence={"correlation": 0.82, "recent_correlation": 0.21},
    )

    result = CorrelationDiscoveryResult(
        schema_version="CRD-001",
        engine_id="oracle.discovery.correlation.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_correlation_contract_read_only(result) is True


if __name__ == "__main__":
    test_correlation_discovery_contract_empty_result()
    test_correlation_discovery_contract_opportunity_hash()
    test_correlation_discovery_contract_result_count()

    result = empty_correlation_discovery_result()

    print("[PASS] CRD-001 Correlation Discovery Contract")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
