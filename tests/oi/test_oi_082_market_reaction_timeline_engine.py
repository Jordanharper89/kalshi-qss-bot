from qseries_v2.oracle_intelligence.market_reaction_timeline_engine import MarketReactionTimelineEngine


def test_oi_082_market_reaction_timeline_engine():
    engine = MarketReactionTimelineEngine()

    engine.record_reaction_sequence(
        catalyst_id="CPI-1",
        catalyst_type="macro_cpi",
        market_reactions=[
            {"ticker": "BTC", "market_type": "crypto", "reaction_time_minutes": 2, "reaction_strength": 6, "direction": "YES"},
            {"ticker": "NASDAQ", "market_type": "equities", "reaction_time_minutes": 8, "reaction_strength": 4, "direction": "YES"},
            {"ticker": "RATES", "market_type": "rates", "reaction_time_minutes": 14, "reaction_strength": 5, "direction": "NO"},
        ],
    )

    engine.record_reaction_sequence(
        catalyst_id="CPI-2",
        catalyst_type="macro_cpi",
        market_reactions=[
            {"ticker": "BTC2", "market_type": "crypto", "reaction_time_minutes": 3, "reaction_strength": 7, "direction": "YES"},
            {"ticker": "NASDAQ2", "market_type": "equities", "reaction_time_minutes": 9, "reaction_strength": 4.5, "direction": "YES"},
            {"ticker": "RATES2", "market_type": "rates", "reaction_time_minutes": 16, "reaction_strength": 5.5, "direction": "NO"},
        ],
    )

    model = engine.build_timeline_model("macro_cpi")
    assert model["status"] == "ok"
    assert model["read_only"] is True
    assert model["observation_count"] == 2
    assert model["summary"]["fastest_market"] == "crypto"
    assert model["summary"]["slowest_market"] == "rates"
    assert len(model["lead_lag_edges"]) >= 2

    current = engine.analyze_current_reaction(
        catalyst_type="macro_cpi",
        elapsed_minutes=20,
        current_markets=[
            {"ticker": "BTC-LIVE", "market_type": "crypto", "reaction_strength": 6},
            {"ticker": "RATES-LIVE", "market_type": "rates", "reaction_strength": 0.5},
        ],
    )

    assert current["status"] == "ok"
    assert current["markets_analyzed"] == 2
    assert current["catch_up_candidates"][0]["ticker"] == "RATES-LIVE"

    window = engine.expected_reaction_window("macro_cpi", "rates")
    assert window["status"] == "ok"
    assert window["expected_median_minute"] >= 14

    status = engine.status()
    assert status["status"] == "ok"
    assert status["observations"] == 2

    print("[PASS] OI-082 Market Reaction Timeline Engine")
    print({
        "model_summary": model["summary"],
        "top_catch_up": current["summary"]["top_candidate"],
        "window": window,
    })


if __name__ == "__main__":
    test_oi_082_market_reaction_timeline_engine()
