from qseries_v2.oracle_intelligence.arbitrage_discovery_model.arbitrage_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryRequest,
    EmptyArbitrageDiscoveryEngine,
)


def test_adm_001_arbitrage_discovery_contract():
    request = ArbitrageDiscoveryRequest(
        request_id="arbitrage.discovery.test.request",
        family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
        source_name="test_source",
        symbols=("btc-usd", "eth-usd"),
        venues=("Coinbase", "Kraken"),
        metadata={"records": [{"symbol": "BTC-USD", "venue": "coinbase"}]},
    )

    engine = EmptyArbitrageDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "ADM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.arbitrage"

    assert request.read_only is True
    assert request.symbols == ("BTC-USD", "ETH-USD")
    assert request.venues == ("coinbase", "kraken")
    assert request.family == ArbitrageDiscoveryFamily.CROSS_EXCHANGE

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "ADM-001"
    assert result.engine_id == "oracle.discovery.arbitrage.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.pairs_evaluated == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "ADM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] ADM-001 Arbitrage Discovery Contract")
    print(
        {
            "schema_version": d["schema_version"],
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_001_arbitrage_discovery_contract()
