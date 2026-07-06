from qseries_v2.oracle_intelligence.causal_market_inference_engine import CausalMarketInferenceEngine


def test_oi_084_causal_market_inference_engine():
    engine = CausalMarketInferenceEngine()

    for i in range(8):
        engine.record_causal_observation(
            source_market="BTC",
            target_market="COIN",
            source_move_time=i,
            target_move_time=i + 10,
            source_strength=5,
            target_strength=3.5,
            shared_catalyst="crypto_news",
        )

    engine.record_causal_observation(
        source_market="BTC",
        target_market="COIN",
        source_move_time=100,
        target_move_time=95,
        source_strength=4,
        target_strength=-2,
    )

    result = engine.infer_causal_link("BTC", "COIN")

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["observations"] == 9
    assert result["causal_confidence"] >= 70
    assert result["counterexamples"] == 1

    graph = engine.causal_graph()
    assert graph["status"] == "ok"
    assert graph["link_count"] == 1
    assert graph["strongest_link"]["pair_key"] == "BTC->COIN"

    status = engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-084 Causal Market Inference Engine")
    print({"link": result, "graph_count": graph["link_count"]})


if __name__ == "__main__":
    test_oi_084_causal_market_inference_engine()
