
from qseries_v2.oracle_intelligence.oracle_digest_engine import oracle_digest_engine


def test_oi_112_oracle_digest_engine():
    briefing = {
        "briefing_packets": [
            {
                "market": "CRYPTO",
                "briefing_score": 92,
                "briefing_tier": "critical",
                "support_tier": "critical",
                "health_score": 24,
                "alert_count": 1,
                "top_alert_priority": "critical",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
            },
            {
                "market": "NASDAQ",
                "briefing_score": 74,
                "briefing_tier": "high",
                "support_tier": "high",
                "health_score": 32,
                "alert_count": 1,
                "top_alert_priority": "high",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
            },
        ]
    }

    stability = {
        "global_stability_score": 62.6,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
    }

    posture = {
        "postures": [
            {"market": "CRYPTO", "risk_posture_score": 90, "posture": "systemic_alert"},
            {"market": "NASDAQ", "risk_posture_score": 62.9, "posture": "heightened_monitoring"},
        ]
    }

    report = oracle_digest_engine.build_digest(briefing, stability, posture)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["digest_count"] == 2
    assert report["digest_items"][0]["digest_rank"] == 1
    assert report["digest_items"][0]["digest_score"] >= report["digest_items"][-1]["digest_score"]
    assert report["executive_summary"]["execution_allowed"] is False

    diag = oracle_digest_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-112 Oracle Digest Engine")
    print({
        "digest_count": report["digest_count"],
        "summary": report["executive_summary"],
        "top": report["digest_items"][0],
    })


if __name__ == "__main__":
    test_oi_112_oracle_digest_engine()
