from qseries_v2.oracle_intelligence.shock_path_trace_engine import shock_path_trace_engine


def test_oi_090_shock_path_trace_engine():
    influence_graph = {
        "edges": [
            {"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83, "confidence": 75},
            {"source": "NASDAQ", "target": "AI-SECTOR", "influence_score": 59, "confidence": 67},
            {"source": "AI-SECTOR", "target": "NVDA", "influence_score": 48, "confidence": 64},
            {"source": "NASDAQ", "target": "CRYPTO", "influence_score": 42, "confidence": 60},
        ]
    }

    contagion_report = {
        "market_scores": [
            {"market": "NASDAQ", "systemic_importance_score": 75, "vulnerability_score": 83},
            {"market": "AI-SECTOR", "systemic_importance_score": 64, "vulnerability_score": 72},
            {"market": "NVDA", "systemic_importance_score": 51, "vulnerability_score": 61},
            {"market": "CRYPTO", "systemic_importance_score": 55, "vulnerability_score": 69},
        ]
    }

    trace = shock_path_trace_engine.trace_shock_paths("FED-RATE", influence_graph, contagion_report)

    assert trace["status"] == "ok"
    assert trace["read_only"] is True
    assert trace["source_market"] == "FED-RATE"
    assert trace["path_count"] >= 3
    assert trace["top_paths"]
    assert trace["impacted_markets"]
    assert trace["top_paths"][0]["decay_adjusted_score"] >= trace["top_paths"][-1]["decay_adjusted_score"]

    diag = shock_path_trace_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-090 Shock Path Trace Engine")
    print({
        "source": trace["source_market"],
        "paths": trace["path_count"],
        "top_path": trace["top_paths"][0],
        "impacted": trace["impacted_markets"][:3],
    })


if __name__ == "__main__":
    test_oi_090_shock_path_trace_engine()
