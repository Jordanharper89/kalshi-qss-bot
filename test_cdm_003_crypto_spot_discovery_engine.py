from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_discovery_contract import (
    CryptoDiscoveryFamily,
    CryptoDiscoveryRequest,
)
from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_discovery_engine import (
    CryptoSpotDiscoveryEngine,
)


def test_cdm_003_crypto_spot_discovery_engine():
    raw_records = [
        {
            "symbol": "BTC-USD",
            "exchange": "coinbase",
            "price": 65000,
            "fair_value": 67000,
            "bid": 64990,
            "ask": 65010,
            "volume": 5000000,
            "depth": 2500000,
            "volatility_24h": 0.03,
            "status": "active",
        },
        {
            "symbol": "ETH/USD",
            "exchange": "coinbase",
            "price": 3500,
            "model_price": 3400,
            "bid": 3499,
            "ask": 3501,
            "volume_24h": 1000000,
            "liquidity": 500000,
            "volatility": 0.04,
            "status": "active",
        },
        {
            "symbol": "SOL-USD",
            "exchange": "coinbase",
            "price": 150,
            "fair_value": 151,
            "volume": 1000000,
            "depth": 500000,
            "status": "active",
        },
    ]

    request = CryptoDiscoveryRequest(
        request_id="cdm003.test.request",
        family=CryptoDiscoveryFamily.CRYPTO_SPOT,
        source_name="coinbase_snapshot",
        symbols=("BTC-USD", "ETH-USD", "SOL-USD"),
        metadata={"raw_records": raw_records},
    )

    engine = CryptoSpotDiscoveryEngine(min_edge_percent=0.01, min_liquidity=1000)
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

    assert report_1.schema_version == "CDM-001"
    assert report_1.engine_id == "oracle.discovery.crypto_spot"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    sides = sorted([o.side for o in report_1.opportunities])
    assert sides == ["LONG_SPOT_OBSERVATION", "SHORT_SPOT_OBSERVATION"]

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "crypto_spot_value"
    assert first.source_engine_id == "oracle.discovery.crypto_spot"
    assert first.status == "discovered"
    assert abs(first.edge_percent) >= 0.01
    assert 0.0 <= first.confidence <= 1.0
    assert first.universal_market["market_type"] == "crypto_spot"
    assert first.universal_market["read_only"] is True
    assert first.explanation["rules"]

    try:
        first.universal_market["read_only"] = False
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] CDM-003 Crypto Spot Discovery Engine")
    print(
        {
            "schema_version": "CDM-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_cdm_003_crypto_spot_discovery_engine()
