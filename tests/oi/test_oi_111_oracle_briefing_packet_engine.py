
from qseries_v2.oracle_intelligence.oracle_briefing_packet_engine import oracle_briefing_packet_engine


def test_oi_111_oracle_briefing_packet_engine():
    support_packets = {
        "support_packets": [
            {
                "market": "CRYPTO",
                "support_packet_score": 91,
                "support_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
            },
            {
                "market": "NASDAQ",
                "support_packet_score": 74,
                "support_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
            },
        ]
    }

    health_dashboard = {
        "cards": [
            {
                "market": "CRYPTO",
                "health_score": 24,
                "health_tier": "critical",
                "dashboard_status": "red",
            },
            {
                "market": "NASDAQ",
                "health_score": 32,
                "health_tier": "weak",
                "dashboard_status": "orange",
            },
        ]
    }

    alerts = {
        "alerts": [
            {"market": "CRYPTO", "priority": "critical"},
            {"market": "NASDAQ", "priority": "high"},
        ]
    }

    report = oracle_briefing_packet_engine.build_briefing_packets(
        support_packets,
        health_dashboard,
        alerts,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["briefing_count"] == 2
    assert report["briefing_packets"][0]["briefing_rank"] == 1
    assert report["briefing_packets"][0]["briefing_score"] >= report["briefing_packets"][-1]["briefing_score"]
    assert report["summary"]["execution_allowed"] is False

    diag = oracle_briefing_packet_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-111 Oracle Briefing Packet Engine")
    print({
        "briefings": report["briefing_count"],
        "summary": report["summary"],
        "top": report["briefing_packets"][0],
    })


if __name__ == "__main__":
    test_oi_111_oracle_briefing_packet_engine()
