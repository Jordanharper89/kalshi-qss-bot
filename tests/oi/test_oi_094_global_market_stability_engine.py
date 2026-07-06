
from qseries_v2.oracle_intelligence.global_market_stability_engine import global_market_stability_engine


def test_oi_094_global_market_stability_engine():
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
    contagion_report = {
        "market_scores": [
            {"market": "NASDAQ", "systemic_importance_score": 75, "vulnerability_score": 83, "contagion_source_score": 77},
            {"market": "FED-RATE", "systemic_importance_score": 52, "vulnerability_score": 20, "contagion_source_score": 70},
        ]
    }
    severity_ranking = {
        "rankings": [
            {"item_type": "market", "label": "NASDAQ", "severity_score": 92},
            {"item_type": "market", "label": "FED-RATE", "severity_score": 40},
        ]
    }
    decay_profiles = {
        "profiles": [
            {"market": "NASDAQ", "persistence_score": 80, "decay_rate": 0.25},
            {"market": "FED-RATE", "persistence_score": 42, "decay_rate": 0.55},
        ]
    }

    index = global_market_stability_engine.build_stability_index(
        fragility_report,
        resilience_report,
        contagion_report,
        severity_ranking,
        decay_profiles,
    )

    assert index["status"] == "ok"
    assert index["read_only"] is True
    assert index["market_count"] == 2
    assert 0 <= index["global_stability_score"] <= 100
    assert index["global_stability_tier"] in {"stable", "constructive", "mixed", "unstable", "critical"}
    assert index["most_stable_markets"][0]["stability_score"] >= index["most_stable_markets"][-1]["stability_score"]

    diag = global_market_stability_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-094 Global Market Stability Engine")
    print({
        "markets": index["market_count"],
        "global_score": index["global_stability_score"],
        "tier": index["global_stability_tier"],
        "posture": index["risk_posture"],
        "least_stable": index["least_stable_markets"][0],
    })


if __name__ == "__main__":
    test_oi_094_global_market_stability_engine()
