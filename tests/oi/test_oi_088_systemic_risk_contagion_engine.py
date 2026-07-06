
from qseries_v2.oracle_intelligence.systemic_risk_contagion_engine import systemic_risk_contagion_engine


def test_oi_088_systemic_risk_contagion_engine():
    influence_graph = {
        "nodes": [
            {"market": "FED-RATE", "outgoing_influence": 90, "incoming_influence": 5, "net_influence": 85, "bridge_score": 12, "role": "dominant_source"},
            {"market": "NASDAQ", "outgoing_influence": 62, "incoming_influence": 86, "net_influence": -24, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "outgoing_influence": 35, "incoming_influence": 75, "net_influence": -40, "bridge_score": 54, "role": "sink"},
            {"market": "NVDA", "outgoing_influence": 5, "incoming_influence": 58, "net_influence": -53, "bridge_score": 14, "role": "sink"},
        ],
        "edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83, "confidence": 75},
            {"source": "NASDAQ", "target": "AI-SECTOR", "influence_score": 59, "confidence": 67},
            {"source": "AI-SECTOR", "target": "NVDA", "influence_score": 48, "confidence": 64},
        ],
    }

    transition_graph = {
        "nodes": [
            {"market": "FED-RATE", "regime": "expansion", "transition_pressure": 67, "instability_score": 28, "influence_role": "dominant_source"},
            {"market": "NASDAQ", "regime": "contagion", "transition_pressure": 72, "instability_score": 76, "influence_role": "bridge"},
            {"market": "AI-SECTOR", "regime": "stress", "transition_pressure": 78, "instability_score": 70, "influence_role": "sink"},
            {"market": "NVDA", "regime": "contraction", "transition_pressure": 66, "instability_score": 61, "influence_role": "sink"},
        ],
        "transition_edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "transition_score": 71, "transition_type": "mixed_regime_transition"},
            {"source": "NASDAQ", "target": "AI-SECTOR", "transition_score": 76, "transition_type": "risk_spread"},
            {"source": "AI-SECTOR", "target": "NVDA", "transition_score": 63, "transition_type": "risk_spread"},
        ],
    }

    report = systemic_risk_contagion_engine.analyze_contagion(influence_graph, transition_graph)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 4
    assert report["cascade_path_count"] >= 1
    assert report["headline_risk"]["level"] in {"watch", "elevated", "high", "low"}
    assert report["top_systemic_markets"]
    assert any(p["path"][0] == "FED-RATE" for p in report["cascade_paths"])

    diag = systemic_risk_contagion_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-088 Systemic Risk Contagion Engine")
    print({
        "markets": report["market_count"],
        "cascade_paths": report["cascade_path_count"],
        "headline_risk": report["headline_risk"],
        "top_systemic": report["top_systemic_markets"][0],
    })


if __name__ == "__main__":
    test_oi_088_systemic_risk_contagion_engine()
