from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_spot_source_adapter import (
    CryptoSpotSourceAdapter,
)


def test_cdm_002_crypto_spot_source_adapter():
    raw_records = [
        {
            "symbol": "ETH/USD",
            "exchange": "coinbase",
            "price": 3500,
            "model_price": 3575,
            "bid": 3499,
            "ask": 3501,
            "volume_24h": 1000000,
            "liquidity": 500000,
            "volatility": 0.04,
            "status": "active",
        },
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
    ]

    adapter = CryptoSpotSourceAdapter(source_name="coinbase_snapshot")
    caps = adapter.capabilities()
    health = adapter.health()

    batch_1 = adapter.normalize_batch(raw_records)
    batch_2 = adapter.normalize_batch(list(reversed(raw_records)))

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "CDM-002"
    assert batch_1.adapter_id == "oracle.discovery.source.crypto_spot"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    symbols_1 = [s.symbol for s in batch_1.snapshots]
    symbols_2 = [s.symbol for s in batch_2.snapshots]
    assert symbols_1 == symbols_2
    assert symbols_1 == ["BTC-USD", "ETH-USD"]

    first = batch_1.snapshots[0]
    assert first.symbol == "BTC-USD"
    assert first.base_asset == "BTC"
    assert first.quote_asset == "USD"
    assert first.exchange == "coinbase"
    assert first.price == 65000.0
    assert first.fair_value == 67000.0
    assert first.spread == 20.0
    assert first.volume_24h == 5000000.0
    assert first.liquidity == 2500000.0
    assert first.read_only is True
    assert first.metadata["source_name"] == "coinbase_snapshot"

    try:
        first.metadata["new"] = "mutation"
        raise AssertionError("snapshot metadata should be immutable")
    except TypeError:
        pass

    d = batch_1.to_dict()
    assert d["schema_version"] == "CDM-002"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2
    assert d["telemetry"]["read_only"] is True

    print("[PASS] CDM-002 Crypto Spot Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "symbols": symbols_1,
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_cdm_002_crypto_spot_source_adapter()
