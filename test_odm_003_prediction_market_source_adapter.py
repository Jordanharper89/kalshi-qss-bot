from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_source_adapter import (
    PredictionMarketSourceAdapter,
)


def test_odm_003_prediction_market_source_adapter():
    raw_markets = [
        {
            "ticker": "KX.Z",
            "question": "Will Z happen?",
            "platform": "kalshi",
            "category": "macro",
            "price": 42,
            "model_probability": 55,
            "liquidity": 2500,
            "volume": 9000,
            "status": "open",
        },
        {
            "ticker": "KX.A",
            "question": "Will A happen?",
            "platform": "kalshi",
            "category": "macro",
            "price": 71,
            "model_probability": 61,
            "liquidity": 3000,
            "volume": 12000,
            "status": "open",
        },
    ]

    adapter = PredictionMarketSourceAdapter(source_name="kalshi_snapshot")
    caps = adapter.capabilities()
    health = adapter.health()
    batch_1 = adapter.normalize_batch(raw_markets)
    batch_2 = adapter.normalize_batch(list(reversed(raw_markets)))

    assert caps["read_only"] is True
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert batch_1.schema_version == "ODM-003"
    assert batch_1.adapter_id == "oracle.discovery.source.prediction_market"
    assert batch_1.read_only is True
    assert len(batch_1.snapshots) == 2

    ids_1 = [s.market_id for s in batch_1.snapshots]
    ids_2 = [s.market_id for s in batch_2.snapshots]
    assert ids_1 == ids_2
    assert ids_1 == ["KX.A", "KX.Z"]

    first = batch_1.snapshots[0]
    assert first.yes_price == 0.71
    assert first.fair_probability == 0.61
    assert first.metadata["source_name"] == "kalshi_snapshot"

    report = adapter.discover(raw_markets, min_edge=0.02, min_liquidity=100)
    assert report.read_only is True
    assert report.status == "passed"
    assert len(report.opportunities) == 2

    sides = sorted([o.side for o in report.opportunities])
    assert sides == ["NO", "YES"]

    d = batch_1.to_dict()
    assert d["schema_version"] == "ODM-003"
    assert d["read_only"] is True
    assert d["telemetry"]["raw_records_seen"] == 2
    assert d["telemetry"]["snapshots_emitted"] == 2

    print("[PASS] ODM-003 Prediction Market Source Adapter")
    print(
        {
            "schema_version": d["schema_version"],
            "adapter_id": d["adapter_id"],
            "snapshots": len(d["snapshots"]),
            "read_only": d["read_only"],
            "discovered_opportunities": len(report.opportunities),
        }
    )


if __name__ == "__main__":
    test_odm_003_prediction_market_source_adapter()
