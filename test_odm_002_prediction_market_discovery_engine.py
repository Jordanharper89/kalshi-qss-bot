from qseries_v2.oracle_intelligence.oracle_discovery_model.prediction_market_discovery_engine import (
    PredictionMarketDiscoveryEngine,
)


def test_odm_002_prediction_market_discovery_engine():
    markets = [
        {
            "market_id": "KX.TEST.YES",
            "title": "Will test market resolve yes?",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.41,
            "fair_probability": 0.52,
            "liquidity": 1500,
            "volume": 20000,
            "status": "open",
        },
        {
            "market_id": "KX.TEST.NO",
            "title": "Will second test market resolve yes?",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.74,
            "fair_probability": 0.63,
            "liquidity": 1300,
            "volume": 15000,
            "status": "open",
        },
        {
            "market_id": "KX.TEST.REJECT",
            "title": "Rejected low edge market",
            "platform": "kalshi",
            "category": "test",
            "yes_price": 0.50,
            "fair_probability": 0.505,
            "liquidity": 1300,
            "status": "open",
        },
    ]

    engine = PredictionMarketDiscoveryEngine(source_snapshots=markets, min_edge=0.02, min_liquidity=100)
    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover()
    report_2 = engine.discover()

    assert caps["read_only"] is True
    assert caps["deterministic"] is True
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_1.schema_version == "ODM-002"
    assert report_1.engine_id == "oracle.discovery.prediction_market"
    assert report_1.read_only is True
    assert report_1.status == "passed"
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.universal_market["market_type"] == "prediction_market"
    assert first.universal_market["read_only"] is True
    assert first.opportunity_type == "prediction_market_value"
    assert first.source_engine_id == "oracle.discovery.prediction_market"
    assert first.status == "discovered"
    assert abs(first.edge) >= 0.02
    assert first.confidence > 0
    assert "rules" in first.explanation

    sides = sorted([o.side for o in report_1.opportunities])
    assert sides == ["NO", "YES"]

    d = report_1.to_dict()
    assert d["schema_version"] == "ODM-002"
    assert d["read_only"] is True
    assert d["telemetry"]["markets_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["markets_rejected"] == 1

    try:
        first.universal_market["read_only"] = False
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    print("[PASS] ODM-002 Prediction Market Discovery Engine")
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
    test_odm_002_prediction_market_discovery_engine()
