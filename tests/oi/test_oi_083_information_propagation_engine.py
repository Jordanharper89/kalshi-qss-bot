from qseries_v2.oracle_intelligence.information_propagation_engine import InformationPropagationEngine


def test_oi_083_information_propagation_engine():
    engine = InformationPropagationEngine()

    engine.record_information_event(
        event_id="INFO-1",
        source_market="BTC",
        event_type="crypto_news",
        observations=[
            {"ticker": "BTC", "reaction_delay_minutes": 0, "reaction_strength": 8},
            {"ticker": "COIN", "reaction_delay_minutes": 9, "reaction_strength": 5},
            {"ticker": "MSTR", "reaction_delay_minutes": 12, "reaction_strength": 6},
        ],
    )

    engine.record_information_event(
        event_id="INFO-2",
        source_market="BTC",
        event_type="crypto_news",
        observations=[
            {"ticker": "BTC", "reaction_delay_minutes": 0, "reaction_strength": 7},
            {"ticker": "COIN", "reaction_delay_minutes": 8, "reaction_strength": 4.5},
            {"ticker": "MSTR", "reaction_delay_minutes": 13, "reaction_strength": 6.5},
        ],
    )

    model = engine.propagation_model("crypto_news")
    assert model["status"] == "ok"
    assert model["events_analyzed"] == 2
    assert model["summary"]["path_count"] == 2

    lag = engine.detect_lagging_markets(
        source_market="BTC",
        event_type="crypto_news",
        elapsed_minutes=15,
        live_markets=[
            {"ticker": "COIN", "reaction_strength": 4.7},
            {"ticker": "MSTR", "reaction_strength": 0.5},
        ],
    )

    assert lag["status"] == "ok"
    assert lag["lagging_markets"][0]["ticker"] == "MSTR"

    status = engine.status()
    assert status["status"] == "ok"
    assert status["events"] == 2

    print("[PASS] OI-083 Information Propagation Engine")
    print({"model": model["summary"], "lagging": lag["lagging_markets"]})


if __name__ == "__main__":
    test_oi_083_information_propagation_engine()
