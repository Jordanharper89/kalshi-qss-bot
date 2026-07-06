
from qseries_v2.oracle_intelligence.market_regime_transition_graph_engine import market_regime_transition_graph_engine


def test_oi_087_market_regime_transition_graph_engine():
    influence_graph = {
        "nodes": [
            {"market": "FED-RATE", "outgoing_influence": 90, "incoming_influence": 5, "net_influence": 85, "bridge_score": 12, "role": "dominant_source"},
            {"market": "NASDAQ", "outgoing_influence": 62, "incoming_influence": 86, "net_influence": -24, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "outgoing_influence": 35, "incoming_influence": 75, "net_influence": -40, "bridge_score": 54, "role": "sink"},
            {"market": "OIL", "outgoing_influence": 58, "incoming_influence": 10, "net_influence": 48, "bridge_score": 22, "role": "source"},
            {"market": "AIRLINES", "outgoing_influence": 2, "incoming_influence": 55, "net_influence": -53, "bridge_score": 11, "role": "sink"},
        ],
        "edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83, "confidence": 75},
            {"source": "NASDAQ", "target": "AI-SECTOR", "influence_score": 59, "confidence": 67},
            {"source": "OIL", "target": "AIRLINES", "influence_score": 52, "confidence": 70},
        ],
    }

    state = {
        "markets": {
            "FED-RATE": {"momentum": 25, "volatility": 35, "liquidity_stress": 10},
            "NASDAQ": {"momentum": -12, "volatility": 65, "liquidity_stress": 45},
            "AI-SECTOR": {"momentum": -20, "volatility": 48, "liquidity_stress": 42},
            "OIL": {"momentum": 12, "volatility": 38, "liquidity_stress": 20},
            "AIRLINES": {"momentum": -15, "volatility": 44, "liquidity_stress": 50},
        }
    }

    graph = market_regime_transition_graph_engine.build_transition_graph(influence_graph, state)

    assert graph["status"] == "ok"
    assert graph["read_only"] is True
    assert graph["node_count"] == 5
    assert graph["transition_edge_count"] >= 3
    assert graph["regime_counts"]
    assert graph["dominant_transitions"]
    assert any(n["market"] == "FED-RATE" for n in graph["nodes"])

    diag = market_regime_transition_graph_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-087 Market Regime Transition Graph Engine")
    print({
        "nodes": graph["node_count"],
        "transition_edges": graph["transition_edge_count"],
        "regimes": graph["regime_counts"],
        "top_transition": graph["dominant_transitions"][0],
    })


if __name__ == "__main__":
    test_oi_087_market_regime_transition_graph_engine()
