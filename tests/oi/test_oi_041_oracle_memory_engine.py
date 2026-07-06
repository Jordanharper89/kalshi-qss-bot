from qseries_v2.oracle_intelligence.oracle_memory_engine import oracle_memory_engine


def test_oi_041_oracle_memory_engine():
    status = oracle_memory_engine.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    market = oracle_memory_engine.remember_market_snapshot({
        "ticker": "TEST-MARKET",
        "price": 42,
        "volume": 1000,
        "confidence": 72,
        "importance": 65,
    })

    assert market["memory_type"] == "market"
    assert market["market_ticker"] == "TEST-MARKET"

    pattern = oracle_memory_engine.remember_pattern({
        "ticker": "TEST-MARKET",
        "pattern_name": "late_reaction",
        "confidence": 81,
    })

    assert pattern["memory_type"] == "pattern"

    forecast = oracle_memory_engine.remember_forecast_result(
        {"ticker": "TEST-MARKET", "horizon": "30m", "forecast_value": 58, "confidence": 77},
        {"ticker": "TEST-MARKET", "actual_value": 61},
    )

    assert forecast["memory_type"] == "forecast"

    recalled = oracle_memory_engine.recall(market_ticker="TEST-MARKET")
    assert len(recalled) >= 3

    probe = oracle_memory_engine.similarity_probe({"ticker": "TEST-MARKET", "pattern": "late_reaction"})
    assert probe["match_count"] >= 1

    print("[PASS] OI-041 Oracle Memory Engine")
    print(oracle_memory_engine.status())


if __name__ == "__main__":
    test_oi_041_oracle_memory_engine()
