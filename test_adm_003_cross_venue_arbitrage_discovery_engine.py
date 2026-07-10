from qseries_v2.oracle_intelligence.arbitrage_discovery_model.arbitrage_discovery_contract import (
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_discovery_engine import (
    CrossVenueArbitrageDiscoveryEngine,
)


def test_adm_003_cross_venue_arbitrage_discovery_engine():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "venue": "coinbase",
            "bid": 65000,
            "ask": 65020,
            "last_price": 65010,
            "fee_bps": 8,
            "liquidity": 2500000,
            "volume_24h": 5000000,
            "latency_ms": 40,
            "status": "active",
        },
        {
            "symbol": "BTC/USD",
            "exchange": "kraken",
            "bid": 65300,
            "ask": 65320,
            "last": 65310,
            "taker_fee_bps": 10,
            "depth": 1500000,
            "volume": 4000000,
            "latency_ms": 80,
            "status": "active",
        },
        {
            "pair": "ETH/USD",
            "venue": "coinbase",
            "best_bid": 3500,
            "best_ask": 3502,
            "price": 3501,
            "fee_bps": 8,
            "liquidity": 800000,
            "volume_24h": 2000000,
            "status": "active",
        },
    ]

    request = ArbitrageDiscoveryRequest(
        request_id="adm003.test.request",
        family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
        source_name="adm_003_test_feed",
        symbols=("BTC-USD", "ETH-USD"),
        venues=("coinbase", "kraken"),
        metadata={"raw_records": raw_records},
    )

    engine = CrossVenueArbitrageDiscoveryEngine(
        min_net_edge_percent=0.001,
        min_liquidity=1000,
    )

    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover(request)
    report_2 = engine.discover(request)

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.telemetry is True
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "ADM-001"
    assert report_1.engine_id == "oracle.discovery.cross_venue_arbitrage"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 1

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    opp = report_1.opportunities[0]
    assert opp.read_only is True
    assert opp.symbol == "BTC-USD"
    assert opp.opportunity_type == "cross_venue_arbitrage"
    assert opp.source_engine_id == "oracle.discovery.cross_venue_arbitrage"
    assert opp.buy_venue == "coinbase"
    assert opp.sell_venue == "kraken"
    assert opp.buy_price == 65020.0
    assert opp.sell_price == 65300.0
    assert opp.gross_edge > 0
    assert opp.net_edge_percent >= 0.001
    assert 0.0 <= opp.confidence <= 1.0
    assert opp.status == "discovered"
    assert opp.universal_market["market_type"] == "cross_venue_arbitrage"
    assert opp.universal_market["read_only"] is True
    assert opp.universal_market["execution_allowed"] is False
    assert opp.explanation["rules"]

    try:
        opp.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["pairs_evaluated"] == 2
    assert d["telemetry"]["opportunities_emitted"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] ADM-003 Cross-Venue Arbitrage Discovery Engine")
    print(
        {
            "schema_version": "ADM-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_003_cross_venue_arbitrage_discovery_engine()
