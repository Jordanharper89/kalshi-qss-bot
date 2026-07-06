
from qseries_v2.oracle_intelligence.market_influence_graph_engine import market_influence_graph_engine


def test_oi_086_market_influence_graph_engine():
    propagation = {
        "propagation_edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "propagation_score": 42, "confidence": 72},
            {"source": "NASDAQ", "target": "AI-SECTOR", "propagation_score": 28, "confidence": 64},
        ]
    }

    causal = {
        "causal_edges": [
            {"cause": "FED-RATE", "effect": "NASDAQ", "causal_score": 38, "confidence": 78},
            {"cause": "OIL", "effect": "AIRLINES", "causal_score": 35, "confidence": 70},
        ]
    }

    flow = {
        "information_flows": [
            {"source": "NASDAQ", "target": "AI-SECTOR", "flow_score": 31, "confidence": 68},
            {"source": "AI-SECTOR", "target": "NVDA", "flow_score": 30, "confidence": 66},
        ]
    }

    graph = market_influence_graph_engine.build_graph(
        propagation_snapshot=propagation,
        causal_snapshot=causal,
        flow_snapshot=flow,
    )

    assert graph["status"] == "ok"
    assert graph["read_only"] is True
    assert graph["node_count"] >= 5
    assert graph["edge_count"] >= 4
    assert graph["edges"][0]["influence_score"] >= graph["edges"][-1]["influence_score"]
    assert any(n["market"] == "FED-RATE" for n in graph["nodes"])
    assert any(e["source"] == "FED-RATE" and e["target"] == "NASDAQ" for e in graph["edges"])
    assert graph["clusters"]

    diag = market_influence_graph_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-086 Market Influence Graph Engine")
    print({
        "nodes": graph["node_count"],
        "edges": graph["edge_count"],
        "top_edge": graph["edges"][0],
        "clusters": len(graph["clusters"]),
    })


if __name__ == "__main__":
    test_oi_086_market_influence_graph_engine()
