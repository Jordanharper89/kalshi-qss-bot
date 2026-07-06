
from qseries_v2.oracle_intelligence.oracle_strategic_briefing_engine import oracle_strategic_briefing_engine


def test_oi_114_oracle_strategic_briefing_engine():
    executive_packet = {
        "executive_score": 81,
        "executive_posture": "balanced_review",
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

    digest = {
        "digest_items": [
            {"market": "CRYPTO", "digest_score": 88, "digest_tier": "critical"},
            {"market": "NASDAQ", "digest_score": 74, "digest_tier": "high"},
        ],
        "executive_summary": {
            "urgent_count": 2,
            "summary_tone": "urgent_oracle_attention",
        },
    }

    stability = {
        "global_stability_score": 66,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
    }

    report = oracle_strategic_briefing_engine.build_strategic_briefing(
        executive_packet,
        digest,
        stability,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["strategic_score"] > 0
    assert report["strategic_posture"] in {
        "strategic_defense",
        "selective_review",
        "priority_expansion_review",
        "balanced_strategy_review",
    }
    assert report["priority_count"] == 2
    assert report["risk_count"] == 2
    assert report["lane_count"] >= 4
    assert report["strategic_lanes"][0]["strategic_rank"] == 1
    assert report["briefing_cards"]
    assert report["briefing_cards"][0]["execution_allowed"] is False
    assert "Oracle remains read-only" in report["executive_notes"][-1]

    diag = oracle_strategic_briefing_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["lane_count"] == report["lane_count"]

    print("[PASS] OI-114 Oracle Strategic Briefing Engine")
    print({
        "strategic_score": report["strategic_score"],
        "strategic_posture": report["strategic_posture"],
        "lane_count": report["lane_count"],
        "top_lane": report["strategic_lanes"][0],
    })


if __name__ == "__main__":
    test_oi_114_oracle_strategic_briefing_engine()
