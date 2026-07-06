from qseries_v2.oracle_intelligence.cascade_severity_ranking_engine import cascade_severity_ranking_engine


def test_oi_089_cascade_severity_ranking_engine():
    report = {
        "market_scores": [
            {
                "market": "NASDAQ",
                "contagion_source_score": 77.2,
                "vulnerability_score": 83.1,
                "systemic_importance_score": 75.1,
                "risk_role": "systemic_contagion_hub",
                "reasons": ["Bridge market", "High incoming pressure"],
            },
            {
                "market": "AI-SECTOR",
                "contagion_source_score": 50,
                "vulnerability_score": 72,
                "systemic_importance_score": 63,
                "risk_role": "vulnerable_sink",
            },
        ],
        "cascade_paths": [
            {
                "path": ["FED-RATE", "NASDAQ", "AI-SECTOR", "NVDA"],
                "cascade_score": 82,
                "path_length": 3,
                "risk_type": "stress_contagion_chain",
            }
        ],
        "risk_clusters": [
            {
                "risk_type": "stress_contagion_chain",
                "path_count": 2,
                "avg_cascade_score": 78,
                "markets": ["FED-RATE", "NASDAQ", "AI-SECTOR", "NVDA"],
                "market_count": 4,
            }
        ],
    }

    ranking = cascade_severity_ranking_engine.rank_cascades(report)

    assert ranking["status"] == "ok"
    assert ranking["read_only"] is True
    assert ranking["item_count"] >= 4
    assert ranking["highest_severity"] is not None
    assert ranking["rankings"][0]["rank"] == 1
    assert ranking["rankings"][0]["severity_score"] >= ranking["rankings"][-1]["severity_score"]

    diag = cascade_severity_ranking_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-089 Cascade Severity Ranking Engine")
    print({
        "items": ranking["item_count"],
        "highest": ranking["highest_severity"],
        "counts": ranking["severity_counts"],
    })


if __name__ == "__main__":
    test_oi_089_cascade_severity_ranking_engine()
