
from qseries_v2.oracle_intelligence.adaptive_influence_decay_engine import adaptive_influence_decay_engine


def test_oi_093_adaptive_influence_decay_engine():
    influence_graph = {
        "nodes": [
            {"market": "NASDAQ", "incoming_influence": 86, "outgoing_influence": 62, "bridge_score": 70},
            {"market": "FED-RATE", "incoming_influence": 5, "outgoing_influence": 90, "bridge_score": 12},
        ]
    }
    fragility_report = {
        "scores": [
            {"market": "NASDAQ", "fragility_score": 71},
            {"market": "FED-RATE", "fragility_score": 28},
        ]
    }
    resilience_report = {
        "scores": [
            {"market": "NASDAQ", "resilience_score": 35},
            {"market": "FED-RATE", "resilience_score": 78},
        ]
    }
    transition_graph = {
        "nodes": [
            {"market": "NASDAQ", "transition_pressure": 72, "instability_score": 76},
            {"market": "FED-RATE", "transition_pressure": 35, "instability_score": 25},
        ]
    }

    profiles = adaptive_influence_decay_engine.build_decay_profiles(
        influence_graph,
        fragility_report,
        resilience_report,
        transition_graph,
    )

    assert profiles["status"] == "ok"
    assert profiles["read_only"] is True
    assert profiles["market_count"] == 2
    assert profiles["profiles"][0]["persistence_score"] >= profiles["profiles"][-1]["persistence_score"]

    shock_trace = {
        "source_market": "FED-RATE",
        "paths": [
            {"path": ["FED-RATE", "NASDAQ"], "shock_score": 80},
            {"path": ["FED-RATE", "NASDAQ", "AI-SECTOR"], "shock_score": 72},
        ],
    }

    adjusted = adaptive_influence_decay_engine.apply_decay_to_paths(shock_trace, profiles)
    assert adjusted["status"] == "ok"
    assert adjusted["read_only"] is True
    assert adjusted["path_count"] == 2
    assert "adaptive_decay_score" in adjusted["adjusted_paths"][0]

    diag = adaptive_influence_decay_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-093 Adaptive Influence Decay Engine")
    print({
        "markets": profiles["market_count"],
        "slowest": profiles["slowest_decay_markets"][0],
        "adjusted_top": adjusted["top_adjusted_paths"][0],
    })


if __name__ == "__main__":
    test_oi_093_adaptive_influence_decay_engine()
