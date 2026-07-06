
from qseries_v2.oracle_intelligence.oracle_executive_intelligence_engine import (
    build_executive_intelligence,
    oracle_executive_intelligence_engine,
)


def test_oi_113_oracle_executive_intelligence_engine():
    digest = {
        "digest_score": 82,
        "themes": ["Cross-market pressure building"],
        "top_priorities": [
            {"label": "Election market volatility", "priority": 91},
            {"label": "Macro rate path", "priority": 76},
        ],
        "top_risks": [
            {"label": "Liquidity fragility", "severity": 68},
            {"label": "Contagion risk", "severity": 61},
        ],
    }

    packet = build_executive_intelligence(digest)

    assert packet["status"] == "ok"
    assert packet["read_only"] is True
    assert packet["execution_permission"] is False
    assert packet["execution_owner"] == "Q Series"
    assert packet["executive_score"] > 0
    assert packet["executive_posture"] in {
        "defensive",
        "cautious",
        "balanced_review",
        "aggressive_review",
    }
    assert packet["priority_count"] == 2
    assert packet["risk_count"] == 2
    assert packet["top_priorities"][0]["label"] == "Election market volatility"
    assert packet["top_risks"][0]["label"] == "Liquidity fragility"
    assert "read-only" in packet["executive_summary"].lower()
    assert len(packet["recommended_oracle_focus"]) >= 3
    assert oracle_executive_intelligence_engine.history


if __name__ == "__main__":
    test_oi_113_oracle_executive_intelligence_engine()
    print("[PASS] OI-113 Oracle Executive Intelligence Engine")
    print(build_executive_intelligence({
        "digest_score": 78,
        "themes": ["Executive synthesis active"],
        "top_priorities": [{"label": "Market priority queue", "priority": 88}],
        "top_risks": [{"label": "Review workload imbalance", "severity": 55}],
    }))
