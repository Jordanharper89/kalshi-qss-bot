
from qseries_v2.oracle_intelligence.qseries_intake_packet_engine import qseries_intake_packet_engine


def test_oi_118_qseries_intake_packet_engine():
    manifest = {
        "manifest_status": "ready",
        "validation_status": "validated",
        "q_series_visibility_ready": True,
        "execution_allowed": False,
        "execution_owner": "Q Series",
        "manifest_items": [
            {
                "market": "CRYPTO",
                "handoff_rank": 1,
                "handoff_score": 90.2,
                "handoff_tier": "critical",
                "digest_tier": "critical",
                "support_tier": "critical",
                "review_conclusion": "high_confidence_review",
                "oracle_observation": "Keep market in elevated Oracle observation rotation.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
            {
                "market": "NASDAQ",
                "handoff_rank": 2,
                "handoff_score": 72.0,
                "handoff_tier": "high",
                "digest_tier": "elevated",
                "support_tier": "high",
                "review_conclusion": "confirmed_review",
                "oracle_observation": "Oracle review packet is ready for read-only downstream visibility.",
                "execution_allowed": False,
                "execution_owner": "Q Series",
                "read_only": True,
            },
        ],
    }

    packet = qseries_intake_packet_engine.build_intake_packet(manifest)

    assert packet["status"] == "ok"
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False
    assert packet["execution_owner"] == "Q Series"
    assert packet["q_series_visibility_ready"] is True
    assert packet["intake_status"] == "ready"
    assert packet["intake_count"] == 2
    assert packet["intake_items"][0]["intake_rank"] == 1
    assert packet["intake_items"][0]["market"] == "CRYPTO"
    assert packet["intake_summary"]["execution_allowed"] is False

    diag = qseries_intake_packet_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["intake_status"] == "ready"

    print("[PASS] OI-118 Q Series Intake Packet Engine")
    print({
        "intake_status": packet["intake_status"],
        "intake_count": packet["intake_count"],
        "summary": packet["intake_summary"],
        "top": packet["intake_items"][0],
    })


if __name__ == "__main__":
    test_oi_118_qseries_intake_packet_engine()
