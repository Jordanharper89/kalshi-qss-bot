from qseries_v2.oracle_intelligence.arbitrage_discovery_model.cross_venue_arbitrage_source_adapter import (
    CrossVenueArbitrageSourceAdapter,
)


def test_adm_002_cross_venue_arbitrage_source_adapter():
    raw_records = [
        {
            "symbol": "BTC/USD",
            "exchange": "Kraken",
            "bid": 65100,
            "ask": 65120,
            "last": 65110,
            "taker_fee_bps": 10,
            "depth": 1500000,
            "volume": 4000000,
            "latency_ms": 80,
            "status": "active",
        },
        {
            "symbol": "BTC-USD",
            "venue": "Coinbase",
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

    adapter = CrossVenueArbitrageSourceAdapter(source_name="adm_002_test_feed")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_1 = adapter.normalize_batch(raw_records)
    batch_2 = adapter.normalize_batch(list(reversed(raw_records)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["order_allowed"] is False
    assert caps["route_allowed"] is False
    assert caps["leg_execution_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "ADM-002"
    assert batch_1.adapter_id == "oracle.discovery.source.cross_venue_arbitrage"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 3

    order_1 = [(s.symbol, s.venue) for s in batch_1.snapshots]
    order_2 = [(s.symbol, s.venue) for s in batch_2.snapshots]
    assert order_1 == order_2
    assert order_1 == [
        ("BTC-USD", "coinbase"),
        ("BTC-USD", "kraken"),
        ("ETH-USD", "coinbase"),
    ]

    first = batch_1.snapshots[0]
    assert first.symbol == "BTC-USD"
    assert first.base_asset == "BTC"
    assert first.quote_asset == "USD"
    assert first.venue == "coinbase"
    assert first.bid == 65000.0
    assert first.ask == 65020.0
    assert first.mid == 65010.0
    assert first.spread == 20.0
    assert first.fee_bps == 8.0
    assert first.liquidity == 2500000.0
    assert first.volume_24h == 5000000.0
    assert first.read_only is True
    assert first.metadata["source_name"] == "adm_002_test_feed"

    try:
        first.metadata["new"] = "mutation"
        raise AssertionError("snapshot metadata should be immutable")
    except TypeError:
        pass

    d = batch_1.to_dict()
    assert d["schema_version"] == "ADM-002"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 3
    assert d["telemetry"]["snapshots_emitted"] == 3
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False

    print("[PASS] ADM-002 Cross-Venue Arbitrage Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "order": order_1,
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_adm_002_cross_venue_arbitrage_source_adapter()
