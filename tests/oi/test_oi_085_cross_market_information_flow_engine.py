from qseries_v2.oracle_intelligence.cross_market_information_flow_engine import CrossMarketInformationFlowEngine


def test_oi_085_cross_market_information_flow_engine():
    engine = CrossMarketInformationFlowEngine()

    propagation = {
        "results": [
            {
                "ticker": "COIN",
                "lagging": False,
                "information_edge_score": 35,
                "reaction_lag_minutes": 2,
                "reason_codes": ["reaction_in_line"],
            },
            {
                "ticker": "MSTR",
                "lagging": True,
                "information_edge_score": 90,
                "reaction_lag_minutes": 12,
                "reason_codes": ["expected_reaction_window_passed", "market_underreacted"],
            },
        ],
        "lagging_markets": [{"ticker": "MSTR"}],
    }

    causal_graph = {
        "links": [
            {"source_market": "BTC", "target_market": "COIN", "causal_confidence": 65},
            {"source_market": "BTC", "target_market": "MSTR", "causal_confidence": 88},
        ]
    }

    report = engine.build_flow_report(
        source_market="BTC",
        live_markets=[],
        elapsed_minutes=15,
        event_type="crypto_news",
        propagation_result=propagation,
        causal_graph=causal_graph,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["flow_count"] == 2
    assert report["flows"][0]["target_market"] == "MSTR"
    assert report["flows"][0]["priority"] in {"critical", "high"}
    assert report["summary"]["priority_count"] >= 1

    history = engine.flow_history()
    assert history["count"] == 1

    status = engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-085 Cross-Market Information Flow Engine")
    print({"summary": report["summary"], "top": report["flows"][0]})


if __name__ == "__main__":
    test_oi_085_cross_market_information_flow_engine()
