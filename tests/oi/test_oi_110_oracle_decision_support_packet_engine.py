
from qseries_v2.oracle_intelligence.oracle_decision_support_packet_engine import oracle_decision_support_packet_engine


def test_oi_110_oracle_decision_support_packet_engine():
    review_results = {
        "review_results": [
            {
                "market": "CRYPTO",
                "review_conclusion": "high_confidence_review",
                "signal_quality_score": 88,
                "checklist_completion_rate": 0.91,
            },
            {
                "market": "NASDAQ",
                "review_conclusion": "confirmed_review",
                "signal_quality_score": 72,
                "checklist_completion_rate": 0.75,
            },
        ]
    }

    priority_queue = {
        "priority_queue": [
            {
                "market": "CRYPTO",
                "priority_score": 92,
                "queue_action": "immediate_oracle_review",
            },
            {
                "market": "NASDAQ",
                "priority_score": 72.94,
                "queue_action": "priority_oracle_watch",
            },
        ]
    }

    risk_posture = {
        "postures": [
            {
                "market": "CRYPTO",
                "risk_posture_score": 90,
                "posture": "systemic_alert",
            },
            {
                "market": "NASDAQ",
                "risk_posture_score": 62.9,
                "posture": "heightened_monitoring",
            },
        ]
    }

    report = oracle_decision_support_packet_engine.build_support_packets(
        review_results,
        priority_queue,
        risk_posture,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["packet_count"] == 2
    assert report["support_packets"][0]["support_rank"] == 1
    assert report["support_packets"][0]["support_packet_score"] >= report["support_packets"][-1]["support_packet_score"]
    assert report["summary"]["execution_allowed"] is False

    diag = oracle_decision_support_packet_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False

    print("[PASS] OI-110 Oracle Decision Support Packet Engine")
    print({
        "packets": report["packet_count"],
        "summary": report["summary"],
        "top": report["support_packets"][0],
    })


if __name__ == "__main__":
    test_oi_110_oracle_decision_support_packet_engine()
