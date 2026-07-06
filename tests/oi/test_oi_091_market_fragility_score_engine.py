from qseries_v2.oracle_intelligence.market_fragility_score_engine import market_fragility_score_engine


def test_oi_091_market_fragility_score_engine():
    influence_graph = {
        "nodes": [
            {"market": "NASDAQ", "outgoing_influence": 62, "incoming_influence": 86, "net_influence": -24, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "outgoing_influence": 35, "incoming_influence": 75, "net_influence": -40, "bridge_score": 54, "role": "sink"},
        ]
    }

    transition_graph = {
        "nodes": [
            {"market": "NASDAQ", "regime": "contagion", "transition_pressure": 72, "instability_score": 76},
            {"market": "AI-SECTOR", "regime": "stress", "transition_pressure": 78, "instability_score": 70},
        ]
    }

    contagion_report = {
        "market_scores": [
            {"market": "NASDAQ", "contagion_source_score": 77, "vulnerability_score": 83, "systemic_importance_score": 75, "risk_role": "systemic_contagion_hub"},
            {"market": "AI-SECTOR", "contagion_source_score": 50, "vulnerability_score": 72, "systemic_importance_score": 63, "risk_role": "vulnerable_sink"},
        ]
    }

    severity_ranking = {
        "rankings": [
            {"item_type": "market", "label": "NASDAQ", "severity_score": 82},
            {"item_type": "market", "label": "AI-SECTOR", "severity_score": 70},
        ]
    }

    report = market_fragility_score_engine.score_fragility(
        influence_graph,
        transition_graph,
        contagion_report,
        severity_ranking,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 2
    assert report["highest_fragility"] is not None
    assert report["top_fragile_markets"][0]["fragility_score"] >= report["top_fragile_markets"][-1]["fragility_score"]
    assert report["fragility_counts"]

    diag = market_fragility_score_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-091 Market Fragility Score Engine")
    print({
        "markets": report["market_count"],
        "highest": report["highest_fragility"],
        "counts": report["fragility_counts"],
    })


if __name__ == "__main__":
    test_oi_091_market_fragility_score_engine()
