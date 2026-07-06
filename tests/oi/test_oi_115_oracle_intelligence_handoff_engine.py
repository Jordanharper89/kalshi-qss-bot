
from qseries_v2.oracle_intelligence.oracle_intelligence_handoff_engine import oracle_intelligence_handoff_engine


def test_oi_115_oracle_intelligence_handoff_engine():
    executive = {
        "executive_score": 77.27,
        "executive_posture": "balanced_review",
        "headline": "Executive posture balanced; review top-ranked intelligence.",
    }

    strategic = {
        "strategic_score": 88.0,
        "strategic_posture": "priority_expansion_review",
    }

    digest = {
        "digest_items": [
            {
                "market": "CRYPTO",
                "digest_score": 85.58,
                "digest_tier": "critical",
                "alert_count": 1,
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
            },
            {
                "market": "NASDAQ",
                "digest_score": 64.2,
                "digest_tier": "elevated",
                "alert_count": 1,
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
            },
        ]
    }

    support = {
        "support_packets": [
            {
                "market": "CRYPTO",
                "support_packet_score": 90.02,
                "support_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
            },
            {
                "market": "NASDAQ",
                "support_packet_score": 74.0,
                "support_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
            },
        ]
    }

    report = oracle_intelligence_handoff_engine.build_handoff(
        executive,
        strategic,
        digest,
        support,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["execution_owner"] == "Q Series"
    assert report["handoff_count"] == 2
    assert report["handoff_items"][0]["handoff_rank"] == 1
    assert report["handoff_items"][0]["handoff_score"] >= report["handoff_items"][-1]["handoff_score"]
    assert report["handoff_summary"]["execution_allowed"] is False

    diag = oracle_intelligence_handoff_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-115 Oracle Intelligence Handoff Engine")
    print({
        "handoff_score": report["handoff_score"],
        "handoff_posture": report["handoff_posture"],
        "summary": report["handoff_summary"],
        "top": report["handoff_items"][0],
    })


if __name__ == "__main__":
    test_oi_115_oracle_intelligence_handoff_engine()
