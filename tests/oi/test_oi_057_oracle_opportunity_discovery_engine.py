from qseries_v2.oracle_intelligence.oracle_opportunity_discovery_engine import oracle_opportunity_discovery_engine


def test_oi_057_oracle_opportunity_discovery_engine():
    markets = [
        {
            "ticker": "OPP-STRONG",
            "price": 52,
            "volume": 50000,
            "previous_volume": 10000,
            "liquidity": 40000,
            "spread": 1,
            "momentum": 9,
            "volatility": 6,
            "time_to_expiration_minutes": 45,
            "category": "crypto",
            "regime": "trend",
            "pattern_name": "breakout",
            "historical_similarity_count": 40,
            "cross_market_divergence": 0.82,
        },
        {
            "ticker": "OPP-WEAK",
            "price": 92,
            "volume": 500,
            "previous_volume": 450,
            "liquidity": 700,
            "spread": 14,
            "momentum": 1,
            "volatility": 1,
            "time_to_expiration_minutes": 3000,
            "category": "weather",
        },
    ]

    result = oracle_opportunity_discovery_engine.discover(markets, limit=2)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["markets_scanned"] == 2
    assert result["opportunities_found"] == 2
    assert result["top_opportunities"][0]["ticker"] == "OPP-STRONG"
    assert result["top_opportunities"][0]["opportunity_score"] > result["top_opportunities"][1]["opportunity_score"]
    assert result["top_opportunities"][0]["priority"] in {"critical", "high", "medium"}
    assert "rapid_volume_acceleration" in result["top_opportunities"][0]["reason_codes"]

    scored = oracle_opportunity_discovery_engine.score_market(markets[0])
    assert scored["read_only"] is True
    assert scored["suggested_analysis_depth"] in {
        "full_oracle_consensus",
        "standard_oracle_research",
        "light_watch_report",
        "no_deep_analysis",
    }

    status = oracle_opportunity_discovery_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-057 Oracle Opportunity Discovery Engine")
    print({
        "top": result["top_opportunities"][0]["ticker"],
        "score": result["top_opportunities"][0]["opportunity_score"],
        "priority": result["top_opportunities"][0]["priority"],
        "reasons": result["top_opportunities"][0]["reason_codes"],
    })


if __name__ == "__main__":
    test_oi_057_oracle_opportunity_discovery_engine()
