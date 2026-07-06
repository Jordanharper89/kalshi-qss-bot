
from qseries_v2.oracle_intelligence.market_resilience_engine import market_resilience_engine


def test_oi_092_market_resilience_engine():
    fragility_report = {
        "scores": [
            {"market": "NASDAQ", "fragility_score": 71.1},
            {"market": "AI-SECTOR", "fragility_score": 62.2},
            {"market": "FED-RATE", "fragility_score": 28.0},
        ]
    }

    transition_graph = {
        "nodes": [
            {"market": "NASDAQ", "regime": "contagion", "transition_pressure": 72, "instability_score": 76},
            {"market": "AI-SECTOR", "regime": "stress", "transition_pressure": 78, "instability_score": 70},
            {"market": "FED-RATE", "regime": "accumulation", "transition_pressure": 35, "instability_score": 25},
        ]
    }

    contagion_report = {
        "market_scores": [
            {"market": "NASDAQ", "vulnerability_score": 83, "contagion_source_score": 77, "systemic_importance_score": 75},
            {"market": "AI-SECTOR", "vulnerability_score": 72, "contagion_source_score": 50, "systemic_importance_score": 63},
            {"market": "FED-RATE", "vulnerability_score": 20, "contagion_source_score": 70, "systemic_importance_score": 52},
        ]
    }

    influence_graph = {
        "nodes": [
            {"market": "NASDAQ", "incoming_influence": 86, "outgoing_influence": 62, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "incoming_influence": 75, "outgoing_influence": 35, "bridge_score": 54, "role": "sink"},
            {"market": "FED-RATE", "incoming_influence": 5, "outgoing_influence": 90, "bridge_score": 12, "role": "dominant_source"},
        ]
    }

    report = market_resilience_engine.score_resilience(
        fragility_report,
        transition_graph,
        contagion_report,
        influence_graph,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 3
    assert report["highest_resilience"]["market"] == "FED-RATE"
    assert report["top_resilient_markets"][0]["resilience_score"] >= report["top_resilient_markets"][-1]["resilience_score"]
    assert report["recovery_tier_counts"]

    diag = market_resilience_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-092 Market Resilience Engine")
    print({
        "markets": report["market_count"],
        "highest": report["highest_resilience"],
        "tiers": report["recovery_tier_counts"],
    })


if __name__ == "__main__":
    test_oi_092_market_resilience_engine()
